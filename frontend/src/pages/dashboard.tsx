import { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import Layout from '../components/Layout';
import LoadingSpinner from '../components/LoadingSpinner';
import { dataService } from '../lib/firestore';
import { Portfolio, Trade, Signal } from '../types';

interface DashboardData {
    portfolio: Portfolio | null;
    recentTrades: Trade[];
    recentSignals: Signal[];
    portfolioHistory: Array<{ date: string; value: number }>;
    loading: boolean;
    error: string | null;
}

const Dashboard: NextPage = () => {
    const [data, setData] = useState<DashboardData>({
        portfolio: null,
        recentTrades: [],
        recentSignals: [],
        portfolioHistory: [],
        loading: true,
        error: null
    });

    const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d');

    useEffect(() => {
        const loadDashboardData = async () => {
            try {
                setData(prev => ({ ...prev, loading: true, error: null }));

                const [portfolio, recentTrades, recentSignals, portfolioHistory] = await Promise.allSettled([
                    dataService.getPortfolio(),
                    dataService.getRecentTrades(10),
                    dataService.getTopSignals(5, 0.6),
                    dataService.getPortfolioHistory(timeRange)
                ]);

                setData(prev => ({
                    ...prev,
                    portfolio: portfolio.status === 'fulfilled' ? portfolio.value : null,
                    recentTrades: recentTrades.status === 'fulfilled' ? recentTrades.value : [],
                    recentSignals: recentSignals.status === 'fulfilled' ? recentSignals.value : [],
                    portfolioHistory: portfolioHistory.status === 'fulfilled' ? portfolioHistory.value : [],
                    loading: false
                }));
            } catch (error) {
                setData(prev => ({
                    ...prev,
                    loading: false,
                    error: error instanceof Error ? error.message : 'Failed to load dashboard data'
                }));
            }
        };

        loadDashboardData();
    }, [timeRange]);

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    };

    const formatPercentage = (value: number) => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    if (data.loading) {
        return (
            <Layout>
                <div className="flex justify-center items-center h-64">
                    <LoadingSpinner />
                </div>
            </Layout>
        );
    }

    const portfolioValue = data.portfolio?.summary?.total_value || 0;
    const portfolioPnL = data.portfolio?.summary?.total_pnl || 0;
    const portfolioPnLPct = data.portfolio?.summary?.total_pnl_pct || 0;
    const positions = data.portfolio?.positions || [];

    return (
        <Layout>
            <Head>
                <title>Dashboard - Moda Crypto</title>
                <meta name="description" content="Moda Crypto trading dashboard" />
            </Head>

            <div className="space-y-8">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                    <div className="flex space-x-2">
                        {(['24h', '7d', '30d', '90d'] as const).map((range) => (
                            <button
                                key={range}
                                onClick={() => setTimeRange(range)}
                                className={`px-3 py-1 text-sm rounded-md ${
                                    timeRange === range
                                        ? 'bg-blue-100 text-blue-700'
                                        : 'text-gray-500 hover:text-gray-700'
                                }`}
                            >
                                {range}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Portfolio Overview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Total Portfolio Value</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {formatCurrency(portfolioValue)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
                        <p className={`text-2xl font-bold mt-2 ${
                            portfolioPnL >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                            {formatCurrency(portfolioPnL)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Total P&L %</h3>
                        <p className={`text-2xl font-bold mt-2 ${
                            portfolioPnLPct >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                            {formatPercentage(portfolioPnLPct)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Active Positions</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {positions.length}
                        </p>
                    </div>
                </div>

                {/* Portfolio Chart */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Value Over Time</h3>
                    {data.portfolioHistory.length > 0 ? (
                        <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg">
                            <div className="text-center text-gray-500">
                                <p>📈 Chart visualization would go here</p>
                                <p className="text-sm mt-2">Integration with Chart.js or Recharts needed</p>
                            </div>
                        </div>
                    ) : (
                        <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg">
                            <p className="text-gray-500">No historical data available</p>
                        </div>
                    )}
                </div>

                {/* Two Column Layout */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Current Holdings */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">Current Holdings</h3>
                        </div>
                        <div className="p-6">
                            {positions.length > 0 ? (
                                <div className="space-y-4">
                                    {positions.slice(0, 5).map((position, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                            <div>
                                                <h4 className="font-medium text-gray-900">{position.token_id}</h4>
                                                <p className="text-sm text-gray-500">
                                                    {position.quantity.toFixed(4)} tokens
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-medium text-gray-900">
                                                    {formatCurrency(position.current_value)}
                                                </p>
                                                <p className={`text-sm ${
                                                    position.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'
                                                }`}>
                                                    {formatPercentage(position.pnl_pct)}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-500 text-center py-8">No positions found</p>
                            )}
                        </div>
                    </div>

                    {/* Recent Transactions */}
                    <div className="bg-white rounded-lg shadow">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">Recent Transactions</h3>
                        </div>
                        <div className="p-6">
                            {data.recentTrades.length > 0 ? (
                                <div className="space-y-4">
                                    {data.recentTrades.map((trade) => (
                                        <div key={trade.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                            <div className="flex items-center space-x-3">
                                                <div className={`w-2 h-2 rounded-full ${
                                                    trade.action === 'buy' ? 'bg-green-500' : 'bg-red-500'
                                                }`}></div>
                                                <div>
                                                    <h4 className="font-medium text-gray-900">
                                                        {trade.action.toUpperCase()} {trade.token_id}
                                                    </h4>
                                                    <p className="text-sm text-gray-500">
                                                        {new Date(trade.timestamp).toLocaleDateString()}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-medium text-gray-900">
                                                    {formatCurrency(trade.total_cost || trade.total_proceeds || 0)}
                                                </p>
                                                {trade.pnl_pct !== undefined && (
                                                    <p className={`text-sm ${
                                                        trade.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'
                                                    }`}>
                                                        {formatPercentage(trade.pnl_pct)}
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-gray-500 text-center py-8">No recent trades found</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Recent Signals Preview */}
                <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                        <h3 className="text-lg font-medium text-gray-900">Latest Signals</h3>
                        <a href="/signals" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            View All →
                        </a>
                    </div>
                    <div className="p-6">
                        {data.recentSignals.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {data.recentSignals.map((signal) => (
                                    <div key={signal.id} className="p-4 border border-gray-200 rounded-lg">
                                        <div className="flex justify-between items-start mb-2">
                                            <h4 className="font-medium text-gray-900">{signal.token_id}</h4>
                                            <span className={`px-2 py-1 text-xs font-medium rounded ${
                                                signal.action === 'buy' 
                                                    ? 'bg-green-100 text-green-800'
                                                    : signal.action === 'sell'
                                                    ? 'bg-red-100 text-red-800'
                                                    : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                                {signal.action.toUpperCase()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-2">
                                            Score: {signal.composite_score.toFixed(2)}
                                        </p>
                                        <p className="text-sm text-gray-600">
                                            Confidence: {(signal.confidence * 100).toFixed(1)}%
                                        </p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500 text-center py-8">No recent signals found</p>
                        )}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Dashboard;