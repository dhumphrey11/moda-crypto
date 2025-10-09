import { useEffect, useState } from 'react';
import { User, onAuthStateChanged } from 'firebase/auth';
import { auth } from './firebase';

export const useAuth = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        try {
            const unsubscribe = onAuthStateChanged(
                auth,
                (user) => {
                    setUser(user);
                    setLoading(false);
                    setError(null);
                },
                (error) => {
                    console.error('Auth state change error:', error);
                    setError(error.message);
                    setLoading(false);
                }
            );

            return () => unsubscribe();
        } catch (error) {
            console.error('Failed to set up auth listener:', error);
            setError(error instanceof Error ? error.message : 'Authentication setup failed');
            setLoading(false);
        }
    }, []);

    const logout = async () => {
        try {
            await auth.signOut();
        } catch (error) {
            console.error('Logout error:', error);
            throw error;
        }
    };

    return {
        user,
        loading,
        error,
        logout,
        isAuthenticated: !!user
    };
};