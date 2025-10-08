from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("events/new/", views.event_create, name="event_create"),
    path("events/<int:pk>/edit/", views.event_edit, name="event_edit"),
    path("bookings/", views.booking_list, name="booking_list"),
]
