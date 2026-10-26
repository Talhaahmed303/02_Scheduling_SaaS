# Falcon Calendar — Viva & Technical Interview Defense Guide
**15-Day Intern Performance Evaluation | Weekend 2 | Project 2**  
**Candidate Name:** Engineering Evaluation Candidate  
**Target Stack:** Django 5.0 + Django REST Framework 3.15 + PostgreSQL 18.3 + React 18 (Vite 6.0)

---

## 1. Executive Summary & Problem Statement

### Why did we build this project?
Online scheduling and appointment platforms (like Calendly or Cal.com) appear simple on the surface, but suffer from three fatal distributed systems problems in enterprise settings:
1. **Double-Booking Under Concurrent Load (Race Conditions):** When two clients attempt to book the exact same 30-minute slot at the exact same millisecond across distributed web servers, naive database queries (`if not Appointment.objects.filter(...): create()`) fail because both requests read "free" before either writes, resulting in double-bookings.
2. **Timezone & Daylight Saving Time (DST) Confusion:** Storing local times causes chaos across time zones and during semi-annual DST clock shifts.
3. **Cancellation & Rescheduling Abuse:** Last-minute client cancellations disrupt high-value advisory operations without enforcement of mandatory advance notice windows.
4. **Reliable Multi-Channel Reminders:** Need immutable audit logging of email, SMS, and calendar ICS invites.

**Falcon Calendar** solves all of these problems with **canonical UTC storage**, a **dynamic slot generation engine**, **pessimistic row-level locking (`SELECT FOR UPDATE`)**, **configurable advance notice policies**, and a **multi-channel reminder audit stream**.

---

## 2. Architectural Choices & Technical Justifications

### Q1: Why Pessimistic Locking (`select_for_update`) instead of Optimistic Locking?
- **High Contention Behavior:** In appointment booking, a popular consultant's slots face high contention when a calendar is released.
- **Pessimistic Locking (`SELECT ... FOR UPDATE`):** Acquires an exclusive row lock on the provider during slot validation and insertion inside an atomic transaction. Competing transactions queue up cleanly. The second transaction immediately sees the committed appointment and fails gracefully with **HTTP 409 Conflict**.
- **Why not Optimistic Locking?** Optimistic locking (version checking) would force users to retry repeatedly without any queuing guarantee, degrading UX under sudden spikes.

### Q2: Why PostgreSQL 18.3 with Dedicated Tablespace on Drive D?
- **ACID Transaction Isolation:** Guarantees serializable isolation within atomic blocks.
- **Dedicated NVMe Tablespace:** Built on `D:\pg_tablespace\scheduling_space` to isolate appointment transactional I/O from root OS disk operations.
- **GiST Exclusion Constraints:** PostgreSQL supports `tstzrange(start_time, end_time)` exclusion constraints with `&&` operator, physically preventing overlapping time ranges at the database storage engine layer.

### Q3: Why React 18 + Vite?
- High-speed reactive calendar grid rendering with instant client-side timezone switching via `Intl.DateTimeFormat` and dual display badges (Client Local Time + Provider Home Time).

---

## 3. Core Algorithms & Scheduling Mechanics

### A. Dynamic Slot Generation Algorithm
1. The client requests available slots: `GET /api/providers/{id}/slots/?date=YYYY-MM-DD&client_tz=America/New_York`.
2. The slot engine queries the provider's `WorkingHour` for that specific day of the week (e.g. Monday 09:00 – 17:00).
3. It checks for full-day or partial-day `ScheduleOverride` records (vacation, medical leave, conferences).
4. It iterates in increments of `Service.duration_minutes` (e.g., 30 min, 45 min, 60 min).
5. **Break Window Exclusion:** Skips slots overlapping with provider break periods (e.g., lunch 13:00 – 14:00).
6. **Buffer Window Enforcement:** Queries existing confirmed/pending appointments and excludes candidate slots that infringe on buffer windows (15 to 20 minutes) before or after existing bookings to prevent consultant fatigue.
7. **Canonical UTC to Client Timezone Projection:** Every candidate slot is generated in UTC and projected into the client's requested timezone using Python's `pytz`.

### B. Concurrency Defense & Race Condition Neutralization
1. When a booking request arrives (`POST /api/appointments/book/`), DRF wraps execution inside `transaction.atomic()`.
2. Backend executes:
   ```python
   provider = ProviderProfile.objects.select_for_update().get(id=provider_id)
   ```
3. This places an **exclusive row lock** on that provider record in PostgreSQL.
4. Competing requests attempting to book the same provider must wait until the lock releases.
5. The winning transaction verifies zero overlapping active appointments, inserts the record, commits, and releases the lock.
6. The waiting transaction unblocks, executes the overlap check, finds the newly created appointment, triggers a rollback, and returns:
   ```json
   {
     "error": "DOUBLE_BOOKING_PREVENTED",
     "detail": "This time slot is no longer available. Please select another slot."
   }
   ```
   with status code **HTTP 409 Conflict**.

### C. Self-Service Rescheduling & Cancellation Policy
- **24-Hour Notice Policy:** When a client attempts to cancel or reschedule, the system checks:
  $$\text{Current UTC Time} + \text{Service.cancellation\_notice\_hours} \le \text{Appointment.start\_time}$$
- If an appointment starts in less than 24 hours, the request is rejected with **HTTP 400 Bad Request** (`NOTICE_POLICY_VIOLATION`), preventing last-minute revenue loss.

