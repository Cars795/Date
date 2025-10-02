from django.contrib import admin
from .models import (
    EventType, Event, Booking,
    Staff, Client, Appointment, AppointmentStatusHistory
)

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_minutes")
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "start", "capacity", "seats_taken")
    list_filter = ("type", "start")
    search_fields = ("title",)
    date_hierarchy = "start"
    ordering = ("-start",)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "event", "created_at", "cancelled")
    list_filter = ("cancelled", "created_at")
    search_fields = ("name", "email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "specialty")
    search_fields = ("name", "role", "specialty")
    ordering = ("name",)

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "email", "phone")
    ordering = ("name",)

class AppointmentStatusHistoryInline(admin.TabularInline):
    model = AppointmentStatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ("old_status", "new_status", "changed_at", "changed_by")
    ordering = ("-changed_at",)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "staff", "start", "status")
    list_filter = ("staff", "status", "start")
    search_fields = ("client__name", "staff__name", "notes")
    date_hierarchy = "start"
    ordering = ("-start",)
    list_select_related = ("client", "staff")
    raw_id_fields = ("client", "staff")
    list_per_page = 25
    inlines = [AppointmentStatusHistoryInline]

@admin.register(AppointmentStatusHistory)
class AppointmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("appointment", "old_status", "new_status", "changed_at", "changed_by")
    readonly_fields = ("changed_at",)
    list_filter = ("new_status", "old_status", "changed_at")
    date_hierarchy = "changed_at"
    search_fields = ("appointment__client__name", "appointment__staff__name")
    ordering = ("-changed_at",)
