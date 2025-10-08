# Development Guide

This guide helps you get started with developing and extending the Moda Crypto application.

## 🏃‍♂️ Quick Start

### Automated Setup

**Windows:**
```powershell
# Run the PowerShell setup script
.\setup.ps1
```

**macOS/Linux:**
```bash
# Run the Python setup script
python setup.py
```

### Manual Setup

1. **Install dependencies:**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   
   # Frontend
   cp frontend/.env.example frontend/.env.local
   # Edit frontend/.env.local with Firebase config
   ```

3. **Start development servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   venv\Scripts\activate  # Windows
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

## 🏗️ Architecture Overview

### Backend (FastAPI)

```
backend/app/
├── main.py              # FastAPI application entry point
├── config.py            # Environment configuration
├── firestore_client.py  # Firebase integration
├── routers/             # API endpoints
│   ├── fetch.py         # Data fetching endpoints
│   ├── compute.py       # Signal computation
│   ├── trade.py         # Paper trading
│   └── admin.py         # System administration
├── services/            # External API wrappers
│   ├── coingecko.py     # CoinGecko API
│   ├── moralis.py       # Moralis Web3 API
│   ├── covalent.py      # Covalent blockchain data
│   ├── lunarcrush.py    # Social sentiment data
│   ├── coinmarketcal.py # Market events
│   ├── cryptopanic.py   # News sentiment
│   └── coinbase.py      # Coinbase trading data
├── features/            # ML feature engineering
│   └── feature_engineer.py
├── models/              # ML training & prediction
│   ├── train.py         # Model training pipeline
│   └── predict.py       # Signal generation
└── paper_trade/         # Trading logic
    └── executor.py      # Paper trading execution
```

### Frontend (Next.js + TypeScript)

```
frontend/src/
├── pages/
│   ├── _app.tsx         # App wrapper with auth
│   ├── index.tsx        # Dashboard page
│   ├── signals.tsx      # Signals listing
│   ├── portfolio.tsx    # Portfolio view
│   └── admin.tsx        # Admin panel
├── components/
│   ├── Layout.tsx       # Main layout with navigation
│   ├── LoadingSpinner.tsx
│   ├── SignalCard.tsx   # Signal display component
│   ├── PortfolioTable.tsx
│   ├── DashboardStats.tsx
│   └── HealthPanel.tsx  # System health monitoring
├── lib/
│   ├── firebase.ts      # Firebase configuration
│   └── firestore.ts     # Data service layer
└── types/
    └── index.ts         # TypeScript type definitions
