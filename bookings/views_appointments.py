from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.timezone import now
from .models import Staff, Appointment   # 👈 import the models you use
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from datetime import date, timedelta
from collections import defaultdict
from .forms import AppointmentForm
import calendar
import locale
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # en Linux/mac
from django.db.models import Count, Q  # 👈 arriba del archivo
from datetime import datetime
from django.db.models import Prefetch, Q


def agenda(request):
    today = now().date()
    staff_list = Staff.objects.all()
    return render(request, "bookings/agenda.html", {
        "today": today,
        "staff_list": staff_list,
    })


def agenda_semanal(request):
    base_date_str = request.GET.get("date")  # fecha de referencia opcional (YYYY-MM-DD)

    view_type = request.GET.get("view", "week")  # por defecto "week"
    today = now().date()

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
                "name": calendar.month_name[m],
                "count": agg["total"] or 0,
                "pending": agg["pending"] or 0,
                "confirmed": agg["confirmed"] or 0,
                "cancelled": agg["cancelled"] or 0,
                "done": agg["done"] or 0,
            })

        context = {"view": "year", "year": year, "months": months, "today": today}
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

    elif view_type == "day":
        # 1) Fecha seleccionada (o hoy)
        day_str = request.GET.get("date", today.isoformat())
        selected = date.fromisoformat(day_str)

        # 2) Prefetch SOLAMENTE las citas del día para cada staff
        todays_appointments = Appointment.objects.filter(start__date=selected).select_related("client", "staff")
        staff_list = Staff.objects.prefetch_related(
            Prefetch("appointment_set", queryset=todays_appointments.order_by("start"))
        )

        # 3) (Opcional) Lista plana de citas si la quieres para otros usos
        citas = todays_appointments

        # 4) Contadores por staff: atendidas (done) de totales (del día)
        staff_counters = {}
        for s in staff_list:
            total = s.appointment_set.all().count()
            done = sum(1 for a in s.appointment_set.all() if a.status == "done")
            staff_counters[s.id] = {"done": done, "total": total}

        # 5) Contexto para la plantilla
        context = {
            "view": "day",
            "day": selected,
            "today": today,
            "staff_list": staff_list,
            "citas": citas,              # por si la plantilla lo usa en otros lados
            "staff_counters": staff_counters,  # <- usado por el badge “5 de 7”
        }
    else:  # week
        offset = int(request.GET.get("week", 0))
        start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
        days = [start_of_week + timedelta(days=i) for i in range(7)]
        appointments = Appointment.objects.filter(start__date__range=[days[0], days[-1]])

        # agrupamos por día/hora
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





from django.shortcuts import get_object_or_404, redirect, render
from .models import Appointment
from .forms import AppointmentForm
from datetime import datetime

def create_appointment(request):
    from .forms import AppointmentForm
    cancel_url = _safe_next(request)  # antes de cualquier return

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(cancel_url)  # vuelve a donde venías
    else:
        initial = {}
        if "date" in request.GET:
            initial["start"] = request.GET["date"]
        form = AppointmentForm(initial=initial)

    return render(request, "bookings/appointment_form.html", {
        "form": form,
        "is_edit": False,
        "cancel_url": cancel_url,
    })

def edit_appointment(request, pk):
    from .forms import AppointmentForm
    apt = get_object_or_404(Appointment, pk=pk)
    cancel_url = _safe_next(request)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=apt)
        if form.is_valid():
            form.save()
            return redirect(cancel_url)
    else:
        form = AppointmentForm(instance=apt)

    return render(request, "bookings/appointment_form.html", {
        "form": form,
        "is_edit": True,
        "cancel_url": cancel_url,
    })

# (opcional) eliminar con confirmación simple
def delete_appointment(request, pk):
    next_url = request.GET.get("next") or request.POST.get("next")
    apt = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        apt.delete()
        return redirect(next_url or "bookings:agenda_semanal")
    return render(request, "bookings/appointment_confirm_delete.html", {"appointment": apt, "next": next_url})




from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseBadRequest, HttpResponse
from django.urls import reverse
from django.utils.timezone import now

from .models import Appointment, AppointmentStatusHistory  # 👈 importa el historial

ALLOWED = {
    "pending":   {"confirmed", "cancelled"},
    "confirmed": {"pending", "cancelled", "done"},
    "cancelled": {"pending"},
    "done":      set(),
}


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

    # 📝 guardar historial
    AppointmentStatusHistory.objects.create(
        appointment=apt,
        old_status=old,
        new_status=new,
        changed_by=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
    )

    # respuesta: si viene de fetch (AJAX) no navegamos
    if request.headers.get("X-Requested-With") == "fetch":
        return HttpResponse(status=204)

    # si fue navegación normal, regresamos a donde estaba
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or reverse("bookings:agenda_semanal")
    return redirect(next_url)

# al inicio del archivo
from django.urls import reverse

def _safe_next(request, fallback_name="bookings:agenda_semanal"):
    """
    Devuelve la URL a la que volver:
    - ?next=... (GET o POST)
    - HTTP_REFERER (si viene)
    - reverse(fallback_name)
    """
    return (
        request.GET.get("next")
        or request.POST.get("next")
        or request.META.get("HTTP_REFERER")
        or reverse(fallback_name)
    )
