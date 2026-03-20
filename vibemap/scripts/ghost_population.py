"""
Ghost Population Simulator
Generates 50 autonomous agents with distinct Vibe-Personas for Wynwood, Miami
"""

import asyncio
import random
import httpx
from datetime import datetime
from typing import List, Dict

# Vibemap API endpoint
API_BASE = "http://localhost:8000"

# Wynwood bounding box (roughly)
WYNWOOD_BOUNDS = {
    "lat_min": 25.7950,
    "lat_max": 25.8050,
    "lon_min": -80.2050,
    "lon_max": -80.1950
}

# Agent personas with vibe fingerprints
AGENT_PERSONAS = [
    {
        "name": "Street Artist",
        "social": (0.6, 0.9),
        "creative": (0.85, 0.99),
        "commercial": (0.3, 0.6),
        "residential": (0.2, 0.5),
        "activities": ["creating", "observing", "interacting"],
        "tags": ["murals", "graffiti", "expression", "color"],
        "observations": [
            "Fresh tag on the warehouse wall",
            "The light hits this mural perfectly at 4pm",
            "New piece going up near Wynwood Walls",
            "This corner needs more color",
            "Artist collective meeting tonight"
        ]
    },
    {
        "name": "Tech Hustler",
        "social": (0.7, 0.95),
        "creative": (0.5, 0.7),
        "commercial": (0.8, 0.99),
        "residential": (0.2, 0.4),
        "activities": ["hustling", "interacting", "observing"],
        "tags": ["startup", "funding", "networking", "crypto"],
        "observations": [
            "Pitching at the LAB Miami later",
            "New co-working space opening on 29th",
            "Met a potential investor at Panther",
            "The wifi at this cafe is blazing",
            "Miami tech scene is heating up"
        ]
    },
    {
        "name": "Zen Seeker",
        "social": (0.2, 0.5),
        "creative": (0.5, 0.8),
        "commercial": (0.1, 0.3),
        "residential": (0.7, 0.95),
        "activities": ["resting", "observing", "creating"],
        "tags": ["meditation", "quiet", "peace", "nature"],
        "observations": [
            "Found a quiet courtyard away from the crowds",
            "The bamboo garden is perfect for breathing",
            "Morning light through the palms",
            "This spot has good energy",
            "Away from the hustle, finally"
        ]
    },
    {
        "name": "Night Owl",
        "social": (0.8, 0.99),
        "creative": (0.6, 0.85),
        "commercial": (0.5, 0.8),
        "residential": (0.1, 0.3),
        "activities": ["interacting", "observing", "hustling"],
        "tags": ["nightlife", "music", "dancing", "late"],
        "observations": [
            "The afterparty is moving to the warehouse",
            "DJ set starts at 2am",
            "This alley has the best acoustics",
            "Neon lights hit different at midnight",
            "The real vibe starts after dark"
        ]
    },
    {
        "name": "Flâneur",
        "social": (0.5, 0.8),
        "creative": (0.7, 0.9),
        "commercial": (0.4, 0.6),
        "residential": (0.4, 0.7),
        "activities": ["observing", "creating", "resting"],
        "tags": ["wandering", "observing", "beauty", "serendipity"],
        "observations": [
            "Discovered a hidden mural today",
            "The architecture here tells stories",
            "Watching people is an art form",
            "Every corner holds a surprise",
            "Walking without destination"
        ]
    },
    {
        "name": "Foodie",
        "social": (0.6, 0.85),
        "creative": (0.5, 0.7),
        "commercial": (0.6, 0.85),
        "residential": (0.2, 0.4),
        "activities": ["interacting", "observing", "hustling"],
        "tags": ["food", "tasting", "culinary", "flavor"],
        "observations": [
            "New popup at the food hall",
            "Best cuban sandwich in the district",
            "The coffee here is exceptional",
            "Food truck gathering tonight",
            "Chef's tasting menu was transcendent"
        ]
    },
    {
        "name": "Local",
        "social": (0.7, 0.9),
        "creative": (0.4, 0.7),
        "commercial": (0.5, 0.75),
        "residential": (0.8, 0.95),
        "activities": ["observing", "interacting", "resting"],
        "tags": ["community", "history", "roots", "neighborhood"],
        "observations": [
            "Remember when this was all warehouses",
            "The neighborhood is changing fast",
            "Mrs. Rodriguez still runs the bodega",
            "Community meeting next Tuesday",
            "This block has seen it all"
        ]
    }
]