```

### Database Schema (Firestore)

```
Collections:
├── tokens/              # Cryptocurrency data
├── features/            # ML feature vectors
├── signals/             # Generated trading signals
├── trades/              # Paper trading history
├── models/              # ML model metadata
├── adminConfig/         # System configuration
├── runs/                # Processing run logs
├── events/              # System events
└── portfolio/           # Portfolio state
```

## 🔧 Key Development Workflows

### Adding a New Data Source

1. **Create service wrapper** in `backend/app/services/`:
   ```python
   # backend/app/services/your_service.py
   import asyncio
   import aiohttp
   from typing import Dict, List, Optional
   
   class YourServiceClient:
       def __init__(self, api_key: str):
           self.api_key = api_key
           self.base_url = "https://api.yourservice.com"
       
       async def fetch_data(self, symbol: str) -> Dict:
           # Implementation
           pass
   ```

2. **Add to configuration** in `backend/app/config.py`:
   ```python
   YOUR_SERVICE_API_KEY: str = Field(..., env="YOUR_SERVICE_API_KEY")
   ```

3. **Integrate in fetch router** `backend/app/routers/fetch.py`:
   ```python
   @router.post("/your-service-data")
   async def fetch_your_service_data():
       # Implementation
       pass
   ```

4. **Update feature engineering** in `backend/app/features/feature_engineer.py`

### Adding a New Frontend Component

1. **Create component** in `frontend/src/components/`:
   ```typescript
   // YourComponent.tsx
   interface YourComponentProps {
     data: SomeType;
   }
   
   const YourComponent = ({ data }: YourComponentProps) => {
     return (
       <div className="card">
         {/* Component implementation */}
       </div>
     );
   };
   
   export default YourComponent;
   ```

2. **Add types** in `frontend/src/types/index.ts`:
   ```typescript
   export interface SomeType {
     // Type definition
   }
   ```

3. **Use in pages** - import and use the component

### Adding a New API Endpoint

1. **Create endpoint** in appropriate router:
   ```python
   @router.post("/your-endpoint")
   async def your_endpoint(request: YourRequest):
       try:
           # Implementation
           result = await some_service.do_something()
           await firestore_client.store_data("collection", result)
           return {"status": "success", "data": result}
       except Exception as e:
           logger.error(f"Error in your_endpoint: {e}")
           raise HTTPException(status_code=500, detail=str(e))
   ```

2. **Add request/response models**:
   ```python
   from pydantic import BaseModel
   
   class YourRequest(BaseModel):
       param1: str
       param2: Optional[int] = None
   
   class YourResponse(BaseModel):
       status: str
       data: Dict
   ```

3. **Update frontend data service** in `frontend/src/lib/firestore.ts`

## 🧪 Testing

### Backend Testing

```bash
cd backend
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/ -v
```

### Frontend Testing

```bash
cd frontend
# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Run tests
npm test
```

## 📊 Monitoring and Debugging

### Backend Debugging

1. **Enable debug mode** in `.env`:
   ```env
   DEBUG=true
   ```

2. **Check logs** in the terminal running the backend

3. **Use API docs** at http://localhost:8000/docs for testing endpoints

4. **Firebase Console** for database operations

### Frontend Debugging

1. **Browser DevTools** for console errors and network requests

2. **React DevTools** extension for component debugging

3. **Firebase DevTools** for Firestore operations

## 🚀 Deployment

### Backend to Google Cloud Run

```bash
cd backend
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/moda-crypto-backend
gcloud run deploy moda-crypto-backend \
  --image gcr.io/YOUR_PROJECT_ID/moda-crypto-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Frontend to Firebase Hosting

```bash
cd frontend
npm run build
npm run export
firebase deploy --only hosting
```

## 🔧 Configuration Management

### Environment Variables

**Backend (.env):**
- Firebase service account credentials
- External API keys (CoinGecko, Moralis, etc.)
- CORS origins
- Debug settings

**Frontend (.env.local):**
- Firebase client configuration
- Backend API URL
- Feature flags

### Firebase Configuration

1. **Firestore Rules:**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /{document=**} {
         allow read, write: if request.auth != null;
       }
     }
   }
   ```

2. **Security considerations:**
   - Use Firebase Authentication
   - Implement proper access controls
   - Validate all inputs
   - Rate limit API calls

## 📈 Performance Optimization

### Backend Optimization

1. **Async operations** for external API calls
2. **Connection pooling** for database connections
3. **Caching** for frequently accessed data
4. **Rate limiting** for external APIs

### Frontend Optimization

1. **Code splitting** with Next.js dynamic imports
2. **Image optimization** with Next.js Image component
3. **Data caching** with SWR or React Query
4. **Lazy loading** for components

## 🤝 Contributing Guidelines

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Follow coding standards**: Use TypeScript, proper error handling
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Submit a pull request**

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict TypeScript, proper interfaces
- **React**: Functional components with hooks
- **Styling**: Tailwind CSS classes

## 📞 Getting Help

1. **Check the logs** first for error messages
2. **Review API documentation** at `/docs`
3. **Check Firebase Console** for database issues
4. **Verify environment variables** are set correctly
5. **Test API endpoints** individually

Common debugging commands:
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend build
cd frontend && npm run build

# Check Python dependencies
cd backend && pip list

# Check Node.js dependencies
cd frontend && npm list
```