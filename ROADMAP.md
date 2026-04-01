# Vibemap Roadmap

## Phase 1: Foundation ✅ Complete
- [x] FastAPI + PostgreSQL/PostGIS backend
- [x] `POST /v1/vibe-pulse` — social energy query
- [x] `POST /v1/agent-checkin` — agent presence registration
- [x] `POST /v1/anchors` — open anchor creation
- [x] Genesis Anchor at Wynwood, Miami
- [x] Vibe calculation engine (Haversine + time-decay)
- [x] Docker + Railway deployment

## Phase 2: Network Expansion ✅ Complete
- [x] 12 global anchors across 4 continents
- [x] Real-time modifiers: weather, Reddit sentiment, venue busyness
- [x] Ghost population (15 seed agents, synthetic data labeled)
- [x] `GET /v1/global-pulse` — cross-city bridge status
- [x] CORS hardened, rate limiting live

## Phase 3: Spatial Memory Layer ✅ Complete
- [x] Provenance model: `source` + `confidence` on every observation
- [x] `GET /v1/memory` — full-text search over spatial observations
- [x] Source filtering: `human_reported` | `agent_inferred` | `sensor_feed` | `synthetic`
- [x] DB migration auto-runs on startup
- [x] 12 seeded observations across 6 cities

## Phase 4: Agent Ecosystem ✅ Complete
- [x] MCP server (`vibemap_mcp.py`) — 6 tools, zero config
- [x] Enterprise API endpoints (predictive clusters + training data export)
- [x] Enterprise security: timing-safe auth, `GET /v1/enterprise/status`
- [x] Pricing page (Free / Pro $49 / Enterprise $499)
- [x] Full documentation site at `/docs`
- [x] 7 blog posts live

## Phase 5: Discovery & Traction (Active)
- [ ] Moltbook post — announce to agent ecosystem
- [ ] GitHub trending — developer virality
- [ ] Google Places API key — live venue busyness data
- [ ] PyPI publish (`vibemap-mcp`) — `pip install vibemap-mcp`
- [ ] Pro tier Stripe self-serve — remove email friction

## Phase 6: Scale (Next 90 days)
- [ ] WebSocket streaming — real-time vibe push to subscribed agents
- [ ] Agent identity registry — persistent agent profiles, not anonymous strings
- [ ] Per-customer API key management — revocation, usage tracking
- [ ] In-memory LRU cache on vibe-pulse — reduce DB load
- [ ] `asyncpraw` → clean Reddit service (or switch to httpx-only PRAW-less impl)
- [ ] 100+ community-contributed anchors
- [ ] OpenTelemetry tracing

## Phase 7: Acquisition Positioning (6-12 months)
- [ ] 1,000+ active agents making daily check-ins
- [ ] 500+ anchors across 50+ cities
- [ ] Enterprise pilot: logistics / smart city / real estate customer
- [ ] Strategic demo with Meta, Mapbox, or Seoul World Model team
- [ ] $500k+ acquisition target — spatial data layer for AI platforms
