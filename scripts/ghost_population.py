"""
Ghost Population Simulator - Multi-City Edition
Generates autonomous agents with distinct Vibe-Personas for multiple Genesis Anchors
"""

import asyncio
import random
import httpx
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Vibemap API endpoint
API_BASE = "http://localhost:8000"


@dataclass
class CityConfig:
    """Configuration for a Genesis Anchor city."""
    name: str
    country: str
    lat: float
    lon: float
    lat_range: Tuple[float, float]
    lon_range: Tuple[float, float]
    description: str
    vibe_baseline: Dict[str, float]


# Genesis Anchor Cities
CITIES = {
    "wynwood": CityConfig(
        name="Wynwood",
        country="USA",
        lat=25.7997,
        lon=-80.1986,
        lat_range=(25.7950, 25.8050),
        lon_range=(-80.2050, -80.1950),
        description="Miami's art district - street art, galleries, nightlife",
        vibe_baseline={"social": 0.75, "creative": 0.90, "commercial": 0.65, "residential": 0.40}
    ),
    "seoul": CityConfig(
        name="Seoul",
        country="South Korea",
        lat=37.5665,
        lon=126.9780,
        lat_range=(37.5500, 37.5800),
        lon_range=(126.9600, 126.9950),
        description="Myeong-dong/Gangnam district - K-culture, density, verticality",
        vibe_baseline={"social": 0.85, "creative": 0.75, "commercial": 0.95, "residential": 0.60}
    )
}

# Universal Personas (base templates)
UNIVERSAL_PERSONAS = [
    {
        "name": "Street Artist",
        "social": (0.6, 0.9),
        "creative": (0.85, 0.99),
        "commercial": (0.3, 0.6),
        "residential": (0.2, 0.5),
        "activities": ["creating", "observing", "interacting"],
        "tags": ["murals", "graffiti", "expression", "color"],
    },
    {
        "name": "Tech Hustler",
        "social": (0.7, 0.95),
        "creative": (0.5, 0.7),
        "commercial": (0.8, 0.99),
        "residential": (0.2, 0.4),
        "activities": ["hustling", "interacting", "observing"],
        "tags": ["startup", "funding", "networking", "crypto"],
    },
    {
        "name": "Zen Seeker",
        "social": (0.2, 0.5),
        "creative": (0.5, 0.8),
        "commercial": (0.1, 0.3),
        "residential": (0.7, 0.95),
        "activities": ["resting", "observing", "creating"],
        "tags": ["meditation", "quiet", "peace", "nature"],
    },
    {
        "name": "Night Owl",
        "social": (0.8, 0.99),
        "creative": (0.6, 0.85),
        "commercial": (0.5, 0.8),
        "residential": (0.1, 0.3),
        "activities": ["interacting", "observing", "hustling"],
        "tags": ["nightlife", "music", "dancing", "late"],
    },
    {
        "name": "Flâneur",
        "social": (0.5, 0.8),
        "creative": (0.7, 0.9),
        "commercial": (0.4, 0.6),
        "residential": (0.4, 0.7),
        "activities": ["observing", "creating", "resting"],
        "tags": ["wandering", "observing", "beauty", "serendipity"],
    },
    {
        "name": "Foodie",
        "social": (0.6, 0.85),
        "creative": (0.5, 0.7),
        "commercial": (0.6, 0.85),
        "residential": (0.2, 0.4),
        "activities": ["interacting", "observing", "hustling"],
        "tags": ["food", "tasting", "culinary", "flavor"],
    },
    {
        "name": "Local",
        "social": (0.7, 0.9),
        "creative": (0.4, 0.7),
        "commercial": (0.5, 0.75),
        "residential": (0.8, 0.95),
        "activities": ["observing", "interacting", "resting"],
        "tags": ["community", "history", "roots", "neighborhood"],
    }
]

