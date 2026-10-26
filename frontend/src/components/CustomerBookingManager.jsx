import React, { useState, useEffect } from 'react';
import { fetchAppointments, rescheduleAppointment, cancelAppointment } from '../api';

export default function CustomerBookingManager({ clientTz, initialEmail = '' }) {
  const [email, setEmail] = useState(initialEmail || 'alex.dubois@technova.eu');
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Reschedule state
  const [reschedulingApt, setReschedulingApt] = useState(null);
  const [rescheduleDate, setRescheduleDate] = useState('');
  const [rescheduleTime, setRescheduleTime] = useState('14:00');
  const [rescheduleLoading, setRescheduleLoading] = useState(false);

  // Cancel state
  const [cancellingApt, setCancellingApt] = useState(null);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelLoading, setCancelLoading] = useState(false);

  const loadAppointments = (searchEmail) => {
    if (!searchEmail) return;
    setLoading(true);
    setError(null);
    setSuccessMsg(null);

    fetchAppointments({ email: searchEmail })
      .then((data) => {
        setAppointments(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadAppointments(email);
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadAppointments(email);
  };

  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    if (!rescheduleDate || !rescheduleTime) {
      alert('Please select both a date and a time for rescheduling.');
      return;
    }

    setRescheduleLoading(true);
    try {
      // Build ISO string in UTC or local
      const combinedDateTime = new Date(`${rescheduleDate}T${rescheduleTime}:00Z`).toISOString();
      await rescheduleAppointment(reschedulingApt.id, combinedDateTime, clientTz);
      setSuccessMsg(`Appointment #${reschedulingApt.id.slice(0, 8)} successfully rescheduled.`);
      setReschedulingApt(null);
      loadAppointments(email);
    } catch (err) {
      alert(`Rescheduling Failed: ${err.message}`);
    } finally {
      setRescheduleLoading(false);
    }
  };

  const handleCancelSubmit = async (e) => {
    e.preventDefault();
    setCancelLoading(true);
    try {
      await cancelAppointment(cancellingApt.id, cancelReason);
      setSuccessMsg(`Appointment #${cancellingApt.id.slice(0, 8)} has been cancelled.`);
      setCancellingApt(null);
      loadAppointments(email);
    } catch (err) {
      alert(`Cancellation Failed: ${err.message}`);
    } finally {
      setCancelLoading(false);
    }
  };

  return (
    <div className="fade-in">
      <div className="section-header">
        <div>
          <h2 className="section-title">My Scheduled Consultations</h2>
          <p className="section-desc">
            Manage your booked appointments, check status, or request rescheduling and cancellation.
          </p>
        </div>
      </div>

      {/* Email Search Box */}
      <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', maxWidth: '600px' }}>
        <input
          id="search-email-input"
          type="email"
          required
          className="form-input"
          placeholder="Enter your booking email..."
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button id="btn-search-bookings" type="submit" className="btn-primary" style={{ width: 'auto', padding: '0 1.5rem', whiteSpace: 'nowrap' }}>
          Find Bookings
        </button>
      </form>

      {successMsg && (
        <div className="alert-box success">
          <span>✓</span>
          <div>{successMsg}</div>
        </div>
      )}

      {error && (
        <div className="alert-box error">
          <span>⚠️</span>
          <div>{error}</div>
        </div>
      )}

      {loading ? (
        <div className="empty-slots-state">
          <p>Loading your appointments...</p>
        </div>
      ) : appointments.length === 0 ? (
        <div className="empty-slots-state" style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
          <div className="empty-slots-icon">📑</div>
          <h4>No Appointments Found</h4>
          <p>No active or past bookings registered for <strong>{email}</strong>.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Service & Provider</th>
                <th>Scheduled Time (UTC / Local)</th>
                <th>Duration</th>
                <th>Status</th>
                <th>Meeting Room</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((apt) => {
                const startDate = new Date(apt.start_time);
                const isUpcoming = startDate > new Date() && apt.status === 'CONFIRMED';

                return (
                  <tr key={apt.id} id={`apt-row-${apt.id}`}>
                    <td>
                      <div style={{ fontWeight: 700 }}>{apt.service_name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>w/ {apt.provider_name}</div>
                    </td>
                    <td>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
                        {startDate.toLocaleDateString()} {startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        Client TZ: {apt.customer_timezone}
                      </div>
                    </td>
                    <td>{apt.duration_minutes} mins</td>
                    <td>
                      <span className={`status-pill ${apt.status.toLowerCase()}`}>
                        {apt.status}
                      </span>
                    </td>
                    <td>
                      {apt.meeting_link && apt.status !== 'CANCELLED' ? (
                        <a
                          href={apt.meeting_link}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--accent-cyan)', textDecoration: 'none', fontWeight: 600 }}
                        >
                          Join Room ↗
                        </a>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>
                    <td>
                      {isUpcoming ? (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button
                            id={`btn-reschedule-${apt.id}`}
                            className="provider-select-btn"
                            style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
                            onClick={() => {
                              setReschedulingApt(apt);
                              const nextDay = new Date();
                              nextDay.setDate(nextDay.getDate() + 2);
                              setRescheduleDate(nextDay.toISOString().split('T')[0]);
                            }}
                          >
                            Reschedule
                          </button>
                          <button
                            id={`btn-cancel-${apt.id}`}
                            className="btn-danger"
                            onClick={() => {
                              setCancellingApt(apt);
                              setCancelReason('');
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>No actions</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Reschedule Modal */}
      {reschedulingApt && (
        <div className="modal-overlay">
          <div className="modal-content fade-in">
            <button className="modal-close-btn" onClick={() => setReschedulingApt(null)}>✕</button>
            <h3 className="modal-title">Reschedule Consultation</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
              Select a new date and time for your session with {reschedulingApt.provider_name}.
            </p>

            <form onSubmit={handleRescheduleSubmit}>
              <div className="form-group">
                <label className="form-label">New Target Date</label>
                <input
                  type="date"
                  required
                  className="form-input"
                  value={rescheduleDate}
                  min={new Date().toISOString().split('T')[0]}
                  onChange={(e) => setRescheduleDate(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">New Time (UTC)</label>
                <input
                  type="time"
                  required
                  className="form-input"
                  value={rescheduleTime}
                  onChange={(e) => setRescheduleTime(e.target.value)}
                />
              </div>

              <button type="submit" className="btn-primary" disabled={rescheduleLoading}>
                {rescheduleLoading ? 'Checking Availability & Rescheduling...' : 'Confirm Reschedule'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Cancellation Modal */}
      {cancellingApt && (
        <div className="modal-overlay">
          <div className="modal-content fade-in">
            <button className="modal-close-btn" onClick={() => setCancellingApt(null)}>✕</button>
            <h3 className="modal-title" style={{ color: '#f87171' }}>Cancel Appointment</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
              Are you sure you want to cancel your session '{cancellingApt.service_name}' with {cancellingApt.provider_name}?
            </p>

            <form onSubmit={handleCancelSubmit}>
              <div className="form-group">
                <label className="form-label">Reason for Cancellation</label>
                <textarea
                  rows="3"
                  className="form-textarea"
                  placeholder="Please let us know why you need to cancel..."
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                ></textarea>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="provider-select-btn"
                  onClick={() => setCancellingApt(null)}
                >
                  Keep Appointment
                </button>
                <button
                  type="submit"
                  className="btn-danger"
                  style={{ flex: 1, padding: '0.75rem' }}
                  disabled={cancelLoading}
                >
                  {cancelLoading ? 'Cancelling...' : 'Confirm Cancellation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
