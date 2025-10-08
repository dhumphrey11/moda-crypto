import { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import DashboardStats from '@/components/DashboardStats';
import SignalCard from '@/components/SignalCard';
import PortfolioTable from '@/components/PortfolioTable';
import HealthPanel from '@/components/HealthPanel';
import LoadingSpinner from '@/components/LoadingSpinner';
import { dataService } from '@/lib/firestore';
import { Signal, Portfolio, SystemHealth } from '@/types';

interface DashboardData {
    signals: Signal[];
    portfolio: Portfolio | null;
    systemHealth: SystemHealth | null;
    loading: boolean;
    error: string | null;
}

const Dashboard: NextPage = () => {
    const [data, setData] = useState<DashboardData>({
        signals: [],
        portfolio: null,
        systemHealth: null,
        loading: true,
        error: null
    });

    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        let signalPollId: string | null = null;
        let portfolioPollId: string | null = null;

        const loadInitialData = async () => {
            try {
                setData(prev => ({ ...prev, loading: true, error: null }));

                // Load initial data
                const [signals, portfolio, systemHealth] = await Promise.allSettled([
                    dataService.getTopSignals(10, 0.6),
                    dataService.getPortfolio(),
                    dataService.getSystemHealth()
                ]);

                setData(prev => ({
                    ...prev,
                    signals: signals.status === 'fulfilled' ? signals.value : [],
                    portfolio: portfolio.status === 'fulfilled' ? portfolio.value : null,
                    systemHealth: systemHealth.status === 'fulfilled' ? systemHealth.value : null,
                    loading: false
                }));

                // Start polling for updates
                signalPollId = dataService.startSignalPolling((newSignals) => {
                    setData(prev => ({ ...prev, signals: newSignals }));
                }, 24);

                portfolioPollId = dataService.startPortfolioPolling((newPortfolio) => {
                    setData(prev => ({ ...prev, portfolio: newPortfolio }));
                });

            } catch (error) {
                console.error('Failed to load dashboard data:', error);
                setData(prev => ({
                    ...prev,
                    loading: false,
                    error: error instanceof Error ? error.message : 'Failed to load data'
                }));
            }
        };

        loadInitialData();

        // Cleanup polling when component unmounts
        return () => {
            if (signalPollId) dataService.stopPolling(signalPollId);
            if (portfolioPollId) dataService.stopPolling(portfolioPollId);
        };
    }, []);

    const handleRefresh = async () => {
        setRefreshing(true);
        try {
            const [signals, portfolio, systemHealth] = await Promise.allSettled([
                dataService.getTopSignals(10, 0.6),
                dataService.getPortfolio(),
                dataService.getSystemHealth()
            ]);

            setData(prev => ({
                ...prev,
                signals: signals.status === 'fulfilled' ? signals.value : prev.signals,
                portfolio: portfolio.status === 'fulfilled' ? portfolio.value : prev.portfolio,
                systemHealth: systemHealth.status === 'fulfilled' ? systemHealth.value : prev.systemHealth,
            }));
        } catch (error) {
            console.error('Refresh failed:', error);
        } finally {
            setRefreshing(false);
        }
    };

    if (data.loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <LoadingSpinner size="large" />
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Dashboard - Moda Crypto</title>
                <meta name="description" content="Crypto signal and paper trading dashboard" />
            </Head>

            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                        <p className="text-gray-600 mt-1">
                            Monitor signals, portfolio performance, and system health
                        </p>
                    </div>

                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="btn-primary flex items-center space-x-2"
                    >
                        <svg
                            className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                            />
                        </svg>
                        <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
                    </button>
                </div>

                {/* Error Display */}
                {data.error && (
                    <div className="bg-danger-50 border border-danger-200 rounded-md p-4">
                        <div className="flex">
                            <svg className="w-5 h-5 text-danger-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <div className="ml-3">
                                <h3 className="text-sm font-medium text-danger-800">Error Loading Data</h3>
                                <p className="text-sm text-danger-700 mt-1">{data.error}</p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Dashboard Stats */}
                <DashboardStats
                    signals={data.signals}
                    portfolio={data.portfolio}
                    systemHealth={data.systemHealth}
                />

                {/* System Health */}
                <HealthPanel systemHealth={data.systemHealth} />

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Recent Signals */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="text-lg font-semibold text-gray-900">Top Signals</h2>
                            <p className="text-sm text-gray-600">
                                Highest confidence signals from the last 24 hours
                            </p>
                        </div>
                        <div className="card-body">
                            {data.signals.length > 0 ? (
                                <div className="space-y-4">
                                    {data.signals.slice(0, 5).map((signal, index) => (
                                        <SignalCard key={signal.id} signal={signal} rank={index + 1} />
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-8">
                                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                    <p className="text-gray-600">No signals available</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Portfolio Overview */}
                    <div className="card">
                        <div className="card-header">
                            <h2 className="text-lg font-semibold text-gray-900">Portfolio Overview</h2>
                            <p className="text-sm text-gray-600">
                                Current positions and performance
                            </p>
                        </div>
                        <div className="card-body">
                            <PortfolioTable portfolio={data.portfolio} compact={true} />
                        </div>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="card">
                    <div className="card-header">
                        <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
                    </div>
                    <div className="card-body">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <button className="btn-secondary text-left p-4 h-auto">
                                <div className="text-sm font-medium text-gray-900">View All Signals</div>
                                <div className="text-xs text-gray-600 mt-1">Browse complete signal history</div>
                            </button>

                            <button className="btn-secondary text-left p-4 h-auto">
                                <div className="text-sm font-medium text-gray-900">Portfolio Details</div>
                                <div className="text-xs text-gray-600 mt-1">Detailed position analysis</div>
                            </button>

                            <button className="btn-secondary text-left p-4 h-auto">
                                <div className="text-sm font-medium text-gray-900">System Admin</div>
                                <div className="text-xs text-gray-600 mt-1">Configure and monitor</div>
                            </button>

                            <button className="btn-secondary text-left p-4 h-auto">
                                <div className="text-sm font-medium text-gray-900">Trade History</div>
                                <div className="text-xs text-gray-600 mt-1">Review past trades</div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Dashboard;