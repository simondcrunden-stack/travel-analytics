-- Add target_revenue column to preferred_airlines table
ALTER TABLE preferred_airlines
ADD COLUMN IF NOT EXISTS target_revenue NUMERIC(12, 2) NULL
CHECK (target_revenue >= 0);

-- Record migration 0019 as applied
INSERT INTO django_migrations (app, name, applied)
VALUES ('bookings', '0019_add_target_revenue', NOW())
ON CONFLICT DO NOTHING;
