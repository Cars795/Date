from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import weasyprint

def send_booking_email_safe(booking):
    """Genera PDF y envía correo, pero nunca lanza excepción."""
    try:
        html = render_to_string("bookings/booking_email.html", {"booking": booking})
    except Exception as e:
        print(f"⚠️ Error cargando plantilla de correo: {e}")
        return

    # Intentar generar PDF
    try:
        pdf = weasyprint.HTML(string=html).write_pdf()
    except Exception as e:
        print(f"⚠️ Error generando PDF: {e}")
        pdf = None

    # Intentar enviar correo
    try:
        email = EmailMessage(
            subject=f"Confirmación de reserva: {booking.event.title}",
            body="Gracias por tu reserva. Adjuntamos tu boleto.",
            to=[booking.email],
        )
        if pdf:
            email.attach(f"Boleto_{booking.confirmation_code}.pdf", pdf, "application/pdf")
        email.send(fail_silently=True)
    except Exception as e:
        print(f"⚠️ Error enviando correo: {e}")
