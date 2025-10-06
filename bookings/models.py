from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User


User = get_user_model()

class EventType(models.Model):
    name = models.CharField(max_length=100)
    duration_minutes = models.PositiveIntegerField(default=60)

    def __str__(self):
        return self.name
 
class Event(models.Model):
    type = models.ForeignKey("EventType", on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=1)
    organizer = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)

    # NUEVOS CAMPOS
    allow_group_booking = models.BooleanField(default=False)
    max_tickets_per_booking = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(allow_group_booking=False) | Q(max_tickets_per_booking__gte=1),
                name="valid_group_booking_limit"
            ),
        ]

    @property
    def seats_taken(self):
        return self.bookings.filter(cancelled=False).aggregate(models.Sum("quantity"))["quantity__sum"] or 0

    @property
    def seats_available(self):
        return max(0, self.capacity - self.seats_taken)


import uuid

class Booking(models.Model):
    event = models.ForeignKey("Event", on_delete=models.CASCADE, related_name="bookings")
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=1)
    cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmation_code = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.event.title})"

    class Meta:
        ordering = ["-created_at"]


class Staff(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50)  # Doctor, Abogado, Consultor...
    specialty = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.role} {self.name}"

class Client(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name

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


# models.py
class AppointmentStatusHistory(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="history")
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
