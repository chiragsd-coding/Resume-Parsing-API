# Scaling Strategy - From 1K to 1M+ Resumes

## Architecture Phases

### Phase 1: Startup (1K-100K Resumes)
**Single Deployment**
- 1 API server (3 replicas)
- 1 PostgreSQL instance (with replica)
- 1 Redis instance
- 1 Qdrant instance
- Monthly data pruning

**Capacity**: 100K resumes
**Cost**: ~$5K/month
**RPS**: 100-500

### Phase 2: Scaling (100K-1M Resumes)
**Database Sharding**
- Split by tenant_id
- 4-8 PostgreSQL shards
- Each shard: 1 primary + 2 replicas
- Read replicas for analytics

**Capacity**: 1M resumes
**Cost**: ~$25K/month
**RPS**: 1K-5K

### Phase 3: Enterprise (1M+ Resumes)
**Full Distributed System**
- 16+ PostgreSQL shards
- Multiple Qdrant clusters
- Redis cluster (16 nodes)
- Multiple Elasticsearch clusters
- Dedicated Ollama GPU instances
- Kafka for real-time processing

**Capacity**: 100M+ resumes
**Cost**: $100K+/month
**RPS**: 10K+

## Load Distribution

### API Load Balancing
```
NLB (Network Load Balancer)
  ├─ Pod 1 (8000)
  ├─ Pod 2 (8000)
  ├─ Pod 3 (8000)
  ├─ Pod 4-10 (auto-scale)
  └─ Pod N
```

### Database Routing (Shard Key: tenant_id)
```
Consistent Hashing
├─ Shard 0: tenant 0, 16, 32... (10 tenants)
├─ Shard 1: tenant 1, 17, 33... (10 tenants)
└─ Shard 15: tenant 15, 31, 47... (10 tenants)

Each shard:
- Primary (writes)
- Replica 1 (reads)
- Replica 2 (analytics)
```

### Cache Layer
```
Redis Cluster (16 nodes)
├─ Tenant cache: tenant_id:cache
├─ JD embedding cache: jd:{id}:embedding
├─ Match results: match_result:{jd_id}
└─ Session cache: interview:{session_id}

TTL:
- Hot data (1hr): 3600s
- Warm data (24hr): 86400s
- Cold data: Not cached
```

## Horizontal Scaling Triggers

| Metric | Threshold | Action |
|--------|-----------|--------|
| CPU | > 70% | +2 pods |
| Memory | > 80% | +2 pods |
| DB Connections | > 80% | Add replica |
| Redis Memory | > 80% | Evict cold keys |
| Queue Depth | > 1000 | +1 processing worker |

## Network Architecture

### Regional Deployment (US-East, US-West, EU)
```
AWS Route53 (Global LB)
├─ us-east-1 (Primary)
│  └─ K8s cluster (10-20 nodes)
├─ us-west-2 (Secondary)
│  └─ K8s cluster (5-10 nodes)
└─ eu-west-1 (Tertiary)
   └─ K8s cluster (5-10 nodes)

Data Replication:
- PostgreSQL: streaming replication
- Redis: cross-region sync
- Qdrant: cluster replication
```

## Processing Pipeline Scaling

### Resume Parsing
```
Input Queue (SQS/Kafka)
  ↓
Parsing Workers (100-1000)
  ├─ OCR (GPU instances)
  ├─ Text extraction
  └─ Embedding generation
  ↓
Output Storage (S3 + PostgreSQL)
  ↓
Vector DB (Qdrant)
```

### Matching Engine
```
Batch Matching (Async)
├─ New JD: Calculate against all candidates
├─ New Candidate: Calculate against all active JDs
├─ Cache results for 24 hours
└─ Background re-rank top 100

Real-time Matching (Streaming)
├─ WebSocket connections
├─ Live updates to recruiters
└─ Streaming scores as available
```

## Cost Optimization

