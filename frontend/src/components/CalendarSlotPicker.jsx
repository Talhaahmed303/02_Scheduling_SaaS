import React, { useState, useEffect } from 'react';
import { fetchProviderSlots } from '../api';

export default function CalendarSlotPicker({
  provider,
  selectedService,
  setSelectedService,
  clientTz,
  onSelectSlot,
}) {
  const [selectedDate, setSelectedDate] = useState(() => {
    // Default to tomorrow's date formatted as YYYY-MM-DD
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });

  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!provider || !selectedService || !selectedDate) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    fetchProviderSlots(provider.id, selectedService.id, selectedDate, clientTz)
      .then((data) => {
        if (isMounted) {
          setSlots(data.slots || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message);
          setSlots([]);
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [provider, selectedService, selectedDate, clientTz]);

  if (!provider) return null;

  return (
    <div className="scheduling-workspace fade-in">
      {/* Left Column: Services offered by this provider */}
      <div className="services-col">
        <div style={{ marginBottom: '1.25rem' }}>
          <h4 style={{ fontSize: '1.15rem', fontWeight: 700 }}>1. Select Consultation Service</h4>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Offered by {provider.name}
          </p>
        </div>

        {provider.services?.map((svc) => (
          <div
            key={svc.id}
            id={`service-opt-${svc.id}`}
            className={`service-card ${selectedService?.id === svc.id ? 'selected' : ''}`}
            onClick={() => setSelectedService(svc)}
          >
            <div className="service-card-title">{svc.name}</div>
            <div className="service-card-desc">{svc.description}</div>
            <div className="service-card-meta">
              <div className="service-duration">
                <span>⏱</span> {svc.duration_minutes} mins (+{svc.buffer_minutes}m buffer)
              </div>
              <div className="service-price">
                ${svc.price} {svc.currency}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Right Column: Calendar Date & Available Time Slots */}
      <div className="slots-col">
        <div className="calendar-control-bar">
          <div>
            <h4 style={{ fontSize: '1.1rem', fontWeight: 700 }}>2. Select Date & Slot</h4>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Times displayed in your timezone (<strong>{clientTz}</strong>)
            </span>
          </div>

          <div>
            <input
              type="date"
              id="booking-date-picker"
              className="date-input-field"
              value={selectedDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setSelectedDate(e.target.value)}
            />
          </div>
        </div>

        {loading && (
          <div className="empty-slots-state">
            <div className="empty-slots-icon">⏳</div>
            <p>Computing available slots via dynamic scheduling engine...</p>
          </div>
        )}

        {error && (
          <div className="alert-box error">
            <span>⚠️</span>
            <div>{error}</div>
          </div>
        )}

        {!loading && !error && slots.length === 0 && (
          <div className="empty-slots-state">
            <div className="empty-slots-icon">📅</div>
            <h4 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>No Slots Available</h4>
            <p>
              {provider.name} is either fully booked, observing a break, or unavailable on{' '}
              <strong>{selectedDate}</strong>.
            </p>
            <p style={{ marginTop: '0.5rem', fontSize: '0.82rem' }}>
              Please select another date on the calendar.
            </p>
          </div>
        )}

        {!loading && !error && slots.length > 0 && (
          <div>
            <div style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {slots.length} available slots found for <strong>{selectedDate}</strong>:
              </span>
              <span className="brand-badge">⚡ Atomic Lock Protected</span>
            </div>

            <div className="slots-grid-container">
              {slots.map((slot, idx) => (
                <button
                  key={idx}
                  id={`slot-btn-${idx}`}
                  className="slot-btn"
                  onClick={() => onSelectSlot(slot)}
                >
                  <span className="slot-time-primary">{slot.display_time}</span>
                  <span className="slot-time-sub">{slot.client_display_label.split('(')[0].trim()}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
