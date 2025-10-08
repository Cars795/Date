from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
import uuid
from datetime import timedelta

User = get_user_model()

# --------------------------------------------------------------------
#  Tipos y estado de eventos
# --------------------------------------------------------------------
class EventType(models.Model):
    name = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return self.name


class EventStatus(models.TextChoices):
    ACTIVE = "active", "Activo"
    CANCELLED = "cancelled", "Cancelado"
    POSTPONED = "postponed", "Reprogramado"
    FINISHED = "finished", "Finalizado"


# --------------------------------------------------------------------
#  Eventos
# --------------------------------------------------------------------
class Event(models.Model):
    type = models.ForeignKey("EventType", on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    allow_group_booking = models.BooleanField(default=False)
    max_tickets_per_booking = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.ACTIVE,
    )
    reference_event = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_versions",
        help_text="Evento original si fue reprogramado",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(allow_group_booking=False) | Q(max_tickets_per_booking__gte=1),
                name="valid_group_booking_limit",
            ),
        ]
        ordering = ["-start"]

    def __str__(self):
        return f"{self.title} — {self.start.strftime('%d/%m/%Y %H:%M')} ({self.get_status_display()})"

    @property
    def seats_taken(self):
        return self.bookings.filter(cancelled=False).aggregate(models.Sum("quantity"))["quantity__sum"] or 0

    @property
    def seats_available(self):
        return max(0, self.capacity - self.seats_taken)

    @property
    def occupancy_rate(self):
        if self.capacity == 0:
            return 0
        return round((self.seats_taken / self.capacity) * 100, 1)

    def duplicate(self, new_date=None):
        new_event = Event.objects.create(
            type=self.type,
            title=self.title + " (Reprogramado)",
            description=self.description,
            start=new_date or (self.start + timedelta(days=7)),
            capacity=self.capacity,
            organizer=self.organizer,
            allow_group_booking=self.allow_group_booking,
            max_tickets_per_booking=self.max_tickets_per_booking,
            status=EventStatus.POSTPONED,
            reference_event=self,
        )
        return new_event

    def cancel(self, reason=None):
        self.status = EventStatus.CANCELLED
        self.save()


# --------------------------------------------------------------------
#  Reservas
# --------------------------------------------------------------------
class Booking(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmation_code = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.event.title})"


# --------------------------------------------------------------------
#  Personas base y derivadas
# --------------------------------------------------------------------
class Person(models.Model):
    """Entidad base para Cliente y Staff."""
    name = models.CharField("Nombre completo", max_length=100)
    phone = models.CharField("Teléfono", max_length=20, blank=True)
    email = models.EmailField("Correo electrónico", blank=True)
    notes = models.TextField("Notas adicionales", blank=True)
    preferences = models.TextField("Preferencias", blank=True)
    services = models.TextField("Servicios asociados", blank=True)
    available_days = models.JSONField("Días disponibles", blank=True, null=True)
    active = models.BooleanField("Activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class Client(Person):
    """Cliente del sistema de reservas."""
    company = models.CharField("Empresa / procedencia", max_length=120, blank=True)
    is_whatsapp = models.BooleanField("WhatsApp activo", default=False)



class Staff(Person):
    """Personal interno o externo que atiende citas."""
    role = models.CharField("Rol / puesto", max_length=80)
    specialty = models.CharField("Especialidad", max_length=120, blank=True)
    allow_multiple = models.BooleanField("Permitir citas simultáneas", default=True)
    is_whatsapp = models.BooleanField("WhatsApp activo", default=False)



# --------------------------------------------------------------------
#  Citas
# --------------------------------------------------------------------
class Appointment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    start = models.DateTimeField()
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pendiente"),
            ("confirmed", "Confirmada"),
            ("cancelled", "Cancelada"),
            ("done", "Atendida"),
        ],
        default="pending"
    )

    def __str__(self):
        return f"{self.client} con {self.staff} el {self.start:%d/%m %H:%M}"


class AppointmentStatusHistory(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
