from django import forms
from django.utils.timezone import localtime
from .models import Booking, Appointment
 
from django.core.validators import RegexValidator, EmailValidator
import uuid

class BookingForm(forms.ModelForm):
    quantity = forms.IntegerField(
        label="Cantidad",
        min_value=1,
        initial=1,
        required=False,
    )

    phone = forms.CharField(
        label="Teléfono",
        validators=[
            RegexValidator(
                regex=r'^\+?(\d[\d\s-]{7,15})$',
                message="Ingrese un número de teléfono válido (7-15 dígitos)."
            )
        ],
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "+52 55 1234 5678",
            "inputmode": "tel",
            "pattern": r"^\+?(\d[\d\s-]{7,15})$"
        })
    )

    email = forms.EmailField(
        label="Correo electrónico",
        validators=[EmailValidator(message="Ingrese un correo válido (ej. usuario@gmail.com).")],
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "ejemplo@correo.com",
            "autocomplete": "email",
        })
    )

    class Meta:
        model = Booking
        fields = ["name", "email", "phone", "quantity"]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        dominios_validos = [
            "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "icloud.com",
            "live.com", "msn.com"
        ]
        dominio = email.split("@")[-1].lower()
        if dominio not in dominios_validos:
            raise forms.ValidationError(f"El dominio '{dominio}' no es común. Verifique su correo.")
        return email



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
