"""
Real-Time Data Ingestion Layer
Connects Vibemap to live external data sources for authentic vibe calculation
"""

import os
import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta
from aiocache import cached

# OpenWeatherMap API (free tier: 1000 calls/day)
# Get API key from: https://openweathermap.org/api
from config import get_settings

settings = get_settings()
OPENWEATHER_API_KEY = settings.openweather_api_key or os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherService:
    """
    Real-time weather integration for vibe modulation.
    
    Weather affects agent behavior and social energy:
    - Rain → Lower commercial/residential, higher stress
    - Heat → Lower social outdoors, higher indoor activity
    - Clear → Baseline vibes
    """
    
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        self.client = httpx.AsyncClient(timeout=10.0)
    
    @cached(ttl=600)  # Cache weather for 10 minutes
    async def get_current_weather(self, lat: float, lon: float) -> Optional[Dict]:
        """Fetch current weather for location."""
        if not self.api_key:
            # Return simulated weather if no API key
            return self._simulate_weather(lat, lon)
        
        try:
            response = await self.client.get(
                f"{OPENWEATHER_BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "weather_main": data["weather"][0]["main"],
                "weather_description": data["weather"][0]["description"],
                "wind_speed": data["wind"].get("speed", 0),
                "clouds": data["clouds"].get("all", 0),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "openweather"
            }
        except Exception as e:
            print(f"⚠️ Weather API error: {e}")
            return self._simulate_weather(lat, lon)
    
    def _simulate_weather(self, lat: float, lon: float) -> Dict:
        """Simulate weather based on location and time."""
        # Simple simulation based on location
        hour = datetime.utcnow().hour
        
        # Seoul (Korea) - temperate climate
        if 37.0 < lat < 38.0 and 126.0 < lon < 128.0:
            base_temp = 15 if 6 <= hour <= 18 else 8
            weather = "Clear" if random.random() > 0.3 else "Clouds"
        # Miami (USA) - tropical climate
        elif 25.0 < lat < 26.0 and -81.0 < lon < -80.0:
            base_temp = 28 if 6 <= hour <= 18 else 22
            weather = "Clear" if random.random() > 0.4 else "Rain"
        else:
            base_temp = 20
            weather = "Clear"
        
        return {
            "temperature": base_temp + random.uniform(-3, 3),
            "feels_like": base_temp,
            "humidity": random.randint(40, 80),
            "weather_main": weather,
            "weather_description": weather.lower(),
            "wind_speed": random.uniform(0, 10),
            "clouds": random.randint(0, 50),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulated",
            "note": "Set OPENWEATHER_API_KEY for real data"
        }
    
    def calculate_vibe_modifiers(self, weather: Dict) -> Dict[str, float]:
        """
        Calculate vibe energy modifiers based on weather.
        
        Returns multipliers for each vibe dimension.
        """
        weather_main = weather.get("weather_main", "Clear")
        temp = weather.get("temperature", 20)
        
        # Base modifiers (1.0 = no change)
        modifiers = {
            "social": 1.0,
            "creative": 1.0,
            "commercial": 1.0,
            "residential": 1.0
        }
        
        # Rain impact
        if weather_main in ["Rain", "Drizzle", "Thunderstorm"]:
            modifiers["commercial"] -= 0.15  # Less shopping/street activity
            modifiers["social"] -= 0.10      # Less outdoor socializing
            modifiers["residential"] += 0.10 # More staying home
        
        # Heat impact (>30°C)
        if temp > 30:
            modifiers["social"] -= 0.15      # Too hot outdoors
            modifiers["creative"] -= 0.10    # Heat fatigue
            modifiers["commercial"] += 0.05  # AC venues popular
        
        # Cold impact (<5°C)
        if temp < 5:
            modifiers["social"] -= 0.10
            modifiers["commercial"] -= 0.10
            modifiers["residential"] += 0.15
        
        # Clear/sunny boost
        if weather_main == "Clear":
            modifiers["social"] += 0.10
            modifiers["creative"] += 0.10
        
        # Ensure bounds
        for key in modifiers:
            modifiers[key] = max(0.5, min(1.5, modifiers[key]))
        
        return modifiers
    
    def get_agent_observation_modifier(self, weather: Dict, persona: str) -> str:
        """
        Get weather-specific observation for an agent persona.
        """
        weather_main = weather.get("weather_main", "Clear")
        temp = weather.get("temperature", 20)
        
        # Rain observations
        if weather_main in ["Rain", "Drizzle"]:
            rain_obs = {
                "Street Artist": "Painting in the rain, colors bleeding beautifully",
                "Tech Hustler": "Coffee shop is packed due to the rain",
                "Zen Seeker": "Rain on the roof, perfect meditation weather",
                "Night Owl": "Club is drier than the streets tonight",
                "Flâneur": "Umbrella patterns create moving art",
                "Foodie": "Seeking comfort food in this weather",
                "Local": "Rain always brings out the neighborhood solidarity",
                "K-Pop Scout": "Indoor venues packed due to rain",
                "Night-Market Vendor": "Slow night, rain keeping customers away",
                "High-Speed Commuter": "Subway is extra crowded tonight",
                "Esports Strategist": "Perfect weather for indoor gaming"
            }
            return rain_obs.get(persona, "Adjusting plans due to rain")
        
        # Heat observations
        if temp > 30:
            heat_obs = {
                "Street Artist": "Paint drying too fast in this heat",
                "Tech Hustler": "AC cafes are the new boardrooms",
                "Zen Seeker": "Seeking shade and stillness",
                "Night Owl": "Heat means the party starts later",
                "Flâneur": "Moving slowly, observing the heat haze",
                "Foodie": "Cold noodles and iced coffee only",
                "Local": "Summer heat, familiar and oppressive",
                "K-Pop Scout": "Indoor auditions only today",
                "Night-Market Vendor": "Heat keeping some vendors home",
                "High-Speed Commuter": "Subway AC is a lifesaver",
                "Esports Strategist": "Cool PC room beats the heat"
            }
            return heat_obs.get(persona, "Managing in the heat")
        
        # Clear weather
        if weather_main == "Clear":
            clear_obs = {
                "Street Artist": "Perfect light for outdoor work",
                "Tech Hustler": "Beautiful day for walking meetings",
                "Zen Seeker": "Sunlight through the leaves",
                "Night Owl": "Clear skies mean clear minds",
                "Flâneur": "Every corner worth exploring today",
                "Foodie": "Outdoor seating is prime real estate",
                "Local": "Days like this remind me why I live here",
                "K-Pop Scout": "Perfect weather for street performances",
                "Night-Market Vendor": "Great turnout with this weather",
                "High-Speed Commuter": "Walking beats the subway today",
                "Esports Strategist": "Nice day but gaming calls"
            }
            return clear_obs.get(persona, "Enjoying the clear weather")
        
        return "Observing the day's energy"


# Global weather service instance
_weather_service: Optional[WeatherService] = None


def get_weather_service() -> WeatherService:
    """Get or create weather service singleton."""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service


import random