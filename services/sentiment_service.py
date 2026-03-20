"""
Real-Time Sentiment Scraper
Monitors X/Twitter for location-based social sentiment
"""

import os
import re
import httpx
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from aiocache import cached

# Twitter/X API v2 (Bearer token required)
# Get from: https://developer.twitter.com/en/portal/dashboard
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_API_BASE = "https://api.twitter.com/2"

# Location keywords for our anchors
LOCATION_KEYWORDS = {
    "wynwood": ["#Wynwood", "Wynwood Miami", "Wynwood Walls", "Wynwood art"],
    "seoul": ["#Seoul", "Gangnam", "Myeongdong", "Hongdae", "Korea travel"],
    "miami": ["#Miami", "Miami art", "Miami nightlife", "Miami events"]
}

# Sentiment keywords (simple lexicon)
POSITIVE_WORDS = [
    "amazing", "awesome", "beautiful", "best", "brilliant", "cool", "excellent",
    "excited", "fantastic", "fun", "good", "great", "happy", "incredible",
    "inspired", "love", "lovely", "nice", "perfect", "vibrant", "wonderful",
    "🔥", "❤️", "😍", "🥰", "😊", "🎉", "✨", "💯", "👏"
]

NEGATIVE_WORDS = [
    "awful", "bad", "boring", "crowded", "disappointing", "hate", "horrible",
    "overrated", "sad", "terrible", "ugly", "worst", "boring", "empty",
    "😢", "😠", "😡", "🤢", "👎", "💔"
]

EVENT_KEYWORDS = {
    "concert": ["concert", "live music", "performance", "gig", "show"],
    "festival": ["festival", "celebration", "event", "party"],
    "art": ["art", "exhibition", "gallery", "mural", "street art"],
    "food": ["food", "restaurant", "cafe", "popup", "dining"],
    "protest": ["protest", "strike", "demonstration", "rally"],
    "accident": ["accident", "crash", "emergency", "closed"]
}


