#!/bin/bash

# Interactive API Key Setup for Moda Crypto
# This script helps you get and configure all external API keys

echo "🔑 Interactive API Key Setup for Moda Crypto"
echo "============================================="
echo ""

# Function to open URL and prompt for API key
setup_api() {
    local service_name="$1"
    local website="$2"
    local secret_name="$3"
    local description="$4"
    local is_free="$5"
    
    echo "🌐 Setting up $service_name API"
    echo "   Website: $website"
    echo "   Secret: $secret_name"
    echo "   $description"
    
    if [ "$is_free" = "true" ]; then
        echo "   💚 FREE SERVICE"
    else
        echo "   💰 PAID SERVICE"
    fi
    
    echo ""
    echo "   Opening $website in your browser..."
    open "$website"
    
    echo ""
    read -p "   After getting your API key, paste it here (or press Enter to skip): " api_key
    
    if [ -n "$api_key" ]; then
        echo "   Setting GitHub secret $secret_name..."
        echo "$api_key" | gh secret set "$secret_name" --repo=dhumphrey11/moda-crypto
        echo "   ✅ $service_name API key configured!"
    else
        echo "   ⏭️  Skipped $service_name (you can add it later)"
    fi
    
    echo ""
}

# Check if GitHub CLI is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Please authenticate with GitHub CLI first:"
    echo "   gh auth login"
    exit 1
fi

echo "🎯 We'll set up the APIs in order of priority (free ones first)"
echo ""

# 1. CoinGecko (Free, most important)
setup_api "CoinGecko" "https://www.coingecko.com/en/api/pricing" "COINGECKO_API_KEY" "Free tier: 30 calls/minute" "true"

# 2. CryptoPanic (Free)
setup_api "CryptoPanic" "https://cryptopanic.com/developers/api/" "CRYPTOPANIC_API_KEY" "Free tier: 1000 requests/day" "true"

# 3. Covalent (Free)  
setup_api "Covalent" "https://www.covalenthq.com/platform/auth/register/" "COVALENT_API_KEY" "Free tier: 1M requests/month" "true"

# 4. CoinMarketCal (Free)
setup_api "CoinMarketCal" "https://coinmarketcal.com/en/api" "COINMARKETCAL_API_KEY" "Free tier: 1000 requests/month" "true"

# 5. Moralis (Free)
setup_api "Moralis" "https://admin.moralis.io/register" "MORALIS_API_KEY" "Free tier: 40k requests/month" "true"

echo "🎉 Free APIs setup complete! You can deploy now with these."
echo ""

# Ask about paid services
read -p "💰 Do you want to set up the paid services? (y/N): " setup_paid

if [[ $setup_paid =~ ^[Yy]$ ]]; then
    # 6. LunarCrush (Paid)
    setup_api "LunarCrush" "https://lunarcrush.com/developers/docs" "LUNARCRUSH_API_KEY" "Paid service: starts at \$99/month" "false"
    
    # 7. Coinbase (Optional)
    echo "🏦 Coinbase Advanced Trade API Setup"
    echo "   This requires a Coinbase Pro/Advanced account"
    echo "   Used for live trading (paper trading works without it)"
    echo ""
    read -p "   Do you want to set up Coinbase API? (y/N): " setup_coinbase
    
    if [[ $setup_coinbase =~ ^[Yy]$ ]]; then
        setup_api "Coinbase" "https://developer.coinbase.com/api/v2" "COINBASE_API_KEY" "For live trading" "false"
        
        echo "   📝 Coinbase also requires an API SECRET"
        read -p "   Enter your Coinbase API Secret: " coinbase_secret
        if [ -n "$coinbase_secret" ]; then
            echo "$coinbase_secret" | gh secret set "COINBASE_API_SECRET" --repo=dhumphrey11/moda-crypto
            echo "   ✅ Coinbase API Secret configured!"
        fi
    fi
fi

echo ""
echo "🎉 API Key Setup Complete!"
echo "========================="
echo ""

# Show current secrets status
echo "📊 Current GitHub Secrets:"
gh secret list --repo=dhumphrey11/moda-crypto | grep -E "(COINGECKO|MORALIS|COVALENT|LUNARCRUSH|COINMARKETCAL|CRYPTOPANIC|COINBASE)" || echo "   No external API secrets found"

echo ""
echo "🚀 Ready to deploy!"
echo "   Run: git push origin main"
echo ""
echo "💡 You can add more API keys later by running:"
echo "   echo 'your_key' | gh secret set SECRET_NAME --repo=dhumphrey11/moda-crypto"