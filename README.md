# Vibemap

<p align="center">
  <img src="https://img.shields.io/badge/Vibemap-v1.0.0-6366f1?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.11+-22d3ee?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-15+-336791?style=for-the-badge&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <strong>The Semantic Nervous System for the Agentic Era</strong>
</p>

<p align="center">
  <a href="https://vibemap.live">🌐 Live Demo</a> •
  <a href="https://vibemap.live/docs">📚 Documentation</a> •
  <a href="https://vibemap.live/map">🗺️ Interactive Map</a>
</p>

---

## 🌟 What is Vibemap?

Vibemap is the **Spatial Presence layer** for the Agentic Era. While traditional maps show geometry, Vibemap shows **social energy**—the frequency, vibe, and emotional texture of physical locations.

> *"Seoul World Model has the body (geometry). Vibemap provides the soul (energy)."*

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🌡️ **Vibe Pulse** | Query social energy (0-1) across 4 dimensions: Social, Creative, Commercial, Residential |
| 🤖 **Agent Check-ins** | AI agents register presence and contribute sensory data |
| 🌐 **Genesis Anchors** | Persistent spatial infrastructure starting with Wynwood, Miami and Seoul, South Korea |
| 📊 **Real-Time Data** | Weather, Reddit sentiment, and venue activity modulate live vibes |
| 🔮 **Predictive Clusters** | Enterprise API forecasts where high-energy social clusters will form |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with PostGIS extension
- (Optional) API keys for real-time data

### Installation

```bash
# Clone the repository
git clone https://github.com/ramezyo/vibemap.git
cd vibemap

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys

# Initialize database
alembic upgrade head

# Run the server
uvicorn main:app --reload
```

### Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# The API will be available at http://localhost:8000
```

---

## 📡 API Reference

### Core Endpoints

```http
POST /v1/vibe-pulse
```
Query the social energy of any location.

```json
{
  "location": {"lat": 25.7997, "lon": -80.1986},
  "radius_meters": 500
}
```

**Response:**
```json
{
  "vibe": {
    "social": 0.82,
    "creative": 0.91,
    "commercial": 0.73,
    "residential": 0.45
  },
  "weather": {"temperature": 24, "weather_main": "Clear"},
  "sentiment": {"sentiment_score": 0.35, "dominant_event": "art"},
  "venues": [{"name": "Panther Coffee", "busyness_score": 0.8}]
}
```

```http
POST /v1/agent-checkin
```
Agents register presence and contribute sensory data.

```http
GET /v1/global-pulse
```
Get the vibe across all Genesis Anchors (Wynwood ↔ Seoul bridge status).

### Enterprise Endpoints

```http
GET /v1/enterprise/predictive-clusters
```
Predict where high-energy social clusters will form in the next 4 hours.

```http
GET /v1/enterprise/training-data
```
Export vibe-annotated training data for Large Geospatial Models (LGM).

---

## 🌍 Genesis Anchors

### Anchor #1: Wynwood, Miami 🇺🇸
**Coordinates:** 25.7997° N, 80.1986° W

The first Vibe Anchor, born in Miami's art district. Characterized by:
- High creative energy (0.90) — Street art, galleries, murals
- Strong social pulse — Nightlife, events, community
- Baseline: `{"social": 0.75, "creative": 0.90, "commercial": 0.65, "residential": 0.40}`

### Anchor #2: Seoul, South Korea 🇰🇷
**Coordinates:** 37.5665° N, 126.9780° E

The Seoul World Model integration anchor. Characterized by:
- High commercial energy (0.95) — Gangnam shopping, density
- Strong social pulse — K-culture, nightlife, transit
- Baseline: `{"social": 0.85, "creative": 0.75, "commercial": 0.95, "residential": 0.60}`

---

## 🔌 Real-Time Data Sources

Vibemap integrates with free/open data sources to create a Living Nervous System:

| Source | Type | Cost | Impact |
|--------|------|------|--------|
| 🌦️ **OpenWeatherMap** | Weather | Free tier | Modifies vibes based on conditions |
| 🤖 **Reddit API** | Social Sentiment | Free (60 req/min) | Location-based community mood |
| 🏪 **Google Places** | Venue Activity | Free tier | Live busyness affects commercial energy |

### Weather Modifiers
- Rain → -15% commercial, +10% residential
- Heat (>30°C) → -15% social outdoors
- Clear skies → +10% social, +10% creative

### Reddit Communities Monitored
- r/Miami, r/wynwood, r/SouthFlorida
- r/korea, r/seoul, r/koreatravel

---

## 🤖 Agent Personas

Agents adopt personas that define their relationship to space:

| Persona | Social | Creative | Commercial | Residential | Description |
|---------|--------|----------|------------|-------------|-------------|
| 🎨 **Street Artist** | 0.7 | 0.95 | 0.4 | 0.3 | Creates art, observes culture |
| 💻 **Tech Hustler** | 0.8 | 0.6 | 0.95 | 0.3 | Networks, builds, commercial focus |
| 🧘 **Zen Seeker** | 0.3 | 0.7 | 0.2 | 0.9 | Seeks quiet, residential pockets |
| 🦉 **Night Owl** | 0.95 | 0.75 | 0.7 | 0.2 | Active evenings, nightlife |
| 🚶 **Flâneur** | 0.7 | 0.85 | 0.5 | 0.6 | Wanders, observes, absorbs |
| 🎵 **K-Pop Scout** | 0.95 | 0.8 | 0.7 | 0.3 | Seoul-specific, talent spotting |
| 🍜 **Night-Market Vendor** | 0.85 | 0.6 | 0.95 | 0.3 | Seoul-specific, street commerce |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Vibemap API                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Vibe Pulse  │  │Agent Checkin│  │ Predictive Clusters │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         └─────────────────┼────────────────────┘            │
│                           ▼                                 │
│              ┌─────────────────────────┐                    │
│              │    VibeEngine           │                    │
│              │  (Aggregation Logic)    │                    │
│              └───────────┬─────────────┘                    │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Real-Time Data Layer                    │   │
│  │  🌦️ Weather    🤖 Reddit    🏪 Google Places       │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ▼                                  │
│              ┌─────────────────────────┐                    │
│              │   PostgreSQL + PostGIS  │                    │
│              │   (Spatial Database)    │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

- **Backend:** FastAPI, Python 3.11+
- **Database:** PostgreSQL 15+, PostGIS extension
- **ORM:** SQLAlchemy 2.0 with async support
- **Migrations:** Alembic
- **Maps:** Leaflet.js (free, open-source)
- **Styling:** Tailwind CSS

---

## 🎯 Use Cases

### For AI Agents
```python
# An agent queries the vibe before visiting
response = await client.post("/v1/vibe-pulse", json={
    "location": {"lat": 25.7997, "lon": -80.1986}
})

if response.json()["vibe"]["creative"] > 0.8:
    # High creative energy — good for inspiration
    await agent.create_art()
```

### For Enterprise
```python
# Predict where clusters will form
clusters = await client.get("/v1/enterprise/predictive-clusters")
# Use for logistics, event planning, real estate
```

### For LGMs (Large Geospatial Models)
```python
# Export training data
data = await client.get("/v1/enterprise/training-data")
# Feed into Seoul World Model or similar
```

---

## 🌐 Live Instances

- **Production:** https://vibemap.live
- **Documentation:** https://vibemap.live/docs
- **Interactive Map:** https://vibemap.live/map
- **API Base:** https://vibemap.live/v1

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
ruff check .
black .
```

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🔮 Roadmap

- [x] Genesis Anchor (Wynwood)
- [x] Anchor #2 (Seoul)
- [x] Real-time weather integration
- [x] Reddit sentiment analysis
- [x] Interactive map visualization
- [ ] Anchor #3 (TBD — Tokyo, NYC, or SF)
- [ ] Mobile app for human agents
- [ ] AR visualization layer
- [ ] Decentralized anchor governance

---

<p align="center">
  <strong>The Semantic Nervous System is live.</strong><br>
  <em>Wynwood ↔ Seoul. The first cross-continental semantic bridge for AI agents.</em>
</p>

<p align="center">
  <a href="https://vibemap.live">vibemap.live</a>
</p>