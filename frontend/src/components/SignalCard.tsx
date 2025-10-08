import { Signal } from '../types';

interface SignalCardProps {
    signal: Signal;
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
                            <div>Confidence: {(signal.confidence * 100).toFixed(1)}%</div>
                            <div>Composite Score: {signal.composite_score.toFixed(3)}</div>
                        </div>

                        <div className="mt-2 text-sm text-gray-600">
                            <div>ML Probability: {(signal.ml_prob * 100).toFixed(1)}%</div>
                            <div>Rule Score: {signal.rule_score.toFixed(3)}</div>
                            <div>Sentiment Score: {signal.sentiment_score.toFixed(3)}</div>
                        </div>

                        <div className="mt-2 text-xs text-gray-500">
                            Generated: {formatTimestamp(signal.timestamp.toISOString())}
                        </div>
                    </div>

                    <div className="text-right">
                        <div className={`text-lg font-bold ${getConfidenceColor(signal.confidence)}`}>
                            {(signal.confidence * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">Confidence</div>
                    </div>
                </div>

                {/* Weights Information */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="text-xs text-gray-500 mb-2">Model Weights</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between">
                            <span className="text-gray-600">ML Weight:</span>
                            <span className="font-medium">{signal.weights_used.ml_weight.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Rule Weight:</span>
                            <span className="font-medium">{signal.weights_used.rule_weight.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Sentiment Weight:</span>
                            <span className="font-medium">{signal.weights_used.sentiment_weight.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Event Weight:</span>
                            <span className="font-medium">{signal.weights_used.event_weight.toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                {/* Threshold Information */}
                <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>Min Threshold: {signal.min_threshold.toFixed(3)}</span>
                        <span>Event Score: {signal.event_score.toFixed(3)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SignalCard;