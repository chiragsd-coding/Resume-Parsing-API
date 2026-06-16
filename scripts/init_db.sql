-- Initialize PostgreSQL database with required extensions

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Text similarity
CREATE EXTENSION IF NOT EXISTS "vector";   -- pgvector for embeddings

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;

-- Set session defaults
ALTER DATABASE ats_db SET timezone = 'UTC';

-- Create custom types
DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('pending', 'processing', 'completed', 'failed');
    CREATE TYPE subscription_tier AS ENUM ('free', 'pro', 'enterprise');
    CREATE TYPE audit_action AS ENUM ('create', 'update', 'delete', 'view', 'export');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = 'off';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_lock_waits = 'on';

-- Replication settings (if needed)
-- ALTER SYSTEM SET wal_level = 'replica';
-- ALTER SYSTEM SET max_wal_senders = 10;
-- ALTER SYSTEM SET wal_keep_segments = 64;
