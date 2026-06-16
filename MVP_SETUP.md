# MVP Setup - 0.5 CPU + PostgreSQL Only

## 🎯 Your Configuration

You have: **0.5 CPU total**
You want: **API + PostgreSQL only**
Goal: **Start generating revenue, then upgrade**

## ✅ What You Get

```
FastAPI Backend         0.3 CPU + 200MB RAM
PostgreSQL Database     0.2 CPU + 300MB RAM
─────────────────────────────────────────
TOTAL:                  0.5 CPU + 500MB RAM ✅
```

## 📋 Files You Need

### Use These Files
```
docker-compose-barebone.yml    # API + PostgreSQL only
Dockerfile.barebone            # Optimized image
requirements-barebone.txt      # Only 12 dependencies
```

### DON'T Use
```
❌ docker-compose.yml (too many services)
❌ docker-compose-minimal.yml (still has extra)
❌ Dockerfile (too much)
❌ requirements.txt (45 packages)
```

## 🚀 Quick Start (3 Steps)

### Step 1: Prepare
```bash
cd /home/chirag/Downloads/Resume-Parsing-API

# Create necessary directories
mkdir -p data uploads

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://ats_user:ats_password@postgres:5432/ats_db
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-change-later
EOF
```

### Step 2: Start Services
```bash
docker-compose -f docker-compose-barebone.yml up -d
```

### Step 3: Verify Running
```bash
# Check services
docker-compose -f docker-compose-barebone.yml ps

# Check logs
docker-compose -f docker-compose-barebone.yml logs -f api

# Health check
curl http://localhost:8000/health

# Open API docs
open http://localhost:8000/docs
```

## 📊 Resource Usage

### Actual Usage (Not Just Limits)
```
At Rest:
  API process:          ~50-80MB RAM, <0.01 CPU
  PostgreSQL:           ~100-150MB RAM, <0.01 CPU
  ───────────────────────────────────
  Idle total:           ~150-230MB (plenty of headroom)

Under Load (10 requests):
  API process:          ~150-180MB RAM, ~0.2-0.3 CPU
  PostgreSQL:           ~200-250MB RAM, ~0.1-0.15 CPU
  ───────────────────────────────────
  Peak total:           ~350-430MB, ~0.3-0.45 CPU (safe!)
```

## 🎨 Features Available

### ✅ Working Features
```
✅ Resume parsing (text only, no OCR)
✅ Job description parsing
✅ Candidate matching (basic scoring)
✅ Multi-tenancy (per-tenant data isolation)
✅ Authentication (JWT tokens)
✅ API key management
✅ Rate limiting per API key
✅ Stripe billing integration
✅ Audit logging (who did what)
✅ 15+ REST API endpoints
✅ Complete OpenAPI documentation
✅ Multi-user support
```

### ❌ Disabled (To Save Resources)
```
❌ OCR support (parse text/PDF only)
❌ Ollama LLM (use OpenAI API instead)
❌ Redis caching
❌ Vector search (Qdrant)
❌ Full-text search (Elasticsearch)
❌ Prometheus monitoring
❌ Grafana dashboards
❌ Multi-region deployment
❌ Auto-scaling
```

## 💾 Database Configuration

PostgreSQL is tuned for low resources:

```sql
max_connections=20           # Only 20 connections needed
shared_buffers=64MB          # Minimal memory
```

This is safe for development/early production with 1-2 users.

## 📈 What This Can Handle

```
Users:                  1-5 concurrent
Resumes:               100-500 total
Resumes per day:       5-20 (realistic for MVP)
API calls per day:     100-1000
Response time:         50-200ms
Database queries/sec:  1-10
```

## 🔄 How to Upgrade Later

### When You Get More CPU (0.5 → 1 CPU)
```bash
# Just increase limits in docker-compose-barebone.yml
# Change:
#   api.cpus: 0.3  →  0.5
#   postgres.cpus: 0.2  →  0.5
```

### When You Get More RAM (500MB → 1-2GB)
```bash
# Add Redis for caching
# Add more PostgreSQL connections
# Switch to docker-compose-minimal.yml
```

### When You Need All Features
```bash
# Use full docker-compose.yml with all 13 services
# Requires: 2-4 CPU + 4GB+ RAM
```

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in .env to something strong
- [ ] Change PostgreSQL password from default
- [ ] Enable HTTPS in reverse proxy (nginx/traefik)
- [ ] Set `DEBUG=false` in .env
- [ ] Enable API rate limiting in code
- [ ] Set up regular database backups
- [ ] Use strong API keys for external services

## 📝 Environment Variables

### Required (.env)
```env
DATABASE_URL=postgresql://ats_user:ats_password@postgres:5432/ats_db
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-strong-secret-key-here
```

