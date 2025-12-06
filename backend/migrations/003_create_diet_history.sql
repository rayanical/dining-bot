-- Create diet_history table if it does not exist
CREATE TABLE IF NOT EXISTS diet_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    date DATE NOT NULL,
    item VARCHAR NOT NULL,
    mealtime VARCHAR NOT NULL,
    calories DOUBLE PRECISION NOT NULL,
    protein_g DOUBLE PRECISION,
    allergens TEXT[] NOT NULL DEFAULT '{}',
    diet_types TEXT[] NOT NULL DEFAULT '{}'
);

-- Ensure protein_g column exists even if table was created earlier without it
ALTER TABLE diet_history
    ADD COLUMN IF NOT EXISTS protein_g DOUBLE PRECISION;

-- Backfill NULL protein_g to 0 for consistency
UPDATE diet_history SET protein_g = 0 WHERE protein_g IS NULL;

-- Optional: index for user/date lookups
CREATE INDEX IF NOT EXISTS idx_diet_history_user_date ON diet_history (user_id, date);
