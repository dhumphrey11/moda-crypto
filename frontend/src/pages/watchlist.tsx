import { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import LoadingSpinner from '../components/LoadingSpinner';
import { dataService } from '../lib/firestore';
import { Token } from '../types';

interface WatchlistData {
    tokens: Token[];
    availableTokens: Token[];
    loading: boolean;
    error: string | null;
}

interface NewTokenForm {
    symbol: string;
    name: string;
    coingecko_id: string;
}

const WatchlistPage: NextPage = () => {
    const [data, setData] = useState<WatchlistData>({
        tokens: [],
        availableTokens: [],
        loading: true,
        error: null
    });

    const [showAddForm, setShowAddForm] = useState(false);
    const [newToken, setNewToken] = useState<NewTokenForm>({
        symbol: '',
        name: '',
        coingecko_id: ''
    });
    const [searchQuery, setSearchQuery] = useState('');
    const [editingToken, setEditingToken] = useState<string | null>(null);

    useEffect(() => {
        loadWatchlistData();
    }, []);

    const loadWatchlistData = async () => {
        try {
            setData(prev => ({ ...prev, loading: true, error: null }));

            const [activeTokens, allTokens] = await Promise.allSettled([
                dataService.fetchFromBackend<{ tokens: Token[] }>('/admin/watchlist'),
                dataService.fetchFromBackend<{ tokens: Token[] }>('/admin/tokens/all')
            ]);

            setData(prev => ({
                ...prev,
                tokens: activeTokens.status === 'fulfilled' ? activeTokens.value.tokens : [],
                availableTokens: allTokens.status === 'fulfilled' ? allTokens.value.tokens : [],
                loading: false
            }));

        } catch (error) {
            setData(prev => ({
                ...prev,
                loading: false,
                error: error instanceof Error ? error.message : 'Failed to load watchlist data'
            }));
        }
    };

    const addToWatchlist = async (token: Token | NewTokenForm) => {
        try {
            await dataService.postToBackend('/admin/watchlist', token);
            await loadWatchlistData();
            setShowAddForm(false);
            setNewToken({ symbol: '', name: '', coingecko_id: '' });
        } catch (error) {
            alert(`Failed to add token: ${error}`);
        }
    };

    const removeFromWatchlist = async (tokenId: string) => {
        if (!confirm('Are you sure you want to remove this token from the watchlist?')) return;
        
        try {
            await dataService.deleteFromBackend(`/admin/watchlist/${tokenId}`);
            await loadWatchlistData();
        } catch (error) {
            alert(`Failed to remove token: ${error}`);
        }
    };

    const toggleTokenStatus = async (tokenId: string, active: boolean) => {
        try {
            await dataService.putToBackend(`/admin/watchlist/${tokenId}`, { active });
            await loadWatchlistData();
        } catch (error) {
            alert(`Failed to update token status: ${error}`);
        }
    };

    const updateToken = async (tokenId: string, updates: Partial<Token>) => {
        try {
            await dataService.putToBackend(`/admin/watchlist/${tokenId}`, updates);
            await loadWatchlistData();
            setEditingToken(null);
        } catch (error) {
            alert(`Failed to update token: ${error}`);
        }
    };

    const triggerDataSync = async () => {
        try {
            await dataService.postToBackend('/admin/watchlist/sync');
            alert('Watchlist data sync triggered');
            await loadWatchlistData();
        } catch (error) {
            alert(`Failed to sync data: ${error}`);
        }
    };

    const filteredTokens = data.tokens.filter(token => 
        token.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        token.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const availableToAdd = data.availableTokens.filter(token => 
        !data.tokens.some(watchedToken => watchedToken.id === token.id)
    );

    if (data.loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <LoadingSpinner />
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>Watchlist - Moda Crypto</title>
                <meta name="description" content="Cryptocurrency watchlist management" />
            </Head>

            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Cryptocurrency Watchlist</h1>
                        <p className="text-gray-500 mt-2">
                            Manage the cryptocurrencies monitored by the data ingestion services
                        </p>
                    </div>
                    <div className="flex space-x-4">
                        <button
                            onClick={() => setShowAddForm(true)}
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                        >
                            Add Token
                        </button>
                        <button
                            onClick={triggerDataSync}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                            Sync Data
                        </button>
                        <button
                            onClick={loadWatchlistData}
                            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Total Tokens</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {data.tokens.length}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Active</h3>
                        <p className="text-2xl font-bold text-green-600 mt-2">
                            {data.tokens.filter(t => t.active).length}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Inactive</h3>
                        <p className="text-2xl font-bold text-red-600 mt-2">
                            {data.tokens.filter(t => !t.active).length}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Available to Add</h3>
                        <p className="text-2xl font-bold text-blue-600 mt-2">
                            {availableToAdd.length}
                        </p>
                    </div>
                </div>

                {/* Search */}
                <div className="flex justify-between items-center">
                    <div className="relative flex-1 max-w-lg">
                        <input
                            type="text"
                            placeholder="Search tokens..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                    </div>
                </div>

                {/* Add Token Form Modal */}
                {showAddForm && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-medium text-gray-900">Add New Token</h3>
                                <button
                                    onClick={() => setShowAddForm(false)}
                                    className="text-gray-400 hover:text-gray-600"
                                >
                                    ✕
                                </button>
                            </div>

                            {/* Quick Add from Available Tokens */}
                            {availableToAdd.length > 0 && (
                                <div className="mb-6">
                                    <h4 className="text-sm font-medium text-gray-700 mb-2">Quick Add from Available</h4>
                                    <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-md">
                                        {availableToAdd.slice(0, 10).map((token) => (
                                            <button
                                                key={token.id}
                                                onClick={() => addToWatchlist(token)}
                                                className="w-full text-left px-3 py-2 hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
                                            >
                                                <div className="font-medium">{token.symbol}</div>
                                                <div className="text-sm text-gray-500">{token.name}</div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Manual Add Form */}
                            <div className="space-y-4">
                                <h4 className="text-sm font-medium text-gray-700">Or Add Manually</h4>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Symbol</label>
                                    <input
                                        type="text"
                                        value={newToken.symbol}
                                        onChange={(e) => setNewToken(prev => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                                        placeholder="BTC"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                                    <input
                                        type="text"
                                        value={newToken.name}
                                        onChange={(e) => setNewToken(prev => ({ ...prev, name: e.target.value }))}
                                        placeholder="Bitcoin"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">CoinGecko ID</label>
                                    <input
                                        type="text"
                                        value={newToken.coingecko_id}
                                        onChange={(e) => setNewToken(prev => ({ ...prev, coingecko_id: e.target.value }))}
                                        placeholder="bitcoin"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div className="flex space-x-4 pt-4">
                                    <button
                                        onClick={() => addToWatchlist(newToken)}
                                        disabled={!newToken.symbol || !newToken.name || !newToken.coingecko_id}
                                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Add Token
                                    </button>
                                    <button
                                        onClick={() => {
                                            setShowAddForm(false);
                                            setNewToken({ symbol: '', name: '', coingecko_id: '' });
                                        }}
                                        className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Tokens Table */}
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Token
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        CoinGecko ID
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Market Cap
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        24h Liquidity
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Last Updated
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredTokens.map((token) => (
                                    <tr key={token.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div>
                                                    <div className="text-sm font-medium text-gray-900">{token.symbol}</div>
                                                    <div className="text-sm text-gray-500">{token.name}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {editingToken === token.id ? (
                                                <input
                                                    type="text"
                                                    defaultValue={token.coingecko_id || ''}
                                                    onBlur={(e) => updateToken(token.id, { coingecko_id: e.target.value })}
                                                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                                                />
                                            ) : (
                                                token.coingecko_id || '-'
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {token.market_cap ? `$${(token.market_cap / 1000000).toFixed(0)}M` : '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {token.liquidity_24h ? `$${(token.liquidity_24h / 1000000).toFixed(1)}M` : '-'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <button
                                                onClick={() => toggleTokenStatus(token.id, !token.active)}
                                                className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                    token.active 
                                                        ? 'bg-green-100 text-green-800 hover:bg-green-200'
                                                        : 'bg-red-100 text-red-800 hover:bg-red-200'
                                                }`}
                                            >
                                                {token.active ? 'ACTIVE' : 'INACTIVE'}
                                            </button>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(token.last_updated).toLocaleDateString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            <div className="flex space-x-2">
                                                <button
                                                    onClick={() => setEditingToken(editingToken === token.id ? null : token.id)}
                                                    className="text-blue-600 hover:text-blue-900"
                                                >
                                                    {editingToken === token.id ? 'Done' : 'Edit'}
                                                </button>
                                                <button
                                                    onClick={() => removeFromWatchlist(token.id)}
                                                    className="text-red-600 hover:text-red-900"
                                                >
                                                    Remove
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {filteredTokens.length === 0 && (
                        <div className="text-center py-12">
                            <p className="text-gray-500">
                                {searchQuery ? 'No tokens match your search.' : 'No tokens in watchlist.'}
                            </p>
                        </div>
                    )}
                </div>

                {/* Data Sources Info */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <h3 className="text-lg font-medium text-blue-900 mb-2">About Watchlist Monitoring</h3>
                    <div className="text-sm text-blue-700 space-y-2">
                        <p>
                            <strong>Data Sources:</strong> The system monitors these tokens across multiple data sources including CoinGecko, Moralis, LunarCrush, CoinMarketCal, and CryptoPanic.
                        </p>
                        <p>
                            <strong>Auto-sync:</strong> Token data is automatically synchronized every hour. Use the "Sync Data" button to trigger an immediate update.
                        </p>
                        <p>
                            <strong>Active Status:</strong> Only active tokens are monitored for signals and included in trading decisions. Inactive tokens remain in the list but are ignored by the AI models.
                        </p>
                        <p>
                            <strong>CoinGecko ID:</strong> Required for price data and market metrics. You can find the correct ID on the token's CoinGecko page URL.
                        </p>
                    </div>
                </div>
            </div>
        </>
    );
};

export default WatchlistPage;