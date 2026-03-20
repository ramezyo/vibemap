"""
Reddit Sentiment Service
Free alternative to Twitter/X API using Reddit's location-based communities
"""

import os
import httpx
import asyncpraw
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from aiocache import cached

# Reddit API credentials (free tier: 60 requests/minute)
# Get from: https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = "Vibemap/1.0 (Sentiment Analysis for Spatial Intelligence)"

# Location to subreddit mapping
LOCATION_SUBREDDITS = {
    "wynwood": ["Miami", "wynwood", "SouthFlorida"],
    "miami": ["Miami", "SouthFlorida", "Florida"],
    "seoul": ["korea", "seoul", "koreatravel"],
    "south_korea": ["korea", "koreatravel", "Living_in_Korea"]
}

# Sentiment keywords
POSITIVE_WORDS = [
    "amazing", "awesome", "beautiful", "best", "brilliant", "cool", "excellent",
    "excited", "fantastic", "fun", "good", "great", "happy", "incredible",
    "inspired", "love", "lovely", "nice", "perfect", "vibrant", "wonderful",
    "recommend", "enjoy", "beautiful", "delicious", "tasty", "worth"
]

NEGATIVE_WORDS = [
    "awful", "bad", "boring", "crowded", "disappointing", "hate", "horrible",
    "overrated", "sad", "terrible", "ugly", "worst", "boring", "empty",
    "avoid", "skip", "waste", "expensive", "rude", "dirty"
]

EVENT_KEYWORDS = {
    "concert": ["concert", "live music", "performance", "gig", "show", "festival"],
    "art": ["art", "exhibition", "gallery", "mural", "street art", "wynwood walls"],
    "food": ["food", "restaurant", "cafe", "popup", "dining", "brunch", "tacos"],
    "traffic": ["traffic", "congestion", "parking", "crowded", "busy"],
    "weather": ["rain", "storm", "hot", "humid", "sunny", "weather"]
}


