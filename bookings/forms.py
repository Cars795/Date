from django import forms
from django.utils.timezone import localtime
from .models import Booking, Appointment

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['name', 'email', 'phone']


class AppointmentForm(forms.ModelForm):
    # Asegura parseo y render del <input type="datetime-local">
    start = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'class': 'form-control', 'step': '60'},
            format='%Y-%m-%dT%H:%M',
        ),
    )

    class Meta:
        model = Appointment
        fields = ["client", "staff", "start", "notes", "status"]
        widgets = {
            "client": forms.Select(attrs={"class": "form-select"}),
            "staff": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si es edición, precarga el valor en formato datetime-local (zona local)
        if self.instance and self.instance.pk and self.instance.start:
            self.fields['start'].initial = localtime(self.instance.start).strftime('%Y-%m-%dT%H:%M')