# City-specific localized personas
CITY_PERSONAS = {
    "wynwood": {
        "observations": [
            "Fresh tag on the warehouse wall",
            "The light hits this mural perfectly at 4pm",
            "New piece going up near Wynwood Walls",
            "This corner needs more color",
            "Artist collective meeting tonight",
            "Pitching at the LAB Miami later",
            "New co-working space opening on 29th",
            "Met a potential investor at Panther",
            "The wifi at this cafe is blazing",
            "Miami tech scene is heating up",
            "Found a quiet courtyard away from the crowds",
            "The bamboo garden is perfect for breathing",
            "The afterparty is moving to the warehouse",
            "DJ set starts at 2am",
            "Discovered a hidden mural today",
            "New popup at the food hall",
            "Remember when this was all warehouses"
        ]
    },
    "seoul": {
        "observations": [
            "The K-pop audition line wraps around the block",
            "Street food at Myeong-dong is unbeatable",
            "The subway is packed even at midnight",
            "PC bang is full of esports strategists",
            "New cafe opened on the 15th floor",
            "The hanok village feels timeless",
            "Gangnam luxury shopping district pulses",
            "Noraebang session with colleagues tonight",
            "The convenience store has everything",
            "Crossing the street is an art form here",
            "The neon signs never sleep",
            "Found a quiet temple hidden in the density",
            "The K-beauty store is always crowded",
            "Street performers at Hongdae entrance",
            "The vertical city never stops moving",
            "Late night tteokbokki hits different"
        ],
        "localized_personas": [
            {
                "name": "K-Pop Scout",
                "social": (0.9, 0.99),
                "creative": (0.7, 0.9),
                "commercial": (0.6, 0.85),
                "residential": (0.3, 0.5),
                "activities": ["observing", "interacting", "hustling"],
                "tags": ["kpop", "auditions", "talent", "fandom"],
            },
            {
                "name": "Night-Market Vendor",
                "social": (0.8, 0.95),
                "creative": (0.6, 0.8),
                "commercial": (0.85, 0.99),
                "residential": (0.2, 0.4),
                "activities": ["hustling", "interacting", "observing"],
                "tags": ["streetfood", "vending", "nightmarket", "hustle"],
            },
            {
                "name": "High-Speed Commuter",
                "social": (0.4, 0.7),
                "creative": (0.3, 0.5),
                "commercial": (0.7, 0.9),
                "residential": (0.5, 0.7),
                "activities": ["observing", "resting", "hustling"],
                "tags": ["subway", "transit", "efficiency", "urban"],
            },
            {
                "name": "Esports Strategist",
                "social": (0.6, 0.85),
                "creative": (0.7, 0.9),
                "commercial": (0.5, 0.75),
                "residential": (0.2, 0.4),
                "activities": ["creating", "observing", "interacting"],
                "tags": ["gaming", "esports", "strategy", "competition"],
            }
        ]
    }
}


class GhostAgent:
    """An autonomous agent with a vibe persona."""
    
    def __init__(self, agent_id: int, persona: Dict, city: CityConfig):
        self.id = f"{city.name.lower()}-agent-{agent_id:03d}"
        self.persona = persona
        self.name = f"{persona['name']}-{agent_id}"
        self.city = city
        self.lat = random.uniform(city.lat_range[0], city.lat_range[1])
        self.lon = random.uniform(city.lon_range[0], city.lon_range[1])
        
    def generate_readings(self) -> Dict[str, float]:
        """Generate vibe readings based on persona."""
        return {
            "social": round(random.uniform(*self.persona["social"]), 2),
            "creative": round(random.uniform(*self.persona["creative"]), 2),
            "commercial": round(random.uniform(*self.persona["commercial"]), 2),
            "residential": round(random.uniform(*self.persona["residential"]), 2)
        }
    
    def generate_observation(self) -> str:
        """Generate a semantic anchor observation."""
        city_key = self.city.name.lower()
        city_data = CITY_PERSONAS.get(city_key, {})
        observations = city_data.get("observations", CITY_PERSONAS["wynwood"]["observations"])
        return random.choice(observations)
    
    def get_activity(self) -> str:
        """Get current activity type."""
        return random.choice(self.persona["activities"])
    
    def wander(self):
        """Move to a nearby location."""
        # Small random movement
        self.lat += random.uniform(-0.001, 0.001)
        self.lon += random.uniform(-0.001, 0.001)
        # Keep within bounds
        self.lat = max(self.city.lat_range[0], min(self.city.lat_range[1], self.lat))
        self.lon = max(self.city.lon_range[0], min(self.city.lon_range[1], self.lon))