class GhostAgent:
    """An autonomous agent with a vibe persona."""
    
    def __init__(self, agent_id: int, persona: Dict):
        self.id = f"ghost-{agent_id:03d}"
        self.persona = persona
        self.name = f"{persona['name']}-{agent_id}"
        self.lat = random.uniform(WYNWOOD_BOUNDS["lat_min"], WYNWOOD_BOUNDS["lat_max"])
        self.lon = random.uniform(WYNWOOD_BOUNDS["lon_min"], WYNWOOD_BOUNDS["lon_max"])
        
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
        return random.choice(self.persona["observations"])
    
    def get_activity(self) -> str:
        """Get current activity type."""
        return random.choice(self.persona["activities"])
    
    def wander(self):
        """Move to a nearby location."""
        # Small random movement
        self.lat += random.uniform(-0.001, 0.001)
        self.lon += random.uniform(-0.001, 0.001)
        # Keep within bounds
        self.lat = max(WYNWOOD_BOUNDS["lat_min"], min(WYNWOOD_BOUNDS["lat_max"], self.lat))
        self.lon = max(WYNWOOD_BOUNDS["lon_min"], min(WYNWOOD_BOUNDS["lon_max"], self.lon))


class GhostPopulation:
    """Manages the ghost population of autonomous agents."""
    
    def __init__(self, size: int = 50):
        self.agents: List[GhostAgent] = []
        self.size = size
        self._spawn_agents()
        
    def _spawn_agents(self):
        """Create the initial population."""
        for i in range(self.size):
            persona = random.choice(AGENT_PERSONAS)
            agent = GhostAgent(i + 1, persona)
            self.agents.append(agent)
        print(f"🌐 Spawned {self.size} ghost agents in Wynwood")
        
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
        payload = {
            "agent_id": agent.id,
            "location": {
                "lat": round(agent.lat, 6),
                "lon": round(agent.lon, 6)
            },
            "social_reading": agent.generate_readings()["social"],
            "creative_reading": agent.generate_readings()["creative"],
            "commercial_reading": agent.generate_readings()["commercial"],
            "residential_reading": agent.generate_readings()["residential"],
            "activity_type": agent.get_activity(),
            "sensory_payload": {
                "semantic_anchor": {
                    "type": "observation",
                    "content": agent.generate_observation(),
                    "tags": agent.persona["tags"],
                    "mood": random.choice(["inspired", "energized", "calm", "curious", "excited"]),
                    "persona": agent.persona["name"]
                }
            }
        }
        
        response = await client.post(f"{API_BASE}/v1/agent-checkin", json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()
    
    async def simulate_lifecycle(self, cycles: int = 3, delay: float = 2.0):
        """Run simulation cycles."""
        for cycle in range(cycles):
            print(f"\n🔄 Cycle {cycle + 1}/{cycles}")
            
            # Agents wander
            for agent in self.agents:
                agent.wander()
            
            # Check in
            await self.checkin_all()
            
            # Query current vibe
            pulse = await self._query_vibe_pulse()
            if pulse:
                v = pulse.get("vibe", {})
                print(f"📊 Current Wynwood Vibe: social={v.get('social')}, creative={v.get('creative')}, "
                      f"commercial={v.get('commercial')}, residential={v.get('residential')}")
            
            if cycle < cycles - 1:
                await asyncio.sleep(delay)
    
    async def _query_vibe_pulse(self) -> Dict:
        """Query the current vibe at Wynwood center."""
        async with httpx.AsyncClient() as client:
            payload = {
                "location": {"lat": 25.7997, "lon": -80.1986},
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
            "total_agents": len(self.agents),
            "persona_distribution": persona_counts,
            "bounds": WYNWOOD_BOUNDS
        }


async def main():
    """Initialize and run the ghost population."""
    print("=" * 60)
    print("🌐 VIBEMAP GHOST POPULATION SIMULATOR")
    print("=" * 60)
    print(f"Genesis Anchor: Wynwood, Miami (25.7997°N, 80.1986°W)")
    print(f"API Endpoint: {API_BASE}")
    print("=" * 60)
    
    # Create population
    ghosts = GhostPopulation(size=50)
    
    # Show stats
    stats = ghosts.get_population_stats()
    print("\n📊 Population Distribution:")
    for persona, count in stats["persona_distribution"].items():
        print(f"   {persona}: {count}")
    
    # Run simulation
    print("\n🚀 Starting simulation...")
    await ghosts.simulate_lifecycle(cycles=3, delay=1.0)
    
    print("\n✨ Simulation complete. Wynwood is now populated.")
    print("Visit http://localhost:8000 to see the live pulse.")


if __name__ == "__main__":
    asyncio.run(main())
