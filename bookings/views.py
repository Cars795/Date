from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.urls import reverse
from django.contrib import messages
from .models import Event
from .forms import BookingForm
from .models import Booking


class EventListView(ListView):
    model = Event
    template_name = 'bookings/event_list.html'
    context_object_name = 'events'
    queryset = Event.objects.order_by('start').all()

# bookings/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Event
from .forms import BookingForm

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form = BookingForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.event = event
        if booking.quantity > event.seats_available:
            form.add_error("quantity", "No hay suficientes lugares disponibles.")
        else:
            booking.save()
            messages.success(
                request,
                f"Reserva confirmada. Tu número de confirmación es: {booking.confirmation_code}"
            )
            return redirect("bookings:booking_success", code=booking.confirmation_code)

    return render(request, "bookings/event_detail.html", {"event": event, "form": form})


def booking_success(request, code):
    booking = get_object_or_404(Booking, confirmation_code=code)
    return render(request, "bookings/booking_success.html", {"booking": booking})

def home(request):
    return render(request, "bookings/home.html")