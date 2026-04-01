"""
Vibemap Global Anchor Seed Script
===================================
Seeds the network with a global set of culturally significant anchors.
Run once against the live API to bootstrap the network.

Usage:
    python scripts/seed_anchors.py
    VIBEMAP_API_URL=https://vibemap.live python scripts/seed_anchors.py
"""

import asyncio
import httpx
import os
import sys

API_BASE = os.environ.get("VIBEMAP_API_URL", "https://vibemap.live")

# 10 cities with distinct vibe profiles — chosen for cultural density,
# agent population relevance, and geographic spread
GLOBAL_ANCHORS = [
    {
        "name": "Tokyo Anchor - Shibuya",
        "description": "Hyperkinetic crossroads of youth culture, fashion, and digital life",
        "lat": 35.6598,
        "lon": 139.7006,
        "social_energy": 0.95,
        "creative_energy": 0.88,
        "commercial_energy": 0.98,
        "residential_energy": 0.45,
        "properties": {
            "city": "Tokyo", "country": "Japan",
            "neighborhood": "Shibuya",
            "vibe_signature": "hyperkinetic_youth_commerce",
            "population_density": "extreme",
            "anchor_tier": "global"
        }
    },
    {
        "name": "New York Anchor - Lower East Side",
        "description": "Birthplace of NYC counterculture — art, music, and radical energy",
        "lat": 40.7157,
        "lon": -73.9863,
        "social_energy": 0.88,
        "creative_energy": 0.92,
        "commercial_energy": 0.72,
        "residential_energy": 0.65,
        "properties": {
            "city": "New York", "country": "USA",
            "neighborhood": "Lower East Side",
            "vibe_signature": "creative_resistance_density",
            "population_density": "very_high",
            "anchor_tier": "global"
        }
    },
    {
        "name": "Berlin Anchor - Mitte/Kreuzberg",
        "description": "Post-wall creative explosion — techno, art, and radical openness",
        "lat": 52.4994,
        "lon": 13.4194,
        "social_energy": 0.82,
        "creative_energy": 0.97,
        "commercial_energy": 0.55,
        "residential_energy": 0.70,
        "properties": {
            "city": "Berlin", "country": "Germany",
            "neighborhood": "Kreuzberg",
            "vibe_signature": "radical_creative_freedom",
            "population_density": "high",
            "anchor_tier": "global"
        }
    },
    {
        "name": "San Francisco Anchor - Mission District",
        "description": "Tech meets street art — the collision zone of capital and culture",
        "lat": 37.7599,
        "lon": -122.4148,
        "social_energy": 0.78,
        "creative_energy": 0.85,
        "commercial_energy": 0.80,
        "residential_energy": 0.58,
        "properties": {
            "city": "San Francisco", "country": "USA",
            "neighborhood": "Mission District",
            "vibe_signature": "tech_culture_collision",
            "population_density": "high",
            "anchor_tier": "global"
        }
    },
    {
        "name": "London Anchor - Shoreditch",
        "description": "East London's creative engine — startups, street art, and late nights",
        "lat": 51.5226,
        "lon": -0.0782,
        "social_energy": 0.85,
        "creative_energy": 0.90,
        "commercial_energy": 0.75,
        "residential_energy": 0.52,
        "properties": {
            "city": "London", "country": "UK",
            "neighborhood": "Shoreditch",
            "vibe_signature": "creative_capital_node",
            "population_density": "very_high",
            "anchor_tier": "global"
        }
    },
    {
        "name": "Lagos Anchor - Victoria Island",
        "description": "Africa's most electric city — density, hustle, and unstoppable energy",
        "lat": 6.4281,
        "lon": 3.4219,
        "social_energy": 0.94,
        "creative_energy": 0.82,
        "commercial_energy": 0.89,
        "residential_energy": 0.60,
        "properties": {
            "city": "Lagos", "country": "Nigeria",
            "neighborhood": "Victoria Island",
            "vibe_signature": "maximum_density_hustle",
            "population_density": "extreme",
            "anchor_tier": "global"
        }
    },
    {
        "name": "Buenos Aires Anchor - Palermo",
        "description": "Tango, design, and the art of living — South America's cultural nucleus",
        "lat": -34.5885,
        "lon": -58.4261,
        "social_energy": 0.87,
        "creative_energy": 0.91,
        "commercial_energy": 0.68,
        "residential_energy": 0.72,
        "properties": {
            "city": "Buenos Aires", "country": "Argentina",
            "neighborhood": "Palermo",
            "vibe_signature": "latin_creative_rhythm",
            "population_density": "high",
            "anchor_tier": "global"
        }
    },
    {
        "name": "Singapore Anchor - Kampong Glam",
        "description": "Southeast Asia's bridge city — multicultural density at maximum efficiency",
        "lat": 1.3025,
        "lon": 103.8597,
        "social_energy": 0.83,
        "creative_energy": 0.78,
        "commercial_energy": 0.92,
        "residential_energy": 0.55,
        "properties": {
            "city": "Singapore", "country": "Singapore",
            "neighborhood": "Kampong Glam",
            "vibe_signature": "multicultural_efficiency_hub",
            "population_density": "extreme",
            "anchor_tier": "global"
        }
    },
    {
        "name": "Nairobi Anchor - Westlands",
        "description": "East Africa's tech hub — M-Pesa born here, the future is being built",
        "lat": -1.2631,
        "lon": 36.8027,
        "social_energy": 0.80,
        "creative_energy": 0.76,
        "commercial_energy": 0.84,
        "residential_energy": 0.62,
        "properties": {
            "city": "Nairobi", "country": "Kenya",
            "neighborhood": "Westlands",
            "vibe_signature": "emerging_tech_energy",
            "population_density": "high",
            "anchor_tier": "global"
        }
    },
    {
        "name": "São Paulo Anchor - Vila Madalena",
        "description": "Brazil's creative underground — street art capital of the world",
        "lat": -23.5629,
        "lon": -46.6934,
        "social_energy": 0.89,
        "creative_energy": 0.95,
        "commercial_energy": 0.63,
        "residential_energy": 0.66,
        "properties": {
            "city": "São Paulo", "country": "Brazil",
            "neighborhood": "Vila Madalena",
            "vibe_signature": "street_art_creative_underground",
            "population_density": "very_high",
            "anchor_tier": "global"
        }
    },
]


