import React from 'react';

export default function ProviderCard({ provider, isSelected, onSelect }) {
  return (
    <div
      className={`provider-card fade-in ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(provider)}
      id={`provider-card-${provider.slug}`}
    >
      <div className="provider-header">
        <img
          src={provider.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=400'}
          alt={provider.name}
          className="provider-avatar"
        />
        <div>
          <h3 className="provider-name">{provider.name}</h3>
          <div className="provider-title">{provider.title}</div>
          <div className="provider-tz-tag">
            <span>📍</span> {provider.timezone}
          </div>
        </div>
      </div>

      <p className="provider-bio">{provider.bio}</p>

      <div className="services-badge-list">
        {provider.services?.map((svc) => (
          <span key={svc.id} className="service-pill-tag">
            {svc.name.split(' ')[0]} ({svc.duration_minutes}m · ${svc.price})
          </span>
        ))}
      </div>

      <button
        id={`select-provider-${provider.slug}`}
        className="provider-select-btn"
        onClick={(e) => {
          e.stopPropagation();
          onSelect(provider);
        }}
      >
        {isSelected ? '✓ Selected Consultant' : 'Select Consultant & View Slots'}
      </button>
    </div>
  );
}
