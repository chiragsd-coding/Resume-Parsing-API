# 🚀 START MVP NOW - 0.5 CPU + PostgreSQL

## Your Setup
- **CPU**: 0.5 total
- **RAM**: 512MB minimum
- **Services**: API + PostgreSQL only
- **Cost**: $0-10/month to start

---

## 3-STEP QUICK START

### Step 1: Prepare (2 minutes)
```bash
cd /home/chirag/Downloads/Resume-Parsing-API

# Create directories
mkdir -p data uploads

# Create .env
cat > .env << 'EOF'
DATABASE_URL=postgresql://ats_user:ats_password@postgres:5432/ats_db
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key-change-later
EOF
```

### Step 2: Start (1 minute)
```bash
docker-compose -f docker-compose-barebone.yml up -d
```

### Step 3: Verify (1 minute)
```bash
# Check running
docker ps

# Test API
curl http://localhost:8000/health

# Open API docs
open http://localhost:8000/docs
```

**Total time: ~5 minutes ✅**

---

## Files You Need

✅ Use These:
```
docker-compose-barebone.yml
Dockerfile.barebone
requirements-barebone.txt
MVP_SETUP.md (this guide)
```

❌ Don't Use:
```
docker-compose.yml (too heavy)
Dockerfile (too many features)
requirements.txt (45 packages)
```

---

## What Works

✅ Upload resumes
✅ Parse resumes (text)
✅ Create job descriptions
✅ Match candidates
✅ User management
✅ API rate limiting
✅ Billing integration
✅ 15+ endpoints

---

## Resource Split

```
Your 0.5 CPU:
  API:        0.3 CPU + 200MB RAM
  PostgreSQL: 0.2 CPU + 300MB RAM
  ═══════════════════════════════
  Total:      0.5 CPU + 500MB ✅
```

---

## API Endpoints

```
GET  /health                    Check service
POST /resumes/parse             Upload resume
POST /job-descriptions          Create job
POST /matches/search            Find candidates
GET  /billing/usage             Usage metrics
POST /auth/login               User login
```

Full docs at: http://localhost:8000/docs

---

## Common Tasks

```bash
# View logs
docker-compose -f docker-compose-barebone.yml logs -f api

# Stop services
docker-compose -f docker-compose-barebone.yml down

# Restart
docker-compose -f docker-compose-barebone.yml restart

# Check status
docker ps
```

---

## Upgrade When Revenue Comes

### At 1K/month revenue
```bash
# Upgrade to:
# - 1 CPU + 1GB RAM
# - Switch to: docker-compose-minimal.yml
```

### At 5K/month revenue
```bash
# Upgrade to:
# - 2 CPU + 2GB RAM
# - Add Redis + more features
```

### At 20K+/month revenue
```bash
# Use full setup:
# - 4+ CPU + 4GB+ RAM
# - All 13 services
# - Multi-region ready
```

---

## Revenue Potential

```
Feature               Price          Users
Basic parse          Free           Unlimited
Pro subscription     $299/month     Growing
Enterprise           Custom         Large clients
Per-resume           $0.10-$1       Variable
```

---

## Database Backups (Important!)

```bash
# Backup
docker-compose -f docker-compose-barebone.yml exec postgres \
  pg_dump -U ats_user ats_db > backup.sql

# Store safely!
# (AWS S3, Google Drive, GitHub, etc.)
```

---

## Security Checklist

- [ ] Change `SECRET_KEY` in .env
- [ ] Change PostgreSQL password
- [ ] Set `DEBUG=false`
- [ ] Enable HTTPS (in production)
- [ ] Set up backups

---

## Troubleshooting

### "Connection refused"
Wait 10 seconds for PostgreSQL to start:
```bash
sleep 10
curl http://localhost:8000/health
```

### "Out of memory"
Your system has enough (512MB allocated, ~300MB used).

### "Can't connect to database"
Check PostgreSQL is running:
```bash
docker logs ats_postgres
```

### API is slow
Normal with 0.5 CPU. When revenue comes, upgrade.

---

## Cost Options

| Option | CPU | RAM | Cost | Time |
|--------|-----|-----|------|------|
| Laptop | 0.5 | 2GB | $0 | Now |
| Linode | 0.5 | 512MB | $5/mo | Today |
| DigitalOcean | 1 | 512MB | $4/mo | Today |
| AWS | 2 | 512MB | $3/mo | Today |

**Recommendation**: Start local free, move to $5/mo server when ready.

---

## Next Steps

1. ✅ Run `docker-compose -f docker-compose-barebone.yml up -d`
2. ✅ Test API at http://localhost:8000/docs
3. ✅ Create first user
4. ✅ Upload first resume
5. ✅ Get first customer
6. ✅ Generate revenue
7. ✅ Upgrade infrastructure
8. 🚀 Scale!

---

## Support

- API Docs: http://localhost:8000/docs
- Read: MVP_SETUP.md (full guide)
- Questions? Check README.md

---

## Summary

```
You have:   0.5 CPU + PostgreSQL + API
You start:  Now with 5-minute setup
You grow:   As revenue increases
You scale:  Based on customer needs

Perfect for MVP! 🎯
```

---

**Ready? Let's go:**

```bash
docker-compose -f docker-compose-barebone.yml up -d
```

**Done! 🚀**

Visit: http://localhost:8000/docs

Your MVP is live! Now get customers. 💰

---

*Start small, grow fast, scale smart!*
