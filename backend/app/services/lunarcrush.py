import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from ..config import settings


class LunarCrushService:
    """Service for fetching social sentiment data from LunarCrush API."""

    def __init__(self):
        self.base_url = "https://api.lunarcrush.com/v2"
        self.api_key = settings.lunarcrush_api_key
        self.rate_limit_delay = 2.0  # Conservative rate limiting
        self.last_request_time = 0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to LunarCrush API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            if not params:
                params = {}

            if self.api_key:
                params['key'] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.get(url, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logging.warning(
                            "LunarCrush rate limit hit, waiting...")
                        await asyncio.sleep(120)  # Wait 2 minutes
                        return await self._make_request(endpoint, params)
                    else:
                        logging.error(
                            f"LunarCrush API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"LunarCrush request failed: {e}")
            return None

    async def get_assets(self, limit: int = 50) -> Optional[Dict]:
        """Get social metrics for top assets."""
        try:
            params = {
                'data': 'assets',
                'limit': limit,
                'sort': 'social_score'
            }

            return await self._make_request("", params)

        except Exception as e:
            logging.error(f"Failed to fetch LunarCrush assets: {e}")
            return None

    async def get_asset_details(self, symbol: str) -> Optional[Dict]:
        """Get detailed social metrics for a specific asset."""
        try:
            params = {
                'data': 'assets',
                'symbol': symbol
            }

            return await self._make_request("", params)

        except Exception as e:
            logging.error(f"Failed to fetch asset details for {symbol}: {e}")
            return None

    async def get_market_insights(self) -> Optional[Dict]:
        """Get overall market social sentiment insights."""
        try:
            params = {
                'data': 'market'
            }

            return await self._make_request("", params)

        except Exception as e:
            logging.error(f"Failed to fetch market insights: {e}")
            return None


# Global service instance
lunarcrush_service = LunarCrushService()


async def fetch_social_data() -> List[Dict[str, Any]]:
    """
    Public function to fetch social sentiment data from LunarCrush.
    This function is called by the fetch router.
    """
    try:
        from ..firestore_client import init_db, get_tokens_list

        # Get top social assets
        assets_data = await lunarcrush_service.get_assets(limit=30)
        market_data = await lunarcrush_service.get_market_insights()

        all_data = []

        if assets_data and assets_data.get('data'):
            for asset in assets_data['data']:
                try:
                    # Extract social sentiment metrics
                    social_data = {
                        'symbol': asset.get('symbol', '').upper(),
                        'name': asset.get('name'),
                        'social_score': asset.get('social_score', 0),
                        'social_volume_24h': asset.get('social_volume_24h', 0),
                        'social_dominance': asset.get('social_dominance', 0),
                        'sentiment': asset.get('sentiment', 0),
                        'tweets_24h': asset.get('tweets_24h', 0),
                        'reddit_posts_24h': asset.get('reddit_posts_24h', 0),
                        'social_contributors': asset.get('social_contributors', 0),
                        'social_volume_change_24h': asset.get('social_volume_change_24h', 0),
                        'sentiment_relative': asset.get('sentiment_relative', 0),
                        'fetched_at': datetime.utcnow()
                    }

                    all_data.append(social_data)

                except Exception as e:
                    logging.error(
                        f"Failed to process social data for {asset.get('symbol', 'unknown')}: {e}")
                    continue

        # Add market sentiment data
        if market_data and market_data.get('data'):
            market_sentiment = {
                'type': 'market_sentiment',
                'data': market_data['data'],
                'fetched_at': datetime.utcnow()
            }
            all_data.append(market_sentiment)

        # Store in Firestore
        if all_data:
            db = init_db()

            for data in all_data:
                try:
                    if data.get('type') == 'market_sentiment':
                        # Store market sentiment
                        db.collection('events').add({
                            'event_type': 'market_sentiment',
                            'data': data['data'],
                            'impact_score': 0.5,  # Moderate impact
                            'timestamp': datetime.utcnow()
                        })
                    else:
                        # Store individual token social data
                        symbol = data['symbol']

                        # Calculate composite social score
                        social_score = data.get('social_score', 0)
                        sentiment = data.get('sentiment', 0)
                        volume_change = data.get('social_volume_change_24h', 0)

                        composite_social_score = (
                            (social_score / 100) * 0.4 +
                            # Assuming sentiment is 1-5 scale
                            (sentiment / 5) * 0.3 +
                            min(abs(volume_change) / 100, 1.0) * 0.3
                        )

                        # Store in features collection
                        db.collection('features').add({
                            'token_id': symbol,
                            'feature_type': 'social',
                            'social_score': social_score,
                            'sentiment': sentiment,
                            'social_volume_24h': data.get('social_volume_24h', 0),
                            'tweets_24h': data.get('tweets_24h', 0),
                            'reddit_posts_24h': data.get('reddit_posts_24h', 0),
                            'composite_social_score': composite_social_score,
                            'timestamp': datetime.utcnow()
                        })

                        # Also create an event if sentiment is extreme
                        if abs(sentiment) > 3.5:  # Assuming 1-5 scale
                            db.collection('events').add({
                                'event_type': 'sentiment_extreme',
                                'token_id': symbol,
                                'sentiment_value': sentiment,
                                'social_score': social_score,
                                'impact_score': min(abs(sentiment) / 5, 1.0),
                                'timestamp': datetime.utcnow()
                            })

                except Exception as e:
                    logging.error(f"Failed to store social data: {e}")
                    continue

        logging.info(
            f"Processed {len(all_data)} social data points from LunarCrush")
        return all_data

    except Exception as e:
        logging.error(f"LunarCrush fetch_social_data failed: {e}")
        raise
