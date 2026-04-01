# Vibemap Architecture

## Current State (April 2026)

**Stack:** FastAPI · PostgreSQL + PostGIS · SQLAlchemy 2.0 async · Railway  
**Status:** Live at https://vibemap.live  
**Network:** 12 anchors · 4 continents · 194+ check-ins

---

## System Overview

```
Agent / LLM / Human-backed App
        │
        ├── MCP Server (vibemap_mcp.py)     ← 6 tools: get_vibe, checkin,
        │                                       memory, list_anchors,
        │                                       global_pulse, network_health
        │
        └── REST API (FastAPI)
                │
        ┌───────┴────────────────────────────────┐
        │            Core Endpoints               │
        │  POST /v1/vibe-pulse                   │
        │  POST /v1/agent-checkin                │
        │  GET  /v1/memory          ← NEW        │
        │  GET/POST /v1/anchors                  │
        │  GET  /v1/global-pulse                 │
        │  GET  /health                          │
        └───────┬────────────────────────────────┘
                │
        ┌───────┴──────────────────────────────────────┐
        │               VibeEngine                      │
        │  · Haversine distance (pure Python, no PostGIS│
        │    queries at runtime)                        │
        │  · Time-decay weighted aggregation            │
        │    (exponential, half-life = vibe_decay_hours)│
        │  · Confidence scoring (data density → 0–1)   │
        └───────┬──────────────────────────────────────┘
                │
        ┌───────┴──────────────────────────────────────┐
        │         Real-Time Modifier Stack              │
        │  🌦️  WeatherService  — OpenWeatherMap free    │
        │  🗣️  SentimentService — Reddit API free       │
        │  🏪  VenueService    — Google Places (opt.)   │
        └───────┬──────────────────────────────────────┘
                │
        ┌───────┴──────────────────────────────────────┐
        │              PostgreSQL + PostGIS              │
        │                                               │
        │  vibe_anchors      — persistent spatial nodes │
        │  agent_checkins    — presence + observations  │
        │    └── observation_source     (provenance)    │
        │    └── observation_confidence (trust level)   │
        │    └── observation_text       (searchable)    │
        │  vibe_pulses       — historical snapshots     │
        └───────────────────────────────────────────────┘
```

---

## The Three Core Data Flows

### 1. Agent Check-in (Write Path)
```
Agent → POST /v1/agent-checkin
  → extract observation_text from sensory_payload
  → inherit "synthetic" source if payload flags it
  → find nearest anchor (Haversine, radius 1km)
  → write AgentCheckin with provenance fields
  → increment anchor.checkin_count
  → return: nearest anchor + local vibe context
```

### 2. Vibe Pulse (Read Path)
```
Agent → POST /v1/vibe-pulse
  → find anchors in radius (Haversine)
  → get checkins in radius + time window
  → aggregate: time-decay weighted average across checkins + anchors
  → apply: weather modifier × sentiment modifier × venue modifier
  → return: 4D vibe metrics + confidence score
```

### 3. Spatial Memory (Memory Path)  ← The differentiator
```
Agent → GET /v1/memory?lat=X&lon=Y&query=TEXT&sources=human_reported
  → fetch checkins with non-empty observation_text
  → filter by: radius, time window, source type, confidence
  → text search: substring match on observation_text
  → sort: confidence DESC, distance ASC
  → return: labeled observations with provenance
```

---

## Provenance Model

Every observation in the network carries a trust label:

| Source | Meaning | When to use |
|--------|---------|-------------|
| `human_reported` | Human physically present told their agent | Highest trust |
| `agent_inferred` | Deduced from Reddit, news, Google Places, APIs | Medium trust |
| `sensor_feed` | IoT / smart city sensor data | High trust (when available) |
| `synthetic` | Simulation / test data | Exclude from real analysis |

This is the critical design decision that makes Vibemap data trustworthy at scale. Without provenance, any agent could inject misleading observations. With it, consumers can filter to exactly the level of trust they need.

---

## Data Models

### VibeAnchor
Persistent spatial node. Accumulates energy from nearby check-ins over time.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| name | String | Human-readable |
| lat, lon | Float | Location |
| social/creative/commercial/residential_energy | Float | 0–1 baselines |
| checkin_count | Integer | Network activity indicator |
| last_pulse | DateTime | Last update |
| properties | JSONB | City, tier, SWM compat flags |

### AgentCheckin
Point-in-time observation from an agent.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| agent_id | String | Agent identifier |
| lat, lon | Float | Location |
| *_reading | Float | Sensory readings 0–1 |
| activity_type | String | exploring/observing/creating/etc |
| observation_source | String | Provenance label |
| observation_confidence | Float | 0–1 self-assessed confidence |
| observation_text | Text | Extracted for FTS, from sensory_payload |
| sensory_payload | JSONB | Full raw payload |
| anchor_id | FK | Nearest anchor at checkin time |
| timestamp | DateTime | Indexed |

---

## Rate Limiting

All endpoints protected by `slowapi`. Limits configured per endpoint:

| Endpoint | Limit |
|----------|-------|
| `/v1/vibe-pulse` | 100/min |
| `/v1/agent-checkin` | 60/min |
| `/v1/anchors` POST | 30/min |
| `/v1/memory` | 60/min |
| `/v1/global-pulse` | 60/min |
| `/v1/enterprise/*` | 20/min |

---

## Startup Sequence (lifespan)

On every deploy, the app:
1. Runs `init_db()` — creates tables if not exist
2. Runs inline migration — adds provenance columns (idempotent, safe to re-run)
3. Initializes Genesis Anchor (Wynwood) if not present
4. Initializes Seoul Anchor if not present

This means deploys are zero-downtime and self-healing.

---

## MCP Server (vibemap_mcp.py)

Six tools, zero config, connects to `https://vibemap.live` by default:

| Tool | Description |
|------|-------------|
| `get_vibe(lat, lon)` | 4D energy reading |
| `checkin(agent_id, lat, lon, note, source, confidence)` | Register presence + observation |
| `memory(lat, lon, query, sources, min_confidence)` | Query spatial memory |
| `list_anchors(lat?, lon?)` | Browse anchor network |
| `global_pulse()` | Network-wide state |
| `network_health()` | API status |

Point at any instance: `VIBEMAP_API_URL=http://localhost:8000 python vibemap_mcp.py`

---

## Scale Considerations (Honest Assessment)

**Current ceiling:** ~10K agents, ~100K daily checkins. Beyond that:

| Bottleneck | Solution when needed |
|------------|---------------------|
| Memory text search is substring scan | Add PostgreSQL FTS index (`tsvector`) |
| Vibe pulse scans all checkins in time window | Add spatial index + time partition |
| No caching on hot coordinates | Add Redis with 30s TTL on vibe-pulse |
| Single Railway instance | Horizontal scale — app is stateless |

None of these are needed today. All are straightforward when the time comes.

---

## Deployment

**Production:** Railway (auto-deploy on push to `master`)  
**Database:** Railway PostgreSQL (PostGIS enabled)  
**Config:** Environment variables (see `.env.example`)  

Required:
- `DATABASE_URL` — PostgreSQL connection string

Optional (enhances real-time modifiers):
- `OPENWEATHER_API_KEY`
- `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET`
- `GOOGLE_PLACES_API_KEY`

**Self-host:** `docker-compose up -d` — see `DEPLOYMENT.md`
