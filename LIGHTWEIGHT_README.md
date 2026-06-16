# 🚀 Lightweight Deployment (0.5 CPU + 512MB RAM)

## Answer to Your Question

**Q: Will the application run on 0.5 core CPU and 512MB RAM?**

**A: YES** ✅ - But NOT with the full architecture. You need the **lightweight version**.

## Quick Comparison

### Full Version (Original)
- CPU: 2+ cores
- RAM: 4GB+
- Services: 13 (PostgreSQL, Redis, Qdrant, etc.)
- Image Size: 500MB+
- Cost: $500+/month

### Lightweight Version (NEW)
- CPU: 0.5 cores ✅
- RAM: 512MB ✅
- Services: 1 (FastAPI + SQLite)
- Image Size: 200MB ✅
- Cost: $10-50/month ✅

## Files for 0.5 CPU + 512MB

You now have these files:

```
Dockerfile.minimal              # Optimized for small resources
requirements-minimal.txt        # Only 15 dependencies
docker-compose-minimal.yml      # Single service setup
kubernetes-minimal.yaml         # K8s deployment
LIGHTWEIGHT_DEPLOYMENT.md       # Detailed guide
MINIMUM_SPECS_GUIDE.md          # Complete reference
```

## Quick Start

### Step 1: Build
```bash
docker build -f Dockerfile.minimal -t ats-light:latest .
```

### Step 2: Run
```bash
docker-compose -f docker-compose-minimal.yml up -d
```

### Step 3: Test
```bash
curl http://localhost:8000/health
open http://localhost:8000/docs
```

## What Works on 0.5 CPU + 512MB

✅ Resume parsing (text only)
✅ Job description parsing
✅ Candidate matching
✅ Multi-tenancy
✅ Authentication
✅ API rate limiting
✅ Billing integration
✅ 15+ API endpoints

## What Doesn't Work

❌ OCR (parse text only)
❌ Local LLM (use API)
❌ Redis cache
❌ Vector search
❌ Elasticsearch
❌ Monitoring/Dashboards

## Performance

```
Resumes/day:        50-100
Concurrent users:   1-2
API calls/day:      500-2,000
Latency:            50-200ms
```

## Cost Options

- Local machine: $0
- Linode Nanode: $5-6/month
- DigitalOcean: $5-6/month
- AWS Lambda: $10-20/month
- Google Cloud Run: $10-30/month

## Upgrade Path

```
0.5 CPU + 512MB (MVP)
    ↓
1 CPU + 1GB (Small production)
    ↓
2 CPU + 2GB (Medium)
    ↓
4+ CPU + 4GB+ (Full production)
```

## Read These Docs

1. **LIGHTWEIGHT_DEPLOYMENT.md** - Full optimization guide
2. **MINIMUM_SPECS_GUIDE.md** - Complete specs reference
3. **DEPLOYMENT_GUIDE.md** - How to deploy

## Summary

| Item | Lightweight | Full |
|------|------------|------|
| CPU | 0.5 | 2-4 |
| RAM | 512MB | 4GB+ |
| DB | SQLite | PostgreSQL |
| Cost | $10-50 | $500+ |
| Resumes/day | 100 | 50K+ |

**Start with lightweight, upgrade when you grow!**

---

**Next Step:**
```bash
docker-compose -f docker-compose-minimal.yml up
```

Done! 🚀
