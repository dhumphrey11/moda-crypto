import { useState, useEffect } from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import LoadingSpinner from '../components/LoadingSpinner';
import { dataService } from '../lib/firestore';
import { SystemHealth, ModelInfo } from '../types';

interface AdminData {
    systemHealth: SystemHealth | null;
    models: ModelInfo[];
    gcpStatus: {
        cloudRun: { status: string; url: string; lastDeploy: string };
        firestore: { status: string; collections: number; documents: number };
        cloudStorage: { status: string; buckets: number };
        logging: { status: string; entries24h: number };
    } | null;
    firebaseStats: {
        hosting: { status: string; domains: string[]; lastDeploy: string };
        authentication: { status: string; users: number };
        database: { status: string; reads24h: number; writes24h: number };
    } | null;
    apiStatus: Array<{ name: string; status: string; lastCheck: string; responseTime: number }>;
    portfolioSettings: {
        ml_weight: number;
        rule_weight: number;
        sentiment_weight: number;
        event_weight: number;
        min_composite_score: number;
        max_positions: number;
        position_size_limit: number;
        stop_loss_pct: number;
        take_profit_pct: number;
    } | null;
    loading: boolean;
    error: string | null;
}

const AdminPage: NextPage = () => {
    const [data, setData] = useState<AdminData>({
        systemHealth: null,
        models: [],
        gcpStatus: null,
        firebaseStats: null,
        apiStatus: [],
        portfolioSettings: null,
        loading: true,
        error: null
    });

    const [activeTab, setActiveTab] = useState<'overview' | 'models' | 'gcp' | 'firebase' | 'apis' | 'settings' | 'populate'>('overview');
    const [settingsEditing, setSettingsEditing] = useState(false);
    const [settingsForm, setSettingsForm] = useState<typeof data.portfolioSettings>(null);
    const [populateTokens, setPopulateTokens] = useState(40);

    useEffect(() => {
        loadAdminData();
        // Set up auto-refresh every 30 seconds
        const interval = setInterval(loadAdminData, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadAdminData = async () => {
        try {
            setData(prev => ({ ...prev, loading: true, error: null }));

            const [systemHealth, models, gcpStatus, firebaseStats, apiStatus, portfolioSettings] = await Promise.allSettled([
                dataService.getSystemHealth(),
                dataService.fetchFromBackend<{ models: ModelInfo[] }>('/admin/models'),
                dataService.fetchFromBackend<typeof data.gcpStatus>('/admin/gcp-status'),
                dataService.fetchFromBackend<typeof data.firebaseStats>('/admin/firebase-stats'),
                dataService.fetchFromBackend<{ apis: typeof data.apiStatus }>('/admin/api-status'),
                dataService.fetchFromBackend<{ settings: typeof data.portfolioSettings }>('/admin/portfolio-settings')
            ]);

            setData(prev => ({
                ...prev,
                systemHealth: systemHealth.status === 'fulfilled' ? systemHealth.value : null,
                models: models.status === 'fulfilled' ? models.value.models : [],
                gcpStatus: gcpStatus.status === 'fulfilled' ? gcpStatus.value : null,
                firebaseStats: firebaseStats.status === 'fulfilled' ? firebaseStats.value : null,
                apiStatus: apiStatus.status === 'fulfilled' ? apiStatus.value.apis : [],
                portfolioSettings: portfolioSettings.status === 'fulfilled' ? portfolioSettings.value.settings : null,
                loading: false
            }));

            // Set settings form if not already set
            if (!settingsForm && portfolioSettings.status === 'fulfilled') {
                setSettingsForm(portfolioSettings.value.settings);
            }

        } catch (error) {
            setData(prev => ({
                ...prev,
                loading: false,
                error: error instanceof Error ? error.message : 'Failed to load admin data'
            }));
        }
    };

    const triggerDataFetch = async (source: string) => {
        try {
            await dataService.triggerDataFetch(source);
            alert(`Data fetch triggered for ${source}`);
        } catch (error) {
            alert(`Failed to trigger data fetch: ${error}`);
        }
    };

    const triggerSignalComputation = async () => {
        try {
            await dataService.triggerSignalComputation();
            alert('Signal computation triggered');
        } catch (error) {
            alert(`Failed to trigger signal computation: ${error}`);
        }
    };

    const savePortfolioSettings = async () => {
        if (!settingsForm) return;
        
        try {
            await dataService.postToBackend('/admin/portfolio-settings', settingsForm);
            setData(prev => ({ ...prev, portfolioSettings: settingsForm }));
            setSettingsEditing(false);
            alert('Settings saved successfully');
        } catch (error) {
            alert(`Failed to save settings: ${error}`);
        }
    };

    const populateWatchlist = async () => {
        try {
            const response = await dataService.postToBackend(`/admin/populate/watchlist?top_n=${populateTokens}`, {}) as { tokens_added: number; message: string };
            alert(`Successfully populated watchlist with ${response.tokens_added} tokens`);
        } catch (error) {
            alert(`Failed to populate watchlist: ${error}`);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'healthy':
            case 'active':
            case 'online':
            case 'ok':
                return 'text-green-600 bg-green-100';
            case 'degraded':
            case 'warning':
                return 'text-yellow-600 bg-yellow-100';
            case 'error':
            case 'failed':
            case 'offline':
                return 'text-red-600 bg-red-100';
            default:
                return 'text-gray-600 bg-gray-100';
        }
    };

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
                <title>Admin - Moda Crypto</title>
                <meta name="description" content="System administration and monitoring" />
            </Head>

            <div className="space-y-6">
                {/* Header */}
                <div className="flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-gray-900">System Administration</h1>
                    <div className="flex space-x-4">
                        <button
                            onClick={loadAdminData}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                        >
                            Refresh
                        </button>
                        <button
                            onClick={triggerSignalComputation}
                            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                        >
                            Compute Signals
                        </button>
                    </div>
                </div>

                {/* System Status Overview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">System Health</h3>
                        <div className="mt-2 flex items-center">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                getStatusColor(data.systemHealth?.status || 'unknown')
                            }`}>
                                {data.systemHealth?.status?.toUpperCase() || 'UNKNOWN'}
                            </span>
                        </div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">Active Models</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {data.models.filter(m => m.status === 'active').length}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">API Services</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {data.apiStatus.filter(api => api.status === 'online').length}/{data.apiStatus.length}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg shadow p-6">
                        <h3 className="text-sm font-medium text-gray-500">24h Runs</h3>
                        <p className="text-2xl font-bold text-gray-900 mt-2">
                            {data.systemHealth?.total_runs_24h || 0}
                        </p>
                    </div>
                </div>

                {/* Tab Navigation */}
                <div className="border-b border-gray-200">
                    <nav className="-mb-px flex space-x-8">
                        {[
                            { id: 'overview', name: 'Overview', icon: '📊' },
                            { id: 'models', name: 'ML Models', icon: '🤖' },
                            { id: 'gcp', name: 'GCP Status', icon: '☁️' },
                            { id: 'firebase', name: 'Firebase', icon: '🔥' },
                            { id: 'apis', name: 'API Services', icon: '🔌' },
                            { id: 'populate', name: 'Populate', icon: '📋' },
                            { id: 'settings', name: 'Settings', icon: '⚙️' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                                    activeTab === tab.id
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

                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {/* System Services */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h3 className="text-lg font-medium text-gray-900">System Services</h3>
                            </div>
                            <div className="p-6">
                                {data.systemHealth?.services ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {Object.entries(data.systemHealth.services).map(([service, info]) => (
                                            <div key={service} className="border border-gray-200 rounded-lg p-4">
                                                <div className="flex justify-between items-start mb-2">
                                                    <h4 className="font-medium text-gray-900">{service}</h4>
                                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                        getStatusColor(info.status)
                                                    }`}>
                                                        {info.status.toUpperCase()}
                                                    </span>
                                                </div>
                                                <div className="text-sm text-gray-500 space-y-1">
                                                    <div>Last Run: {info.last_run ? new Date(info.last_run).toLocaleString() : 'Never'}</div>
                                                    <div>Count: {info.count}</div>
                                                    <div>Duration: {info.duration.toFixed(2)}s</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500">No service data available</p>
                                )}
                            </div>
                        </div>

                        {/* Quick Actions */}
                        <div className="bg-white rounded-lg shadow">
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h3 className="text-lg font-medium text-gray-900">Data Collection Actions</h3>
                            </div>
                            <div className="p-6">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {['coingecko', 'moralis', 'lunarcrush', 'coinmarketcal'].map((source) => (
                                        <button
                                            key={source}
                                            onClick={() => triggerDataFetch(source)}
                                            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                                        >
                                            Fetch {source}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Models Tab */}
                {activeTab === 'models' && (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">ML Models</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Model</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Version</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Accuracy</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Training Date</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.models.map((model) => (
                                        <tr key={model.id}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {model.model_id}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {model.model_type}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {model.version}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {(model.accuracy * 100).toFixed(1)}%
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(model.training_date).toLocaleDateString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                                    getStatusColor(model.status)
                                                }`}>
                                                    {model.status.toUpperCase()}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* GCP Status Tab */}
                {activeTab === 'gcp' && (
                    <div className="space-y-6">
                        {data.gcpStatus ? (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div className="bg-white rounded-lg shadow p-6">
                                        <h4 className="text-lg font-medium text-gray-900 mb-4">Cloud Run</h4>
                                        <div className="space-y-2">
                                            <div className="flex justify-between">
                                                <span>Status:</span>
                                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(data.gcpStatus.cloudRun.status)}`}>
                                                    {data.gcpStatus.cloudRun.status.toUpperCase()}
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>URL:</span>
                                                <a href={data.gcpStatus.cloudRun.url} target="_blank" rel="noopener noreferrer" 
                                                   className="text-blue-600 hover:text-blue-800 text-sm">
                                                    {data.gcpStatus.cloudRun.url}
                                                </a>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Last Deploy:</span>
                                                <span className="text-sm">{data.gcpStatus.cloudRun.lastDeploy}</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div className="bg-white rounded-lg shadow p-6">
                                        <h4 className="text-lg font-medium text-gray-900 mb-4">Firestore</h4>
                                        <div className="space-y-2">
                                            <div className="flex justify-between">
                                                <span>Status:</span>
                                                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(data.gcpStatus.firestore.status)}`}>
                                                    {data.gcpStatus.firestore.status.toUpperCase()}
                                                </span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Collections:</span>
                                                <span>{data.gcpStatus.firestore.collections}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span>Documents:</span>
                                                <span>{data.gcpStatus.firestore.documents}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="bg-white rounded-lg shadow p-6">
                                <p className="text-gray-500">GCP status data not available</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Firebase Tab */}
                {activeTab === 'firebase' && (
                    <div className="space-y-6">
                        {data.firebaseStats ? (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h4 className="text-lg font-medium text-gray-900 mb-4">Hosting</h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span>Status:</span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(data.firebaseStats.hosting.status)}`}>
                                                {data.firebaseStats.hosting.status.toUpperCase()}
                                            </span>
                                        </div>
                                        <div>
                                            <span>Domains:</span>
                                            <div className="mt-1">
                                                {data.firebaseStats.hosting.domains.map((domain, index) => (
                                                    <div key={index} className="text-sm text-blue-600">{domain}</div>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Last Deploy:</span>
                                            <span className="text-sm">{data.firebaseStats.hosting.lastDeploy}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h4 className="text-lg font-medium text-gray-900 mb-4">Authentication</h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span>Status:</span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(data.firebaseStats.authentication.status)}`}>
                                                {data.firebaseStats.authentication.status.toUpperCase()}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Users:</span>
                                            <span>{data.firebaseStats.authentication.users}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h4 className="text-lg font-medium text-gray-900 mb-4">Database</h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between">
                                            <span>Status:</span>
                                            <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(data.firebaseStats.database.status)}`}>
                                                {data.firebaseStats.database.status.toUpperCase()}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Reads (24h):</span>
                                            <span>{data.firebaseStats.database.reads24h}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Writes (24h):</span>
                                            <span>{data.firebaseStats.database.writes24h}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-white rounded-lg shadow p-6">
                                <p className="text-gray-500">Firebase statistics not available</p>
                            </div>
                        )}
                    </div>
                )}

                {/* API Services Tab */}
                {activeTab === 'apis' && (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <div className="px-6 py-4 border-b border-gray-200">
                            <h3 className="text-lg font-medium text-gray-900">External API Services</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Service</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response Time</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Check</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {data.apiStatus.map((api, index) => (
                                        <tr key={index}>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {api.name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(api.status)}`}>
                                                    {api.status.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {api.responseTime}ms
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {new Date(api.lastCheck).toLocaleString()}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                <button
                                                    onClick={() => triggerDataFetch(api.name.toLowerCase())}
                                                    className="text-blue-600 hover:text-blue-900"
                                                >
                                                    Test
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Populate Tab */}
                {activeTab === 'populate' && (
                    <div className="space-y-6">
                        <div className="bg-white rounded-lg shadow">
                            <div className="px-6 py-4 border-b border-gray-200">
                                <h3 className="text-lg font-medium text-gray-900">Populate Watchlist</h3>
                                <p className="text-sm text-gray-600 mt-1">Add popular cryptocurrencies to the watchlist</p>
                            </div>
                            <div className="px-6 py-4">
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Number of tokens to add:
                                        </label>
                                        <select 
                                            value={populateTokens}
                                            onChange={(e) => setPopulateTokens(Number(e.target.value))}
                                            className="w-48 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        >
                                            <option value={10}>10 tokens</option>
                                            <option value={20}>20 tokens</option>
                                            <option value={30}>30 tokens</option>
                                            <option value={40}>40 tokens</option>
                                            <option value={50}>50 tokens</option>
                                        </select>
                                    </div>
                                    <button
                                        onClick={() => populateWatchlist()}
                                        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                                    >
                                        Populate Watchlist
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Settings Tab */}
                {activeTab === 'settings' && (
                    <div className="space-y-6">
                        <div className="bg-white rounded-lg shadow">
                            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                                <h3 className="text-lg font-medium text-gray-900">Portfolio Settings</h3>
                                <div className="space-x-2">
                                    {settingsEditing ? (
                                        <>
                                            <button
                                                onClick={() => {
                                                    setSettingsForm(data.portfolioSettings);
                                                    setSettingsEditing(false);
                                                }}
                                                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                                            >
                                                Cancel
                                            </button>
                                            <button
                                                onClick={savePortfolioSettings}
                                                className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                                            >
                                                Save
                                            </button>
                                        </>
                                    ) : (
                                        <button
                                            onClick={() => setSettingsEditing(true)}
                                            className="px-3 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                                        >
                                            Edit
                                        </button>
                                    )}
                                </div>
                            </div>
                            <div className="p-6">
                                {settingsForm ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Signal Weights */}
                                        <div className="space-y-4">
                                            <h4 className="text-md font-medium text-gray-900">Signal Weights</h4>
                                            {[
                                                { key: 'ml_weight', label: 'ML Weight' },
                                                { key: 'rule_weight', label: 'Rule Weight' },
                                                { key: 'sentiment_weight', label: 'Sentiment Weight' },
                                                { key: 'event_weight', label: 'Event Weight' }
                                            ].map((field) => (
                                                <div key={field.key}>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        {field.label}
                                                    </label>
                                                    <input
                                                        type="number"
                                                        step="0.01"
                                                        min="0"
                                                        max="1"
                                                        disabled={!settingsEditing}
                                                        value={settingsForm[field.key as keyof typeof settingsForm] || 0}
                                                        onChange={(e) => setSettingsForm(prev => prev ? {
                                                            ...prev,
                                                            [field.key]: parseFloat(e.target.value)
                                                        } : null)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        {/* Trading Parameters */}
                                        <div className="space-y-4">
                                            <h4 className="text-md font-medium text-gray-900">Trading Parameters</h4>
                                            {[
                                                { key: 'min_composite_score', label: 'Min Composite Score', step: 0.01 },
                                                { key: 'max_positions', label: 'Max Positions', step: 1 },
                                                { key: 'position_size_limit', label: 'Position Size Limit ($)', step: 100 },
                                                { key: 'stop_loss_pct', label: 'Stop Loss %', step: 0.01 },
                                                { key: 'take_profit_pct', label: 'Take Profit %', step: 0.01 }
                                            ].map((field) => (
                                                <div key={field.key}>
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        {field.label}
                                                    </label>
                                                    <input
                                                        type="number"
                                                        step={field.step}
                                                        min="0"
                                                        disabled={!settingsEditing}
                                                        value={settingsForm[field.key as keyof typeof settingsForm] || 0}
                                                        onChange={(e) => setSettingsForm(prev => prev ? {
                                                            ...prev,
                                                            [field.key]: parseFloat(e.target.value)
                                                        } : null)}
                                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-gray-500">No settings available</p>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default AdminPage;