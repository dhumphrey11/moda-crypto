#!/bin/bash

# External API Keys Setup Guide
# This script helps you get API keys for external services

echo "🔑 External API Keys Setup Guide"
echo "================================"
echo ""

echo "📋 Here are the services you need to sign up for:"
echo ""

# CoinGecko
echo "1️⃣ CoinGecko API"
echo "   🌐 Website: https://coingecko.com/api"
echo "   📝 Sign up for free account"
echo "   🔑 Get API key from dashboard"
echo "   💡 Free tier: 30 calls/minute"
echo "   💰 Pro plan: \$199/month for higher limits"
echo ""

# Moralis
echo "2️⃣ Moralis Web3 API"
echo "   🌐 Website: https://moralis.io"
echo "   📝 Sign up for free account"
echo "   🔑 Get API key from admin panel"
echo "   💡 Free tier: 40k requests/month"
echo ""

# Covalent
echo "3️⃣ Covalent API"
echo "   🌐 Website: https://covalenthq.com"
echo "   📝 Sign up for free account"
echo "   🔑 Get API key from dashboard"
echo "   💡 Free tier: 1M requests/month"
echo ""

# LunarCrush
echo "4️⃣ LunarCrush API"
echo "   🌐 Website: https://lunarcrush.com/developers"
echo "   📝 Sign up for account"
echo "   🔑 Get API key from developer section"
echo "   💡 Paid service: starts at \$99/month"
echo ""

# CoinMarketCal
echo "5️⃣ CoinMarketCal API"
echo "   🌐 Website: https://coinmarketcal.com/api"
echo "   📝 Sign up for free account"
echo "   🔑 Get API key from profile"
echo "   💡 Free tier: 1000 requests/month"
echo ""

# CryptoPanic
echo "6️⃣ CryptoPanic API"
echo "   🌐 Website: https://cryptopanic.com/developers/api"
echo "   📝 Sign up for free account"
echo "   🔑 Get API key from developer panel"
echo "   💡 Free tier: 1000 requests/day"
echo ""

# Coinbase
echo "7️⃣ Coinbase Advanced Trade API (Optional)"
echo "   🌐 Website: https://developer.coinbase.com"
echo "   📝 Coinbase Pro/Advanced account required"
echo "   🔑 Generate API credentials"
echo "   💡 Used for live trading (paper trading works without)"
echo ""

echo "🚀 Quick setup commands (run after getting API keys):"
echo ""
echo "gh secret set COINGECKO_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set MORALIS_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set COVALENT_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set LUNARCRUSH_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set COINMARKETCAL_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set CRYPTOPANIC_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set COINBASE_API_KEY --repo=dhumphrey11/moda-crypto"
echo "gh secret set COINBASE_API_SECRET --repo=dhumphrey11/moda-crypto"
echo ""

echo "💡 Pro tip: Start with the free APIs first!"
echo "   - CoinGecko (free)"
echo "   - Covalent (free)"
echo "   - CryptoPanic (free)"
echo "   - CoinMarketCal (free)"
echo ""
echo "   Skip the paid ones initially:"
echo "   - LunarCrush (paid)"
echo "   - Coinbase (optional)"
echo ""

echo "🎯 Minimum setup to get started:"
echo "   1. Get CoinGecko API key (free)"
echo "   2. Get CryptoPanic API key (free)"
echo "   3. Deploy and test!"