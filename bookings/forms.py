from django import forms
from django.utils.timezone import localtime
from .models import Booking, Appointment
 
class BookingForm(forms.ModelForm):
    quantity = forms.IntegerField(
        label="Cantidad de lugares",
        min_value=1,
        initial=1,
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control", "style": "max-width:120px"})
    )

    class Meta:
        model = Booking
        fields = ['name', 'email', 'phone', 'quantity']
        
    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

        # si el evento no permite reservas múltiples, se oculta el campo
        if not event or not event.allow_group_booking:
            self.fields.pop("quantity", None)

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity", 1)
        if self.event:
            if qty > self.event.seats_available:
                raise forms.ValidationError("No hay suficientes lugares disponibles.")
            if self.event.allow_group_booking and qty > self.event.max_tickets_per_booking:
                raise forms.ValidationError(
                    f"Solo puede reservar hasta {self.event.max_tickets_per_booking} lugares."
                )
        return qty


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
