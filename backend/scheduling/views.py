import datetime
import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import ProviderProfile, Service, WorkingHour, ScheduleOverride, Appointment, ReminderLog
from .serializers import (
    ProviderProfileSerializer, ServiceSerializer, WorkingHourSerializer,
    AppointmentSerializer, AppointmentCreateSerializer,
    AppointmentRescheduleSerializer, AppointmentCancelSerializer,
    ReminderLogSerializer, SlotAvailabilityResponseSerializer,
    DashboardMetricsResponseSerializer
)
from .slot_engine import get_available_slots
from .reminder_service import ReminderService


class ProviderListView(ListAPIView):
    """Lists all active providers with services and working hours."""
    queryset = ProviderProfile.objects.filter(is_active=True).prefetch_related('services', 'working_hours')
    serializer_class = ProviderProfileSerializer


class ProviderDetailView(RetrieveAPIView):
    """Retrieves full details for a single provider."""
    queryset = ProviderProfile.objects.filter(is_active=True).prefetch_related('services', 'working_hours')
    serializer_class = ProviderProfileSerializer
    lookup_field = 'id'


class ServiceListView(ListAPIView):
    """Lists all services, optionally filtered by provider_id."""
    serializer_class = ServiceSerializer

    def get_queryset(self):
        qs = Service.objects.filter(is_active=True).select_related('provider')
        provider_id = self.request.query_params.get('provider_id')
        if provider_id:
            qs = qs.filter(provider_id=provider_id)
        return qs


class ServiceDetailView(RetrieveAPIView):
    queryset = Service.objects.filter(is_active=True).select_related('provider')
    serializer_class = ServiceSerializer
    lookup_field = 'id'


