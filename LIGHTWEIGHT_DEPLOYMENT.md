# Lightweight Deployment - 0.5 CPU + 512MB RAM

## Current vs Optimized Specs

### Current Architecture (What We Built)
```
CPU: 2+ cores
RAM: 4GB+
Services: 13 (api, postgres, redis, qdrant, elasticsearch, ollama, etc.)
Suitable for: Mid-scale production
Monthly Cost: $5K+
```

### Lightweight Architecture (0.5 CPU + 512MB)
```
CPU: 0.5 cores (500m)
RAM: 512MB
Services: 3-5 (api, lightweight db, optional cache)
Suitable for: MVP, prototyping, small scale
Monthly Cost: $30-50 (serverless) or free (local)
```

## Minimum Requirements to Run

### Absolute Minimum
```
CPU: 0.5 cores
RAM: 512MB
Storage: 10GB
Database: SQLite (instead of PostgreSQL)
Cache: In-memory only (no Redis)
LLM: Ollama removed (use OpenAI API instead)
Search: Elasticsearch removed (PostgreSQL full-text only)
```

**Cost**: ~$10-20/month on serverless

### Still Production-Ready
```
CPU: 1 core
RAM: 1GB
Storage: 20GB
Database: PostgreSQL (lightweight config)
Cache: Redis (lightweight config)
LLM: Ollama (minimal model)
Search: Elasticsearch removed
```

**Cost**: ~$30-50/month on cloud

### Recommended Minimum (Balanced)
```
CPU: 1-2 cores
RAM: 2GB
Storage: 50GB
Database: PostgreSQL (optimized)
Cache: Redis
LLM: Ollama or API
Search: Elasticsearch (optional)
```

**Cost**: ~$100-150/month

## Step 1: Minimal Python Runtime

### Dockerfile for 512MB
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-minimal.txt .

# Install only essential Python packages
RUN pip install --no-cache-dir \
    --no-compile \
    -r requirements-minimal.txt

COPY app/ ./app/

EXPOSE 8000

# Use gunicorn with minimal workers
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--max-requests", "100", "--timeout", "30", "app.main:app"]
```

**Image size**: ~200MB (vs 500MB+ for full)

## Step 2: Minimal Dependencies

### requirements-minimal.txt
```
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# No Redis, Qdrant, Elasticsearch initially

# Authentication
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
pydantic-settings==2.1.0

# Core utilities
python-dotenv==1.0.0
requests==2.31.0

# Optional: Lightweight parsing (no OCR)
regex==2023.12.25
```

**Reduces dependencies from 45 to 15 packages**
**Cuts image from 500MB to 200MB**

## Step 3: Database Configuration

### For 512MB RAM - SQLite
```python
# app/config.py - Add this option

class Settings(BaseSettings):
    DATABASE_TYPE: str = "sqlite"  # or "postgresql"
    
    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_TYPE == "sqlite":
            return "sqlite:///./ats.db"  # File-based DB
        return "postgresql://user:pass@localhost/ats_db"

settings = Settings()
```

### SQLite Connection (Minimal)
```python
# app/database.py - SQLite optimized

from sqlalchemy import create_engine, event
import sqlite3

if settings.DATABASE_TYPE == "sqlite":
    engine = create_engine(
        "sqlite:///./ats.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Single connection
        echo=False,
    )
    
    # WAL mode for better concurrency
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=1000")
        cursor.close()
```

## Step 4: Lightweight Docker Compose

### docker-compose-minimal.yml
```yaml
version: '3.9'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.minimal
    container_name: ats_api_light
    ports:
      - "8000:8000"
    environment:
      - DATABASE_TYPE=sqlite
      - ENVIRONMENT=production
      - DEBUG=false
      - WORKERS=1
    volumes:
      - ./data:/app/data  # SQLite DB file
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

