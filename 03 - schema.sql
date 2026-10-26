-- ==============================================================================
-- FalconXoft | Weekend 2 Engineering Evaluation
-- Project 2: Appointment & Scheduling SaaS
-- Deliverable 03 - schema.sql (PostgreSQL 18.3 DDL Specification)
-- Tablespace: scheduling_space (Drive D:\pg_tablespace)
-- ==============================================================================

-- Enable UUID extension for cryptographic primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS scheduling_reminderlog CASCADE;
DROP TABLE IF EXISTS scheduling_appointment CASCADE;
DROP TABLE IF EXISTS scheduling_scheduleoverride CASCADE;
DROP TABLE IF EXISTS scheduling_workinghour CASCADE;
DROP TABLE IF EXISTS scheduling_service CASCADE;
DROP TABLE IF EXISTS scheduling_providerprofile CASCADE;

-- ------------------------------------------------------------------------------
-- 1. PROVIDER PROFILES
-- ------------------------------------------------------------------------------
CREATE TABLE scheduling_providerprofile (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    bio TEXT NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL DEFAULT '',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    avatar_url VARCHAR(200) NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_provider_slug ON scheduling_providerprofile(slug);
CREATE INDEX idx_provider_active ON scheduling_providerprofile(is_active);

-- ------------------------------------------------------------------------------
-- 2. SERVICES CATALOG
-- ------------------------------------------------------------------------------
CREATE TABLE scheduling_service (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES scheduling_providerprofile(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    buffer_minutes INTEGER NOT NULL DEFAULT 15 CHECK (buffer_minutes >= 0),
    price NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (price >= 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    cancellation_notice_hours INTEGER NOT NULL DEFAULT 24 CHECK (cancellation_notice_hours >= 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_provider_service_slug UNIQUE (provider_id, slug)
);

CREATE INDEX idx_service_provider ON scheduling_service(provider_id);
CREATE INDEX idx_service_active ON scheduling_service(is_active);

-- ------------------------------------------------------------------------------
-- 3. WORKING HOURS SPECIFICATION (0=Monday ... 6=Sunday)
-- ------------------------------------------------------------------------------
CREATE TABLE scheduling_workinghour (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES scheduling_providerprofile(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL DEFAULT '09:00:00',
    end_time TIME NOT NULL DEFAULT '17:00:00',
    break_start_time TIME NULL,
    break_end_time TIME NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_provider_day_of_week UNIQUE (provider_id, day_of_week),
    CONSTRAINT chk_workinghour_time_order CHECK (end_time > start_time),
    CONSTRAINT chk_break_order CHECK (break_start_time IS NULL OR break_end_time IS NULL OR break_end_time > break_start_time)
);

CREATE INDEX idx_workinghour_provider_day ON scheduling_workinghour(provider_id, day_of_week);

-- ------------------------------------------------------------------------------
-- 4. SCHEDULE OVERRIDES (Holidays, Sick Days, Custom Hours)
-- ------------------------------------------------------------------------------
CREATE TABLE scheduling_scheduleoverride (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES scheduling_providerprofile(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    is_unavailable BOOLEAN NOT NULL DEFAULT TRUE,
    custom_start_time TIME NULL,
    custom_end_time TIME NULL,
    reason VARCHAR(200) NOT NULL DEFAULT 'Holiday / Personal Time Off',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_provider_override_date UNIQUE (provider_id, date)
);

CREATE INDEX idx_override_provider_date ON scheduling_scheduleoverride(provider_id, date);

-- ------------------------------------------------------------------------------
-- 5. APPOINTMENTS (With Pessimistic Row-Locking & Concurrency Defense)
-- ------------------------------------------------------------------------------
CREATE TABLE scheduling_appointment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider_id UUID NOT NULL REFERENCES scheduling_providerprofile(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES scheduling_service(id) ON DELETE CASCADE,
    customer_name VARCHAR(150) NOT NULL,
    customer_email VARCHAR(254) NOT NULL,
    customer_phone VARCHAR(30) NOT NULL DEFAULT '',
    customer_notes TEXT NOT NULL DEFAULT '',
    customer_timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED' CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'RESCHEDULED')),
    cancellation_reason TEXT NOT NULL DEFAULT '',
    rescheduled_from_id UUID NULL REFERENCES scheduling_appointment(id) ON DELETE SET NULL,
    rescheduled_at TIMESTAMPTZ NULL,
    meeting_link VARCHAR(255) NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_appointment_time_order CHECK (end_time > start_time)
);

-- Performance & Overlap Query Indexes
CREATE INDEX idx_appointment_provider_window ON scheduling_appointment(provider_id, start_time, end_time, status);
CREATE INDEX idx_appointment_customer_email ON scheduling_appointment(customer_email, status);
CREATE INDEX idx_appointment_start_time ON scheduling_appointment(start_time);

-- Optional PostgreSQL Native GiST Exclusion Constraint to physically guarantee no overlapping active appointments:
-- ALTER TABLE scheduling_appointment ADD CONSTRAINT no_overlapping_appointments
-- EXCLUDE USING gist (
--     provider_id WITH =,
--     tstzrange(start_time, end_time) WITH &&
-- ) WHERE (status IN ('CONFIRMED', 'PENDING'));

-- ------------------------------------------------------------------------------
-- 6. REMINDER AUDIT LOGS (Multi-channel Notification Dispatch Stream)
-- ------------------------------------------------------------------------------
CREATE TABLE scheduling_reminderlog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID NOT NULL REFERENCES scheduling_appointment(id) ON DELETE CASCADE,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('EMAIL', 'SMS', 'CALENDAR_INVITE')),
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DISPATCHED' CHECK (status IN ('QUEUED', 'DISPATCHED', 'FAILED')),
    recipient VARCHAR(150) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    payload_preview JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reminder_appointment ON scheduling_reminderlog(appointment_id);
CREATE INDEX idx_reminder_status ON scheduling_reminderlog(status);
CREATE INDEX idx_reminder_scheduled ON scheduling_reminderlog(scheduled_for);
