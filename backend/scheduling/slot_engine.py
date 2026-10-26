import datetime
import pytz
from django.utils import timezone
from .models import ProviderProfile, Service, WorkingHour, ScheduleOverride, Appointment

def get_available_slots(provider_id, service_id, target_date_str, client_tz_str='UTC'):
    """
    Generates dynamic appointment slots for a given provider, service, and calendar date.
    Performs full time zone conversion, working hours bounds checking, break exclusion,
    buffer time inclusion, and atomic overlap checking against active appointments.
    """
    try:
        provider = ProviderProfile.objects.get(id=provider_id, is_active=True)
        service = Service.objects.get(id=service_id, provider=provider, is_active=True)
    except (ProviderProfile.DoesNotExist, Service.DoesNotExist):
        return []

    try:
        target_date = datetime.date.fromisoformat(target_date_str)
    except ValueError:
        return []

    # Resolve time zones
    try:
        provider_tz = pytz.timezone(provider.timezone)
    except pytz.UnknownTimeZoneError:
        provider_tz = pytz.UTC

    try:
        client_tz = pytz.timezone(client_tz_str)
    except pytz.UnknownTimeZoneError:
        client_tz = pytz.UTC

    # 1. Check for schedule override on target date (vacation, sick leave, custom hours)
    override = ScheduleOverride.objects.filter(provider=provider, date=target_date).first()
    if override and override.is_unavailable:
        return []

    # 2. Get standard working hours for this weekday (0=Monday, 6=Sunday)
    weekday = target_date.weekday()
    working_hour = WorkingHour.objects.filter(provider=provider, day_of_week=weekday).first()
    
    if not working_hour or not working_hour.is_available:
        if not (override and not override.is_unavailable):
            return []

    # Determine start and end times in provider local time
    if override and not override.is_unavailable and override.custom_start_time and override.custom_end_time:
        day_start_time = override.custom_start_time
        day_end_time = override.custom_end_time
        break_start = None
        break_end = None
    else:
        day_start_time = working_hour.start_time
        day_end_time = working_hour.end_time
        break_start = working_hour.break_start_time
        break_end = working_hour.break_end_time

    # Construct localized provider datetime boundaries
    local_start_dt = provider_tz.localize(datetime.datetime.combine(target_date, day_start_time))
    local_end_dt = provider_tz.localize(datetime.datetime.combine(target_date, day_end_time))
    
    break_start_dt = provider_tz.localize(datetime.datetime.combine(target_date, break_start)) if break_start else None
    break_end_dt = provider_tz.localize(datetime.datetime.combine(target_date, break_end)) if break_end else None

    # Step duration and total slot stride (duration + buffer)
    duration_delta = datetime.timedelta(minutes=service.duration_minutes)
    buffer_delta = datetime.timedelta(minutes=service.buffer_minutes)
    stride_delta = duration_delta + buffer_delta

    # Fetch all confirmed/pending appointments overlapping this provider's entire day window
    utc_day_start = local_start_dt.astimezone(pytz.UTC)
    utc_day_end = local_end_dt.astimezone(pytz.UTC)

    existing_appointments = list(Appointment.objects.filter(
        provider=provider,
        status__in=['CONFIRMED', 'PENDING'],
        start_time__lt=utc_day_end + buffer_delta,
        end_time__gt=utc_day_start - buffer_delta
    ).values('start_time', 'end_time'))

    now_utc = timezone.now()

    candidate_slots = []
    curr_time = local_start_dt

    while curr_time + duration_delta <= local_end_dt:
        slot_end_time = curr_time + duration_delta
        
        # Check break overlap
        in_break = False
        if break_start_dt and break_end_dt:
            if not (slot_end_time <= break_start_dt or curr_time >= break_end_dt):
                in_break = True

        # Check existing appointment overlap (including buffer periods)
        slot_start_utc = curr_time.astimezone(pytz.UTC)
        slot_end_utc = slot_end_time.astimezone(pytz.UTC)

        has_conflict = False
        if not in_break:
            # Must be in the future (minimum 10 minutes notice)
            if slot_start_utc <= now_utc + datetime.timedelta(minutes=10):
                has_conflict = True
            else:
                for apt in existing_appointments:
                    apt_start = apt['start_time']
                    apt_end = apt['end_time']
                    # Overlap with buffer:
                    # New slot conflicts if start < apt_end + buffer AND end + buffer > apt_start
                    if slot_start_utc < (apt_end + buffer_delta) and (slot_end_utc + buffer_delta) > apt_start:
                        has_conflict = True
                        break

        if not in_break and not has_conflict:
            slot_client_start = slot_start_utc.astimezone(client_tz)
            slot_client_end = slot_end_utc.astimezone(client_tz)
            
            candidate_slots.append({
                'start_time_utc': slot_start_utc.isoformat(),
                'end_time_utc': slot_end_utc.isoformat(),
                'start_time_provider': curr_time.isoformat(),
                'end_time_provider': slot_end_time.isoformat(),
                'start_time_client': slot_client_start.isoformat(),
                'end_time_client': slot_client_end.isoformat(),
                'display_time': curr_time.strftime('%I:%M %p'),
                'display_label': f"{curr_time.strftime('%I:%M %p')} - {slot_end_time.strftime('%I:%M %p')} ({provider_tz.zone})",
                'client_display_label': f"{slot_client_start.strftime('%I:%M %p')} - {slot_client_end.strftime('%I:%M %p')} ({client_tz.zone})",
                'duration_minutes': service.duration_minutes,
                'buffer_minutes': service.buffer_minutes,
            })

        curr_time += stride_delta

    return candidate_slots
