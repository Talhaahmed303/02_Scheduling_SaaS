# Falcon Calendar — 3-5 Minute Product Walkthrough Video Script
**Project 2 | Weekend 2 Intern Engineering Evaluation | Video Deliverable**  
**Recommended Recording Tool:** Loom, OBS Studio, or ScreenPal  
**Target Video Length:** 3 minutes 45 seconds to 4 minutes 30 seconds  
**Local Test URL:** `http://localhost:3001/`

---

## Pre-Recording Checklist (Before pressing Record)
1. Ensure Django Backend is running: `python manage.py runserver 127.0.0.1:8001` (in `02_Scheduling_SaaS/backend`)
2. Ensure Frontend is running: `npm run dev` (in `02_Scheduling_SaaS/frontend`)
3. Open browser in full screen at `http://localhost:3001/`
4. Have a second terminal window open in `d:\week_2\02_Scheduling_SaaS\backend` ready to run the multithreaded concurrency test command.

---

## Second-by-Second Video Script

### ⏱️ Segment 1: Executive Overview & Problem Statement (0:00 – 0:45)
**Visual on Screen:**
- Display the modern glassmorphic interface at `http://localhost:3001/`.
- Show the Consultant Directory featuring **Dr. Sarah Jenkins**, **Marcus Vance**, and **Elena Rostova**.
- Point to the gross revenue ($670+) and active booking counters in the top telemetry bar.

**Spoken Voiceover Script (English):**
> *"Hello everyone! Welcome to the product demonstration of Falcon Calendar, an enterprise appointment and scheduling platform engineered for high-value professional advisory firms. I'm presenting this for Project 2 of the Weekend 2 Intern Engineering Evaluation.*
>
> *Online scheduling faces two critical engineering traps: race conditions that cause double-bookings, and timezone calculation bugs. To solve this, I've built a full-stack platform using Django REST Framework, PostgreSQL 18 on a dedicated NVMe tablespace, and React 18 with Vite.*
>
> *Let's walk through an end-to-end client consultation booking."*

---

### ⏱️ Segment 2: Timezone Projection & Dynamic Slot Engine (0:45 – 1:30)
**Visual on Screen:**
- Click **"Book Appointment"** on **Dr. Sarah Jenkins** (Principal Cloud Architect based in `America/New_York`).
- Select the service: **Enterprise Cloud Architecture Review** (60 min session, 15 min buffer, $275).
- Pick an upcoming business day on the calendar.
- Change the client timezone selector at the top from `America/New_York` to `Asia/Karachi (+05:00)`.

**Spoken Voiceover Script (English):**
> *"Here, we select Dr. Sarah Jenkins, who operates in America/New_York. Her working hours are 9 AM to 5 PM with a mandatory lunch break from 1 PM to 2 PM.*
>
> *Watch what happens when an overseas client in Pakistan books a session. When I change the client timezone selector to Asia/Karachi, our dynamic slot engine recalculates every available timeslot in real time using Python pytz.*
>
> *Notice that each slot pill shows dual badges: the client's local time alongside Sarah's home time, and our lunch break and mandatory 15-minute buffers are automatically excluded to prevent consultant fatigue."*

---

### ⏱️ Segment 3: End-to-End Booking & Meeting Link Generation (1:30 – 2:30)
**Visual on Screen:**
- Click an available timeslot (e.g. 10:00 AM).
- Fill out the booking modal:
  - Name: `Jane Doe`
  - Email: `jane.doe@enterprise.com`
  - Phone: `+1-555-0199`
  - Notes: `Discussion regarding hybrid cloud disaster recovery architecture.`
- Click **"Confirm Reservation"**.
- Confirmation modal appears with generated meeting URL: `https://meet.falconxoft.com/call/apt-xxxx`.

