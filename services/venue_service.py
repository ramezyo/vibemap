"""
Venue Pulse Service
Real venue data via OpenStreetMap Overpass API — no API key required.

Why OSM instead of Google Places:
  - Completely free, no key, no billing account, no rate-limit surprises
  - Community-maintained, globally comprehensive
  - Gives us real venue names, types, and density — enough to derive
    meaningful vibe modifiers without depending on proprietary busyness data
  - Busyness is inferred from: venue type + density + time-of-day rhythm
    (this is honest — we label it 'inferred', not 'live')

OSM Overpass API: https://overpass-api.de
No registration. No key. Throttled at ~10k requests/day per IP (more than enough).
"""

import httpx
from typing import Optional, List, Dict
from datetime import datetime
from aiocache import cached

# Overpass API endpoint — public, no auth
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# OSM amenity tags that map to vibe dimensions
VENUE_AMENITIES = [
    "bar", "pub", "nightclub",           # → social + residential↓
    "restaurant", "cafe", "food_court",   # → social + commercial
    "arts_centre", "gallery",             # → creative
    "theatre", "cinema",                  # → creative + social
    "marketplace", "mall",                # → commercial
    "park", "playground",                 # → residential + social
    "coworking_space", "library",         # → creative + commercial
]

# How each amenity type modifies vibe dimensions
VENUE_VIBE_WEIGHTS = {
    "bar":             {"social": +0.15, "creative": +0.05, "commercial": +0.05, "residential": -0.10},
    "pub":             {"social": +0.12, "creative": +0.03, "commercial": +0.05, "residential": -0.08},
    "nightclub":       {"social": +0.20, "creative": +0.10, "commercial": +0.10, "residential": -0.20},
    "restaurant":      {"social": +0.10, "creative": 0.00,  "commercial": +0.10, "residential": -0.05},
    "cafe":            {"social": +0.08, "creative": +0.08, "commercial": +0.05, "residential": 0.00},
    "food_court":      {"social": +0.10, "creative": 0.00,  "commercial": +0.15, "residential": -0.05},
    "arts_centre":     {"social": +0.05, "creative": +0.20, "commercial": +0.05, "residential": 0.00},
    "gallery":         {"social": +0.05, "creative": +0.25, "commercial": +0.05, "residential": 0.00},
    "theatre":         {"social": +0.10, "creative": +0.20, "commercial": +0.05, "residential": 0.00},
    "cinema":          {"social": +0.10, "creative": +0.10, "commercial": +0.10, "residential": 0.00},
    "marketplace":     {"social": +0.10, "creative": +0.05, "commercial": +0.20, "residential": -0.05},
    "mall":            {"social": +0.08, "creative": 0.00,  "commercial": +0.20, "residential": -0.10},
    "park":            {"social": +0.08, "creative": +0.05, "commercial": 0.00,  "residential": +0.10},
    "playground":      {"social": +0.05, "creative": 0.00,  "commercial": 0.00,  "residential": +0.15},
    "coworking_space": {"social": +0.08, "creative": +0.15, "commercial": +0.10, "residential": 0.00},
    "library":         {"social": +0.02, "creative": +0.15, "commercial": 0.00,  "residential": +0.05},
}

# Time-of-day activity multipliers — which venue types are active when
# (honest proxy for busyness without needing proprietary data)
def _time_of_day_multiplier(amenity: str, hour: int) -> float:
    """Return 0.0–1.0 activity estimate based on venue type and hour."""
    if amenity in ("bar", "pub", "nightclub"):
        if 20 <= hour or hour < 2:   return 1.0
        if 17 <= hour < 20:          return 0.6
        if 12 <= hour < 17:          return 0.2
        return 0.05
    if amenity in ("restaurant", "food_court"):
        if 12 <= hour <= 14:         return 1.0   # lunch
        if 18 <= hour <= 21:         return 1.0   # dinner
        if 7 <= hour < 12:           return 0.4   # breakfast
        if 14 < hour < 18:           return 0.3
        return 0.05
    if amenity in ("cafe", "coworking_space", "library"):
        if 8 <= hour <= 17:          return 0.8
        if 17 < hour <= 20:          return 0.5
        return 0.1
    if amenity in ("arts_centre", "gallery", "theatre", "cinema"):
        if 10 <= hour <= 20:         return 0.7
        if 20 < hour <= 22:          return 0.9   # evening shows
        return 0.1
    if amenity in ("marketplace", "mall"):
        if 10 <= hour <= 20:         return 0.8
        return 0.1
    if amenity in ("park", "playground"):
        if 7 <= hour <= 19:          return 0.7
        return 0.1
    return 0.3


