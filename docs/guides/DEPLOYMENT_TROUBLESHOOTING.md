# GitHub Actions Deployment Error Troubleshooting Guide

## 🔍 How to Check Deployment Logs

### 1. Access GitHub Actions
1. Go to: https://github.com/dhumphrey11/moda-crypto/actions
2. Look for recent workflow runs with ❌ (failed) status
3. Click on the failed run to see details

### 2. Identify the Failing Step
Common failure points:

#### Backend Deployment (`backend-deploy.yml`)
- **Authentication step**: GCP credentials issues
- **Docker build step**: Build context or Dockerfile issues  
- **Docker push step**: Artifact Registry permissions
- **Cloud Run deploy step**: Service configuration issues
- **Health check step**: Application startup issues

#### Frontend Deployment (`frontend-deploy.yml`)
- **Build step**: Next.js compilation errors
- **Firebase deploy step**: Authentication or permissions

## 🚨 Most Common Error Patterns

### Backend Errors

#### 1. GCP Authentication Errors
```
Error: google.auth.exceptions.DefaultCredentialsError
```
**Solution**: Check `GCP_SA_KEY` secret is valid JSON

#### 2. Docker Build Errors
```
Error: failed to solve: failed to read dockerfile
```
**Solution**: Verify Dockerfile syntax and file paths

#### 3. Cloud Run Permission Errors
```
Error: Permission 'run.services.create' denied
```
**Solution**: Service account needs Cloud Run Admin role

#### 4. Environment Variable Errors
```
Error: 4 validation errors for Settings
```
**Solution**: Check all required Firebase secrets are set

### Frontend Errors

#### 1. Firebase Authentication Errors
```
Error: Failed to authenticate with Firebase
```
**Solution**: Check `FIREBASE_TOKEN` and `FIREBASE_SERVICE_ACCOUNT` secrets

#### 2. Next.js Build Errors
```
Error: Build failed with exit code 1
```
**Solution**: Check TypeScript errors and missing dependencies

#### 3. Firebase Hosting Errors
```
Error: Firebase project not found
```
**Solution**: Verify `FIREBASE_PROJECT_ID` secret matches actual project

## 🛠️ Quick Fixes

### 1. Update GitHub Secrets
Go to: Repository Settings → Secrets and Variables → Actions

**Required Backend Secrets:**
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account JSON (base64 encoded)
- `FIREBASE_PROJECT_ID`: Firebase project ID
- `FIREBASE_CLIENT_EMAIL`: Service account email
- `FIREBASE_PRIVATE_KEY`: Firebase private key
- `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket name

**Required Frontend Secrets:**
- `FIREBASE_API_KEY`: Firebase web API key
- `FIREBASE_AUTH_DOMAIN`: Firebase auth domain
- `FIREBASE_PROJECT_ID`: Firebase project ID
- `FIREBASE_STORAGE_BUCKET`: Firebase storage bucket
- `FIREBASE_MESSAGING_SENDER_ID`: Firebase sender ID
- `FIREBASE_APP_ID`: Firebase app ID
- `FIREBASE_SERVICE_ACCOUNT`: Firebase service account JSON
- `FIREBASE_TOKEN`: Firebase CLI token
- `BACKEND_URL`: Deployed backend URL

### 2. Re-trigger Deployment
- Go to Actions tab
- Click "Re-run all jobs" on failed workflow
- Or push a new commit to trigger deployment

### 3. Check Service Account Permissions
Your GCP service account needs these roles:
- Cloud Run Admin
- Artifact Registry Administrator  
- Service Account User
- Firebase Admin

## 🔧 Manual Deployment (if needed)

### Backend Manual Deploy
```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/moda-crypto-backend backend/

# Deploy to Cloud Run
gcloud run deploy moda-crypto-backend \
  --image gcr.io/PROJECT_ID/moda-crypto-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Frontend Manual Deploy
```bash
cd frontend
npm install
npm run build
firebase deploy --only hosting
```

## 📊 Monitoring Deployment Status

After fixing issues, monitor:
1. **GitHub Actions**: Watch workflow progress
2. **Cloud Run Console**: Check service status and logs
3. **Firebase Console**: Verify hosting deployment
4. **Application URLs**: Test actual functionality

## 🆘 Getting Help

If issues persist:
1. Check the specific error message in GitHub Actions logs
2. Verify all secrets are correctly set
3. Test manual deployment to isolate issues
4. Check GCP/Firebase quotas and billing