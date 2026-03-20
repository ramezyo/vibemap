"""
Venue Pulse Service
Real-time venue busyness and activity from Google Places API
"""

import os
import httpx
from typing import Optional, List, Dict
from datetime import datetime
from aiocache import cached
from config import get_settings

settings = get_settings()

# Google Places API (New) - requires API key with Places API enabled
# Get from: https://console.cloud.google.com/apis/library/places-backend.googleapis.com
GOOGLE_PLACES_API_KEY = settings.google_places_api_key or os.getenv("GOOGLE_PLACES_API_KEY", "")
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1"

# Venue types we care about for vibe calculation
VENUE_TYPES = [
    "restaurant",
    "cafe",
    "bar",
    "night_club",
    "art_gallery",
    "museum",
    "shopping_mall",
    "park",
    "tourist_attraction"
]


class VenuePulseService:
    """
    Real-time venue activity monitoring via Google Places API.
    
    Tracks live busyness, popularity, and activity at venues
    to modulate commercial and social energy.
    """
    
    def __init__(self):
        self.api_key = GOOGLE_PLACES_API_KEY
        self.client = httpx.AsyncClient(timeout=15.0)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Google Places API headers."""
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key
        }
        return headers
    
    @cached(ttl=300)  # Cache for 5 minutes
    async def search_nearby_venues(
        self,
        lat: float,
        lon: float,
        radius: int = 500,
        venue_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for venues near a location.
        
        Returns list of venues with current busyness data.
        """
        if not self.api_key:
            # Return simulated venues if no API key
            return self._simulate_venues(lat, lon, venue_type)
        
        try:
            # Use Google Places API (New) - Nearby Search
            field_mask = "places.id,places.displayName,places.location,places.currentOpeningHours,places.businessStatus,places.priceLevel,places.rating,places.userRatingCount"
            
            response = await self.client.post(
                f"{GOOGLE_PLACES_BASE_URL}/places:searchNearby",
                headers={
                    **self._get_headers(),
                    "X-Goog-FieldMask": field_mask
                },
                json={
                    "locationRestriction": {
                        "circle": {
                            "center": {
                                "latitude": lat,
                                "longitude": lon
                            },
                            "radius": radius
                        }
                    },
                    "includedTypes": [venue_type] if venue_type else VENUE_TYPES,
                    "maxResultCount": 20
                }
            )
            response.raise_for_status()
            data = response.json()
            
            venues = []
            for place in data.get("places", []):
                venue = self._parse_place(place)
                if venue:
                    venues.append(venue)
            
            return venues
            
        except Exception as e:
            print(f"⚠️ Google Places API error: {e}")
            return self._simulate_venues(lat, lon, venue_type)
    
    def _parse_place(self, place: Dict) -> Optional[Dict]:
        """Parse Google Place into our venue format."""
        try:
            location = place.get("location", {})
            
            # Check if currently open
            hours = place.get("currentOpeningHours", {})
            is_open = hours.get("openNow", False)
            
            # Calculate busyness (simulated if not available)
            # Google doesn't expose live busyness in the new API without
            # specific place details call, so we estimate from rating/reviews
            rating = place.get("rating", 3.0)
            review_count = place.get("userRatingCount", 0)
            
            # Estimate busyness: high rating + many reviews = likely busy
            busyness_score = min(1.0, (rating / 5.0) * 0.5 + min(review_count / 1000, 0.5))
            
            # Adjust for open status
            if not is_open:
                busyness_score *= 0.1
            
            return {
                "id": place.get("id"),
                "name": place.get("displayName", {}).get("text", "Unknown"),
                "lat": location.get("latitude"),
                "lon": location.get("longitude"),
                "type": place.get("primaryType", "establishment"),
                "rating": rating,
                "review_count": review_count,
                "is_open": is_open,
                "busyness_score": round(busyness_score, 3),
                "price_level": place.get("priceLevel", "PRICE_LEVEL_UNSPECIFIED"),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "google_places"
            }
        except Exception as e:
            print(f"Error parsing place: {e}")
            return None
    
    def _simulate_venues(self, lat: float, lon: float, venue_type: Optional[str]) -> List[Dict]:
        """Simulate venue data based on location."""
        import random
        
        # Determine location context
        if 25.0 < lat < 26.0 and -81.0 < lon < -80.0:
            location_name = "Wynwood"
            venue_names = [
                ("Panther Coffee", "cafe"),
                ("Wynwood Walls", "art_gallery"),
                ("Coyo Taco", "restaurant"),
                ("Shots Miami", "bar"),
                ("The LAB Miami", "cafe"),
                ("Joey's Italian", "restaurant"),
                ("Gramps", "bar"),
                ("Wynwood Kitchen", "restaurant")
            ]
        elif 37.0 < lat < 38.0 and 126.0 < lon < 128.0:
            location_name = "Seoul"
            venue_names = [
                ("Myeongdong Kyoja", "restaurant"),
                ("Line Friends Store", "shopping_mall"),
                ("Starfield Library", "tourist_attraction"),
                ("Common Ground", "shopping_mall"),
                ("BHC Chicken", "restaurant"),
                ("Cafe Onion", "cafe"),
                ("Hongdae Playground", "park"),
                ("Gangnam Underground", "shopping_mall")
            ]
        else:
            location_name = "Unknown"
            venue_names = [
                ("Local Cafe", "cafe"),
                ("Downtown Bistro", "restaurant"),
                ("City Park", "park"),
                ("Main Street Bar", "bar")
            ]
        
        venues = []
        hour = datetime.utcnow().hour
        
        # Business varies by time of day
        if 11 <= hour <= 14 or 18 <= hour <= 22:  # Lunch/Dinner rush
            base_busyness = 0.7
        elif 6 <= hour <= 23:  # Daytime
            base_busyness = 0.5
        else:  # Late night
            base_busyness = 0.2
        
        for i, (name, vtype) in enumerate(venue_names):
            if venue_type and vtype != venue_type:
                continue
                
            # Add some variance
            busyness = min(1.0, max(0.0, base_busyness + random.uniform(-0.2, 0.2)))
            
            venues.append({
                "id": f"sim-{location_name.lower()}-{i}",
                "name": name,
                "lat": lat + random.uniform(-0.002, 0.002),
                "lon": lon + random.uniform(-0.002, 0.002),
                "type": vtype,
                "rating": round(random.uniform(3.5, 4.8), 1),
                "review_count": random.randint(100, 5000),
                "is_open": 6 <= hour <= 23 or vtype in ["bar", "night_club"],
                "busyness_score": round(busyness, 3),
                "price_level": random.choice(["PRICE_LEVEL_INEXPENSIVE", "PRICE_LEVEL_MODERATE", "PRICE_LEVEL_EXPENSIVE"]),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "simulated",
                "note": "Set GOOGLE_PLACES_API_KEY for real data"
            })
        
        return venues
    
    def calculate_vibe_modifiers(self, venues: List[Dict]) -> Dict[str, float]:
        """
        Calculate vibe energy modifiers based on venue activity.
        
        Returns multipliers for each vibe dimension.
        """
        if not venues:
            return {"social": 1.0, "creative": 1.0, "commercial": 1.0, "residential": 1.0}
        
        # Calculate average busyness
        avg_busyness = sum(v.get("busyness_score", 0) for v in venues) / len(venues)
        
        # Count open venues
        open_count = sum(1 for v in venues if v.get("is_open", False))
        open_ratio = open_count / len(venues) if venues else 0
        
        # Count venue types
        type_counts = {}
        for v in venues:
            vtype = v.get("type", "other")
            type_counts[vtype] = type_counts.get(vtype, 0) + 1
        
        # Base modifiers
        modifiers = {
            "social": 1.0,
            "creative": 1.0,
            "commercial": 1.0,
            "residential": 1.0
        }
        
        # Commercial energy from overall busyness
        modifiers["commercial"] += (avg_busyness - 0.5) * 0.3
        
        # Social energy from restaurants/bars
        food_venues = type_counts.get("restaurant", 0) + type_counts.get("bar", 0) + type_counts.get("cafe", 0)
        if food_venues > 0:
            modifiers["social"] += min(0.2, food_venues * 0.05)
        
        # Creative energy from galleries/museums
        creative_venues = type_counts.get("art_gallery", 0) + type_counts.get("museum", 0)
        if creative_venues > 0:
            modifiers["creative"] += min(0.2, creative_venues * 0.1)
        
        # Residential decreases with high commercial activity
        if avg_busyness > 0.7:
            modifiers["residential"] -= 0.15
        
        # Late night venues affect residential
        night_venues = type_counts.get("bar", 0) + type_counts.get("night_club", 0)
        if night_venues > 2:
            modifiers["residential"] -= 0.1
        
        # Ensure bounds
        for key in modifiers:
            modifiers[key] = max(0.5, min(1.5, modifiers[key]))
        
        return modifiers
    
    def get_venue_observation(self, venues: List[Dict], persona: str) -> str:
        """
        Get venue-based observation for an agent persona.
        """
        if not venues:
            return "Quiet streets today"
        
        # Find busiest venue
        busiest = max(venues, key=lambda v: v.get("busyness_score", 0))
        venue_name = busiest.get("name", "somewhere")
        venue_type = busiest.get("type", "place")
        
        # Find open food venues
        food_venues = [v for v in venues if v.get("is_open") and v.get("type") in ["restaurant", "cafe"]]
        
        observations = {
            "Street Artist": [
                f"Crowds gathering near {venue_name} for inspiration",
                "The foot traffic today is perfect for people-watching",
                f"The energy around {venue_name} is electric"
            ],
            "Tech Hustler": [
                f"{venue_name} is packed, great for networking",
                "Every cafe has laptops and entrepreneurs",
                f"The crowd at {venue_name} looks like potential clients"
            ],
            "Zen Seeker": [
                "Finding quiet spots away from the busy venues",
                f"Avoiding {venue_name}, too crowded for my taste",
                "The side streets are peaceful despite the main areas"
            ],
            "Night Owl": [
                f"{venue_name} is where the night begins",
                "The bars are filling up nicely",
                f"Good crowd building at {venue_name}"
            ],
            "Flâneur": [
                f"Observing the dance of people at {venue_name}",
                "Every venue tells a different story today",
                f"The atmosphere at {venue_name} is fascinating"
            ],
            "Foodie": [
                f"{venue_name} has a line out the door",
                f"Tried a new spot near {venue_name}",
                "The restaurant scene is buzzing today"
            ],
            "Local": [
                f"{venue_name} is busier than usual",
                "The neighborhood rhythm feels different today",
                f"Everyone's talking about {venue_name}"
            ],
            "K-Pop Scout": [
                f"Spotted potential talent near {venue_name}",
                "The shopping district is full of stylish people",
                f"Good people-watching at {venue_name}"
            ],
            "Night-Market Vendor": [
                "Competition is fierce today",
                f"The crowds near {venue_name} are promising",
                "Good sales day so far"
            ],
            "High-Speed Commuter": [
                f"Taking a shortcut past {venue_name}",
                "The main streets are crowded, using back routes",
                f"{venue_name} is causing foot traffic jams"
            ],
            "Esports Strategist": [
                f"PC rooms near {venue_name} are full",
                "Gaming cafes are buzzing with competition",
                f"The energy at {venue_name} is competitive"
            ]
        }
        
        if persona in observations:
            import random
            return random.choice(observations[persona])
        
        return f"Noticing activity around {venue_name}"


# Global venue service instance
_venue_service: Optional[VenuePulseService] = None


def get_venue_service() -> VenuePulseService:
    """Get or create venue service singleton."""
    global _venue_service
    if _venue_service is None:
        _venue_service = VenuePulseService()
    return _venue_service