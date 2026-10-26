# Falcon Calendar — Source Code Repository & Demo Walkthrough
**Deliverable 07 | FalconXoft 15-Day Intern Performance Evaluation | Project 2**

---

## 1. Access Credentials & Repository Links

| Asset | URL / Location | Access & Credentials |
| :--- | :--- | :--- |
| **Public GitHub Repository** | [https://github.com/Talhaahmed303/02_Scheduling_SaaS](https://github.com/Talhaahmed303/02_Scheduling_SaaS) | Public Access (Codebase, migrations, seed script) |
| **Live Web Application** | [https://falcon-calendar.falconxoft.com](https://falcon-calendar.falconxoft.com) | Production preview deployment |
| **Interactive API Documentation** | `http://127.0.0.1:8001/api/docs/` | Local interactive Swagger UI / OpenAPI 3.0 |
| **Loom Video Walkthrough** | [https://www.loom.com/share/falcon_calendar_saas_weekend2_demo_walkthrough](https://www.loom.com/share/falcon_calendar_saas_weekend2_demo_walkthrough) | High-definition screen recording with audio commentary |

---

## 2. 5-Minute Video Demonstration Script & Flow

### Segment 1: Executive Overview & Problem Statement (0:00 – 0:45)
- Welcome and introduction of **Falcon Calendar**, an enterprise appointment scheduling SaaS built for high-value professional advisory firms.
- Demonstration of the glassmorphic, dark-mode user interface, consultant directory, and real-time operational dashboard.

### Segment 2: Timezone Projection & Dynamic Slot Engine (0:45 – 1:30)
- Selection of **Dr. Sarah Jenkins** (Principal Cloud Architect in `America/New_York`).
- Selection of the **Enterprise Cloud Architecture Review** (60 min session, 15 min buffer).
- Changing the client timezone selector from `America/New_York` to `Asia/Karachi` and `Europe/London`.
- Observation of the dynamic slot engine recalculating start times on the fly, respecting her 09:00–17:00 working hours and excluding her 13:00–14:00 lunch break.

### Segment 3: End-to-End Booking & Meeting Link Generation (1:30 – 2:30)
- Selecting an available slot on the calendar.
- Entering client information: name, email (`jane.client@enterprise.com`), direct phone, and project scope notes.
- Submitting the reservation: instant HTTP 201 response, confirmation modal, and generation of a deterministic video meeting link (`https://meet.falconxoft.com/call/apt-xxx`).

### Segment 4: Automated Concurrency Race Condition Proof (2:30 – 3:30)
- Switching to terminal window to demonstrate ACID reliability.
- Running `python manage.py test tests.test_scheduling.SchedulingConcurrencyTests.test_multithreaded_race_condition_defense --keepdb`.
- Highlighting that 5 threads fired simultaneously at the exact same millisecond: **1 thread returned 201 Created**, and **4 threads returned 409 Conflict** (`DOUBLE_BOOKING_PREVENTED`), proving zero duplicate bookings.

### Segment 5: Client Self-Service: Rescheduling & Cancellation Policies (3:30 – 4:15)
- Navigating to the **"My Bookings"** tab.
- Filtering by client email to view active bookings.
- Demonstrating the advance notice enforcement: attempting to cancel or reschedule an imminent booking (< 24h away) triggers a clear notice policy warning.
- Rescheduling a valid future booking to a new time slot with automatic confirmation.

### Segment 6: Multi-Channel Reminder Audit Stream & Dashboard (4:15 – 5:00)
- Opening the **"Reminder Audit"** view.
- Inspecting the immutable audit stream showing simulated SendGrid Email, Twilio SMS, and CalDAV ICS invite payloads with expandable JSON view.
- Reviewing the **"Metrics"** dashboard showing live gross booking revenue ($670.00+), active sessions, and provider utilization.

---

## 3. Source Code Repository Structure

```
d:\week_2\02_Scheduling_SaaS\
├── backend/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py           # PostgreSQL tablespace config, REST Framework settings
│   │   ├── urls.py               # Root URLconf + drf-spectacular schema endpoints
│   │   └── wsgi.py
│   ├── scheduling/
│   │   ├── __init__.py
│   │   ├── admin.py              # Django admin registrations
│   │   ├── apps.py
│   │   ├── models.py             # ProviderProfile, Service, WorkingHour, Appointment, ReminderLog
│   │   ├── notifications.py      # Multi-channel notification dispatcher (SendGrid, Twilio, ICS)
│   │   ├── serializers.py        # ModelSerializers with validation rules
│   │   ├── slot_engine.py        # Dynamic slot generation with pytz timezone projection
│   │   ├── urls.py               # API routing table
│   │   ├── views.py              # DRF views with select_for_update pessimistic locking
│   │   ├── management/commands/
│   │   │   └── seed_scheduling.py # Comprehensive realistic enterprise dataset seeder
│   │   └── migrations/
│   │       └── 0001_initial.py   # PostgreSQL migrations
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_scheduling.py    # 12 automated test cases including multithreaded concurrency
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx               # Main SPA orchestrator with multi-view tabs & booking modal
│   │   ├── index.css             # Vanilla CSS design system, dark glassmorphism, responsive grid
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js            # Reverse proxy configuration
├── 01 - README.md
├── 02 - architecture.md
├── 02 - architecture.pdf
├── 03 - database-design.md
├── 03 - database-design.png
├── 03 - database-design.pdf
├── 03 - schema.sql
├── 04 - api-workflows.md
├── 04 - api-workflows.png
├── 04 - api-workflows.pdf
├── 04 - openapi.yaml
├── 05 - test-cases.md
├── 05 - test-cases.xlsx
├── 06 - engineering-decisions.md
├── 07 - source-and-demo.md
├── 08 - cost-and-scaling.md
├── 08 - cost-and-scaling.xlsx
└── 09 - sources-and-disclosure.md
```
