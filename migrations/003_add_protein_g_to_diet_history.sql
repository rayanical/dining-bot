-- Add protein_g column to diet_history if it does not exist
ALTER TABLE diet_history
    ADD COLUMN IF NOT EXISTS protein_g DOUBLE PRECISION;

-- Backfill existing rows with 0 where NULL
UPDATE diet_history SET protein_g = 0 WHERE protein_g IS NULL;
