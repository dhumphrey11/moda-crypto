import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import ta  # Technical analysis library

from ..firestore_client import init_db, write_features
from ..config import settings


async def engineer_features(token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Engineer features for a given token.

    This function combines market data, technical indicators, on-chain metrics,
    social sentiment, and event data to create a comprehensive feature set.

    Args:
        token: Token information dictionary

    Returns:
        Dictionary of engineered features or None if insufficient data
    """
    try:
        token_id = token.get('id') or token.get('symbol', 'unknown')
        symbol = token.get('symbol', '').upper()

        logging.debug(f"Engineering features for {symbol}")

        # Initialize features dictionary
        features = {
            'token_id': symbol,
            'timestamp': datetime.utcnow()
        }

        # Get Firestore client
        db = init_db()

        # 1. Technical Analysis Features
        ta_features = await _calculate_technical_features(db, symbol)
        if ta_features:
            features.update(ta_features)

        # 2. Market Features
        market_features = await _calculate_market_features(db, symbol)
        if market_features:
            features.update(market_features)

        # 3. On-chain Features
        onchain_features = await _calculate_onchain_features(db, symbol)
        if onchain_features:
            features.update(onchain_features)

        # 4. Social Sentiment Features
        social_features = await _calculate_social_features(db, symbol)
        if social_features:
            features.update(social_features)

        # 5. Event-based Features
        event_features = await _calculate_event_features(db, symbol)
        if event_features:
            features.update(event_features)

        # 6. Cross-market Features
        cross_features = await _calculate_cross_market_features(db, symbol)
        if cross_features:
            features.update(cross_features)

        # Store features in Firestore
        write_features(symbol, features)

        logging.debug(f"Generated {len(features)} features for {symbol}")
        return features

    except Exception as e:
        logging.error(
            f"Feature engineering failed for {token.get('symbol', 'unknown')}: {e}")
        return None


async def _calculate_technical_features(db, symbol: str) -> Dict[str, Any]:
    """Calculate technical analysis features."""
    try:
        # Get recent price data (last 30 days for TA calculations)
        cutoff_time = datetime.utcnow() - timedelta(days=30)

        # Query recent market data
        docs = db.collection('features')\
                 .where('token_id', '==', symbol)\
                 .where('timestamp', '>=', cutoff_time)\
                 .order_by('timestamp')\
                 .limit(100)\
                 .stream()

        price_data = []
        for doc in docs:
            data = doc.to_dict()
            if 'current_price' in data:
                price_data.append({
                    'timestamp': data['timestamp'],
                    'price': float(data['current_price']),
                    'volume': float(data.get('volume_24h', 0))
                })

        if len(price_data) < 14:  # Need minimum data for TA
            return {}

        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Calculate technical indicators
        features = {}

        # Price-based indicators
        features['sma_7'] = df['price'].rolling(window=7).mean(
        ).iloc[-1] if len(df) >= 7 else df['price'].mean()
        features['sma_14'] = df['price'].rolling(window=14).mean().iloc[-1]
        features['ema_7'] = df['price'].ewm(span=7).mean(
        ).iloc[-1] if len(df) >= 7 else df['price'].mean()
        features['ema_14'] = df['price'].ewm(span=14).mean().iloc[-1]

        # RSI
        if len(df) >= 14:
            rsi = ta.momentum.RSIIndicator(df['price'], window=14)
            features['rsi_14'] = rsi.rsi().iloc[-1]
        else:
            features['rsi_14'] = 50.0  # Neutral

        # MACD
        if len(df) >= 26:
            macd = ta.trend.MACD(df['price'])
            features['macd'] = macd.macd().iloc[-1]
            features['macd_signal'] = macd.macd_signal().iloc[-1]
            features['macd_histogram'] = macd.macd_diff().iloc[-1]

        # Bollinger Bands
        if len(df) >= 20:
            bb = ta.volatility.BollingerBands(df['price'], window=20)
            current_price = df['price'].iloc[-1]
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]
            bb_middle = bb.bollinger_mavg().iloc[-1]

            features['bb_position'] = (
                current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
            features['bb_width'] = (bb_upper - bb_lower) / \
                bb_middle if bb_middle != 0 else 0

        # Price momentum
        if len(df) >= 7:
            features['price_change_7d'] = (
                df['price'].iloc[-1] - df['price'].iloc[-7]) / df['price'].iloc[-7]
        if len(df) >= 14:
            features['price_change_14d'] = (
                df['price'].iloc[-1] - df['price'].iloc[-14]) / df['price'].iloc[-14]

        # Volume indicators
        if 'volume' in df.columns and df['volume'].sum() > 0:
            features['volume_sma_7'] = df['volume'].rolling(
                window=7).mean().iloc[-1] if len(df) >= 7 else df['volume'].mean()
            features['volume_ratio'] = df['volume'].iloc[-1] / \
                features['volume_sma_7'] if features['volume_sma_7'] > 0 else 1.0

        # Volatility
        if len(df) >= 7:
            returns = df['price'].pct_change().dropna()
            features['volatility_7d'] = returns.tail(
                7).std() * np.sqrt(7) if len(returns) > 0 else 0

        return features

    except Exception as e:
        logging.error(
            f"Technical features calculation failed for {symbol}: {e}")
        return {}


async def _calculate_market_features(db, symbol: str) -> Dict[str, Any]:
    """Calculate market-based features."""
    try:
        # Get recent market data
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        docs = db.collection('features')\
                 .where('token_id', '==', symbol)\
                 .where('timestamp', '>=', cutoff_time)\
                 .order_by('timestamp', direction='DESCENDING')\
                 .limit(10)\
                 .stream()

        market_data = []
        for doc in docs:
            data = doc.to_dict()
            market_data.append(data)

        if not market_data:
            return {}

        latest = market_data[0]
        features = {}

        # Basic market metrics
        features['current_price'] = float(latest.get('current_price', 0))
        features['market_cap'] = float(latest.get('market_cap', 0))
        features['volume_24h'] = float(latest.get('volume_24h', 0))
        features['price_change_24h'] = float(latest.get('price_change_24h', 0))
        features['price_change_percentage_24h'] = float(
            latest.get('price_change_percentage_24h', 0))

        # Market cap rank (lower is better)
        market_cap_rank = latest.get('market_cap_rank', 1000)
        features['market_cap_rank_score'] = max(
            0, (1000 - market_cap_rank) / 1000) if market_cap_rank else 0

        # Liquidity score (volume to market cap ratio)
        if features['market_cap'] > 0:
            features['liquidity_ratio'] = features['volume_24h'] / \
                features['market_cap']
        else:
            features['liquidity_ratio'] = 0

        return features

    except Exception as e:
        logging.error(f"Market features calculation failed for {symbol}: {e}")
        return {}


async def _calculate_onchain_features(db, symbol: str) -> Dict[str, Any]:
    """Calculate on-chain features."""
    try:
        # Get recent on-chain events
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        docs = db.collection('events')\
                 .where('event_type', '==', 'onchain_activity')\
                 .where('timestamp', '>=', cutoff_time)\
                 .stream()

        onchain_events = []
        for doc in docs:
            data = doc.to_dict()
            # Filter for events that might relate to this token
            # This is a simplified approach - in production you'd have better token-address mapping
            onchain_events.append(data)

        features = {}

        if onchain_events:
            # Aggregate on-chain activity
            total_activity = sum(event.get('metrics', {}).get(
                'activity_score', 0) for event in onchain_events)
            features['onchain_activity_7d'] = total_activity / \
                len(onchain_events) if onchain_events else 0

            # Count of on-chain events
            features['onchain_events_count_7d'] = len(onchain_events)
        else:
            features['onchain_activity_7d'] = 0
            features['onchain_events_count_7d'] = 0

        return features

    except Exception as e:
        logging.error(
            f"On-chain features calculation failed for {symbol}: {e}")
        return {}


async def _calculate_social_features(db, symbol: str) -> Dict[str, Any]:
    """Calculate social sentiment features."""
    try:
        # Get recent social data
        cutoff_time = datetime.utcnow() - timedelta(days=3)

        docs = db.collection('features')\
                 .where('token_id', '==', symbol)\
                 .where('feature_type', '==', 'social')\
                 .where('timestamp', '>=', cutoff_time)\
                 .order_by('timestamp', direction='DESCENDING')\
                 .limit(10)\
                 .stream()

        social_data = []
        for doc in docs:
            data = doc.to_dict()
            social_data.append(data)

        features = {}

        if social_data:
            # Average social metrics
            features['social_score'] = np.mean(
                [d.get('social_score', 0) for d in social_data])
            features['sentiment'] = np.mean(
                [d.get('sentiment', 0) for d in social_data])
            features['social_volume_24h'] = np.mean(
                [d.get('social_volume_24h', 0) for d in social_data])
            features['tweets_24h'] = np.mean(
                [d.get('tweets_24h', 0) for d in social_data])
            features['reddit_posts_24h'] = np.mean(
                [d.get('reddit_posts_24h', 0) for d in social_data])

            # Composite social score
            features['composite_social_score'] = np.mean(
                [d.get('composite_social_score', 0) for d in social_data])
        else:
            # Default neutral values
            features['social_score'] = 50.0
            features['sentiment'] = 0.0
            features['social_volume_24h'] = 0.0
            features['tweets_24h'] = 0.0
            features['reddit_posts_24h'] = 0.0
            features['composite_social_score'] = 0.5

        return features

    except Exception as e:
        logging.error(f"Social features calculation failed for {symbol}: {e}")
        return {}


async def _calculate_event_features(db, symbol: str) -> Dict[str, Any]:
    """Calculate event-based features."""
    try:
        # Get recent events for this token
        cutoff_time = datetime.utcnow() - timedelta(days=14)

        docs = db.collection('events')\
                 .where('token_id', '==', symbol)\
                 .where('timestamp', '>=', cutoff_time)\
                 .order_by('timestamp', direction='DESCENDING')\
                 .limit(20)\
                 .stream()

        events = []
        for doc in docs:
            data = doc.to_dict()
            events.append(data)

        features = {}

        if events:
            # Count events by type
            event_types = {}
            total_impact = 0
            positive_events = 0
            negative_events = 0

            for event in events:
                event_type = event.get('event_type', 'unknown')
                impact_score = event.get('impact_score', 0)

                event_types[event_type] = event_types.get(event_type, 0) + 1
                total_impact += impact_score

                # Classify events as positive/negative based on type and sentiment
                if event_type in ['scheduled_event', 'token_event'] and impact_score > 0.5:
                    positive_events += 1
                elif event_type in ['news', 'token_news']:
                    sentiment = event.get('sentiment_score', 0)
                    if sentiment > 0:
                        positive_events += 1
                    elif sentiment < 0:
                        negative_events += 1

            features['events_count_14d'] = len(events)
            features['average_event_impact'] = total_impact / \
                len(events) if events else 0
            features['positive_events_14d'] = positive_events
            features['negative_events_14d'] = negative_events
            features['event_sentiment_ratio'] = (
                positive_events - negative_events) / len(events) if events else 0

            # Specific event type counts
            features['scheduled_events_14d'] = event_types.get(
                'scheduled_event', 0)
            features['news_events_14d'] = event_types.get(
                'news', 0) + event_types.get('token_news', 0)
        else:
            features['events_count_14d'] = 0
            features['average_event_impact'] = 0
            features['positive_events_14d'] = 0
            features['negative_events_14d'] = 0
            features['event_sentiment_ratio'] = 0
            features['scheduled_events_14d'] = 0
            features['news_events_14d'] = 0

        return features

    except Exception as e:
        logging.error(f"Event features calculation failed for {symbol}: {e}")
        return {}


async def _calculate_cross_market_features(db, symbol: str) -> Dict[str, Any]:
    """Calculate cross-market correlation features."""
    try:
        # Get BTC price movement for correlation (market leader)
        cutoff_time = datetime.utcnow() - timedelta(days=7)

        # Get BTC data
        btc_docs = db.collection('features')\
                     .where('token_id', '==', 'BTC')\
                     .where('timestamp', '>=', cutoff_time)\
                     .order_by('timestamp')\
                     .limit(50)\
                     .stream()

        btc_prices = []
        for doc in btc_docs:
            data = doc.to_dict()
            if 'current_price' in data:
                btc_prices.append(float(data['current_price']))

        # Get this token's data
        token_docs = db.collection('features')\
                       .where('token_id', '==', symbol)\
                       .where('timestamp', '>=', cutoff_time)\
                       .order_by('timestamp')\
                       .limit(50)\
                       .stream()

        token_prices = []
        for doc in token_docs:
            data = doc.to_dict()
            if 'current_price' in data:
                token_prices.append(float(data['current_price']))

        features = {}

        # Calculate correlation with BTC
        if len(btc_prices) >= 5 and len(token_prices) >= 5:
            min_len = min(len(btc_prices), len(token_prices))
            btc_returns = np.diff(
                btc_prices[:min_len]) / btc_prices[:min_len-1]
            token_returns = np.diff(
                token_prices[:min_len]) / token_prices[:min_len-1]

            if len(btc_returns) > 0 and len(token_returns) > 0:
                correlation = np.corrcoef(btc_returns, token_returns)[0, 1]
                features['btc_correlation'] = correlation if not np.isnan(
                    correlation) else 0
            else:
                features['btc_correlation'] = 0
        else:
            features['btc_correlation'] = 0

        # Market beta (volatility relative to BTC)
        if len(btc_prices) >= 5 and len(token_prices) >= 5:
            btc_volatility = np.std(btc_returns) if 'btc_returns' in locals() and len(
                btc_returns) > 0 else 0
            token_volatility = np.std(token_returns) if 'token_returns' in locals(
            ) and len(token_returns) > 0 else 0

            features['market_beta'] = token_volatility / \
                btc_volatility if btc_volatility > 0 else 1.0
        else:
            features['market_beta'] = 1.0

        return features

    except Exception as e:
        logging.error(
            f"Cross-market features calculation failed for {symbol}: {e}")
        return {}
