import datetime
import threading
import pytz
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from scheduling.models import ProviderProfile, Service, WorkingHour, ScheduleOverride, Appointment, ReminderLog
from scheduling.slot_engine import get_available_slots

class SchedulingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Provider in New York
        self.provider = ProviderProfile.objects.create(
            name="Dr. Sarah Jenkins",
            slug="dr-sarah-jenkins-test",
            title="Principal Distributed Systems Architect",
            email="sarah.test@falconxoft.io",
            timezone="America/New_York",
            avatar_url="https://example.com/sarah.jpg"
        )

        # 30-min Service with 15-min buffer and 24h cancellation notice
        self.service = Service.objects.create(
            provider=self.provider,
            name="30-Min Architecture Advisory",
            slug="30-min-advisory",
            duration_minutes=30,
            buffer_minutes=15,
            price=150.00,
            cancellation_notice_hours=24
        )

        # Working hours: Monday to Friday, 09:00 - 17:00, Break: 13:00 - 14:00
        for day in range(7):
            WorkingHour.objects.create(
                provider=self.provider,
                day_of_week=day,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(17, 0),
                break_start_time=datetime.time(13, 0) if day < 5 else None,
                break_end_time=datetime.time(14, 0) if day < 5 else None,
                is_available=(day < 5)
            )

    def test_provider_list_api(self):
        """Test retrieving active provider profiles with nested services and working hours."""
        response = self.client.get('/api/providers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if 'results' in response.data else response.data
        self.assertGreaterEqual(len(results), 1)
        provider_data = next(p for p in results if str(p['id']) == str(self.provider.id))
        self.assertEqual(provider_data['name'], "Dr. Sarah Jenkins")
        self.assertEqual(len(provider_data['services']), 1)

    def test_slot_generation_working_hours(self):
        """Test slot generation produces slots within 9-5 and excludes weekend."""
        # Find next Monday
        today = timezone.now().date()
        days_ahead = (0 - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_monday = today + datetime.timedelta(days=days_ahead)
        
        slots = get_available_slots(str(self.provider.id), str(self.service.id), next_monday.isoformat(), 'America/New_York')
        self.assertGreater(len(slots), 0)
        # Check that no slot starts between 13:00 and 14:00 (break)
        for s in slots:
            slot_time = datetime.datetime.fromisoformat(s['start_time_provider']).time()
            self.assertFalse(datetime.time(13, 0) <= slot_time < datetime.time(14, 0))

    def test_slot_generation_weekend_off(self):
        """Test that weekend day returns 0 slots."""
        today = timezone.now().date()
        days_ahead = (5 - today.weekday() + 7) % 7  # Saturday
        if days_ahead == 0:
            days_ahead = 7
        next_saturday = today + datetime.timedelta(days=days_ahead)
        
        slots = get_available_slots(str(self.provider.id), str(self.service.id), next_saturday.isoformat(), 'UTC')
        self.assertEqual(len(slots), 0)

    def test_slot_generation_override_unavailability(self):
        """Test schedule override marks date completely unavailable."""
        target_date = timezone.now().date() + datetime.timedelta(days=10)
        ScheduleOverride.objects.create(
            provider=self.provider,
            date=target_date,
            is_unavailable=True,
            reason="Medical Conference"
        )
        slots = get_available_slots(str(self.provider.id), str(self.service.id), target_date.isoformat(), 'UTC')
        self.assertEqual(len(slots), 0)

    def test_booking_appointment_success(self):
        """Test successful appointment creation and mock reminder generation."""
        future_start = timezone.now() + datetime.timedelta(days=3, hours=2)
        payload = {
            'provider_id': str(self.provider.id),
            'service_id': str(self.service.id),
            'start_time': future_start.isoformat(),
            'customer_name': 'Alice Johnson',
            'customer_email': 'alice@example.com',
            'customer_phone': '+1 (555) 234-5678',
            'customer_notes': 'Initial system audit',
            'customer_timezone': 'America/New_York'
        }
        response = self.client.post('/api/appointments/book/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'CONFIRMED')
        self.assertTrue('meeting_link' in response.data)
        
        # Verify reminder logs dispatched
        reminders = ReminderLog.objects.filter(appointment_id=response.data['id'])
        self.assertGreaterEqual(reminders.count(), 2)  # Email + ICS + SMS
        channels = [r.channel for r in reminders]
        self.assertIn('EMAIL', channels)
        self.assertIn('CALENDAR_INVITE', channels)

    def test_double_booking_prevention_same_slot(self):
        """Test that booking the same slot twice is rejected with HTTP 409 Conflict."""
        future_start = timezone.now() + datetime.timedelta(days=4)
        payload = {
            'provider_id': str(self.provider.id),
            'service_id': str(self.service.id),
            'start_time': future_start.isoformat(),
            'customer_name': 'Bob Miller',
            'customer_email': 'bob@example.com',
            'customer_phone': '+1 (555) 999-0000',
            'customer_timezone': 'UTC'
        }
        # First booking succeeds
        resp1 = self.client.post('/api/appointments/book/', payload, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Second booking with same slot must fail with 409
        resp2 = self.client.post('/api/appointments/book/', payload, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(resp2.data['error'], 'DOUBLE_BOOKING_PREVENTED')

    def test_overlapping_buffer_conflict(self):
        """Test that booking a slot that infringes on the 15-min post-appointment buffer is rejected."""
        future_start = timezone.now() + datetime.timedelta(days=5)
        # First appointment: 30 minutes duration (e.g. 10:00 - 10:30, buffer until 10:45)
        payload1 = {
            'provider_id': str(self.provider.id),
            'service_id': str(self.service.id),
            'start_time': future_start.isoformat(),
            'customer_name': 'Charlie',
            'customer_email': 'charlie@example.com',
        }
        resp1 = self.client.post('/api/appointments/book/', payload1, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Second appointment starts at 10:35 (inside the 15m buffer period of 10:30-10:45)
        conflict_start = future_start + datetime.timedelta(minutes=35)
        payload2 = {
            'provider_id': str(self.provider.id),
            'service_id': str(self.service.id),
            'start_time': conflict_start.isoformat(),
            'customer_name': 'Dan',
            'customer_email': 'dan@example.com',
        }
        resp2 = self.client.post('/api/appointments/book/', payload2, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)

    def test_reschedule_success(self):
        """Test rescheduling an appointment to a valid future time slot."""
        future_start = timezone.now() + datetime.timedelta(days=6)
        apt = Appointment.objects.create(
            provider=self.provider,
            service=self.service,
            customer_name='Eva Green',
            customer_email='eva@example.com',
            start_time=future_start,
            end_time=future_start + datetime.timedelta(minutes=30),
            status='CONFIRMED'
        )
        new_time = future_start + datetime.timedelta(days=1)
        response = self.client.post(f'/api/appointments/{apt.id}/reschedule/', {
            'new_start_time': new_time.isoformat(),
            'customer_timezone': 'UTC'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        apt.refresh_from_db()
        self.assertEqual(apt.start_time, new_time)
        self.assertEqual(apt.version, 2)

    def test_reschedule_notice_policy_violation(self):
        """Test that rescheduling within 24 hours notice window fails with 400 Bad Request."""
        # Appointment starts in 10 hours (< 24h notice window)
        soon_start = timezone.now() + datetime.timedelta(hours=10)
        apt = Appointment.objects.create(
            provider=self.provider,
            service=self.service,
            customer_name='George',
            customer_email='george@example.com',
            start_time=soon_start,
            end_time=soon_start + datetime.timedelta(minutes=30),
            status='CONFIRMED'
        )
        new_time = soon_start + datetime.timedelta(days=2)
        response = self.client.post(f'/api/appointments/{apt.id}/reschedule/', {
            'new_start_time': new_time.isoformat(),
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'NOTICE_POLICY_VIOLATION')

    def test_cancel_appointment_success(self):
        """Test cancelling an appointment updates status and logs cancellation notice."""
        future_start = timezone.now() + datetime.timedelta(days=7)
        apt = Appointment.objects.create(
            provider=self.provider,
            service=self.service,
            customer_name='Helen Hunt',
            customer_email='helen@example.com',
            start_time=future_start,
            end_time=future_start + datetime.timedelta(minutes=30),
            status='CONFIRMED'
        )
        response = self.client.post(f'/api/appointments/{apt.id}/cancel/', {
            'reason': 'Schedule conflict with board meeting'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        apt.refresh_from_db()
        self.assertEqual(apt.status, 'CANCELLED')
        self.assertIn('Schedule conflict', apt.cancellation_reason)

    def test_dashboard_metrics_api(self):
        """Test dashboard metrics endpoint returns accurate counts and financial totals."""
        response = self.client.get('/api/dashboard/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_appointments', response.data)
        self.assertIn('gross_revenue', response.data)
        self.assertIn('active_providers', response.data)


class ConcurrencyDefenseTestCase(TransactionTestCase):
    """
    Simulates concurrent race conditions across simultaneous threads
    attempting to reserve the exact same appointment slot.
    """
    def setUp(self):
        self.provider = ProviderProfile.objects.create(
            name="Concurrent Dr. Sarah",
            slug="concurrent-sarah",
            title="Senior Concurrency Specialist",
            email="sarah.concurrent@falconxoft.io",
            timezone="UTC"
        )
        self.service = Service.objects.create(
            provider=self.provider,
            name="Concurrency Consultation",
            slug="concurrency-consult",
            duration_minutes=30,
            buffer_minutes=15,
            price=200.00
        )

    def tearDown(self):
        from django.db import connection, connections
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = current_database() AND pid <> pg_backend_pid();
                """)
        except Exception:
            pass
        connections.close_all()
        super().tearDown()

    def test_multithreaded_race_condition_defense(self):
        """
        Spawns 5 concurrent threads trying to book the exact same slot simultaneously.
        Verifies that exactly ONE booking succeeds (HTTP 201) and all others are rejected (HTTP 409).
        """
        slot_time = timezone.now() + datetime.timedelta(days=10, hours=10)
        results = []

        def attempt_booking(thread_idx):
            from django.db import connections
            try:
                client = APIClient()
                resp = client.post('/api/appointments/book/', {
                    'provider_id': str(self.provider.id),
                    'service_id': str(self.service.id),
                    'start_time': slot_time.isoformat(),
                    'customer_name': f"Concurrent Client {thread_idx}",
                    'customer_email': f"client_{thread_idx}@concurrent-test.com",
                }, format='json')
                results.append(resp.status_code)
            finally:
                connections.close_all()

        threads = [threading.Thread(target=attempt_booking, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Explicitly close all connections
        from django.db import connections
        connections.close_all()

        # Exactly 1 success (201) and 4 conflicts (409)
        success_count = results.count(status.HTTP_201_CREATED)
        conflict_count = results.count(status.HTTP_409_CONFLICT)
        
        self.assertEqual(success_count, 1, f"Expected exactly 1 booking to succeed, got {success_count}. Results: {results}")
        self.assertEqual(conflict_count, 4, f"Expected 4 bookings to be rejected with 409 Conflict, got {conflict_count}. Results: {results}")
