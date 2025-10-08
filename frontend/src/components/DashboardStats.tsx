import { Signal, Portfolio, SystemHealth } from '@/types';

interface DashboardStatsProps {
    signals: Signal[];
    portfolio: Portfolio | null;
    systemHealth: SystemHealth | null;
}

const DashboardStats = ({ signals, portfolio, systemHealth }: DashboardStatsProps) => {
    const stats = [
        {
            name: 'Active Signals',
            value: signals.length,
            change: '+2.5%',
            changeType: 'positive' as const,
            icon: '📡'
        },
        {
            name: 'Portfolio Value',
            value: portfolio ? `$${portfolio.totalValue?.toLocaleString() || '0'}` : '$0',
            change: portfolio?.totalReturn ? `${(portfolio.totalReturn * 100).toFixed(2)}%` : '0%',
            changeType: (portfolio?.totalReturn || 0) >= 0 ? 'positive' as const : 'negative' as const,
            icon: '💼'
        },
        {
            name: 'System Health',
            value: systemHealth?.overall || 'Unknown',
            change: systemHealth?.uptime ? `${systemHealth.uptime}% uptime` : 'N/A',
            changeType: 'neutral' as const,
            icon: '🔧'
        },
        {
            name: 'High Confidence',
            value: signals.filter(s => s.confidence > 0.8).length,
            change: `${signals.length > 0 ? ((signals.filter(s => s.confidence > 0.8).length / signals.length) * 100).toFixed(1) : 0}%`,
            changeType: 'positive' as const,
            icon: '⭐'
        }
    ];

    const getChangeColor = (type: 'positive' | 'negative' | 'neutral') => {
        switch (type) {
            case 'positive':
                return 'text-success-600';
            case 'negative':
                return 'text-danger-600';
            default:
                return 'text-gray-600';
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => (
                <div key={stat.name} className="card">
                    <div className="card-body">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="text-2xl">{stat.icon}</div>
                            </div>
                            <div className="ml-4 w-0 flex-1">
                                <div className="text-sm font-medium text-gray-500 truncate">
                                    {stat.name}
                                </div>
                                <div className="text-lg font-bold text-gray-900">
                                    {stat.value}
                                </div>
                                <div className={`text-sm ${getChangeColor(stat.changeType)}`}>
                                    {stat.change}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default DashboardStats;