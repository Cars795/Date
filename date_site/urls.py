"""
URL principal del proyecto Django 'date_site'.
---------------------------------------------
Integra las rutas del sitio público (bookings),
el panel administrativo y el admin clásico de Django.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 🔧 Admin nativo de Django
    path("admin/", admin.site.urls),

    # 🌐 Sitio público (eventos, agenda, reservas)
    path("", include("bookings.urls")),

    # 🧩 Panel de administración visual (creación de eventos, reservas, métricas)
    path("panel/", include("bookings.admin_panel.urls")),
]
