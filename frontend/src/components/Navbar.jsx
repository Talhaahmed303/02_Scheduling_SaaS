import React from 'react';

const COMMON_TIMEZONES = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Asia/Dubai',
  'Asia/Karachi',
  'Asia/Tokyo',
  'UTC',
];

export default function Navbar({ activeTab, setActiveTab, clientTz, setClientTz }) {
  return (
    <header className="navbar">
      <div className="nav-brand" onClick={() => setActiveTab('book')}>
        <div className="brand-icon">F</div>
        <div>
          <div className="brand-name">Falcon Calendar</div>
        </div>
        <span className="brand-badge">SaaS v2.0</span>
      </div>

      <nav className="nav-tabs">
        <button
          id="nav-tab-book"
          className={`nav-tab-btn ${activeTab === 'book' ? 'active' : ''}`}
          onClick={() => setActiveTab('book')}
        >
          <span>📅</span> Book Session
        </button>
        <button
          id="nav-tab-my-bookings"
          className={`nav-tab-btn ${activeTab === 'my-bookings' ? 'active' : ''}`}
          onClick={() => setActiveTab('my-bookings')}
        >
          <span>📋</span> My Bookings
        </button>
        <button
          id="nav-tab-provider-ops"
          className={`nav-tab-btn ${activeTab === 'provider-ops' ? 'active' : ''}`}
          onClick={() => setActiveTab('provider-ops')}
        >
          <span>📊</span> Operations
        </button>
        <button
          id="nav-tab-reminders"
          className={`nav-tab-btn ${activeTab === 'reminders' ? 'active' : ''}`}
          onClick={() => setActiveTab('reminders')}
        >
          <span>🔔</span> Reminder Audit
        </button>
      </nav>

      <div className="nav-actions">
        <div className="tz-selector-pill">
          <span>🌐 Timezone:</span>
          <select
            id="client-tz-select"
            value={clientTz}
            onChange={(e) => setClientTz(e.target.value)}
          >
            {COMMON_TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>
                {tz}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  );
}
