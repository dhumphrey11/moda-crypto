# Moda Crypto - Personal Crypto Signal & Paper Trading App

A complete mono-repo application for crypto signal generation and paper trading, built with FastAPI backend and Next.js frontend. Features real-time data integration, ML-powered signals, and automated paper trading with comprehensive monitoring.

## 🏗️ Architecture

```
moda-crypto/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── routers/  # API endpoints
│   │   ├── services/ # External API wrappers
│   │   ├── features/ # Feature engineering
│   │   ├── models/   # ML training & prediction
│   │   └── paper_trade/ # Trading logic
│   └── models/       # Saved ML models
├── frontend/         # Next.js TypeScript app
│   ├── pages/        # App pages
│   ├── components/   # React components
│   └── lib/          # Utilities & Firebase
├── docs/             # Documentation & Setup Scripts
│   ├── setup/        # Automated setup scripts
│   └── guides/       # Development & deployment guides
└── infra/            # Infrastructure & CI/CD
    ├── github-actions/
    └── cron/
```

## � Documentation

Comprehensive setup and development guides are located in the [`docs/`](docs/) folder:

- **Setup Scripts**: [`docs/setup/`](docs/setup/) - Automated setup for all platforms
- **Development Guide**: [`docs/guides/DEVELOPMENT.md`](docs/guides/DEVELOPMENT.md) - Detailed development workflow  
- **Deployment Guide**: [`docs/guides/FIREBASE_PRODUCTION_GUIDE.md`](docs/guides/FIREBASE_PRODUCTION_GUIDE.md) - Production deployment
- **API Keys Guide**: [`docs/setup/api-keys-guide.sh`](docs/setup/api-keys-guide.sh) - Interactive API setup
- **Secrets Guide**: [`docs/guides/SECRETS_REQUIRED.md`](docs/guides/SECRETS_REQUIRED.md) - Required environment variables

## �🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Firebase project with Firestore and Storage enabled
- GCP project for Cloud Run deployment

### Local Development Setup

1. **Automated setup (recommended):**
   ```bash
   git clone <your-repo>
   cd moda-crypto
   
   # For macOS/Linux:
   python docs/setup/setup.py
   
   # For Windows:
   powershell -ExecutionPolicy Bypass -File docs/setup/setup.ps1
   ```

2. **Manual setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and Firebase credentials
   # Use docs/setup/api-keys-guide.sh for interactive API key setup
   ```

2. **Backend setup:**
   ```bash
   cd backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```

3. **Frontend setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application:**
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

## 📊 Firestore Collections Schema

### Core Collections

- **tokens**: `{ symbol, name, coingecko_id, market_cap, liquidity_24h }`
- **features**: `{ token_id, timestamp, price_change_24h, volume_24h, rsi, macd, social_sentiment, on_chain_volume }`
- **signals**: `{ token_id, timestamp, ml_prob, rule_score, sentiment_score, event_score, composite_score, action }`
- **trades**: `{ signal_id, token_id, action, quantity, price, timestamp, status, pnl }`
- **portfolio**: `{ token_id, quantity, avg_cost, current_value, pnl, last_updated }`
- **models**: `{ model_id, version, accuracy, training_date, storage_path }`
- **adminConfig**: `{ ml_weight, rule_weight, sentiment_weight, event_weight, min_composite_score }`
- **runs**: `{ service, timestamp, status, count, duration }`
- **events**: `{ token_id, event_type, impact_score, date, description }`

## 🔧 Available Commands

### Backend
```bash
# Development
python -m uvicorn app.main:app --reload

# Docker
docker build -t moda-crypto-backend ./backend
docker run -p 8000:8000 moda-crypto-backend

