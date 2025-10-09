import { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import LoadingSpinner from '../components/LoadingSpinner';
import PortfolioTable from '../components/PortfolioTable';
import { dataService } from '../lib/firestore';
import { Portfolio, PortfolioPosition, Trade } from '../types';

interface PortfolioData {
    portfolio: Portfolio | null;
    allTrades: Trade[];
    historicalPositions: Array<{
        date: string;
        positions: PortfolioPosition[];
        totalValue: number;
        totalPnL: number;
    }>;
    loading: boolean;
    error: string | null;
}

const PortfolioPage: NextPage = () => {
    const [data, setData] = useState<PortfolioData>({
        portfolio: null,
        allTrades: [],
        historicalPositions: [],
        loading: true,
        error: null
    });

    const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
    const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
    const [view, setView] = useState<'positions' | 'performance' | 'trades'>('positions');

    useEffect(() => {
        loadPortfolioData();
    }, [timeRange]);

    const loadPortfolioData = async () => {
        try {
            setData(prev => ({ ...prev, loading: true, error: null }));

            const [portfolio, allTrades, historicalPositions] = await Promise.allSettled([
                dataService.getPortfolio(),
                dataService.getTrades(),
                dataService.fetchFromBackend<{
                    history: Array<{
                        date: string;
                        positions: PortfolioPosition[];
                        total_value: number;
                        total_pnl: number;
                    }>
                }>(`/paper-trade/portfolio/history/detailed?range=${timeRange}`)
            ]);

            setData(prev => ({
                ...prev,
                portfolio: portfolio.status === 'fulfilled' ? portfolio.value : null,
                allTrades: allTrades.status === 'fulfilled' ? allTrades.value : [],
                historicalPositions: historicalPositions.status === 'fulfilled' 
                    ? historicalPositions.value.history.map(h => ({
                        date: h.date,
                        positions: h.positions,
                        totalValue: h.total_value,
                        totalPnL: h.total_pnl
                    }))
                    : [],
                loading: false
            }));

        } catch (error) {
            setData(prev => ({
                ...prev,
                loading: false,
                error: error instanceof Error ? error.message : 'Failed to load portfolio data'
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
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    };

    const getTradesForPosition = (tokenId: string) => {
        return data.allTrades.filter(trade => trade.token_id === tokenId);
    };

    const calculatePositionMetrics = (position: PortfolioPosition) => {
        const trades = getTradesForPosition(position.token_id);
        const buyTrades = trades.filter(t => t.action === 'buy');
        const sellTrades = trades.filter(t => t.action === 'sell');
        
        return {
            totalBuys: buyTrades.reduce((sum, t) => sum + (t.total_cost || 0), 0),
            totalSells: sellTrades.reduce((sum, t) => sum + (t.total_proceeds || 0), 0),
            tradeCount: trades.length,
            avgBuyPrice: buyTrades.length > 0 ? 
                buyTrades.reduce((sum, t) => sum + t.price, 0) / buyTrades.length : 0,
            avgSellPrice: sellTrades.length > 0 ? 
                sellTrades.reduce((sum, t) => sum + t.price, 0) / sellTrades.length : 0
        };
    };

    if (data.loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <LoadingSpinner />
            </div>
        );
    }

    const portfolio = data.portfolio;
    const positions = portfolio?.positions || [];

    return (
        <>
            <Head>
                <title>Portfolio - Moda Crypto</title>
                <meta name="description" content="Portfolio analytics and performance tracking" />
            </Head>

            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
                    <div className="flex space-x-4">
                        {/* Time Range Selector */}
                        <div className="flex space-x-2">
                            {(['7d', '30d', '90d', '1y'] as const).map((range) => (
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
                        
                        {/* Refresh Button */}
                        <button
                            onClick={loadPortfolioData}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Portfolio Summary */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Total Value</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {formatCurrency(portfolio?.summary?.total_value || 0)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Cost Basis</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {formatCurrency(portfolio?.summary?.total_cost || 0)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Total P&L</h3>
                        <p className={`text-2xl font-bold mt-2 ${
                            (portfolio?.summary?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                            {formatCurrency(portfolio?.summary?.total_pnl || 0)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">P&L %</h3>
                        <p className={`text-2xl font-bold mt-2 ${
                            (portfolio?.summary?.total_pnl_pct || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                            {formatPercentage(portfolio?.summary?.total_pnl_pct || 0)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Positions</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {positions.length}
                        </p>
                    </div>
                </div>

                {/* View Tabs */}
                <div className="border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8">
                        {[
                            { id: 'positions', name: 'Current Positions', icon: '📊' },
                            { id: 'performance', name: 'Performance History', icon: '📈' },
                            { id: 'trades', name: 'Trade History', icon: '📋' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setView(tab.id as any)}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                    view === tab.id
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                <span className="mr-2">{tab.icon}</span>
                                {tab.name}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Current Positions View */}
                {view === 'positions' && (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Token
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Quantity
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Avg Cost
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Current Value
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Cost Basis
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            P&L
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            P&L %
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Last Updated
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {positions.map((position) => {
                                        const metrics = calculatePositionMetrics(position);
                                        return (
                                            <tr 
                                                key={position.token_id}
                                                className={`hover:bg-gray-50 cursor-pointer ${
                                                    selectedPosition === position.token_id ? 'bg-blue-50' : ''
                                                }`}
                                                onClick={() => setSelectedPosition(
                                                    selectedPosition === position.token_id ? null : position.token_id
                                                )}
                                            >
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="font-medium text-gray-900">{position.token_id}</div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {position.quantity.toFixed(4)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {formatCurrency(position.avg_cost)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                    {formatCurrency(position.current_value)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {formatCurrency(position.cost_basis)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                    <span className={position.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                        {formatCurrency(position.pnl)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                    <span className={position.pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                        {formatPercentage(position.pnl_pct)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {new Date(position.last_updated).toLocaleDateString()}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>

                        {positions.length === 0 && (
                            <div className="text-center py-12">
                                <p className="text-gray-500">No positions found.</p>
                            </div>
                        )}

                        {/* Position Details */}
                        {selectedPosition && (
                            <div className="border-t border-gray-200 p-6 bg-gray-50">
                                <h4 className="text-lg font-medium text-gray-900 mb-4">
                                    {selectedPosition} - Trade History
                                </h4>
                                <div className="space-y-2">
                                    {getTradesForPosition(selectedPosition).map((trade) => (
                                        <div key={trade.id} className="flex justify-between items-center p-3 bg-white rounded-lg">
                                            <div className="flex items-center space-x-3">
                                                <div className={`w-2 h-2 rounded-full ${
                                                    trade.action === 'buy' ? 'bg-green-500' : 'bg-red-500'
                                                }`}></div>
                                                <div>
                                                    <span className="font-medium text-gray-900">
                                                        {trade.action.toUpperCase()}
                                                    </span>
                                                    <span className="text-gray-500 ml-2">
                                                        {trade.quantity} @ {formatCurrency(trade.price)}
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-sm font-medium text-gray-900">
                                                    {formatCurrency(trade.total_cost || trade.total_proceeds || 0)}
                                                </div>
                                                <div className="text-xs text-gray-500">
                                                    {new Date(trade.timestamp).toLocaleDateString()}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Performance History View */}
                {view === 'performance' && (
                    <div className="space-y-6">
                        {/* Historical Portfolio Chart Placeholder */}
                        <div className="bg-white rounded-lg shadow p-6">
                            <h3 className="text-lg font-medium text-gray-900 mb-4">Portfolio Value Over Time</h3>
                            <div className="h-64 flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg">
                                <div className="text-center text-gray-500">
                                    <p>📈 Portfolio performance chart would go here</p>
                                    <p className="text-sm mt-2">Integration with Chart.js or Recharts needed</p>
                                </div>
                            </div>
                        </div>

                        {/* Historical Snapshots */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h3 className="text-lg font-medium text-gray-900">Portfolio Snapshots</h3>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Date
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Total Value
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Total P&L
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                Positions
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {data.historicalPositions.map((snapshot, index) => (
                                            <tr key={index}>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {new Date(snapshot.date).toLocaleDateString()}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                    {formatCurrency(snapshot.totalValue)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                    <span className={snapshot.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                        {formatCurrency(snapshot.totalPnL)}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {snapshot.positions.length} positions
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* Trade History View */}
                {view === 'trades' && (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">All Trades</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Date
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Token
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Action
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Quantity
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Price
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Total
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            P&L
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            Status
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.allTrades.map((trade) => (
                                        <tr key={trade.id}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {new Date(trade.timestamp).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {trade.token_id}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                    trade.action === 'buy' 
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-red-100 text-red-800'
                                                }`}>
                                                    {trade.action.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {trade.quantity}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {formatCurrency(trade.price)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {formatCurrency(trade.total_cost || trade.total_proceeds || 0)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                {trade.pnl !== undefined ? (
                                                    <span className={trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                        {formatCurrency(trade.pnl)}
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-400">-</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                    trade.status === 'open' 
                                                        ? 'bg-blue-100 text-blue-800'
                                                        : 'bg-gray-100 text-gray-800'
                                                }`}>
                                                    {trade.status.toUpperCase()}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {data.allTrades.length === 0 && (
                            <div className="text-center py-12">
                                <p className="text-gray-500">No trades found.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </>
    );
};

export default PortfolioPage;