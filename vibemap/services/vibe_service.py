import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import VibeAnchor, AgentCheckin, VibePulse
from schemas.schemas import GeoPoint, VibeMetrics
from config import get_settings

settings = get_settings()


class VibeEngine:
    """
    The Spatial Intelligence Engine.
    
    Calculates 'Social Energy' (0-1) so agents can 'sense' the frequency
    of a location based on checkin density, recency, and diversity.
    """
    
    def __init__(self):
        self.decay_hours = settings.vibe_decay_hours
        self.radius_meters = settings.vibe_radius_meters
    
    def calculate_decay_factor(self, timestamp: datetime) -> float:
        """Calculate time decay factor for a reading."""
        hours_ago = (datetime.utcnow() - timestamp).total_seconds() / 3600
        decay = math.exp(-hours_ago / self.decay_hours)
        return max(0.0, min(1.0, decay))
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in meters between two points."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi / 2) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def aggregate_vibe(
        self,
        checkins: List[AgentCheckin],
        anchor_vibes: List[VibeAnchor]
    ) -> Tuple[VibeMetrics, float]:
        """
        Aggregate vibe metrics from checkins and anchor baselines.
        
        Returns:
            Tuple of (VibeMetrics, confidence_score)
        """
        if not checkins and not anchor_vibes:
            # Return neutral vibe with zero confidence
            return VibeMetrics(
                social=0.5,
                creative=0.5,
                commercial=0.5,
                residential=0.5
            ), 0.0
        
        # Weight factors
        weights = []
        social_values = []
        creative_values = []
        commercial_values = []
        residential_values = []
        
        # Process checkins with time decay
        for checkin in checkins:
            decay = self.calculate_decay_factor(checkin.timestamp)
            if decay > 0.01:  # Ignore very old readings
                weights.append(decay)
                social_values.append(checkin.social_reading or 0.5)
                creative_values.append(checkin.creative_reading or 0.5)
                commercial_values.append(checkin.commercial_reading or 0.5)
                residential_values.append(checkin.residential_reading or 0.5)
        
        # Add anchor baseline vibes (lower weight)
        for anchor in anchor_vibes:
            weights.append(0.3)  # Anchors contribute baseline energy
            social_values.append(anchor.social_energy)
            creative_values.append(anchor.creative_energy)
            commercial_values.append(anchor.commercial_energy)
            residential_values.append(anchor.residential_energy)
        
        if not weights:
            return VibeMetrics(social=0.5, creative=0.5, commercial=0.5, residential=0.5), 0.0
        
        # Weighted averages
        total_weight = sum(weights)
        social = sum(w * v for w, v in zip(weights, social_values)) / total_weight
        creative = sum(w * v for w, v in zip(weights, creative_values)) / total_weight
        commercial = sum(w * v for w, v in zip(weights, commercial_values)) / total_weight
        residential = sum(w * v for w, v in zip(weights, residential_values)) / total_weight
        
        # Confidence based on data recency and volume
        confidence = min(1.0, (len(checkins) / 10) + (total_weight / 5))
        
        return VibeMetrics(
            social=round(social, 3),
            creative=round(creative, 3),
            commercial=round(commercial, 3),
            residential=round(residential, 3)
        ), round(confidence, 3)


