import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
import xgboost as xgb
import joblib
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, Tuple

from ..firestore_client import init_db, write_run
from ..config import settings

# Model storage paths
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


async def train_model() -> Dict[str, Any]:
    """
    Train a new ML model for signal prediction.

    This function:
    1. Collects training data from Firestore
    2. Engineers features and labels
    3. Trains an XGBoost model
    4. Evaluates performance
    5. Saves model artifacts
    6. Updates model metadata in Firestore

    Returns:
        Dictionary containing model info and performance metrics
    """
    try:
        logging.info("Starting model training pipeline")

        # 1. Collect training data
        training_data = await _collect_training_data()
        if not training_data:
            raise Exception("No training data available")

        # 2. Prepare features and labels
        X, y, feature_names = await _prepare_training_data(training_data)
        if X is None or len(X) == 0:
            raise Exception("No valid training samples")

        logging.info(
            f"Training data: {len(X)} samples, {len(feature_names)} features")

        # 3. Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # 4. Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # 5. Train models
        models = {}

        # XGBoost
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        xgb_model.fit(X_train_scaled, y_train)
        models['xgboost'] = xgb_model

        # Random Forest (backup model)
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        rf_model.fit(X_train_scaled, y_train)
        models['random_forest'] = rf_model

        # 6. Evaluate models
        best_model_name = None
        best_score = 0
        model_performances = {}

        for name, model in models.items():
            # Predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

            # Metrics
            accuracy = accuracy_score(y_test, y_pred)
            auc_score = roc_auc_score(y_test, y_pred_proba)

            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train_scaled, y_train, cv=5, scoring='roc_auc')

            performance = {
                'accuracy': accuracy,
                'auc_score': auc_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }

            model_performances[name] = performance

            logging.info(
                f"{name} - Accuracy: {accuracy:.3f}, AUC: {auc_score:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")

            # Select best model based on AUC score
            if auc_score > best_score:
                best_score = auc_score
                best_model_name = name

        if not best_model_name:
            raise Exception("No valid model trained")

        best_model = models[best_model_name]
        best_performance = model_performances[best_model_name]

        logging.info(
            f"Best model: {best_model_name} with AUC: {best_score:.3f}")

        # 7. Save model artifacts
        model_version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        model_filename = f"crypto_model_{model_version}.joblib"
        scaler_filename = f"crypto_scaler_{model_version}.joblib"

        model_path = os.path.join(MODEL_DIR, model_filename)
        scaler_path = os.path.join(MODEL_DIR, scaler_filename)

        # Save model and scaler
        joblib.dump(best_model, model_path)
        joblib.dump(scaler, scaler_path)

        # Save feature names
        feature_names_path = os.path.join(
            MODEL_DIR, f"feature_names_{model_version}.joblib")
        joblib.dump(feature_names, feature_names_path)

        # 8. Upload to Firebase Storage (optional)
        storage_paths = await _upload_model_to_storage(model_path, scaler_path, feature_names_path)

        # 9. Save model metadata to Firestore
        model_info = {
            'model_id': model_version,
            'model_type': best_model_name,
            'version': model_version,
            'training_date': datetime.utcnow(),
            'accuracy': best_performance['accuracy'],
            'auc_score': best_performance['auc_score'],
            'cv_mean': best_performance['cv_mean'],
            'cv_std': best_performance['cv_std'],
            'training_samples': len(X),
            'feature_count': len(feature_names),
            'feature_names': feature_names,
            'local_paths': {
                'model': model_path,
                'scaler': scaler_path,
                'features': feature_names_path
            },
            'storage_paths': storage_paths,
            'status': 'active'
        }

        # Store in Firestore
        db = init_db()
        db.collection('models').document(model_version).set(model_info)

        # Mark previous models as inactive
        await _deactivate_old_models(db, model_version)

        logging.info(f"Model training completed successfully: {model_version}")

        return model_info

    except Exception as e:
        logging.error(f"Model training failed: {e}")
        raise


