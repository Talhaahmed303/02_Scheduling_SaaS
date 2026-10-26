import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ProviderCard from './components/ProviderCard';
import CalendarSlotPicker from './components/CalendarSlotPicker';
import BookingModal from './components/BookingModal';
import CustomerBookingManager from './components/CustomerBookingManager';
import ProviderScheduleDashboard from './components/ProviderScheduleDashboard';
import ReminderAuditLog from './components/ReminderAuditLog';
import { fetchProviders, fetchDashboardMetrics } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('book');
  const [clientTz, setClientTz] = useState(() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    } catch {
      return 'UTC';
    }
  });

  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastBookedEmail, setLastBookedEmail] = useState('');

  useEffect(() => {
    Promise.all([fetchProviders(), fetchDashboardMetrics()])
      .then(([providersData, metricsData]) => {
        setProviders(providersData);
        setMetrics(metricsData);
        if (providersData.length > 0) {
          setSelectedProvider(providersData[0]);
          if (providersData[0].services?.length > 0) {
            setSelectedService(providersData[0].services[0]);
          }
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to initialize app:', err);
        setLoading(false);
      });
  }, []);

  const handleSelectProvider = (provider) => {
    setSelectedProvider(provider);
    if (provider.services?.length > 0) {
      setSelectedService(provider.services[0]);
    } else {
      setSelectedService(null);
    }
  };

  const handleSelectSlot = (slot) => {
    setSelectedSlot(slot);
    setIsBookingModalOpen(true);
  };

  const handleBookingSuccess = (booking) => {
    setLastBookedEmail(booking.customer_email);
    fetchDashboardMetrics().then(setMetrics);
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        clientTz={clientTz}
        setClientTz={setClientTz}
      />

      <main className="main-content">
        {activeTab === 'book' && (
          <div className="fade-in">
            {/* Hero Section */}
            <section className="hero-banner">
              <div className="hero-pill">
                <span className="hero-pill-dot"></span>
                <span>PostgreSQL 18 Atomic Concurrency & Range Defense</span>
              </div>
              <h1 className="hero-title">
                High-Impact Advisory Sessions,<br />
                <span>Synchronized Globally Across Time Zones</span>
              </h1>
              <p className="hero-subtitle">
                Schedule one-on-one architecture, compliance, and systems consulting with senior specialists.
                Zero double bookings, automatic DST alignment, and real-time multi-channel reminders.
              </p>
            </section>

            {/* Quick Metrics Bar */}
            {metrics && (
              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Active Consultants</div>
                  <div className="metric-value">{metrics.active_providers}</div>
                  <div className="metric-sub">Distributed across 4 global timezones</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Available Services</div>
                  <div className="metric-value">{metrics.active_services}</div>
                  <div className="metric-sub">30m, 45m & 60m consulting tiers</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Total Bookings</div>
                  <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
                    {metrics.total_appointments}
                  </div>
                  <div className="metric-sub">{metrics.upcoming_appointments} upcoming sessions</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Platform Gross</div>
                  <div className="metric-value" style={{ color: 'var(--accent-emerald)' }}>
                    ${metrics.gross_revenue.toLocaleString()}
                  </div>
                  <div className="metric-sub">Simulated client billings</div>
                </div>
              </div>
            )}

            {/* Providers Section */}
            <div className="section-header">
              <div>
                <h2 className="section-title">Senior Enterprise Consultants</h2>
                <p className="section-desc">
                  Choose a consultant to inspect working hours and book an available consultation slot.
                </p>
              </div>
            </div>

            {loading ? (
              <div className="empty-slots-state">
                <p>Loading enterprise consultants...</p>
              </div>
            ) : (
              <div className="providers-grid">
                {providers.map((p) => (
                  <ProviderCard
                    key={p.id}
                    provider={p}
                    isSelected={selectedProvider?.id === p.id}
                    onSelect={handleSelectProvider}
                  />
                ))}
              </div>
            )}

            {/* Calendar & Slots Interactive Section */}
            {selectedProvider && selectedService && (
              <section id="calendar-section" style={{ marginTop: '2rem' }}>
                <div className="section-header">
                  <div>
                    <h3 className="section-title">
                      Schedule with {selectedProvider.name}
                    </h3>
                    <p className="section-desc">
                      Current Selection: <strong>{selectedService.name}</strong> ·{' '}
                      {selectedService.duration_minutes}m · ${selectedService.price}
                    </p>
                  </div>
                </div>

                <CalendarSlotPicker
                  provider={selectedProvider}
                  selectedService={selectedService}
                  setSelectedService={setSelectedService}
                  clientTz={clientTz}
                  onSelectSlot={handleSelectSlot}
                />
              </section>
            )}

            {/* Booking Modal */}
            {isBookingModalOpen && selectedProvider && selectedService && selectedSlot && (
              <BookingModal
                provider={selectedProvider}
                service={selectedService}
                slot={selectedSlot}
                clientTz={clientTz}
                onClose={() => setIsBookingModalOpen(false)}
                onBookingSuccess={handleBookingSuccess}
              />
            )}
          </div>
        )}

        {activeTab === 'my-bookings' && (
          <CustomerBookingManager
            clientTz={clientTz}
            initialEmail={lastBookedEmail}
          />
        )}

        {activeTab === 'provider-ops' && (
          <ProviderScheduleDashboard />
        )}

        {activeTab === 'reminders' && (
          <ReminderAuditLog />
        )}
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '1.5rem 2.5rem',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '0.82rem',
          background: 'rgba(7, 11, 20, 0.8)',
        }}
      >
        <div>
          FalconXoft Appointment & Scheduling SaaS · 15-Day Intern Performance Evaluation (Weekend 2)
        </div>
        <div style={{ marginTop: '0.4rem', fontFamily: 'var(--font-mono)', fontSize: '0.74rem' }}>
          Backend: Django REST Framework (Port 8001) · DB: PostgreSQL 18.3 (Tablespace: D:\pg_tablespace) · Frontend: React 18 + Vite (Port 3001)
        </div>
      </footer>
    </div>
  );
}
