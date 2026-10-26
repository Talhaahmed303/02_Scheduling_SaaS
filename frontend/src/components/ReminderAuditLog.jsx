import React, { useState, useEffect } from 'react';
import { fetchReminders } from '../api';

export default function ReminderAuditLog() {
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  const loadLogs = () => {
    setLoading(true);
    fetchReminders()
      .then((data) => {
        setReminders(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div className="fade-in">
      <div className="section-header">
        <div>
          <h2 className="section-title">Automated Reminder & Notification Audit</h2>
          <p className="section-desc">
            Immutable log of dispatched multi-channel alerts (SendGrid Email, Twilio SMS, CalDAV ICS invites).
          </p>
        </div>
        <button
          className="brand-badge"
          style={{ cursor: 'pointer', background: 'rgba(56, 189, 248, 0.1)', padding: '0.4rem 0.8rem' }}
          onClick={loadLogs}
        >
          🔄 Refresh Audit Feed
        </button>
      </div>

      <div style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
        <span className="brand-badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-emerald)' }}>
          ✓ Mock Dispatch Active
        </span>
        <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Total logged notification dispatches: <strong>{reminders.length}</strong>
        </span>
      </div>

      {loading ? (
        <div className="empty-slots-state">
          <p>Loading reminder event audit logs...</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Channel</th>
                <th>Recipient</th>
                <th>Notification Subject</th>
                <th>Dispatched At</th>
                <th>Status</th>
                <th>Payload</th>
              </tr>
            </thead>
            <tbody>
              {reminders.map((log) => {
                const isExpanded = expandedId === log.id;
                const sentTime = log.sent_at ? new Date(log.sent_at) : null;

                return (
                  <React.Fragment key={log.id}>
                    <tr>
                      <td>
                        <span
                          className="brand-badge"
                          style={{
                            background:
                              log.channel === 'EMAIL'
                                ? 'rgba(56, 189, 248, 0.15)'
                                : log.channel === 'SMS'
                                ? 'rgba(168, 85, 247, 0.15)'
                                : 'rgba(99, 102, 241, 0.15)',
                            color:
                              log.channel === 'EMAIL'
                                ? 'var(--accent-cyan)'
                                : log.channel === 'SMS'
                                ? 'var(--accent-purple)'
                                : '#a5b4fc',
                          }}
                        >
                          {log.channel}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem' }}>
                        {log.recipient}
                      </td>
                      <td style={{ fontWeight: 500 }}>{log.subject}</td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        {sentTime
                          ? `${sentTime.toLocaleDateString()} ${sentTime.toLocaleTimeString()}`
                          : 'Pending Queue'}
                      </td>
                      <td>
                        <span className={`status-pill ${log.status === 'DISPATCHED' ? 'confirmed' : 'completed'}`}>
                          {log.status}
                        </span>
                      </td>
                      <td>
                        <button
                          className="provider-select-btn"
                          style={{ padding: '0.25rem 0.6rem', fontSize: '0.74rem' }}
                          onClick={() => setExpandedId(isExpanded ? null : log.id)}
                        >
                          {isExpanded ? 'Hide Payload' : 'View Payload'}
                        </button>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr>
                        <td colSpan="6" style={{ background: 'rgba(0, 0, 0, 0.25)', padding: '1rem 1.5rem' }}>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                            Simulated Gateway Dispatcher Payload:
                          </div>
                          <pre
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.78rem',
                              color: '#38bdf8',
                              background: '#070b14',
                              padding: '0.8rem',
                              borderRadius: '6px',
                              overflowX: 'auto',
                            }}
                          >
                            {JSON.stringify(log.payload_preview, null, 2)}
                          </pre>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
