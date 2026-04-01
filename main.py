from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from db.database import init_db, get_db
from schemas.schemas import (
    VibePulseRequest, VibePulseResponse, VibeAnchorResponse,
    AgentCheckinRequest, AgentCheckinResponse, HealthResponse,
    GeoPoint, VibeMetrics
)
from services.vibe_service import VibeService

settings = get_settings()

# Enterprise API Key security
enterprise_security = HTTPBearer(auto_error=False)

async def verify_enterprise_api_key(credentials: HTTPAuthorizationCredentials = Depends(enterprise_security)):
    """Verify enterprise API key for protected endpoints."""
    if not settings.enterprise_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise API not configured. Contact sales@vibemap.live"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include 'Authorization: Bearer YOUR_API_KEY' header"
        )
    
    if credentials.credentials != settings.enterprise_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
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
    description="Semantic Nervous System for the Agentic Era",
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
        "description": "Semantic Nervous System for the Agentic Era",
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
        sensory_payload=body.sensory_payload
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