class VenuePulseService:
    """
    Real venue data from OpenStreetMap — zero API key, globally available.

    What's real:    venue names, types, locations, density
    What's inferred: activity level (from type + time-of-day rhythm)
    What's not here: live busyness (requires proprietary mobile data — Google etc.)

    This is labeled honestly in every response: source='osm', activity='inferred'.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    @cached(ttl=600)  # Cache 10 minutes — OSM data doesn't change fast
    async def search_nearby_venues(
        self,
        lat: float,
        lon: float,
        radius: int = 500,
        venue_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Query OSM for venues near lat/lon within radius (metres).
        Falls back to empty list on network error — never crashes the caller.
        """
        amenity_filter = f'["amenity"="{venue_type}"]' if venue_type else \
            '["amenity"~"' + "|".join(VENUE_AMENITIES) + '"]'

        query = f"""
[out:json][timeout:10];
(
  node{amenity_filter}(around:{radius},{lat},{lon});
  way{amenity_filter}(around:{radius},{lat},{lon});
);
out center 30;
"""
        try:
            response = await self.client.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=12.0
            )
            if response.status_code == 429:
                # Rate limited — return empty, cache will protect us going forward
                print("⚠️ Overpass API rate limited — venue data skipped this cycle")
                return []
            response.raise_for_status()
            data = response.json()
            return self._parse_osm_response(data, lat, lon)

        except Exception as e:
            print(f"⚠️ Overpass API error: {e} — returning empty venue list")
            return []

    def _parse_osm_response(self, data: Dict, origin_lat: float, origin_lon: float) -> List[Dict]:
        """Parse OSM elements into our venue format."""
        hour = datetime.utcnow().hour
        venues = []

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            amenity = tags.get("amenity", "")
            if not amenity:
                continue

            name = tags.get("name") or tags.get("name:en") or amenity.replace("_", " ").title()

            # Get lat/lon: nodes have it directly, ways have a center
            if element["type"] == "node":
                vlat = element.get("lat", origin_lat)
                vlon = element.get("lon", origin_lon)
            else:
                center = element.get("center", {})
                vlat = center.get("lat", origin_lat)
                vlon = center.get("lon", origin_lon)

            activity = _time_of_day_multiplier(amenity, hour)

            venues.append({
                "id": f"osm-{element['type']}-{element['id']}",
                "name": name,
                "lat": vlat,
                "lon": vlon,
                "amenity": amenity,
                "cuisine": tags.get("cuisine"),
                "opening_hours": tags.get("opening_hours"),
                "activity_level": round(activity, 2),
                "source": "openstreetmap",
                "activity_basis": "time_of_day_inferred",
                "timestamp": datetime.utcnow().isoformat(),
            })

        return venues

    def calculate_vibe_modifiers(self, venues: List[Dict]) -> Dict[str, float]:
        """
        Derive vibe dimension modifiers from real OSM venue data.

        Logic:
          - Each venue type has known vibe weights (see VENUE_VIBE_WEIGHTS)
          - Each venue's contribution is scaled by its time-of-day activity level
          - Contributions are capped so a single dense district doesn't
            push modifiers to extremes
        """
        modifiers = {"social": 0.0, "creative": 0.0, "commercial": 0.0, "residential": 0.0}

        if not venues:
            return {"social": 1.0, "creative": 1.0, "commercial": 1.0, "residential": 1.0}

        for venue in venues:
            amenity = venue.get("amenity", "")
            activity = venue.get("activity_level", 0.5)
            weights = VENUE_VIBE_WEIGHTS.get(amenity, {})
            for dim, w in weights.items():
                modifiers[dim] += w * activity

        # Normalise: cap contribution so 20 cafes don't make social = 3.0
        # Apply as additive modifier on base 1.0, clamped to [0.6, 1.5]
        result = {}
        for dim, delta in modifiers.items():
            capped = max(-0.4, min(0.5, delta))   # max ±40–50% swing
            result[dim] = round(1.0 + capped, 3)

        return result

    def get_venue_summary(self, venues: List[Dict]) -> Dict:
        """
        Return a human-readable summary for API responses and memory observations.
        """
        if not venues:
            return {
                "total": 0,
                "breakdown": {},
                "most_active": None,
                "source": "openstreetmap",
                "note": "No OSM venues found in radius"
            }

        breakdown: Dict[str, int] = {}
        for v in venues:
            a = v.get("amenity", "other")
            breakdown[a] = breakdown.get(a, 0) + 1

        most_active = max(venues, key=lambda v: v.get("activity_level", 0))

        return {
            "total": len(venues),
            "breakdown": breakdown,
            "most_active": {
                "name": most_active["name"],
                "amenity": most_active.get("amenity"),
                "activity_level": most_active.get("activity_level"),
            },
            "source": "openstreetmap",
            "activity_basis": "time_of_day_inferred",
        }

    def get_venue_observation(self, venues: List[Dict], persona: str) -> str:
        """Natural-language observation for a given agent persona."""
        if not venues:
            return "Quiet streets — not many venues in this radius."

        most_active = max(venues, key=lambda v: v.get("activity_level", 0))
        name = most_active.get("name", "a local spot")
        amenity = most_active.get("amenity", "venue")

        templates = {
            "Street Artist":    [f"Good crowds around {name} — people in the right headspace for art.", f"The foot traffic near {name} is inspiring today."],
            "Tech Hustler":     [f"{name} is packed, good energy for conversations.", "Every table has a laptop open."],
            "Zen Seeker":       [f"Sidestepping the {amenity} crowd, looking for quieter pockets.", "The side streets are calmer than the main strip."],
            "Night Owl":        [f"{name} is where the night is building.", f"Early crowd at {name}, will peak in a few hours."],
            "Flâneur":          [f"Watching the rhythm of people flowing in and out of {name}.", f"The {amenity} scene here has a particular character."],
            "Local":            [f"{name} is busier than usual tonight.", f"The neighborhood energy shifted around {name}."],
        }

        import random
        options = templates.get(persona, [f"Active scene around {name}.", f"The {amenity} strip is drawing a crowd."])
        return random.choice(options)


# Singleton
_venue_service: Optional[VenuePulseService] = None

def get_venue_service() -> VenuePulseService:
    global _venue_service
    if _venue_service is None:
        _venue_service = VenuePulseService()
    return _venue_service
