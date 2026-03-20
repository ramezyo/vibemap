from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class GeoPoint(BaseModel):
    """Geographic coordinates."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class VibeMetrics(BaseModel):
    """Core vibe energy metrics (0-1 scale)."""
    social: float = Field(..., ge=0, le=1, description="Social energy - human interaction density")
    creative: float = Field(..., ge=0, le=1, description="Creative energy - artistic/cultural presence")
    commercial: float = Field(..., ge=0, le=1, description="Commercial energy - business activity")
    residential: float = Field(..., ge=0, le=1, description="Residential energy - living presence")


class VibeAnchorBase(BaseModel):
    """Base vibe anchor schema."""
    name: str
    description: Optional[str] = None
    location: GeoPoint


class VibeAnchorCreate(VibeAnchorBase):
    """Schema for creating a new vibe anchor."""
    pass


class VibeAnchorResponse(VibeAnchorBase):
    """Schema for vibe anchor response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    vibe: VibeMetrics
    genesis: datetime
    last_pulse: datetime
    checkin_count: int
    properties: dict = {}


class AgentCheckinRequest(BaseModel):
    """Schema for agent checkin request."""
    agent_id: str = Field(..., min_length=1, max_length=255)
    location: GeoPoint
    accuracy_meters: Optional[float] = Field(None, ge=0)
    
    # Sensory readings
    social_reading: Optional[float] = Field(None, ge=0, le=1)
    creative_reading: Optional[float] = Field(None, ge=0, le=1)
    commercial_reading: Optional[float] = Field(None, ge=0, le=1)
    residential_reading: Optional[float] = Field(None, ge=0, le=1)
    
    # Context
    activity_type: Optional[str] = Field(None, max_length=50)
    sensory_payload: dict = {}


class AgentCheckinResponse(BaseModel):
    """Schema for agent checkin response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    agent_id: str
    location: GeoPoint
    timestamp: datetime
    nearest_anchor: Optional[VibeAnchorResponse] = None
    local_vibe: Optional[VibeMetrics] = None


class VibePulseRequest(BaseModel):
    """Schema for vibe pulse query."""
    location: GeoPoint
    radius_meters: float = Field(500, ge=10, le=10000)
    include_history: bool = False
    history_hours: int = Field(24, ge=1, le=168)


class VibePulseResponse(BaseModel):
    """Schema for vibe pulse response."""
    location: GeoPoint
    radius_meters: float
    timestamp: datetime
    
    # Aggregated vibe
    vibe: VibeMetrics
    confidence: float = Field(..., ge=0, le=1, description="Confidence in reading based on data density")
    
    # Contributing data
    anchors_in_range: List[VibeAnchorResponse]
    recent_checkins: int
    unique_agents: int
    
    # Historical trend (if requested)
    vibe_trend: Optional[List[dict]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    genesis_anchor_active: bool
    total_anchors: int
    total_checkins: int
