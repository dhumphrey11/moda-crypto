import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcp_firestore
from datetime import datetime
from typing import Dict, List, Any
import logging
from .config import settings

# Initialize Firebase Admin SDK


def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    if not firebase_admin._apps:
        try:
            logging.info("Initializing Firebase Admin SDK...")
            
            # Validate required settings
            if not settings.firebase_project_id:
                raise ValueError("FIREBASE_PROJECT_ID is required")
            if not settings.firebase_client_email:
                raise ValueError("FIREBASE_CLIENT_EMAIL is required") 
            if not settings.firebase_private_key:
                raise ValueError("FIREBASE_PRIVATE_KEY is required")
                
            # Try to use service account file if provided
            if settings.google_application_credentials:
                logging.info("Using service account file for Firebase initialization")
                cred = credentials.Certificate(
                    settings.google_application_credentials)
            else:
                logging.info("Using environment variables for Firebase initialization")
                # Use environment variables - ensure private key format is correct
                private_key = settings.firebase_private_key
                if private_key and not private_key.startswith('-----BEGIN'):
                    # Handle base64 encoded or escaped private key
                    private_key = private_key.replace('\\n', '\n')
                    if not private_key.startswith('-----BEGIN'):
                        import base64
                        try:
                            private_key = base64.b64decode(private_key).decode('utf-8')
                        except:
                            pass  # Use as-is if decode fails
                
                cred_dict = {
                    "type": "service_account",
                    "project_id": settings.firebase_project_id,
                    "client_email": settings.firebase_client_email,
                    "private_key": private_key,
                    "private_key_id": "1",
                    "client_id": "1",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                }
                cred = credentials.Certificate(cred_dict)

            firebase_admin.initialize_app(cred, {
                'storageBucket': settings.firebase_storage_bucket
            })
            logging.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {e}")
            raise

# Initialize Firestore client


def get_firestore_client():
    """Get Firestore client instance."""
    if not firebase_admin._apps:
        initialize_firebase()
    return firestore.client()


# Global Firestore client
db = None


def init_db():
    """Initialize global database client."""
    global db
    if db is None:
        try:
            db = get_firestore_client()
            logging.info("Firestore client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Firestore client: {e}")
            raise
    return db

# Helper functions for common Firestore operations


def write_run(service: str, count: int, status: str, duration: float = 0.0) -> None:
    """Write a run log entry to Firestore."""
    try:
        db = init_db()
        run_data = {
            'service': service,
            'timestamp': datetime.utcnow(),
            'status': status,
            'count': count,
            'duration': duration
        }
        db.collection('runs').add(run_data)
        logging.info(f"Run logged: {service} - {status} ({count} items)")
    except Exception as e:
        logging.error(f"Failed to write run log: {e}")


def write_features(token_id: str, features: Dict[str, Any]) -> None:
    """Write feature data to Firestore."""
    try:
        db = init_db()
        feature_data = {
            'token_id': token_id,
            'timestamp': datetime.utcnow(),
            **features
        }
        db.collection('features').add(feature_data)
        logging.debug(f"Features written for token: {token_id}")
    except Exception as e:
        logging.error(f"Failed to write features: {e}")


def write_signal(signal_data: Dict[str, Any]) -> str:
    """Write signal data to Firestore and return document ID."""
    try:
        db = init_db()
        signal_data['timestamp'] = datetime.utcnow()
        doc_ref = db.collection('signals').add(signal_data)
        logging.debug(
            f"Signal written for token: {signal_data.get('token_id')}")
        return doc_ref[1].id
    except Exception as e:
        logging.error(f"Failed to write signal: {e}")
        return ""


def write_trade(trade_data: Dict[str, Any]) -> str:
    """Write trade data to Firestore and return document ID."""
    try:
        db = init_db()
        trade_data['timestamp'] = datetime.utcnow()
        doc_ref = db.collection('trades').add(trade_data)
        logging.info(
            f"Trade written: {trade_data.get('action')} {trade_data.get('token_id')}")
        return doc_ref[1].id
    except Exception as e:
        logging.error(f"Failed to write trade: {e}")
        return ""


