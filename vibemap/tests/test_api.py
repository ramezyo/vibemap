import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from db.database import get_db, Base
from config import get_settings

settings = get_settings()

# Test database URL - use in-memory SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

test_async_session = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Override database dependency for testing."""
    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db():
    """Create tables before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for the health endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns correct structure."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "genesis_anchor_active" in data


class TestVibePulseEndpoint:
    """Tests for the vibe-pulse endpoint."""
    
    def test_vibe_pulse_wynwood(self, client):
        """Test vibe pulse at Genesis Anchor location."""
        payload = {
            "location": {
                "lat": 25.7997,
                "lon": -80.1986
            },
            "radius_meters": 500
        }
        
        response = client.post("/v1/vibe-pulse", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "vibe" in data
        assert "social" in data["vibe"]
        assert "creative" in data["vibe"]
        assert "commercial" in data["vibe"]
        assert "residential" in data["vibe"]
        assert "confidence" in data
        assert "anchors_in_range" in data


class TestAgentCheckinEndpoint:
    """Tests for the agent-checkin endpoint."""
    
    def test_agent_checkin(self, client):
        """Test agent can check in at a location."""
        payload = {
            "agent_id": "test-agent-001",
            "location": {
                "lat": 25.7997,
                "lon": -80.1986
            },
            "social_reading": 0.8,
            "creative_reading": 0.9,
            "activity_type": "observing"
        }
        
        response = client.post("/v1/agent-checkin", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["agent_id"] == "test-agent-001"
        assert "local_vibe" in data
        assert "nearest_anchor" in data


class TestAnchorsEndpoint:
    """Tests for the anchors endpoint."""
    
    def test_list_anchors(self, client):
        """Test listing vibe anchors."""
        response = client.get("/v1/anchors")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Genesis anchor is created during app startup
        # Note: In tests with fresh DB per test, this may be 0 if
        # the genesis anchor creation happens in a different session
        # This test validates the endpoint structure
