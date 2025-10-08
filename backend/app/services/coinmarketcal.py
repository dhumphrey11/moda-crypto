import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from ..config import settings


class CoinMarketCalService:
    """Service for fetching cryptocurrency events from CoinMarketCal API."""

    def __init__(self):
        self.base_url = "https://api.coinmarketcal.com/v1"
        self.api_key = settings.coinmarketcal_api_key
        self.rate_limit_delay = 1.0  # Conservative rate limiting
        self.last_request_time = 0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to CoinMarketCal API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            headers = {}
            if self.api_key:
                headers['x-api-key'] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.get(url, headers=headers, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logging.warning(
                            "CoinMarketCal rate limit hit, waiting...")
                        await asyncio.sleep(60)
                        return await self._make_request(endpoint, params)
                    else:
                        logging.error(
                            f"CoinMarketCal API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"CoinMarketCal request failed: {e}")
            return None

    async def get_events(self, days_ahead: int = 30) -> Optional[Dict]:
        """Get upcoming cryptocurrency events."""
        try:
            # Calculate date range
            start_date = datetime.utcnow().strftime('%Y-%m-%d')
            end_date = (datetime.utcnow() +
                        timedelta(days=days_ahead)).strftime('%Y-%m-%d')

            params = {
                'dateRangeStart': start_date,
                'dateRangeEnd': end_date,
                'page': 1,
                'max': 100,
                'sortBy': 'hot_events'
            }

            return await self._make_request("events", params)

        except Exception as e:
            logging.error(f"Failed to fetch events: {e}")
            return None

    async def get_categories(self) -> Optional[Dict]:
        """Get event categories."""
        try:
            return await self._make_request("categories")

        except Exception as e:
            logging.error(f"Failed to fetch categories: {e}")
            return None

    async def get_coins(self) -> Optional[Dict]:
        """Get available coins."""
        try:
            params = {'page': 1, 'max': 100}
            return await self._make_request("coins", params)

        except Exception as e:
            logging.error(f"Failed to fetch coins: {e}")
            return None


# Global service instance
coinmarketcal_service = CoinMarketCalService()


async def fetch_events() -> List[Dict[str, Any]]:
    """
    Public function to fetch cryptocurrency events from CoinMarketCal.
    This function is called by the fetch router.
    """
    try:
        from ..firestore_client import init_db

        # Fetch upcoming events
        events_data = await coinmarketcal_service.get_events(days_ahead=14)

        all_events = []

        if events_data and events_data.get('body'):
            for event in events_data['body']:
                try:
                    # Extract and normalize event data
                    event_data = {
                        'event_id': event.get('id'),
                        'title': event.get('title', {}).get('en', ''),
                        'description': event.get('description', {}).get('en', ''),
                        'date_event': event.get('date_event'),
                        'created_date': event.get('created_date'),
                        'hot_events': event.get('hot_events', False),
                        'percentage': event.get('percentage', 0),
                        'coins': event.get('coins', []),
                        'categories': event.get('categories', []),
                        'is_hot': event.get('hot_events', False),
                        'votes': {
                            'positive': event.get('positive_votes', 0),
                            'negative': event.get('negative_votes', 0),
                            'important': event.get('important_votes', 0)
                        },
                        'fetched_at': datetime.utcnow()
                    }

                    all_events.append(event_data)

                except Exception as e:
                    logging.error(
                        f"Failed to process event {event.get('id', 'unknown')}: {e}")
                    continue

        # Store events in Firestore
        if all_events:
            db = init_db()

            for event in all_events:
                try:
                    # Calculate event impact score
                    impact_score = 0.0

                    # Base score from votes
                    total_votes = sum(event['votes'].values())
                    if total_votes > 0:
                        positive_ratio = event['votes']['positive'] / \
                            total_votes
                        important_ratio = event['votes']['important'] / \
                            total_votes
                        impact_score += (positive_ratio *
                                         0.3 + important_ratio * 0.5)

                    # Boost for hot events
                    if event['is_hot']:
                        impact_score += 0.3

                    # Boost based on percentage
                    if event['percentage'] > 0:
                        impact_score += min(event['percentage'] / 100, 0.4)

                    # Cap impact score at 1.0
                    impact_score = min(impact_score, 1.0)

                    # Store in events collection
                    event_doc = {
                        'event_type': 'scheduled_event',
                        'title': event['title'],
                        'description': event['description'],
                        'date': event['date_event'],
                        'impact_score': impact_score,
                        'is_hot': event['is_hot'],
                        'votes': event['votes'],
                        'percentage': event['percentage'],
                        'external_id': event['event_id'],
                        'source': 'coinmarketcal',
                        'timestamp': datetime.utcnow()
                    }

                    # Add token associations
                    if event['coins']:
                        event_doc['associated_tokens'] = [
                            coin.get('symbol', '').upper()
                            for coin in event['coins']
                            if coin.get('symbol')
                        ]

                    # Add category information
                    if event['categories']:
                        event_doc['categories'] = [
                            cat.get('name', '')
                            for cat in event['categories']
                            if cat.get('name')
                        ]

                    db.collection('events').add(event_doc)

                    # Create individual token events for associated coins
                    if event['coins']:
                        for coin in event['coins']:
                            if coin.get('symbol'):
                                token_event = event_doc.copy()
                                token_event['token_id'] = coin['symbol'].upper()
                                token_event['event_type'] = 'token_event'
                                db.collection('events').add(token_event)

                except Exception as e:
                    logging.error(f"Failed to store event data: {e}")
                    continue

        logging.info(f"Processed {len(all_events)} events from CoinMarketCal")
        return all_events

    except Exception as e:
        logging.error(f"CoinMarketCal fetch_events failed: {e}")
        raise
