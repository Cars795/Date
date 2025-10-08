"""
📘 Admin Panel — Vistas principales
----------------------------------
Incluye:
  • Dashboard general de eventos y reservas.
  • Creación y edición de eventos.
  • Listado y exportación de reservas (Excel).

Autor: El Cris 🔥
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, Count
from django import forms
import pandas as pd

from bookings.models import Event, Booking, EventType
from django.contrib.auth.decorators import login_required, user_passes_test


# ============================================================
# 🎟️ FORMULARIO DE EVENTOS
# ============================================================

class EventForm(forms.ModelForm):
    """Formulario administrativo básico para alta/edición de eventos."""

    class Meta:
        model = Event
        fields = [
            "type", "title", "description", "start", "capacity",
            "allow_group_booking", "max_tickets_per_booking"
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "start": forms.DateTimeInput(attrs={
                "class": "form-control", "type": "datetime-local"
            }),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "max_tickets_per_booking": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }


# ============================================================
# 🧭 DASHBOARD PRINCIPAL
# ============================================================

def dashboard(request):
    """
    Vista principal del panel:
      - Muestra todos los eventos creados.
      - Incluye KPIs de conteo general.
    """
    events = Event.objects.annotate(num_bookings=Count("bookings")).order_by("-start")
    total_bookings = Booking.objects.count()
    total_events = events.count()

    context = {
        "events": events,
        "total_bookings": total_bookings,
        "total_events": total_events,
    }
    return render(request, "admin_panel/dashboard.html", context)


# ============================================================
# ✏️ GESTIÓN DE EVENTOS
# ============================================================

def event_create(request):
    """
    Permite crear un nuevo evento desde el panel administrativo.
    """
    form = EventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "✅ Evento creado correctamente.")
        return redirect("admin_panel:dashboard")

    return render(request, "admin_panel/event_form.html", {
        "form": form,
        "action": "Nuevo evento"
    })


def event_edit(request, pk):
    """
    Permite editar un evento existente.
    """
    event = get_object_or_404(Event, pk=pk)
    form = EventForm(request.POST or None, instance=event)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "✅ Evento actualizado correctamente.")
        return redirect("admin_panel:dashboard")

    return render(request, "admin_panel/event_form.html", {
        "form": form,
        "action": "Editar evento"
    })


# ============================================================
# 📦 LISTADO DE RESERVAS + EXPORTACIÓN A EXCEL
# ============================================================

# @login_required(login_url="/admin/login/")
# @user_passes_test(lambda u: u.is_staff)
def booking_list(request):
    """
    Vista principal de reservas:
      - Permite buscar, filtrar y exportar.
      - Exporta en Excel con formato limpio y columnas autoajustadas.
    """
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "all")
    export = request.GET.get("export", "")

    # Base query optimizada
    bookings = Booking.objects.select_related("event").order_by("-created_at")

    # --- 🔍 Filtrado por texto libre ---
    if query:
        bookings = bookings.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(event__title__icontains=query)
        )

    # --- ⚙️ Filtrado por estado ---
    if status_filter == "active":
        bookings = bookings.filter(cancelled=False)
    elif status_filter == "cancelled":
        bookings = bookings.filter(cancelled=True)

    # --- 📊 Totales para KPIs ---
    total = bookings.count()
    total_active = bookings.filter(cancelled=False).count()
    total_cancelled = bookings.filter(cancelled=True).count()

    # ============================================================
    # 📤 EXPORTACIÓN A EXCEL
    # ============================================================
    if export == "excel":
        df = pd.DataFrame(list(bookings.values(
            "event__title", "name", "email", "phone", "quantity",
            "created_at", "cancelled"
        )))

        # --- Renombrar columnas ---
        df.rename(columns={
            "event__title": "Evento",
            "name": "Nombre",
            "email": "Correo",
            "phone": "Teléfono",
            "quantity": "Cantidad",
            "created_at": "Fecha de creación",
            "cancelled": "Cancelada",
        }, inplace=True)

        # --- Normalización de datos ---
        if "Fecha de creación" in df.columns:
            df["Fecha de creación"] = (
                pd.to_datetime(df["Fecha de creación"], errors="coerce")
                .dt.tz_localize(None)
                .dt.strftime("%d/%m/%Y %H:%M")
            )
        df["Cancelada"] = df["Cancelada"].apply(lambda x: "Sí" if x else "No")

        # --- Configurar respuesta ---
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="reservas_filtradas.xlsx"'

        # --- Escritura con formato dinámico ---
        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Reservas")
            sheet = writer.sheets["Reservas"]

            # Ancho automático de columnas
            for col in sheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except Exception:
                        pass
                sheet.column_dimensions[column].width = max_length + 3

        return response

    # ============================================================
    # 🧭 Render del listado normal
    # ============================================================
    context = {
        "bookings": bookings,
        "query": query,
        "status_filter": status_filter,
        "total": total,
        "total_active": total_active,
        "total_cancelled": total_cancelled,
    }
    return render(request, "admin_panel/booking_list.html", context)
