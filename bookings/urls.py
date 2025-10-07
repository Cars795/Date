from django.urls import path
from . import views, views_appointments

app_name = 'bookings'

urlpatterns = [
    path("", views.home, name="home"),
    # Eventos públicos
    path("eventos/", views.EventListView.as_view(), name="event_list"),
    path("event/<int:pk>/", views.event_detail, name="event_detail"),
    path("booking/success/<uuid:code>/", views.booking_success, name="booking_success"),
    # Agenda interna
    path("agenda/", views_appointments.agenda, name="agenda"),
    path("appointment/new/", views_appointments.create_appointment, name="create_appointment"),
    path("appointment/<int:pk>/status/<str:status>/", views_appointments.change_appointment_status, name="change_appointment_status"),
    path("agenda/semanal/", views_appointments.agenda_semanal, name="agenda_semanal"),
    
 
 
    path("appointment/new/", views_appointments.create_appointment, name="create_appointment"),
    path("appointment/<int:pk>/edit/", views_appointments.edit_appointment, name="edit_appointment"),
    path("appointment/<int:pk>/delete/", views_appointments.delete_appointment, name="delete_appointment"),  # opcional
    path("appointment/<int:pk>/status/<str:status>/", views_appointments.change_appointment_status, name="change_appointment_status"),

    # 👉 agrega esta línea para el PDF:
    path("booking/pdf/<uuid:code>/", views.booking_ticket_pdf, name="booking_ticket_pdf"),
]