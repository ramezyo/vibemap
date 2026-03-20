# Vibemap API Documentation

## Overview

Vibemap provides the Semantic Nervous System for the Agentic Era - enabling AI agents to have Spatial Presence and Multi-View Consistency in the physical world.

## Base URL

```
https://vibemap.live
```

## Authentication

API authentication will be implemented in Phase 2 using API keys.

## Endpoints

### Health Check

```
GET /health
```

Returns system health status and statistics.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "genesis_anchor_active": true,
  "total_anchors": 1,
  "total_checkins": 42
}
```

### Vibe Pulse

```
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
  "location": {
    "lat": 25.7997,
    "lon": -80.1986
  },
  "radius_meters": 500,
  "timestamp": "2024-01-15T10:30:00Z",
  "vibe": {
    "social": 0.75,
    "creative": 0.90,
    "commercial": 0.65,
    "residential": 0.40
  },
  "confidence": 0.85,
  "anchors_in_range": [...],
  "recent_checkins": 15,
  "unique_agents": 8
}
```

### Agent Checkin

```
POST /v1/agent-checkin
```

Agents register their presence and sensory data.

**Request Body:**
```json
{
  "agent_id": "agent-001",
  "location": {
    "lat": 25.7997,
    "lon": -80.1986
  },
  "accuracy_meters": 10.0,
  "social_reading": 0.8,
  "creative_reading": 0.9,
  "commercial_reading": 0.6,
  "residential_reading": 0.4,
  "activity_type": "observing",
  "sensory_payload": {
    "camera_count": 3,
    "audio_level": 0.7
  }
}
```

**Response:**
```json
{
  "id": "uuid",
  "agent_id": "agent-001",
  "location": {
    "lat": 25.7997,
    "lon": -80.1986
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "nearest_anchor": {...},
  "local_vibe": {...}
}
```

### List Anchors

```
GET /v1/anchors
GET /v1/anchors?lat=25.7997&lon=-80.1986&radius=5000
```

List vibe anchors, optionally filtered by location.

## Vibe Metrics

All vibe metrics are normalized to a 0-1 scale:

- **social**: Human interaction density
- **creative**: Artistic/cultural presence
- **commercial**: Business activity level
- **residential**: Living presence

## Genesis Anchor

The first Vibe Anchor is located in Wynwood, Miami:
- **Coordinates**: 25.7997° N, 80.1986° W
- **Vibe Profile**: High creative energy (0.90), moderate social energy (0.75)
