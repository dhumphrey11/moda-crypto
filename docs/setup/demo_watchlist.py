#!/usr/bin/env python3
"""
Watchlist Demo Script for Moda Crypto

This script demonstrates the watchlist population functionality without requiring
Firebase credentials. It shows what data would be fetched and how it would be
structured for the Firestore watchlist.

Usage:
    python demo_watchlist.py [--format json|table]
"""

import argparse
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional
import json

# Top 40 cryptocurrencies by market cap (as of 2025)
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

class WatchlistDemo:
    def __init__(self, output_format: str = "table"):
        self.output_format = output_format
        self.demo_data = []
        
    def get_market_data(self, coingecko_ids: List[str]) -> Dict[str, Dict]:
        """Fetch market data from CoinGecko API."""
        print("🔍 Fetching live market data from CoinGecko...")
        
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
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true'
            }
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                market_data.update(data)
                
                # Rate limiting - CoinGecko allows 50 calls/minute for free tier
                time.sleep(1.5)
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Warning: Failed to fetch market data for some tokens: {e}")
                # Continue with partial data
        
        print(f"✅ Fetched market data for {len(market_data)} tokens")
        return market_data
    
    def create_token_document(self, symbol: str, name: str, coingecko_id: str, 
                            market_data: Dict) -> Dict:
        """Create a token document with market data."""
        token_data = market_data.get(coingecko_id, {})
        
        doc = {
            "symbol": symbol.upper(),
            "name": name,
            "coingecko_id": coingecko_id,
            "active": True,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "market_cap": token_data.get('usd_market_cap', 0),
            "liquidity_24h": token_data.get('usd_24h_vol', 0),
            "price_usd": token_data.get('usd', 0),
            "price_change_24h": token_data.get('usd_24h_change', 0),
            "created_by": "demo_watchlist_script",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return doc
    
    def format_currency(self, value: float) -> str:
        """Format currency values for display."""
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        elif value >= 1_000:
            return f"${value/1_000:.2f}K"
        else:
            return f"${value:.2f}"
    
    def format_percentage(self, value: float) -> str:
        """Format percentage change with color indicators."""
        if value > 0:
            return f"+{value:.2f}%"
        else:
            return f"{value:.2f}%"
    
    def display_table_format(self):
        """Display data in table format."""
        print(f"\n{'='*120}")
        print(f"{'SYMBOL':<8} {'NAME':<20} {'PRICE (USD)':<12} {'24H CHANGE':<12} {'MARKET CAP':<15} {'VOLUME 24H':<15} {'COINGECKO ID':<20}")
        print(f"{'='*120}")
        
        for doc in self.demo_data:
            price = self.format_currency(doc['price_usd'])
            change = self.format_percentage(doc['price_change_24h'])
            mcap = self.format_currency(doc['market_cap'])
            volume = self.format_currency(doc['liquidity_24h'])
            
            # Color coding for price change
            change_color = "🟢" if doc['price_change_24h'] > 0 else "🔴" if doc['price_change_24h'] < 0 else "⚪"
            
            print(f"{doc['symbol']:<8} {doc['name'][:19]:<20} {price:<12} {change_color} {change:<11} {mcap:<15} {volume:<15} {doc['coingecko_id']:<20}")
    
    def display_json_format(self):
        """Display data in JSON format."""
        print("\n📋 Firestore Document Structure (JSON):")
        print("=" * 50)
        
        # Show first 3 documents as examples
        for i, doc in enumerate(self.demo_data[:3]):
            print(f"\n🪙 Document {i+1}: tokens/{doc['symbol']}")
            print(json.dumps(doc, indent=2))
        
        if len(self.demo_data) > 3:
            print(f"\n... and {len(self.demo_data) - 3} more tokens")
    
    def generate_summary_stats(self):
        """Generate and display summary statistics."""
        if not self.demo_data:
            return
            
        total_market_cap = sum(doc['market_cap'] for doc in self.demo_data if doc['market_cap'])
        total_volume = sum(doc['liquidity_24h'] for doc in self.demo_data if doc['liquidity_24h'])
        positive_changes = sum(1 for doc in self.demo_data if doc['price_change_24h'] > 0)
        negative_changes = sum(1 for doc in self.demo_data if doc['price_change_24h'] < 0)
        
        print(f"\n📊 MARKET SUMMARY")
        print(f"{'='*50}")
        print(f"🪙 Total Tokens: {len(self.demo_data)}")
        print(f"💰 Combined Market Cap: {self.format_currency(total_market_cap)}")
        print(f"📈 24h Volume: {self.format_currency(total_volume)}")
        print(f"🟢 Tokens Up: {positive_changes}")
        print(f"🔴 Tokens Down: {negative_changes}")
        print(f"⚪ Unchanged: {len(self.demo_data) - positive_changes - negative_changes}")
    
    def run_demo(self):
        """Main demo execution."""
        print("🚀 Moda Crypto Watchlist Demo")
        print("=" * 50)
        print(f"📊 Demonstrating data for {len(TOP_40_CRYPTOS)} cryptocurrencies")
        print("🌐 This shows what would be added to your Firestore watchlist")
        print()
        
        # Get market data for all tokens
        coingecko_ids = [crypto[2] for crypto in TOP_40_CRYPTOS]
        market_data = self.get_market_data(coingecko_ids)
        
        # Create demo documents
        print("\n🔨 Creating Firestore document structure...")
        for symbol, name, coingecko_id in TOP_40_CRYPTOS:
            token_doc = self.create_token_document(symbol, name, coingecko_id, market_data)
            self.demo_data.append(token_doc)
        
        print(f"✅ Generated {len(self.demo_data)} token documents")
        
        # Display results
        if self.output_format == "json":
            self.display_json_format()
        else:
            self.display_table_format()
        
        # Show summary stats
        self.generate_summary_stats()
        
        # Show what would happen with Firebase
        print(f"\n🔥 What happens with Firebase:")
        print("=" * 50)
        print("📤 Each token would be saved to: firestore.collection('tokens').doc('{symbol}')")
        print("🔄 Existing tokens would be skipped (unless using --force)")
        print("⏰ Timestamps would be recorded for tracking")
        print("🛡️  Data validation ensures required fields are present")
        
        print(f"\n💡 To actually populate your watchlist:")
        print("1. Configure Firebase credentials in backend/.env")
        print("2. Run: ./docs/setup/validate_firebase.sh")
        print("3. Run: ./docs/setup/populate_watchlist.sh --dry-run")
        print("4. Run: ./docs/setup/populate_watchlist.sh")

def main():
    parser = argparse.ArgumentParser(description='Demo the Moda Crypto watchlist population')
    parser.add_argument('--format', choices=['table', 'json'], default='table',
                       help='Output format for displaying data')
    
    args = parser.parse_args()
    
    demo = WatchlistDemo(output_format=args.format)
    demo.run_demo()

if __name__ == "__main__":
    main()