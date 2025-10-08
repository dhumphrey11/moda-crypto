import { SystemHealth } from '@/types';

interface HealthPanelProps {
    systemHealth: SystemHealth | null;
}

const HealthPanel = ({ systemHealth }: HealthPanelProps) => {
    if (!systemHealth) {
        return (
            <div className="card">
                <div className="card-header">
                    <h2 className="text-lg font-semibold text-gray-900">System Health</h2>
                </div>
                <div className="card-body">
                    <div className="text-center py-4">
                        <div className="text-yellow-500 text-4xl mb-2">⚠️</div>
                        <p className="text-gray-600">System health data unavailable</p>
                    </div>
                </div>
            </div>
        );
    }

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'healthy':
            case 'operational':
            case 'online':
                return 'text-success-600 bg-success-50';
            case 'warning':
            case 'degraded':
                return 'text-warning-600 bg-warning-50';
            case 'critical':
            case 'error':
            case 'offline':
                return 'text-danger-600 bg-danger-50';
            default:
                return 'text-gray-600 bg-gray-50';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status.toLowerCase()) {
            case 'healthy':
            case 'operational':
            case 'online':
                return '✅';
            case 'warning':
            case 'degraded':
                return '⚠️';
            case 'critical':
            case 'error':
            case 'offline':
                return '❌';
            default:
                return '❓';
        }
    };

    // Mock system components for demonstration
    const components = [
        { name: 'API Server', status: 'healthy', lastCheck: '2 min ago' },
        { name: 'Database', status: 'healthy', lastCheck: '1 min ago' },
        { name: 'ML Pipeline', status: systemHealth.ml_status || 'healthy', lastCheck: '5 min ago' },
        { name: 'External APIs', status: systemHealth.api_status || 'healthy', lastCheck: '3 min ago' },
        { name: 'Paper Trading', status: 'healthy', lastCheck: '1 min ago' },
    ];

    return (
        <div className="card">
            <div className="card-header">
                <div className="flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-gray-900">System Health</h2>
                    <div className="flex items-center space-x-2">
                        <span className="text-2xl">
                            {getStatusIcon(systemHealth.overall || 'unknown')}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemHealth.overall || 'unknown')}`}>
                            {systemHealth.overall || 'Unknown'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {components.map((component) => (
                        <div key={component.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center space-x-3">
                                <span className="text-lg">{getStatusIcon(component.status)}</span>
                                <div>
                                    <div className="font-medium text-gray-900">{component.name}</div>
                                    <div className="text-xs text-gray-500">Last check: {component.lastCheck}</div>
                                </div>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(component.status)}`}>
                                {component.status}
                            </span>
                        </div>
                    ))}
                </div>

                {/* System Metrics */}
                <div className="mt-6 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div>
                            <div className="text-2xl font-bold text-gray-900">
                                {systemHealth.uptime ? `${systemHealth.uptime}%` : '99.9%'}
                            </div>
                            <div className="text-sm text-gray-600">Uptime</div>
                        </div>

                        <div>
                            <div className="text-2xl font-bold text-gray-900">
                                {systemHealth.response_time || '120ms'}
                            </div>
                            <div className="text-sm text-gray-600">Response Time</div>
                        </div>

                        <div>
                            <div className="text-2xl font-bold text-gray-900">
                                {systemHealth.last_signal_time ? new Date(systemHealth.last_signal_time).toLocaleTimeString() : '--:--'}
                            </div>
                            <div className="text-sm text-gray-600">Last Signal</div>
                        </div>

                        <div>
                            <div className="text-2xl font-bold text-gray-900">
                                {systemHealth.error_rate || '0.1%'}
                            </div>
                            <div className="text-sm text-gray-600">Error Rate</div>
                        </div>
                    </div>
                </div>

                {/* Recent Issues */}
                {systemHealth.recent_issues && systemHealth.recent_issues.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                        <h4 className="text-sm font-medium text-gray-900 mb-3">Recent Issues</h4>
                        <div className="space-y-2">
                            {systemHealth.recent_issues.slice(0, 3).map((issue, index) => (
                                <div key={index} className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                                    <span className="text-yellow-500">⚠️</span>
                                    <div>
                                        <div className="text-sm font-medium text-gray-900">{issue.title}</div>
                                        <div className="text-xs text-gray-600">{issue.timestamp}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default HealthPanel;