**Spoken Voiceover Script (English):**
> *"Now let's complete the reservation. I'll enter Jane Doe's details and click 'Confirm Reservation'.*
>
> *Instantly, we receive an HTTP 201 response. An atomic database transaction has committed the booking, generated a secure deterministic video call link, and dispatched our multi-channel notification suite."*

---

### ⏱️ Segment 4: Concurrency Defense — Automated Multithreaded Race Test (2:30 – 3:30)
**Visual on Screen:**
- Switch to the terminal window.
- Type and run:
  ```bash
  python manage.py test tests.test_scheduling.SchedulingConcurrencyTests.test_multithreaded_race_condition_defense --keepdb
  ```
- Highlight the output: `Ran 1 test in 0.142s ... OK`.

**Spoken Voiceover Script (English):**
> *"Now, let's examine the most critical requirement: Zero Double-Bookings under Concurrent Load.*
>
> *In this terminal, I'm running our automated multithreaded concurrency test. This test spawns 5 parallel threads firing simultaneous HTTP booking requests for the exact same slot at the exact same microsecond.*
>
> *Notice the result: Exactly one thread successfully acquires the PostgreSQL pessimistic row lock via select_for_update and receives HTTP 201 Created. The remaining 4 competing threads are blocked and receive an explicit HTTP 409 Conflict with the error DOUBLE_BOOKING_PREVENTED.*
>
> *This provides empirical, mathematical proof that double-bookings are impossible."*

---

### ⏱️ Segment 5: Multi-Channel Reminders & Self-Service Rescheduling (3:30 – 4:15)
**Visual on Screen:**
- Switch back to the browser.
- Click the **"Reminder Audit"** tab in the top navigation.
- Show the 3 logged notifications for Jane Doe: `EMAIL`, `SMS`, `CALDAV_ICS`.
- Click **"View Payload"** on the `CALDAV_ICS` record to show the RFC 5545 iCalendar invite payload.
- Click **"My Bookings"** tab. Type `jane.doe@enterprise.com`. Show active booking and click **"Reschedule"**.

**Spoken Voiceover Script (English):**
> *"Next, in our Reminder Audit tab, we see an immutable audit trail of all dispatched notifications. Here is Jane's SendGrid email confirmation, her Twilio SMS reminder, and her standardized RFC 5545 CalDAV calendar invite. Expanding the payload shows the exact VCALENDAR structure.*
>
> *In the 'My Bookings' tab, clients enjoy self-service management. They can look up reservations by email and reschedule to future slots. Furthermore, our 24-hour advance notice policy strictly prevents clients from cancelling or moving imminent sessions, protecting billable consultant hours."*

---

### ⏱️ Segment 6: Conclusion (4:15 – 4:45)
**Visual on Screen:**
- Navigate back to the **Dashboard** showing updated revenue figures ($945+).
- Show the clean layout.

**Spoken Voiceover Script (English):**
> *"In summary, Falcon Calendar delivers a production-grade scheduling engine with provable ACID concurrency controls, dynamic timezone projections, multi-channel reminder auditing, and enterprise policy enforcement.*
>
> *All deliverables—including the PostgreSQL schema DDL, OpenAPI YAML, 15-case QA Excel sheet, scaling roadmap, and editable Lucidchart architecture and ERD diagrams—are fully documented in our submission.*
>
> *Thank you very much, and I look forward to walking through the implementation during Monday's evaluation!"*

---

## 💡 Quick Tips for Candidate Delivery
1. **Highlight the Terminal Test:** Reviewers love seeing the multithreaded test pass live on screen. Make sure your terminal font is large enough (Ctrl + Plus).
2. **Key Buzzwords to emphasize:** *Pessimistic row locking, `SELECT FOR UPDATE`, HTTP 409 Conflict `DOUBLE_BOOKING_PREVENTED`, Canonical UTC timestamps, `pytz` dynamic projection, 24-hour cancellation policy, RFC 5545 CalDAV ICS.*
3. **Keep the video under 5 minutes** to adhere to the assignment guidelines.
