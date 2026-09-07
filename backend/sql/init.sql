-- IP-SAKTI Sahayak — PostgreSQL Initialization
-- This script runs once when the Docker container first starts.
-- It enables required extensions.

-- Enable pgvector for embedding storage
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable trigram matching for fuzzy keyword search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Enable unaccent for language-agnostic text search
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Create FTS configuration that works with unaccent
-- (Used in the full-text search index on chunks)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_ts_config WHERE cfgname = 'ipsakti_english'
  ) THEN
    CREATE TEXT SEARCH CONFIGURATION ipsakti_english (COPY = english);
    ALTER TEXT SEARCH CONFIGURATION ipsakti_english
      ALTER MAPPING FOR hword, hword_part, word
      WITH unaccent, english_stem;
  END IF;
END;
$$;
