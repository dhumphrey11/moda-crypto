import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from ..config import settings


class MoralisService:
    """Service for fetching on-chain data from Moralis API."""

    def __init__(self):
        self.base_url = "https://deep-index.moralis.io/api/v2"
        self.api_key = settings.moralis_api_key
        self.rate_limit_delay = 0.5  # 25 requests per second
        self.last_request_time = 0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to Moralis API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            headers = {
                'X-API-Key': self.api_key
            } if self.api_key else {}

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.get(url, headers=headers, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logging.warning("Moralis rate limit hit, waiting...")
                        await asyncio.sleep(30)
                        return await self._make_request(endpoint, params)
                    else:
                        logging.error(f"Moralis API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"Moralis request failed: {e}")
            return None

    async def get_token_transfers(self, address: str, chain: str = "eth") -> Optional[Dict]:
        """Get token transfers for an address."""
        try:
            params = {
                'chain': chain,
                'limit': 100
            }

            return await self._make_request(f"{address}/erc20/transfers", params)

        except Exception as e:
            logging.error(
                f"Failed to fetch token transfers for {address}: {e}")
            return None

    async def get_token_balances(self, address: str, chain: str = "eth") -> Optional[Dict]:
        """Get token balances for an address."""
        try:
            params = {'chain': chain}
            return await self._make_request(f"{address}/erc20", params)

        except Exception as e:
            logging.error(f"Failed to fetch token balances for {address}: {e}")
            return None

    async def get_defi_positions(self, address: str, chain: str = "eth") -> Optional[Dict]:
        """Get DeFi positions for an address."""
        try:
            params = {'chain': chain}
            return await self._make_request(f"wallets/{address}/defi/positions", params)

        except Exception as e:
            logging.error(f"Failed to fetch DeFi positions for {address}: {e}")
            return None


# Global service instance
moralis_service = MoralisService()


async def fetch_onchain_data() -> List[Dict[str, Any]]:
    """
    Public function to fetch on-chain data from Moralis.
    This function is called by the fetch router.
    """
    try:
        from ..firestore_client import init_db, get_tokens_list

        # Get list of tokens to fetch data for
        tokens = get_tokens_list()
        if not tokens:
            logging.warning("No tokens found for on-chain data fetch")
            return []

        # For demo purposes, we'll fetch data for some well-known addresses
        # In production, you'd have a list of relevant contract addresses
        demo_addresses = [
            "0xA0b86a33E6441B8a84C5c5c4C6C6F5d2f1c6D4E0",  # Example address
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
            "0x6B175474E89094C44Da98b954EedeAC495271d0F"   # DAI
        ]

        all_data = []

        for address in demo_addresses[:3]:  # Limit to avoid rate limits
            try:
                # Fetch various on-chain metrics
                transfers = await moralis_service.get_token_transfers(address)
                balances = await moralis_service.get_token_balances(address)

                if transfers or balances:
                    onchain_data = {
                        'address': address,
                        'transfers': transfers,
                        'balances': balances,
                        'fetched_at': datetime.utcnow()
                    }
                    all_data.append(onchain_data)

                # Add delay between addresses
                await asyncio.sleep(1)

            except Exception as e:
                logging.error(
                    f"Failed to fetch on-chain data for {address}: {e}")
                continue

        # Store aggregated on-chain metrics in Firestore
        if all_data:
            db = init_db()

            # Process and aggregate the data
            processed_metrics = []

            for data in all_data:
                try:
                    # Extract meaningful metrics from raw data
                    transfers = data.get('transfers', {})
                    transfer_count = len(transfers.get(
                        'result', [])) if transfers else 0

                    balances = data.get('balances', {})
                    unique_tokens = len(balances.get(
                        'result', [])) if balances else 0

                    metrics = {
                        'address': data['address'],
                        'transfer_count_24h': transfer_count,  # Approximate
                        'unique_token_count': unique_tokens,
                        'activity_score': transfer_count * 0.1 + unique_tokens * 0.2,
                        'timestamp': datetime.utcnow()
                    }

                    processed_metrics.append(metrics)

                    # Store in Firestore events collection
                    db.collection('events').add({
                        'event_type': 'onchain_activity',
                        'address': data['address'],
                        'metrics': metrics,
                        'impact_score': min(metrics['activity_score'] / 10, 1.0),
                        'timestamp': datetime.utcnow()
                    })

                except Exception as e:
                    logging.error(f"Failed to process on-chain data: {e}")
                    continue

        logging.info(
            f"Processed {len(all_data)} on-chain data points from Moralis")
        return all_data

    except Exception as e:
        logging.error(f"Moralis fetch_onchain_data failed: {e}")
        raise
