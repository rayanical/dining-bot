-- Migration: Add ingredients and embedding columns for semantic search
-- Run this against your PostgreSQL database

-- 1. Enable pgvector extension (requires superuser or rds_superuser on AWS)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add ingredients column (array of text)
ALTER TABLE dining_hall_menu 
ADD COLUMN IF NOT EXISTS ingredients TEXT[];

-- 3. Add embedding column (1536 dimensions for text-embedding-3-small)
ALTER TABLE dining_hall_menu 
ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- 4. Create index for fast similarity search (IVFFlat)
-- Use cosine distance for normalized embeddings
CREATE INDEX IF NOT EXISTS idx_dining_hall_menu_embedding 
ON dining_hall_menu 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 5. Create index for ingredient array searches
CREATE INDEX IF NOT EXISTS idx_dining_hall_menu_ingredients 
ON dining_hall_menu 
USING gin (ingredients);

-- Verify the changes
SELECT 
    column_name, 
    data_type, 
    udt_name
FROM information_schema.columns 
WHERE table_name = 'dining_hall_menu' 
  AND column_name IN ('ingredients', 'embedding');
