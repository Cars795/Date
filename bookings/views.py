from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
import weasyprint

from .models import Event, Booking
from .forms import BookingForm


# ============================
#  LISTA DE EVENTOS
# ============================
class EventListView(ListView):
    model = Event
    template_name = "bookings/event_list.html"
    context_object_name = "events"
    queryset = Event.objects.order_by("start").all()

# ============================
#  DETALLE / RESERVA DE EVENTO
# ============================
import uuid
import traceback
from django.shortcuts import get_object_or_404, render
from django.contrib import messages
from django.urls import reverse
from .models import Event, Booking
from .forms import BookingForm


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form = BookingForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.event = event

        # Generar código único
        if not booking.confirmation_code:
            booking.confirmation_code = uuid.uuid4()

        # Validar cupos
        if booking.quantity > event.seats_available:
            form.add_error("quantity", "No hay suficientes lugares disponibles.")
        else:
            booking.save()

            # Intentar envío de correo/PDF
            try:
                from .utils import send_booking_email_safe
                send_booking_email_safe(booking)
            except Exception:
                print("⚠️ Error enviando correo o generando PDF:")
                print(traceback.format_exc())

            # URLs para redirecciones
            success_url = reverse("bookings:booking_success", args=[booking.confirmation_code])
            list_url = reverse("bookings:event_list")

            messages.success(request, f"✅ Reserva confirmada. Código: {booking.confirmation_code}")

            # Renderiza plantilla de doble acción
            return render(request, "bookings/redirect_newtab.html", {
                "success_url": success_url,
                "list_url": list_url,
                "booking": booking
            })

    return render(request, "bookings/event_detail.html", {"event": event, "form": form})


# ============================
#  CONFIRMACIÓN
# ============================
def booking_success(request, code):
    booking = get_object_or_404(Booking, confirmation_code=code)
    return render(request, "bookings/booking_success.html", {"booking": booking})


# ============================
#  GENERAR PDF
# ============================
def booking_ticket_pdf(request, code):
    booking = get_object_or_404(Booking, confirmation_code=code)
    html = render_to_string("bookings/booking_success.html", {"booking": booking})
    pdf = weasyprint.HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="boleto_{booking.confirmation_code}.pdf"'
    return response


# ============================
#  CORREO CON PDF
# ============================
def send_booking_email(booking):
    html = render_to_string("bookings/booking_email.html", {"booking": booking})
    pdf = weasyprint.HTML(string=html).write_pdf()
    email = EmailMessage(
        subject=f"🎟️ Confirmación de reserva: {booking.event.title}",
        body="Gracias por tu reserva. Te enviamos tu boleto adjunto en PDF.",
        to=[booking.email],
    )
    email.attach(f"Boleto_{booking.confirmation_code}.pdf", pdf, "application/pdf")
    email.send()


# ============================
#  HOME SIMPLE
# ============================
def home(request):
    return render(request, "bookings/home.html")
