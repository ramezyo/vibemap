from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from config import get_settings
from db.database import init_db, get_db
from schemas.schemas import (
    VibePulseRequest, VibePulseResponse, VibeAnchorResponse,
    AgentCheckinRequest, AgentCheckinResponse, HealthResponse,
    GeoPoint, VibeMetrics
)
from services.vibe_service import VibeService

settings = get_settings()

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


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Semantic Nervous System for the Agentic Era",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
        "genesis_anchor": {
            "name": settings.genesis_name,
            "lat": settings.genesis_lat,
            "lon": settings.genesis_lon
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health(db: AsyncSession = Depends(get_db)):
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
async def vibe_pulse(
    request: VibePulseRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Query the social energy of a location.
    
    Returns the aggregated vibe metrics for the specified location and radius,
    including nearby anchors and recent agent activity.
    """
    service = VibeService(db)
    
    vibe, confidence, anchors, checkins, unique_agents = await service.calculate_vibe_pulse(
        request.location,
        request.radius_meters
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
    if request.include_history:
        # Simplified trend - in production, query vibe_pulses table
        vibe_trend = [
            {"hour": i, "social": vibe.social * (0.8 + 0.4 * (i % 3) / 3)}
            for i in range(min(request.history_hours, 24))
        ]
    
    return VibePulseResponse(
        location=request.location,
        radius_meters=request.radius_meters,
        timestamp=datetime.utcnow(),
        vibe=vibe,
        confidence=confidence,
        anchors_in_range=anchor_responses,
        recent_checkins=len(checkins),
        unique_agents=unique_agents,
        vibe_trend=vibe_trend
    )


@app.post("/v1/agent-checkin", response_model=AgentCheckinResponse)
async def agent_checkin(
    request: AgentCheckinRequest,
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
        "social": request.social_reading,
        "creative": request.creative_reading,
        "commercial": request.commercial_reading,
        "residential": request.residential_reading
    }
    
    # Record checkin
    checkin = await service.record_checkin(
        agent_id=request.agent_id,
        location=request.location,
        readings=readings,
        accuracy_meters=request.accuracy_meters,
        activity_type=request.activity_type,
        sensory_payload=request.sensory_payload
    )
    
    # Get local vibe context
    vibe, _, anchors, _, _ = await service.calculate_vibe_pulse(
        request.location,
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
async def list_anchors(
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
async def predictive_clusters(
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
async def export_training_data(
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
    
    training_data = await service.export_training_data(
        GeoPoint(lat=lat, lon=lon),
        radius_meters=radius,
        sample_size=samples
    )
    
    response = {
        "dataset_label": "Training Data for Large Geospatial Models (LGM) - Wynwood Alpha",
        "dataset_version": "v1.0.0",
        "sample_count": len(training_data),
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
async def global_pulse(db: AsyncSession = Depends(get_db)):
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