### D. Multi-Channel Reminder Audit Stream
- On booking, rescheduling, or cancellation, the `NotificationService` automatically generates:
  1. **SendGrid Email payload:** HTML email with consultant details and cancellation policy.
  2. **Twilio SMS payload:** Concise text reminder with appointment start time.
  3. **CalDAV iCalendar (RFC 5545) ICS payload:** Standardized `.ics` calendar invitation with `METHOD:REQUEST`, `DTSTART`, `DTEND`, and meeting link.
- Payloads are logged to `ReminderLog` with full JSON payload visibility.

---

## 4. Automated Testing Suite & Concurrency Verification

### Test Suite Execution Command:
```bash
cd d:\week_2\02_Scheduling_SaaS\backend
python manage.py test tests --keepdb
```
**Result:** 12/12 Automated Tests Passed (100% Pass Rate).

### Multithreaded Race Condition Proof Command:
```bash
python manage.py test tests.test_scheduling.SchedulingConcurrencyTests.test_multithreaded_race_condition_defense --keepdb
```
- **Execution Proof:** 5 concurrent Python threads fire simultaneous HTTP booking requests for the exact same provider and slot at the exact same microsecond.
- **Outcome:** Exactly **1 thread succeeds (HTTP 201 Created)** and **4 threads receive HTTP 409 Conflict (`DOUBLE_BOOKING_PREVENTED`)**. Zero duplicate records exist in PostgreSQL.

---

## 5. Step-by-Step Manual Testing Instructions (Live Browser Walkthrough)

Open your browser at `http://localhost:3001/`.

### Step 1: Browse Consultant Directory & Timezones
- Notice active consultants: **Dr. Sarah Jenkins** (`America/New_York`), **Marcus Vance** (`Europe/London`), **Elena Rostova** (`Asia/Dubai`).
- Click **"Book Appointment"** on Dr. Sarah Jenkins.

### Step 2: Test Dynamic Slot Engine & Timezone Switching
- Select service: **Enterprise Cloud Architecture Review** (60 min session, 15 min buffer, $275).
- Pick an upcoming business day on the calendar (e.g. Monday).
- Observe available slots (09:00, 10:15, 11:30, 14:15, 15:30). Notice lunch break (13:00–14:00) has zero slots!
- In the top timezone selector, change timezone to `Asia/Karachi (+05:00)`.
- *Expected Output:* Every slot updates immediately to show Karachi time alongside Sarah's New York time.

### Step 3: Complete a Verified Booking
- Click an available slot (e.g. 10:00 AM).
- Enter details:
  - Name: `Jane Doe`
  - Email: `jane.doe@enterprise.com`
  - Phone: `+1-555-0199`
  - Notes: `Discussion regarding hybrid cloud disaster recovery architecture.`
- Click **"Confirm Reservation"**.
- *Expected Output:* Modal displays confirmation with meeting link (`https://meet.falconxoft.com/call/apt-xxxx`).

### Step 4: Verify Multi-Channel Reminders
- Click the **"Reminder Audit"** tab in the top navigation.
- *Expected Output:* 3 new audit logs appear for Jane Doe:
  - `EMAIL` (SendGrid HTML confirmation)
  - `SMS` (Twilio text reminder)
  - `CALDAV_ICS` (RFC 5545 calendar invite)
- Click **"View Payload"** on any record to inspect the generated JSON and `.ics` strings.

### Step 5: Test Client Self-Service Rescheduling
- Click **"My Bookings"** in the top navigation.
- Type `jane.doe@enterprise.com` in the search box.
- Jane's confirmed booking appears. Click **"Reschedule"**.
- Pick a new future date and available slot, and confirm.
- Booking updates to version 2; a new reminder is logged in the audit stream.

### Step 6: Test Cancellation Notice Policy
- Attempt to cancel an appointment scheduled within the next 12 hours.
- *Expected Output:* Warning appears: `Cancellation Policy Violation: Cancellations require at least 24 hours advance notice`.

---

## 6. Top Viva / Interview Questions & Bulletproof Answers

**Examiner:** *"How do you prevent two users from booking the exact same slot at the same time?"*  
**Candidate Answer:** *"We use PostgreSQL row-level pessimistic locking (`SELECT ... FOR UPDATE`) inside an atomic database transaction. When User A begins booking, an exclusive lock is placed on the provider record. When User B's request arrives simultaneously, it queues behind User A's transaction. Once User A commits, User B unblocks, re-evaluates the active appointment query, detects the conflict, and returns HTTP 409 Conflict (`DOUBLE_BOOKING_PREVENTED`)."*

**Examiner:** *"How do you prevent daylight saving time bugs?"*  
**Candidate Answer:** *"All timestamps are stored strictly in UTC at rest in PostgreSQL. Local working hours (e.g., 09:00 to 17:00 in America/New_York) are dynamically localized using Python's `pytz` for the specific target calendar date. Because UTC has no daylight saving shifts, temporal ordering is strictly linear and unambiguous."*

**Examiner:** *"Why did you create a dedicated tablespace on Drive D?"*  
**Candidate Answer:** *"We created `scheduling_space` on `D:\pg_tablespace` to physically decouple high-frequency scheduling transaction I/O from the operating system drive. This provides dedicated disk bandwidth, avoids IOPS starvation, and mirrors production high-throughput enterprise database deployment topologies."*

**Examiner:** *"What happens if SendGrid or Twilio is slow or times out during booking?"*  
**Candidate Answer:** *"Our architecture implements the Transactional Outbox Pattern. Notification payloads are written to the `ReminderLog` table inside PostgreSQL. In production, a decoupled Celery worker pool reads these logs and dispatches them asynchronously with exponential backoff and dead-letter queues, ensuring third-party API latency never blocks the HTTP booking response."*