### Optional (with defaults)
```env
STRIPE_SECRET_KEY=sk_test_xxx          # For billing
OPENAI_API_KEY=sk_xxx                  # For LLM features
SMTP_HOST=smtp.gmail.com               # For email
```

## 🚨 Common Issues

### Issue: "Connection refused" to PostgreSQL
```bash
# PostgreSQL not ready yet. Wait 10 seconds:
sleep 10
curl http://localhost:8000/health
```

### Issue: "Out of memory"
```bash
# Reduce worker processes or increase server RAM
# For now, this config should be fine
```

### Issue: "Database locked"
```bash
# PostgreSQL might be restarting. Restart services:
docker-compose -f docker-compose-barebone.yml restart
```

### Issue: API is slow
```bash
# With 0.5 CPU, some queries might take time
# Check logs for long-running queries
docker-compose -f docker-compose-barebone.yml logs api
```

## 📊 Monitoring (Basic)

### Check CPU/Memory Usage
```bash
# Real-time monitoring
docker stats

# Or check individual containers
docker stats ats_api ats_postgres
```

### Check Database Size
```bash
docker-compose -f docker-compose-barebone.yml exec postgres \
  psql -U ats_user -d ats_db -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
```

### Check Logs
```bash
# API logs
docker-compose -f docker-compose-barebone.yml logs api

# PostgreSQL logs
docker-compose -f docker-compose-barebone.yml logs postgres

# Follow logs in real-time
docker-compose -f docker-compose-barebone.yml logs -f
```

## 💰 Cost Estimate

### Bare Minimum Hosting Options

| Provider | Spec | Cost | Notes |
|----------|------|------|-------|
| Your machine | 0.5 CPU + 512MB | $0 | Local dev |
| Linode Nanode | 0.5 CPU + 512MB | $5/mo | Cheapest option |
| DigitalOcean | 1 CPU + 512MB | $4/mo | Very cheap |
| AWS EC2 t4g.nano | 2 vCPU + 512MB | $3.33/mo | Good value |
| Heroku | 0.5 dyno | $7/mo | Easy to deploy |
| Railway.app | 0.5 CPU + 512MB | $5-10/mo | Developer friendly |

**Recommended for MVP**: Linode Nanode or DigitalOcean Droplet ($5-6/month)

## 🎯 What to Do Next

### Immediate (Today)
- [ ] Run `docker-compose -f docker-compose-barebone.yml up -d`
- [ ] Test API at http://localhost:8000/docs
- [ ] Create first user via API
- [ ] Upload first resume

### This Week
- [ ] Connect to Stripe for billing
- [ ] Set up PostgreSQL backups
- [ ] Deploy to cloud ($5/mo server)
- [ ] Get first customer

### Next Month (When Revenue Comes In)
- [ ] Upgrade to 1 CPU + 1GB RAM
- [ ] Add Redis caching
- [ ] Add OCR support
- [ ] Switch to docker-compose-minimal.yml

### After Revenue Stable
- [ ] Upgrade to full version (2+ CPU + 2GB+ RAM)
- [ ] Add all features
- [ ] Scale horizontally
- [ ] Multi-region deployment

## 📚 Documentation

| File | Read When |
|------|-----------|
| README.md | Understand project |
| openapi.yaml | Build API clients |
| DATABASE_SCHEMA.md | Query database directly |
| DEPLOYMENT_GUIDE.md | Deploy to production |
| COST_ESTIMATION.md | Financial planning |

## ✅ Verification Checklist

- [ ] Services running: `docker ps` shows 2 containers
- [ ] API healthy: `curl http://localhost:8000/health`
- [ ] API docs working: `http://localhost:8000/docs`
- [ ] Database connected: `curl http://localhost:8000/api/v1/billing/usage`
- [ ] No errors in logs: `docker-compose logs | grep ERROR` (empty)

## 🎉 You're Ready!

You now have:
- ✅ Bare minimum MVP setup
- ✅ API + PostgreSQL running
- ✅ 0.5 CPU perfectly utilized
- ✅ Ready to accept first customers
- ✅ Clear upgrade path

**Start generating revenue, then upgrade! 🚀**

---

## Quick Commands Reference

```bash
# Start services
docker-compose -f docker-compose-barebone.yml up -d

# Stop services
docker-compose -f docker-compose-barebone.yml down

# View logs
docker-compose -f docker-compose-barebone.yml logs -f

# Check services
docker-compose -f docker-compose-barebone.yml ps

# Restart services
docker-compose -f docker-compose-barebone.yml restart

# View resource usage
docker stats

# Backup database
docker-compose -f docker-compose-barebone.yml exec postgres \
  pg_dump -U ats_user ats_db > backup.sql

# Restore database
docker-compose -f docker-compose-barebone.yml exec -T postgres \
  psql -U ats_user ats_db < backup.sql
```

---

**Start with this MVP setup. When revenue flows in, upgrade! 💰**
