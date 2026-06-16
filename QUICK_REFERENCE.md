# Quick Reference Guide

## 🚀 Start Here

### 1. Local Development (Pick One)

**Option A: Docker Compose (Recommended)**
```bash
docker-compose up -d
# Services: API, PostgreSQL, Redis, Qdrant, Elasticsearch, Ollama, Prometheus, Grafana, Loki
# API: http://localhost:8000
```

**Option B: Manual Setup**
```bash
pip install -r requirements.txt
psql -U ats_user -h localhost -d ats_db -f scripts/init_db.sql
python -m uvicorn app.main:app --reload
```

### 2. Test API
```bash
# Health check
curl http://localhost:8000/health

# Interactive docs
open http://localhost:8000/docs

# OpenAPI spec
curl http://localhost:8000/openapi.json
```

### 3. Access Services
```
API              http://localhost:8000
API Docs         http://localhost:8000/docs
PostgreSQL       localhost:5432
Redis            localhost:6379
Qdrant           http://localhost:6333/dashboard
Elasticsearch    http://localhost:9200
Prometheus       http://localhost:9090
Grafana          http://localhost:3000 (admin/admin)
Loki             http://localhost:3100
```

## 📚 Key Files

| File | Purpose | Read When |
|------|---------|-----------|
| `README.md` | Overview & features | First time |
| `ARCHITECTURE_SUMMARY.md` | What's included | Evaluating |
| `PROJECT_ARCHITECTURE.md` | System design | Understanding design |
| `DATABASE_SCHEMA.md` | PostgreSQL schema | Working with DB |
| `SCALING_STRATEGY.md` | Growing to millions | Planning scale |
| `DEPLOYMENT_GUIDE.md` | Production setup | Going to production |
| `COST_ESTIMATION.md` | Financial model | Planning budget |
| `IMPLEMENTATION_ROADMAP.md` | 12-month plan | Planning development |
| `openapi.yaml` | API specification | Building integrations |

## 🔧 Common Tasks

### Run Tests
```bash
pytest tests/ -v
pytest tests/test_api.py::test_resume_parse -v  # Single test
pytest --cov=app  # With coverage
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Add field"

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Build & Deploy
```bash
# Build Docker image
docker build -t ats-platform:latest .

# Push to registry
docker tag ats-platform:latest ghcr.io/your-org/ats-platform:latest
docker push ghcr.io/your-org/ats-platform:latest

# Deploy to K8s
kubectl apply -f kubernetes/deployment.yaml
```

### Monitor Logs
```bash
# Docker
docker-compose logs api -f

# Kubernetes
kubectl logs deployment/ats-api -f
kubectl logs deployment/ats-api --previous  # Crashed pod

# Loki (via Grafana)
# http://localhost:3000 -> Explore -> Loki
```

### Check Performance
```bash
# Redis memory
redis-cli info memory

# PostgreSQL connections
psql -U ats_user -h localhost -d ats_db -c "SELECT count(*) FROM pg_stat_activity;"

# API metrics (Prometheus)
curl http://localhost:9090/api/v1/query?query=http_requests_total
```

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in .env
- [ ] Set `ENVIRONMENT=production`
- [ ] Enable HTTPS/TLS
- [ ] Configure database password
- [ ] Set Stripe keys
- [ ] Enable firewall rules
- [ ] Configure VPC security groups
- [ ] Set up WAF
- [ ] Enable audit logging
- [ ] Configure backups

## 📊 Important Metrics

### Database
- **Connections**: `SELECT count(*) FROM pg_stat_activity;`
- **Disk usage**: `SELECT pg_size_pretty(pg_database_size(current_database()));`
- **Slow queries**: Check PostgreSQL logs
- **Replication lag**: `SELECT * FROM pg_stat_replication;`

### Cache (Redis)
- **Memory**: `redis-cli info memory`
- **Hit rate**: `redis-cli info stats` (hits/misses)
- **Connected clients**: `redis-cli info clients`

### API
- **QPS**: Check Prometheus `http_requests_total` rate
- **Error rate**: Check `http_requests_total{status=~"5.."}`
- **Latency**: Check `http_request_duration_seconds` p99

## 🎯 Scaling Checklist

### Before 100K Resumes
- [ ] Database backups working
- [ ] Monitoring alerts configured
- [ ] Rate limiting tested
- [ ] Quota system working

### Before 1M Resumes (Phase 2)
- [ ] Database sharding setup
- [ ] Redis cluster configured
- [ ] K8s auto-scaling enabled
- [ ] Multi-region replication ready

### Before 100M Resumes (Phase 3)
- [ ] 16+ database shards
- [ ] Multiple Qdrant clusters
- [ ] Redis cluster operational
- [ ] Multi-region active-active

## 🐛 Troubleshooting

### API Won't Start
```bash
# Check logs
docker-compose logs api
# Check database connection
psql -U ats_user -h localhost -d ats_db
# Check environment variables
cat .env
```

### Database Connection Issues
```bash
# Test connection
psql "postgresql://ats_user:ats_password@localhost:5432/ats_db"
# Check pool
SELECT * FROM pg_stat_activity;
# Check firewall
telnet localhost 5432
```

### High Memory Usage
```bash
# Check Python processes
ps aux | grep python
# Check Redis
redis-cli info memory
# Check PostgreSQL
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC;
```

### Slow Queries
```bash
# Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 1s
SELECT pg_reload_conf();

