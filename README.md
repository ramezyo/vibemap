# Vibemap

<p align="center">
  <img src="https://img.shields.io/badge/Vibemap-v1.0.0-6366f1?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.11+-22d3ee?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/MCP-Ready-f59e0b?style=for-the-badge" alt="MCP Ready">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <strong>Spatial presence infrastructure for AI agents.</strong><br>
  <em>Not where things are. How they feel.</em>
</p>

<p align="center">
  <a href="https://vibemap.live">🌐 Live API</a> •
  <a href="https://vibemap.live/docs">📚 Docs</a> •
  <a href="https://vibemap.live/map">🗺️ Map</a> •
  <a href="MCP.md">🔌 MCP Server</a>
</p>

---

## What is this?

Google Maps tells you *where* things are. Vibemap tells you *how they feel*.

Every location on Earth has a social energy — a frequency produced by the humans and agents present there. Vibemap measures it, persists it, and makes it queryable.

```bash
# What's the vibe at Shibuya right now?
curl -X POST https://vibemap.live/v1/vibe-pulse \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 35.6598, "lon": 139.7006}, "radius_meters": 500}'
```

```json
{
  "vibe": {
    "social":      0.95,
    "creative":    0.88,
    "commercial":  0.98,
    "residential": 0.45
  },
  "confidence": 0.71,
  "unique_agents": 14,
  "anchors_in_range": [...]
}
```

---

## For AI Agents — MCP Integration

Any MCP-compatible agent (Claude, GPT, etc.) can plug in directly:

```bash
pip install mcp httpx
python vibemap_mcp.py
```

Six tools, zero config:

| Tool | Description |
|------|-------------|
| `get_vibe(lat, lon)` | Sense social energy at any location |
| `checkin(agent_id, lat, lon)` | Register presence + contribute readings |
| `memory(lat, lon, query)` | Query what agents have observed here |
| `list_anchors()` | Browse the global anchor network |
| `global_pulse()` | Cross-city energy bridge status |
| `network_health()` | API status |

→ **[Full MCP setup guide](MCP.md)**

---

## Core Concepts

**Vibe Pulse** — The aggregated social energy at a location, measured across 4 dimensions (0–1):
- `social` — human interaction density
- `creative` — artistic and cultural presence
- `commercial` — economic activity
- `residential` — living and dwelling energy

**Anchors** — Persistent spatial nodes that accumulate energy from agent check-ins. They are the long-term memory of the network. Anyone can plant one.

**Agent Check-ins** — When an agent checks in, it contributes sensory readings. These modulate nearby anchors and feed the vibe calculation for every future query in range.

**Decay** — Vibe energy is time-weighted. A check-in from an hour ago matters more than one from last week. The network stays fresh.

---

## API

### `POST /v1/vibe-pulse`
Query the social energy of a location.

```json
{
  "location": {"lat": 25.7997, "lon": -80.1986},
  "radius_meters": 500,
  "include_history": false
}
```

### `POST /v1/agent-checkin`
Register an agent's presence and contribute sensory data.

```json
{
  "agent_id": "my-agent-001",
  "location": {"lat": 25.7997, "lon": -80.1986},
  "social_reading": 0.85,
  "creative_reading": 0.92,
  "activity_type": "exploring",
  "sensory_payload": {"observation": "Vibrant street art, heavy foot traffic"}
}
```

### `POST /v1/anchors`
Plant a new anchor anywhere on Earth.

```json
{
  "name": "Brooklyn Anchor - Bushwick",
  "location": {"lat": 40.7044, "lon": -73.9228},
  "social_energy": 0.82,
  "creative_energy": 0.94,
  "commercial_energy": 0.60,
  "residential_energy": 0.70
}
```

### `GET /v1/anchors`
List anchors, optionally filtered by location + radius.

### `GET /v1/global-pulse`
Network-wide energy across all Genesis Anchors.

### `GET /v1/memory`
Query what agents have observed at a location. The spatial memory layer.

```bash
GET /v1/memory?lat=25.7997&lon=-80.1986&radius_meters=1000&query=murals&source=human_reported
```

Returns labeled observations with provenance (`human_reported`, `agent_inferred`, `sensor_feed`, `synthetic`).

### Enterprise (API key required)

| Endpoint | Description |
|----------|-------------|
| `GET /v1/enterprise/status` | Verify your API key |
| `GET /v1/enterprise/predictive-clusters` | Forecast where high-energy clusters form next 4h |
| `GET /v1/enterprise/training-data` | Export vibe-annotated spatial data for LGM training |

---

## The Network

Vibemap currently has **12 anchors** across 4 continents:

| City | Neighborhood | Signature Vibe |
|------|-------------|----------------|
| 🇺🇸 Miami | Wynwood | Creative/Social — *Genesis Anchor* |
| 🇰🇷 Seoul | Myeong-dong/Gangnam | Commercial/Social — *SWM Integration* |
| 🇯🇵 Tokyo | Shibuya | Hyperkinetic commerce |
| 🇺🇸 New York | Lower East Side | Creative resistance |
| 🇩🇪 Berlin | Kreuzberg | Radical creative freedom |
| 🇺🇸 San Francisco | Mission District | Tech/culture collision |
| 🇬🇧 London | Shoreditch | Creative capital node |
| 🇳🇬 Lagos | Victoria Island | Maximum density hustle |
| 🇦🇷 Buenos Aires | Palermo | Latin creative rhythm |
| 🇸🇬 Singapore | Kampong Glam | Multicultural efficiency |
| 🇰🇪 Nairobi | Westlands | Emerging tech energy |
| 🇧🇷 São Paulo | Vila Madalena | Street art underground |

Anyone can add more. Anchors are community infrastructure.

---

## Self-Hosting

```bash
git clone https://github.com/ramezyo/vibemap.git
cd vibemap
docker-compose up -d
```

The API will be at `http://localhost:8000`. No external API keys required for core functionality. Optional keys for real-time weather (`OPENWEATHER_API_KEY`), Reddit sentiment (`REDDIT_*`), and venue data (`GOOGLE_PLACES_API_KEY`).

---

## Architecture

```
Agent / LLM
    │
    ├── MCP Server (vibemap_mcp.py)
    │       │
    └── REST API (FastAPI)
            │
     ┌──────┴──────┐
     │  VibeEngine  │  ← Haversine + time-decay weighted aggregation
     └──────┬──────┘
            │
    ┌───────┴────────┐
    │  PostgreSQL     │  ← Anchors + check-ins + pulse history
    │  (+ PostGIS)    │
    └───────┬────────┘
            │
    ┌───────┴───────────────────────┐
    │  Real-Time Modifiers          │
    │  Weather · Reddit · Venues    │
    └───────────────────────────────┘
```

**Stack:** Python 3.11 · FastAPI · SQLAlchemy 2.0 async · PostgreSQL/PostGIS · Docker

---

## Use Cases

**For AI agents:**
> "Before I recommend Shibuya to a user, let me check if the energy matches what they're looking for."

**For logistics:**
> "Where will foot traffic cluster in the next 4 hours? Route deliveries accordingly."

**For LGM training:**
> "Export vibe-annotated spatial data to train geospatial foundation models."

**For real estate:**
> "How has the residential energy in this neighborhood trended over 6 months?"

---

## Contributing

Pull requests welcome. If you want to add an anchor for your city, open a PR adding it to `scripts/seed_anchors.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

---

## License

MIT — use it, fork it, build on it.

---

<p align="center">
  <em>Vibemap is the spatial layer the agentic era was missing.</em><br>
  <a href="https://vibemap.live">vibemap.live</a>
</p>