class SentimentService:
    """
    Real-time social sentiment analysis from X/Twitter.
    
    Monitors location-based conversations to modulate social energy scores.
    """
    
    def __init__(self):
        self.bearer_token = TWITTER_BEARER_TOKEN
        self.client = httpx.AsyncClient(timeout=15.0)
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get Twitter API auth headers."""
        if self.bearer_token:
            return {"Authorization": f"Bearer {self.bearer_token}"}
        return {}
    
    @cached(ttl=300)  # Cache for 5 minutes
    async def search_location_sentiment(self, location_key: str, max_results: int = 20) -> Dict:
        """
        Search recent tweets for location-based sentiment.
        
        Returns sentiment analysis and event detection.
        """
        if not self.bearer_token:
            # Return simulated sentiment if no API key
            return self._simulate_sentiment(location_key)
        
        keywords = LOCATION_KEYWORDS.get(location_key, [f"#{location_key}"])
        query = " OR ".join(keywords) + " -is:retweet lang:en"
        
        try:
            response = await self.client.get(
                f"{TWITTER_API_BASE}/tweets/search/recent",
                headers=self._get_auth_headers(),
                params={
                    "query": query,
                    "max_results": min(max_results, 100),
                    "tweet.fields": "created_at,public_metrics,geo"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            tweets = data.get("data", [])
            return self._analyze_tweets(tweets, location_key)
            
        except Exception as e:
            print(f"⚠️ Twitter API error: {e}")
            return self._simulate_sentiment(location_key)
    
    def _analyze_tweets(self, tweets: List[Dict], location_key: str) -> Dict:
        """Analyze tweet sentiment and detect events."""
        if not tweets:
            return self._simulate_sentiment(location_key)
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        event_mentions = {k: 0 for k in EVENT_KEYWORDS.keys()}
        
        for tweet in tweets:
            text = tweet.get("text", "").lower()
            
            # Count sentiment words
            pos_score = sum(1 for word in POSITIVE_WORDS if word in text)
            neg_score = sum(1 for word in NEGATIVE_WORDS if word in text)
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
            
            # Detect events
            for event_type, keywords in EVENT_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    event_mentions[event_type] += 1
        
        total = len(tweets)
        
        # Calculate sentiment score (-1 to 1)
        sentiment_score = (positive_count - negative_count) / total if total > 0 else 0
        
        # Determine dominant event
        dominant_event = None
        if event_mentions:
            max_mentions = max(event_mentions.values())
            if max_mentions > 0:
                dominant_event = max(event_mentions.items(), key=lambda x: x[1])[0]
        
        return {
            "sentiment_score": round(sentiment_score, 3),
            "positive_ratio": round(positive_count / total, 3) if total > 0 else 0,
            "negative_ratio": round(negative_count / total, 3) if total > 0 else 0,
            "neutral_ratio": round(neutral_count / total, 3) if total > 0 else 0,
            "tweet_count": total,
            "dominant_event": dominant_event,
            "event_mentions": event_mentions,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "twitter_api",
            "location": location_key
        }
    
    def _simulate_sentiment(self, location_key: str) -> Dict:
        """Simulate sentiment data based on location and time."""
        import random
        
        hour = datetime.utcnow().hour
        
        # Base sentiment varies by time of day
        if 10 <= hour <= 22:  # Daytime/Evening
            base_sentiment = random.uniform(0.1, 0.4)
        else:  # Night
            base_sentiment = random.uniform(-0.1, 0.2)
        
        # Location-specific adjustments
        if location_key == "wynwood":
            # Art district tends positive
            base_sentiment += 0.2
        elif location_key == "seoul":
            # Seoul nightlife positive
            if hour >= 18:
                base_sentiment += 0.3
        
        # Random event occasionally
        events = [None, None, None, "art", "food", "concert"]  # Mostly None
        dominant_event = random.choice(events)
        
        return {
            "sentiment_score": round(base_sentiment, 3),
            "positive_ratio": round(random.uniform(0.4, 0.7), 3),
            "negative_ratio": round(random.uniform(0.1, 0.3), 3),
            "neutral_ratio": round(random.uniform(0.2, 0.4), 3),
            "tweet_count": random.randint(10, 50),
            "dominant_event": dominant_event,
            "event_mentions": {
                "concert": random.randint(0, 3),
                "festival": random.randint(0, 2),
                "art": random.randint(0, 4),
                "food": random.randint(0, 3),
                "protest": 0,
                "accident": random.randint(0, 1)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulated",
            "location": location_key,
            "note": "Set TWITTER_BEARER_TOKEN for real data"
        }
    
    def calculate_vibe_modifiers(self, sentiment_data: Dict) -> Dict[str, float]:
        """
        Calculate vibe energy modifiers based on social sentiment.
        
        Returns multipliers for each vibe dimension.
        """
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        dominant_event = sentiment_data.get("dominant_event")
        
        # Base modifiers
        modifiers = {
            "social": 1.0,
            "creative": 1.0,
            "commercial": 1.0,
            "residential": 1.0
        }
        
        # Apply sentiment score (range -1 to 1)
        # Positive sentiment boosts social and creative
        if sentiment_score > 0:
            modifiers["social"] += sentiment_score * 0.2
            modifiers["creative"] += sentiment_score * 0.15
        else:
            # Negative sentiment reduces social
            modifiers["social"] += sentiment_score * 0.25
            modifiers["residential"] -= sentiment_score * 0.1  # People stay home
        
        # Event-specific modifiers
        if dominant_event:
            event_mods = {
                "concert": {"social": 0.3, "creative": 0.2},
                "festival": {"social": 0.4, "creative": 0.3, "commercial": 0.2},
                "art": {"creative": 0.3, "social": 0.1},
                "food": {"commercial": 0.25, "social": 0.15},
                "protest": {"social": 0.2, "commercial": -0.2, "residential": -0.1},
                "accident": {"social": -0.15, "commercial": -0.1}
            }
            
            if dominant_event in event_mods:
                for vibe_type, mod in event_mods[dominant_event].items():
                    modifiers[vibe_type] += mod
        
        # Ensure bounds
        for key in modifiers:
            modifiers[key] = max(0.5, min(1.5, modifiers[key]))
        
        return modifiers
    
    def get_sentiment_observation(self, sentiment_data: Dict, persona: str) -> str:
        """
        Get sentiment-based observation for an agent persona.
        """
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        dominant_event = sentiment_data.get("dominant_event")
        location = sentiment_data.get("location", "")
        
        # Event-based observations
        if dominant_event:
            event_obs = {
                "concert": {
                    "Street Artist": "The energy from tonight's concert is inspiring",
                    "Tech Hustler": "Post-concert crowd, perfect for networking",
                    "Night Owl": "Music still echoing through the streets",
                    "K-Pop Scout": "Concert spillover creating buzz everywhere"
                },
                "festival": {
                    "Street Artist": "Festival colors everywhere, feeling creative",
                    "Foodie": "Festival food trucks are incredible today",
                    "Flâneur": "Festival crowds make for great people watching",
                    "Night-Market Vendor": "Festival bringing huge crowds"
                },
                "art": {
                    "Street Artist": "New exhibition opening, community buzzing",
                    "Flâneur": "Gallery hopping today, so much to see",
                    "Tech Hustler": "Art-tech meetup happening tonight"
                },
                "food": {
                    "Foodie": "New restaurant opening, line around the block",
                    "Local": "Food scene here keeps getting better",
                    "Street Artist": "Painted near a popular new cafe"
                },
                "protest": {
                    "Local": "Community gathering for a cause",
                    "Zen Seeker": "Seeking calm away from the main area",
                    "Flâneur": "Observing the civic engagement"
                }
            }
            
            if dominant_event in event_obs and persona in event_obs[dominant_event]:
                return event_obs[dominant_event][persona]
        
        # Sentiment-based observations
        if sentiment_score > 0.3:
            positive_obs = [
                "The mood here is electric today",
                "Everyone seems energized and positive",
                "Great vibes all around",
                "The community feels alive"
            ]
            return random.choice(positive_obs)
        elif sentiment_score < -0.2:
            negative_obs = [
                "Something feels off in the air today",
                "Quieter than usual, people seem subdued",
                "Tension noticeable in the crowd",
                "Seeking calmer spots today"
            ]
            return random.choice(negative_obs)
        
        return "Observing the social flow"


# Global sentiment service instance
_sentiment_service: Optional[SentimentService] = None


def get_sentiment_service() -> SentimentService:
    """Get or create sentiment service singleton."""
    global _sentiment_service
    if _sentiment_service is None:
        _sentiment_service = SentimentService()
    return _sentiment_service