async def create_anchor(client: httpx.AsyncClient, anchor: dict) -> dict:
    """Create an anchor via POST /v1/anchors."""
    payload = {
        "name": anchor["name"],
        "description": anchor["description"],
        "location": {"lat": anchor["lat"], "lon": anchor["lon"]},
        "social_energy": anchor["social_energy"],
        "creative_energy": anchor["creative_energy"],
        "commercial_energy": anchor["commercial_energy"],
        "residential_energy": anchor["residential_energy"],
        "properties": anchor["properties"]
    }
    r = await client.post(f"{API_BASE}/v1/anchors", json=payload, timeout=15)
    return {"status": r.status_code, "city": anchor["properties"]["city"], "body": r.text[:100]}


async def main():
    print(f"🌐 Seeding Vibemap Global Anchor Network")
    print(f"📡 Target: {API_BASE}")
    print(f"🗺️  Anchors to seed: {len(GLOBAL_ANCHORS)}\n")

    async with httpx.AsyncClient() as client:
        # Health check first
        r = await client.get(f"{API_BASE}/health", timeout=10)
        if r.status_code != 200:
            print(f"❌ API not healthy: {r.status_code}")
            sys.exit(1)
        health = r.json()
        print(f"✅ API healthy — v{health['version']} | existing anchors: {health['total_anchors']}\n")

        # Seed each anchor
        for anchor in GLOBAL_ANCHORS:
            result = await create_anchor(client, anchor)
            status_icon = "✅" if result["status"] == 200 else "❌"
            print(f"{status_icon} {anchor['name']} — HTTP {result['status']}")
            await asyncio.sleep(0.3)  # be gentle on the API

        # Final health check
        print()
        r = await client.get(f"{API_BASE}/health", timeout=10)
        health = r.json()
        print(f"🏁 Done — total checkins: {health['total_checkins']}")

        # Show anchors
        r = await client.get(f"{API_BASE}/v1/anchors", timeout=10)
        anchors = r.json()
        print(f"🗺️  Active anchors in network: {len(anchors)}")
        for a in anchors:
            print(f"   • {a['name']} ({a['checkin_count']} checkins)")


if __name__ == "__main__":
    asyncio.run(main())
