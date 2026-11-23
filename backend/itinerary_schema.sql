CREATE TABLE IF NOT EXISTS itineraries (
    itinerary_id TEXT PRIMARY KEY NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    departure_date TEXT NOT NULL,
    return_date TEXT NOT NULL,
    departure_time TEXT NOT NULL,
    interests TEXT NOT NULL,
    min_rest_minutes INTEGER NOT NULL CHECK (min_rest_minutes > 0),
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'CURRENT')),
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    created_at TEXT NOT NULL,
    confirmed_at TEXT,
    CHECK (departure_date <= return_date),
    CHECK ((status = 'DRAFT' AND confirmed_at IS NULL)
        OR (status = 'CURRENT' AND confirmed_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS itineraries_owner_status_confirmed
    ON itineraries (user_id, status, confirmed_at DESC);

CREATE TABLE IF NOT EXISTS demo_samples (
    itinerary_id TEXT PRIMARY KEY REFERENCES itineraries(itinerary_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    active INTEGER NOT NULL CHECK (active IN (0, 1))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_sample_per_user
    ON demo_samples(user_id) WHERE active = 1;

CREATE TABLE IF NOT EXISTS itinerary_days (
    day_id TEXT PRIMARY KEY NOT NULL,
    itinerary_id TEXT NOT NULL REFERENCES itineraries(itinerary_id),
    day_number INTEGER NOT NULL CHECK (day_number >= 1),
    date TEXT NOT NULL,
    end_deadline TEXT NOT NULL,
    enforce_end_deadline INTEGER NOT NULL DEFAULT 1 CHECK (enforce_end_deadline IN (0, 1)),
    UNIQUE (itinerary_id, day_number),
    UNIQUE (itinerary_id, date)
);

CREATE TABLE IF NOT EXISTS activities (
    activity_id TEXT PRIMARY KEY NOT NULL,
    day_id TEXT NOT NULL REFERENCES itinerary_days(day_id),
    type TEXT NOT NULL CHECK (type IN ('TRAVEL', 'REST', 'VISIT')),
    name TEXT NOT NULL,
    place_id TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'DONE', 'DROPPED', 'REPLACED')),
    is_optional INTEGER NOT NULL CHECK (is_optional IN (0, 1)),
    replaces_activity_id TEXT REFERENCES activities(activity_id),
    completed_at TEXT,
    CHECK (type <> 'VISIT' OR place_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS activities_day_start
    ON activities (day_id, start_time);
