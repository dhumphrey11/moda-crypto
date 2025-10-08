import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from ..config import settings


class CryptoPanicService:
    """Service for fetching cryptocurrency news and sentiment from CryptoPanic API."""

    def __init__(self):
        self.base_url = "https://cryptopanic.com/api/v1"
        self.api_key = settings.cryptopanic_api_key
        self.rate_limit_delay = 1.0  # Conservative rate limiting
        self.last_request_time = 0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to CryptoPanic API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            if not params:
                params = {}

            if self.api_key:
                params['auth_token'] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.get(url, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logging.warning(
                            "CryptoPanic rate limit hit, waiting...")
                        await asyncio.sleep(60)
                        return await self._make_request(endpoint, params)
                    else:
                        logging.error(
                            f"CryptoPanic API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"CryptoPanic request failed: {e}")
            return None

    async def get_posts(self, filter_type: str = "hot", page: int = 1) -> Optional[Dict]:
        """Get news posts with specified filter."""
        try:
            params = {
                'filter': filter_type,
                'page': page,
                'public': 'true'
            }

            return await self._make_request("posts/", params)

        except Exception as e:
            logging.error(f"Failed to fetch posts: {e}")
            return None

    async def get_currencies(self) -> Optional[Dict]:
        """Get available currencies."""
        try:
            return await self._make_request("currencies/")

        except Exception as e:
            logging.error(f"Failed to fetch currencies: {e}")
            return None


# Global service instance
cryptopanic_service = CryptoPanicService()


async def fetch_news() -> List[Dict[str, Any]]:
    """
    Public function to fetch cryptocurrency news from CryptoPanic.
    This function is called by the fetch router.
    """
    try:
        from ..firestore_client import init_db

        # Fetch different types of news
        hot_posts = await cryptopanic_service.get_posts(filter_type="hot", page=1)
        trending_posts = await cryptopanic_service.get_posts(filter_type="trending", page=1)

        all_news = []

        # Process hot posts
        if hot_posts and hot_posts.get('results'):
            for post in hot_posts['results']:
                try:
                    news_data = {
                        'post_id': post.get('id'),
                        'title': post.get('title', ''),
                        'url': post.get('url', ''),
                        'source': post.get('source', {}).get('title', ''),
                        'published_at': post.get('published_at'),
                        'created_at': post.get('created_at'),
                        'kind': post.get('kind', ''),
                        'domain': post.get('domain', ''),
                        'votes': {
                            'negative': post.get('votes', {}).get('negative', 0),
                            'positive': post.get('votes', {}).get('positive', 0),
                            'important': post.get('votes', {}).get('important', 0),
                            'liked': post.get('votes', {}).get('liked', 0),
                            'disliked': post.get('votes', {}).get('disliked', 0),
                            'lol': post.get('votes', {}).get('lol', 0),
                            'toxic': post.get('votes', {}).get('toxic', 0),
                            'saved': post.get('votes', {}).get('saved', 0)
                        },
                        'currencies': post.get('currencies', []),
                        'filter_type': 'hot',
                        'fetched_at': datetime.utcnow()
                    }

                    all_news.append(news_data)

                except Exception as e:
                    logging.error(
                        f"Failed to process hot post {post.get('id', 'unknown')}: {e}")
                    continue

        # Process trending posts
        if trending_posts and trending_posts.get('results'):
            for post in trending_posts['results']:
                try:
                    # Avoid duplicates
                    if any(news['post_id'] == post.get('id') for news in all_news):
                        continue

                    news_data = {
                        'post_id': post.get('id'),
                        'title': post.get('title', ''),
                        'url': post.get('url', ''),
                        'source': post.get('source', {}).get('title', ''),
                        'published_at': post.get('published_at'),
                        'created_at': post.get('created_at'),
                        'kind': post.get('kind', ''),
                        'domain': post.get('domain', ''),
                        'votes': {
                            'negative': post.get('votes', {}).get('negative', 0),
                            'positive': post.get('votes', {}).get('positive', 0),
                            'important': post.get('votes', {}).get('important', 0),
                            'liked': post.get('votes', {}).get('liked', 0),
                            'disliked': post.get('votes', {}).get('disliked', 0),
                            'lol': post.get('votes', {}).get('lol', 0),
                            'toxic': post.get('votes', {}).get('toxic', 0),
                            'saved': post.get('votes', {}).get('saved', 0)
                        },
                        'currencies': post.get('currencies', []),
                        'filter_type': 'trending',
                        'fetched_at': datetime.utcnow()
                    }

                    all_news.append(news_data)

                except Exception as e:
                    logging.error(
                        f"Failed to process trending post {post.get('id', 'unknown')}: {e}")
                    continue

        # Store news in Firestore and calculate sentiment
        if all_news:
            db = init_db()

            for news in all_news:
                try:
                    # Calculate news sentiment score
                    votes = news['votes']
                    total_votes = sum(votes.values())

                    if total_votes > 0:
                        # Calculate weighted sentiment
                        positive_score = (
                            votes['positive'] + votes['liked']) / total_votes
                        negative_score = (
                            votes['negative'] + votes['disliked'] + votes['toxic']) / total_votes
                        importance_score = votes['important'] / total_votes

                        sentiment_score = positive_score - negative_score
                        impact_score = min(
                            (importance_score + abs(sentiment_score)) / 2, 1.0)
                    else:
                        sentiment_score = 0.0
                        impact_score = 0.2  # Default low impact for news without votes

                    # Store in events collection
                    event_doc = {
                        'event_type': 'news',
                        'title': news['title'],
                        'url': news['url'],
                        'source': news['source'],
                        'published_at': news['published_at'],
                        'kind': news['kind'],
                        'sentiment_score': sentiment_score,
                        'impact_score': impact_score,
                        'votes': votes,
                        'filter_type': news['filter_type'],
                        'external_id': news['post_id'],
                        'timestamp': datetime.utcnow()
                    }

                    # Add currency associations
                    if news['currencies']:
                        associated_tokens = []
                        for currency in news['currencies']:
                            if currency.get('code'):
                                associated_tokens.append(
                                    currency['code'].upper())

                        event_doc['associated_tokens'] = associated_tokens

                    db.collection('events').add(event_doc)

                    # Create individual token events for associated currencies
                    if news['currencies']:
                        for currency in news['currencies']:
                            if currency.get('code'):
                                token_event = event_doc.copy()
                                token_event['token_id'] = currency['code'].upper()
                                token_event['event_type'] = 'token_news'
                                db.collection('events').add(token_event)

                                # Also store as feature for sentiment analysis
                                db.collection('features').add({
                                    'token_id': currency['code'].upper(),
                                    'feature_type': 'news_sentiment',
                                    'sentiment_score': sentiment_score,
                                    'impact_score': impact_score,
                                    'news_count': 1,
                                    'source': 'cryptopanic',
                                    'timestamp': datetime.utcnow()
                                })

                except Exception as e:
                    logging.error(f"Failed to store news data: {e}")
                    continue

        logging.info(f"Processed {len(all_news)} news items from CryptoPanic")
        return all_news

    except Exception as e:
        logging.error(f"CryptoPanic fetch_news failed: {e}")
        raise
