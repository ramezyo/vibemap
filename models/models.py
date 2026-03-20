import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import TypeDecorator, String as SQLString
from db.database import Base, IS_SQLITE

# Handle JSONB for SQLite vs PostgreSQL
if IS_SQLITE:
    from sqlalchemy import JSON
    JSONType = JSON
    
    # SQLite doesn't have native UUID, use String
    class UUIDType(TypeDecorator):
        impl = SQLString(36)
        
        def process_bind_param(self, value, dialect):
            if value is None:
                return None
            return str(value)
        
        def process_result_value(self, value, dialect):
            if value is None:
                return None
            return uuid.UUID(value)
else:
    JSONType = JSONB
    UUIDType = UUID(as_uuid=True)


class VibeAnchor(Base):
    """A location anchor with persistent social energy."""
    __tablename__ = "vibe_anchors"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Location
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    
    # Vibe metrics (0-1 scale)
    social_energy = Column(Float, default=0.5)
    creative_energy = Column(Float, default=0.5)
    commercial_energy = Column(Float, default=0.5)
    residential_energy = Column(Float, default=0.5)
    
    # Metadata
    genesis = Column(DateTime, default=datetime.utcnow)
    last_pulse = Column(DateTime, default=datetime.utcnow)
    checkin_count = Column(Integer, default=0)
    
    # Properties
    properties = Column(JSONType, default=dict)
    
    def __repr__(self):
        return f"<VibeAnchor {self.name} ({self.lat}, {self.lon}) energy={self.social_energy:.2f}>"


class AgentCheckin(Base):
    """Agent presence and sensory data at a location."""
    __tablename__ = "agent_checkins"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), nullable=False, index=True)
    
    # Location
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    accuracy_meters = Column(Float)
    
    # Sensory data
    social_reading = Column(Float)
    creative_reading = Column(Float)
    commercial_reading = Column(Float)
    residential_reading = Column(Float)
    
    # Context
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    activity_type = Column(String(50))
    
    # Raw sensory payload
    sensory_payload = Column(JSONType, default=dict)
    
    # Link to nearest anchor
    anchor_id = Column(UUIDType, ForeignKey("vibe_anchors.id"), nullable=True)
    
    def __repr__(self):
        return f"<AgentCheckin {self.agent_id} @ ({self.lat}, {self.lon})>"


class VibePulse(Base):
    """Historical vibe readings for temporal analysis."""
    __tablename__ = "vibe_pulses"
    
    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    anchor_id = Column(UUIDType, ForeignKey("vibe_anchors.id"), nullable=False)
    
    # Vibe snapshot
    social_energy = Column(Float)
    creative_energy = Column(Float)
    commercial_energy = Column(Float)
    residential_energy = Column(Float)
    
    # Contributing factors
    checkin_count = Column(Integer)
    unique_agents = Column(Integer)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
