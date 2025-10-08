import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import hmac
import hashlib
import base64

from ..config import settings


class CoinbaseService:
    """Service for fetching trading data from Coinbase Advanced Trade API."""

    def __init__(self):
        self.base_url = "https://api.coinbase.com/api/v3/brokerage"
        self.api_key = settings.coinbase_api_key
        self.api_secret = settings.coinbase_api_secret
        self.rate_limit_delay = 0.1  # 10 requests per second
        self.last_request_time = 0

    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate signature for Coinbase API authentication."""
        if not self.api_secret:
            return ""

        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Coinbase API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            if not self.api_key or not self.api_secret:
                logging.warning("Coinbase API credentials not configured")
                return None

            timestamp = str(int(time.time()))
            path = f"/api/v3/brokerage/{endpoint}"

            headers = {
                'CB-ACCESS-KEY': self.api_key,
                'CB-ACCESS-SIGN': self._generate_signature(timestamp, method, path),
                'CB-ACCESS-TIMESTAMP': timestamp,
                'Content-Type': 'application/json'
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.request(method, url, headers=headers, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logging.warning("Coinbase rate limit hit, waiting...")
                        await asyncio.sleep(60)
                        return await self._make_request(endpoint, method, params)
                    else:
                        logging.error(f"Coinbase API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"Coinbase request failed: {e}")
            return None

    async def get_products(self) -> Optional[Dict]:
        """Get all trading products."""
        try:
            return await self._make_request("products")

        except Exception as e:
            logging.error(f"Failed to fetch products: {e}")
            return None

    async def get_product_ticker(self, product_id: str) -> Optional[Dict]:
        """Get ticker information for a product."""
        try:
            return await self._make_request(f"products/{product_id}/ticker")

        except Exception as e:
            logging.error(f"Failed to fetch ticker for {product_id}: {e}")
            return None

    async def get_product_stats(self, product_id: str) -> Optional[Dict]:
        """Get 24hr stats for a product."""
        try:
            return await self._make_request(f"products/{product_id}/stats")

        except Exception as e:
            logging.error(f"Failed to fetch stats for {product_id}: {e}")
            return None


# Global service instance
coinbase_service = CoinbaseService()


async def fetch_trading_data() -> List[Dict[str, Any]]:
    """
    Public function to fetch trading data from Coinbase.
    This function can be called by the fetch router.
    """
    try:
        from ..firestore_client import init_db

        # Get available products
        products_data = await coinbase_service.get_products()

        if not products_data or not products_data.get('products'):
            logging.warning("No products data from Coinbase")
            return []

        all_data = []

        # Focus on major USD pairs
        major_pairs = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD']

        for product_id in major_pairs:
            try:
                # Check if product exists
                product_exists = any(
                    p.get('product_id') == product_id
                    for p in products_data['products']
                )

                if not product_exists:
                    continue

                # Get ticker and stats
                ticker = await coinbase_service.get_product_ticker(product_id)
                stats = await coinbase_service.get_product_stats(product_id)

                if ticker or stats:
                    trading_data = {
                        'product_id': product_id,
                        'ticker': ticker,
                        'stats': stats,
                        'fetched_at': datetime.utcnow()
                    }
                    all_data.append(trading_data)

                # Add delay between requests
                await asyncio.sleep(0.2)

            except Exception as e:
                logging.error(
                    f"Failed to fetch trading data for {product_id}: {e}")
                continue

        # Store in Firestore
        if all_data:
            db = init_db()

            for data in all_data:
                try:
                    product_id = data['product_id']
                    symbol = product_id.split('-')[0]  # Extract base currency

                    ticker = data.get('ticker', {})
                    stats = data.get('stats', {})

                    # Extract trading metrics
                    current_price = float(ticker.get(
                        'price', 0)) if ticker.get('price') else 0
                    volume_24h = float(stats.get('volume', 0)
                                       ) if stats.get('volume') else 0
                    price_change_24h = float(stats.get('price_change', 0)) if stats.get(
                        'price_change') else 0

                    # Store as features
                    db.collection('features').add({
                        'token_id': symbol,
                        'feature_type': 'trading',
                        'exchange': 'coinbase',
                        'current_price': current_price,
                        'volume_24h': volume_24h,
                        'price_change_24h': price_change_24h,
                        'product_id': product_id,
                        'timestamp': datetime.utcnow()
                    })

                except Exception as e:
                    logging.error(
                        f"Failed to store Coinbase trading data: {e}")
                    continue

        logging.info(
            f"Processed {len(all_data)} trading data points from Coinbase")
        return all_data

    except Exception as e:
        logging.error(f"Coinbase fetch_trading_data failed: {e}")
        return []
