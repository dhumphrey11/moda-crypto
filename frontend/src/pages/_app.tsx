import type { AppProps } from 'next/app';
import { useEffect, useState } from 'react';
import { useAuth } from '../lib/useAuth';
import Layout from '../components/Layout';
import LoginPage from '../components/LoginPage';
import LoadingSpinner from '../components/LoadingSpinner';
import '../styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
    const { user, loading, error } = useAuth();
    const [initError, setInitError] = useState<string | null>(null);

    useEffect(() => {
        // Set up global error handlers
        const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
            console.error('Unhandled promise rejection:', event.reason);
            if (event.reason?.message?.includes('_databaseId')) {
                setInitError('Firebase initialization failed. Please check your configuration.');
            }
        };

        const handleError = (event: ErrorEvent) => {
            console.error('Global error:', event.error);
            if (event.error?.message?.includes('_databaseId')) {
                setInitError('Firebase database connection failed. Please check your configuration.');
            }
        };

        window.addEventListener('unhandledrejection', handleUnhandledRejection);
        window.addEventListener('error', handleError);

        return () => {
            window.removeEventListener('unhandledrejection', handleUnhandledRejection);
            window.removeEventListener('error', handleError);
        };
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <LoadingSpinner size="large" />
            </div>
        );
    }

    if (error || initError) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900 mb-4">Application Error</h1>
                    <p className="text-gray-600 mb-4">{error || initError}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="btn-primary"
                    >
                        Reload Page
                    </button>
                </div>
            </div>
        );
    }

    if (!user) {
        return <LoginPage />;
    }

    return (
        <Layout>
            <Component {...pageProps} />
        </Layout>
    );
}