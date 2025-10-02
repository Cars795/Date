from django import forms
from .models import Booking, Appointment

 
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'email', 'phone']
 


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["client", "staff", "start", "notes", "status"]
        widgets = {
            "start": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "client": forms.Select(attrs={"class": "form-select"}),
            "staff": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