def get_tokens_list() -> List[Dict[str, Any]]:
    """Get list of all tokens from Firestore."""
    try:
        db = init_db()
        tokens = []
        docs = db.collection('tokens').stream()
        for doc in docs:
            token_data = doc.to_dict()
            token_data['id'] = doc.id
            tokens.append(token_data)
        return tokens
    except Exception as e:
        logging.error(f"Failed to get tokens list: {e}")
        return []


def get_admin_config() -> Dict[str, Any]:
    """Get admin configuration from Firestore."""
    try:
        db = init_db()
        doc = db.collection('adminConfig').document('default').get()
        if doc.exists:
            data = doc.to_dict()
            return data if data is not None else {}
        else:
            # Return default config if not found
            default_config = {
                'ml_weight': 0.4,
                'rule_weight': 0.3,
                'sentiment_weight': 0.2,
                'event_weight': 0.1,
                'min_composite_score': settings.min_composite_score
            }
            # Write default config
            db.collection('adminConfig').document(
                'default').set(default_config)
            return default_config
    except Exception as e:
        logging.error(f"Failed to get admin config: {e}")
        return {
            'ml_weight': 0.4,
            'rule_weight': 0.3,
            'sentiment_weight': 0.2,
            'event_weight': 0.1,
            'min_composite_score': settings.min_composite_score
        }


def get_portfolio() -> Dict[str, Any]:
    """Get current portfolio from Firestore."""
    try:
        db = init_db()
        portfolio = {}
        docs = db.collection('portfolio').stream()
        for doc in docs:
            data = doc.to_dict()
            portfolio[doc.id] = data
        return portfolio
    except Exception as e:
        logging.error(f"Failed to get portfolio: {e}")
        return {}


def update_portfolio(token_id: str, quantity: float, avg_cost: float) -> None:
    """Update portfolio position in Firestore."""
    try:
        db = init_db()
        portfolio_data = {
            'token_id': token_id,
            'quantity': quantity,
            'avg_cost': avg_cost,
            'last_updated': datetime.utcnow()
        }
        db.collection('portfolio').document(
            token_id).set(portfolio_data, merge=True)
        logging.info(f"Portfolio updated: {token_id}")
    except Exception as e:
        logging.error(f"Failed to update portfolio: {e}")


def get_recent_signals(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent signals from Firestore."""
    try:
        db = init_db()
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        signals = []
        docs = db.collection('signals')\
            .where('timestamp', '>=', cutoff_time)\
            .order_by('timestamp', direction=gcp_firestore.Query.DESCENDING)\
            .stream()

        for doc in docs:
            signal_data = doc.to_dict()
            signal_data['id'] = doc.id
            signals.append(signal_data)

        return signals
    except Exception as e:
        logging.error(f"Failed to get recent signals: {e}")
        return []


def get_open_trades() -> List[Dict[str, Any]]:
    """Get open trades from Firestore."""
    try:
        db = init_db()
        trades = []
        docs = db.collection('trades')\
            .where('status', '==', 'open')\
            .stream()

        for doc in docs:
            trade_data = doc.to_dict()
            trade_data['id'] = doc.id
            trades.append(trade_data)

        return trades
    except Exception as e:
        logging.error(f"Failed to get open trades: {e}")
        return []


def get_recent_runs(hours: int = 24) -> List[Dict[str, Any]]:
    """Get recent run logs from Firestore."""
    try:
        db = init_db()
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        runs = []
        docs = db.collection('runs')\
                 .where('timestamp', '>=', cutoff_time)\
                 .order_by('timestamp', direction=gcp_firestore.Query.DESCENDING)\
                 .stream()

        for doc in docs:
            run_data = doc.to_dict()
            run_data['id'] = doc.id
            runs.append(run_data)

        return runs
    except Exception as e:
        logging.error(f"Failed to get recent runs: {e}")
        return []