# No PostgreSQL, Redis, Qdrant, Elasticsearch
```

**Start**: `docker-compose -f docker-compose-minimal.yml up`

## Step 5: Lightweight Kubernetes

### k8s-minimal.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ats-api-light
spec:
  replicas: 1  # Single replica
  selector:
    matchLabels:
      app: ats-api-light
  template:
    metadata:
      labels:
        app: ats-api-light
    spec:
      containers:
      - name: ats-api
        image: ats-platform/api:lightweight
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_TYPE
          value: "sqlite"
        - name: WORKERS
          value: "1"
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        emptyDir: {}  # or PVC for persistence

---
apiVersion: v1
kind: Service
metadata:
  name: ats-api-light-service
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: ats-api-light
```

**Deploy**: `kubectl apply -f k8s-minimal.yaml`

## Step 6: Optimized Code Changes

### Remove Heavy Services
```python
# app/main.py - Minimal version

from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # No LLM initialization
    # No Redis connection
    # No Qdrant connection
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

# Only essential endpoints
```

### Simplified Parsing (No OCR)
```python
# app/services/parser.py - Lightweight

class ResumeParser:
    @staticmethod
    async def parse_resume(file_path: str) -> dict:
        """Simplified parsing - no OCR, just text extraction"""
        try:
            if file_path.endswith('.txt'):
                with open(file_path, 'r') as f:
                    text = f.read()
            elif file_path.endswith('.pdf'):
                # Use pdfplumber instead of pytesseract + tesseract
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ''.join(page.extract_text() for page in pdf.pages)
            else:
                text = ""
            
            return {
                "raw_text": text,
                "full_name": extract_name(text),
                "email": extract_email(text),
                "skills": extract_skills(text),
                # Skip OCR, embedding, etc.
            }
        except Exception as e:
            raise ValueError(f"Parse error: {e}")
```

### Remove LLM Features
```python
# app/services/llm.py - Disabled

class OllamaService:
    async def generate(self, prompt: str) -> str:
        """Disabled - use API instead"""
        raise NotImplementedError("Use OpenAI API instead")

# Or fallback to OpenAI
import openai

async def generate_questions(job_title: str, skills: list) -> list:
    """Use OpenAI API instead of local Ollama"""
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"Generate interview questions for {job_title}"}
        ]
    )
    return response.choices[0].message.content
```

## Step 7: Minimal Features

### API Endpoints (Reduced Set)
```
/health                           # Health check
/resumes/parse (text only)       # No OCR
/job-descriptions               # Basic create
/matches/search (simple scoring) # No embeddings
/billing/usage                   # Usage tracking
```

### Removed Features
```
❌ OCR support (parse text only)
❌ Vector similarity search (use keyword matching)
❌ Ollama LLM (use OpenAI API)
❌ Interview generation (basic templates)
❌ Elasticsearch (use SQL only)
❌ Redis caching (in-memory only)
❌ Multi-region (single instance)
❌ Auto-scaling (manual scale)
```

### Kept Features
```
✅ Resume parsing (text)
✅ Job description parsing
✅ Basic candidate matching
✅ Multi-tenancy
✅ Authentication
✅ API rate limiting
✅ Audit logging
✅ Billing integration
```

## Step 8: Environment Variables (Minimal)

### .env-minimal
```env
# Minimal setup
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./ats.db
ENVIRONMENT=production
DEBUG=false

# Optional - for LLM
OPENAI_API_KEY=sk_test_xxxxx
OPENAI_MODEL=gpt-3.5-turbo

# Stripe
STRIPE_SECRET_KEY=sk_test_xxxxx

# Disable heavy services
ENABLE_OLLAMA=false
ENABLE_REDIS=false
ENABLE_ELASTICSEARCH=false
```

## Step 9: Resource Limits

### Memory Breakdown (512MB)
```
Python runtime:     150MB
FastAPI + deps:      100MB
SQLite DB (cached):   100MB
Buffer/heap:          60MB
─────────────────────────
Total:               512MB
```

### CPU Breakdown (0.5 core)
```
Request handling:    40%
Database queries:    30%
Parsing:            20%
Overhead:           10%
─────────────────────
Total:              100%
```

## Step 10: Performance Tuning