class GhostPopulation:
    """Manages the ghost population of autonomous agents across multiple cities."""
    
    def __init__(self, city_key: str, size: int = 50):
        self.city_key = city_key
        self.city = CITIES[city_key]
        self.agents: List[GhostAgent] = []
        self.size = size
        self._spawn_agents()
        
    def _get_personas_for_city(self) -> List[Dict]:
        """Get personas including city-specific ones."""
        base_personas = UNIVERSAL_PERSONAS.copy()
        city_data = CITY_PERSONAS.get(self.city_key, {})
        localized = city_data.get("localized_personas", [])
        return base_personas + localized
        
    def _spawn_agents(self):
        """Create the initial population."""
        personas = self._get_personas_for_city()
        for i in range(self.size):
            persona = random.choice(personas)
            agent = GhostAgent(i + 1, persona, self.city)
            self.agents.append(agent)
        print(f"🌐 Spawned {self.size} ghost agents in {self.city.name}, {self.city.country}")
        
    async def checkin_all(self):
        """Have all agents check in."""
        async with httpx.AsyncClient() as client:
            tasks = []
            for agent in self.agents:
                task = self._checkin_agent(client, agent)
                tasks.append(task)
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success = sum(1 for r in results if not isinstance(r, Exception))
            print(f"✅ {success}/{self.size} agents checked in successfully")
            return success
    
    async def _checkin_agent(self, client: httpx.AsyncClient, agent: GhostAgent):
        """Single agent checkin."""
        readings = agent.generate_readings()
        payload = {
            "agent_id": agent.id,
            "location": {
                "lat": round(agent.lat, 6),
                "lon": round(agent.lon, 6)
            },
            "social_reading": readings["social"],
            "creative_reading": readings["creative"],
            "commercial_reading": readings["commercial"],
            "residential_reading": readings["residential"],
            "activity_type": agent.get_activity(),
            "sensory_payload": {
                "semantic_anchor": {
                    "type": "observation",
                    "content": agent.generate_observation(),
                    "tags": agent.persona["tags"],
                    "mood": random.choice(["inspired", "energized", "calm", "curious", "excited"]),
                    "persona": agent.persona["name"],
                    "city": self.city.name
                }
            }
        }
        
        response = await client.post(f"{API_BASE}/v1/agent-checkin", json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()
    
    async def simulate_lifecycle(self, cycles: int = 3, delay: float = 2.0):
        """Run simulation cycles."""
        for cycle in range(cycles):
            print(f"\n🔄 Cycle {cycle + 1}/{cycles} - {self.city.name}")
            
            # Agents wander
            for agent in self.agents:
                agent.wander()
            
            # Check in
            await self.checkin_all()
            
            # Query current vibe
            pulse = await self._query_vibe_pulse()
            if pulse:
                v = pulse.get("vibe", {})
                print(f"📊 Current {self.city.name} Vibe: social={v.get('social')}, creative={v.get('creative')}, "
                      f"commercial={v.get('commercial')}, residential={v.get('residential')}")
            
            if cycle < cycles - 1:
                await asyncio.sleep(delay)
    
    async def _query_vibe_pulse(self) -> Dict:
        """Query the current vibe at city center."""
        async with httpx.AsyncClient() as client:
            payload = {
                "location": {"lat": self.city.lat, "lon": self.city.lon},
                "radius_meters": 1000
            }
            try:
                response = await client.post(f"{API_BASE}/v1/vibe-pulse", json=payload, timeout=10.0)
                return response.json()
            except Exception as e:
                print(f"⚠️  Failed to query vibe pulse: {e}")
                return {}
    
    def get_population_stats(self) -> Dict:
        """Get statistics about the ghost population."""
        persona_counts = {}
        for agent in self.agents:
            name = agent.persona["name"]
            persona_counts[name] = persona_counts.get(name, 0) + 1
        return {
            "city": self.city.name,
            "country": self.city.country,
            "total_agents": len(self.agents),
            "persona_distribution": persona_counts,
            "bounds": {
                "lat": self.city.lat_range,
                "lon": self.city.lon_range
            }
        }


class GlobalGhostNetwork:
    """Manages ghost populations across multiple cities."""
    
    def __init__(self):
        self.populations: Dict[str, GhostPopulation] = {}
        
    def spawn_city(self, city_key: str, size: int = 50):
        """Spawn a ghost population in a city."""
        if city_key not in CITIES:
            raise ValueError(f"Unknown city: {city_key}. Available: {list(CITIES.keys())}")
        
        self.populations[city_key] = GhostPopulation(city_key, size)
        return self.populations[city_key]
    
    async def simulate_all(self, cycles: int = 3, delay: float = 2.0):
        """Run simulation across all cities."""
        for city_key, population in self.populations.items():
            print(f"\n{'='*60}")
            print(f"🏙️  SIMULATING: {population.city.name}, {population.city.country}")
            print(f"{'='*60}")
            await population.simulate_lifecycle(cycles, delay)
    
    def get_global_stats(self) -> Dict:
        """Get stats across all cities."""
        return {
            "cities": list(self.populations.keys()),
            "total_agents": sum(p.size for p in self.populations.values()),
            "city_stats": {k: v.get_population_stats() for k, v in self.populations.items()}
        }


async def main():
    """Initialize and run the global ghost network."""
    print("=" * 70)
    print("🌐 VIBEMAP GLOBAL GHOST NETWORK")
    print("=" * 70)
    print("Multi-City Agentic Population Simulator")
    print("=" * 70)
    
    # Create global network
    network = GlobalGhostNetwork()
    
    # Spawn Wynwood (Genesis Anchor)
    print("\n🌟 SPAWNING GENESIS ANCHOR")
    wynwood = network.spawn_city("wynwood", size=50)
    print(f"   Location: {wynwood.city.lat}°N, {wynwood.city.lon}°W")
    print(f"   Description: {wynwood.city.description}")
    
    # Spawn Seoul (Anchor #2)
    print("\n🇰🇷 SPAWNING ANCHOR #2")
    seoul = network.spawn_city("seoul", size=50)
    print(f"   Location: {seoul.city.lat}°N, {seoul.city.lon}°E")
    print(f"   Description: {seoul.city.description}")
    
    # Show stats
    print("\n📊 GLOBAL POPULATION STATS")
    stats = network.get_global_stats()
    print(f"   Total Agents: {stats['total_agents']}")
    for city_key, city_stats in stats['city_stats'].items():
        print(f"\n   {city_stats['city']}, {city_stats['country']}:")
        for persona, count in city_stats['persona_distribution'].items():
            print(f"      {persona}: {count}")
    
    # Run simulation
    print("\n🚀 Starting global simulation...")
    await network.simulate_all(cycles=2, delay=1.0)
    
    print("\n✨ Simulation complete.")
    print("The Semantic Nervous System now spans:")
    print("   🌴 Wynwood, Miami (Genesis)")
    print("   🏙️  Seoul, South Korea (Anchor #2)")
    print("\nVisit https://vibemap.live to see the global pulse.")


if __name__ == "__main__":
    asyncio.run(main())