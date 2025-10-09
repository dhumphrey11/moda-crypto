#!/bin/bash

# Moda Crypto - GitHub Secrets Setup Script
# This script creates all required GitHub secrets for deployment

set -e

REPO="dhumphrey11/moda-crypto"

echo "🔐 Setting up GitHub Secrets for $REPO"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to set a secret
set_secret() {
    local name=$1
    local value=$2
    local description=$3
    
    if [ -z "$value" ] || [ "$value" == "your-api-key" ] || [ "$value" == "placeholder" ]; then
        echo -e "${YELLOW}⚠️  $name: ${description}${NC}"
        echo -e "${BLUE}   Please set this manually: gh secret set $name${NC}"
        return
    fi
    
    echo -n "Setting $name... "
    if echo "$value" | gh secret set "$name" --repo="$REPO"; then
        echo -e "${GREEN}✅${NC}"
    else
        echo -e "${RED}❌${NC}"
    fi
}

echo -e "${BLUE}📋 Setting up Firebase secrets...${NC}"

# Firebase secrets (from your current config)
set_secret "FIREBASE_PROJECT_ID" "moda-crypto" "Firebase project ID"
set_secret "FIREBASE_CLIENT_EMAIL" "firebase-adminsdk-fbsvc@moda-crypto.iam.gserviceaccount.com" "Firebase service account email"
set_secret "FIREBASE_STORAGE_BUCKET" "moda-crypto.firebasestorage.app" "Firebase storage bucket"
set_secret "FIREBASE_AUTH_DOMAIN" "moda-crypto.firebaseapp.com" "Firebase auth domain"
set_secret "FIREBASE_MESSAGING_SENDER_ID" "455022068927" "Firebase messaging sender ID"
set_secret "FIREBASE_APP_ID" "1:455022068927:web:77fab1351924344a33b20a" "Firebase app ID"

echo -e "${BLUE}📋 Setting placeholder secrets (you need to update these)...${NC}"

# Secrets that need manual configuration
set_secret "GCP_PROJECT_ID" "placeholder" "Your Google Cloud Project ID"
set_secret "GCP_SA_KEY" "placeholder" "Google Cloud Service Account JSON key (entire JSON)"
set_secret "FIREBASE_API_KEY" "your-api-key" "Firebase Web API Key (from Firebase Console)"
set_secret "FIREBASE_PRIVATE_KEY" "placeholder" "Firebase service account private key"
set_secret "BACKEND_URL" "https://placeholder.run.app" "Backend URL (set after first deployment)"

# External API keys (all need manual setup)
echo -e "${BLUE}📋 Setting external API key placeholders...${NC}"
set_secret "COINGECKO_API_KEY" "your-api-key" "CoinGecko API key"
set_secret "MORALIS_API_KEY" "your-api-key" "Moralis API key"
set_secret "COVALENT_API_KEY" "your-api-key" "Covalent API key"
set_secret "LUNARCRUSH_API_KEY" "your-api-key" "LunarCrush API key"
set_secret "COINMARKETCAL_API_KEY" "your-api-key" "CoinMarketCal API key"
set_secret "CRYPTOPANIC_API_KEY" "your-api-key" "CryptoPanic API key"
set_secret "COINBASE_API_KEY" "your-api-key" "Coinbase API key"
set_secret "COINBASE_API_SECRET" "your-api-key" "Coinbase API secret"

echo ""
echo -e "${GREEN}✅ Basic secrets setup complete!${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: You still need to manually set these critical secrets:${NC}"
echo ""
echo -e "${BLUE}1. GCP_PROJECT_ID${NC} - Your Google Cloud project ID"
echo -e "   gh secret set GCP_PROJECT_ID --repo=$REPO"
echo ""
echo -e "${BLUE}2. GCP_SA_KEY${NC} - Google Cloud Service Account JSON (entire JSON content)"
echo -e "   gh secret set GCP_SA_KEY --repo=$REPO < /path/to/service-account.json"
echo ""
echo -e "${BLUE}3. FIREBASE_API_KEY${NC} - From Firebase Console → Project Settings → Web API Key"
echo -e "   gh secret set FIREBASE_API_KEY --repo=$REPO"
echo ""
echo -e "${BLUE}4. FIREBASE_PRIVATE_KEY${NC} - From Firebase service account JSON"
echo -e "   gh secret set FIREBASE_PRIVATE_KEY --repo=$REPO"
echo ""
echo -e "${BLUE}5. External API Keys${NC} - Sign up for each service and get API keys"
echo -e "   gh secret set COINGECKO_API_KEY --repo=$REPO"
echo -e "   gh secret set MORALIS_API_KEY --repo=$REPO"
echo -e "   # ... and so on"
echo ""
echo -e "${GREEN}🚀 After setting the critical secrets, push to main branch to deploy!${NC}"
echo -e "${BLUE}   git push origin main${NC}"