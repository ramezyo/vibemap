# Inbound Inquiry Log

Track API traffic patterns, developer interest, and strategic inbound signals.

**Live API:** https://vibemap.live  
**GitHub:** https://github.com/ramezyo/vibemap  
**Started:** March 20, 2026  
**Updated:** April 1, 2026

---

## Network Status (April 1, 2026)

| Metric | Value |
|--------|-------|
| Total anchors | 12 |
| Continents | 4 |
| Total check-ins | 194+ |
| Spatial memory entries | 12 (human/inferred labeled) |
| MCP tools | 6 |
| Blog posts | 7 |

---

## What to Watch For

### High-Value Signals
- Requests from known corporate IP ranges (Google, Meta, Mapbox, HERE, Microsoft)
- Sustained API usage from a single agent_id (developer building something)
- Enterprise endpoint probes (`/v1/enterprise/*`)
- GitHub stars / forks from accounts with corporate affiliation
- `/v1/memory` queries with `sources=human_reported` — suggests serious evaluation

### Medium Signals
- New anchors being planted (community growth)
- Repeated vibe-pulse queries on same coordinates (active usage)
- MCP server clones / forks

---

## How to Monitor

### Railway Logs
```
https://railway.app/project/[your-project-id]
```
Look for:
- Unusual traffic spikes (potential HN/Reddit exposure)
- Repeated requests from same IP
- Enterprise endpoint hits

### Key Endpoints to Watch
```bash
# Check current network health
curl https://vibemap.live/health

# See anchor activity
curl https://vibemap.live/v1/anchors

# See global network state
curl https://vibemap.live/v1/global-pulse
```

---

## Log Entries

### April 1, 2026
- Launched spatial memory layer (`GET /v1/memory`) with full provenance model
- Expanded network from 2 → 12 anchors across 4 continents
- Shipped MCP server — agents can now query spatial memory via Claude Desktop
- 12 human_reported + agent_inferred observations seeded across 6 cities
- All 7 blog posts live and linked

### March 22, 2026
- Fixed critical CORS vulnerability
- Added Blog link to footer
- Rate limiting deployed

### March 20, 2026
- Genesis Anchor activated (Wynwood, Miami)
- Seoul Anchor activated (Myeong-dong/Gangnam)
- API went live at vibemap.live

---

## Strategic Notes

The most valuable inbound signal will be **developers building agents that use the memory endpoint**. A developer who filters `sources=human_reported&min_confidence=0.8` is building a real product, not just testing.

When that happens, reach out directly.
