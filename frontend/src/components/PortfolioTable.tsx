import { Portfolio } from '@/types';

interface PortfolioTableProps {
    portfolio: Portfolio | null;
    compact?: boolean;
}

const PortfolioTable = ({ portfolio, compact = false }: PortfolioTableProps) => {
    if (!portfolio) {
        return (
            <div className="text-center py-8">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m0 0v3a1 1 0 001 1h1m-4-4h4v4H6v-4z" />
                </svg>
                <p className="text-gray-600">No portfolio data available</p>
            </div>
        );
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount);
    };

    const formatPercentage = (value: number) => {
        const formatted = (value * 100).toFixed(2);
        return `${value >= 0 ? '+' : ''}${formatted}%`;
    };

    const getReturnColor = (value: number) => {
        if (value > 0) return 'text-success-600';
        if (value < 0) return 'text-danger-600';
        return 'text-gray-600';
    };

    if (compact) {
        return (
            <div className="space-y-4">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <div className="text-sm text-gray-600">Total Value</div>
                        <div className="text-lg font-semibold">{formatCurrency(portfolio.totalValue)}</div>
                    </div>
                    <div>
                        <div className="text-sm text-gray-600">Total Return</div>
                        <div className={`text-lg font-semibold ${getReturnColor(portfolio.totalReturn)}`}>
                            {formatPercentage(portfolio.totalReturn)}
                        </div>
                    </div>
                </div>

                {/* Top Holdings */}
                {portfolio.holdings && portfolio.holdings.length > 0 && (
                    <div>
                        <div className="text-sm font-medium text-gray-900 mb-2">Top Holdings</div>
                        <div className="space-y-2">
                            {portfolio.holdings.slice(0, 3).map((holding, index) => (
                                <div key={`${holding.symbol}-${index}`} className="flex justify-between items-center">
                                    <div className="flex items-center space-x-2">
                                        <span className="font-medium">{holding.symbol}</span>
                                        <span className="text-sm text-gray-600">{holding.quantity} tokens</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="font-medium">{formatCurrency(holding.value)}</div>
                                        <div className={`text-xs ${getReturnColor(holding.unrealizedPnL)}`}>
                                            {formatPercentage(holding.unrealizedPnL)}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Portfolio Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-lg border">
                    <div className="text-sm text-gray-600">Total Value</div>
                    <div className="text-2xl font-bold">{formatCurrency(portfolio.totalValue)}</div>
                </div>

                <div className="bg-white p-4 rounded-lg border">
                    <div className="text-sm text-gray-600">Cash Balance</div>
                    <div className="text-2xl font-bold">{formatCurrency(portfolio.cashBalance)}</div>
                </div>

                <div className="bg-white p-4 rounded-lg border">
                    <div className="text-sm text-gray-600">Total Return</div>
                    <div className={`text-2xl font-bold ${getReturnColor(portfolio.totalReturn)}`}>
                        {formatPercentage(portfolio.totalReturn)}
                    </div>
                </div>

                <div className="bg-white p-4 rounded-lg border">
                    <div className="text-sm text-gray-600">Active Positions</div>
                    <div className="text-2xl font-bold">{portfolio.holdings?.length || 0}</div>
                </div>
            </div>

            {/* Holdings Table */}
            {portfolio.holdings && portfolio.holdings.length > 0 ? (
                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    <div className="px-4 py-5 sm:px-6">
                        <h3 className="text-lg leading-6 font-medium text-gray-900">Holdings</h3>
                        <p className="mt-1 max-w-2xl text-sm text-gray-500">
                            Current portfolio positions and performance
                        </p>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Symbol
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Quantity
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Avg Price
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Current Price
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Value
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        P&L
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Return %
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {portfolio.holdings.map((holding, index) => (
                                    <tr key={`${holding.symbol}-${index}`} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {holding.symbol}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {holding.quantity.toFixed(6)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatCurrency(holding.avgPrice)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatCurrency(holding.currentPrice)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                                            {formatCurrency(holding.value)}
                                        </td>
                                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getReturnColor(holding.unrealizedPnL)}`}>
                                            {formatCurrency(holding.unrealizedPnL)}
                                        </td>
                                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${getReturnColor(holding.unrealizedPnL / holding.value)}`}>
                                            {formatPercentage(holding.unrealizedPnL / holding.value)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            ) : (
                <div className="bg-white shadow sm:rounded-md p-6">
                    <div className="text-center">
                        <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m0 0v3a1 1 0 001 1h1m-4-4h4v4H6v-4z" />
                        </svg>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No Holdings</h3>
                        <p className="text-gray-600">Start trading to see your portfolio positions here.</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PortfolioTable;