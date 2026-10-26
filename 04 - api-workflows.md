# Falcon Calendar — API Workflows & Sequence Flows
**Deliverable 04 | FalconXoft 15-Day Intern Performance Evaluation | Project 2**

---

## 1. Lucidchart Workspace Reference
> **Lucidchart Editable API Flows URL:**  
> [https://lucid.app/lucidchart/e9fd80d5-1509-4b3b-8e8d-6f349d603ca2/edit?viewport_loc=74%2C-84%2C3316%2C1609%2C0_0&invitationId=inv_b4b4df8d-4a77-4a75-81b6-1d81dca18a9f](https://lucid.app/lucidchart/e9fd80d5-1509-4b3b-8e8d-6f349d603ca2/edit?viewport_loc=74%2C-84%2C3316%2C1609%2C0_0&invitationId=inv_b4b4df8d-4a77-4a75-81b6-1d81dca18a9f)  
> *Note: Complete sequence flows covering success paths, conflict handling, and failure states.*  
> **Exported Deliverable Files:** [`04 - api-workflows.png`](./04%20-%20api-workflows.png) | [`04 - api-workflows.pdf`](./04%20-%20api-workflows.pdf) | [`04 - openapi.yaml`](./04%20-%20openapi.yaml)

---

## 2. API Specifications & Interactive Documentation
- **OpenAPI 3.0 YAML Specification:** Located at [04 - openapi.yaml](file:///d:/week_2/02_Scheduling_SaaS/04%20-%20openapi.yaml)
- **Live Swagger UI:** `http://127.0.0.1:8001/api/docs/`
- **Live Redoc View:** `http://127.0.0.1:8001/api/redoc/`

---

## 3. Sequence Flow: Dynamic Slot Generation & Timezone Projection

```mermaid
sequenceDiagram
    autonumber
    actor User as Client Browser
    participant API as Slot Engine (/api/providers/{id}/slots/)
    participant DB as PostgreSQL 18
    
    User->>API: GET ?service_id=...&date=2026-10-26&client_tz=America/Los_Angeles
    API->>DB: Query ProviderProfile, Service & WorkingHours for Monday
    DB-->>API: Provider in America/New_York (09:00 - 17:00 EDT), Lunch (13:00 - 14:00 EDT)
    API->>DB: Query ScheduleOverride for 2026-10-26
    DB-->>API: No override found (active working day)
    
    Note over API: Generate candidate intervals: [09:00, 09:30], [09:45, 10:15]...
    Note over API: Filter out candidates overlapping break [13:00 - 14:00 EDT]
    
    API->>DB: Query Appointments where provider=P1 AND start < day_end AND end > day_start
    DB-->>API: 1 Confirmed Appointment at [14:00 - 14:30 EDT]
    
    Note over API: Eliminate candidates overlapping [14:00 - 14:45] (including 15m buffer)
    Note over API: Project remaining slots into client timezone (America/Los_Angeles):<br/>09:00 EDT -> 06:00 PDT
    
    API-->>User: HTTP 200 OK (Array of slots with localized display labels)
```

---

## 4. Sequence Flow: Atomic Booking & Double-Booking Prevention

```mermaid
sequenceDiagram
    autonumber
    actor Client as Booking Client
    participant API as DRF AppointmentBookingView
    participant DB as PostgreSQL 18 (InnoDB/Postgres Engine)
    participant Reminders as Mock Reminder Dispatcher

    Client->>API: POST /api/appointments/book/ {provider_id, service_id, start_time: "2026-10-26T13:00:00Z", ...}
    
    API->>DB: BEGIN TRANSACTION
    API->>DB: SELECT * FROM ProviderProfile WHERE id=provider_id FOR UPDATE
    Note over DB: Exclusive row lock acquired on provider row
    
    API->>DB: SELECT * FROM Appointment WHERE provider=provider_id AND status IN ('CONFIRMED','PENDING') AND start < candidate_end+buffer AND end > candidate_start-buffer
    
    alt Overlapping Booking or Buffer Violation Exists
        DB-->>API: Found conflicting appointment ID: "apt-9a82df1b"
        API->>DB: ROLLBACK
        API-->>Client: HTTP 409 Conflict {"error": "DOUBLE_BOOKING_PREVENTED", "message": "Slot conflicts with existing booking"}
    else Slot is Clean & Available
        DB-->>API: 0 Overlapping rows found
        API->>DB: INSERT INTO Appointment (status='CONFIRMED', meeting_link='https://meet.falconxoft.com/call/apt-xxx', ...)
        API->>Reminders: dispatch_booking_notifications(appointment)
        Reminders->>DB: INSERT INTO ReminderLog (Email, SMS, ICS Invites)
        API->>DB: COMMIT TRANSACTION
        Note over DB: Row lock released on provider
        API-->>Client: HTTP 201 Created (Appointment Record, Confirmed Status, Meeting Room Link)
    end
```

---

## 5. Sequence Flow: Rescheduling with Advance Notice Policy Check

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client Browser
    participant API as DRF AppointmentRescheduleView
    participant DB as PostgreSQL 18

    Client->>API: POST /api/appointments/{id}/reschedule/ {new_start_time: "2026-10-28T15:00:00Z"}
    API->>DB: BEGIN TRANSACTION
    API->>DB: SELECT * FROM Appointment WHERE id=id FOR UPDATE
    
    Note over API: Evaluate Notice Policy: now + timedelta(hours=service.cancellation_notice_hours)
    
    alt Notice Window Breached (e.g. < 24 Hours Before Appointment)
        API->>DB: ROLLBACK
        API-->>Client: HTTP 400 Bad Request {"error": "NOTICE_POLICY_VIOLATION", "message": "Rescheduling requires at least 24 hours notice"}
    else Valid Notice Provided
        API->>DB: SELECT * FROM ProviderProfile WHERE id=provider_id FOR UPDATE
        API->>DB: Check overlap on new proposed slot
        alt New Slot Already Booked
            API->>DB: ROLLBACK
            API-->>Client: HTTP 409 Conflict {"error": "DOUBLE_BOOKING_PREVENTED"}
        else New Slot Free
            API->>DB: UPDATE Appointment SET start_time=new_start, version=version+1, rescheduled_at=now()
            API->>DB: INSERT INTO ReminderLog (Reschedule Notification)
            API->>DB: COMMIT TRANSACTION
            API-->>Client: HTTP 200 OK (Updated Appointment Data)
        end
    end
```

---

## 6. Comprehensive Endpoint Reference

| Method | Endpoint | Query / Body Payload | Response Codes | Description |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/providers/` | None | `200 OK` | Retrieves all active consultants with embedded services and working hours |
| **GET** | `/api/providers/{id}/` | None | `200 OK`, `404 Not Found` | Retrieves individual consultant detail |
| **GET** | `/api/providers/{id}/slots/` | `service_id`, `date`, `client_tz` | `200 OK`, `400 Bad Request` | Generates available slots projected into client timezone |
| **POST** | `/api/appointments/book/` | `provider_id`, `service_id`, `start_time`, `customer_name`, `customer_email`, `customer_phone`, `customer_notes` | `201 Created`, `400 Bad Request`, `409 Conflict` | Atomically secures slot with pessimistic locking |
| **POST** | `/api/appointments/{id}/reschedule/` | `new_start_time`, `customer_timezone` | `200 OK`, `400 Bad Request`, `409 Conflict` | Reschedules session subject to notice policy |
| **POST** | `/api/appointments/{id}/cancel/` | `reason` | `200 OK`, `400 Bad Request` | Cancels session and dispatches cancellation alerts |
| **GET** | `/api/appointments/` | `email`, `provider_id`, `status` | `200 OK` | Filtered appointment query for portal and administration |
| **GET** | `/api/reminders/` | `appointment_id`, `channel` | `200 OK` | Audit trail of dispatched multi-channel reminders |
| **GET** | `/api/dashboard/metrics/` | None | `200 OK` | Real-time business intelligence: gross revenue, confirmed, upcoming, completed |
