
# python scripts/seed_monthly_events.py 2025
# o sin año -> usa año actual
# python scripts/seed_monthly_events.py

# scripts/seed_monthly_events.py
import os
import sys
from pathlib import Path

# === Asegurar que el root del proyecto esté en sys.path ===
BASE_DIR = Path(__file__).resolve().parents[1]  # carpeta que contiene manage.py
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# === DJANGO_SETTINGS_MODULE ===
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "date_site.settings")
#    ^ ajusta si tu paquete de settings se llama distinto

import django
django.setup()

from datetime import datetime
from django.utils import timezone
from bookings.models import Event, EventType

def ensure_event_type(name="General", duration_minutes=60):
    et, _ = EventType.objects.get_or_create(
        name=name, defaults={"duration_minutes": duration_minutes}
    )
    return et

def seed_year(year: int, tzaware=True):
    etype = ensure_event_type("Mensual", 90)
    titles = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
              "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    created, skipped = 0, 0
    for i, t in enumerate(titles, start=1):
        # Día 15 a las 19:00
        naive = datetime(year, i, 15, 19, 0)
        dt = timezone.make_aware(naive) if tzaware else naive

        # Idempotente: no duplicar si ya existe mismo título o misma fecha
        if Event.objects.filter(start=dt).exists() or Event.objects.filter(title=f"Encuentro {t} {year}").exists():
            skipped += 1
            continue

        Event.objects.create(
            title=f"Encuentro {t} {year}",
            type=etype,
            start=dt,
            capacity=100,
            description=f"Evento mensual de {t} {year}",
        )
        created += 1

    print(f"Año {year}: creados {created}, omitidos {skipped}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed de eventos mensuales")
    parser.add_argument("year", type=int, nargs="?", help="Año (ej. 2025)")
    args = parser.parse_args()

    if not args.year:
        from datetime import date
        args.year = date.today().year

    seed_year(args.year)
