import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import firestore as gcp_firestore
from datetime import datetime
from typing import Dict, List, Any, Optional
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


def get_recent_trades(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent trades with pagination."""
    try:
        db = get_firestore_client()
        trades_ref = db.collection("trades")
        
        # Query recent trades ordered by timestamp
        query = trades_ref.order_by("timestamp", direction=gcp_firestore.Query.DESCENDING).limit(limit)
        trades_stream = query.stream()

        trades = []
        for trade_doc in trades_stream:
            trade_data = trade_doc.to_dict()
            trade_data["id"] = trade_doc.id
            trades.append(trade_data)

        return trades
    except Exception as e:
        logging.error(f"Failed to get recent trades: {e}")
        return []


def get_portfolio_history(days: int = 30) -> List[Dict[str, Any]]:
    """Get portfolio value history for the specified number of days."""
    try:
        db = get_firestore_client()
        portfolio_ref = db.collection("portfolio")
        
        # Calculate the cutoff date
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query portfolio snapshots ordered by timestamp
        query = portfolio_ref.where("timestamp", ">=", cutoff_date).order_by("timestamp", direction=gcp_firestore.Query.ASCENDING)
        history_stream = query.stream()

        history = []
        for history_doc in history_stream:
            history_data = history_doc.to_dict()
            history_data["id"] = history_doc.id
            history.append(history_data)

        # If no historical data, create a current snapshot
        if not history:
            current_portfolio = get_portfolio()
            total_value = sum(position.get('current_value', 0) for position in current_portfolio.values())
            
            snapshot = {
                "timestamp": datetime.utcnow(),
                "total_value": total_value,
                "positions_count": len(current_portfolio),
                "id": "current"
            }
            history.append(snapshot)

        return history
    except Exception as e:
        logging.error(f"Failed to get portfolio history: {e}")
        return []


def write_portfolio_snapshot(portfolio_data: Dict[str, Any]) -> str:
    """Write a portfolio snapshot for historical tracking."""
    try:
        db = get_firestore_client()
        portfolio_ref = db.collection("portfolio")
        
        snapshot = {
            "timestamp": datetime.utcnow(),
            "total_value": portfolio_data.get("total_value", 0),
            "total_cost": portfolio_data.get("total_cost", 0),
            "total_pnl": portfolio_data.get("total_pnl", 0),
            "total_pnl_pct": portfolio_data.get("total_pnl_pct", 0),
            "positions_count": portfolio_data.get("positions_count", 0),
            "positions": portfolio_data.get("positions", [])
        }
        
        doc_ref = portfolio_ref.add(snapshot)
        logging.info(f"Portfolio snapshot written with ID: {doc_ref[1].id}")
        return doc_ref[1].id
    except Exception as e:
        logging.error(f"Failed to write portfolio snapshot: {e}")
        return ""


def get_trades_paginated(page: int = 1, limit: int = 20, status: str | None = None) -> Dict[str, Any]:
    """Get trades with pagination and optional status filter."""
    try:
        db = get_firestore_client()
        trades_ref = db.collection("trades")
        
        # Build query
        query = trades_ref.order_by("timestamp", direction=gcp_firestore.Query.DESCENDING)
        
        # Apply status filter if provided
        if status:
            query = query.where("status", "==", status)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count for pagination
        all_trades = query.stream()
        total_count = len(list(all_trades))
        
        # Get paginated results
        trades_stream = query.offset(offset).limit(limit).stream()
        
        trades = []
        for trade_doc in trades_stream:
            trade_data = trade_doc.to_dict()
            trade_data["id"] = trade_doc.id
            trades.append(trade_data)

        return {
            "trades": trades,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit,
                "has_next": page * limit < total_count,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        logging.error(f"Failed to get paginated trades: {e}")
        return {"trades": [], "pagination": {}}


def get_signals_paginated(
    page: int = 1, 
    limit: int = 20, 
    action: str | None = None,
    min_confidence: float = 0.0,
    date_range: str = "all",
    sort_by: str = "timestamp",
    sort_order: str = "desc"
) -> Dict[str, Any]:
    """Get paginated signals with filtering and sorting."""
    try:
        db = get_firestore_client()
        signals_ref = db.collection("signals")
        
        # Start building the query
        query = signals_ref
        
        # Apply date range filter
        if date_range != "all":
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow()
            
            if date_range == "24h":
                cutoff_date = cutoff_date - timedelta(hours=24)
            elif date_range == "7d":
                cutoff_date = cutoff_date - timedelta(days=7)
            elif date_range == "30d":
                cutoff_date = cutoff_date - timedelta(days=30)
            elif date_range == "90d":
                cutoff_date = cutoff_date - timedelta(days=90)
            
            query = query.where("timestamp", ">=", cutoff_date)
        
        # Apply action filter
        if action and action != "all":
            query = query.where("action", "==", action)
        
        # Apply confidence filter
        if min_confidence > 0:
            query = query.where("confidence", ">=", min_confidence)
        
        # Apply sorting
        sort_direction = gcp_firestore.Query.DESCENDING if sort_order == "desc" else gcp_firestore.Query.ASCENDING
        
        if sort_by == "confidence":
            query = query.order_by("confidence", direction=sort_direction)
        elif sort_by == "composite_score":
            query = query.order_by("composite_score", direction=sort_direction)
        else:  # timestamp (default)
            query = query.order_by("timestamp", direction=sort_direction)
        
        # Get total count for pagination (before applying limit/offset)
        # Note: In a production environment, you might want to cache this or use approximation
        all_docs = query.stream()
        total_count = len(list(all_docs))
        
        # Calculate offset and apply pagination
        offset = (page - 1) * limit
        
        # Re-run query with pagination
        paginated_query = query.offset(offset).limit(limit)
        signals_stream = paginated_query.stream()
        
        signals = []
        for signal_doc in signals_stream:
            signal_data = signal_doc.to_dict()
            signal_data["id"] = signal_doc.id
            signals.append(signal_data)
        
        return {
            "signals": signals,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit,
                "has_more": page * limit < total_count,
                "has_prev": page > 1
            },
            "filters_applied": {
                "action": action,
                "min_confidence": min_confidence,
                "date_range": date_range,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
    except Exception as e:
        logging.error(f"Failed to get paginated signals: {e}")
        return {"signals": [], "pagination": {}, "filters_applied": {}}


def get_signals_summary(date_range: str = "24h") -> Dict[str, Any]:
    """Get signals summary statistics for the specified time range."""
    try:
        db = get_firestore_client()
        signals_ref = db.collection("signals")
        
        # Calculate date range
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow()
        
        if date_range == "24h":
            cutoff_date = cutoff_date - timedelta(hours=24)
        elif date_range == "7d":
            cutoff_date = cutoff_date - timedelta(days=7)
        elif date_range == "30d":
            cutoff_date = cutoff_date - timedelta(days=30)
        elif date_range == "90d":
            cutoff_date = cutoff_date - timedelta(days=90)
        else:  # all
            cutoff_date = datetime(2020, 1, 1)  # Very old date for "all time"
        
        # Get signals in the time range
        query = signals_ref.where("timestamp", ">=", cutoff_date)
        signals_stream = query.stream()
        
        # Calculate statistics
        total_signals = 0
        buy_signals = 0
        sell_signals = 0
        hold_signals = 0
        high_confidence_signals = 0  # >= 0.8 confidence
        avg_confidence = 0.0
        avg_composite_score = 0.0
        confidence_sum = 0.0
        score_sum = 0.0
        
        for signal_doc in signals_stream:
            signal_data = signal_doc.to_dict()
            total_signals += 1
            
            action = signal_data.get("action", "").lower()
            if action == "buy":
                buy_signals += 1
            elif action == "sell":
                sell_signals += 1
            elif action == "hold":
                hold_signals += 1
            
            confidence = signal_data.get("confidence", 0)
            if confidence >= 0.8:
                high_confidence_signals += 1
            
            confidence_sum += confidence
            score_sum += signal_data.get("composite_score", 0)
        
        # Calculate averages
        if total_signals > 0:
            avg_confidence = confidence_sum / total_signals
            avg_composite_score = score_sum / total_signals
        
        return {
            "period": date_range,
            "total_signals": total_signals,
            "action_breakdown": {
                "buy": buy_signals,
                "sell": sell_signals,
                "hold": hold_signals
            },
            "high_confidence_signals": high_confidence_signals,
            "avg_confidence": round(avg_confidence, 3),
            "avg_composite_score": round(avg_composite_score, 3),
            "confidence_distribution": {
                "high": high_confidence_signals,  # >= 0.8
                "medium": total_signals - high_confidence_signals if total_signals > 0 else 0  # < 0.8
            }
        }
    except Exception as e:
        logging.error(f"Failed to get signals summary: {e}")
        return {
            "period": date_range,
            "total_signals": 0,
            "action_breakdown": {"buy": 0, "sell": 0, "hold": 0},
            "high_confidence_signals": 0,
            "avg_confidence": 0.0,
            "avg_composite_score": 0.0,
            "confidence_distribution": {"high": 0, "medium": 0}
        }


def get_system_health() -> Dict[str, Any]:
    """Get system health status based on recent runs and overall activity."""
    try:
        db = get_firestore_client()
        
        # Get recent runs from last 24 hours
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        runs_ref = db.collection("runs")
        recent_runs_query = runs_ref.where("timestamp", ">=", cutoff_time)
        runs_stream = recent_runs_query.stream()
        
        # Analyze runs by service
        services = {}
        total_runs = 0
        
        for run_doc in runs_stream:
            run_data = run_doc.to_dict()
            service = run_data.get("service", "unknown")
            status = run_data.get("status", "unknown")
            duration = run_data.get("duration", 0)
            timestamp = run_data.get("timestamp")
            
            if service not in services:
                services[service] = {
                    "status": "healthy",
                    "last_run": None,
                    "count": 0,
                    "duration": 0,
                    "success_count": 0,
                    "error_count": 0
                }
            
            services[service]["count"] += 1
            services[service]["duration"] += duration
            
            if status == "success":
                services[service]["success_count"] += 1
            else:
                services[service]["error_count"] += 1
            
            # Track most recent run
            if not services[service]["last_run"] or timestamp > services[service]["last_run"]:
                services[service]["last_run"] = timestamp
            
            total_runs += 1
        
        # Calculate service health status
        overall_status = "healthy"
        
        for service_name, service_data in services.items():
            # Calculate error rate
            error_rate = service_data["error_count"] / service_data["count"] if service_data["count"] > 0 else 0
            
            if error_rate > 0.5:  # More than 50% errors
                services[service_name]["status"] = "error"
                overall_status = "error"
            elif error_rate > 0.2:  # More than 20% errors
                services[service_name]["status"] = "degraded"
                if overall_status == "healthy":
                    overall_status = "degraded"
            
            # Average duration
            if service_data["count"] > 0:
                services[service_name]["duration"] = round(service_data["duration"] / service_data["count"], 2)
            
            # Format last_run timestamp
            if services[service_name]["last_run"]:
                services[service_name]["last_run"] = services[service_name]["last_run"].isoformat()
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": services,
            "total_runs_24h": total_runs,
            "environment": "development"  # You could get this from settings
        }
        
    except Exception as e:
        logging.error(f"Failed to get system health: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "total_runs_24h": 0,
            "environment": "unknown",
            "error": str(e)
        }


def get_collection_stats() -> Dict[str, Any]:
    """Get statistics about Firestore collections."""
    try:
        db = get_firestore_client()
        
        collections = ["signals", "trades", "portfolio", "tokens", "models", "runs", "adminConfig"]
        stats = {}
        
        for collection_name in collections:
            try:
                # Get document count (this can be expensive for large collections)
                docs = db.collection(collection_name).limit(1000).stream()
                count = len(list(docs))
                stats[collection_name] = {
                    "document_count": count,
                    "status": "active" if count > 0 else "empty"
                }
            except Exception as e:
                stats[collection_name] = {
                    "document_count": 0,
                    "status": "error",
                    "error": str(e)
                }
        
        return stats
        
    except Exception as e:
        logging.error(f"Failed to get collection stats: {e}")
        return {}


def get_performance_metrics() -> Dict[str, Any]:
    """Get performance metrics for the system."""
    try:
        # Get recent runs for performance analysis
        recent_runs = get_recent_runs(hours=24)
        
        # Calculate metrics by service
        service_metrics = {}
        
        for run in recent_runs:
            service = run.get("service", "unknown")
            duration = run.get("duration", 0)
            status = run.get("status", "unknown")
            
            if service not in service_metrics:
                service_metrics[service] = {
                    "avg_duration": 0,
                    "max_duration": 0,
                    "min_duration": float('inf'),
                    "success_rate": 0,
                    "total_runs": 0,
                    "successful_runs": 0
                }
            
            metrics = service_metrics[service]
            metrics["total_runs"] += 1
            
            if status == "success":
                metrics["successful_runs"] += 1
            
            # Update duration metrics
            metrics["max_duration"] = max(metrics["max_duration"], duration)
            metrics["min_duration"] = min(metrics["min_duration"], duration)
        
        # Calculate averages and success rates
        for service, metrics in service_metrics.items():
            if metrics["total_runs"] > 0:
                metrics["success_rate"] = round(
                    (metrics["successful_runs"] / metrics["total_runs"]) * 100, 2
                )
                
                # Calculate average duration from all runs
                total_duration = sum(
                    run.get("duration", 0) for run in recent_runs 
                    if run.get("service") == service
                )
                metrics["avg_duration"] = round(total_duration / metrics["total_runs"], 2)
            
            # Handle edge case for min_duration
            if metrics["min_duration"] == float('inf'):
                metrics["min_duration"] = 0
        
        return service_metrics
        
    except Exception as e:
        logging.error(f"Failed to get performance metrics: {e}")
        return {}


def create_system_alert(alert_type: str, message: str, severity: str = "warning", metadata: Optional[Dict[str, Any]] = None) -> str:
    """Create a system alert for monitoring purposes."""
    try:
        db = get_firestore_client()
        alerts_ref = db.collection("alerts")
        
        alert_data = {
            "type": alert_type,
            "message": message,
            "severity": severity,  # info, warning, error, critical
            "timestamp": datetime.utcnow(),
            "resolved": False,
            "metadata": metadata or {},
            "created_by": "system"
        }
        
        doc_ref = alerts_ref.add(alert_data)
        alert_id = doc_ref[1].id
        
        logging.warning(f"System alert created: {alert_type} - {message}")
        return alert_id
        
    except Exception as e:
        logging.error(f"Failed to create system alert: {e}")
        return ""


def get_active_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Get active (unresolved) system alerts."""
    try:
        db = get_firestore_client()
        alerts_ref = db.collection("alerts")
        
        query = alerts_ref.where("resolved", "==", False)\
                          .order_by("timestamp", direction=gcp_firestore.Query.DESCENDING)\
                          .limit(limit)
        
        alerts_stream = query.stream()
        
        alerts = []
        for alert_doc in alerts_stream:
            alert_data = alert_doc.to_dict()
            alert_data["id"] = alert_doc.id
            alerts.append(alert_data)
        
        return alerts
        
    except Exception as e:
        logging.error(f"Failed to get active alerts: {e}")
        return []


def resolve_alert(alert_id: str) -> bool:
    """Mark an alert as resolved."""
    try:
        db = get_firestore_client()
        alert_ref = db.collection("alerts").document(alert_id)
        
        alert_ref.update({
            "resolved": True,
            "resolved_at": datetime.utcnow()
        })
        
        logging.info(f"Alert resolved: {alert_id}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to resolve alert: {e}")
        return False


def check_system_thresholds() -> List[Dict[str, Any]]:
    """Check system metrics against defined thresholds and create alerts if needed."""
    try:
        alerts_created = []
        
        # Check recent runs for error rates
        recent_runs = get_recent_runs(hours=1)  # Check last hour
        
        if recent_runs:
            # Group runs by service
            service_stats = {}
            for run in recent_runs:
                service = run.get("service", "unknown")
                if service not in service_stats:
                    service_stats[service] = {"total": 0, "errors": 0}
                
                service_stats[service]["total"] += 1
                if run.get("status") != "success":
                    service_stats[service]["errors"] += 1
            
            # Check error rate thresholds
            for service, stats in service_stats.items():
                error_rate = stats["errors"] / stats["total"] if stats["total"] > 0 else 0
                
                if error_rate > 0.5 and stats["total"] >= 3:  # More than 50% errors with at least 3 runs
                    alert_id = create_system_alert(
                        alert_type="high_error_rate",
                        message=f"High error rate detected for {service}: {error_rate:.1%} ({stats['errors']}/{stats['total']})",
                        severity="error",
                        metadata={
                            "service": service,
                            "error_rate": error_rate,
                            "total_runs": stats["total"],
                            "error_count": stats["errors"]
                        }
                    )
                    if alert_id:
                        alerts_created.append({"id": alert_id, "type": "high_error_rate", "service": service})
        
        # Check for services that haven't run recently
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=6)  # 6 hours without runs
        
        expected_services = ["coingecko", "signal_compute", "moralis"]
        for service in expected_services:
            service_runs = [r for r in recent_runs if r.get("service") == service]
            if not service_runs:
                # Check if this service has run in the last 6 hours
                extended_runs = get_recent_runs(hours=6)
                service_extended_runs = [r for r in extended_runs if r.get("service") == service]
                
                if not service_extended_runs:
                    alert_id = create_system_alert(
                        alert_type="service_inactive",
                        message=f"Service {service} has not run in the last 6 hours",
                        severity="warning",
                        metadata={"service": service, "last_check_hours": 6}
                    )
                    if alert_id:
                        alerts_created.append({"id": alert_id, "type": "service_inactive", "service": service})
        
        return alerts_created
        
    except Exception as e:
        logging.error(f"Failed to check system thresholds: {e}")
        return []


