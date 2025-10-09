import { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import Layout from '../components/Layout';
import LoadingSpinner from '../components/LoadingSpinner';
import { dataService } from '../lib/firestore';
import { Signal } from '../types';

interface SignalsData {
    signals: Signal[];
    loading: boolean;
    error: string | null;
    totalCount: number;
    pagination: {
        page: number;
        limit: number;
        hasMore: boolean;
    };
}

interface SignalsFilters {
    action: 'all' | 'buy' | 'sell' | 'hold';
    confidence: number;
    dateRange: '24h' | '7d' | '30d' | '90d' | 'all';
    sortBy: 'timestamp' | 'confidence' | 'composite_score';
    sortOrder: 'asc' | 'desc';
}

const SignalsPage: NextPage = () => {
    const [data, setData] = useState<SignalsData>({
        signals: [],
        loading: true,
        error: null,
        totalCount: 0,
        pagination: {
            page: 1,
            limit: 20,
            hasMore: false
        }
    });

    const [filters, setFilters] = useState<SignalsFilters>({
        action: 'all',
        confidence: 0.5,
        dateRange: '7d',
        sortBy: 'timestamp',
        sortOrder: 'desc'
    });

    const [showFilters, setShowFilters] = useState(false);

    useEffect(() => {
        loadSignals();
    }, [filters, data.pagination.page]);

    const loadSignals = async () => {
        try {
            setData(prev => ({ ...prev, loading: true, error: null }));

            // Build query parameters
            const params = new URLSearchParams({
                page: data.pagination.page.toString(),
                limit: data.pagination.limit.toString(),
                min_confidence: filters.confidence.toString(),
                sort: filters.sortBy,
                order: filters.sortOrder,
                range: filters.dateRange
            });

            if (filters.action !== 'all') {
                params.append('action', filters.action);
            }

            const response = await dataService.fetchFromBackend<{
                signals: any[];
                total: number;
                page: number;
                has_more: boolean;
            }>(`/compute/signals?${params.toString()}`);

            // The signals should already be in the correct format from the backend
            const convertedSignals = response.signals;

            setData(prev => ({
                ...prev,
                signals: convertedSignals,
                totalCount: response.total,
                loading: false,
                pagination: {
                    ...prev.pagination,
                    hasMore: response.has_more
                }
            }));

        } catch (error) {
            setData(prev => ({
                ...prev,
                loading: false,
                error: error instanceof Error ? error.message : 'Failed to load signals'
            }));
        }
    };

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    };

    const formatPercentage = (value: number) => {
        return `${value >= 0 ? '+' : ''}${value.toFixed(1)}%`;
    };

    const getActionBadge = (action: string) => {
        const colors = {
            buy: 'bg-green-100 text-green-800',
            sell: 'bg-red-100 text-red-800',
            hold: 'bg-yellow-100 text-yellow-800'
        };
        return colors[action as keyof typeof colors] || 'bg-gray-100 text-gray-800';
    };

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.8) return 'text-green-600';
        if (confidence >= 0.6) return 'text-yellow-600';
        return 'text-red-600';
    };

    const resetFilters = () => {
        setFilters({
            action: 'all',
            confidence: 0.5,
            dateRange: '7d',
            sortBy: 'timestamp',
            sortOrder: 'desc'
        });
        setData(prev => ({ ...prev, pagination: { ...prev.pagination, page: 1 } }));
    };

    const nextPage = () => {
        if (data.pagination.hasMore) {
            setData(prev => ({
                ...prev,
                pagination: { ...prev.pagination, page: prev.pagination.page + 1 }
            }));
        }
    };

    const prevPage = () => {
        if (data.pagination.page > 1) {
            setData(prev => ({
                ...prev,
                pagination: { ...prev.pagination, page: prev.pagination.page - 1 }
            }));
        }
    };

    if (data.loading && data.signals.length === 0) {
        return (
            <Layout>
                <div className="flex justify-center items-center h-64">
                    <LoadingSpinner />
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <Head>
                <title>Signals - Moda Crypto</title>
                <meta name="description" content="AI Trading Signals History" />
            </Head>

            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Trading Signals</h1>
                        <p className="text-gray-500 mt-2">
                            {data.totalCount} total signals • Page {data.pagination.page}
                        </p>
                    </div>
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                    >
                        <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707v4.586l-4-4V9.414a1 1 0 00-.293-.707L3.293 2.707A1 1 0 013 2V4z" />
                        </svg>
                        Filters
                    </button>
                </div>

                {/* Filters Panel */}
                {showFilters && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-lg font-medium text-gray-900 mb-4">Filter Signals</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            {/* Action Filter */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Action</label>
                                <select
                                    value={filters.action}
                                    onChange={(e) => setFilters(prev => ({ ...prev, action: e.target.value as any }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="all">All Actions</option>
                                    <option value="buy">Buy</option>
                                    <option value="sell">Sell</option>
                                    <option value="hold">Hold</option>
                                </select>
                            </div>

                            {/* Confidence Filter */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Min Confidence ({(filters.confidence * 100).toFixed(0)}%)
                                </label>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.1"
                                    value={filters.confidence}
                                    onChange={(e) => setFilters(prev => ({ ...prev, confidence: parseFloat(e.target.value) }))}
                                    className="w-full"
                                />
                            </div>

                            {/* Date Range Filter */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
                                <select
                                    value={filters.dateRange}
                                    onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value as any }))}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="24h">Last 24 Hours</option>
                                    <option value="7d">Last 7 Days</option>
                                    <option value="30d">Last 30 Days</option>
                                    <option value="90d">Last 90 Days</option>
                                    <option value="all">All Time</option>
                                </select>
                            </div>

                            {/* Sort Options */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
                                <div className="flex space-x-2">
                                    <select
                                        value={filters.sortBy}
                                        onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value as any }))}
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        <option value="timestamp">Date</option>
                                        <option value="confidence">Confidence</option>
                                        <option value="composite_score">Score</option>
                                    </select>
                                    <button
                                        onClick={() => setFilters(prev => ({ 
                                            ...prev, 
                                            sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc' 
                                        }))}
                                        className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                                    >
                                        {filters.sortOrder === 'asc' ? '↑' : '↓'}
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="mt-4 flex space-x-4">
                            <button
                                onClick={loadSignals}
                                disabled={data.loading}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                            >
                                Apply Filters
                            </button>
                            <button
                                onClick={resetFilters}
                                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                            >
                                Reset
                            </button>
                        </div>
                    </div>
                )}

                {/* Signals Table */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    {data.loading && (
                        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
                            <LoadingSpinner />
                        </div>
                    )}

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Token
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Action
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Score
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Confidence
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Components
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Timestamp
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {data.signals.map((signal) => (
                                    <tr key={signal.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="font-medium text-gray-900">{signal.token_id}</div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getActionBadge(signal.action)}`}>
                                                {signal.action.toUpperCase()}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">
                                                {signal.composite_score.toFixed(3)}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className={`text-sm font-medium ${getConfidenceColor(signal.confidence)}`}>
                                                {(signal.confidence * 100).toFixed(1)}%
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <div className="space-y-1">
                                                <div>ML: {signal.ml_prob.toFixed(3)} ({(signal.weights_used.ml_weight * 100).toFixed(0)}%)</div>
                                                <div>Rules: {signal.rule_score.toFixed(3)} ({(signal.weights_used.rule_weight * 100).toFixed(0)}%)</div>
                                                <div>Sentiment: {signal.sentiment_score.toFixed(3)} ({(signal.weights_used.sentiment_weight * 100).toFixed(0)}%)</div>
                                                <div>Events: {signal.event_score.toFixed(3)} ({(signal.weights_used.event_weight * 100).toFixed(0)}%)</div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <div>{new Date(signal.timestamp).toLocaleDateString()}</div>
                                            <div>{new Date(signal.timestamp).toLocaleTimeString()}</div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {data.signals.length === 0 && !data.loading && (
                        <div className="text-center py-12">
                            <p className="text-gray-500">No signals found with the current filters.</p>
                        </div>
                    )}
                </div>

                {/* Pagination */}
                <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-700">
                        Showing {((data.pagination.page - 1) * data.pagination.limit) + 1} to {Math.min(data.pagination.page * data.pagination.limit, data.totalCount)} of {data.totalCount} signals
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={prevPage}
                            disabled={data.pagination.page === 1}
                            className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <button
                            onClick={nextPage}
                            disabled={!data.pagination.hasMore}
                            className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default SignalsPage;