### ASGI Server Tuning
```python
# Run with minimal workers
gunicorn -w 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --max-requests 100 \
  --timeout 30 \
  --access-logfile - \
  app.main:app
```

### SQLite Optimization
```sql
-- In database initialization
PRAGMA journal_mode=WAL;        -- Better concurrency
PRAGMA synchronous=NORMAL;      -- Balance safety/speed
PRAGMA cache_size=1000;         -- Use more cache
PRAGMA temp_store=MEMORY;       -- Temp in memory
PRAGMA foreign_keys=ON;         -- Enable constraints
```

## Complete Minimal Requirements

### Minimum Specs
```
CPU:              0.5 cores (500m)
RAM:              512MB
Storage:          10GB (SQLite DB grows slowly)
Network:          10Mbps (local only)
Connections:      Single connection to DB
Concurrency:      1-2 concurrent requests
Uptime:           95% (no HA)
```

### What This Can Handle
```
Users:            5-10 concurrent
Resumes/day:      50-100
API requests:     100-500/sec (with caching)
Data storage:     1,000 resumes (~50MB SQLite DB)
Deployments:      Local dev, small staging
```

## Deployment Options

### Option 1: Local Machine (Free)
```bash
docker-compose -f docker-compose-minimal.yml up
# Uses your local CPU/RAM
```

### Option 2: Serverless (Cheapest)
```
AWS Lambda (or equivalent)
- Memory: 512MB
- vCPU: ~0.5
- Cost: $0.20 per million requests
- Perfect for: MVP, low traffic
```

### Option 3: Small VPS ($30/month)
```
Linode/DigitalOcean Nanode
- 0.5 vCPU
- 512MB RAM (or 1GB)
- 10GB SSD
- Cost: $5-10/month
```

### Option 4: Kubernetes + Shared Cluster
```
- Namespace: ats-light
- Replicas: 1
- Resource requests: 250m CPU, 256Mi RAM
- Cost: $0 if already paying for cluster
```

## Migration Path

### Phase 1: Lightweight (Current)
```
0.5 CPU + 512MB RAM
SQLite
No LLM/Redis/Elasticsearch
100 resumes/day
$10-50/month
```

### Phase 2: Small Production
```
1 CPU + 1GB RAM
PostgreSQL (lightweight)
Redis optional
500 resumes/day
$50-100/month
```

### Phase 3: Mid Scale
```
2 CPU + 2GB RAM
PostgreSQL + Redis
Elasticsearch optional
5K resumes/day
$150-300/month
```

### Phase 4: Full Production (Original)
```
4+ CPU + 4GB+ RAM
PostgreSQL + Redis + Qdrant + Elasticsearch
Ollama LLM
10K+ resumes/day
$500+/month
```

## Cost Comparison

| Setup | CPU | RAM | Monthly Cost | Resumes/day |
|-------|-----|-----|--------------|------------|
| Lightweight | 0.5 | 512MB | $10-50 | 100 |
| Small Prod | 1 | 1GB | $50-100 | 500 |
| Medium Prod | 2 | 2GB | $150-300 | 5K |
| Full Prod | 4+ | 4GB+ | $500+ | 50K+ |

## Getting Started (Minimal)

### 1. Build Lightweight Image
```bash
docker build -f Dockerfile.minimal -t ats-light:latest .
```

### 2. Run Locally
```bash
docker-compose -f docker-compose-minimal.yml up
```

### 3. Test API
```bash
curl http://localhost:8000/health
open http://localhost:8000/docs
```

### 4. Deploy to VPS
```bash
# Upload files
scp Dockerfile.minimal user@vps:/app/
scp docker-compose-minimal.yml user@vps:/app/

# Run on VPS
ssh user@vps
cd /app
docker-compose -f docker-compose-minimal.yml up -d
```

---

**Bottom Line**: Yes, it can run on 0.5 CPU + 512MB RAM using SQLite + lightweight config.
**Trade-offs**: No OCR, no local LLM, no advanced search, slower matching.
**Use case**: MVP, prototyping, early-stage startup with small user base.

Choose the specs that match your needs and budget!
