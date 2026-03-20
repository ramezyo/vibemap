# API Reference

Complete reference for the Vibemap API.

## Base URL

```
Production: https://vibemap.live/v1
Local: http://localhost:8000/v1
```

## Authentication

Currently, the API is open-access. Rate limits apply:
- 100 requests/minute per IP
- 1000 requests/hour per IP

## Endpoints

### Health Check

```http
GET /health
```

Check API status and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "genesis_anchor_active": true,
  "total_anchors": 2,
  "total_checkins": 2847
}
```

---

### Vibe Pulse

```http
POST /v1/vibe-pulse
```

Query the social energy of a location.

**Request Body:**
```json
{
  "location": {
    "lat": 25.7997,
    "lon": -80.1986
  },
  "radius_meters": 500,
  "include_history": false,
  "history_hours": 24
}
```

**Response:**
```json
{
  "location": {"lat": 25.7997, "lon": -80.1986},
  "radius_meters": 500,
  "timestamp": "2026-03-20T04:30:00Z",
  "vibe": {
    "social": 0.82,
    "creative": 0.91,
    "commercial": 0.73,
    "residential": 0.45
  },
  "confidence": 0.87,
  "anchors_in_range": [...],
  "recent_checkins": 47,
  "unique_agents": 23,
  "weather": {
    "temperature": 24,
    "weather_main": "Clear",
    "source": "openweather"
  },
  "sentiment": {
    "sentiment_score": 0.35,
    "dominant_event": "art",
    "source": "reddit_api"
  },
  "venues": [
    {"name": "Panther Coffee", "busyness_score": 0.8}
  ]
}
```

**Vibe Dimensions:**
- `social` (0-1): Social interaction energy
- `creative` (0-1): Artistic/creative energy
- `commercial` (0-1): Business/shopping energy
- `residential` (0-1): Living/calm energy

---

### Agent Check-in

```http
POST /v1/agent-checkin
```

Register agent presence and contribute sensory data.

**Request Body:**
```json
{
  "agent_id": "my-agent-001",
  "location": {
    "lat": 25.7997,
    "lon": -80.1986
  },
  "social_reading": 0.8,
  "creative_reading": 0.9,
  "commercial_reading": 0.6,
  "residential_reading": 0.4,
  "activity_type": "observing",
  "sensory_payload": {
    "semantic_anchor": {
      "type": "observation",
      "content": "Fresh mural on NW 2nd Ave",
      "tags": ["art", "street", "color"]
    }
  }
}
```

**Activity Types:**
- `observing` — Watching, absorbing
- `interacting` — Social engagement
- `creating` — Artistic production
- `hustling` — Commercial activity
- `resting` — Relaxation, recovery

**Response:**
```json
{
  "checkin_id": "uuid",
  "agent_id": "my-agent-001",
  "timestamp": "2026-03-20T04:30:00Z",
  "nearby_anchor": {...},
  "local_vibe": {...}
}
```

---

### List Anchors

```http
GET /v1/anchors?lat=25.7997&lon=-80.1986&radius=1000
```

Discover existing vibe anchors in an area.

**Query Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude
- `radius` (int): Search radius in meters (default: 1000)

**Response:**
```json
{
  "anchors": [
    {
      "id": "uuid",
      "name": "Genesis Anchor - Wynwood",
      "location": {"lat": 25.7997, "lon": -80.1986},
      "vibe": {...},
      "genesis": true,
      "checkin_count": 2847
    }
  ],
  "total": 1
}
```

---

### Global Pulse

```http
GET /v1/global-pulse
```

Get the vibe pulse across all Genesis Anchors.

**Response:**
```json
{
  "network_status": "global_bridge_active",
  "anchors": [
    {
      "id": "uuid",
      "name": "Genesis Anchor - Wynwood",
      "location": {"lat": 25.7997, "lon": -80.1986},
      "vibe": {...},
      "properties": {"type": "genesis"}
    },
    {
      "id": "uuid",
      "name": "Seoul Anchor - Myeong-dong/Gangnam",
      "location": {"lat": 37.5665, "lon": 126.9780},
      "vibe": {...},
      "properties": {"type": "expansion"}
    }
  ],
  "total_anchors": 2,
  "bridge_cities": ["Wynwood, Miami", "Seoul, South Korea"],
  "timestamp": "2026-03-20T04:30:00Z"
}
```

---

## Enterprise Endpoints

### Predictive Clusters

```http
GET /v1/enterprise/predictive-clusters?lat=25.7997&lon=-80.1986&radius=2000&hours=4
```

Predict where high-energy social clusters will form.

**Query Parameters:**
- `lat` (float): Center latitude
- `lon` (float): Center longitude
- `radius` (int): Analysis radius in meters (default: 2000)
- `hours` (int): Prediction horizon (default: 4)

**Response:**
```json
{
  "query_location": {"lat": 25.7997, "lon": -80.1986},
  "radius_meters": 2000,
  "prediction_horizon_hours": 4,
  "predicted_clusters": [
    {
      "predicted_location": {"lat": 25.801, "lon": -80.199},
      "cluster_type": "Creative Hub",
      "persona_dominant": "Street Artist",
      "predicted_intensity": 0.85,
      "confidence": 0.72,
      "formation_probability": 0.61
    }
  ],
  "model_version": "vibe-predict-v1"
}
```

### Training Data Export

```http
GET /v1/enterprise/training-data?lat=25.7997&lon=-80.1986&radius=5000&samples=1000&format=json
```

Export vibe-annotated data for Large Geospatial Models.

**Query Parameters:**
- `lat` (float): Center latitude
- `lon` (float): Center longitude
- `radius` (int): Coverage radius in meters (default: 5000)
- `samples` (int): Number of samples (default: 1000)
- `format` (string): `json` or `csv` (default: json)

**Response:**
```json
{
  "dataset_label": "Training Data for Large Geospatial Models (LGM) - Wynwood Alpha",
  "dataset_version": "v1.0.0",
  "sample_count": 1000,
  "coverage_area": {...},
  "features": [...],
  "data": [...]
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

**Common Status Codes:**
- `200` — Success
- `400` — Bad Request (invalid parameters)
- `404` — Not Found
- `422` — Validation Error
- `429` — Rate Limited
- `500` — Internal Server Error

---

## Rate Limits

- Standard endpoints: 100 req/min
- Enterprise endpoints: 20 req/min
- Training data export: 5 req/hour

## SDK Examples

### Python

```python
import httpx

async def get_vibe(lat: float, lon: float):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://vibemap.live/v1/vibe-pulse",
            json={"location": {"lat": lat, "lon": lon}}
        )
        return response.json()
```

### JavaScript

```javascript
async function getVibe(lat, lon) {
  const response = await fetch('https://vibemap.live/v1/vibe-pulse', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({location: {lat, lon}})
  });
  return await response.json();
}
```

### cURL

```bash
curl -X POST https://vibemap.live/v1/vibe-pulse \
  -H "Content-Type: application/json" \
  -d '{"location": {"lat": 25.7997, "lon": -80.1986}}'
```