from django.contrib import admin
from .models import ProviderProfile, Service, WorkingHour, ScheduleOverride, Appointment, ReminderLog

@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'timezone', 'email', 'is_active', 'created_at')
    search_fields = ('name', 'email', 'title')
    list_filter = ('is_active', 'timezone')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'duration_minutes', 'buffer_minutes', 'price', 'currency', 'is_active')
    search_fields = ('name', 'provider__name')
    list_filter = ('is_active', 'provider')

@admin.register(WorkingHour)
class WorkingHourAdmin(admin.ModelAdmin):
    list_display = ('provider', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available')

@admin.register(ScheduleOverride)
class ScheduleOverrideAdmin(admin.ModelAdmin):
    list_display = ('provider', 'date', 'is_unavailable', 'reason')
    list_filter = ('is_unavailable', 'date')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'provider', 'service', 'start_time', 'end_time', 'status', 'version')
    search_fields = ('customer_name', 'customer_email', 'meeting_link')
    list_filter = ('status', 'provider', 'service')

@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'channel', 'status', 'scheduled_for', 'sent_at', 'subject')
    list_filter = ('channel', 'status')
