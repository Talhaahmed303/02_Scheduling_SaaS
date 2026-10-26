from rest_framework import serializers
from .models import ProviderProfile, Service, WorkingHour, ScheduleOverride, Appointment, ReminderLog

class ServiceSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    provider_timezone = serializers.CharField(source='provider.timezone', read_only=True)

    class Meta:
        model = Service
        fields = [
            'id', 'provider', 'provider_name', 'provider_timezone',
            'name', 'slug', 'description', 'duration_minutes',
            'buffer_minutes', 'price', 'currency',
            'cancellation_notice_hours', 'is_active',
            'created_at', 'updated_at'
        ]


class WorkingHourSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkingHour
        fields = [
            'id', 'provider', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'break_start_time',
            'break_end_time', 'is_available'
        ]

    def get_day_name(self, obj):
        return dict(WorkingHour.DAY_CHOICES).get(obj.day_of_week, '')


class ScheduleOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleOverride
        fields = ['id', 'provider', 'date', 'is_unavailable', 'custom_start_time', 'custom_end_time', 'reason']


class ProviderProfileSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)
    working_hours = WorkingHourSerializer(many=True, read_only=True)
    overrides = ScheduleOverrideSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderProfile
        fields = [
            'id', 'name', 'slug', 'title', 'bio', 'email', 'phone',
            'timezone', 'avatar_url', 'is_active',
            'services', 'working_hours', 'overrides',
            'created_at', 'updated_at'
        ]


class ReminderLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderLog
        fields = [
            'id', 'appointment', 'channel', 'scheduled_for',
            'sent_at', 'status', 'recipient', 'subject',
            'payload_preview', 'created_at'
        ]


class AppointmentSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    duration_minutes = serializers.IntegerField(source='service.duration_minutes', read_only=True)
    reminders = ReminderLogSerializer(many=True, read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'provider', 'provider_name', 'service', 'service_name',
            'duration_minutes', 'customer_name', 'customer_email',
            'customer_phone', 'customer_notes', 'customer_timezone',
            'start_time', 'end_time', 'status', 'cancellation_reason',
            'meeting_link', 'version', 'reminders',
            'created_at', 'updated_at'
        ]


class AppointmentCreateSerializer(serializers.Serializer):
    provider_id = serializers.UUIDField()
    service_id = serializers.UUIDField()
    start_time = serializers.DateTimeField()
    customer_name = serializers.CharField(max_length=150)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    customer_notes = serializers.CharField(required=False, allow_blank=True)
    customer_timezone = serializers.CharField(max_length=50, default='UTC')


class AppointmentRescheduleSerializer(serializers.Serializer):
    new_start_time = serializers.DateTimeField()
    customer_timezone = serializers.CharField(max_length=50, default='UTC')


class AppointmentCancelSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class SlotItemSerializer(serializers.Serializer):
    start_time_utc = serializers.CharField()
    end_time_utc = serializers.CharField()
    start_time_provider = serializers.CharField()
    end_time_provider = serializers.CharField()
    start_time_client = serializers.CharField()
    end_time_client = serializers.CharField()
    display_time = serializers.CharField()
    display_label = serializers.CharField()
    client_display_label = serializers.CharField()
    duration_minutes = serializers.IntegerField()
    buffer_minutes = serializers.IntegerField()


class SlotAvailabilityResponseSerializer(serializers.Serializer):
    provider_id = serializers.UUIDField()
    service_id = serializers.UUIDField()
    date = serializers.CharField()
    client_timezone = serializers.CharField()
    slot_count = serializers.IntegerField()
    slots = SlotItemSerializer(many=True)


class DashboardMetricsResponseSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField()
    confirmed_appointments = serializers.IntegerField()
    upcoming_appointments = serializers.IntegerField()
    cancelled_appointments = serializers.IntegerField()
    completed_appointments = serializers.IntegerField()
    gross_revenue = serializers.FloatField()
    currency = serializers.CharField()
    active_providers = serializers.IntegerField()
    active_services = serializers.IntegerField()
    reminders_dispatched = serializers.IntegerField()
    generated_at = serializers.DateTimeField()

