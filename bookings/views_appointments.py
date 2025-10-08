# bookings/views_appointments.py

from datetime import date, datetime, timedelta
import calendar
from collections import defaultdict
from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timezone import now, get_current_timezone, make_aware
from .models import Staff, Appointment, AppointmentStatusHistory
from .forms import AppointmentForm

# ---- Opcional: locale (evitar crash en Windows) ----
import locale
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Linux/Mac
except locale.Error:
    try:
        # Windows: intenta alguna variante española común
        locale.setlocale(locale.LC_TIME, "Spanish_Mexico")
    except locale.Error:
        pass  # usa locale por defecto

# ---- Reglas de transición de estado ----
ALLOWED = {
    "pending":   {"confirmed", "cancelled"},
    "confirmed": {"pending", "cancelled", "done"},
    "cancelled": {"pending"},
    "done":      set(),
}

# ---- Helper: a dónde regresar después de crear/editar/accionar ----
def _resolve_next(request, fallback_name="bookings:agenda_semanal"):
    return (
        request.GET.get("next")
        or request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse(fallback_name)
    )

# =======================
# VISTA SIMPLE: AGENDA
# =======================
from datetime import date
from django.utils.timezone import now
from django.db.models import Prefetch
from django.shortcuts import render
from .models import Appointment, Staff  # Ajusta los imports a tus modelos reales


def agenda(request):
    """Tablero diario de citas — versión optimizada e interiorista digital."""

    # --- Día seleccionado: ?date=YYYY-MM-DD o hoy ---
    today = now().date()
    day_str = request.GET.get("date")
    try:
        selected_day = date.fromisoformat(day_str) if day_str else today
    except ValueError:
        selected_day = today

    # --- Solo citas del día seleccionado ---
    todays_appointments = Appointment.objects.filter(
        start__date=selected_day
    ).select_related("client", "staff").order_by("start")

    # --- Staff + Prefetch de citas del día ---
    staff_list = Staff.objects.prefetch_related(
        Prefetch("appointment_set", queryset=todays_appointments)
    )

    # --- Contadores por staff ---
    staff_counters = {}
    for s in staff_list:
        total = s.appointment_set.all().count()
        done = sum(1 for a in s.appointment_set.all() if a.status == "done")
        staff_counters[s.id] = {"done": done, "total": total}

    # --- 📊 Estadísticas globales del día (para el panel lateral) ---
    stats = {
        "pending": todays_appointments.filter(status="pending").count(),
        "confirmed": todays_appointments.filter(status="confirmed").count(),
        "cancelled": todays_appointments.filter(status="cancelled").count(),
        "done": todays_appointments.filter(status="done").count(),
    }

    # --- Render final ---
    return render(request, "bookings/agenda.html", {
        "today": today,
        "day": selected_day,
        "staff_list": staff_list,
        "staff_counters": staff_counters,
        "stats": stats,  # 👈 ahora alimenta el panel lateral
    })


