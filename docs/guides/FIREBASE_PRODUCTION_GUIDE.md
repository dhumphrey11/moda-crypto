# Firebase Production Deployment Guide

## 🔥 Firestore Security Rules Deployment

### Prerequisites
1. Firebase CLI installed: `npm install -g firebase-tools`
2. Authenticated with Firebase: `firebase login`
3. Project initialized: `firebase init` (select Firestore)

### Step 1: Deploy Security Rules

```bash
# Navigate to project root
cd /Users/Morghan/Documents/davy/moda-crypto

# Deploy Firestore rules
firebase deploy --only firestore:rules

# Or deploy all Firebase resources
firebase deploy
```

### Step 2: Manual Deployment via Firebase Console

1. **Go to Firebase Console**: https://console.firebase.google.com
2. **Select your project**: moda-crypto
3. **Navigate to Firestore Database**: 
   - Click "Firestore Database" in the left sidebar
   - Click "Rules" tab
4. **Copy and paste the rules** from `firestore.rules` file
5. **Click "Publish"** to deploy the new rules

### Step 3: Verify Security Rules

Test the rules to ensure they work as expected:

```javascript
// Test in Firebase Console Rules Playground
// Try these scenarios:

// 1. Unauthenticated user trying to read signals (should DENY)
get /databases/(default)/documents/signals/test123

// 2. Authenticated user trying to read signals (should ALLOW)
get /databases/(default)/documents/signals/test123
// Set auth.uid = "test-user-123"

// 3. User trying to access another user's portfolio (should DENY)
get /databases/(default)/documents/portfolio/other-user-456
// Set auth.uid = "test-user-123"

// 4. User accessing their own portfolio (should ALLOW)
get /databases/(default)/documents/portfolio/test-user-123
// Set auth.uid = "test-user-123"
```

## 🔐 Authentication Setup for Production

### Required Authentication Methods

1. **Email/Password Authentication**:
   ```bash
   # Enable in Firebase Console:
   # Authentication > Sign-in method > Email/Password > Enable
   ```

2. **Custom Claims for Roles** (Backend setup required):
   ```javascript
   // Set custom claims for users (backend admin function)
   await admin.auth().setCustomUserClaims(uid, {
     admin: true,        // For admin users
     system: true,       // For system/service accounts
     role: 'trader'      // For specific user roles
   });
   ```

### Environment Variables for Production

Create `.env.production` with:
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your-production-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=moda-crypto.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=moda-crypto
# ... other production values
```

## 📊 Security Rules Breakdown

### Collections Access Control:

| Collection | Read Access | Write Access |
|------------|------------|--------------|
| `signals` | ✅ Authenticated users | ❌ System/Admin only |
| `portfolio/{userId}` | ✅ Owner or Admin | ✅ Owner or Admin |
| `system_health` | ✅ Authenticated users | ❌ System/Admin only |
| `users/{userId}` | ✅ Owner or Admin | ✅ Owner or Admin |
| `admin_config` | ❌ Admin only | ❌ Admin only |
| `api_keys` | ❌ Admin only | ❌ Admin only |

### Custom Claims Required:
- `admin: true` - Full system access
- `system: true` - System operations (data writes)
- `role: "trader"` - User role specification

## 🚀 Production Checklist

- [ ] **Deploy security rules** to Firebase
- [ ] **Enable Authentication** methods in Firebase Console
- [ ] **Set up custom claims** for admin users
- [ ] **Update environment variables** for production
- [ ] **Test authentication flow** with real users
- [ ] **Monitor security rules** in Firebase Console
- [ ] **Set up Firebase Analytics** (optional)
- [ ] **Configure backup and monitoring**

## 🛡️ Security Best Practices

1. **Never expose admin credentials** in frontend
2. **Use HTTPS only** for production
3. **Regularly audit user permissions**
4. **Monitor Firebase usage** for unusual patterns
5. **Keep Firebase SDK updated**
6. **Use Firebase App Check** for additional security
7. **Enable audit logging** for sensitive operations

## 📋 Troubleshooting

### Common Issues:

1. **"Permission denied" errors**:
   - Check user authentication status
   - Verify custom claims are set
   - Test rules in Firebase Console

2. **Rules not applying**:
   - Ensure rules are deployed (`firebase deploy --only firestore:rules`)
   - Check Firebase Console for deployment status
   - Clear browser cache

3. **Authentication errors**:
   - Verify API keys in environment variables
   - Check Firebase Authentication settings
   - Ensure auth domain is correct

### Debug Commands:
```bash
# Check Firebase project status
firebase projects:list

# Test local rules (if using emulator)
firebase emulators:start --only firestore

# Deploy specific resources
firebase deploy --only firestore:rules
firebase deploy --only hosting
```

## 📞 Support

For additional help:
- Firebase Documentation: https://firebase.google.com/docs
- Firebase Console: https://console.firebase.google.com
- Firebase CLI Reference: https://firebase.google.com/docs/cli