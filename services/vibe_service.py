import math
import random
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict
from uuid import UUID
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import VibeAnchor, AgentCheckin, VibePulse
from schemas.schemas import GeoPoint, VibeMetrics
from config import get_settings
from services.weather_service import get_weather_service
from services.sentiment_service import get_sentiment_service

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
    
    def predict_cluster_formation(
        self,
        checkins: List[AgentCheckin],
        location: GeoPoint,
        prediction_hours: int = 4
    ) -> List[Dict]:
        """
        Predict where high-energy social clusters will form.
        
        Analyzes ghost population movement patterns to forecast
        cluster formation locations and intensities.
        
        Returns:
            List of predicted clusters with confidence scores
        """
        if not checkins:
            return []
        
        # Group checkins by persona type
        persona_groups = {}
        for checkin in checkins:
            persona = checkin.activity_type or "Unknown"
            if persona not in persona_groups:
                persona_groups[persona] = []
            persona_groups[persona].append(checkin)
        
        # Calculate movement vectors for each persona group
        clusters = []
        
        for persona, group_checkins in persona_groups.items():
            if len(group_checkins) < 3:
                continue
            
            # Sort by time to find trajectory
            sorted_checkins = sorted(group_checkins, key=lambda x: x.timestamp)
            
            # Calculate weighted center of recent activity
            recent_weight = 0
            weighted_lat = 0
            weighted_lon = 0
            
            for checkin in sorted_checkins[-10:]:  # Last 10 checkins
                decay = self.calculate_decay_factor(checkin.timestamp)
                recent_weight += decay
                weighted_lat += checkin.lat * decay
                weighted_lon += checkin.lon * decay
            
            if recent_weight > 0:
                center_lat = weighted_lat / recent_weight
                center_lon = weighted_lon / recent_weight
                
                # Calculate momentum (direction of movement)
                if len(sorted_checkins) >= 2:
                    recent = sorted_checkins[-1]
                    previous = sorted_checkins[-2]
                    lat_velocity = recent.lat - previous.lat
                    lon_velocity = recent.lon - previous.lon
                    
                    # Predict future location
                    prediction_factor = prediction_hours / 24  # Scale by time
                    predicted_lat = center_lat + (lat_velocity * prediction_factor * 10)
                    predicted_lon = center_lon + (lon_velocity * prediction_factor * 10)
                else:
                    predicted_lat = center_lat
                    predicted_lon = center_lon
                
                # Calculate cluster intensity based on persona concentration
                intensity = min(1.0, len(group_checkins) / 20)
                
                # Calculate confidence based on data quality
                confidence = min(1.0, (len(group_checkins) / 10) * recent_weight)
                
                # Determine cluster type based on persona
                cluster_types = {
                    'Street Artist': 'Creative Hub',
                    'Tech Hustler': 'Innovation Cluster',
                    'Zen Seeker': 'Wellness Zone',
                    'Night Owl': 'Nightlife District',
                    'Flâneur': 'Cultural Corridor',
                    'Foodie': 'Culinary Hotspot',
                    'Local': 'Community Anchor'
                }
                
                clusters.append({
                    "predicted_location": {
                        "lat": round(predicted_lat, 6),
                        "lon": round(predicted_lon, 6)
                    },
                    "cluster_type": cluster_types.get(persona, "Social Node"),
                    "persona_dominant": persona,
                    "predicted_intensity": round(intensity, 3),
                    "confidence": round(confidence, 3),
                    "prediction_horizon_hours": prediction_hours,
                    "agent_count": len(group_checkins),
                    "formation_probability": round(confidence * intensity, 3)
                })
        
        # Sort by formation probability
        clusters.sort(key=lambda x: x["formation_probability"], reverse=True)
        
        return clusters[:5]  # Return top 5 predictions


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
    ) -> Tuple[VibeMetrics, float, List[VibeAnchor], List[AgentCheckin], int, Dict]:
        """
        Calculate the vibe pulse at a location.
        
        Returns:
            Tuple of (vibe_metrics, confidence, anchors, checkins, unique_agent_count, weather_data)
        """
        # Get nearby anchors
        anchors = await self.find_nearest_anchors(location, radius_meters)
        
        # Get recent checkins
        checkins = await self.get_recent_checkins(location, radius_meters)
        
        # Count unique agents
        unique_agents = len(set(c.agent_id for c in checkins))
        
        # Calculate vibe
        vibe, confidence = self.engine.aggregate_vibe(checkins, anchors)
        
        # Get weather and apply modifiers
        weather_service = get_weather_service()
        weather = await weather_service.get_current_weather(location.lat, location.lon)
        weather_modifiers = weather_service.calculate_vibe_modifiers(weather)
        
        # Get sentiment and apply modifiers
        sentiment_service = get_sentiment_service()
        # Determine location key based on coordinates
        if 25.0 < location.lat < 26.0 and -81.0 < location.lon < -80.0:
            location_key = "wynwood"
        elif 37.0 < location.lat < 38.0 and 126.0 < location.lon < 128.0:
            location_key = "seoul"
        else:
            location_key = "miami"
        
        sentiment = await sentiment_service.search_location_sentiment(location_key)
        sentiment_modifiers = sentiment_service.calculate_vibe_modifiers(sentiment)
        
        # Apply combined modifiers to vibe
        vibe.social = round(min(1.0, vibe.social * weather_modifiers["social"] * sentiment_modifiers["social"]), 3)
        vibe.creative = round(min(1.0, vibe.creative * weather_modifiers["creative"] * sentiment_modifiers["creative"]), 3)
        vibe.commercial = round(min(1.0, vibe.commercial * weather_modifiers["commercial"] * sentiment_modifiers["commercial"]), 3)
        vibe.residential = round(min(1.0, vibe.residential * weather_modifiers["residential"] * sentiment_modifiers["residential"]), 3)
        
        return vibe, confidence, anchors, checkins, unique_agents, weather, sentiment
    
    async def predict_clusters(
        self,
        location: GeoPoint,
        radius_meters: float = 2000,
        prediction_hours: int = 4
    ) -> List[Dict]:
        """
        Enterprise endpoint: Predict high-energy social cluster formation.
        
        Analyzes ghost population movements to forecast where clusters
        will form in the next N hours.
        """
        # Get recent checkins in wider area
        checkins = await self.get_recent_checkins(location, radius_meters, hours=48)
        
        # Use prediction engine
        predictions = self.engine.predict_cluster_formation(
            checkins, location, prediction_hours
        )
        
        return predictions
    
    async def export_training_data(
        self,
        location: GeoPoint,
        radius_meters: float = 5000,
        sample_size: int = 1000
    ) -> List[Dict]:
        """
        Export vibe-annotated training data for Large Geospatial Models.
        
        Returns structured dataset suitable for training LGM models.
        """
        since = datetime.utcnow() - timedelta(days=30)
        
        result = await self.db.execute(
            select(AgentCheckin).where(AgentCheckin.timestamp >= since)
        )
        all_checkins = result.scalars().all()
        
        # Filter by location and sample
        nearby_checkins = []
        for checkin in all_checkins:
            distance = self.engine.haversine_distance(
                location.lat, location.lon, checkin.lat, checkin.lon
            )
            if distance <= radius_meters:
                nearby_checkins.append(checkin)
        
        # Sample if too many
        if len(nearby_checkins) > sample_size:
            nearby_checkins = random.sample(nearby_checkins, sample_size)
        
        # Format as training data
        training_data = []
        for checkin in nearby_checkins:
            training_data.append({
                "id": str(checkin.id),
                "timestamp": checkin.timestamp.isoformat(),
                "location": {
                    "lat": checkin.lat,
                    "lon": checkin.lon
                },
                "agent_id": checkin.agent_id,
                "persona": checkin.activity_type,
                "vibe_annotations": {
                    "social": checkin.social_reading,
                    "creative": checkin.creative_reading,
                    "commercial": checkin.commercial_reading,
                    "residential": checkin.residential_reading
                },
                "sensory_payload": checkin.sensory_payload,
                "anchor_id": str(checkin.anchor_id) if checkin.anchor_id else None,
                "dataset_label": "LGM-Wynwood-Alpha-v1"
            })
        
        return training_data
    
    async def create_seoul_anchor(self) -> VibeAnchor:
        """Initialize the Seoul Anchor - Anchor #2 for SWM integration."""
        seoul_name = "Seoul Anchor - Myeong-dong/Gangnam"
        
        # Check if seoul anchor exists
        result = await self.db.execute(
            select(VibeAnchor).where(VibeAnchor.name == seoul_name)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Create seoul anchor
        seoul = VibeAnchor(
            name=seoul_name,
            description="The Seoul World Model integration anchor - high-density K-culture hub",
            lat=37.5665,
            lon=126.9780,
            social_energy=0.85,  # High social density
            creative_energy=0.75,  # K-creative industries
            commercial_energy=0.95,  # Gangnam shopping district
            residential_energy=0.60,
            properties={
                "type": "expansion",
                "city": "Seoul",
                "neighborhood": "Myeong-dong/Gangnam",
                "significance": "Anchor #2 - Seoul World Model integration",
                "swm_compatible": True,
                "focus": "high_density_transit_verticality"
            }
        )
        
        self.db.add(seoul)
        await self.db.commit()
        await self.db.refresh(seoul)
        
        return seoul
    
    async def get_global_pulse(self) -> Dict:
        """Get pulse across all Genesis Anchors."""
        result = await self.db.execute(select(VibeAnchor))
        all_anchors = result.scalars().all()
        
        anchors_data = []
        for anchor in all_anchors:
            anchors_data.append({
                "id": str(anchor.id),
                "name": anchor.name,
                "location": {"lat": anchor.lat, "lon": anchor.lon},
                "vibe": {
                    "social": anchor.social_energy,
                    "creative": anchor.creative_energy,
                    "commercial": anchor.commercial_energy,
                    "residential": anchor.residential_energy
                },
                "checkin_count": anchor.checkin_count,
                "properties": anchor.properties
            })
        
        return {
            "anchors": anchors_data,
            "total_anchors": len(anchors_data),
            "global_bridge_active": len(anchors_data) >= 2
        }
    
    async def get_stats(self) -> dict:
        """Get system statistics."""
        anchor_count = await self.db.execute(select(func.count(VibeAnchor.id)))
        checkin_count = await self.db.execute(select(func.count(AgentCheckin.id)))
        
        # Check for genesis anchor
        genesis_result = await self.db.execute(
            select(VibeAnchor).where(VibeAnchor.name == settings.genesis_name)
        )
        genesis = genesis_result.scalar_one_or_none()
        
        # Check for seoul anchor
        seoul_result = await self.db.execute(
            select(VibeAnchor).where(VibeAnchor.name == "Seoul Anchor - Myeong-dong/Gangnam")
        )
        seoul = seoul_result.scalar_one_or_none()
        
        return {
            "total_anchors": anchor_count.scalar(),
            "total_checkins": checkin_count.scalar(),
            "genesis_anchor_active": genesis is not None,
            "genesis_location": {
                "lat": settings.genesis_lat,
                "lon": settings.genesis_lon
            } if genesis else None,
            "seoul_anchor_active": seoul is not None,
            "seoul_location": {
                "lat": 37.5665,
                "lon": 126.9780
            } if seoul else None,
            "global_network_status": "active" if (genesis and seoul) else "single_anchor"
        }