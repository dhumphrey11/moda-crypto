"""
Universe Management Module

This module handles the three-tier token universe system:
- Market Universe: Top 100-500 tokens for macro market trends
- Watchlist Universe: <=100 curated tokens for ML feature engineering  
- Portfolio Universe: <10 active trading positions

Each universe defines which tokens to track and how frequently to update their data.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from .firestore_client import init_db

# Universe type constants
MARKET_UNIVERSE = "market"
WATCHLIST_UNIVERSE = "watchlist"  
PORTFOLIO_UNIVERSE = "portfolio"

# Default update frequencies (in minutes)
DEFAULT_FREQUENCIES = {
    MARKET_UNIVERSE: 60,      # Every hour
    WATCHLIST_UNIVERSE: 30,   # Every 30 minutes (15-60 range)
    PORTFOLIO_UNIVERSE: 5     # Every 5 minutes (1-5 range)
}

class UniverseManager:
    """Manages token universes and their configurations."""
    
    def __init__(self):
        self.db = init_db()
    
    async def get_universe_tokens(self, universe_name: str) -> List[Dict[str, Any]]:
        """
        Get all active tokens from a specific universe.
        
        Args:
            universe_name: One of 'market', 'watchlist', or 'portfolio'
            
        Returns:
            List of token documents with include=True
        """
        try:
            collection_name = f"{universe_name}Universe"
            docs = self.db.collection(collection_name).where("include", "==", True).stream()
            
            tokens = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                tokens.append(data)
                
            logging.info(f"Retrieved {len(tokens)} tokens from {universe_name} universe")
            return tokens
            
        except Exception as e:
            logging.error(f"Error retrieving {universe_name} universe tokens: {e}")
            return []
    
    async def get_universe_token_ids(self, universe_name: str) -> List[str]:
        """
        Get list of token IDs from a specific universe.
        
        Args:
            universe_name: One of 'market', 'watchlist', or 'portfolio'
            
        Returns:
            List of token IDs (strings)
        """
        tokens = await self.get_universe_tokens(universe_name)
        return [token.get('tokenId', token.get('id', '')) for token in tokens]
    
    async def get_universe_symbols(self, universe_name: str) -> List[str]:
        """
        Get list of token symbols from a specific universe.
        
        Args:
            universe_name: One of 'market', 'watchlist', or 'portfolio'
            
        Returns:
            List of token symbols (strings)
        """
        tokens = await self.get_universe_tokens(universe_name)
        return [token.get('symbol', '').lower() for token in tokens if token.get('symbol')]
    
    async def add_token_to_universe(self, universe_name: str, token_data: Dict[str, Any]) -> bool:
        """
        Add a token to a specific universe.
        
        Args:
            universe_name: One of 'market', 'watchlist', or 'portfolio'
            token_data: Token information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = f"{universe_name}Universe"
            
            # Ensure required fields
            token_data.setdefault('include', True)
            token_data.setdefault('createdAt', datetime.utcnow())
            token_data.setdefault('updatedAt', datetime.utcnow())
            
            # Use tokenId as document ID if provided
            doc_id = token_data.get('tokenId') or token_data.get('id')
            
            if doc_id:
                self.db.collection(collection_name).document(doc_id).set(token_data)
            else:
                self.db.collection(collection_name).add(token_data)
                
            logging.info(f"Added token {token_data.get('symbol')} to {universe_name} universe")
            return True
            
        except Exception as e:
            logging.error(f"Error adding token to {universe_name} universe: {e}")
            return False
    
    async def remove_token_from_universe(self, universe_name: str, token_id: str) -> bool:
        """
        Remove a token from a specific universe (set include=False).
        
        Args:
            universe_name: One of 'market', 'watchlist', or 'portfolio'
            token_id: Token ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = f"{universe_name}Universe"
            
            self.db.collection(collection_name).document(token_id).update({
                'include': False,
                'updatedAt': datetime.utcnow()
            })
            
            logging.info(f"Removed token {token_id} from {universe_name} universe")
            return True
            
        except Exception as e:
            logging.error(f"Error removing token from {universe_name} universe: {e}")
            return False
    
    async def get_universe_stats(self, universe_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific universe.
        
        Args:
            universe_name: One of 'market', 'watchlist', or 'portfolio'
            
        Returns:
            Dictionary with universe statistics
        """
        try:
            collection_name = f"{universe_name}Universe"
            
            # Get all documents
            all_docs = list(self.db.collection(collection_name).stream())
            active_docs = []
            for doc in all_docs:
                doc_data = doc.to_dict()
                if doc_data and doc_data.get('include', False):
                    active_docs.append(doc)
            
            stats = {
                'universe': universe_name,
                'total_tokens': len(all_docs),
                'active_tokens': len(active_docs),
                'update_frequency_minutes': DEFAULT_FREQUENCIES.get(universe_name, 60),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Add universe-specific stats
            if universe_name == MARKET_UNIVERSE:
                stats['purpose'] = 'Market trends and macro-level metrics'
                stats['target_count'] = '100-500 tokens'
                stats['apis'] = ['CoinGecko', 'LunarCrush']
                
            elif universe_name == WATCHLIST_UNIVERSE:
                stats['purpose'] = 'ML feature engineering and prediction'
                stats['target_count'] = '<=100 tokens'
                stats['apis'] = ['CoinGecko', 'Moralis', 'Covalent', 'LunarCrush', 'CoinMarketCal', 'CryptoPanic']
                
            elif universe_name == PORTFOLIO_UNIVERSE:
                stats['purpose'] = 'Active trading positions'
                stats['target_count'] = '<10 tokens'
                stats['apis'] = ['CoinGecko', 'Coinbase', 'Moralis']
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting {universe_name} universe stats: {e}")
            return {'error': str(e)}
    
    async def populate_market_universe(self, top_n: int = 100) -> int:
        """
        Populate market universe with top N tokens by market cap.
        
        Args:
            top_n: Number of top tokens to include (default: 100)
            
        Returns:
            Number of tokens added
        """
        try:
            # This would typically call CoinGecko API to get top tokens
            # For now, we'll create some example tokens
            example_tokens = [
                {
                    'tokenId': 'bitcoin',
                    'symbol': 'btc',
                    'name': 'Bitcoin',
                    'marketCapRank': 1,
                    'include': True
                },
                {
                    'tokenId': 'ethereum', 
                    'symbol': 'eth',
                    'name': 'Ethereum',
                    'marketCapRank': 2,
                    'include': True
                },
                {
                    'tokenId': 'binancecoin',
                    'symbol': 'bnb', 
                    'name': 'BNB',
                    'marketCapRank': 3,
                    'include': True
                }
            ]
            
            count = 0
            for token in example_tokens:
                if await self.add_token_to_universe(MARKET_UNIVERSE, token):
                    count += 1
                    
            logging.info(f"Populated market universe with {count} tokens")
            return count
            
        except Exception as e:
            logging.error(f"Error populating market universe: {e}")
            return 0
    
    async def sync_watchlist_universe_from_ui(self) -> int:
        """
        Sync watchlist universe with tokens managed in the UI.
        Pulls from existing 'tokens' collection where active=True.
        
        Returns:
            Number of tokens synced
        """
        try:
            # Get active tokens from the UI watchlist (tokens collection)
            active_watchlist = self.db.collection('tokens').where('active', '==', True).stream()
            
            count = 0
            for doc in active_watchlist:
                token_data = doc.to_dict()
                
                # Convert to universe format
                universe_token = {
                    'tokenId': token_data.get('symbol', '').lower(),
                    'symbol': token_data.get('symbol', '').lower(), 
                    'name': token_data.get('name', ''),
                    'coingecko_id': token_data.get('coingecko_id', ''),
                    'priority': 'high',  # UI-managed tokens get high priority
                    'include': True,
                    'source': 'ui_watchlist',
                    'last_synced': datetime.utcnow()
                }
                
                if await self.add_token_to_universe(WATCHLIST_UNIVERSE, universe_token):
                    count += 1
            
            logging.info(f"Synced {count} tokens from UI watchlist to Watchlist Universe")
            return count
            
        except Exception as e:
            logging.error(f"Error syncing watchlist universe from UI: {e}")
            return 0

    async def sync_portfolio_universe_from_positions(self) -> int:
        """
        Sync portfolio universe with actively held crypto positions.
        Pulls from existing 'portfolio' collection for positions with quantity > 0.
        
        Returns:
            Number of positions synced
        """
        try:
            # Get all portfolio documents (user portfolios)
            portfolio_docs = self.db.collection('portfolio').stream()
            
            active_positions = set()
            
            for portfolio_doc in portfolio_docs:
                portfolio_data = portfolio_doc.to_dict()
                positions = portfolio_data.get('positions', [])
                
                # Find positions with actual holdings (quantity > 0)
                for position in positions:
                    if position.get('quantity', 0) > 0:
                        symbol = position.get('symbol', '').lower()
                        if symbol:
                            active_positions.add((
                                symbol,
                                position.get('name', ''),
                                position.get('quantity', 0),
                                position.get('avg_entry', 0)
                            ))
            
            count = 0
            for symbol, name, quantity, avg_entry in active_positions:
                universe_token = {
                    'tokenId': symbol,
                    'symbol': symbol,
                    'name': name,
                    'quantity': quantity,
                    'avgEntry': avg_entry,
                    'include': True,
                    'source': 'active_position',
                    'last_synced': datetime.utcnow()
                }
                
                if await self.add_token_to_universe(PORTFOLIO_UNIVERSE, universe_token):
                    count += 1
            
            logging.info(f"Synced {count} active positions to Portfolio Universe")
            return count
            
        except Exception as e:
            logging.error(f"Error syncing portfolio universe from positions: {e}")
            return 0

    async def populate_watchlist_universe(self, token_list: List[str]) -> int:
        """
        Populate watchlist universe with specified tokens (manual override).
        
        Args:
            token_list: List of token symbols to add to watchlist
            
        Returns:
            Number of tokens added
        """
        try:
            count = 0
            for symbol in token_list:
                token_data = {
                    'tokenId': symbol.lower(),
                    'symbol': symbol.lower(),
                    'name': symbol.upper(),
                    'priority': 'medium',
                    'include': True,
                    'source': 'manual',
                    'last_synced': datetime.utcnow()
                }
                
                if await self.add_token_to_universe(WATCHLIST_UNIVERSE, token_data):
                    count += 1
                    
            logging.info(f"Populated watchlist universe with {count} tokens")
            return count
            
        except Exception as e:
            logging.error(f"Error populating watchlist universe: {e}")
            return 0

# Global universe manager instance
universe_manager = UniverseManager()

# Helper functions for backward compatibility
async def get_universe_tokens(universe_name: str) -> List[str]:
    """Get token IDs from specified universe."""
    return await universe_manager.get_universe_token_ids(universe_name)

async def get_universe_symbols(universe_name: str) -> List[str]:
    """Get token symbols from specified universe."""
    return await universe_manager.get_universe_symbols(universe_name)