### Compute
| Component | Instance | Count | Cost/mo |
|-----------|----------|-------|---------|
| API Pod | t3.medium | 10 | $400 |
| DB Primary | r7i.2xlarge | 1 | $2000 |
| DB Replica | r7i.xlarge | 2 | $1500 |
| Cache | cache.r7g.xlarge | 2 | $800 |
| Workers | c7i.2xlarge | 5 | $1500 |
| **Total** | | | **$6,200** |

### Storage
| Component | Size | Cost/mo |
|-----------|------|---------|
| PostgreSQL | 100GB | $300 |
| S3 (Resumes) | 500GB | $200 |
| Qdrant | 50GB | $300 |
| Backups | 150GB | $150 |
| **Total** | | **$950** |

### Data Transfer
| Type | Volume | Cost/mo |
|------|--------|---------|
| Inter-region | 1TB | $500 |
| CDN egress | 100GB | $50 |
| API calls | 10M | $200 |
| **Total** | | **$750** |

**Total Monthly Cost (Phase 2): ~$8K**

## Performance Targets

### Latency (p99)
- Resume parse: 15s (GPU-accelerated)
- Match search: 2s (cached)
- Interview generation: 5s (LLM streaming)
- API response: 200ms

### Throughput
- Parse: 100 resumes/second
- Match: 10K matches/second
- API: 5K requests/second

### Availability
- Uptime: 99.95%
- RTO: 5 minutes (failover)
- RPO: 1 minute (data loss)

## Monitoring & Alerting

### Key Metrics
```
- Pod restart rate
- Database replication lag
- Cache hit ratio
- Queue depth
- P95/P99 latencies
- Error rates by service
- Cost per transaction
```

### Dashboards
```
1. Real-time Operations
   - Live request rate
   - Error rate
   - Resource utilization
   
2. Capacity Planning
   - Growth trend
   - Shard distribution
   - Burst capacity
   
3. Financial
   - Cost per resume
   - Revenue vs cost
   - Forecast next quarter
```

## Disaster Recovery

### Multi-Region Failover
```
Primary (us-east-1) DOWN
├─ DNS failover (30s)
├─ Route to us-west-2
├─ Data loss: < 1min
└─ Full recovery: < 5min

Cross-region sync:
- RPO: 1 minute (acceptable)
- RTO: 5 minutes
```

### Database Recovery
```
Corrupted data detected
├─ Automatic backup restore
├─ Point-in-time recovery to 1min before
├─ Parallel with live system
├─ Validation + cutover
└─ Total time: 15 minutes
```

## Migration Path

### From Single DB to Sharded (100K → 1M)
1. **Week 1**: Deploy standby shard infrastructure
2. **Week 2**: Dual-write to primary + shard N
3. **Week 3**: Backfill historical data
4. **Week 4**: Verify data integrity
5. **Week 5**: Switch reads to shards
6. **Week 6**: Decomission old primary

### Zero-downtime Deployment
```
v1 (3 pods running)
├─ Deploy v2 (1 pod)
├─ Health check v2
├─ Route 10% traffic to v2
├─ Monitor for errors
├─ Route 100% traffic to v2
├─ Scale v2 to 3 pods
└─ Terminate v1 pods
```

## Auto-Scaling Rules

### Kubernetes HPA Configuration
```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 80
- type: Pods
  pods:
    metric:
      name: http_requests_per_second
    target:
      type: AverageValue
      averageValue: "1000"

minReplicas: 3
maxReplicas: 100
```

## Capacity Planning Formula

### Resumes per Shard
```
Storage: 1 resume ≈ 10KB
  - 1M resumes = 10GB per shard
  
Connections: 30 connections/shard
  - 16 shards = 480 total connections
  
CPU: 1 query ≈ 1ms
  - 100 concurrent queries = 100ms CPU
  - Utilization: 70% = 5 cores used
```

### When to Add Shard
```
Metrics:
- DB CPU > 80% for 5min
- Connections > 80% of max
- Query latency p99 > 1s
- Shard size > 500GB

Action:
- Provision new shard
- Rebalance tenant mapping
- Gradual migration (24hrs)
```
