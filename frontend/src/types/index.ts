export interface Token {
    id: string;
    symbol: string;
    name: string;
    coingecko_id?: string;
    market_cap?: number;
    liquidity_24h?: number;
    active: boolean;
    last_updated: Date;
}

export interface Signal {
    id: string;
    token_id: string;
    ml_prob: number;
    rule_score: number;
    sentiment_score: number;
    event_score: number;
    composite_score: number;
    action: 'buy' | 'sell' | 'hold';
    confidence: number;
    weights_used: {
        ml_weight: number;
        rule_weight: number;
        sentiment_weight: number;
        event_weight: number;
    };
    min_threshold: number;
    timestamp: Date;
}

export interface Trade {
    id: string;
    signal_id: string;
    token_id: string;
    action: 'buy' | 'sell';
    quantity: number;
    price: number;
    total_cost?: number;
    total_proceeds?: number;
    pnl?: number;
    pnl_pct?: number;
    composite_score: number;
    status: 'open' | 'closed';
    timestamp: Date;
}

export interface PortfolioPosition {
    token_id: string;
    quantity: number;
    avg_cost: number;
    current_value: number;
    cost_basis: number;
    pnl: number;
    pnl_pct: number;
    last_updated: Date;
}

export interface Portfolio {
    positions: PortfolioPosition[];
    summary: {
        total_value: number;
        total_cost: number;
        total_pnl: number;
        total_pnl_pct: number;
        position_count: number;
    };
}

export interface SystemHealth {
    status: 'healthy' | 'degraded' | 'error';
    timestamp: string;
    services: {
        [serviceName: string]: {
            status: string;
            last_run: string | null;
            count: number;
            duration: number;
        };
    };
    total_runs_24h: number;
    environment: string;
}

export interface AdminConfig {
    ml_weight: number;
    rule_weight: number;
    sentiment_weight: number;
    event_weight: number;
    min_composite_score: number;
}

export interface ModelInfo {
    id: string;
    model_id: string;
    model_type: string;
    version: string;
    training_date: Date;
    accuracy: number;
    auc_score: number;
    cv_mean: number;
    cv_std: number;
    training_samples: number;
    feature_count: number;
    status: 'active' | 'inactive';
}

export interface ApiResponse<T> {
    status: 'success' | 'error';
    data?: T;
    message?: string;
    error?: string;
}

export interface DashboardStats {
    total_signals_24h: number;
    high_confidence_signals: number;
    active_trades: number;
    portfolio_value: number;
    portfolio_pnl: number;
    portfolio_pnl_pct: number;
    system_health: 'healthy' | 'degraded' | 'error';
    last_updated: Date;
}

export interface ChartDataPoint {
    timestamp: Date;
    value: number;
    label?: string;
}

export interface TokenDetail {
    token: Token;
    latest_signal?: Signal;
    price_history: ChartDataPoint[];
    current_position?: PortfolioPosition;
    recent_trades: Trade[];
}