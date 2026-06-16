# Database Schema & ERD

## Overview
PostgreSQL multi-tenant schema supporting millions of resumes with proper indexing and partitioning strategy.

## Core Tables

### 1. Tenants (Multi-Tenant Isolation)
```sql
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    subscription_tier ENUM('free', 'pro', 'enterprise'),
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    monthly_resume_limit INTEGER DEFAULT 50,
    resumes_used_this_month INTEGER DEFAULT 0,
    reset_date TIMESTAMP,
    features JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_tenant_slug (slug),
    INDEX idx_tenant_active (is_active)
);
```

### 2. Users (Identity & RBAC)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'recruiter',
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, email),
    INDEX idx_user_email (email),
    INDEX idx_user_tenant (tenant_id)
);
```

### 3. API Keys (Authentication)
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    name VARCHAR(255),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    scopes JSONB DEFAULT '["read", "write"]',
    rate_limit_calls INTEGER DEFAULT 100,
    rate_limit_period INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    INDEX idx_apikey_hash (key_hash),
    INDEX idx_apikey_tenant (tenant_id)
);
```

### 4. Resumes (Core Entity - Partitioned)
```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    candidate_id UUID REFERENCES candidates(id),
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_hash VARCHAR(255) UNIQUE,
    raw_text TEXT,
    parsed_data JSONB,
    embedding BYTEA,  -- Vector embedding for similarity search
    full_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    location VARCHAR(255),
    summary TEXT,
    skills JSONB DEFAULT '[]',
    experience JSONB DEFAULT '[]',
    education JSONB DEFAULT '[]',
    certifications JSONB DEFAULT '[]',
    status ENUM('pending', 'processing', 'completed', 'failed'),
    parsing_job_id VARCHAR(255),
    error_message TEXT,
    is_duplicate BOOLEAN DEFAULT false,
    duplicate_of_id UUID,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_resume_tenant_status (tenant_id, status),
    INDEX idx_resume_candidate (candidate_id),
    INDEX idx_resume_email (email),
    INDEX idx_resume_created (created_at)
) PARTITION BY RANGE (created_at);

-- Monthly partitions for 2024-2026
CREATE TABLE resumes_2024_01 PARTITION OF resumes
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
-- ... more partitions
```

### 5. Candidates (Aggregated Profile)
```sql
CREATE TABLE candidates (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    location VARCHAR(255),
    skills JSONB DEFAULT '[]',
    total_experience_years FLOAT,
    highest_education_level VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    rating FLOAT,
    notes TEXT,
    is_duplicate BOOLEAN DEFAULT false,
    merged_with_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_candidate_tenant_email (tenant_id, email),
    INDEX idx_candidate_status (status)
);
```

### 6. Job Descriptions
```sql
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    job_description TEXT,
    parsed_data JSONB,
    embedding BYTEA,  -- Vector embedding
    required_skills JSONB DEFAULT '[]',
    nice_to_have_skills JSONB DEFAULT '[]',
    experience_level VARCHAR(100),
    years_experience_required FLOAT,
    location VARCHAR(255),
    salary_min FLOAT,
    salary_max FLOAT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_jd_tenant_active (tenant_id, is_active),
    INDEX idx_jd_created (created_at)
);
```

### 7. Candidate Matches (Denormalized for Speed)
```sql
CREATE TABLE candidate_matches (
    id UUID PRIMARY KEY,
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    job_description_id UUID NOT NULL REFERENCES job_descriptions(id),
    overall_score FLOAT,  -- 0-100
    skill_match_score FLOAT,
    experience_match_score FLOAT,
    education_match_score FLOAT,
    matching_skills JSONB DEFAULT '[]',
    missing_skills JSONB DEFAULT '[]',
    skill_gap_analysis JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_match_overall_score (overall_score),
    INDEX idx_match_job_score (job_description_id, overall_score),
    INDEX idx_match_candidate (candidate_id),
    INDEX idx_match_created (created_at)
);
```

### 8. Interview Sessions
```sql
CREATE TABLE interview_sessions (
    id UUID PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id),
    job_description_id UUID REFERENCES job_descriptions(id),
    num_questions INTEGER DEFAULT 5,
    focus_areas JSONB,
    questions JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    INDEX idx_session_candidate (candidate_id)
);
```

### 9. Audit Logs (Compliance)
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    action ENUM('create', 'update', 'delete', 'view', 'export'),
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    changes JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_audit_tenant_date (tenant_id, created_at),
    INDEX idx_audit_resource (resource_type, resource_id)
);
```

### 10. Billing Events
```sql
CREATE TABLE billing_events (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    event_type VARCHAR(50),  -- resume_processed, api_call
    quantity FLOAT,
    cost FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_billing_tenant (tenant_id),
    INDEX idx_billing_created (created_at)
);
```

## Scaling Strategy

### Sharding
- Shard key: `tenant_id`
- Hash-based sharding across 16-64 shards
- Each shard: independent PostgreSQL instance

### Partitioning
- Time-based: Monthly partitions for large tables
- Range: created_at (resumes, matches, audit logs)
- Benefits: Efficient pruning, faster queries, parallel scan

### Indexing
- B-tree: tenant_id, status, created_at
- Hash: email (unique lookup)
- BRIN: created_at (time-series data)
- Partial: is_active = true (common filter)

### Vector Search Integration
- Embedding: BYTEA column stores 384-dim vectors
- Qdrant: Separate vector DB for semantic search
- Sync: Async job syncs embeddings to Qdrant

## Capacity Estimates

### 1 Tenant = 10,000 Resumes
- resumes: 10,000 rows (~5MB uncompressed, ~500KB compressed)
- candidates: 5,000 rows
- matches: 50,000 rows (if 10 JDs each)
- Total: ~100MB per tenant

### 1 Million Resumes (100 Tenants)
- Total storage: ~10GB
- Sharded across 16 instances: ~625MB each
- Partitioned by month: ~830MB per month

## Connection Pooling
```python
# Per instance: 20-50 connections
# 16 shards × 30 connections = 480 connections
# Load balancer distributes across pool
```

## Backup Strategy
- WAL archiving: S3/GCS
- Point-in-time recovery: 30 days
- Snapshots: Daily
- Replication: 2x standby replicas

## Monitoring Queries
```sql
-- Check query performance
EXPLAIN ANALYZE
SELECT * FROM candidate_matches
WHERE job_description_id = 'job-123'
ORDER BY overall_score DESC LIMIT 20;

-- Monitor table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables WHERE tablename LIKE 'resume%'
ORDER BY pg_total_relation_size DESC;

-- Replication lag
SELECT * FROM pg_stat_replication;
```