# ====================================
# VISTA UNIFICADA: AÑO / MES / SEMANA / DÍA
# ====================================
def agenda_semanal(request):
    view_type = request.GET.get("view", "week")
    today = now().date()

    # ----- AÑO -----
    if view_type == "year":
        year = int(request.GET.get("year", today.year))
        months = []
        for m in range(1, 13):
            first_day = date(year, m, 1)
            _, last_day = calendar.monthrange(year, m)
            last_date = date(year, m, last_day)

            qs = Appointment.objects.filter(start__date__range=[first_day, last_date])
            agg = qs.aggregate(
                total=Count("id"),
                pending=Count("id", filter=Q(status="pending")),
                confirmed=Count("id", filter=Q(status="confirmed")),
                cancelled=Count("id", filter=Q(status="cancelled")),
                done=Count("id", filter=Q(status="done")),
            )

            months.append({
                "year": year,
                "month": m,
                "name": calendar.month_name[m],  # Nombre del mes (puede salir en inglés según locale)
                "count": agg["total"] or 0,
            })

        context = {"view": "year", "year": year, "months": months, "today": today}

    # ----- MES -----
    elif view_type == "month":
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))
        first_day = date(year, month, 1)

        # total de días del mes
        _, last_day = calendar.monthrange(year, month)
        days = [first_day + timedelta(days=i) for i in range(last_day)]

        # calcular mes anterior y siguiente
        prev_month = (first_day - timedelta(days=1)).replace(day=1)
        next_month = (first_day + timedelta(days=32)).replace(day=1)

        citas = Appointment.objects.filter(start__date__range=[days[0], days[-1]])

        context = {
            "view": "month",
            "year": year,
            "month": month,
            "month_name": calendar.month_name[month],
            "days": days,
            "citas": citas,
            "today": today,
            "prev_month": prev_month,
            "next_month": next_month,
        }

    # ----- DÍA -----
    elif view_type == "day":
        # Fecha seleccionada (o hoy)
        day_str = request.GET.get("date", today.isoformat())
        selected = date.fromisoformat(day_str)

        # Prefetch SOLO citas del día para cada staff
        todays_appointments = Appointment.objects.filter(
            start__date=selected
        ).select_related("client", "staff").order_by("start")

        staff_list = Staff.objects.prefetch_related(
            Prefetch("appointment_set", queryset=todays_appointments)
        )

        # Contadores por staff (done de totales)
        staff_counters = {}
        for s in staff_list:
            total = s.appointment_set.all().count()
            done = sum(1 for a in s.appointment_set.all() if a.status == "done")
            staff_counters[s.id] = {"done": done, "total": total}

        context = {
            "view": "day",
            "day": selected,
            "today": today,
            "staff_list": staff_list,
            "citas": todays_appointments,
            "staff_counters": staff_counters,
        }

    # ----- SEMANA (default) -----
    else:
        # Permite “sincronizar” semana con un mes/día elegido
        # Si viene ?date=YYYY-MM-DD lo usamos como ancla, si no: hoy.
        anchor_str = request.GET.get("date")
        anchor = date.fromisoformat(anchor_str) if anchor_str else today

        offset = int(request.GET.get("week", 0))
        start_of_week = (anchor - timedelta(days=anchor.weekday())) + timedelta(weeks=offset)
        days = [start_of_week + timedelta(days=i) for i in range(7)]

        appointments = Appointment.objects.filter(start__date__range=[days[0], days[-1]]).select_related("client")

        # Agrupar por día/hora
        citas_por_dia_hora = defaultdict(lambda: defaultdict(list))
        for a in appointments:
            citas_por_dia_hora[a.start.date()][a.start.hour].append(a)

        hours = list(range(8, 21))
        context = {
            "view": "week",
            "days": days,
            "hours": hours,
            "citas_por_dia_hora": citas_por_dia_hora,
            "offset": offset,
            "today": today,
        }

    return render(request, "bookings/agenda_semanal.html", context)

# =======================
# CREAR / EDITAR / ELIMINAR
# =======================
def create_appointment(request):
    next_url = _resolve_next(request)

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(next_url)
    else:
        initial = {}
        # Soporta ?date=YYYY-MM-DD o YYYY-MM-DDTHH:MM / :SS
        date_str = request.GET.get("date")
        if date_str:
            tz = get_current_timezone()
            for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    if fmt == "%Y-%m-%d":
                        dt = dt.replace(hour=9, minute=0)  # hora por defecto
                    initial["start"] = make_aware(dt, tz)
                    break
                except ValueError:
                    pass
        form = AppointmentForm(initial=initial)

    return render(
        request,
        "bookings/appointment_form.html",
        {"form": form, "is_edit": False, "cancel_url": next_url},
    )

def edit_appointment(request, pk):
    apt = get_object_or_404(Appointment, pk=pk)  # <-- corrige el typo: Appointment
    next_url = _resolve_next(request)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=apt)
        if form.is_valid():
            form.save()
            return redirect(next_url)
    else:
        form = AppointmentForm(instance=apt)

    return render(
        request,
        "bookings/appointment_form.html",
        {"form": form, "is_edit": True, "cancel_url": next_url},
    )

def delete_appointment(request, pk):
    next_url = _resolve_next(request)
    apt = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        apt.delete()
        return redirect(next_url)
    return render(request, "bookings/appointment_confirm_delete.html", {"appointment": apt, "next": next_url})

# =======================
# CAMBIO DE ESTADO (con historial)
# =======================
def change_appointment_status(request, pk, status):
    apt = get_object_or_404(Appointment, pk=pk)
    old, new = apt.status, status

    # reglas de negocio
    if new == "pending" and apt.start <= now():
        return HttpResponseBadRequest("No se puede volver a pendiente una cita pasada.")
    if old == "done" and new != "done":
        return HttpResponseBadRequest("No se puede modificar una cita atendida.")
    if new not in ALLOWED.get(old, set()):
        return HttpResponseBadRequest("Transición de estado no permitida.")

    # aplicar cambio
    apt.status = new
    apt.save()

    # historial
    AppointmentStatusHistory.objects.create(
        appointment=apt,
        old_status=old,
        new_status=new,
        changed_by=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
    )

    # Si es fetch (AJAX) no navegamos
    if request.headers.get("X-Requested-With") == "fetch":
        return HttpResponse(status=204)

    # Navegación normal
    next_url = _resolve_next(request)
    return redirect(next_url)
