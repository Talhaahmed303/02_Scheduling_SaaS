import React, { useState, useEffect } from 'react';
import { fetchDashboardMetrics, fetchAppointments, fetchProviders } from '../api';

export default function ProviderScheduleDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [providers, setProviders] = useState([]);
  const [selectedProviderId, setSelectedProviderId] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchDashboardMetrics(),
      fetchProviders(),
      fetchAppointments(),
    ])
      .then(([metricsData, providersData, aptsData]) => {
        setMetrics(metricsData);
        setProviders(providersData);
        setAppointments(aptsData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load dashboard data:', err);
        setLoading(false);
      });
  }, []);

  const handleFilter = () => {
    setLoading(true);
    fetchAppointments({
      provider_id: selectedProviderId || undefined,
      status: selectedStatus || undefined,
    })
      .then((data) => {
        setAppointments(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    handleFilter();
  }, [selectedProviderId, selectedStatus]);

  return (
    <div className="fade-in">
      <div className="section-header">
        <div>
          <h2 className="section-title">Operations & Schedule Intelligence</h2>
          <p className="section-desc">
            Monitor real-time booking throughput, gross platform revenue, and provider schedules.
          </p>
        </div>
        <button
          className="brand-badge"
          style={{ cursor: 'pointer', background: 'rgba(56, 189, 248, 0.1)', padding: '0.4rem 0.8rem' }}
          onClick={() => {
            fetchDashboardMetrics().then(setMetrics);
            handleFilter();
          }}
        >
          🔄 Refresh Metrics
        </button>
      </div>

      {/* Metrics Row */}
      {metrics && (
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-label">Gross Revenue</div>
            <div className="metric-value" style={{ color: 'var(--accent-emerald)' }}>
              ${metrics.gross_revenue.toLocaleString()}
            </div>
            <div className="metric-sub">Processed booking volume</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Confirmed Sessions</div>
            <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
              {metrics.confirmed_appointments}
            </div>
            <div className="metric-sub">{metrics.upcoming_appointments} upcoming in queue</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Completed Sessions</div>
            <div className="metric-value" style={{ color: '#a5b4fc' }}>
              {metrics.completed_appointments}
            </div>
            <div className="metric-sub">Past consultations delivered</div>
          </div>

          <div className="metric-card">
            <div className="metric-label">Reminders Dispatched</div>
            <div className="metric-value" style={{ color: 'var(--accent-purple)' }}>
              {metrics.reminders_dispatched}
            </div>
            <div className="metric-sub">Email, SMS & ICS events</div>
          </div>
        </div>
      )}

      {/* Filter Controls */}
      <div className="calendar-control-bar" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Filter By:</span>
          <select
            id="filter-provider-select"
            className="date-input-field"
            value={selectedProviderId}
            onChange={(e) => setSelectedProviderId(e.target.value)}
          >
            <option value="">All Consultants ({providers.length})</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.timezone})
              </option>
            ))}
          </select>

          <select
            id="filter-status-select"
            className="date-input-field"
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="RESCHEDULED">Rescheduled</option>
          </select>
        </div>

        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Showing <strong>{appointments.length}</strong> appointments
        </div>
      </div>

      {/* Appointment Table */}
      {loading ? (
        <div className="empty-slots-state">
          <p>Loading master schedule...</p>
        </div>
      ) : appointments.length === 0 ? (
        <div className="empty-slots-state">
          <p>No appointments match the selected filter criteria.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Client Name & Email</th>
                <th>Consultant</th>
                <th>Service Name</th>
                <th>Start Time (UTC)</th>
                <th>Status</th>
                <th>Version</th>
                <th>Conference Link</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map((apt) => {
                const start = new Date(apt.start_time);
                return (
                  <tr key={apt.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{apt.customer_name}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{apt.customer_email}</div>
                    </td>
                    <td>
                      <div style={{ color: 'var(--accent-cyan)', fontWeight: 500 }}>{apt.provider_name}</div>
                    </td>
                    <td>{apt.service_name}</td>
                    <td>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                        {start.toLocaleDateString()} {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </td>
                    <td>
                      <span className={`status-pill ${apt.status.toLowerCase()}`}>
                        {apt.status}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>v{apt.version}</span>
                    </td>
                    <td>
                      {apt.meeting_link && apt.status !== 'CANCELLED' ? (
                        <a
                          href={apt.meeting_link}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: 'var(--accent-cyan)', textDecoration: 'none', fontSize: '0.82rem' }}
                        >
                          Join Room ↗
                        </a>
                      ) : (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
