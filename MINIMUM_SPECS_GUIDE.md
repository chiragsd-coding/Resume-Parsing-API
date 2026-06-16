# Minimum Specifications Guide

## Quick Answer

**Can it run on 0.5 CPU + 512MB RAM?** ✅ **YES**

But you need to:
1. Use SQLite instead of PostgreSQL
2. Remove optional services (Ollama, Redis, Qdrant, Elasticsearch)
3. Use minimal Python dependencies
4. Run a single worker process
5. Accept performance trade-offs

## Specification Comparison

### Original Full Stack
```
CPU:          2-4 cores
RAM:          4-8GB
Services:     13 (API, DB, Cache, Vector, Search, LLM, Monitoring, etc.)
Image Size:   500MB+
Dependencies: 45 packages
Startup Time: 60+ seconds
Suitable For: Mid to large production
Cost:         $500+/month
```

### Lightweight Version (For 0.5 CPU + 512MB)
```
CPU:          0.5 cores (500m)
RAM:          512MB
Services:     1 (API only, with SQLite)
Image Size:   200MB
Dependencies: 15 packages
Startup Time: 5 seconds
Suitable For: MVP, prototyping, low traffic
Cost:         $10-50/month
```

## What Runs on 0.5 CPU + 512MB

### ✅ Works (Included)
- FastAPI REST API
- SQLite database (local file)
- JSON-based caching (in-memory)
- Resume text parsing (no OCR)
- Basic keyword matching
- API rate limiting
- Authentication & RBAC
- Audit logging
- Basic billing tracking
- Multi-tenancy support

### ❌ Doesn't Work (Removed)
- PostgreSQL (too heavy for SQLite)
- Redis cache (too much overhead)
- Ollama local LLM (3GB+ model)
- Qdrant vector DB (separate service)
- Elasticsearch (separate service)
- Prometheus monitoring
- Grafana dashboards
- Multi-region support
- Auto-scaling

## Files You Need

### New Files to Use
```
Dockerfile.minimal           # Lightweight image (~200MB)
requirements-minimal.txt     # Only 15 dependencies
docker-compose-minimal.yml   # Single service
kubernetes-minimal.yaml      # Minimal K8s config
.env-minimal                 # Lightweight settings
```

### Updated Configuration
```python
# app/config.py
DATABASE_TYPE = "sqlite"  # Not PostgreSQL
ENABLE_OLLAMA = False
ENABLE_REDIS = False
ENABLE_ELASTICSEARCH = False
MAX_WORKERS = 1
```

## How to Deploy

### Option A: Docker (Recommended for 0.5 CPU + 512MB)
```bash
# Build lightweight image
docker build -f Dockerfile.minimal -t ats-light:latest .

# Run with resource limits
docker run -it \
  --cpus=0.5 \
  --memory=512m \
  -p 8000:8000 \
  -e DATABASE_TYPE=sqlite \
  -e WORKERS=1 \
  ats-light:latest

# Or use docker-compose
docker-compose -f docker-compose-minimal.yml up
```

### Option B: Kubernetes
```bash
kubectl apply -f kubernetes-minimal.yaml

# Check deployment
kubectl get pods
kubectl describe pod ats-api-minimal-xxx
```

### Option C: Raw VPS (Linux)
```bash
# SSH into VPS
ssh user@vps

# Install Python 3.11
apt-get install python3.11 python3.11-venv

# Clone repo and setup
git clone <repo>
cd ats-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt

# Run
export DATABASE_TYPE=sqlite
gunicorn -w 1 app.main:app
```

## Resource Breakdown (512MB)

```
Component                   Usage
────────────────────────────────────
Linux kernel                ~50MB
Python runtime              ~100MB
FastAPI + dependencies      ~80MB
SQLite DB in memory         ~50MB
App cache + buffers         ~32MB
Overhead                    ~100MB
────────────────────────────────────
Total                       ~412MB (within 512MB limit)
```

## Performance Expectations

### With 0.5 CPU + 512MB
```
Concurrent connections:     1-2
Requests per second:        10-50 (CPU limited)
Resume parsing:             ~2-5 seconds (no OCR)
Match search:               ~500ms-2s
Database queries:           <100ms
Startup time:               5-10 seconds
```

### Traffic You Can Handle
```
Resumes per day:            50-100
Users per day:              5-10
API calls per day:          500-2,000
Peak concurrent users:      1-2
```

## Database Comparison

### SQLite (For 0.5 CPU + 512MB) ✅
```
Pros:
- Single file database
- Zero setup required
- Built-in Python support
- Small memory footprint (~20-50MB)
- Good for <10,000 records
- Works on minimal servers

Cons:
- Limited to single writer
- No network access needed
- No advanced features
- Scales only to ~100K records
```

### PostgreSQL (Requires 1+ CPU + 1GB) ❌
```
Pros:
- Multiple writers
- Advanced features
- Scales to billions
- Multi-tenant ready
- Full ACID compliance

Cons:
- Requires 500MB+ just to run
- Need separate database process
- Memory overhead for each connection
- Not suitable for 512MB limit
```

## What to do if you need more power

### Upgrade Path 1: Gradual CPU/RAM Increase
```
0.5 CPU + 512MB    → Current (SQLite)
1 CPU + 1GB        → Add Redis, basic features
2 CPU + 2GB        → Add PostgreSQL, Elasticsearch
4 CPU + 4GB+       → Full production stack
```