# Manual operations
python -m app.models.train        # Train new model
python -m app.features.feature_engineer  # Generate features
```

### Frontend
```bash
npm run dev          # Development server
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Lint code
```

## 📅 Cron Jobs Setup

The system requires periodic execution of data fetching and signal generation:

1. **Setup Cloud Scheduler (recommended)** or use the provided cron examples in [`infra/cron/cronjobs.txt`](infra/cron/cronjobs.txt)

2. **Key endpoints to schedule:**
   - Data fetching: Every 30 minutes
   - Signal computation: Every hour
   - Paper trading: Every hour (after signals)
   - Model retraining: Weekly

## 🚢 Deployment

### Backend (Cloud Run)

1. **Setup GitHub Secrets:**
   ```
   GCP_PROJECT_ID
   GCP_SA_KEY (base64 encoded service account JSON)
   FIREBASE_PROJECT_ID
   FIREBASE_PRIVATE_KEY
   FIREBASE_CLIENT_EMAIL
   ```

2. **Deploy:**
   ```bash
   # Automatic via GitHub Actions on push to main
   # Or manual:
   gcloud run deploy moda-crypto-backend \
     --image gcr.io/$PROJECT_ID/moda-crypto-backend \
     --platform managed \
     --region us-central1
   ```

### Frontend (Firebase Hosting)

1. **Setup Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   firebase login
   firebase init hosting
   ```

2. **Deploy:**
   ```bash
   # Automatic via GitHub Actions
   # Or manual:
   npm run build
   firebase deploy --only hosting
   ```

## 🔐 Security Notes

- **Never commit `.env` files or service account keys**
- Use GCP Secret Manager for production secrets
- Enable Firebase Security Rules for Firestore
- Set up proper CORS for your domain
- Use GitHub Secrets for CI/CD credentials

## 🔍 System Health Monitoring

The system includes built-in health monitoring:

- `/health` endpoint aggregates system status
- `runs` collection tracks all service executions
- Frontend displays system health dashboard
- Failed runs trigger alerts (TODO: implement notifications)

## 🧠 ML Model Pipeline

1. **Feature Engineering**: Combines market, on-chain, and social data
2. **Training**: XGBoost model trained on historical signals
3. **Prediction**: Generates probability scores for potential trades
4. **Signal Generation**: Combines ML with rule-based and sentiment scoring
5. **Paper Trading**: Executes trades based on composite scores ≥ 0.85

## � Additional Documentation

- **[Complete Documentation Index](docs/README.md)** - Overview of all documentation
- **[Development Workflow](docs/guides/DEVELOPMENT.md)** - Detailed development setup and workflow  
- **[Production Deployment](docs/guides/FIREBASE_PRODUCTION_GUIDE.md)** - Complete deployment guide
- **[Refactoring History](docs/guides/REFACTORING_SUMMARY.md)** - Project evolution and changes
- **[Setup Scripts](docs/setup/)** - Automated setup for all platforms

## �📝 Development Notes

### TODO: Production Improvements

- [ ] Implement comprehensive error handling and retries
- [ ] Add rate limiting for external APIs  
- [ ] Set up proper logging with structured logs
- [ ] Add unit and integration tests
- [ ] Implement notification system for alerts
- [ ] Add data validation and schema enforcement
- [ ] Optimize Firestore queries and indexing
- [ ] Add monitoring and alerting (Datadog, New Relic)
- [ ] Implement backup and disaster recovery
- [ ] Add API authentication for backend endpoints

### API Rate Limits

- CoinGecko: 10-50 calls/minute (depends on plan)
- Moralis: 25 req/second (free tier)
- LunarCrush: 1000 req/month (free tier)
- CoinMarketCal: 333 req/day (free tier)

### Cost Considerations

- Firestore: ~$0.06 per 100K reads
- Cloud Run: Pay per request + CPU time
- Firebase Storage: $0.026/GB/month
- Consider implementing data retention policies

## 🆘 Troubleshooting

### Common Issues

1. **Firebase Authentication fails:**
   - Check service account key format
   - Verify project ID matches
   - Ensure Firestore is enabled

2. **API rate limits exceeded:**
   - Check service logs in `runs` collection
   - Implement exponential backoff
   - Consider upgrading API plans

3. **Model training fails:**
   - Check feature data availability
   - Verify Firebase Storage permissions
   - Monitor memory usage during training

### Debug Commands

```bash
# Check backend logs
docker logs <container-id>

# Test Firestore connection
python -c "from app.firestore_client import db; print(db)"

# Verify API keys
curl http://localhost:8000/health
```

## 📄 License

MIT License - Personal use only. See LICENSE file for details.

## 🤝 Contributing

This is a personal project. Fork and customize for your own use cases.

---

**⚠️ Disclaimer**: This is for educational and personal use only. Not financial advice. Paper trading only - no real money involved.