class RedditSentimentService:
    """
    Free sentiment analysis using Reddit's location-based communities.
    
    Reddit API free tier: 60 requests/minute
    Perfect for monitoring city-specific sentiment without paying $100+/mo for Twitter.
    """
    
    def __init__(self):
        self.client_id = REDDIT_CLIENT_ID
        self.client_secret = REDDIT_CLIENT_SECRET
        self.reddit = None
        
    async def _get_reddit_client(self):
        """Get or create Reddit client."""
        if self.reddit is None and self.client_id and self.client_secret:
            self.reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=REDDIT_USER_AGENT
            )
        return self.reddit
    
    @cached(ttl=600)  # Cache for 10 minutes
    async def get_location_sentiment(self, location_key: str, limit: int = 25) -> Dict:
        """
        Get sentiment from location-based subreddits.
        
        Returns aggregated sentiment from recent posts.
        """
        reddit = await self._get_reddit_client()
        
        if not reddit:
            # Return simulated sentiment if no Reddit credentials
            return self._simulate_sentiment(location_key)
        
        try:
            subreddits = LOCATION_SUBREDDITS.get(location_key, [location_key])
            all_posts = []
            
            for subreddit_name in subreddits:
                try:
                    subreddit = await reddit.subreddit(subreddit_name)
                    async for post in subreddit.new(limit=limit // len(subreddits)):
                        all_posts.append({
                            "title": post.title,
                            "text": post.selftext,
                            "score": post.score,
                            "created": datetime.fromtimestamp(post.created_utc)
                        })
                except Exception as e:
                    print(f"⚠️ Error fetching r/{subreddit_name}: {e}")
                    continue
            
            return self._analyze_posts(all_posts, location_key)
            
        except Exception as e:
            print(f"⚠️ Reddit API error: {e}")
            return self._simulate_sentiment(location_key)
    
    def _analyze_posts(self, posts: List[Dict], location_key: str) -> Dict:
        """Analyze Reddit posts for sentiment."""
        if not posts:
            return self._simulate_sentiment(location_key)
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        event_mentions = {k: 0 for k in EVENT_KEYWORDS.keys()}
        total_score = 0
        
        for post in posts:
            text = f"{post.get('title', '')} {post.get('text', '')}".lower()
            score = post.get("score", 1)
            
            # Weight by upvotes
            weight = min(score, 100) / 100  # Cap at 100 upvotes
            
            # Count sentiment words
            pos_score = sum(1 for word in POSITIVE_WORDS if word in text) * weight
            neg_score = sum(1 for word in NEGATIVE_WORDS if word in text) * weight
            
            if pos_score > neg_score:
                positive_count += 1
            elif neg_score > pos_score:
                negative_count += 1
            else:
                neutral_count += 1
            
            # Detect events
            for event_type, keywords in EVENT_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    event_mentions[event_type] += weight
            
            total_score += weight
        
        total = len(posts)
        
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
            "post_count": total,
            "dominant_event": dominant_event,
            "event_mentions": event_mentions,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "reddit_api",
            "location": location_key,
            "subreddits": LOCATION_SUBREDDITS.get(location_key, [location_key])
        }
    
    def _simulate_sentiment(self, location_key: str) -> Dict:
        """Simulate Reddit sentiment data."""
        import random
        
        hour = datetime.utcnow().hour
        
        # Base sentiment varies by time
        if 10 <= hour <= 22:
            base_sentiment = random.uniform(0.1, 0.4)
        else:
            base_sentiment = random.uniform(-0.1, 0.2)
        
        # Location-specific adjustments
        if location_key in ["wynwood", "miami"]:
            base_sentiment += 0.15  # Tourist destinations tend positive
        elif location_key in ["seoul", "south_korea"]:
            if hour >= 18:
                base_sentiment += 0.2  # Seoul nightlife positive
        
        events = [None, None, None, "food", "art", "concert"]
        dominant_event = random.choice(events)
        
        return {
            "sentiment_score": round(base_sentiment, 3),
            "positive_ratio": round(random.uniform(0.4, 0.7), 3),
            "negative_ratio": round(random.uniform(0.1, 0.3), 3),
            "neutral_ratio": round(random.uniform(0.2, 0.4), 3),
            "post_count": random.randint(15, 40),
            "dominant_event": dominant_event,
            "event_mentions": {
                "concert": random.randint(0, 3),
                "art": random.randint(0, 4),
                "food": random.randint(0, 5),
                "traffic": random.randint(0, 3),
                "weather": random.randint(0, 2)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulated",
            "location": location_key,
            "subreddits": LOCATION_SUBREDDITS.get(location_key, [location_key]),
            "note": "Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET for real data"
        }
    
    def calculate_vibe_modifiers(self, sentiment_data: Dict) -> Dict[str, float]:
        """Calculate vibe modifiers from Reddit sentiment."""
        sentiment_score = sentiment_data.get("sentiment_score", 0)
        dominant_event = sentiment_data.get("dominant_event")
        
        modifiers = {
            "social": 1.0,
            "creative": 1.0,
            "commercial": 1.0,
            "residential": 1.0
        }
        
        # Apply sentiment score
        if sentiment_score > 0:
            modifiers["social"] += sentiment_score * 0.2
            modifiers["creative"] += sentiment_score * 0.15
        else:
            modifiers["social"] += sentiment_score * 0.25
            modifiers["residential"] -= sentiment_score * 0.1
        
        # Event-specific modifiers
        if dominant_event:
            event_mods = {
                "concert": {"social": 0.3, "creative": 0.2},
                "art": {"creative": 0.3, "social": 0.1},
                "food": {"commercial": 0.25, "social": 0.15},
                "traffic": {"social": -0.1, "commercial": -0.1},
                "weather": {"social": -0.05}
            }
            
            if dominant_event in event_mods:
                for vibe_type, mod in event_mods[dominant_event].items():
                    modifiers[vibe_type] += mod
        
        # Ensure bounds
        for key in modifiers:
            modifiers[key] = max(0.5, min(1.5, modifiers[key]))
        
        return modifiers


# Global Reddit sentiment service
_reddit_service: Optional[RedditSentimentService] = None


def get_reddit_sentiment_service() -> RedditSentimentService:
    """Get or create Reddit sentiment service."""
    global _reddit_service
    if _reddit_service is None:
        _reddit_service = RedditSentimentService()
    return _reddit_service