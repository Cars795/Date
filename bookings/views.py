from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.urls import reverse
from django.contrib import messages
from .models import Event
from .forms import BookingForm

class EventListView(ListView):
    model = Event
    template_name = 'bookings/event_list.html'
    context_object_name = 'events'
    queryset = Event.objects.order_by('start').all()

def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form = BookingForm(request.POST or None)
    if request.method == 'POST':
        if event.seats_available <= 0:
            messages.error(request, "No hay lugares disponibles.")
            return redirect(reverse('bookings:event_detail', args=[event.pk]))
        if form.is_valid():
            booking = form.save(commit=False)
            booking.event = event
            booking.save()
            messages.success(request, "Reserva creada correctamente.")
            return redirect(reverse('bookings:booking_success', args=[booking.pk]))
    return render(request, 'bookings/event_detail.html', {'event': event, 'form': form})

def booking_success(request, pk):
    from .models import Booking
    booking = get_object_or_404(Booking, pk=pk)
    return render(request, 'bookings/booking_success.html', {'booking': booking})

def home(request):
    return render(request, "bookings/home.html")