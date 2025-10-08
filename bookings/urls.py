"""
URL Configuration for the 'bookings' app.
-----------------------------------------
Contiene todas las rutas públicas y funcionales del módulo de:
- Reservas y eventos
- Agenda interna
- Gestión de personas (clientes y staff)
"""

from django.urls import path
from . import views, views_appointments, views_persons

# Nombre de espacio para el módulo
app_name = "bookings"

urlpatterns = [
    # ==========================
    # 🏠 Página principal
    # ==========================
    path("", views.home, name="home"),

    # ==========================
    # 🎫 Eventos públicos
    # ==========================
    path("eventos/", views.EventListView.as_view(), name="event_list"),
    path("event/<int:pk>/", views.event_detail, name="event_detail"),
    path("booking/success/<uuid:code>/", views.booking_success, name="booking_success"),
    path("booking/pdf/<uuid:code>/", views.booking_ticket_pdf, name="booking_ticket_pdf"),

    # ==========================
    # 🗓️ Agenda interna
    # ==========================
    path("agenda/", views_appointments.agenda, name="agenda"),
    path("agenda/semanal/", views_appointments.agenda_semanal, name="agenda_semanal"),

    # Citas (CRUD)
    path("appointment/new/", views_appointments.create_appointment, name="create_appointment"),
    path("appointment/<int:pk>/edit/", views_appointments.edit_appointment, name="edit_appointment"),
    path("appointment/<int:pk>/delete/", views_appointments.delete_appointment, name="delete_appointment"),
    path("appointment/<int:pk>/status/<str:status>/", views_appointments.change_appointment_status, name="change_appointment_status"),

    # ==========================
    # 👥 Personas (Clientes / Staff)
    # ==========================
    path("personas/", views_persons.person_list, name="person_list"),
    path("personas/nueva/", views_persons.person_form, name="person_form"),
 
    path("personas/<int:pk>/editar/", views_persons.person_edit, name="person_edit"),

]