class SlotAvailabilityView(APIView):
    """
    Computes available booking slots for a provider and service on a specific calendar date.
    Performs full time zone projection into the client's local zone.
    """
    @extend_schema(
        parameters=[
            OpenApiParameter(name='service_id', type=OpenApiTypes.UUID, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name='date', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True, description='YYYY-MM-DD format'),
            OpenApiParameter(name='client_tz', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description='Client IANA timezone e.g. America/Los_Angeles, UTC'),
        ],
        responses={200: SlotAvailabilityResponseSerializer}
    )
    def get(self, request, provider_id):
        service_id = request.query_params.get('service_id')
        date_str = request.query_params.get('date')
        client_tz = request.query_params.get('client_tz', 'UTC')

        if not service_id or not date_str:
            return Response(
                {'error': 'VALIDATION_ERROR', 'message': 'service_id and date query parameters are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        slots = get_available_slots(provider_id, service_id, date_str, client_tz)
        return Response({
            'provider_id': str(provider_id),
            'service_id': str(service_id),
            'date': date_str,
            'client_timezone': client_tz,
            'slot_count': len(slots),
            'slots': slots
        })


class AppointmentBookingView(APIView):
    """
    Atomic Booking Endpoint with Pessimistic Concurrency Defense.
    Locks the provider row during slot validation to guarantee double bookings
    cannot occur even under high concurrency race conditions.
    """
    @extend_schema(request=AppointmentCreateSerializer, responses={201: AppointmentSerializer, 409: dict})
    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        provider_id = data['provider_id']
        service_id = data['service_id']
        start_time = data['start_time']

        # Ensure start time is in the future
        if start_time <= timezone.now() + datetime.timedelta(minutes=5):
            return Response(
                {'error': 'INVALID_TIME', 'message': 'Appointments must be scheduled at least 5 minutes in advance.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atomic transaction with row-level lock on provider to prevent concurrent race conditions
        with transaction.atomic():
            try:
                # Pessimistic locking of the provider record
                provider = ProviderProfile.objects.select_for_update().get(id=provider_id, is_active=True)
            except ProviderProfile.DoesNotExist:
                return Response({'error': 'NOT_FOUND', 'message': 'Provider not found or inactive.'}, status=status.HTTP_404_NOT_FOUND)

            try:
                service = Service.objects.get(id=service_id, provider=provider, is_active=True)
            except Service.DoesNotExist:
                return Response({'error': 'NOT_FOUND', 'message': 'Service not found for this provider.'}, status=status.HTTP_404_NOT_FOUND)

            duration = datetime.timedelta(minutes=service.duration_minutes)
            buffer_time = datetime.timedelta(minutes=service.buffer_minutes)
            end_time = start_time + duration

            # Overlap check with buffer window
            # A conflict occurs if an existing active appointment starts before candidate end+buffer
            # AND ends after candidate start-buffer
            overlapping_appointment = Appointment.objects.filter(
                provider=provider,
                status__in=['CONFIRMED', 'PENDING'],
                start_time__lt=end_time + buffer_time,
                end_time__gt=start_time - buffer_time
            ).first()

            if overlapping_appointment:
                return Response(
                    {
                        'error': 'DOUBLE_BOOKING_PREVENTED',
                        'message': 'The selected time slot conflicts with an existing booking or mandatory buffer window. Please pick another slot.',
                        'conflict_appointment_id': str(overlapping_appointment.id),
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # Generate virtual conference room link
            short_id = uuid.uuid4().hex[:8]
            meeting_link = f"https://meet.falconxoft.com/call/apt-{short_id}"

            appointment = Appointment.objects.create(
                provider=provider,
                service=service,
                customer_name=data['customer_name'],
                customer_email=data['customer_email'],
                customer_phone=data.get('customer_phone', ''),
                customer_notes=data.get('customer_notes', ''),
                customer_timezone=data.get('customer_timezone', 'UTC'),
                start_time=start_time,
                end_time=end_time,
                status='CONFIRMED',
                meeting_link=meeting_link,
                version=1
            )

            # Dispatch mock multi-channel notifications and queue reminders
            ReminderService.dispatch_booking_notifications(appointment)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


class AppointmentRescheduleView(APIView):
    """
    Reschedules an existing appointment to a new slot.
    Enforces minimum cancellation/reschedule notice policy and atomic concurrency check.
    """
    @extend_schema(request=AppointmentRescheduleSerializer, responses={200: AppointmentSerializer})
    def post(self, request, id):
        serializer = AppointmentRescheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'VALIDATION_ERROR', 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        new_start_time = serializer.validated_data['new_start_time']
        customer_tz = serializer.validated_data.get('customer_timezone', 'UTC')

        if new_start_time <= timezone.now() + datetime.timedelta(minutes=5):
            return Response(
                {'error': 'INVALID_TIME', 'message': 'New appointment time must be at least 5 minutes in the future.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            try:
                appointment = Appointment.objects.select_for_update().get(id=id)
            except Appointment.DoesNotExist:
                return Response({'error': 'NOT_FOUND', 'message': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

            if appointment.status in ['CANCELLED', 'COMPLETED']:
                return Response(
                    {'error': 'INVALID_STATE', 'message': f'Cannot reschedule an appointment with status {appointment.status}.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Enforce notice policy
            service = appointment.service
            notice_limit = timezone.now() + datetime.timedelta(hours=service.cancellation_notice_hours)
            if appointment.start_time < notice_limit:
                return Response(
                    {
                        'error': 'NOTICE_POLICY_VIOLATION',
                        'message': f'Rescheduling requires at least {service.cancellation_notice_hours} hours advance notice before appointment start time.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Lock provider to prevent race conditions on new slot
            provider = ProviderProfile.objects.select_for_update().get(id=appointment.provider_id)
            duration = datetime.timedelta(minutes=service.duration_minutes)
            buffer_time = datetime.timedelta(minutes=service.buffer_minutes)
            new_end_time = new_start_time + duration

            # Overlap check excluding self
            conflict = Appointment.objects.filter(
                provider=provider,
                status__in=['CONFIRMED', 'PENDING'],
                start_time__lt=new_end_time + buffer_time,
                end_time__gt=new_start_time - buffer_time
            ).exclude(id=appointment.id).exists()

            if conflict:
                return Response(
                    {'error': 'DOUBLE_BOOKING_PREVENTED', 'message': 'The requested new slot conflicts with another booking. Please select another time.'},
                    status=status.HTTP_409_CONFLICT
                )

            old_start = appointment.start_time
            appointment.start_time = new_start_time
            appointment.end_time = new_end_time
            appointment.customer_timezone = customer_tz
            appointment.status = 'CONFIRMED'
            appointment.rescheduled_at = timezone.now()
            appointment.version += 1
            appointment.save()

            ReminderService.dispatch_reschedule_notification(appointment, old_start)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)


class AppointmentCancelView(APIView):
    """
    Cancels an existing appointment and dispatches cancellation alerts.
    Validates advance notice policy.
    """
    @extend_schema(request=AppointmentCancelSerializer, responses={200: AppointmentSerializer})
    def post(self, request, id):
        serializer = AppointmentCancelSerializer(data=request.data)
        serializer.is_valid()
        reason = serializer.validated_data.get('reason', '') if serializer.validated_data else ''

        with transaction.atomic():
            try:
                appointment = Appointment.objects.select_for_update().get(id=id)
            except Appointment.DoesNotExist:
                return Response({'error': 'NOT_FOUND', 'message': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

            if appointment.status == 'CANCELLED':
                return Response({'error': 'ALREADY_CANCELLED', 'message': 'Appointment is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

            service = appointment.service
            notice_limit = timezone.now() + datetime.timedelta(hours=service.cancellation_notice_hours)
            if appointment.start_time < notice_limit:
                # We can record policy breach flag or warn, but still allow customer cancellation with explanation
                reason = f"[Late Notice < {service.cancellation_notice_hours}h]: " + (reason or 'Customer initiated late cancellation.')

            appointment.status = 'CANCELLED'
            appointment.cancellation_reason = reason or 'Customer requested cancellation.'
            appointment.version += 1
            appointment.save()

            ReminderService.dispatch_cancellation_notification(appointment, reason)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)


class AppointmentListView(ListAPIView):
    """
    Lists appointments filtered by customer email, provider ID, or status.
    """
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        qs = Appointment.objects.select_related('provider', 'service').prefetch_related('reminders').all()
        email = self.request.query_params.get('email')
        provider_id = self.request.query_params.get('provider_id')
        status_param = self.request.query_params.get('status')

        if email:
            qs = qs.filter(customer_email__iexact=email.strip())
        if provider_id:
            qs = qs.filter(provider_id=provider_id)
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs


class AppointmentDetailView(RetrieveAPIView):
    queryset = Appointment.objects.select_related('provider', 'service').prefetch_related('reminders').all()
    serializer_class = AppointmentSerializer
    lookup_field = 'id'


class ReminderAuditListView(ListAPIView):
    """
    Lists audit log entries for all mock dispatched reminders.
    """
    serializer_class = ReminderLogSerializer

    def get_queryset(self):
        qs = ReminderLog.objects.select_related('appointment').all()
        appointment_id = self.request.query_params.get('appointment_id')
        channel = self.request.query_params.get('channel')

        if appointment_id:
            qs = qs.filter(appointment_id=appointment_id)
        if channel:
            qs = qs.filter(channel=channel.upper())
        return qs[:100]


class DashboardMetricsView(APIView):
    """
    Returns high-level business and operational scheduling metrics.
    """
    @extend_schema(responses={200: DashboardMetricsResponseSerializer})
    def get(self, request):
        now = timezone.now()
        total_appointments = Appointment.objects.count()
        confirmed = Appointment.objects.filter(status='CONFIRMED').count()
        cancelled = Appointment.objects.filter(status='CANCELLED').count()
        completed = Appointment.objects.filter(status='COMPLETED').count()
        upcoming = Appointment.objects.filter(status='CONFIRMED', start_time__gte=now).count()
        
        # Calculate gross booking revenue
        total_revenue = sum([
            apt.service.price for apt in Appointment.objects.filter(status__in=['CONFIRMED', 'COMPLETED']).select_related('service')
        ])

        total_providers = ProviderProfile.objects.filter(is_active=True).count()
        total_services = Service.objects.filter(is_active=True).count()
        total_reminders_sent = ReminderLog.objects.filter(status='DISPATCHED').count()

        return Response({
            'total_appointments': total_appointments,
            'confirmed_appointments': confirmed,
            'upcoming_appointments': upcoming,
            'cancelled_appointments': cancelled,
            'completed_appointments': completed,
            'gross_revenue': float(total_revenue),
            'currency': 'USD',
            'active_providers': total_providers,
            'active_services': total_services,
            'reminders_dispatched': total_reminders_sent,
            'generated_at': now.isoformat()
        })
