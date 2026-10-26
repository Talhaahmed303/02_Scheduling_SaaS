const API_BASE = '/api';

export async function fetchProviders() {
  const res = await fetch(`${API_BASE}/providers/`);
  if (!res.ok) throw new Error('Failed to fetch providers');
  const data = await res.json();
  return data.results || data;
}

export async function fetchProviderDetail(providerId) {
  const res = await fetch(`${API_BASE}/providers/${providerId}/`);
  if (!res.ok) throw new Error('Failed to fetch provider detail');
  return res.json();
}

export async function fetchProviderSlots(providerId, serviceId, dateStr, clientTz) {
  const params = new URLSearchParams({
    service_id: serviceId,
    date: dateStr,
    client_tz: clientTz || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  });
  const res = await fetch(`${API_BASE}/providers/${providerId}/slots/?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || 'Failed to fetch available slots');
  }
  return res.json();
}

export async function bookAppointment(payload) {
  const res = await fetch(`${API_BASE}/appointments/book/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || (data.details ? JSON.stringify(data.details) : 'Booking failed'));
  }
  return data;
}

export async function rescheduleAppointment(appointmentId, newStartTime, clientTz) {
  const res = await fetch(`${API_BASE}/appointments/${appointmentId}/reschedule/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      new_start_time: newStartTime,
      customer_timezone: clientTz || 'UTC',
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || 'Rescheduling failed');
  }
  return data;
}

export async function cancelAppointment(appointmentId, reason) {
  const res = await fetch(`${API_BASE}/appointments/${appointmentId}/cancel/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason: reason || 'Customer requested cancellation.' }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.message || 'Cancellation failed');
  }
  return data;
}

export async function fetchAppointments(params = {}) {
  const query = new URLSearchParams();
  if (params.email) query.append('email', params.email);
  if (params.provider_id) query.append('provider_id', params.provider_id);
  if (params.status) query.append('status', params.status);
  
  const res = await fetch(`${API_BASE}/appointments/?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch appointments');
  const data = await res.json();
  return data.results || data;
}

export async function fetchReminders(appointmentId) {
  const query = appointmentId ? `?appointment_id=${appointmentId}` : '';
  const res = await fetch(`${API_BASE}/reminders/${query}`);
  if (!res.ok) throw new Error('Failed to fetch reminder audit logs');
  const data = await res.json();
  return data.results || data;
}

export async function fetchDashboardMetrics() {
  const res = await fetch(`${API_BASE}/dashboard/metrics/`);
  if (!res.ok) throw new Error('Failed to fetch operational metrics');
  return res.json();
}
