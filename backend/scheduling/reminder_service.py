import datetime
import uuid
from django.utils import timezone
from .models import ReminderLog

class ReminderService:
    """
    Mock enterprise multi-channel notification dispatcher.
    Simulates production integration with Twilio (SMS), SendGrid/SES (Email),
    and CalDAV/Google Calendar (ICS invite).
    Records audit entries in ReminderLog.
    """

    @classmethod
    def dispatch_booking_notifications(cls, appointment):
        """Dispatches initial booking confirmation and schedules advance reminders."""
        logs = []
        now = timezone.now()

        # 1. Immediate Email Confirmation
        email_payload = {
            'provider': 'MockSendGridDispatcher_v3',
            'to': appointment.customer_email,
            'template_id': 'tpl_booking_confirmed_v1',
            'data': {
                'customer_name': appointment.customer_name,
                'service': appointment.service.name,
                'provider': appointment.provider.name,
                'start_time': appointment.start_time.isoformat(),
                'meeting_link': appointment.meeting_link,
            }
        }
        log_email = ReminderLog.objects.create(
            appointment=appointment,
            channel='EMAIL',
            scheduled_for=now,
            sent_at=now,
            status='DISPATCHED',
            recipient=appointment.customer_email,
            subject=f"Confirmed: {appointment.service.name} with {appointment.provider.name}",
            payload_preview=email_payload
        )
        logs.append(log_email)

        # 2. Calendar ICS Invite
        ics_payload = {
            'provider': 'MockCalDAV_Dispatcher',
            'uid': str(appointment.id),
            'method': 'REQUEST',
            'dtstart': appointment.start_time.isoformat(),
            'dtend': appointment.end_time.isoformat(),
            'summary': f"{appointment.service.name} - {appointment.provider.name}",
            'url': appointment.meeting_link,
        }
        log_ics = ReminderLog.objects.create(
            appointment=appointment,
            channel='CALENDAR_INVITE',
            scheduled_for=now,
            sent_at=now,
            status='DISPATCHED',
            recipient=appointment.customer_email,
            subject=f"Calendar Invitation: {appointment.service.name}",
            payload_preview=ics_payload
        )
        logs.append(log_ics)

        # 3. 24-Hour Advance SMS Reminder (simulated)
        if appointment.customer_phone:
            sms_scheduled = appointment.start_time - datetime.timedelta(hours=24)
            sms_payload = {
                'provider': 'MockTwilioSmsGateway',
                'to': appointment.customer_phone,
                'body': f"Reminder: Your session '{appointment.service.name}' with {appointment.provider.name} is scheduled for {appointment.start_time.strftime('%b %d at %I:%M %p UTC')}. Join link: {appointment.meeting_link}"
            }
            log_sms = ReminderLog.objects.create(
                appointment=appointment,
                channel='SMS',
                scheduled_for=max(now, sms_scheduled),
                sent_at=now if sms_scheduled <= now else None,
                status='DISPATCHED' if sms_scheduled <= now else 'QUEUED',
                recipient=appointment.customer_phone,
                subject=f"SMS 24h Reminder to {appointment.customer_phone}",
                payload_preview=sms_payload
            )
            logs.append(log_sms)

        return logs

    @classmethod
    def dispatch_cancellation_notification(cls, appointment, reason=''):
        now = timezone.now()
        payload = {
            'provider': 'MockSendGridDispatcher_v3',
            'to': appointment.customer_email,
            'template_id': 'tpl_booking_cancelled_v1',
            'data': {
                'customer_name': appointment.customer_name,
                'service': appointment.service.name,
                'cancelled_at': now.isoformat(),
                'reason': reason or 'Client requested cancellation'
            }
        }
        return ReminderLog.objects.create(
            appointment=appointment,
            channel='EMAIL',
            scheduled_for=now,
            sent_at=now,
            status='DISPATCHED',
            recipient=appointment.customer_email,
            subject=f"Cancelled: {appointment.service.name} with {appointment.provider.name}",
            payload_preview=payload
        )

    @classmethod
    def dispatch_reschedule_notification(cls, appointment, old_time):
        now = timezone.now()
        payload = {
            'provider': 'MockSendGridDispatcher_v3',
            'to': appointment.customer_email,
            'template_id': 'tpl_booking_rescheduled_v1',
            'data': {
                'customer_name': appointment.customer_name,
                'service': appointment.service.name,
                'old_time': old_time.isoformat(),
                'new_time': appointment.start_time.isoformat(),
                'meeting_link': appointment.meeting_link
            }
        }
        return ReminderLog.objects.create(
            appointment=appointment,
            channel='EMAIL',
            scheduled_for=now,
            sent_at=now,
            status='DISPATCHED',
            recipient=appointment.customer_email,
            subject=f"Rescheduled: {appointment.service.name} - New Time Confirmed",
            payload_preview=payload
        )
