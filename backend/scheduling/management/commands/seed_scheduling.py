import datetime
import uuid
import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from scheduling.models import ProviderProfile, Service, WorkingHour, ScheduleOverride, Appointment, ReminderLog
from scheduling.reminder_service import ReminderService

class Command(BaseCommand):
    help = 'Seeds database with realistic providers, services, working hours, and initial bookings'

    def handle(self, *args, **options):
        self.stdout.write("Seeding scheduling SaaS database...")

        # Clear existing data safely
        ReminderLog.objects.all().delete()
        Appointment.objects.all().delete()
        ScheduleOverride.objects.all().delete()
        WorkingHour.objects.all().delete()
        Service.objects.all().delete()
        ProviderProfile.objects.all().delete()

        # 1. Create Providers
        providers_data = [
            {
                'name': 'Dr. Sarah Jenkins',
                'slug': 'dr-sarah-jenkins',
                'title': 'Principal Distributed Systems Architect',
                'bio': 'Over 14 years specializing in high-throughput database systems, event-driven microservices, and multi-region fault tolerance. Former Staff Engineer at CloudScale.',
                'email': 'sarah.jenkins@falconxoft.io',
                'phone': '+1 (415) 890-3421',
                'timezone': 'America/New_York',
                'avatar_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&auto=format&fit=crop&q=80',
            },
            {
                'name': 'Marcus Vance',
                'slug': 'marcus-vance',
                'title': 'Head of Cybersecurity & SOC 2 Compliance',
                'bio': 'Advises enterprise SaaS founders on zero-trust perimeter defense, ISO 27001 readiness, and defensive cryptographic architecture.',
                'email': 'marcus.vance@falconxoft.io',
                'phone': '+44 20 7946 0912',
                'timezone': 'Europe/London',
                'avatar_url': 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&auto=format&fit=crop&q=80',
            },
            {
                'name': 'Elena Rostova',
                'slug': 'elena-rostova',
                'title': 'VP of Enterprise Product & SaaS Strategy',
                'bio': 'Helps growth-stage software companies optimize self-serve onboarding, monetization funnels, and enterprise SLA structures.',
                'email': 'elena.rostova@falconxoft.io',
                'phone': '+971 4 391 1111',
                'timezone': 'Asia/Dubai',
                'avatar_url': 'https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&auto=format&fit=crop&q=80',
            },
            {
                'name': 'Tariq Al-Mansoor',
                'slug': 'tariq-al-mansoor',
                'title': 'Lead Cloud Infrastructure & Kubernetes Architect',
                'bio': 'Deep expertise in Kubernetes orchestration, Terraform automation, multi-cloud cost containment, and CI/CD resilience.',
                'email': 'tariq.mansoor@falconxoft.io',
                'phone': '+92 300 8271923',
                'timezone': 'Asia/Karachi',
                'avatar_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400&auto=format&fit=crop&q=80',
            }
        ]

        created_providers = {}
        for p_data in providers_data:
            provider = ProviderProfile.objects.create(**p_data)
            created_providers[provider.slug] = provider
            self.stdout.write(f"  Created Provider: {provider.name} ({provider.timezone})")

        # 2. Create Working Hours for each Provider (Mon to Fri: 09:00 - 17:00, Lunch: 13:00 - 14:00)
        for provider in created_providers.values():
            for day in range(7):
                is_weekday = day < 5  # Mon-Fri
                WorkingHour.objects.create(
                    provider=provider,
                    day_of_week=day,
                    start_time=datetime.time(9, 0),
                    end_time=datetime.time(17, 0),
                    break_start_time=datetime.time(13, 0) if is_weekday else None,
                    break_end_time=datetime.time(14, 0) if is_weekday else None,
                    is_available=is_weekday
                )

        # 3. Create Services
        services_data = [
            # Sarah Jenkins
            {
                'provider': created_providers['dr-sarah-jenkins'],
                'name': '30-Min High-Level Architecture Advisory',
                'slug': '30-min-architecture-advisory',
                'description': 'Rapid evaluation of current database schema, microservice topology, and bottleneck remediation plan.',
                'duration_minutes': 30,
                'buffer_minutes': 15,
                'price': 150.00,
                'cancellation_notice_hours': 24,
            },
            {
                'provider': created_providers['dr-sarah-jenkins'],
                'name': '60-Min Deep-Dive Concurrency & Scaling Audit',
                'slug': '60-min-concurrency-scaling-audit',
                'description': 'In-depth code and architecture session addressing race conditions, PostgreSQL locking patterns, and caching pipelines.',
                'duration_minutes': 60,
                'buffer_minutes': 15,
                'price': 275.00,
                'cancellation_notice_hours': 24,
            },
            # Marcus Vance
            {
                'provider': created_providers['marcus-vance'],
                'name': '45-Min SOC 2 & Cloud Compliance Readiness',
                'slug': '45-min-soc2-compliance',
                'description': 'Gap analysis of cloud access policies, audit logging, vulnerability triage, and compliance roadmaps.',
                'duration_minutes': 45,
                'buffer_minutes': 15,
                'price': 220.00,
                'cancellation_notice_hours': 24,
            },
            # Elena Rostova
            {
                'provider': created_providers['elena-rostova'],
                'name': '45-Min SaaS Monetization & Pricing Workshop',
                'slug': '45-min-saas-pricing-workshop',
                'description': 'Tailored analysis of usage-based tiers, enterprise feature gating, and customer contract packaging.',
                'duration_minutes': 45,
                'buffer_minutes': 15,
                'price': 250.00,
                'cancellation_notice_hours': 12,
            },
            # Tariq Al-Mansoor
            {
                'provider': created_providers['tariq-al-mansoor'],
                'name': '60-Min Kubernetes & FinOps Cloud Optimization',
                'slug': '60-min-k8s-finops-optimization',
                'description': 'AWS/GCP bill deconstruction, node autoscale right-sizing, spot fleet utilization, and container security.',
                'duration_minutes': 60,
                'buffer_minutes': 20,
                'price': 260.00,
                'cancellation_notice_hours': 24,
            }
        ]

        created_services = []
        for s_data in services_data:
            service = Service.objects.create(**s_data)
            created_services.append(service)
            self.stdout.write(f"  Created Service: {service.name} (${service.price})")

        # 4. Schedule Overrides
        tomorrow = timezone.now().date() + datetime.timedelta(days=7)
        ScheduleOverride.objects.create(
            provider=created_providers['dr-sarah-jenkins'],
            date=tomorrow,
            is_unavailable=True,
            reason="Keynote Speaker at USENIX Distributed Systems Summit"
        )
        self.stdout.write(f"  Created Schedule Override for Dr. Sarah Jenkins on {tomorrow}")

        # 5. Create Sample Appointments & Notifications
        now = timezone.now()
        # Appointment 1: Upcoming Tomorrow at 14:00 UTC with Sarah Jenkins
        sarah = created_providers['dr-sarah-jenkins']
        sarah_svc = created_services[0]
        apt_start_1 = (now + datetime.timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
        apt_end_1 = apt_start_1 + datetime.timedelta(minutes=sarah_svc.duration_minutes)

        apt1 = Appointment.objects.create(
            provider=sarah,
            service=sarah_svc,
            customer_name='Alexandre Dubois',
            customer_email='alex.dubois@technova.eu',
            customer_phone='+33 6 12 34 56 78',
            customer_notes='Need review of our PostgreSQL partitioning strategy under 50k RPS peak load.',
            customer_timezone='Europe/Paris',
            start_time=apt_start_1,
            end_time=apt_end_1,
            status='CONFIRMED',
            meeting_link='https://meet.falconxoft.com/call/apt-9a82df1b',
            version=1
        )
        ReminderService.dispatch_booking_notifications(apt1)
        self.stdout.write(f"  Created Confirmed Appointment: {apt1.id} for Alexandre Dubois")

        # Appointment 2: Marcus Vance appointment
        marcus = created_providers['marcus-vance']
        marcus_svc = created_services[2]
        apt_start_2 = (now + datetime.timedelta(days=2)).replace(hour=11, minute=0, second=0, microsecond=0)
        apt_end_2 = apt_start_2 + datetime.timedelta(minutes=marcus_svc.duration_minutes)

        apt2 = Appointment.objects.create(
            provider=marcus,
            service=marcus_svc,
            customer_name='Claire Chen',
            customer_email='claire.chen@apexhealth.org',
            customer_phone='+1 (617) 555-0199',
            customer_notes='HIPAA BAA compliance review and database audit trail encryption check.',
            customer_timezone='America/New_York',
            start_time=apt_start_2,
            end_time=apt_end_2,
            status='CONFIRMED',
            meeting_link='https://meet.falconxoft.com/call/apt-4e20ba7c',
            version=1
        )
        ReminderService.dispatch_booking_notifications(apt2)
        self.stdout.write(f"  Created Confirmed Appointment: {apt2.id} for Claire Chen")

        # Appointment 3: Completed historical appointment
        apt_start_past = (now - datetime.timedelta(days=3)).replace(hour=15, minute=0, second=0, microsecond=0)
        apt_end_past = apt_start_past + datetime.timedelta(minutes=sarah_svc.duration_minutes)
        apt3 = Appointment.objects.create(
            provider=sarah,
            service=sarah_svc,
            customer_name='David Miller',
            customer_email='d.miller@stratos.io',
            customer_phone='+1 (206) 555-8833',
            customer_notes='Architecture baseline completed.',
            customer_timezone='America/Los_Angeles',
            start_time=apt_start_past,
            end_time=apt_end_past,
            status='COMPLETED',
            meeting_link='https://meet.falconxoft.com/call/apt-33b210ae',
            version=1
        )
        ReminderService.dispatch_booking_notifications(apt3)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with enterprise scheduling dataset!"))
