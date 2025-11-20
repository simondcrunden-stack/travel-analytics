-- Add target_revenue column to preferred_airlines table
ALTER TABLE preferred_airlines
ADD COLUMN target_revenue NUMERIC(12, 2) NULL
CHECK (target_revenue >= 0);
