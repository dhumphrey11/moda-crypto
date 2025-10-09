#!/usr/bin/env python3
"""
Populate Watchlist Script for Moda Crypto

This script adds the top 40 most popular cryptocurrencies to the Firestore watchlist.
It uses the CoinGecko API to fetch current market data and populates the watchlist
with accurate information including market cap and 24h volume data.

Usage:
    python populate_watchlist.py [--dry-run] [--force]

Options:
    --dry-run    Show what would be added without making changes
    --force      Overwrite existing tokens in the watchlist
    
Requirements:
    - Firebase credentials configured in backend/.env
    - Backend dependencies installed (run: pip install -r backend/requirements.txt)
    - Internet connection for CoinGecko API calls
"""

import sys
import os
import argparse
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional

# Add backend to path for imports
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_path)

# Firebase imports will be done conditionally

# Top 40 cryptocurrencies by market cap (as of 2025)
# Format: (symbol, name, coingecko_id)
TOP_40_CRYPTOS = [
    ("BTC", "Bitcoin", "bitcoin"),
    ("ETH", "Ethereum", "ethereum"),
    ("USDT", "Tether", "tether"),
    ("BNB", "BNB", "binancecoin"),
    ("SOL", "Solana", "solana"),
    ("USDC", "USD Coin", "usd-coin"),
    ("XRP", "Ripple", "ripple"),
    ("DOGE", "Dogecoin", "dogecoin"),
    ("TON", "Toncoin", "the-open-network"),
    ("ADA", "Cardano", "cardano"),
    ("SHIB", "Shiba Inu", "shiba-inu"),
    ("AVAX", "Avalanche", "avalanche-2"),
    ("TRX", "TRON", "tron"),
    ("DOT", "Polkadot", "polkadot"),
    ("BCH", "Bitcoin Cash", "bitcoin-cash"),
    ("LINK", "Chainlink", "chainlink"),
    ("NEAR", "NEAR Protocol", "near"),
    ("MATIC", "Polygon", "matic-network"),
    ("ICP", "Internet Computer", "internet-computer"),
    ("UNI", "Uniswap", "uniswap"),
    ("LTC", "Litecoin", "litecoin"),
    ("PEPE", "Pepe", "pepe"),
    ("LEO", "LEO Token", "leo-token"),
    ("DAI", "Dai", "dai"),
    ("ETC", "Ethereum Classic", "ethereum-classic"),
    ("HBAR", "Hedera", "hedera-hashgraph"),
    ("XMR", "Monero", "monero"),
    ("RENDER", "Render Token", "render-token"),
    ("KASPA", "Kaspa", "kaspa"),
    ("ARB", "Arbitrum", "arbitrum"),
    ("VET", "VeChain", "vechain"),
    ("XLM", "Stellar", "stellar"),
    ("FIL", "Filecoin", "filecoin"),
    ("ATOM", "Cosmos", "cosmos"),
    ("CRO", "Cronos", "crypto-com-chain"),
    ("MKR", "Maker", "maker"),
    ("OP", "Optimism", "optimism"),
    ("IMX", "Immutable X", "immutable-x"),
    ("INJ", "Injective", "injective-protocol"),
    ("MANTLE", "Mantle", "mantle"),
]

