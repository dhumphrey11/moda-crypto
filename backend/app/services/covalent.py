import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from ..config import settings


class CovalentService:
    """Service for fetching blockchain data from Covalent API."""

    def __init__(self):
        self.base_url = "https://api.covalenthq.com/v1"
        self.api_key = settings.covalent_api_key
        self.rate_limit_delay = 1.0  # Conservative rate limiting
        self.last_request_time = 0

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make rate-limited request to Covalent API."""
        try:
            # Implement rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - (current_time - self.last_request_time))

            auth = aiohttp.BasicAuth(
                self.api_key, '') if self.api_key else None

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{endpoint}"
                async with session.get(url, auth=auth, params=params) as response:
                    self.last_request_time = time.time()

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:
                        logging.warning("Covalent rate limit hit, waiting...")
                        await asyncio.sleep(60)
                        return await self._make_request(endpoint, params)
                    else:
                        logging.error(f"Covalent API error: {response.status}")
                        return None

        except Exception as e:
            logging.error(f"Covalent request failed: {e}")
            return None

    async def get_token_balances(self, chain_id: int, address: str) -> Optional[Dict]:
        """Get token balances for an address on a specific chain."""
        try:
            endpoint = f"{chain_id}/address/{address}/balances_v2/"
            params = {'nft': False}

            return await self._make_request(endpoint, params)

        except Exception as e:
            logging.error(f"Failed to fetch token balances for {address}: {e}")
            return None

    async def get_transactions(self, chain_id: int, address: str) -> Optional[Dict]:
        """Get transaction history for an address."""
        try:
            endpoint = f"{chain_id}/address/{address}/transactions_v2/"
            params = {'page-size': 100}

            return await self._make_request(endpoint, params)

        except Exception as e:
            logging.error(f"Failed to fetch transactions for {address}: {e}")
            return None

    async def get_portfolio_value(self, chain_id: int, address: str) -> Optional[Dict]:
        """Get portfolio value for an address."""
        try:
            endpoint = f"{chain_id}/address/{address}/portfolio_v2/"

            return await self._make_request(endpoint)

        except Exception as e:
            logging.error(
                f"Failed to fetch portfolio value for {address}: {e}")
            return None


# Global service instance
covalent_service = CovalentService()


async def fetch_blockchain_data() -> List[Dict[str, Any]]:
    """
    Public function to fetch blockchain data from Covalent.
    This function is called by the fetch router.
    """
    try:
        from ..firestore_client import init_db

        # Ethereum chain ID
        eth_chain_id = 1

        # Sample addresses for demonstration
        # In production, you'd have a curated list of important addresses
        sample_addresses = [
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT contract
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",   # DAI contract
            "0xA0b86a33E6441B8a84C5c5c4C6C6F5d2f1c6D4E0"    # Example address
        ]

        all_data = []

        for address in sample_addresses[:2]:  # Limit to avoid rate limits
            try:
                # Fetch various blockchain metrics
                balances = await covalent_service.get_token_balances(eth_chain_id, address)
                transactions = await covalent_service.get_transactions(eth_chain_id, address)

                if balances or transactions:
                    blockchain_data = {
                        'chain_id': eth_chain_id,
                        'address': address,
                        'balances': balances,
                        'transactions': transactions,
                        'fetched_at': datetime.utcnow()
                    }
                    all_data.append(blockchain_data)

                # Add delay between requests
                await asyncio.sleep(2)

            except Exception as e:
                logging.error(
                    f"Failed to fetch blockchain data for {address}: {e}")
                continue

        # Process and store meaningful metrics
        if all_data:
            db = init_db()

            processed_metrics = []

            for data in all_data:
                try:
                    # Extract blockchain activity metrics
                    balances_data = data.get('balances', {}).get('data', {})
                    transactions_data = data.get(
                        'transactions', {}).get('data', {})

                    # Calculate activity metrics
                    token_count = len(balances_data.get(
                        'items', [])) if balances_data else 0
                    tx_count = len(transactions_data.get(
                        'items', [])) if transactions_data else 0

                    # Calculate total portfolio value
                    total_value = 0.0
                    if balances_data and balances_data.get('items'):
                        for item in balances_data['items']:
                            quote = item.get('quote', 0)
                            if quote:
                                total_value += quote

                    metrics = {
                        'address': data['address'],
                        'chain_id': data['chain_id'],
                        'token_count': token_count,
                        'transaction_count': tx_count,
                        'portfolio_value_usd': total_value,
                        'activity_score': (tx_count * 0.1 + token_count * 0.5) / 10,
                        'timestamp': datetime.utcnow()
                    }

                    processed_metrics.append(metrics)

                    # Store aggregated metrics in Firestore
                    db.collection('events').add({
                        'event_type': 'blockchain_activity',
                        'chain_id': data['chain_id'],
                        'address': data['address'],
                        'metrics': metrics,
                        'impact_score': min(metrics['activity_score'], 1.0),
                        'timestamp': datetime.utcnow()
                    })

                except Exception as e:
                    logging.error(f"Failed to process blockchain data: {e}")
                    continue

        logging.info(
            f"Processed {len(all_data)} blockchain data points from Covalent")
        return all_data

    except Exception as e:
        logging.error(f"Covalent fetch_blockchain_data failed: {e}")
        raise
