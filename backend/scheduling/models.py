import uuid
from django.db import models
from django.utils import timezone

class ProviderProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    title = models.CharField(max_length=200, help_text="Professional designation e.g. Principal Cloud Architect")
    bio = models.TextField(blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)
    timezone = models.CharField(max_length=50, default='UTC', help_text="Standard IANA Timezone e.g. America/New_York, UTC, Asia/Karachi")
    avatar_url = models.URLField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Provider Profile'
        verbose_name_plural = 'Provider Profiles'

    def __str__(self):
        return f"{self.name} ({self.title}) - [{self.timezone}]"


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Duration of session in minutes")
    buffer_minutes = models.PositiveIntegerField(default=15, help_text="Cool-down buffer required after session")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='USD')
    cancellation_notice_hours = models.PositiveIntegerField(
        default=24,
        help_text="Minimum advance notice required to reschedule or cancel without penalty"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['provider', 'name']
        unique_together = ('provider', 'slug')

    def __str__(self):
        return f"{self.name} ({self.duration_minutes}m) - {self.provider.name}"


class WorkingHour(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='working_hours')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField(default='09:00:00', help_text="Start of business hours in provider timezone")
    end_time = models.TimeField(default='17:00:00', help_text="End of business hours in provider timezone")
    break_start_time = models.TimeField(null=True, blank=True, help_text="Daily break start (optional)")
    break_end_time = models.TimeField(null=True, blank=True, help_text="Daily break end (optional)")
    is_available = models.BooleanField(default=True, help_text="False if day is off (e.g. weekend)")

    class Meta:
        ordering = ['provider', 'day_of_week']
        unique_together = ('provider', 'day_of_week')

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, 'Unknown')
        status = f"{self.start_time} - {self.end_time}" if self.is_available else "OFF"
        return f"{self.provider.name} | {day_name}: {status}"


class ScheduleOverride(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='overrides')
    date = models.DateField(help_text="Specific calendar date for override")
    is_unavailable = models.BooleanField(default=True, help_text="True if entirely unavailable (holiday/sick)")
    custom_start_time = models.TimeField(null=True, blank=True)
    custom_end_time = models.TimeField(null=True, blank=True)
    reason = models.CharField(max_length=200, blank=True, default='Holiday / Personal Time Off')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        unique_together = ('provider', 'date')

    def __str__(self):
        return f"{self.provider.name} override on {self.date}: {self.reason}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Confirmation'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments')
    customer_name = models.CharField(max_length=150)
    customer_email = models.EmailField(db_index=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    customer_notes = models.TextField(blank=True)
    customer_timezone = models.CharField(max_length=50, default='UTC')
    start_time = models.DateTimeField(db_index=True, help_text="Canonical UTC start timestamp")
    end_time = models.DateTimeField(db_index=True, help_text="Canonical UTC end timestamp")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED', db_index=True)
    cancellation_reason = models.TextField(blank=True)
    rescheduled_from = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='rescheduled_to')
    rescheduled_at = models.DateTimeField(null=True, blank=True)
    meeting_link = models.CharField(max_length=255, blank=True)
    version = models.PositiveIntegerField(default=1, help_text="Optimistic concurrency locking version")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['provider', 'start_time', 'end_time', 'status']),
            models.Index(fields=['customer_email', 'status']),
        ]

    def __str__(self):
        return f"Apt #{str(self.id)[:8]} | {self.customer_name} w/ {self.provider.name} [{self.status}]"


class ReminderLog(models.Model):
    CHANNEL_CHOICES = [
        ('EMAIL', 'Email Notification'),
        ('SMS', 'SMS Text Alert'),
        ('CALENDAR_INVITE', 'Calendar ICS Dispatch'),
    ]
    STATUS_CHOICES = [
        ('QUEUED', 'Queued in Dispatch Buffer'),
        ('DISPATCHED', 'Dispatched Successfully'),
        ('FAILED', 'Dispatch Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='reminders')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='EMAIL')
    scheduled_for = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DISPATCHED')
    recipient = models.CharField(max_length=150)
    subject = models.CharField(max_length=255)
    payload_preview = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reminder [{self.channel}] to {self.recipient} - {self.status}"
