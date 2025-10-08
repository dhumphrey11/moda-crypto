# Required GitHub Secrets

This document lists all the secrets required for the GitHub Actions workflows to deploy successfully.

## Backend Deployment (Cloud Run)

### Google Cloud Platform
- `GCP_PROJECT_ID` - Google Cloud Project ID
- `GCP_SA_KEY` - Service Account JSON key for Google Cloud authentication

### Firebase Admin (Backend)
- `FIREBASE_PROJECT_ID` - Firebase project ID
- `FIREBASE_CLIENT_EMAIL` - Firebase service account email
- `FIREBASE_PRIVATE_KEY` - Firebase service account private key (JSON format)
- `FIREBASE_STORAGE_BUCKET` - Firebase storage bucket name

### API Keys (Backend)
- `COINGECKO_API_KEY` - CoinGecko API key
- `MORALIS_API_KEY` - Moralis API key
- `COVALENT_API_KEY` - Covalent API key  
- `LUNARCRUSH_API_KEY` - LunarCrush API key
- `COINMARKETCAL_API_KEY` - CoinMarketCal API key
- `CRYPTOPANIC_API_KEY` - CryptoPanic API key
- `COINBASE_API_KEY` - Coinbase Pro API key
- `COINBASE_API_SECRET` - Coinbase Pro API secret
- `COINBASE_PASSPHRASE` - Coinbase Pro API passphrase

## Frontend Deployment (Firebase Hosting)

### Firebase Client (Frontend)
- `FIREBASE_API_KEY` - Firebase web API key
- `FIREBASE_AUTH_DOMAIN` - Firebase auth domain
- `FIREBASE_PROJECT_ID` - Firebase project ID (same as backend)
- `FIREBASE_STORAGE_BUCKET` - Firebase storage bucket (same as backend)
- `FIREBASE_MESSAGING_SENDER_ID` - Firebase messaging sender ID
- `FIREBASE_APP_ID` - Firebase web app ID

### Firebase Deployment
- `FIREBASE_SERVICE_ACCOUNT` - Firebase service account JSON for deployment

### Other
- `BACKEND_URL` - Backend service URL (set after backend deployment)

## Setup Notes

1. The `FIREBASE_PRIVATE_KEY` should be in JSON format from the Firebase service account key
2. All Firebase secrets (FIREBASE_PROJECT_ID, FIREBASE_STORAGE_BUCKET) should be consistent between frontend and backend
3. The `BACKEND_URL` should point to your deployed Cloud Run service (e.g., https://moda-crypto-backend-abc123-uc.a.run.app)
4. API keys should be kept secure and rotated regularly