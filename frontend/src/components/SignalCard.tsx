import { Signal } from '@/types';

interface SignalCardProps {                        <div className="mt-2 text-sm text-gray-600">
                            <div>Confidence: {(signal.confidence * 100).toFixed(1)}%</div>
                            <div>Composite Score: {signal.composite_score.toFixed(3)}</div>
                        </div>

                        <div className="mt-2 text-xs text-gray-500">
                            Generated: {formatTimestamp(signal.timestamp.toISOString())}
                        </div>Signal;
    rank?: number;
    onClick?: () => void;
}

const SignalCard = ({ signal, rank, onClick }: SignalCardProps) => {
    const getSignalTypeColor = (type: string) => {
        switch (type) {
            case 'BUY':
                return 'text-success-600 bg-success-50';
            case 'SELL':
                return 'text-danger-600 bg-danger-50';
            default:
                return 'text-gray-600 bg-gray-50';
        }
    };

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.8) return 'text-success-600';
        if (confidence >= 0.6) return 'text-warning-600';
        return 'text-danger-600';
    };

    const formatTimestamp = (timestamp: string) => {
        return new Date(timestamp).toLocaleString();
    };

    const formatPrice = (price: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 6
        }).format(price);
    };

    return (
        <div
            className={`card hover:shadow-md transition-shadow cursor-pointer ${onClick ? 'hover:bg-gray-50' : ''}`}
            onClick={onClick}
        >
            <div className="card-body">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center space-x-3">
                            {rank && (
                                <div className="flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-600 rounded-full text-xs font-bold">
                                    {rank}
                                </div>
                            )}

                            <div className="flex items-center space-x-2">
                                <span className="font-semibold text-gray-900">{signal.token_id}</span>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSignalTypeColor(signal.action)}`}>
                                    {signal.action.toUpperCase()}
                                </span>
                            </div>
                        </div>

                        <div className="mt-2 text-sm text-gray-600">
                            <div>Current Price: {formatPrice(signal.current_price)}</div>
                            {signal.target_price && (
                                <div>Target Price: {formatPrice(signal.target_price)}</div>
                            )}
                            {signal.stop_loss && (
                                <div>Stop Loss: {formatPrice(signal.stop_loss)}</div>
                            )}
                        </div>

                        <div className="mt-3 text-xs text-gray-500">
                            Generated: {formatTimestamp(signal.timestamp)}
                        </div>
                    </div>

                    <div className="text-right">
                        <div className={`text-lg font-bold ${getConfidenceColor(signal.confidence)}`}>
                            {(signal.confidence * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">Confidence</div>
                    </div>
                </div>

                {/* Signal Details */}
                {signal.features && Object.keys(signal.features).length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                        <div className="text-xs text-gray-500 mb-2">Key Indicators</div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                            {Object.entries(signal.features).slice(0, 4).map(([key, value]) => (
                                <div key={key} className="flex justify-between">
                                    <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}</span>
                                    <span className="font-medium">
                                        {typeof value === 'number' ? value.toFixed(3) : String(value)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Source Information */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>Model: {signal.model_version || 'v1.0'}</span>
                        <span>Score: {signal.raw_score?.toFixed(3) || 'N/A'}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SignalCard;