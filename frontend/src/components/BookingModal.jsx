import React, { useState } from 'react';
import { bookAppointment } from '../api';

export default function BookingModal({
  provider,
  service,
  slot,
  clientTz,
  onClose,
  onBookingSuccess,
}) {
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    customer_notes: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [confirmedAppointment, setConfirmedAppointment] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.customer_name || !formData.customer_email) {
      setError('Please provide your name and email address.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        provider_id: provider.id,
        service_id: service.id,
        start_time: slot.start_time_utc,
        customer_name: formData.customer_name,
        customer_email: formData.customer_email,
        customer_phone: formData.customer_phone,
        customer_notes: formData.customer_notes,
        customer_timezone: clientTz,
      };

      const result = await bookAppointment(payload);
      setConfirmedAppointment(result);
      if (onBookingSuccess) onBookingSuccess(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content fade-in">
        <button id="modal-close-btn" className="modal-close-btn" onClick={onClose}>
          ✕
        </button>

        {!confirmedAppointment ? (
          <>
            <h3 className="modal-title">Confirm Consultation Session</h3>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-secondary)' }}>
              Complete your information to lock in your appointment with {provider.name}.
            </p>

            <div className="modal-summary-box">
              <div className="summary-row">
                <span>Consultant:</span>
                <span>{provider.name} ({provider.title})</span>
              </div>
              <div className="summary-row">
                <span>Service:</span>
                <span>{service.name} (${service.price} {service.currency})</span>
              </div>
              <div className="summary-row">
                <span>Duration:</span>
                <span>{service.duration_minutes} minutes (+{service.buffer_minutes}m buffer)</span>
              </div>
              <div className="summary-row">
                <span>Your Time ({clientTz}):</span>
                <span style={{ color: 'var(--accent-cyan)' }}>{slot.client_display_label}</span>
              </div>
              <div className="summary-row">
                <span>Provider Time ({provider.timezone}):</span>
                <span>{slot.display_label}</span>
              </div>
            </div>

            {error && (
              <div className="alert-box error">
                <span>⚠️</span>
                <div>{error}</div>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input
                  id="book-form-name"
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Marcus Aurelius"
                  value={formData.customer_name}
                  onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address (for confirmation & ICS) *</label>
                <input
                  id="book-form-email"
                  type="email"
                  required
                  className="form-input"
                  placeholder="name@company.com"
                  value={formData.customer_email}
                  onChange={(e) => setFormData({ ...formData, customer_email: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone / WhatsApp (for SMS reminders)</label>
                <input
                  id="book-form-phone"
                  type="tel"
                  className="form-input"
                  placeholder="+1 (555) 019-2834"
                  value={formData.customer_phone}
                  onChange={(e) => setFormData({ ...formData, customer_phone: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Consultation Agenda & Architecture Notes</label>
                <textarea
                  id="book-form-notes"
                  rows="3"
                  className="form-textarea"
                  placeholder="Briefly describe what you would like to address during this session..."
                  value={formData.customer_notes}
                  onChange={(e) => setFormData({ ...formData, customer_notes: e.target.value })}
                ></textarea>
              </div>

              <button
                id="btn-confirm-booking"
                type="submit"
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Acquiring Atomic Lock & Reserving...' : `Confirm & Book Appointment ($${service.price})`}
              </button>
            </form>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '1rem 0' }}>
            <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>🎉</div>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent-emerald)' }}>
              Booking Confirmed!
            </h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
              Your appointment has been atomically secured and registered in the system.
            </p>

            <div className="modal-summary-box" style={{ textAlign: 'left' }}>
              <div className="summary-row">
                <span>Appointment ID:</span>
                <span style={{ fontFamily: 'var(--font-mono)' }}>{confirmedAppointment.id}</span>
              </div>
              <div className="summary-row">
                <span>Status:</span>
                <span className="status-pill confirmed">CONFIRMED</span>
              </div>
              <div className="summary-row">
                <span>Meeting Link:</span>
                <span>
                  <a
                    href={confirmedAppointment.meeting_link}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: 'var(--accent-cyan)' }}
                  >
                    {confirmedAppointment.meeting_link}
                  </a>
                </span>
              </div>
              <div className="summary-row">
                <span>Mock Notifications:</span>
                <span style={{ color: 'var(--accent-emerald)' }}>✓ Confirmation Email & ICS Dispatched</span>
              </div>
            </div>

            <button
              id="btn-done-booking"
              className="btn-primary"
              onClick={onClose}
              style={{ marginTop: '1rem' }}
            >
              Close & View My Bookings
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