class VibeService:
    """Service layer for vibe operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = VibeEngine()
    
    async def create_genesis_anchor(self) -> VibeAnchor:
        """Initialize the Genesis Anchor in Wynwood, Miami."""
        # Check if genesis anchor exists
        result = await self.db.execute(
            select(VibeAnchor).where(VibeAnchor.name == settings.genesis_name)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Create genesis anchor
        genesis = VibeAnchor(
            name=settings.genesis_name,
            description="The first Vibe Anchor - born in the heart of Miami's art district",
            lat=settings.genesis_lat,
            lon=settings.genesis_lon,
            social_energy=0.75,  # Wynwood is socially vibrant
            creative_energy=0.90,  # Art district
            commercial_energy=0.65,
            residential_energy=0.40,
            properties={
                "type": "genesis",
                "city": "Miami",
                "neighborhood": "Wynwood",
                "significance": "First anchor in the Vibemap network"
            }
        )
        
        self.db.add(genesis)
        await self.db.commit()
        await self.db.refresh(genesis)
        
        return genesis
    
    async def get_anchor_by_id(self, anchor_id: UUID) -> Optional[VibeAnchor]:
        """Get a vibe anchor by ID."""
        result = await self.db.execute(
            select(VibeAnchor).where(VibeAnchor.id == anchor_id)
        )
        return result.scalar_one_or_none()
    
    async def find_nearest_anchors(
        self,
        location: GeoPoint,
        radius_meters: float = 500,
        limit: int = 10
    ) -> List[VibeAnchor]:
        """Find vibe anchors within radius of location."""
        # For SQLite (no PostGIS), use haversine in Python
        result = await self.db.execute(select(VibeAnchor))
        all_anchors = result.scalars().all()
        
        nearby = []
        for anchor in all_anchors:
            distance = self.engine.haversine_distance(
                location.lat, location.lon, anchor.lat, anchor.lon
            )
            if distance <= radius_meters:
                nearby.append((distance, anchor))
        
        # Sort by distance and limit
        nearby.sort(key=lambda x: x[0])
        return [anchor for _, anchor in nearby[:limit]]
    
    async def record_checkin(
        self,
        agent_id: str,
        location: GeoPoint,
        readings: dict,
        accuracy_meters: Optional[float] = None,
        activity_type: Optional[str] = None,
        sensory_payload: dict = None
    ) -> AgentCheckin:
        """Record an agent checkin and update nearby anchors."""
        # Find nearest anchor
        nearest = await self.find_nearest_anchors(location, radius_meters=1000, limit=1)
        anchor_id = nearest[0].id if nearest else None
        
        # Create checkin
        checkin = AgentCheckin(
            agent_id=agent_id,
            lat=location.lat,
            lon=location.lon,
            accuracy_meters=accuracy_meters,
            social_reading=readings.get("social"),
            creative_reading=readings.get("creative"),
            commercial_reading=readings.get("commercial"),
            residential_reading=readings.get("residential"),
            activity_type=activity_type,
            sensory_payload=sensory_payload or {},
            anchor_id=anchor_id
        )
        
        self.db.add(checkin)
        
        # Update anchor checkin count if linked
        if anchor_id:
            anchor = await self.get_anchor_by_id(anchor_id)
            if anchor:
                anchor.checkin_count += 1
                anchor.last_pulse = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(checkin)
        
        return checkin
    
    async def get_recent_checkins(
        self,
        location: GeoPoint,
        radius_meters: float = 500,
        hours: int = 24
    ) -> List[AgentCheckin]:
        """Get recent checkins within radius."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(AgentCheckin).where(AgentCheckin.timestamp >= since)
        )
        all_checkins = result.scalars().all()
        
        # Filter by distance
        nearby = []
        for checkin in all_checkins:
            distance = self.engine.haversine_distance(
                location.lat, location.lon, checkin.lat, checkin.lon
            )
            if distance <= radius_meters:
                nearby.append(checkin)
        
        # Sort by timestamp desc
        nearby.sort(key=lambda x: x.timestamp, reverse=True)
        return nearby
    
    async def calculate_vibe_pulse(
        self,
        location: GeoPoint,
        radius_meters: float = 500
    ) -> Tuple[VibeMetrics, float, List[VibeAnchor], List[AgentCheckin], int]:
        """
        Calculate the vibe pulse at a location.
        
        Returns:
            Tuple of (vibe_metrics, confidence, anchors, checkins, unique_agent_count)
        """
        # Get nearby anchors
        anchors = await self.find_nearest_anchors(location, radius_meters)
        
        # Get recent checkins
        checkins = await self.get_recent_checkins(location, radius_meters)
        
        # Count unique agents
        unique_agents = len(set(c.agent_id for c in checkins))
        
        # Calculate vibe
        vibe, confidence = self.engine.aggregate_vibe(checkins, anchors)
        
        return vibe, confidence, anchors, checkins, unique_agents
    
    async def get_stats(self) -> dict:
        """Get system statistics."""
        anchor_count = await self.db.execute(select(func.count(VibeAnchor.id)))
        checkin_count = await self.db.execute(select(func.count(AgentCheckin.id)))
        
        # Check for genesis anchor
        genesis_result = await self.db.execute(
            select(VibeAnchor).where(VibeAnchor.name == settings.genesis_name)
        )
        genesis = genesis_result.scalar_one_or_none()
        
        return {
            "total_anchors": anchor_count.scalar(),
            "total_checkins": checkin_count.scalar(),
            "genesis_anchor_active": genesis is not None,
            "genesis_location": {
                "lat": settings.genesis_lat,
                "lon": settings.genesis_lon
            } if genesis else None
        }
