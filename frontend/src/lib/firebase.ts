import { initializeApp, getApps } from 'firebase/app';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getStorage, connectStorageEmulator } from 'firebase/storage';

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Validate Firebase configuration
if (!firebaseConfig.apiKey || !firebaseConfig.projectId) {
    console.error('Firebase configuration is incomplete. Please check your environment variables.');
}

// Initialize Firebase
let app;
try {
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
    console.log('Firebase app initialized successfully');
} catch (error) {
    console.error('Failed to initialize Firebase app:', error);
    throw error;
}

// Initialize Firebase services
export const db = getFirestore(app);
export const auth = getAuth(app);
export const storage = getStorage(app);

// Connect to emulators only if explicitly enabled
if (process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === 'true' && typeof window !== 'undefined') {
    console.log('Attempting to connect to Firebase emulators...');

    // Connect to Auth emulator
    try {
        connectAuthEmulator(auth, 'http://localhost:9099');
        console.log('Connected to Auth emulator');
    } catch (error) {
        console.warn('Auth emulator connection failed:', error);
    }

    // Connect to Firestore emulator
    try {
        connectFirestoreEmulator(db, 'localhost', 8080);
        console.log('Connected to Firestore emulator');
    } catch (error) {
        console.warn('Firestore emulator connection failed:', error);
    }

    // Connect to Storage emulator
    try {
        connectStorageEmulator(storage, 'localhost', 9199);
        console.log('Connected to Storage emulator');
    } catch (error) {
        console.warn('Storage emulator connection failed:', error);
    }
} else {
    console.log('Using production Firebase services');
}

export default app;