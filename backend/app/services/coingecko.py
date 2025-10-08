import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from ..config import settings


class CoinGeckoService:
    """Service for fetching market data from CoinGecko API."""

    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.api_key = settings.coingecko_api_key
        self.rate_limit_delay = 1.2  # seconds between requests
        self.last_request_time = 0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to CoinGecko API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            headers = {}
            if self.api_key:
                headers['X-CG-API-KEY'] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.get(url, headers=headers, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        # Rate limited, wait and retry
                        logging.warning("CoinGecko rate limit hit, waiting...")
                        await asyncio.sleep(60)  # Wait 1 minute
                        return await self._make_request(endpoint, params)
                    else:
                        logging.error(
                            f"CoinGecko API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"CoinGecko request failed: {e}")
            return None

    async def get_market_data(self, vs_currency: str = "usd", per_page: int = 100) -> List[Dict]:
        """Fetch market data for top cryptocurrencies."""
        try:
            params = {
                'vs_currency': vs_currency,
                'order': 'market_cap_desc',
                'per_page': per_page,
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '1h,24h,7d'
            }

            data = await self._make_request("coins/markets", params)
            if data:
                logging.info(
                    f"Fetched {len(data)} market data points from CoinGecko")
                return data
            return []

        except Exception as e:
            logging.error(f"Failed to fetch CoinGecko market data: {e}")
            return []

    async def get_coin_data(self, coin_id: str) -> Optional[Dict]:
        """Get detailed data for a specific coin."""
        try:
            params = {
                'localization': False,
                'tickers': False,
                'market_data': True,
                'community_data': False,
                'developer_data': False,
                'sparkline': False
            }

            return await self._make_request(f"coins/{coin_id}", params)

        except Exception as e:
            logging.error(f"Failed to fetch coin data for {coin_id}: {e}")
            return None

    async def get_price_history(self, coin_id: str, days: int = 7) -> Optional[Dict]:
        """Get historical price data for a coin."""
        try:
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'hourly' if days <= 30 else 'daily'
            }

            return await self._make_request(f"coins/{coin_id}/market_chart", params)

        except Exception as e:
            logging.error(f"Failed to fetch price history for {coin_id}: {e}")
            return None


# Global service instance
coingecko_service = CoinGeckoService()


async def fetch_market_data() -> List[Dict[str, Any]]:
    """
    Public function to fetch market data from CoinGecko.
    This function is called by the fetch router.
    """
    try:
        from ..firestore_client import init_db

        # Fetch market data
        market_data = await coingecko_service.get_market_data(per_page=50)

        if not market_data:
            return []

        # Store in Firestore (optional - for raw data storage)
        db = init_db()

        processed_data = []
        for coin in market_data:
            try:
                # Extract and normalize data
                coin_data = {
                    'coingecko_id': coin.get('id'),
                    'symbol': coin.get('symbol', '').upper(),
                    'name': coin.get('name'),
                    'current_price': coin.get('current_price', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'total_volume': coin.get('total_volume', 0),
                    'price_change_24h': coin.get('price_change_24h', 0),
                    'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0),
                    'price_change_percentage_7d': coin.get('price_change_percentage_7d_in_currency', 0),
                    'circulating_supply': coin.get('circulating_supply', 0),
                    'total_supply': coin.get('total_supply', 0),
                    'ath': coin.get('ath', 0),
                    'ath_date': coin.get('ath_date'),
                    'atl': coin.get('atl', 0),
                    'atl_date': coin.get('atl_date'),
                    'last_updated': coin.get('last_updated'),
                    'fetched_at': datetime.utcnow()
                }

                processed_data.append(coin_data)

                # Update or create token entry
                token_ref = db.collection(
                    'tokens').document(coin_data['symbol'])
                token_ref.set({
                    'symbol': coin_data['symbol'],
                    'name': coin_data['name'],
                    'coingecko_id': coin_data['coingecko_id'],
                    'market_cap': coin_data['market_cap'],
                    # Using volume as liquidity proxy
                    'liquidity_24h': coin_data['total_volume'],
                    'active': True,
                    'last_updated': datetime.utcnow()
                }, merge=True)

            except Exception as e:
                logging.error(
                    f"Failed to process coin data for {coin.get('symbol', 'unknown')}: {e}")
                continue

        logging.info(f"Processed {len(processed_data)} coins from CoinGecko")
        return processed_data

    except Exception as e:
        logging.error(f"CoinGecko fetch_market_data failed: {e}")
        raise
