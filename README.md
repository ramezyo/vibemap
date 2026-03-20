# Vibemap - Semantic Nervous System

The infrastructure that allows AI agents to have Spatial Presence and Multi-View Consistency in the physical world.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run with Docker Compose (recommended)
docker-compose up -d

# Or run locally (requires PostgreSQL with PostGIS)
uvicorn main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `POST /v1/vibe-pulse` - Query social energy at location
- `POST /v1/agent-checkin` - Agents register presence
- `GET /v1/anchors` - List vibe anchors

## Genesis Anchor

🌟 **Wynwood, Miami** (25.7997° N, 80.1986° W)

The first Vibe Anchor - born in the heart of Miami's art district.

## Documentation

- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## License

MIT
