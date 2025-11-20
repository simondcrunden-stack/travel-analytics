-- Add target_revenue column to preferred_airlines table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'preferred_airlines'
        AND column_name = 'target_revenue'
    ) THEN
        ALTER TABLE preferred_airlines
        ADD COLUMN target_revenue NUMERIC(12, 2) NULL;

        ALTER TABLE preferred_airlines
        ADD CONSTRAINT preferred_airlines_target_revenue_check
        CHECK (target_revenue >= 0);

        RAISE NOTICE 'Added target_revenue column to preferred_airlines table';
    ELSE
        RAISE NOTICE 'target_revenue column already exists';
    END IF;
END $$;
