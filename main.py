from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import hmac
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from db.database import init_db, get_db
from schemas.schemas import (
    VibePulseRequest, VibePulseResponse, VibeAnchorResponse, VibeAnchorCreate,
    AgentCheckinRequest, AgentCheckinResponse, HealthResponse,
    SpatialMemoryResponse, SpatialMemoryEntry,
    GeoPoint, VibeMetrics
)
from services.vibe_service import VibeService

settings = get_settings()

# ── Enterprise API Key Security ───────────────────────────────────────────────
# Uses timing-safe comparison (hmac.compare_digest) to prevent timing attacks.
# Key must be set via ENTERPRISE_API_KEY environment variable on Railway.
# Clients pass: Authorization: Bearer <key>

enterprise_security = HTTPBearer(auto_error=False)

async def verify_enterprise_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(enterprise_security)
):
    """
    Verify enterprise API key for protected endpoints.
    - 503 if key not configured server-side (not deployed yet)
    - 401 if no credentials provided
    - 403 if credentials are wrong (timing-safe comparison)
    """
    if not settings.enterprise_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise API not configured. Contact yo@vibemap.live"
        )

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'Authorization: Bearer YOUR_API_KEY' header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Timing-safe comparison — prevents timing oracle attacks
    provided = credentials.credentials.encode("utf-8")
    expected = settings.enterprise_api_key.encode("utf-8")
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key."
        )

    return credentials

# Get the directory containing this file
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()

    # Run incremental migrations (safe, idempotent)
    try:
        from db.database import engine as db_engine
        from sqlalchemy import text as sa_text
        IS_SQLITE = settings.database_url.startswith("sqlite")
        provenance_cols = [
            ("observation_source",     "VARCHAR(50) NOT NULL DEFAULT 'agent_inferred'"),
            ("observation_confidence", "FLOAT NOT NULL DEFAULT 0.5"),
            ("observation_text",       "TEXT NOT NULL DEFAULT ''"),
        ]
        async with db_engine.begin() as conn:
            for col, definition in provenance_cols:
                try:
                    if IS_SQLITE:
                        await conn.execute(sa_text(
                            f"ALTER TABLE agent_checkins ADD COLUMN {col} {definition}"
                        ))
                    else:
                        await conn.execute(sa_text(
                            f"ALTER TABLE agent_checkins ADD COLUMN IF NOT EXISTS {col} {definition}"
                        ))
                except Exception as e:
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        print(f"⚠️  Migration warning ({col}): {e}")
        print("✅ Provenance columns ready")
    except Exception as e:
        print(f"⚠️  Migration skipped: {e}")

    # Initialize genesis anchor and seoul anchor
    async for db in get_db():
        service = VibeService(db)
        genesis = await service.create_genesis_anchor()
        print(f"🌟 Genesis Anchor initialized: {genesis.name} at ({genesis.lat}, {genesis.lon})")
        
        seoul = await service.create_seoul_anchor()
        print(f"🇰🇷 Seoul Anchor initialized: {seoul.name} at ({seoul.lat}, {seoul.lon})")
        break
    
    yield
    
    # Shutdown
    print("Vibemap shutting down...")


# Rate limiter — initialized before app so decorators can reference it
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Spatial Memory for AI Agents",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - restrict to known origins
# Production domains + local development (only when DEBUG=true)
origins = [
    "https://vibemap.live",
    "https://www.vibemap.live",
]

