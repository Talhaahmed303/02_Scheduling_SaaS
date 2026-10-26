from django.urls import path
from .views import (
    ProviderListView, ProviderDetailView,
    ServiceListView, ServiceDetailView,
    SlotAvailabilityView, AppointmentBookingView,
    AppointmentRescheduleView, AppointmentCancelView,
    AppointmentListView, AppointmentDetailView,
    ReminderAuditListView, DashboardMetricsView
)

urlpatterns = [
    # Providers
    path('providers/', ProviderListView.as_view(), name='provider-list'),
    path('providers/<uuid:id>/', ProviderDetailView.as_view(), name='provider-detail'),
    path('providers/<uuid:provider_id>/slots/', SlotAvailabilityView.as_view(), name='provider-slots'),
    
    # Services
    path('services/', ServiceListView.as_view(), name='service-list'),
    path('services/<uuid:id>/', ServiceDetailView.as_view(), name='service-detail'),
    
    # Appointments
    path('appointments/', AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/book/', AppointmentBookingView.as_view(), name='appointment-book'),
    path('appointments/<uuid:id>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('appointments/<uuid:id>/reschedule/', AppointmentRescheduleView.as_view(), name='appointment-reschedule'),
    path('appointments/<uuid:id>/cancel/', AppointmentCancelView.as_view(), name='appointment-cancel'),

    # Audit & Monitoring
    path('reminders/', ReminderAuditListView.as_view(), name='reminder-audit-list'),
    path('dashboard/metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
]
