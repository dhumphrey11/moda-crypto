import {
    collection,
    query,
    orderBy,
    limit,
    where,
    onSnapshot,
    getDocs,
    Timestamp
} from 'firebase/firestore';
import { db } from './firebase';
import { Signal, Trade, Portfolio, SystemHealth, Token } from '@/types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

// Polling interval in milliseconds (60 seconds)
const POLLING_INTERVAL = 60000;

class DataService {
    private pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

    // ==========================================
    // BACKEND API CALLS
    // ==========================================

    async fetchFromBackend<T>(endpoint: string): Promise<T> {
        const response = await fetch(`${BACKEND_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`Backend API error: ${response.statusText}`);
        }
        return response.json();
    }

    async postToBackend<T>(endpoint: string, data?: any): Promise<T> {
        const response = await fetch(`${BACKEND_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: data ? JSON.stringify(data) : undefined,
        });

        if (!response.ok) {
            throw new Error(`Backend API error: ${response.statusText}`);
        }
        return response.json();
    }

    // ==========================================
    // SYSTEM HEALTH
    // ==========================================

    async getSystemHealth(): Promise<SystemHealth> {
        return this.fetchFromBackend<SystemHealth>('/health');
    }

    // ==========================================
    // SIGNALS
    // ==========================================

    async getRecentSignals(hours: number = 24): Promise<Signal[]> {
        const response = await this.fetchFromBackend<{ signals: any[] }>(`/compute/signals/recent?hours=${hours}`);
        return response.signals.map(this.convertFirestoreSignal);
    }

    async getTopSignals(limit: number = 10, min_score: number = 0.7): Promise<Signal[]> {
        const response = await this.fetchFromBackend<{ signals: any[] }>(`/compute/signals/top?limit=${limit}&min_score=${min_score}`);
        return response.signals.map(this.convertFirestoreSignal);
    }

    // Start polling for signal updates
    startSignalPolling(callback: (signals: Signal[]) => void, hours: number = 24): string {
        const pollId = `signals_${Date.now()}`;

        const poll = async () => {
            try {
                const signals = await this.getRecentSignals(hours);
                callback(signals);
            } catch (error) {
                console.error('Signal polling error:', error);
            }
        };

        // Initial fetch
        poll();

        // Set up polling interval
        const intervalId = setInterval(poll, POLLING_INTERVAL);
        this.pollingIntervals.set(pollId, intervalId);

        return pollId;
    }

    // ==========================================
    // PORTFOLIO
    // ==========================================

    async getPortfolio(): Promise<Portfolio> {
        const response = await this.fetchFromBackend<{ portfolio: Portfolio }>('/paper-trade/portfolio');
        return response.portfolio;
    }

    async getTrades(status?: string): Promise<Trade[]> {
        const endpoint = status ? `/paper-trade/trades?status=${status}` : '/paper-trade/trades';
        const response = await this.fetchFromBackend<{ trades: any[] }>(endpoint);
        return response.trades.map(this.convertFirestoreTrade);
    }

    // Start polling for portfolio updates
    startPortfolioPolling(callback: (portfolio: Portfolio) => void): string {
        const pollId = `portfolio_${Date.now()}`;

        const poll = async () => {
            try {
                const portfolio = await this.getPortfolio();
                callback(portfolio);
            } catch (error) {
                console.error('Portfolio polling error:', error);
            }
        };

        // Initial fetch
        poll();

        // Set up polling interval
        const intervalId = setInterval(poll, POLLING_INTERVAL);
        this.pollingIntervals.set(pollId, intervalId);

        return pollId;
    }

    // ==========================================
    // ADMIN OPERATIONS
    // ==========================================

    async triggerDataFetch(source: string): Promise<any> {
        return this.postToBackend(`/fetch/${source}`);
    }

    async triggerSignalComputation(): Promise<any> {
        return this.postToBackend('/compute/signals');
    }

    async triggerPaperTrading(): Promise<any> {
        return this.postToBackend('/paper-trade/execute');
    }

    async triggerModelRetrain(): Promise<any> {
        return this.postToBackend('/admin/retrain');
    }

    async getAdminConfig(): Promise<any> {
        return this.fetchFromBackend('/admin/config');
    }

    async updateAdminConfig(config: any): Promise<any> {
        return this.postToBackend('/admin/config', config);
    }

    async getSystemStats(): Promise<any> {
        return this.fetchFromBackend('/admin/stats');
    }

    // ==========================================
    // FIRESTORE REAL-TIME SUBSCRIPTIONS
    // ==========================================

    subscribeToSignals(callback: (signals: Signal[]) => void, hours: number = 24): () => void {
        const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);

        const q = query(
            collection(db, 'signals'),
            where('timestamp', '>=', Timestamp.fromDate(cutoffTime)),
            orderBy('timestamp', 'desc'),
            limit(50)
        );

        return onSnapshot(q, (snapshot) => {
            const signals = snapshot.docs.map(doc =>
                this.convertFirestoreSignal({ id: doc.id, ...doc.data() })
            );
            callback(signals);
        });
    }

    subscribeToTrades(callback: (trades: Trade[]) => void, status?: string): () => void {
        let q = query(
            collection(db, 'trades'),
            orderBy('timestamp', 'desc'),
            limit(100)
        );

        if (status) {
            q = query(
                collection(db, 'trades'),
                where('status', '==', status),
                orderBy('timestamp', 'desc'),
                limit(100)
            );
        }

        return onSnapshot(q, (snapshot) => {
            const trades = snapshot.docs.map(doc =>
                this.convertFirestoreTrade({ id: doc.id, ...doc.data() })
            );
            callback(trades);
        });
    }

    // ==========================================
    // DATA CONVERSION HELPERS
    // ==========================================

    private convertFirestoreSignal(doc: any): Signal {
        return {
            id: doc.id,
            token_id: doc.token_id,
            ml_prob: doc.ml_prob || 0,
            rule_score: doc.rule_score || 0,
            sentiment_score: doc.sentiment_score || 0,
            event_score: doc.event_score || 0,
            composite_score: doc.composite_score || 0,
            action: doc.action || 'hold',
            confidence: doc.confidence || 0,
            weights_used: doc.weights_used || {
                ml_weight: 0.4,
                rule_weight: 0.3,
                sentiment_weight: 0.2,
                event_weight: 0.1
            },
            min_threshold: doc.min_threshold || 0.85,
            timestamp: doc.timestamp?.toDate?.() || new Date(doc.timestamp)
        };
    }

    private convertFirestoreTrade(doc: any): Trade {
        return {
            id: doc.id,
            signal_id: doc.signal_id || '',
            token_id: doc.token_id,
            action: doc.action,
            quantity: doc.quantity || 0,
            price: doc.price || 0,
            total_cost: doc.total_cost,
            total_proceeds: doc.total_proceeds,
            pnl: doc.pnl,
            pnl_pct: doc.pnl_pct,
            composite_score: doc.composite_score || 0,
            status: doc.status || 'open',
            timestamp: doc.timestamp?.toDate?.() || new Date(doc.timestamp)
        };
    }

    // ==========================================
    // CLEANUP
    // ==========================================

    stopPolling(pollId: string): void {
        const intervalId = this.pollingIntervals.get(pollId);
        if (intervalId) {
            clearInterval(intervalId);
            this.pollingIntervals.delete(pollId);
        }
    }

    stopAllPolling(): void {
        this.pollingIntervals.forEach((intervalId) => {
            clearInterval(intervalId);
        });
        this.pollingIntervals.clear();
    }
}

// Export singleton instance
export const dataService = new DataService();
export default dataService;