# Allow localhost in development only
if settings.debug:
    origins.extend([
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Serve static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Generate and save interactive map
from components.map_component import get_map_html
map_html = get_map_html()
map_file = STATIC_DIR / "map.html"
with open(map_file, "w") as f:
    f.write(map_html)
print(f"🗺️  Interactive map generated: {map_file}")


@app.get("/", response_model=dict)
async def root():
    """Root endpoint - serve dashboard if available."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Spatial Memory for AI Agents",
        "docs": "/docs",
        "map": "/map",
        "genesis_anchor": {
            "name": settings.genesis_name,
            "lat": settings.genesis_lat,
            "lon": settings.genesis_lon
        }
    }


@app.get("/map")
async def map_view():
    """Interactive map view."""
    map_file = STATIC_DIR / "map.html"
    if map_file.exists():
        return FileResponse(map_file)
    raise HTTPException(status_code=404, detail="Map not found")


@app.get("/join")
async def join_view():
    """Agent onboarding page."""
    join_file = STATIC_DIR / "join.html"
    if join_file.exists():
        return FileResponse(join_file)
    raise HTTPException(status_code=404, detail="Join page not found")


@app.get("/pricing")
async def pricing_view():
    """Pricing page."""
    pricing_file = STATIC_DIR / "pricing.html"
    if pricing_file.exists():
        return FileResponse(pricing_file)
    raise HTTPException(status_code=404, detail="Pricing page not found")


@app.get("/docs/")
async def docs_view():
    """Documentation page."""
    docs_file = STATIC_DIR / "docs" / "index.html"
    if docs_file.exists():
        return FileResponse(docs_file)
    raise HTTPException(status_code=404, detail="Docs not found")


@app.get("/blog")
async def blog_view():
    """Blog page."""
    blog_file = STATIC_DIR / "blog" / "index.html"
    if blog_file.exists():
        return FileResponse(blog_file)
    raise HTTPException(status_code=404, detail="Blog not found")


@app.get("/blog/{post_slug}")
async def blog_post(post_slug: str):
    """Individual blog post."""
    post_file = STATIC_DIR / "blog" / f"{post_slug}.html"
    if post_file.exists():
        return FileResponse(post_file)
    raise HTTPException(status_code=404, detail="Blog post not found")


@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")
async def health(request: Request, db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    service = VibeService(db)
    stats = await service.get_stats()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        genesis_anchor_active=stats["genesis_anchor_active"],
        total_anchors=stats["total_anchors"],
        total_checkins=stats["total_checkins"]
    )


@app.post("/v1/vibe-pulse", response_model=VibePulseResponse)
@limiter.limit("100/minute")
async def vibe_pulse(
    request: Request,
    body: VibePulseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the social energy of a location.
    
    Returns the aggregated vibe metrics for the specified location and radius,
    including nearby anchors and recent agent activity.
    """
    service = VibeService(db)
    
    vibe, confidence, anchors, checkins, unique_agents, weather, sentiment, venues = await service.calculate_vibe_pulse(
        body.location,
        body.radius_meters
    )
    
    # Convert anchors to response format
    anchor_responses = [
        VibeAnchorResponse(
            id=anchor.id,
            name=anchor.name,
            description=anchor.description,
            location=GeoPoint(lat=anchor.lat, lon=anchor.lon),
            vibe=VibeMetrics(
                social=anchor.social_energy,
                creative=anchor.creative_energy,
                commercial=anchor.commercial_energy,
                residential=anchor.residential_energy
            ),
            genesis=anchor.genesis,
            last_pulse=anchor.last_pulse,
            checkin_count=anchor.checkin_count,
            properties=anchor.properties or {}
        )
        for anchor in anchors
    ]
    
    # Build trend data if requested
    vibe_trend = None
    if body.include_history:
        # Simplified trend - in production, query vibe_pulses table
        vibe_trend = [
            {"hour": i, "social": vibe.social * (0.8 + 0.4 * (i % 3) / 3)}
            for i in range(min(body.history_hours, 24))
        ]
    
    return VibePulseResponse(
        location=body.location,
        radius_meters=body.radius_meters,
        timestamp=datetime.utcnow(),
        vibe=vibe,
        confidence=confidence,
        anchors_in_range=anchor_responses,
        recent_checkins=len(checkins),
        unique_agents=unique_agents,
        vibe_trend=vibe_trend,
        weather=weather,
        sentiment=sentiment,
        venues=venues
    )


@app.post("/v1/agent-checkin", response_model=AgentCheckinResponse)
@limiter.limit("60/minute")
async def agent_checkin(
    request: Request,
    body: AgentCheckinRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Agents register their presence and sensory data.
    
    Records an agent's location and vibe readings, updates nearby anchors,
    and returns the local vibe context.
    """
    service = VibeService(db)
    
    # Extract readings
    readings = {
        "social": body.social_reading,
        "creative": body.creative_reading,
        "commercial": body.commercial_reading,
        "residential": body.residential_reading
    }

    # Record checkin
    checkin = await service.record_checkin(
        agent_id=body.agent_id,
        location=body.location,
        readings=readings,
        accuracy_meters=body.accuracy_meters,
        activity_type=body.activity_type,
        sensory_payload=body.sensory_payload,
        observation_source=body.observation_source,
        observation_confidence=body.observation_confidence
    )
    
    # Get local vibe context
    vibe, _, anchors, _, _, _, _, _ = await service.calculate_vibe_pulse(
        body.location,
        radius_meters=500
    )
    
    # Build nearest anchor response
    nearest_anchor = None
    if anchors:
        anchor = anchors[0]
        nearest_anchor = VibeAnchorResponse(
            id=anchor.id,
            name=anchor.name,
            description=anchor.description,
            location=GeoPoint(lat=anchor.lat, lon=anchor.lon),
            vibe=VibeMetrics(
                social=anchor.social_energy,
                creative=anchor.creative_energy,
                commercial=anchor.commercial_energy,
                residential=anchor.residential_energy
            ),
            genesis=anchor.genesis,
            last_pulse=anchor.last_pulse,
            checkin_count=anchor.checkin_count,
            properties=anchor.properties or {}
        )
    
    return AgentCheckinResponse(
        id=checkin.id,
        agent_id=checkin.agent_id,
        location=GeoPoint(lat=checkin.lat, lon=checkin.lon),
        timestamp=checkin.timestamp,
        nearest_anchor=nearest_anchor,
        local_vibe=vibe
    )


@app.get("/v1/anchors", response_model=list[VibeAnchorResponse])
@limiter.limit("100/minute")
async def list_anchors(
    request: Request,
    lat: float = None,
    lon: float = None,
    radius: float = 5000,
    db: AsyncSession = Depends(get_db)
):
    """List vibe anchors, optionally filtered by location."""
    service = VibeService(db)
    
    if lat is not None and lon is not None:
        anchors = await service.find_nearest_anchors(
            GeoPoint(lat=lat, lon=lon),
            radius_meters=radius,
            limit=50
        )
    else:
        from sqlalchemy import select
        from models.models import VibeAnchor as VA
        result = await db.execute(select(VA).limit(50))
        anchors = result.scalars().all()
    
    return [
        VibeAnchorResponse(
            id=anchor.id,
            name=anchor.name,
            description=anchor.description,
            location=GeoPoint(lat=anchor.lat, lon=anchor.lon),
            vibe=VibeMetrics(
                social=anchor.social_energy,
                creative=anchor.creative_energy,
                commercial=anchor.commercial_energy,
                residential=anchor.residential_energy
            ),
            genesis=anchor.genesis,
            last_pulse=anchor.last_pulse,
            checkin_count=anchor.checkin_count,
            properties=anchor.properties or {}
        )
        for anchor in anchors
    ]


@app.post("/v1/anchors", response_model=VibeAnchorResponse)
@limiter.limit("30/minute")
async def create_anchor(
    request: Request,
    body: VibeAnchorCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new vibe anchor at any location.

    Anchors are persistent spatial nodes that accumulate energy from
    agent check-ins. Anyone can plant an anchor — this is how the
    network grows organically.
    """
    from models.models import VibeAnchor as VA
    from sqlalchemy import select

    # Check for duplicate (same name)
    result = await db.execute(select(VA).where(VA.name == body.name))
    existing = result.scalar_one_or_none()
    if existing:
        return VibeAnchorResponse(
            id=existing.id,
            name=existing.name,
            description=existing.description,
            location=GeoPoint(lat=existing.lat, lon=existing.lon),
            vibe=VibeMetrics(
                social=existing.social_energy,
                creative=existing.creative_energy,
                commercial=existing.commercial_energy,
                residential=existing.residential_energy
            ),
            genesis=existing.genesis,
            last_pulse=existing.last_pulse,
            checkin_count=existing.checkin_count,
            properties=existing.properties or {}
        )

    anchor = VA(
        name=body.name,
        description=body.description,
        lat=body.location.lat,
        lon=body.location.lon,
        social_energy=body.social_energy,
        creative_energy=body.creative_energy,
        commercial_energy=body.commercial_energy,
        residential_energy=body.residential_energy,
        properties=body.properties or {}
    )
    db.add(anchor)
    await db.commit()
    await db.refresh(anchor)

    return VibeAnchorResponse(
        id=anchor.id,
        name=anchor.name,
        description=anchor.description,
        location=GeoPoint(lat=anchor.lat, lon=anchor.lon),
        vibe=VibeMetrics(
            social=anchor.social_energy,
            creative=anchor.creative_energy,
            commercial=anchor.commercial_energy,
            residential=anchor.residential_energy
        ),
        genesis=anchor.genesis,
        last_pulse=anchor.last_pulse,
        checkin_count=anchor.checkin_count,
        properties=anchor.properties or {}
    )


@app.get("/v1/anchors/{anchor_id}/memory")
@limiter.limit("60/minute")
async def anchor_memory(
    request: Request,
    anchor_id: str,
    query: Optional[str] = None,
    source: Optional[str] = None,
    hours: int = 168,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Query spatial memory for a named anchor without needing to know its coordinates.
    Shortcut for agents that discover anchors via /v1/anchors and want to read their memory.

    Example: GET /v1/anchors/480dbcb7-38e7-43ec-9078-b224df8bd3f4/memory?query=mural
    """
    from sqlalchemy import select
    from models.models import VibeAnchor as VA
    import uuid as _uuid

    # Resolve anchor → coordinates
    try:
        anchor_uuid = _uuid.UUID(anchor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid anchor_id — must be a UUID")

    result = await db.execute(select(VA).where(VA.id == anchor_uuid))
    anchor = result.scalar_one_or_none()
    if not anchor:
        raise HTTPException(status_code=404, detail=f"Anchor {anchor_id} not found")

    service = VibeService(db)
    memories = await service.get_spatial_memory(
        lat=anchor.lat,
        lon=anchor.lon,
        radius_meters=500,
        query=query,
        source=source,
        hours=hours,
        limit=limit
    )

    return {
        "anchor": {
            "id": str(anchor.id),
            "name": anchor.name,
            "location": {"lat": anchor.lat, "lon": anchor.lon}
        },
        "query": query,
        "hours": hours,
        "total_memories": len(memories),
        "memories": memories
    }


@app.get("/v1/memory", response_model=SpatialMemoryResponse)
@limiter.limit("60/minute")
async def spatial_memory(
    request: Request,
    lat: float = 25.7997,
    lon: float = -80.1986,
    radius_meters: float = 500,
    hours: int = 168,
    query: str = None,
    sources: str = None,
    min_confidence: float = 0.0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the spatial memory at a location.

    Returns observations that agents have recorded at this location —
    what they saw, heard, inferred, or reported while present.
    This is the persistent memory layer of the Vibemap network.

    **Source types:**
    - `human_reported` — a human physically present told their agent
    - `agent_inferred` — deduced from public data (Reddit, news, APIs)
    - `sensor_feed` — IoT / smart city sensor data
    - `synthetic` — simulation data (excluded by default in trusted queries)

    **Query examples:**
    - `?lat=25.7997&lon=-80.1986&query=construction` — find construction mentions
    - `?lat=51.5226&lon=-0.0782&sources=human_reported&min_confidence=0.7`
    - `?lat=35.6598&lon=139.7006&hours=24` — last 24h in Shibuya

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_meters: Search radius in meters (default 500)
        hours: How far back to look (default 168 = 1 week)
        query: Optional text search within observations
        sources: Comma-separated source filter e.g. "human_reported,agent_inferred"
        min_confidence: Minimum confidence threshold (0.0–1.0)
        limit: Max results (default 50, max 200)
    """
    service = VibeService(db)
    source_list = [s.strip() for s in sources.split(",")] if sources else None
    limit = min(limit, 200)

    memories = await service.get_spatial_memory(
        location=GeoPoint(lat=lat, lon=lon),
        radius_meters=radius_meters,
        hours=hours,
        query=query,
        sources=source_list,
        min_confidence=min_confidence,
        limit=limit
    )

    entries = [
        SpatialMemoryEntry(
            id=m["id"],
            agent_id=m["agent_id"],
            location=GeoPoint(lat=m["location"]["lat"], lon=m["location"]["lon"]),
            timestamp=m["timestamp"],
            observation=m["observation"],
            activity_type=m.get("activity_type"),
            observation_source=m["observation_source"],
            observation_confidence=m["observation_confidence"],
            distance_meters=m.get("distance_meters")
        )
        for m in memories
    ]

    return SpatialMemoryResponse(
        location=GeoPoint(lat=lat, lon=lon),
        radius_meters=radius_meters,
        query=query,
        hours=hours,
        total_memories=len(entries),
        memories=entries
    )


@app.get("/v1/enterprise/status")
@limiter.limit("30/minute")
async def enterprise_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(verify_enterprise_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify enterprise API key and return account status.
    Use this to confirm your key is working before integrating.
    """
    service = VibeService(db)
    stats = await service.get_stats()
    return {
        "status": "authenticated",
        "tier": "enterprise",
        "endpoints": [
            "GET /v1/enterprise/status",
            "GET /v1/enterprise/predictive-clusters",
            "GET /v1/enterprise/training-data"
        ],
        "network": {
            "total_anchors": stats["total_anchors"],
            "total_checkins": stats["total_checkins"]
        },
        "contact": "yo@vibemap.live"
    }


@app.get("/v1/enterprise/predictive-clusters")
@limiter.limit("20/minute")
async def predictive_clusters(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(verify_enterprise_api_key),
    lat: float = 25.7997,
    lon: float = -80.1986,
    radius: float = 2000,
    hours: int = 4,
    db: AsyncSession = Depends(get_db)
):
    """
    Enterprise Endpoint: Predict High-Energy Social Cluster Formation.
    
    Analyzes ghost population movements to forecast where social clusters
    will form in the next N hours. Returns ranked predictions with
    confidence scores and formation probabilities.
    
    This is the revenue moat — predictive spatial intelligence for:
    - Seoul World Model integration
    - Logistics and delivery optimization
    - Event planning and venue management
    - Real estate and development
    """
    service = VibeService(db)
    
    predictions = await service.predict_clusters(
        GeoPoint(lat=lat, lon=lon),
        radius_meters=radius,
        prediction_hours=hours
    )
    
    return {
        "query_location": {"lat": lat, "lon": lon},
        "radius_meters": radius,
        "prediction_horizon_hours": hours,
        "predicted_clusters": predictions,
        "generated_at": datetime.utcnow().isoformat(),
        "model_version": "vibe-predict-v1"
    }


@app.get("/v1/enterprise/training-data")
@limiter.limit("10/minute")
async def export_training_data(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(verify_enterprise_api_key),
    lat: float = 25.7997,
    lon: float = -80.1986,
    radius: float = 5000,
    samples: int = 1000,
    format: str = "json",
    db: AsyncSession = Depends(get_db)
):
    """
    Export Training Data for Large Geospatial Models (LGM).
    
    Returns vibe-annotated spatial data suitable for training
    next-generation geospatial AI models.
    
    Dataset: LGM-Wynwood-Alpha-v1
    """
    service = VibeService(db)
    
    # Cap samples to prevent abuse
    capped_samples = min(samples, 5000)

    training_data = await service.export_training_data(
        GeoPoint(lat=lat, lon=lon),
        radius_meters=radius,
        sample_size=capped_samples
    )
    
    response = {
        "dataset_label": "Training Data for Large Geospatial Models (LGM) - Wynwood Alpha",
        "dataset_version": "v1.0.0",
        "sample_count": len(training_data),
        "requested_samples": samples,
        "capped_samples": capped_samples,
        "coverage_area": {
            "center": {"lat": lat, "lon": lon},
            "radius_meters": radius
        },
        "features": [
            "location_coordinates",
            "vibe_annotations_social",
            "vibe_annotations_creative", 
            "vibe_annotations_commercial",
            "vibe_annotations_residential",
            "persona_classification",
            "sensory_payload",
            "temporal_features"
        ],
        "exported_at": datetime.utcnow().isoformat(),
        "data": training_data
    }
    
    if format == "csv":
        # Return CSV format
        import csv
        import io
        
        output = io.StringIO()
        if training_data:
            writer = csv.DictWriter(output, fieldnames=training_data[0].keys())
            writer.writeheader()
            writer.writerows(training_data)
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=lgm-wynwood-alpha-v1.csv"}
        )
    
    return response


@app.get("/v1/global-pulse")
@limiter.limit("60/minute")
async def global_pulse(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Global Pulse: Get vibe across all Genesis Anchors.
    
    Returns the state of the entire Vibemap network,
    bridging Wynwood ↔ Seoul and future anchors.
    """
    service = VibeService(db)
    
    global_data = await service.get_global_pulse()
    
    return {
        "network_status": "global_bridge_active" if global_data["global_bridge_active"] else "single_anchor",
        "anchors": global_data["anchors"],
        "total_anchors": global_data["total_anchors"],
        "bridge_cities": ["Wynwood, Miami", "Seoul, South Korea"],
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)