### Upgrade Path 2: Add Cloud Services
```
Keep 0.5 CPU + 512MB, but add:
- OpenAI API (instead of Ollama)        → $0.002-0.02 per request
- AWS S3 (instead of local storage)     → $0.023 per GB
- Serverless functions (for OCR)        → $0.20 per 1M invocations
- managed PostgreSQL (RDS)              → $15+/month minimum

Total: Still ~$50-100/month with better features
```

## Setup Instructions

### Step 1: Verify You Have the Files
```bash
ls -la | grep -E "(Dockerfile.minimal|requirements-minimal|docker-compose-minimal|kubernetes-minimal)"
```

### Step 2: Choose Deployment Method
```
Local Dev:        docker-compose -f docker-compose-minimal.yml up
Production VPS:   Use Dockerfile.minimal on VPS
Kubernetes:       kubectl apply -f kubernetes-minimal.yaml
```

### Step 3: Configure Environment
```bash
# Create .env file
cat > .env << EOF
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/ats.db
ENVIRONMENT=production
DEBUG=false
WORKERS=1
ENABLE_OLLAMA=false
ENABLE_REDIS=false
EOF
```

### Step 4: Start Service
```bash
# Docker
docker-compose -f docker-compose-minimal.yml up -d

# Or Kubernetes
kubectl apply -f kubernetes-minimal.yaml

# Or Raw Python
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Step 5: Verify Running
```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose-minimal.yml logs -f api
```

## Cloud Platform Pricing (0.5 CPU + 512MB)

### AWS Lambda (Serverless)
```
RAM:           512MB
CPU:           ~0.5 equivalent
Cost:          $0.20 per 1M requests + $0.0000166667 per GB-second
Estimated:     $5-20/month for low traffic
Best for:      Hobby, prototyping, extremely low traffic
```

### Google Cloud Run (Serverless)
```
RAM:           512MB
CPU:           0.5
Cost:          $0.0000025 per vCPU-second + $0.000003389 per GB-second
Estimated:     $10-30/month
Best for:      Small projects, pay-per-use
```

### AWS EC2 t3.nano
```
RAM:           512MB
vCPU:          0.09 (burstable)
Cost:          ~$4.75/month on-demand
Estimated:     $10-20/month with storage
Best for:      Always-on services, development
```

### Linode/DigitalOcean Nanode
```
RAM:           512MB - 1GB
vCPU:          0.5 - 1
Cost:          $5-6/month
Estimated:     $5-15/month
Best for:      Cheapest always-on option
```

### Docker Compose (Local)
```
Cost:          $0 (runs on your machine)
Perfect for:   Development, testing
```

## Important Limitations

### SQLite Limitations
```
Max connections:        1 writer, unlimited readers
Max DB size:            ~2TB theoretically, ~1GB practically
Transactions:           Limited to single connection
Concurrent writes:      Not recommended
Typical data:           1,000-50,000 records
```

### 512MB RAM Limitations
```
Max Python libraries:   ~15 (vs 45 in full)
No caching layer:       Redis disabled
No search index:        Elasticsearch disabled
No embedding cache:     Qdrant disabled
No local LLM:           Ollama disabled
Background jobs:        Celery disabled
```

## When to Use This Setup

### Use 0.5 CPU + 512MB if:
```
✅ Building MVP/prototype
✅ Just starting out
✅ <100 resumes/day
✅ <10 active users
✅ Budget is $5-50/month
✅ Single user/small team
✅ Testing business model
✅ Proof of concept
```

### Don't use if:
```
❌ >500 resumes/day
❌ >50 active users
❌ Need 99.9% uptime
❌ Need advanced features
❌ Need multi-region
❌ Need real-time updates
❌ Scaling to production
❌ Enterprise customers
```

## Upgrade Timeline

```
Month 1-3:    0.5 CPU + 512MB (MVP, test market)
Month 4-6:    1 CPU + 1GB (add PostgreSQL)
Month 7-9:    2 CPU + 2GB (add Redis, features)
Month 10+:    4+ CPU + 4GB+ (full production)
```

## Summary Table

| Metric | Light (0.5+512) | Small (1+1GB) | Medium (2+2GB) | Full (4+4GB) |
|--------|-----------------|---------------|----------------|-------------|
| CPU | 0.5 | 1 | 2 | 4+ |
| RAM | 512MB | 1GB | 2GB | 4GB+ |
| DB | SQLite | PostgreSQL | PostgreSQL | PostgreSQL |
| Cache | In-memory | Redis | Redis | Redis Cluster |
| Search | SQL | SQL | Elasticsearch | Elasticsearch |
| LLM | API only | Ollama | Ollama | Ollama |
| Resumes/day | 100 | 500 | 5K | 50K+ |
| Cost/month | $10-50 | $50-100 | $150-300 | $500+ |
| Status | MVP | Small Prod | Mid Prod | Enterprise |

---

**Bottom Line**: Yes, 0.5 CPU + 512MB RAM works perfectly for MVP/prototyping with SQLite.

When you grow, just upgrade to the "Small" or "Medium" tier.

**Next Step**: Use `Dockerfile.minimal`, `requirements-minimal.txt`, and `docker-compose-minimal.yml` to deploy!