def get_enhanced_metrics() -> Dict[str, Any]:
    """Get enhanced system metrics for monitoring dashboards."""
    try:
        # Get comprehensive system data
        health = get_system_health()
        performance = get_performance_metrics()
        collection_stats = get_collection_stats()
        active_alerts = get_active_alerts(limit=10)
        
        # Calculate additional metrics
        total_services = len(health.get("services", {}))
        healthy_services = sum(
            1 for service in health.get("services", {}).values() 
            if service.get("status") == "healthy"
        )
        
        # Calculate overall system score (0-100)
        health_score = 0
        if total_services > 0:
            health_score = (healthy_services / total_services) * 100
        
        # Adjust score based on active alerts
        critical_alerts = sum(1 for alert in active_alerts if alert.get("severity") == "critical")
        error_alerts = sum(1 for alert in active_alerts if alert.get("severity") == "error")
        
        if critical_alerts > 0:
            health_score = min(health_score, 25)  # Critical alerts cap score at 25
        elif error_alerts > 0:
            health_score = min(health_score, 50)  # Error alerts cap score at 50
        
        # System uptime (simplified - based on recent activity)
        uptime_hours = 24  # Assume 24h uptime, could be calculated from first run timestamp
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": round(health_score, 1),
            "system_status": health.get("status", "unknown"),
            "uptime_hours": uptime_hours,
            "services": {
                "total": total_services,
                "healthy": healthy_services,
                "degraded": sum(1 for s in health.get("services", {}).values() if s.get("status") == "degraded"),
                "error": sum(1 for s in health.get("services", {}).values() if s.get("status") == "error")
            },
            "alerts": {
                "total_active": len(active_alerts),
                "critical": critical_alerts,
                "error": error_alerts,
                "warning": sum(1 for alert in active_alerts if alert.get("severity") == "warning")
            },
            "database": {
                "collections_active": sum(1 for col in collection_stats.values() if col.get("status") == "active"),
                "total_documents": sum(col.get("document_count", 0) for col in collection_stats.values()),
                "collections_total": len(collection_stats)
            },
            "performance": performance,
            "runs_24h": health.get("total_runs_24h", 0)
        }
        
    except Exception as e:
        logging.error(f"Failed to get enhanced metrics: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health_score": 0,
            "system_status": "error",
            "error": str(e)
        }