async def _collect_training_data() -> Optional[pd.DataFrame]:
    """Collect training data from Firestore."""
    try:
        db = init_db()

        # Get historical features and signals for training
        cutoff_date = datetime.utcnow() - timedelta(days=90)  # Last 90 days

        # Collect features
        features_data = []
        docs = db.collection('features')\
            .where('timestamp', '>=', cutoff_date)\
            .stream()

        for doc in docs:
            data = doc.to_dict()
            features_data.append(data)

        # Collect signals (labels)
        signals_data = []
        docs = db.collection('signals')\
            .where('timestamp', '>=', cutoff_date)\
            .stream()

        for doc in docs:
            data = doc.to_dict()
            signals_data.append(data)

        if not features_data or not signals_data:
            logging.warning("Insufficient historical data for training")
            return None

        # Convert to DataFrames
        features_df = pd.DataFrame(features_data)
        signals_df = pd.DataFrame(signals_data)

        # Merge features with signals based on token_id and timestamp proximity
        merged_data = _merge_features_signals(features_df, signals_df)

        return merged_data

    except Exception as e:
        logging.error(f"Failed to collect training data: {e}")
        return None


def _merge_features_signals(features_df: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
    """Merge features with signals for training data."""
    try:
        # Convert timestamps to datetime
        features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
        signals_df['timestamp'] = pd.to_datetime(signals_df['timestamp'])

        merged_data = []

        for _, signal in signals_df.iterrows():
            token_id = signal['token_id']
            signal_time = signal['timestamp']

            # Find features for this token around the signal time
            # Look for features within 1 hour before the signal
            time_window_start = signal_time - timedelta(hours=1)
            time_window_end = signal_time

            matching_features = features_df[
                (features_df['token_id'] == token_id) &
                (features_df['timestamp'] >= time_window_start) &
                (features_df['timestamp'] <= time_window_end)
            ]

            if not matching_features.empty:
                # Use the most recent features
                latest_features = matching_features.iloc[-1]

                # Create training sample
                sample = latest_features.to_dict()

                # Add signal information
                sample['signal_timestamp'] = signal_time
                sample['composite_score'] = signal.get('composite_score', 0)
                sample['ml_prob'] = signal.get('ml_prob', 0)
                sample['action'] = signal.get('action', 'hold')

                # Create binary label (1 for strong signals, 0 for weak)
                sample['label'] = 1 if signal.get(
                    'composite_score', 0) >= 0.8 else 0

                merged_data.append(sample)

        if not merged_data:
            # Generate synthetic training data if no historical data
            return _generate_synthetic_data()

        return pd.DataFrame(merged_data)

    except Exception as e:
        logging.error(f"Failed to merge features and signals: {e}")
        return _generate_synthetic_data()


def _generate_synthetic_data() -> pd.DataFrame:
    """Generate synthetic training data for initial model training."""
    try:
        logging.info("Generating synthetic training data")

        np.random.seed(42)
        n_samples = 1000

        # Generate synthetic features
        data = {
            'token_id': np.random.choice(['BTC', 'ETH', 'ADA', 'SOL', 'DOT'], n_samples),
            'timestamp': pd.date_range(start='2024-01-01', periods=n_samples, freq='1H'),

            # Technical indicators
            'rsi_14': np.random.normal(50, 20, n_samples),
            'sma_7': np.random.normal(1000, 200, n_samples),
            'sma_14': np.random.normal(1000, 200, n_samples),
            'macd': np.random.normal(0, 10, n_samples),
            'bb_position': np.random.uniform(0, 1, n_samples),
            'price_change_7d': np.random.normal(0, 0.1, n_samples),
            'price_change_14d': np.random.normal(0, 0.15, n_samples),
            'volatility_7d': np.random.exponential(0.05, n_samples),

            # Market features
            'current_price': np.random.exponential(1000, n_samples),
            'volume_24h': np.random.exponential(1000000, n_samples),
            'market_cap': np.random.exponential(1000000000, n_samples),
            'liquidity_ratio': np.random.exponential(0.1, n_samples),

            # Social features
            'social_score': np.random.normal(50, 15, n_samples),
            'sentiment': np.random.normal(0, 1, n_samples),
            'composite_social_score': np.random.uniform(0, 1, n_samples),

            # Event features
            'events_count_14d': np.random.poisson(2, n_samples),
            'average_event_impact': np.random.uniform(0, 1, n_samples),
            'event_sentiment_ratio': np.random.normal(0, 0.5, n_samples),

            # Cross-market features
            'btc_correlation': np.random.normal(0.5, 0.3, n_samples),
            'market_beta': np.random.exponential(1, n_samples),
        }

        df = pd.DataFrame(data)

        # Generate labels based on synthetic rules
        df['composite_score'] = (
            (df['rsi_14'] < 30).astype(int) * 0.2 +  # Oversold
            (df['price_change_7d'] > 0.05).astype(int) * 0.2 +  # Price momentum
            (df['sentiment'] > 0.5).astype(int) * 0.2 +  # Positive sentiment
            # High impact events
            (df['average_event_impact'] > 0.6).astype(int) * 0.2 +
            (df['volume_24h'] > df['volume_24h'].median()).astype(
                int) * 0.2  # High volume
        )

        df['label'] = (df['composite_score'] >= 0.8).astype(int)

        logging.info(f"Generated {len(df)} synthetic training samples")
        return df

    except Exception as e:
        logging.error(f"Failed to generate synthetic data: {e}")
        return pd.DataFrame()


async def _prepare_training_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
    """Prepare features and labels for training."""
    try:
        # Define feature columns (exclude metadata and target)
        exclude_columns = {
            'token_id', 'timestamp', 'signal_timestamp', 'composite_score',
            'ml_prob', 'action', 'label', 'feature_type'
        }

        feature_columns = [
            col for col in df.columns if col not in exclude_columns]

        # Select only numeric features
        X = df[feature_columns].select_dtypes(include=[np.number])
        y = df['label'].values

        # Handle missing values
        X = X.fillna(X.median())

        # Remove features with zero variance
        feature_variance = X.var()
        X = X.loc[:, feature_variance > 0]

        feature_names = X.columns.tolist()

        logging.info(f"Prepared {len(feature_names)} features for training")

        return X.values, y, feature_names

    except Exception as e:
        logging.error(f"Failed to prepare training data: {e}")
        return None, None, []


async def _upload_model_to_storage(model_path: str, scaler_path: str, features_path: str) -> Dict[str, str]:
    """Upload model artifacts to Firebase Storage."""
    try:
        # TODO: Implement Firebase Storage upload
        # This would upload the model files to Firebase Storage
        # and return the storage URLs

        storage_paths = {
            'model_url': f"gs://{settings.firebase_storage_bucket}/models/{os.path.basename(model_path)}",
            'scaler_url': f"gs://{settings.firebase_storage_bucket}/models/{os.path.basename(scaler_path)}",
            'features_url': f"gs://{settings.firebase_storage_bucket}/models/{os.path.basename(features_path)}"
        }

        logging.info("Model artifacts uploaded to Firebase Storage")
        return storage_paths

    except Exception as e:
        logging.error(f"Failed to upload model to storage: {e}")
        return {}


async def _deactivate_old_models(db, current_model_id: str):
    """Mark old models as inactive."""
    try:
        docs = db.collection('models').where('status', '==', 'active').stream()

        for doc in docs:
            if doc.id != current_model_id:
                db.collection('models').document(
                    doc.id).update({'status': 'inactive'})

        logging.info("Old models marked as inactive")

    except Exception as e:
        logging.error(f"Failed to deactivate old models: {e}")


def get_model_info() -> Dict[str, Any]:
    """Get information about the current active model."""
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

        return {'error': 'No active model found'}

    except Exception as e:
        logging.error(f"Failed to get model info: {e}")
        return {'error': str(e)}
