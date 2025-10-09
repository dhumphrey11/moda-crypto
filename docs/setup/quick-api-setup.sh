#!/bin/bash

# Quick Essential API Setup - Just the free ones needed to start
echo "🚀 Quick Essential API Setup"
echo "============================"
echo ""
echo "Setting up the 2 most important FREE APIs to get you started:"
echo ""

# Check GitHub CLI
if ! gh auth status &> /dev/null; then
    echo "❌ Please authenticate with GitHub CLI first: gh auth login"
    exit 1
fi

# 1. CoinGecko - Most important for price data
echo "1️⃣ CoinGecko API (FREE - 30 calls/minute)"
echo "   🌐 Opening https://www.coingecko.com/en/api/pricing"
open "https://www.coingecko.com/en/api/pricing"
echo ""
echo "   Steps:"
echo "   1. Sign up for free account"
echo "   2. Go to Developer Dashboard"
echo "   3. Copy your API key"
echo ""
read -p "   Paste your CoinGecko API key here: " coingecko_key

if [ -n "$coingecko_key" ]; then
    echo "$coingecko_key" | gh secret set COINGECKO_API_KEY --repo=dhumphrey11/moda-crypto
    echo "   ✅ CoinGecko API configured!"
else
    echo "   ⚠️  No CoinGecko key provided - this is important for price data!"
fi

echo ""

# 2. CryptoPanic - News and sentiment
echo "2️⃣ CryptoPanic API (FREE - 1000 calls/day)"
echo "   🌐 Opening https://cryptopanic.com/developers/api/"
open "https://cryptopanic.com/developers/api/"
echo ""
echo "   Steps:"
echo "   1. Sign up for free account"
echo "   2. Go to API section"
echo "   3. Copy your API key"
echo ""
read -p "   Paste your CryptoPanic API key here: " cryptopanic_key

if [ -n "$cryptopanic_key" ]; then
    echo "$cryptopanic_key" | gh secret set CRYPTOPANIC_API_KEY --repo=dhumphrey11/moda-crypto
    echo "   ✅ CryptoPanic API configured!"
else
    echo "   ⚠️  No CryptoPanic key provided - this provides news data!"
fi

echo ""
echo "🎉 Essential APIs configured!"
echo ""

# Show status
echo "📊 Your current external API secrets:"
gh secret list --repo=dhumphrey11/moda-crypto | grep -E "(COINGECKO|CRYPTOPANIC)" || echo "   None configured yet"

echo ""
echo "✅ Ready to deploy with basic functionality!"
echo "🚀 Run: git push origin main"
echo ""
echo "💡 Want more APIs? Run: ./setup-apis.sh"