class WatchlistPopulator:
    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.db = None
        
    def init_firestore(self):
        """Initialize Firestore connection using existing app configuration."""
        try:
            # Import Firebase modules only when needed
            try:
                from app.firestore_client import init_db
            except ImportError as e:
                print(f"❌ Error importing backend modules: {e}")
                print("Make sure you're running this from the project root and backend dependencies are installed.")
                return False
                
            print("🔥 Initializing Firestore connection...")
            self.db = init_db()
            
            # Test the connection
            test_collection = self.db.collection('tokens')
            print("✓ Firestore connection established successfully")
            print("✓ Database client ready for operations")
            return True
            
        except Exception as e:
            print("❌ Failed to connect to Firestore")
            print("━" * 50)
            error_msg = str(e).lower()
            
            if "validation" in error_msg and "firebase" in error_msg:
                print("🔍 Firebase credential validation failed.")
                print()
                print("The app's Firebase initialization detected invalid credentials.")
                print("This usually means the credentials in backend/.env need to be fixed.")
                print()
                print("💡 The app will try to handle different credential formats,")
                print("   but you may need proper service account credentials.")
                
            elif "credential" in error_msg or "auth" in error_msg:
                print("🔑 Firebase authentication failed.")
                print()
                print("Please verify your Firebase service account has:")
                print("• Proper permissions for Firestore")
                print("• Valid project ID and credentials")
                
            elif "project" in error_msg:
                print("📁 Firebase project configuration issue.")
                print()
                print("Please verify:")
                print("• FIREBASE_PROJECT_ID matches your Firebase project")
                print("• Project exists and Firestore is enabled")
                
            else:
                print(f"Unexpected error: {e}")
                
            print()
            print("🛠️  To resolve:")
            print("1. Check backend/.env has all Firebase variables")
            print("2. Run: ./docs/setup/validate_firebase.sh")
            print("3. Get proper credentials from Firebase Console")
            print("━" * 50)
            return False
    
    def get_market_data(self, coingecko_ids: List[str]) -> Dict[str, Dict]:
        """Fetch market data from CoinGecko API."""
        print("Fetching market data from CoinGecko...")
        
        # Split into chunks of 100 (CoinGecko API limit)
        chunks = [coingecko_ids[i:i+100] for i in range(0, len(coingecko_ids), 100)]
        market_data = {}
        
        for chunk in chunks:
            ids_string = ','.join(chunk)
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ids_string,
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                market_data.update(data)
                
                # Rate limiting - CoinGecko allows 50 calls/minute for free tier
                time.sleep(1.5)
                
            except requests.exceptions.RequestException as e:
                print(f"Warning: Failed to fetch market data for chunk: {e}")
                # Continue without market data for this chunk
        
        print(f"✓ Fetched market data for {len(market_data)} tokens")
        return market_data
    
    def check_existing_tokens(self) -> set:
        """Check which tokens already exist in the watchlist."""
        if self.dry_run:
            return set()
            
        try:
            tokens_ref = self.db.collection('tokens')
            docs = tokens_ref.get()
            existing = {doc.id for doc in docs}
            print(f"Found {len(existing)} existing tokens in watchlist")
            return existing
        except Exception as e:
            print(f"Warning: Failed to check existing tokens: {e}")
            return set()
    
    def create_token_document(self, symbol: str, name: str, coingecko_id: str, 
                            market_data: Dict) -> Dict:
        """Create a token document with market data."""
        token_data = market_data.get(coingecko_id, {})
        
        doc = {
            "symbol": symbol.upper(),
            "name": name,
            "coingecko_id": coingecko_id,
            "active": True,
            "last_updated": datetime.utcnow(),
            "market_cap": token_data.get('usd_market_cap', 0),
            "liquidity_24h": token_data.get('usd_24h_vol', 0),
            "price_usd": token_data.get('usd', 0),
            "created_by": "populate_watchlist_script",
            "created_at": datetime.utcnow()
        }
        
        return doc
    
    def add_tokens_to_watchlist(self) -> Dict[str, int]:
        """Add tokens to the watchlist."""
        results = {
            'added': 0,
            'skipped': 0,
            'updated': 0,
            'failed': 0
        }
        
        # Get market data for all tokens
        coingecko_ids = [crypto[2] for crypto in TOP_40_CRYPTOS]
        market_data = self.get_market_data(coingecko_ids)
        
        # Check existing tokens
        existing_tokens = self.check_existing_tokens()
        
        print(f"\n{'='*60}")
        print(f"{'TOKEN':<8} {'NAME':<20} {'STATUS':<12} {'ACTION'}")
        print(f"{'='*60}")
        
        for symbol, name, coingecko_id in TOP_40_CRYPTOS:
            symbol_upper = symbol.upper()
            
            try:
                # Check if token already exists
                if symbol_upper in existing_tokens and not self.force:
                    print(f"{symbol_upper:<8} {name[:19]:<20} {'EXISTS':<12} Skipped")
                    results['skipped'] += 1
                    continue
                
                # Create token document
                token_doc = self.create_token_document(symbol, name, coingecko_id, market_data)
                
                if self.dry_run:
                    status = "WOULD ADD" if symbol_upper not in existing_tokens else "WOULD UPDATE"
                    print(f"{symbol_upper:<8} {name[:19]:<20} {status:<12} Dry run")
                    results['added'] += 1
                else:
                    # Add to Firestore
                    self.db.collection('tokens').document(symbol_upper).set(token_doc)
                    
                    if symbol_upper in existing_tokens:
                        print(f"{symbol_upper:<8} {name[:19]:<20} {'UPDATED':<12} Force overwrite")
                        results['updated'] += 1
                    else:
                        print(f"{symbol_upper:<8} {name[:19]:<20} {'ADDED':<12} Success")
                        results['added'] += 1
                
            except Exception as e:
                print(f"{symbol_upper:<8} {name[:19]:<20} {'ERROR':<12} {str(e)[:30]}")
                results['failed'] += 1
        
        return results
    
    def run(self):
        """Main execution method."""
        print("🚀 Moda Crypto Watchlist Populator")
        print("="*50)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        if self.force:
            print("⚠️  FORCE MODE - Existing tokens will be overwritten")
        
        print(f"📊 Preparing to add {len(TOP_40_CRYPTOS)} cryptocurrencies")
        print()
        
        # Initialize Firestore
        if not self.init_firestore():
            return False
        
        # Add tokens
        results = self.add_tokens_to_watchlist()
        
        # Print summary
        print(f"\n{'='*60}")
        print("📋 SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Added: {results['added']}")
        print(f"🔄 Updated: {results['updated']}")
        print(f"⏭️  Skipped: {results['skipped']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"📊 Total Processed: {sum(results.values())}")
        
        if self.dry_run:
            print("\n💡 To actually add tokens, run without --dry-run flag")
        
        return results['failed'] == 0

def main():
    parser = argparse.ArgumentParser(description='Populate Moda Crypto watchlist with top 40 cryptocurrencies')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be added without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Overwrite existing tokens in the watchlist')
    parser.add_argument('--no-firebase', action='store_true',
                       help='Run without Firebase (demonstration mode)')
    
    args = parser.parse_args()
    
    if args.no_firebase:
        # Import and run the demo version instead
        import subprocess
        demo_script = os.path.join(os.path.dirname(__file__), 'demo_watchlist.py')
        cmd = [sys.executable, demo_script, '--format', 'table']
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    
    populator = WatchlistPopulator(dry_run=args.dry_run, force=args.force)
    success = populator.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()