# Check slow log
tail -f /var/log/postgresql/postgresql.log | grep duration
```

## 🚀 Deployment Paths

### Development
```
Local Docker → Docker Push → DockerHub
```

### Staging
```
GitHub Commit → CI/CD Pipeline → ECR → ECS
```

### Production
```
GitHub Tag → CI/CD Pipeline → ECR → EKS (Auto-deploy)
```

## 💡 Pro Tips

1. **Use `.env` for secrets** - Never commit to git
2. **Test locally first** - Use docker-compose before K8s
3. **Monitor from day 1** - Prometheus/Grafana saves time
4. **Backup early** - Database backups in week 1
5. **Document API changes** - Keep openapi.yaml updated
6. **Use feature flags** - Safer production deployments
7. **Optimize queries early** - Index on created_at, tenant_id
8. **Cache aggressively** - Redis hits = happy users
9. **Alert on metrics** - Prometheus alerts before issues
10. **Version your APIs** - `/api/v1`, `/api/v2`

## 📞 Getting Help

| Question | Resource |
|----------|----------|
| "How do I...?" | README.md → Quick Start |
| "What's the architecture?" | PROJECT_ARCHITECTURE.md |
| "How do I deploy?" | DEPLOYMENT_GUIDE.md |
| "Can it scale?" | SCALING_STRATEGY.md |
| "What's the cost?" | COST_ESTIMATION.md |
| "What's the API?" | openapi.yaml |
| "What's the DB schema?" | DATABASE_SCHEMA.md |
| "What's the timeline?" | IMPLEMENTATION_ROADMAP.md |

## ⚡ Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| API response | <200ms | ~50ms |
| Resume parse | <15s | ~10s |
| Match search | <2s | ~500ms |
| Interview gen | <5s | ~3s |
| Database query | <100ms | ~10ms |
| Cache hit | <5ms | ~1ms |

## 📈 Growth Timeline

```
Month   1-3    4-6       7-9         10-12
        MVP    Scaling   Enterprise  GA
        ↓      ↓         ↓           ↓
Users   5      50        200         500+
ARR     $12K   $180K     $1.8M       $6M
RPS     100    500       2K          5K+
```

## 🎓 Learning Path

1. **Day 1**: Read README.md + PROJECT_ARCHITECTURE.md
2. **Day 2**: Run local docker-compose, explore API docs
3. **Day 3**: Study DATABASE_SCHEMA.md
4. **Day 4**: Review SCALING_STRATEGY.md
5. **Day 5**: Test endpoints via openapi.yaml
6. **Week 2**: Deploy to K8s following DEPLOYMENT_GUIDE.md
7. **Week 3**: Set up monitoring with Prometheus/Grafana
8. **Week 4**: Plan roadmap using IMPLEMENTATION_ROADMAP.md

## ✅ Pre-Launch Checklist

- [ ] All tests passing (`pytest`)
- [ ] Docker image builds successfully
- [ ] K8s deployment starts without errors
- [ ] API health check responds
- [ ] Database schema created
- [ ] Monitoring dashboards working
- [ ] Backups configured
- [ ] Auth tokens working
- [ ] Rate limiting working
- [ ] Audit logging working
- [ ] Webhooks tested
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Disaster recovery tested

---

**Need help?** Start with README.md, then check the other docs above.

**Ready to scale?** Follow DEPLOYMENT_GUIDE.md then SCALING_STRATEGY.md.

**Want to understand the code?** Check PROJECT_ARCHITECTURE.md then DATABASE_SCHEMA.md.

**Good luck! 🚀**
