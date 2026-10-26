# Falcon Calendar — Enterprise Appointment & Scheduling SaaS
**FalconXoft 15-Day Intern Performance Evaluation | Weekend 2 | Project 2**

---

## 1. Project Purpose & Executive Summary
**Falcon Calendar** is an enterprise-grade appointment and calendar scheduling platform designed for high-value professional services (systems architecture, cybersecurity compliance, executive advisory, and healthcare). 

The platform solves the critical challenges inherent in distributed scheduling:
- **Zero Double-Bookings under Concurrent Load:** Employs atomic database transactions with pessimistic row-level locking (`SELECT ... FOR UPDATE`) and PostgreSQL exclusion logic to eliminate race conditions.
- **Flawless Multi-Timezone & DST Precision:** Canonical UTC timestamps are stored at rest, while dynamic timezone projections translate working hours, break periods, and calendar slots into the client's local timezone.
- **Defensive Cancellation & Rescheduling Policies:** Configurable advance notice rules (e.g. mandatory 24-hour lead time) prevent last-minute schedule disruption while providing self-service management for clients.
- **Multi-Channel Notification & Reminder Auditing:** Every booking, rescheduling, and cancellation event automatically triggers simulated SendGrid (Email), Twilio (SMS), and CalDAV (ICS) reminders with full payload inspection.

---

## 2. Technology Stack

| Layer | Technology | Specification & Role |
| :--- | :--- | :--- |
| **Frontend UI** | **React 18.3 + Vite 6.0** | Modern SPA with Vanilla CSS design system, dark glassmorphism, responsive calendar grid, and timezone projection |
| **Backend API** | **Django 5.0 + Django REST Framework 3.15** | High-throughput REST API with pessimistic locking, dynamic slot generation algorithm, and OpenAPI schema |
| **Relational Database** | **PostgreSQL 18.3** | ACID relational storage deployed on dedicated `scheduling_space` tablespace on Drive D (`D:\pg_tablespace`) |
| **API Schema Docs** | **drf-spectacular (OpenAPI 3.0)** | Auto-generated interactive Swagger UI (`/api/docs/`) and Redoc (`/api/redoc/`) |
| **Notification Engine** | **Mock Enterprise Notification Dispatcher** | Multi-channel dispatcher logging SendGrid Email, Twilio SMS, and Calendar ICS invite payloads |
| **Automated Testing** | **Django Test Runner & Concurrency Suite** | 12 automated unit, integration, and multithreaded race-condition test cases |

---

## 3. System Scope & Feature Breakdown

### A. Provider & Service Catalog
- Multi-provider directory with detailed professional biographies, designation titles, and home timezones (`America/New_York`, `Europe/London`, `Asia/Dubai`, `Asia/Karachi`).
- Service profiles with customizable durations (30m, 45m, 60m), mandatory buffer intervals (15m–20m), fixed pricing ($150–$275), and cancellation notice requirements.

### B. Dynamic Slot Generation Algorithm
- Evaluates provider working hours for any selected calendar date (defaulting to 09:00–17:00).
- Excludes recurring lunch break intervals (13:00–14:00) and full-day schedule overrides (holidays, medical leave).
- Queries PostgreSQL for active appointments (`CONFIRMED`, `PENDING`) and applies buffer windows to prevent back-to-back fatigue.
- Projects slot times into the client's local timezone with dual display badges.

### C. Atomic Concurrency & Race Condition Defense
- Prevents double bookings across distributed web servers using PostgreSQL transaction isolation and row locks.
- Simultaneous concurrent booking attempts on the same slot result in exactly **one** successful reservation (HTTP 201) and all competing attempts receiving **HTTP 409 Conflict** with `DOUBLE_BOOKING_PREVENTED`.

### D. Client Self-Service Management (Reschedule & Cancel)
- Clients can look up bookings by email.
- Reschedule to a future available slot with atomic concurrency verification.
- Cancel with explanation, checking against advance notice policies (e.g., minimum 24 hours).

### E. Operational Dashboard & Real-Time Telemetry
- Real-time gross booking revenue calculation ($670+ live).
- Session counts across confirmed, completed, cancelled, and upcoming statuses.
- Provider and status filtering for operations staff.

### F. Multi-Channel Reminder Audit Stream
- Immutable audit log tracking all automated notifications.
- Expandable JSON payload inspector showing simulated gateway payloads.

---

## 4. User Flows

### Flow 1: End-to-End Client Consultation Booking
```
Client Selects Consultant -> Picks Service Tier -> Picks Calendar Date -> 
Dynamic Slot Engine Computes Available Timeslots in Client Timezone -> 
Client Selects Slot -> Completes Name, Email, Notes in Modal -> 
Backend Executes select_for_update() Lock & Overlap Check -> 
Booking Confirmed (HTTP 201) -> Meeting Link Generated -> 
Email & Calendar ICS Dispatched -> Audit Log Updated
```

### Flow 2: Client Rescheduling with Notice Validation
```
Client Navigates to "My Bookings" -> Searches by Email -> 
Clicks "Reschedule" -> Selects New Target Date & Time -> 
Backend Checks Notice Policy (Current Time + Service.cancellation_notice_hours <= Start Time) -> 
Acquires Atomic Lock on New Slot -> Updates Start/End Time and Version -> 
Reschedule Confirmation Dispatched
```

---

## 5. Local Setup & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm 10+
- PostgreSQL 18+ (running locally on port 5432)

### Step 1: Backend Setup
```bash
cd d:\week_2\02_Scheduling_SaaS\backend

# Install python dependencies (if not already installed globally)
pip install -r requirements.txt

# Create PostgreSQL tablespace and database (already performed in evaluation environment)
# Tablespace: D:\pg_tablespace
# Database: scheduling_saas_db

# Run migrations
python manage.py migrate

# Seed database with realistic enterprise dataset
python manage.py seed_scheduling

# Run automated tests (including 5-thread concurrency race defense)
python manage.py test tests --keepdb

# Start DRF Backend Server on port 8001
python manage.py runserver 127.0.0.1:8001
```
*Backend API Docs live at:* `http://127.0.0.1:8001/api/docs/`

### Step 2: Frontend Setup
```bash
cd d:\week_2\02_Scheduling_SaaS\frontend

# Install node dependencies
npm install

# Start Vite dev server on port 3001
npm run dev
```
*Frontend live at:* `http://localhost:3001/`

---

## 6. Known Limitations & Production Enhancements
1. **Mock Notification Gateway:** Current implementation logs SendGrid, Twilio, and CalDAV payloads to `ReminderLog` synchronously. In production, Celery + Redis workers should be utilized with Exponential Backoff retries.
2. **Video Room Integration:** Currently generates secure deterministic meeting URLs (`https://meet.falconxoft.com/call/apt-xxxx`). Production would integrate Zoom SDK or Daily.co API webhooks.
3. **Payment Gateway:** Service pricing is displayed and gross revenue is aggregated. Production would integrate Stripe Elements with pre-authorization holds prior to slot locking.