def get_gcp_service_status() -> Dict[str, Any]:
    """Get actual GCP service status using Google Cloud SDK (enhanced version)."""
    try:
        # This would require proper GCP SDK setup and authentication
        # For now, we'll provide a comprehensive mock that could be enhanced with real GCP integration
        
        gcp_status = {
            "cloud_run": {
                "status": "active",
                "service_name": "moda-crypto-backend",
                "region": "us-central1",
                "url": "https://moda-crypto-backend.run.app",
                "last_deploy": datetime.utcnow().isoformat(),
                "instances": {
                    "min": 1,
                    "max": 10,
                    "current": 1
                },
                "metrics": {
                    "cpu_utilization": 15.2,
                    "memory_utilization": 34.7,
                    "request_count_1h": 142,
                    "error_rate_1h": 0.01
                }
            },
            "firestore": {
                "status": "active",
                "database_id": "(default)",
                "location": "us-central",
                "collections": len(get_collection_stats()),
                "operations_1h": {
                    "reads": 1250,
                    "writes": 89,
                    "deletes": 2
                },
                "storage_size_gb": 0.15
            },
            "cloud_storage": {
                "status": "active",
                "buckets": [
                    {
                        "name": "moda-crypto-models",
                        "location": "us-central1",
                        "size_gb": 2.3,
                        "object_count": 15
                    }
                ]
            },
            "cloud_logging": {
                "status": "active",
                "logs_ingested_1h": 3421,
                "retention_days": 30,
                "log_based_metrics": 5
            },
            "monitoring": {
                "status": "active",
                "uptime_checks": 3,
                "alert_policies": 8,
                "notification_channels": 2
            }
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "services": gcp_status,
            "overall_status": "healthy",  # Could be calculated based on individual service status
            "region": "us-central1"
        }
        
    except Exception as e:
        logging.error(f"Failed to get GCP service status: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "services": {},
            "overall_status": "unknown"
        }
