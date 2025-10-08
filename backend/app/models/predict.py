import numpy as np
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List

from ..firestore_client import init_db, write_signal, get_admin_config
from ..config import settings

# Model storage paths
MODEL_DIR = "models"


async def predict_signals(token: Dict[str, Any], features: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generate trading signals using ML model and rule-based scoring.

    This function:
    1. Loads the active ML model
    2. Generates ML probability prediction
    3. Calculates rule-based scores
    4. Combines scores using admin weights
    5. Generates final trading signal

    Args:
        token: Token information dictionary
        features: Engineered features dictionary

    Returns:
        Signal dictionary with scores and action, or None if prediction fails
    """
    try:
        token_id = token.get('id') or token.get('symbol', 'unknown')
        symbol = features.get('token_id', token_id)

        logging.debug(f"Generating signal for {symbol}")

        # 1. Get ML prediction
        ml_prob = await _get_ml_prediction(features)

        # 2. Calculate component scores
        rule_score = _calculate_rule_score(features)
        sentiment_score = _calculate_sentiment_score(features)
        event_score = _calculate_event_score(features)

        # 3. Get admin configuration for weights
        admin_config = get_admin_config()
        weights = {
            'ml_weight': admin_config.get('ml_weight', 0.4),
            'rule_weight': admin_config.get('rule_weight', 0.3),
            'sentiment_weight': admin_config.get('sentiment_weight', 0.2),
            'event_weight': admin_config.get('event_weight', 0.1)
        }

        # 4. Calculate composite score
        composite_score = (
            ml_prob * weights['ml_weight'] +
            rule_score * weights['rule_weight'] +
            sentiment_score * weights['sentiment_weight'] +
            event_score * weights['event_weight']
        )

        # 5. Determine trading action
        min_score = admin_config.get(
            'min_composite_score', settings.min_composite_score)

        if composite_score >= min_score:
            action = 'buy'
        elif composite_score <= (1 - min_score):
            action = 'sell'
        else:
            action = 'hold'

        # 6. Create signal
        signal = {
            'token_id': symbol,
            'ml_prob': ml_prob,
            'rule_score': rule_score,
            'sentiment_score': sentiment_score,
            'event_score': event_score,
            'composite_score': composite_score,
            'action': action,
            'confidence': abs(composite_score - 0.5) * 2,  # 0 to 1 scale
            'weights_used': weights,
            'min_threshold': min_score,
            'timestamp': datetime.utcnow()
        }

        # 7. Store signal in Firestore
        signal_id = write_signal(signal)
        signal['id'] = signal_id

        logging.debug(
            f"Signal generated for {symbol}: {action} (score: {composite_score:.3f})")

        return signal

    except Exception as e:
        logging.error(
            f"Signal prediction failed for {token.get('symbol', 'unknown')}: {e}")
        return None


async def _get_ml_prediction(features: Dict[str, Any]) -> float:
    """Get ML model prediction probability."""
    try:
        # Load active model
        model_info = _get_active_model()
        if not model_info:
            logging.warning("No active model found, using default ML score")
            return 0.5

        # Load model artifacts
        model = _load_model_artifacts(model_info)
        if not model:
            logging.warning("Failed to load model, using default ML score")
            return 0.5

        # Prepare features for prediction
        feature_vector = _prepare_features_for_prediction(
            features, model['feature_names'])
        if feature_vector is None:
            return 0.5

        # Scale features
        if model['scaler']:
            feature_vector = model['scaler'].transform([feature_vector])
        else:
            feature_vector = [feature_vector]

        # Get prediction probability
        prob = model['model'].predict_proba(
            feature_vector)[0][1]  # Probability of positive class

        return float(prob)

    except Exception as e:
        logging.error(f"ML prediction failed: {e}")
        return 0.5


def _calculate_rule_score(features: Dict[str, Any]) -> float:
    """Calculate rule-based technical analysis score."""
    try:
        score = 0.0
        rule_count = 0

        # RSI rules
        rsi = features.get('rsi_14', 50)
        if rsi < 30:  # Oversold
            score += 0.8
        elif rsi < 40:
            score += 0.6
        elif rsi > 70:  # Overbought
            score += 0.2
        elif rsi > 60:
            score += 0.4
        else:
            score += 0.5
        rule_count += 1

        # MACD rules
        macd = features.get('macd', 0)
        macd_signal = features.get('macd_signal', 0)
        if macd > macd_signal and macd > 0:  # Bullish crossover above zero
            score += 0.8
        elif macd > macd_signal:  # Bullish crossover
            score += 0.6
        elif macd < macd_signal and macd < 0:  # Bearish crossover below zero
            score += 0.2
        elif macd < macd_signal:  # Bearish crossover
            score += 0.4
        else:
            score += 0.5
        rule_count += 1

        # Bollinger Bands
        bb_position = features.get('bb_position', 0.5)
        if bb_position < 0.1:  # Near lower band
            score += 0.7
        elif bb_position < 0.3:
            score += 0.6
        elif bb_position > 0.9:  # Near upper band
            score += 0.3
        elif bb_position > 0.7:
            score += 0.4
        else:
            score += 0.5
        rule_count += 1

        # Price momentum
        price_change_7d = features.get('price_change_7d', 0)
        if price_change_7d > 0.1:  # Strong upward momentum
            score += 0.8
        elif price_change_7d > 0.05:
            score += 0.6
        elif price_change_7d < -0.1:  # Strong downward momentum
            score += 0.2
        elif price_change_7d < -0.05:
            score += 0.4
        else:
            score += 0.5
        rule_count += 1

        # Volume analysis
        volume_ratio = features.get('volume_ratio', 1.0)
        if volume_ratio > 2.0:  # High volume
            score += 0.7
        elif volume_ratio > 1.5:
            score += 0.6
        elif volume_ratio < 0.5:  # Low volume
            score += 0.4
        else:
            score += 0.5
        rule_count += 1

        # Volatility consideration
        volatility = features.get('volatility_7d', 0.05)
        if volatility > 0.15:  # High volatility - reduce confidence
            score *= 0.9
        elif volatility < 0.02:  # Very low volatility
            score *= 0.95

        return score / rule_count if rule_count > 0 else 0.5

    except Exception as e:
        logging.error(f"Rule score calculation failed: {e}")
        return 0.5


def _calculate_sentiment_score(features: Dict[str, Any]) -> float:
    """Calculate sentiment-based score."""
    try:
        score = 0.5  # Neutral baseline

        # Social sentiment
        sentiment = features.get('sentiment', 0)
        social_score = features.get('social_score', 50)
        composite_social = features.get('composite_social_score', 0.5)

        # Normalize social score (assuming 0-100 scale)
        normalized_social = social_score / \
            100 if social_score <= 100 else min(social_score / 1000, 1.0)

        # Normalize sentiment (assuming -5 to +5 scale, convert to 0-1)
        normalized_sentiment = (sentiment + 5) / \
            10 if abs(sentiment) <= 5 else 0.5

        # Combine sentiment indicators
        sentiment_score = (
            normalized_social * 0.4 +
            normalized_sentiment * 0.4 +
            composite_social * 0.2
        )

        # Social volume boost
        tweets_24h = features.get('tweets_24h', 0)
        reddit_posts_24h = features.get('reddit_posts_24h', 0)
        social_volume = features.get('social_volume_24h', 0)

        # Boost score for high social activity
        activity_multiplier = 1.0
        if tweets_24h > 100 or reddit_posts_24h > 50 or social_volume > 1000:
            activity_multiplier = 1.1
        elif tweets_24h > 50 or reddit_posts_24h > 20 or social_volume > 500:
            activity_multiplier = 1.05

        final_score = min(sentiment_score * activity_multiplier, 1.0)

        return final_score

    except Exception as e:
        logging.error(f"Sentiment score calculation failed: {e}")
        return 0.5


def _calculate_event_score(features: Dict[str, Any]) -> float:
    """Calculate event-based score."""
    try:
        score = 0.5  # Neutral baseline

        # Event counts and impact
        events_count = features.get('events_count_14d', 0)
        avg_impact = features.get('average_event_impact', 0)
        positive_events = features.get('positive_events_14d', 0)
        negative_events = features.get('negative_events_14d', 0)
        event_sentiment_ratio = features.get('event_sentiment_ratio', 0)

        if events_count > 0:
            # Base score from average impact
            impact_score = avg_impact

            # Adjust for event sentiment
            sentiment_adjustment = event_sentiment_ratio * 0.2  # -0.2 to +0.2
            impact_score += sentiment_adjustment

            # Boost for positive events
            if positive_events > negative_events:
                impact_score += 0.1

            # Recent scheduled events boost
            scheduled_events = features.get('scheduled_events_14d', 0)
            if scheduled_events > 0:
                impact_score += min(scheduled_events * 0.05, 0.2)

            score = min(max(impact_score, 0), 1.0)

        return score

    except Exception as e:
        logging.error(f"Event score calculation failed: {e}")
        return 0.5


def _get_active_model() -> Optional[Dict[str, Any]]:
    """Get active model information from Firestore."""
    try:
        db = init_db()

        docs = db.collection('models')\
                 .where('status', '==', 'active')\
                 .order_by('training_date', direction='DESCENDING')\
                 .limit(1)\
                 .stream()

        for doc in docs:
            model_info = doc.to_dict()
            model_info['id'] = doc.id
            return model_info

        return None

    except Exception as e:
        logging.error(f"Failed to get active model: {e}")
        return None


def _load_model_artifacts(model_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load model, scaler, and feature names from disk."""
    try:
        local_paths = model_info.get('local_paths', {})

        model_path = local_paths.get('model')
        scaler_path = local_paths.get('scaler')
        features_path = local_paths.get('features')

        if not all([model_path, scaler_path, features_path]):
            logging.error("Missing model artifact paths")
            return None

        if not all([os.path.exists(model_path), os.path.exists(scaler_path), os.path.exists(features_path)]):
            logging.error("Model artifact files not found")
            return None

        # Load artifacts
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        feature_names = joblib.load(features_path)

        return {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names
        }

    except Exception as e:
        logging.error(f"Failed to load model artifacts: {e}")
        return None


def _prepare_features_for_prediction(features: Dict[str, Any], expected_features: List[str]) -> Optional[List[float]]:
    """Prepare feature vector for model prediction."""
    try:
        feature_vector = []

        for feature_name in expected_features:
            if feature_name in features:
                value = features[feature_name]
                # Convert to float, handle None values
                if value is None:
                    feature_vector.append(0.0)
                else:
                    feature_vector.append(float(value))
            else:
                # Missing feature - use default value
                feature_vector.append(0.0)
                logging.debug(
                    f"Missing feature {feature_name}, using default value")

        return feature_vector

    except Exception as e:
        logging.error(f"Feature preparation failed: {e}")
        return None
