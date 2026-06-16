# Deployment Guide

## Local Development

### Prerequisites
```bash
Python 3.11+
Docker & Docker Compose
PostgreSQL client
Redis CLI
Ollama (for LLM)
```

### Setup
```bash
# Clone repository
git clone https://github.com/your-org/ats-platform.git
cd ats-platform

# Create .env file
cp .env.example .env

# Start services
docker-compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Initialize database
python -m alembic upgrade head

# Run tests
pytest tests/ -v

# Start API server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Postgres: localhost:5432
- Redis: localhost:6379
- Qdrant: http://localhost:6333/dashboard
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## Docker Deployment

### Build Image
```bash
docker build -t ats-platform:latest .
```

### Push to Registry
```bash
docker tag ats-platform:latest ghcr.io/your-org/ats-platform:latest
docker push ghcr.io/your-org/ats-platform:latest
```

## Kubernetes Deployment

### Prerequisites
```bash
kubectl installed
Access to K8s cluster (EKS/AKS/GKE)
Helm 3+
```

### Deploy via Helm
```bash
# Add helm repository
helm repo add ats https://charts.example.com
helm repo update

# Install
helm install ats-platform ats/ats-platform \
  --namespace production \
  --values values.yml

# Check status
kubectl get pods -n production
kubectl logs -n production -l app=ats-api
```

### Manual Deployment
```bash
# Create namespace
kubectl create namespace production

# Create secrets
kubectl create secret generic ats-secrets \
  --from-literal=database_url="postgresql://..." \
  --from-literal=stripe_secret_key="sk_..." \
  -n production

# Deploy
kubectl apply -f kubernetes/deployment.yaml -n production

# Verify
kubectl get deployment ats-api -n production
kubectl describe deployment ats-api -n production
```

### Scaling
```bash
# Manual scale
kubectl scale deployment ats-api --replicas=10 -n production

# HPA already configured - auto-scales 3-100 replicas
kubectl get hpa -n production
```

## Database Migrations

### Create Migration
```bash
alembic revision --autogenerate -m "Add new table"
```

### Apply Migration
```bash
alembic upgrade head
```

### Rollback
```bash
alembic downgrade -1
alembic downgrade base  # Rollback all
```

## Environment Configuration

### Production (.env)
```env
DATABASE_URL=postgresql://user:pass@db.example.com:5432/ats_prod
REDIS_URL=redis://cache.example.com:6379/0
QDRANT_URL=http://vector.example.com:6333
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-strong-key>
STRIPE_SECRET_KEY=sk_live_xxxxx
OLLAMA_BASE_URL=http://ollama.internal:11434
```

### Staging (.env.staging)
```env
DATABASE_URL=postgresql://user:pass@staging-db:5432/ats_staging
REDIS_URL=redis://staging-cache:6379/0
ENVIRONMENT=staging
DEBUG=false
```

## Monitoring Setup

### Prometheus Scrape Configuration
Already configured in `monitoring/prometheus.yml`

### Grafana Dashboards
1. Navigate to http://localhost:3000
2. Add Prometheus data source
3. Import dashboards from `monitoring/grafana/dashboards`

### Alert Rules
Edit `monitoring/alert_rules.yml`:
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  annotations:
    summary: "High error rate detected"
```

## Backup & Recovery

### Database Backup
```bash
# Full backup
pg_dump -U ats_user -h localhost ats_db > backup_$(date +%Y%m%d).sql

# Restore
psql -U ats_user -h localhost ats_db < backup_20240101.sql
```

### S3 Backup
```bash
# Configure WAL archiving
aws s3 cp /var/lib/postgresql/pg_wal/000000010000000000000001 \
  s3://ats-backups/wal/

# Point-in-time recovery
pg_basebackup -h localhost -U ats_user -D /recovery -Ft -z
```

## CI/CD Pipeline

### GitHub Actions
Push to trigger automatic:
1. Tests (pytest)
2. Linting (flake8, mypy)
3. Build Docker image
4. Push to registry
5. Deploy to staging
6. Run integration tests
7. Deploy to production (manual approval)

### Manual Deployment
```bash
# Direct deploy
gcloud run deploy ats-api \
  --image ghcr.io/your-org/ats-platform:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Health Checks

### API Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Database Health
```bash
curl http://localhost:8000/api/v1/health/db
```

### Service Dependencies
```bash
# Check all services
docker-compose ps

# Logs
docker-compose logs api
docker-compose logs postgres
docker-compose logs redis
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod ats-api-xyz -n production
kubectl logs ats-api-xyz -n production --previous
```

### Database connection issues
```bash
# Test connection
psql -U ats_user -h db.example.com -d ats_db -c "SELECT 1;"

# Check connection pool
SELECT count(*) FROM pg_stat_activity;
```

### High memory usage
```bash
# Check Python processes
ps aux | grep python

# Analyze memory leaks
python -m memory_profiler run app.main
```

### Performance degradation
```bash
# Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

# Rebuild indexes
REINDEX INDEX idx_resume_tenant_status;
```

## Scaling Operations

### Add Shard (Phase 2 → Phase 3)
```bash
1. Provision new DB instance
2. Create shard in config: "shard_16": "db-shard-16.internal"
3. Update routing logic
4. Gradual tenant migration
5. Verify data consistency
6. Decommission old shard
```

### Upgrade Ollama Model
```bash
1. Pull new model: ollama pull llama2-13b
2. Update OLLAMA_MODEL env var
3. Rolling restart pods
4. Monitor inference performance
```

## Security Checklist

- [ ] Enable HTTPS/TLS
- [ ] Set strong database password
- [ ] Enable WAF on load balancer
- [ ] Configure VPC security groups
- [ ] Enable audit logging
- [ ] Rotate API keys monthly
- [ ] Enable MFA for admin users
- [ ] Set up DDoS protection
- [ ] Regular security audits
- [ ] Keep dependencies updated

## Runbook Templates

### Incident: Database Down
1. Check replicas: `kubectl logs postgres-replica-1`
2. Verify DNS: `nslookup db.example.com`
3. Failover: `pg_ctl failover -D /var/lib/postgresql`
4. Reroute traffic
5. Investigation & resolution

### Incident: High CPU
1. Identify hot Pod: `kubectl top pods -n production`
2. Check processes: `top` in pod
3. Review logs for errors
4. Scale up: `kubectl scale deployment ats-api --replicas=20`
5. Root cause analysis

### Maintenance: OS Updates
1. Drain node: `kubectl drain node-1 --ignore-daemonsets`
2. Apply updates: `apt-get update && apt-get upgrade`
3. Reboot: `sudo reboot`
4. Uncordon: `kubectl uncordon node-1`
5. Verify Pod redistribution

---

**Last Updated**: 2024
**Version**: 1.0
