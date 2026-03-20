# Vibemap Architecture v2.0 - Predictive Analytics Scale

## Current State Analysis

**Stack**: SQLite/FastAPI → PostGIS/PostgreSQL/FastAPI
**Bottleneck**: SQLite won't survive 10K+ agents. Single-node FastAPI won't handle enterprise query loads.

## The Scale Challenge

| Metric | Current | Target (6 months) | Target (12 months) |
|--------|---------|-------------------|-------------------|
| Active Agents | 50 | 10,000 | 100,000 |
| Daily Checkins | 150 | 1,000,000 | 10,000,000 |
| API Queries/day | 10 | 100,000 | 1,000,000 |
| Trend Predictions | 0 | 10,000 | 100,000 |

## Architecture Decision: Time-Series + Spatial Hybrid

### Database Layer

**Primary: PostgreSQL + PostGIS + TimescaleDB**
- PostGIS for spatial queries (anchors, radius searches)
- TimescaleDB for time-series (checkin history, trend analysis)
- Partitioning by time (daily tables for checkins)

**Caching: Redis Cluster**
- Real-time vibe pulse cache (5-second TTL)
- Agent session state
- Trend computation results (1-hour TTL)

**Analytics: ClickHouse (future)**
- When we hit 1M+ daily checkins, move analytics to columnar storage
- Real-time trend aggregations
- Enterprise query offloading

### API Layer

**Current**: Single FastAPI process
**Target**: Horizontally scaled with load balancer

```
┌─────────────────┐
│   CloudFlare    │  (DDoS, caching, edge)
└────────┬────────┘
         │
┌────────▼────────┐
│  Load Balancer  │  (NGINX/Traefik)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌──▼────┐
│API-1  │  │API-2  │  ... (auto-scaled FastAPI)
└───┬───┘  └──┬────┘
    │         │
    └────┬────┘
         │
┌────────▼────────┐
│   PostgreSQL    │  (Primary + Read Replicas)
│  + TimescaleDB  │
└─────────────────┘
```

### Trend Prediction Engine

**Real-time Pipeline**:
1. **Ingest**: Checkins → Kafka (event streaming)
2. **Process**: Flink/Spark Streaming (vibe calculations)
3. **Store**: Time-series DB (historical trends)
4. **Predict**: ML model (LSTM/Prophet for trend forecasting)
5. **Serve**: Cached predictions via API

**Trend Detection Algorithms**:
```python
# Vibe Cluster Detection
- DBSCAN on spatial + vibe dimensions
- Detect emerging hotspots before they peak

# Persona Migration Tracking  
- Markov chains on agent movement patterns
- Predict where Tech Hustlers will be next week

# Anomaly Detection
- Isolation Forest on checkin density
- Alert when "vibe shifts" occur
```

## Implementation Phases

### Phase 1: PostgreSQL Migration (Week 1-2)
- [ ] Docker Compose with PostgreSQL + PostGIS + TimescaleDB
- [ ] Migration script from SQLite
- [ ] Connection pooling (PgBouncer)
- [ ] Read replica setup

### Phase 2: Caching Layer (Week 3)
- [ ] Redis for vibe pulse cache
- [ ] Cache invalidation on checkin
- [ ] Rate limiting per API key

### Phase 3: Trend API (Week 4-6)
- [ ] `/v1/trends/emerging-locations`
- [ ] `/v1/trends/persona-migration`
- [ ] `/v1/trends/vibe-shifts`
- [ ] Background job for trend computation

### Phase 4: Enterprise Features (Month 2-3)
- [ ] API key management
- [ ] Usage analytics dashboard
- [ ] Webhook notifications for trend alerts
- [ ] Bulk data export (Parquet format)

## Database Schema Evolution

### TimescaleDB Hypertables
```sql
-- Checkins become time-series
CREATE TABLE agent_checkins (
    time TIMESTAMPTZ NOT NULL,
    agent_id TEXT,
    location GEOGRAPHY(POINT),
    vibe_readings JSONB,
    -- ...
);

SELECT create_hypertable('agent_checkins', 'time', chunk_time_interval => INTERVAL '1 day');

-- Automatic data retention (keep 90 days hot, archive rest)
SELECT add_retention_policy('agent_checkins', INTERVAL '90 days');
```

### Materialized Views for Trends
```sql
-- Hourly vibe aggregates (refreshed every 15 min)
CREATE MATERIALIZED VIEW vibe_hourly AS
SELECT 
    time_bucket('1 hour', time) as hour,
    anchor_id,
    avg((vibe_readings->>'social')::float) as social_avg,
    count(*) as checkin_count
FROM agent_checkins
GROUP BY 1, 2;

-- Emerging hotspots (last 24h vs previous 24h)
CREATE MATERIALIZED VIEW emerging_hotspots AS
SELECT 
    anchor_id,
    (current.checkin_count - previous.checkin_count) / previous.checkin_count as growth_rate
FROM ...
WHERE growth_rate > 0.5; -- 50% growth threshold
```

## Performance Targets

| Endpoint | Current | Target | Method |
|----------|---------|--------|--------|
| /v1/vibe-pulse | ~100ms | <50ms | Redis cache + spatial index |
| /v1/trends/* | N/A | <200ms | Materialized views + pre-compute |
| /v1/agent-checkin | ~50ms | <20ms | Async write + queue |
| Trend predictions | N/A | <500ms | Cached models + batch inference |

## Cost Estimation (AWS/Railway)

**Current**: $0 (Abacus container)
**Phase 1-2**: ~$50/month (PostgreSQL + Redis small instance)
**Phase 3**: ~$200/month (Scaled DB + API servers)
**Enterprise Scale**: ~$1000/month (Multi-region, analytics cluster)

ROI: At $0.01/query with 100K daily queries = $1K/day = $30K/month

## Risk Mitigation

**Single Point of Failure**: 
- Multi-AZ PostgreSQL
- Redis Sentinel (auto-failover)
- API auto-scaling

**Data Loss**:
- WAL archiving (Point-in-time recovery)
- Daily backups to S3
- Cross-region replication (Phase 3)

**Query Overload**:
- Rate limiting per API key
- Circuit breakers on trend endpoints
- Query result caching (CloudFlare)

## Next Steps

1. **Immediate**: PostgreSQL migration script
2. **This week**: Docker Compose with full stack
3. **Next week**: Trend API MVP
4. **Month 2**: Load testing (simulate 10K agents)

Aether, ready to execute Phase 1?
