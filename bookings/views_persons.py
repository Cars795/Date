# bookings/views_persons.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Client, Staff
from .forms import ClientForm, StaffForm


def person_list(request):
    """Vista unificada para listar clientes y staff."""
    q = request.GET.get("q", "").strip().lower()
    show = request.GET.get("type", "clients")  # clients | staff

    if show == "staff":
        data = Staff.objects.all()
        title = "Personal interno"
    else:
        data = Client.objects.all()
        title = "Clientes"

    if q:
        data = data.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))

    total = data.count()

    return render(request, "bookings/person_list.html", {
        "title": title,
        "data": data,
        "show": show,
        "query": q,
        "total": total,
    })


from django.shortcuts import render, redirect
from .models import Client, Staff

def person_form(request):
    """Formulario unificado para crear Cliente o Staff según ?type=client|staff"""
    type_param = request.GET.get("type", "client")
    is_edit = False
    type_label = "Cliente" if type_param == "client" else "Staff"

    # Lista de días para staff
    week_days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    if request.method == "POST":
        # Procesar formulario según tipo
        if type_param == "client":
            Client.objects.create(
                name=request.POST.get("name", ""),
                phone=request.POST.get("phone", ""),
                email=request.POST.get("email", ""),
                company=request.POST.get("company", ""),
                notes=request.POST.get("notes", ""),
                preferences=request.POST.get("preferences", ""),
                services=request.POST.get("services", "")
            )
        else:
            # Para staff, recogemos días seleccionados y los convertimos en JSON
            available_days = request.POST.getlist("available_days")
            Staff.objects.create(
                name=request.POST.get("name", ""),
                phone=request.POST.get("phone", ""),
                email=request.POST.get("email", ""),
                role=request.POST.get("role", ""),
                specialty=request.POST.get("specialty", ""),
                notes=request.POST.get("notes", ""),
                preferences=request.POST.get("preferences", ""),
                services=request.POST.get("services", ""),
                allow_multiple=request.POST.get("allow_multiple") == "on",
                available_days=available_days or None
            )

        # Redirigir a la lista
        return redirect(f"/personas/?type={'clients' if type_param == 'client' else 'staff'}")

    # Render del formulario vacío (GET)
    return render(request, "bookings/person_form.html", {
        "type": type_param,
        "type_label": type_label,
        "is_edit": is_edit,
        "week_days": week_days,
        "cancel_url": "/personas/",
    })


from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, Staff

def person_edit(request, pk):
    """Edita una persona existente (cliente o staff)"""
    # Buscar la persona en ambas tablas
    person = None
    type_param = "client"
    try:
        person = Client.objects.get(pk=pk)
        type_param = "client"
    except Client.DoesNotExist:
        try:
            person = Staff.objects.get(pk=pk)
            type_param = "staff"
        except Staff.DoesNotExist:
            return redirect("/personas/")  # si no existe

    is_edit = True
    type_label = "Cliente" if type_param == "client" else "Staff"
    week_days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    if request.method == "POST":
        if type_param == "client":
            person.name = request.POST.get("name", "")
            person.phone = request.POST.get("phone", "")
            person.email = request.POST.get("email", "")
            person.company = request.POST.get("company", "")
            person.notes = request.POST.get("notes", "")
            person.preferences = request.POST.get("preferences", "")
            person.services = request.POST.get("services", "")
            person.save()
        else:
            person.name = request.POST.get("name", "")
            person.phone = request.POST.get("phone", "")
            person.email = request.POST.get("email", "")
            person.role = request.POST.get("role", "")
            person.specialty = request.POST.get("specialty", "")
            person.notes = request.POST.get("notes", "")
            person.preferences = request.POST.get("preferences", "")
            person.services = request.POST.get("services", "")
            person.allow_multiple = request.POST.get("allow_multiple") == "on"
            person.available_days = request.POST.getlist("available_days")
            person.save()

        return redirect(f"/personas/?type={'clients' if type_param == 'client' else 'staff'}")

    # Renderizar con datos actuales
    return render(request, "bookings/person_form.html", {
        "type": type_param,
        "type_label": type_label,
        "is_edit": is_edit,
        "person": person,
        "week_days": week_days,
        "cancel_url": "/personas/",
    })
