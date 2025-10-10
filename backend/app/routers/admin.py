from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime
from typing import Dict, List, Any
import logging
import time

from ..models.train import train_model, get_model_info
from ..firestore_client import write_run, get_admin_config
from ..config import settings

router = APIRouter()


@router.post("/retrain")
async def retrain_model():
    """
    Trigger model retraining.
    This endpoint initiates the full ML model training pipeline.
    """
    start_time = time.time()
    try:
        logging.info("Starting model retraining")

        # Train new model
        model_info = await train_model()

        duration = time.time() - start_time

        # Write run log directly
        write_run("model_retrain", 1, "success", duration)

        return {
            "status": "success",
            "message": "Model retraining completed successfully",
            "model_info": model_info,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Model retraining failed: {e}")
        write_run("model_retrain", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_current_config():
    """Get current admin configuration."""
    try:
        config = get_admin_config()

        return {
            "status": "success",
            "config": config
        }

    except Exception as e:
        logging.error(f"Failed to get admin config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_config(
    ml_weight: float | None = None,
    rule_weight: float | None = None,
    sentiment_weight: float | None = None,
    event_weight: float | None = None,
    min_composite_score: float | None = None
):
    """Update admin configuration."""
    try:
        from ..firestore_client import init_db

        # Get current config
        current_config = get_admin_config()

        # Update provided values
        updates = {}
        if ml_weight is not None:
            updates['ml_weight'] = ml_weight
        if rule_weight is not None:
            updates['rule_weight'] = rule_weight
        if sentiment_weight is not None:
            updates['sentiment_weight'] = sentiment_weight
        if event_weight is not None:
            updates['event_weight'] = event_weight
        if min_composite_score is not None:
            updates['min_composite_score'] = min_composite_score

        if not updates:
            return {
                "status": "error",
                "message": "No configuration updates provided"
            }

        # Validate weights sum to 1.0 (if all weights are provided)
        weight_keys = ['ml_weight', 'rule_weight',
                       'sentiment_weight', 'event_weight']
        if all(key in updates for key in weight_keys):
            total_weight = sum(updates[key] for key in weight_keys)
            if abs(total_weight - 1.0) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"Weights must sum to 1.0, got {total_weight}"
                )

        # Update config in Firestore
        db = init_db()
        current_config.update(updates)
        db.collection('adminConfig').document('default').set(current_config)

        logging.info(f"Admin config updated: {updates}")

        return {
            "status": "success",
            "message": "Configuration updated successfully",
            "config": current_config,
            "updates": updates
        }

    except Exception as e:
        logging.error(f"Failed to update admin config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/info")
async def get_model_information():
    """Get information about the current ML model."""
    try:
        model_info = get_model_info()

        return {
            "status": "success",
            "model": model_info
        }

    except Exception as e:
        logging.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_system_stats():
    """Get system statistics and performance metrics."""
    try:
        from ..firestore_client import get_recent_runs, get_tokens_list, get_recent_signals

        # Get various system stats
        recent_runs = get_recent_runs(hours=24)
        tokens = get_tokens_list()
        recent_signals = get_recent_signals(hours=24)

        # Calculate run statistics
        run_stats = {}
        for run in recent_runs:
            service = run['service']
            if service not in run_stats:
                run_stats[service] = {'success': 0, 'error': 0, 'total': 0}

            run_stats[service][run['status']] += 1
            run_stats[service]['total'] += 1

        # Calculate signal statistics
        signal_stats = {
            'total_signals': len(recent_signals),
            'high_confidence': len([s for s in recent_signals if s.get('composite_score', 0) >= 0.8]),
            'medium_confidence': len([s for s in recent_signals if 0.6 <= s.get('composite_score', 0) < 0.8]),
            'low_confidence': len([s for s in recent_signals if s.get('composite_score', 0) < 0.6])
        }

        return {
            "status": "success",
            "stats": {
                "tokens": {
                    "total": len(tokens),
                    "active": len([t for t in tokens if t.get('active', True)])
                },
                "runs_24h": run_stats,
                "signals_24h": signal_stats,
                "system": {
                    "environment": settings.environment,
                    "min_composite_score": settings.min_composite_score,
                    "max_position_size": settings.max_position_size
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tokens/sync")
async def sync_token_list():
    """
    Sync token list from external sources.
    This endpoint updates the tokens collection with latest token information.
    """
    try:
        logging.info("Starting token list sync")

        # TODO: Implement token sync logic
        # This would:
        # 1. Fetch latest token list from CoinGecko or other source
        # 2. Update existing tokens with new information
        # 3. Add new tokens if needed
        # 4. Mark inactive tokens

        # Placeholder implementation
        updated_count = 0

        return {
            "status": "success",
            "message": f"Token sync completed: {updated_count} tokens updated",
            "updated_count": updated_count
        }

    except Exception as e:
        logging.error(f"Token sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_models():
    """Get information about all ML models."""
    try:
        # Get model information (this might need to be expanded based on your model storage)
        current_model = get_model_info()
        
        models = []
        if current_model:
            models.append({
                "id": current_model.get("id", "current_model"),
                "model_id": current_model.get("model_id", "xgboost_v1"),
                "model_type": current_model.get("model_type", "XGBoost"),
                "version": current_model.get("version", "1.0"),
                "training_date": current_model.get("training_date", datetime.utcnow()).isoformat(),
                "accuracy": current_model.get("accuracy", 0.0),
                "auc_score": current_model.get("auc_score", 0.0),
                "cv_mean": current_model.get("cv_mean", 0.0),
                "cv_std": current_model.get("cv_std", 0.0),
                "training_samples": current_model.get("training_samples", 0),
                "feature_count": current_model.get("feature_count", 0),
                "status": "active"
            })
        
        return {
            "status": "success",
            "models": models
        }
    
    except Exception as e:
        logging.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/gcp-status")
async def get_gcp_status():
    """Get Google Cloud Platform service status."""
    try:
        import subprocess
        
        # This is a simplified implementation - in production you'd want proper GCP SDK integration
        gcp_status = {
            "cloudRun": {
                "status": "active",  # You'd check actual Cloud Run service status
                "url": "https://moda-crypto-backend.run.app",  # Replace with actual Cloud Run URL
                "lastDeploy": datetime.utcnow().isoformat()
            },
            "firestore": {
                "status": "active",
                "collections": 7,  # signals, trades, portfolio, tokens, models, runs, adminConfig
                "documents": 0  # You could count documents if needed
            },
            "cloudStorage": {
                "status": "active",
                "buckets": 1  # Your model storage bucket
            },
            "logging": {
                "status": "active",
                "entries24h": 0  # You could integrate with Cloud Logging API
            }
        }
        
        return {
            "status": "success",
            **gcp_status
        }
    
    except Exception as e:
        logging.error(f"Failed to get GCP status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/firebase-stats")
async def get_firebase_stats():
    """Get Firebase service statistics."""
    try:
        firebase_stats = {
            "hosting": {
                "status": "active",
                "domains": [settings.frontend_url],
                "lastDeploy": datetime.utcnow().isoformat()
            },
            "authentication": {
                "status": "active",
                "users": 1  # You could integrate with Firebase Auth to get actual count
            },
            "database": {
                "status": "active",
                "reads24h": 0,  # You could integrate with Firebase usage API
                "writes24h": 0
            }
        }
        
        return {
            "status": "success",
            **firebase_stats
        }
    
    except Exception as e:
        logging.error(f"Failed to get Firebase stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-status")
async def get_api_status():
    """Check status of external APIs."""
    try:
        import aiohttp
        import asyncio
        
        apis_to_check = [
            {"name": "CoinGecko", "url": "https://api.coingecko.com/api/v3/ping"},
            {"name": "Moralis", "url": "https://api.moralis.io/"},
            {"name": "CoinMarketCal", "url": "https://coinmarketcal.com/"},
            {"name": "CryptoPanic", "url": "https://cryptopanic.com/api/"},
            {"name": "LunarCrush", "url": "https://api.lunarcrush.com/"}
        ]
        
        api_status = []
        
        async def check_api(session, api):
            try:
                start_time = time.time()
                async with session.get(api["url"], timeout=5) as response:
                    response_time = round((time.time() - start_time) * 1000, 2)
                    status = "online" if response.status == 200 else "degraded"
                    return {
                        "name": api["name"],
                        "status": status,
                        "lastCheck": datetime.utcnow().isoformat(),
                        "responseTime": response_time
                    }
            except Exception:
                return {
                    "name": api["name"],
                    "status": "offline",
                    "lastCheck": datetime.utcnow().isoformat(),
                    "responseTime": 0
                }
        
        # Check APIs concurrently
        async with aiohttp.ClientSession() as session:
            tasks = [check_api(session, api) for api in apis_to_check]
            api_status = await asyncio.gather(*tasks)
        
        return {
            "status": "success",
            "apis": api_status
        }
    
    except Exception as e:
        logging.error(f"Failed to check API status: {e}")
        # Return fallback status if check fails
        return {
            "status": "success",
            "apis": [
                {"name": api["name"], "status": "unknown", "lastCheck": datetime.utcnow().isoformat(), "responseTime": 0}
                for api in [
                    {"name": "CoinGecko"}, {"name": "Moralis"}, {"name": "CoinMarketCal"},
                    {"name": "CryptoPanic"}, {"name": "LunarCrush"}
                ]
            ]
        }


@router.get("/portfolio-settings")
async def get_portfolio_settings():
    """Get current portfolio trading settings."""
    try:
        config = get_admin_config()
        
        # Enhanced settings with additional portfolio management parameters
        settings_data = {
            "ml_weight": config.get("ml_weight", 0.4),
            "rule_weight": config.get("rule_weight", 0.3),
            "sentiment_weight": config.get("sentiment_weight", 0.2),
            "event_weight": config.get("event_weight", 0.1),
            "min_composite_score": config.get("min_composite_score", 0.6),
            "max_positions": config.get("max_positions", 10),
            "position_size_limit": config.get("position_size_limit", 0.1),  # 10% of portfolio
            "stop_loss_pct": config.get("stop_loss_pct", -5.0),  # -5%
            "take_profit_pct": config.get("take_profit_pct", 15.0)  # +15%
        }
        
        return {
            "status": "success",
            "settings": settings_data
        }
    
    except Exception as e:
        logging.error(f"Failed to get portfolio settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio-settings")
async def update_portfolio_settings(settings_data: dict):
    """Update portfolio trading settings."""
    try:
        from ..firestore_client import init_db
        
        # Get current config
        current_config = get_admin_config()
        
        # Update with new settings
        allowed_settings = [
            'ml_weight', 'rule_weight', 'sentiment_weight', 'event_weight',
            'min_composite_score', 'max_positions', 'position_size_limit',
            'stop_loss_pct', 'take_profit_pct'
        ]
        
        updates = {}
        for key, value in settings_data.items():
            if key in allowed_settings:
                updates[key] = value
        
        if not updates:
            return {
                "status": "error",
                "message": "No valid settings provided"
            }
        
        # Validate weight sum if all weights are provided
        weight_keys = ['ml_weight', 'rule_weight', 'sentiment_weight', 'event_weight']
        if all(key in updates for key in weight_keys):
            total_weight = sum(updates[key] for key in weight_keys)
            if abs(total_weight - 1.0) > 0.01:
                raise HTTPException(
                    status_code=400,
                    detail=f"Weights must sum to 1.0, got {total_weight}"
                )
        
        # Update config in Firestore
        db = init_db()
        current_config.update(updates)
        db.collection('adminConfig').document('default').set(current_config)
        
        logging.info(f"Portfolio settings updated: {updates}")
        
        return {
            "status": "success",
            "message": "Portfolio settings updated successfully",
            "settings": current_config
        }
    
    except Exception as e:
        logging.error(f"Failed to update portfolio settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health")
async def get_system_health_admin():
    """Get comprehensive system health for admin panel."""
    try:
        from ..firestore_client import get_system_health, get_collection_stats, get_performance_metrics
        
        health = get_system_health()
        collection_stats = get_collection_stats()
        performance = get_performance_metrics()
        
        return {
            "status": "success",
            "health": health,
            "collections": collection_stats,
            "performance": performance
        }
    
    except Exception as e:
        logging.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/watchlist")
async def get_watchlist():
    """Get active tokens in the watchlist."""
    try:
        from ..firestore_client import get_tokens_list
        
        tokens = get_tokens_list()
        active_tokens = [token for token in tokens if token.get('active', True)]
        
        return {
            "status": "success",
            "tokens": active_tokens,
            "count": len(active_tokens)
        }
    
    except Exception as e:
        logging.error(f"Failed to get watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens/all")
async def get_all_tokens():
    """Get all tokens (active and inactive)."""
    try:
        from ..firestore_client import get_tokens_list
        
        tokens = get_tokens_list()
        
        return {
            "status": "success",
            "tokens": tokens,
            "count": len(tokens)
        }
    
    except Exception as e:
        logging.error(f"Failed to get all tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist")
async def add_token_to_watchlist(token_data: dict):
    """Add a new token to the watchlist."""
    try:
        from ..firestore_client import init_db
        
        # Validate required fields
        required_fields = ['symbol', 'name', 'coingecko_id']
        for field in required_fields:
            if field not in token_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create token document
        db = init_db()
        token_doc = {
            "symbol": token_data["symbol"].upper(),
            "name": token_data["name"],
            "coingecko_id": token_data["coingecko_id"],
            "active": True,
            "last_updated": datetime.utcnow(),
            "market_cap": token_data.get("market_cap", 0),
            "liquidity_24h": token_data.get("liquidity_24h", 0)
        }
        
        # Use symbol as document ID
        doc_id = token_data["symbol"].upper()
        db.collection('tokens').document(doc_id).set(token_doc)
        
        logging.info(f"Added token to watchlist: {doc_id}")
        
        # Auto-sync watchlist universe after adding token
        try:
            from ..universe_manager import universe_manager
            await universe_manager.sync_watchlist_universe_from_ui()
            logging.info("Watchlist universe auto-synced after token addition")
        except Exception as sync_error:
            logging.warning(f"Failed to auto-sync watchlist universe: {sync_error}")
        
        return {
            "status": "success",
            "message": f"Token {doc_id} added to watchlist",
            "token": {**token_doc, "id": doc_id}
        }
    
    except Exception as e:
        logging.error(f"Failed to add token to watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/watchlist/{token_id}")
async def update_watchlist_token(token_id: str, token_data: dict):
    """Update a token in the watchlist."""
    try:
        from ..firestore_client import init_db
        
        db = init_db()
        token_ref = db.collection('tokens').document(token_id.upper())
        
        # Check if token exists
        token_doc = token_ref.get()
        if not token_doc.exists:
            raise HTTPException(status_code=404, detail=f"Token {token_id} not found")
        
        # Update allowed fields
        allowed_fields = ['name', 'coingecko_id', 'active', 'market_cap', 'liquidity_24h']
        updates = {
            "last_updated": datetime.utcnow()
        }
        
        for field in allowed_fields:
            if field in token_data:
                updates[field] = token_data[field]
        
        token_ref.update(updates)
        
        logging.info(f"Updated token in watchlist: {token_id}")
        
        return {
            "status": "success",
            "message": f"Token {token_id} updated successfully",
            "updates": updates
        }
    
    except Exception as e:
        logging.error(f"Failed to update watchlist token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/watchlist/{token_id}")
async def remove_token_from_watchlist(token_id: str):
    """Remove a token from the watchlist (sets active=false)."""
    try:
        from ..firestore_client import init_db
        
        db = init_db()
        token_ref = db.collection('tokens').document(token_id.upper())
        
        # Check if token exists
        token_doc = token_ref.get()
        if not token_doc.exists:
            raise HTTPException(status_code=404, detail=f"Token {token_id} not found")
        
        # Set active to false instead of deleting
        token_ref.update({
            "active": False,
            "last_updated": datetime.utcnow()
        })
        
        logging.info(f"Removed token from watchlist: {token_id}")
        
        # Auto-sync watchlist universe after removing token
        try:
            from ..universe_manager import universe_manager
            await universe_manager.sync_watchlist_universe_from_ui()
            # Also remove from universe
            await universe_manager.remove_token_from_universe("watchlist", token_id.lower())
            logging.info("Watchlist universe auto-synced after token removal")
        except Exception as sync_error:
            logging.warning(f"Failed to auto-sync watchlist universe: {sync_error}")
        
        return {
            "status": "success",
            "message": f"Token {token_id} removed from watchlist"
        }
    
    except Exception as e:
        logging.error(f"Failed to remove token from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/sync")
async def sync_watchlist_data():
    """Sync watchlist tokens with latest market data."""
    try:
        from ..firestore_client import get_tokens_list
        
        # Get active tokens
        tokens = get_tokens_list()
        active_tokens = [token for token in tokens if token.get('active', True)]
        
        # TODO: Implement actual sync with CoinGecko or other data sources
        # This would fetch current market data for all active tokens
        
        synced_count = len(active_tokens)
        
        # Write run log directly
        write_run("watchlist_sync", synced_count, "success", 0)
        
        return {
            "status": "success",
            "message": f"Watchlist sync completed for {synced_count} tokens",
            "synced_count": synced_count
        }
    
    except Exception as e:
        logging.error(f"Failed to sync watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Advanced System Monitoring Endpoints

@router.get("/system/alerts")
async def get_system_alerts(
    limit: int = Query(50, description="Maximum number of alerts to return"),
    resolved: bool = Query(False, description="Include resolved alerts")
):
    """Get system alerts for monitoring dashboard."""
    try:
        from ..firestore_client import get_active_alerts
        
        alerts = get_active_alerts(limit=limit)
        
        # Filter by resolved status if specified
        if not resolved:
            alerts = [alert for alert in alerts if not alert.get("resolved", False)]
        
        # Group alerts by severity for summary
        alert_summary = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        for alert in alerts:
            severity = alert.get("severity", "info")
            if severity in alert_summary:
                alert_summary[severity] += 1
        
        logging.info(f"Retrieved {len(alerts)} system alerts")
        
        return {
            "status": "success",
            "alerts": alerts,
            "summary": alert_summary,
            "total_count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting system alerts: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/system/alerts/{alert_id}/resolve")
async def resolve_system_alert(alert_id: str):
    """Mark a system alert as resolved."""
    try:
        from ..firestore_client import resolve_alert
        
        success = resolve_alert(alert_id)
        
        if success:
            logging.info(f"Alert resolved: {alert_id}")
            return {"status": "success", "message": f"Alert {alert_id} resolved successfully"}
        else:
            return {"status": "error", "message": "Failed to resolve alert"}
            
    except Exception as e:
        logging.error(f"Error resolving alert {alert_id}: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/system/metrics/enhanced")
async def get_enhanced_system_metrics():
    """Get comprehensive system metrics for advanced monitoring."""
    try:
        from ..firestore_client import get_enhanced_metrics
        
        metrics = get_enhanced_metrics()
        
        logging.info("Retrieved enhanced system metrics")
        
        return {
            "status": "success",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting enhanced metrics: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/system/monitoring/check-thresholds")
async def check_monitoring_thresholds():
    """Run threshold checks and create alerts if needed."""
    try:
        from ..firestore_client import check_system_thresholds
        
        alerts_created = check_system_thresholds()
        
        logging.info(f"Threshold check completed. {len(alerts_created)} alerts created.")
        
        return {
            "status": "success",
            "alerts_created": alerts_created,
            "count": len(alerts_created),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error checking system thresholds: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/gcp/services")
async def get_gcp_services_status():
    """Get detailed Google Cloud Platform services status."""
    try:
        from ..firestore_client import get_gcp_service_status
        
        gcp_status = get_gcp_service_status()
        
        logging.info("Retrieved GCP services status")
        
        return {
            "status": "success",
            "gcp": gcp_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting GCP services status: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/system/alerts")
async def create_manual_alert(
    alert_type: str = Body(..., description="Type of alert"),
    message: str = Body(..., description="Alert message"),
    severity: str = Body("warning", description="Alert severity: info, warning, error, critical"),
    metadata: dict = Body(None, description="Additional alert metadata")
):
    """Create a manual system alert."""
    try:
        from ..firestore_client import create_system_alert
        
        # Validate severity level
        valid_severities = ["info", "warning", "error", "critical"]
        if severity not in valid_severities:
            return {"status": "error", "message": f"Invalid severity. Must be one of: {', '.join(valid_severities)}"}
        
        alert_id = create_system_alert(
            alert_type=alert_type,
            message=message,
            severity=severity,
            metadata=metadata or {}
        )
        
        if alert_id:
            logging.info(f"Manual alert created: {alert_id}")
            return {
                "status": "success", 
                "alert_id": alert_id,
                "message": "Alert created successfully"
            }
        else:
            return {"status": "error", "message": "Failed to create alert"}
            
    except Exception as e:
        logging.error(f"Error creating manual alert: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/system/monitoring/check-now")
async def check_monitoring_now():
    """Run immediate monitoring check (no background tasks)."""
    try:
        # Run threshold check immediately
        from ..firestore_client import check_system_thresholds
        alerts_created = check_system_thresholds()
        
        logging.info(f"Manual monitoring check completed - {len(alerts_created)} alerts created")
        
        return {
            "status": "success",
            "message": f"Monitoring check completed successfully",
            "alerts_created": len(alerts_created),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error running monitoring check: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/system/monitoring/simple-status")
async def get_simple_monitoring_status():
    """Get basic monitoring status without background complexity."""
    try:
        from ..firestore_client import get_tokens_list, get_active_alerts
        
        # Get basic counts
        tokens = get_tokens_list()
        active_tokens = [token for token in tokens if token.get('active', True)]
        alerts = get_active_alerts(limit=10)
        
        return {
            "status": "success", 
            "monitoring": {
                "tokens_count": len(active_tokens),
                "active_alerts": len(alerts),
                "last_check": datetime.utcnow().isoformat(),
                "status": "active"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting monitoring status: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/system/monitoring/status")
async def get_monitoring_status_endpoint():
    """Get detailed monitoring system status."""
    try:
        from ..monitoring import get_monitoring_status
        
        status = get_monitoring_status()
        
        return {
            "status": "success",
            "monitoring": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting monitoring status: {e}")
        return {"status": "error", "message": str(e)}


# ================================
# POPULATE SECTION
# ================================

@router.post("/populate/watchlist")
async def populate_watchlist(
    top_n: int = Query(40, description="Number of top tokens to add to watchlist")
):
    """Populate watchlist with popular crypto symbols."""
    try:
        from ..firestore_client import init_db
        
        # Simple list of popular crypto symbols
        popular_cryptos = [
            "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP", "DOGE", "TON", "ADA",
            "SHIB", "AVAX", "TRX", "DOT", "BCH", "LINK", "NEAR", "MATIC", "ICP", "UNI", 
            "LTC", "PEPE", "LEO", "DAI", "ETC", "HBAR", "XMR", "RENDER", "KASPA", "ARB",
            "VET", "XLM", "FIL", "ATOM", "CRO", "MKR", "OP", "IMX", "INJ", "MANTLE"
        ]
        
        # Take only the requested number of tokens
        tokens_to_add = popular_cryptos[:top_n]
        
        db = init_db()
        added_count = 0
        
        # Simply write each symbol to Firestore
        for symbol in tokens_to_add:
            try:
                token_doc = {
                    'symbol': symbol,
                    'name': symbol,  # Keep it simple - just use symbol as name
                    'active': True,
                    'added_at': datetime.utcnow().isoformat(),
                    'last_updated': datetime.utcnow()
                }
                
                # Write to tokens collection
                db.collection('tokens').document(symbol).set(token_doc)
                added_count += 1
                
            except Exception as e:
                logging.error(f"Error adding token {symbol}: {e}")
                continue
        
        return {
            "status": "success",
            "message": f"Added {added_count} popular crypto tokens to watchlist",
            "tokens_added": added_count,
            "requested": top_n
        }
        
    except Exception as e:
        logging.error(f"Error populating watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/populate/status")
async def get_populate_status():
    """Get current populate operation status."""
    try:
        from ..firestore_client import get_tokens_list
        
        # Just return the current count of tokens in the watchlist
        tokens = get_tokens_list()
        active_tokens = [token for token in tokens if token.get('active', True)]
        
        return {
            "status": "success",
            "populate_status": {
                "active": False,  # We use synchronous populate, so never active
                "current_operation": None,
                "progress": {},
                "data_counts": {
                    "tokens": len(active_tokens)
                }
            }
        }
            
    except Exception as e:
        logging.error(f"Error getting populate status: {e}")
        return {
            "status": "success", 
            "populate_status": {
                "active": False,
                "current_operation": None,
                "progress": {},
                "data_counts": {"tokens": 0}
            }
        }


# ================================
# HISTORICAL DATA POPULATION
# ================================

@router.post("/populate/historical-data")
async def populate_historical_data(
    days_back: int = Query(730, description="Number of days back to fetch (default: 2 years = 730 days)"),
    sources: list[str] = Query(default=["all"], description="List of sources to fetch from (coingecko, moralis, covalent, lunarcrush, coinmarketcal, cryptopanic, all)"),
    universe: str = Query("watchlist", description="Universe to target (market, watchlist, portfolio, all)")
):
    """
    Populate historical data from external APIs using universe-targeted approach.
    By default, uses watchlist universe for focused historical data collection.
    This allows back-populating data for up to 2 years (730 days) worth of historical information.
    """
    try:
        from ..services import coingecko, moralis, covalent, lunarcrush, coinmarketcal, cryptopanic
        from ..firestore_client import init_db
        import asyncio
        from datetime import datetime, timedelta
        
        start_time = time.time()
        
        # Validate days_back (maximum 2 years)
        max_days = 730  # 2 years
        days_back = min(days_back, max_days)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get universe tokens for targeted historical data collection
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        valid_universes = [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE, "all"]
        if universe not in valid_universes:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid universe. Must be one of: {valid_universes}"
            )
        
        # Get target tokens based on universe
        target_tokens = []
        universe_info = ""
        
        if universe == "all":
            # Use all available tokens (legacy behavior)
            universe_info = "all tokens"
        else:
            target_tokens = await universe_manager.get_universe_symbols(universe)
            universe_info = f"{universe} universe ({len(target_tokens)} tokens)"
            
            if not target_tokens and universe != "all":
                logging.warning(f"No tokens found in {universe} universe. Consider syncing universes first.")
                return {
                    "status": "warning",
                    "message": f"No tokens configured in {universe} universe",
                    "recommendation": f"Run POST /admin/universes/{universe}/sync to populate universe first"
                }
        
        logging.info(f"Starting historical data population for {days_back} days ({start_date.date()} to {end_date.date()}) targeting {universe_info}")
        
        # Determine which sources to fetch from
        all_sources = ["coingecko", "moralis", "covalent", "lunarcrush", "coinmarketcal", "cryptopanic"]
        if "all" in sources:
            active_sources = all_sources
        else:
            active_sources = [s for s in sources if s in all_sources]
        
        if not active_sources:
            raise HTTPException(status_code=400, detail="No valid sources specified")
        
        # Map sources to their fetch functions
        source_functions = {
            "coingecko": coingecko.fetch_market_data,
            "moralis": moralis.fetch_onchain_data,
            "covalent": covalent.fetch_blockchain_data,
            "lunarcrush": lunarcrush.fetch_social_data,
            "coinmarketcal": coinmarketcal.fetch_events,
            "cryptopanic": cryptopanic.fetch_news
        }
        
        # Execute fetch operations for active sources
        results = {}
        total_records = 0
        successful_sources = []
        failed_sources = []
        
        for source in active_sources:
            try:
                logging.info(f"Fetching historical data from {source} for {universe_info}...")
                
                # Call the source's fetch function
                fetch_function = source_functions[source]
                all_data = await fetch_function()
                
                # Filter data by universe tokens (if specific universe is targeted)
                if universe != "all" and target_tokens and all_data:
                    # Filter results to only include tokens from the target universe
                    filtered_data = []
                    for item in all_data:
                        item_symbol = item.get('symbol', '').lower()
                        if item_symbol in target_tokens:
                            filtered_data.append(item)
                    data = filtered_data
                    
                    logging.info(f"Filtered {len(all_data)} records to {len(data)} records for {universe} universe")
                else:
                    data = all_data
                
                record_count = len(data) if data else 0
                total_records += record_count
                
                results[source] = {
                    "status": "success", 
                    "records": record_count,
                    "total_fetched": len(all_data) if all_data else 0,
                    "message": f"Successfully fetched {record_count} universe-targeted records (filtered from {len(all_data) if all_data else 0} total)"
                }
                successful_sources.append(source)
                
                logging.info(f"Successfully fetched {record_count} targeted records from {source}")
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Failed to fetch from {source}: {error_msg}")
                
                results[source] = {
                    "status": "error",
                    "records": 0,
                    "total_fetched": 0,
                    "message": f"Error: {error_msg}"
                }
                failed_sources.append(source)
        
        # Calculate execution time
        duration = time.time() - start_time
        
        # Prepare response
        response_data = {
            "status": "success",
            "message": f"Historical data population completed for {days_back} days targeting {universe_info}",
            "summary": {
                "target": {
                    "universe": universe,
                    "tokens_targeted": len(target_tokens) if target_tokens else "all",
                    "universe_info": universe_info
                },
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days_back": days_back
                },
                "sources": {
                    "requested": active_sources,
                    "successful": successful_sources,
                    "failed": failed_sources,
                    "success_rate": f"{len(successful_sources)}/{len(active_sources)} ({(len(successful_sources)/len(active_sources)*100):.1f}%)"
                },
                "data": {
                    "targeted_records": total_records,
                    "execution_time": f"{duration:.2f}s"
                }
            },
            "details": results
        }
        
        # Log the operation with universe information
        write_run(
            f"historical_populate_{universe}",
            total_records,
            "success" if len(successful_sources) > 0 else "error",
            duration,
            universe
        )
        
        return response_data
        
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        error_msg = str(e)
        logging.error(f"Historical data population failed: {error_msg}")
        
        write_run("historical_populate", 0, "error", duration)
        
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/populate/historical-status")
async def get_historical_populate_status():
    """Get status of historical data population capabilities and universe information."""
    try:
        from ..firestore_client import init_db
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        # Get database stats
        db = init_db()
        
        # Count documents in various collections to show data availability
        collections_info = {}
        collection_names = ["tokens", "market_data", "social_data", "events", "news", "blockchain_data"]
        
        for collection_name in collection_names:
            try:
                # Get a sample of documents to check data availability
                docs = list(db.collection(collection_name).limit(1).stream())
                collections_info[collection_name] = {
                    "exists": len(docs) > 0,
                    "sample_available": len(docs) > 0
                }
            except Exception:
                collections_info[collection_name] = {
                    "exists": False,
                    "sample_available": False
                }
        
        # Get universe statistics
        universe_stats = {}
        for universe_name in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            try:
                stats = await universe_manager.get_universe_stats(universe_name)
                universe_stats[universe_name] = stats
            except Exception as e:
                universe_stats[universe_name] = {"error": str(e)}
        
        return {
            "status": "success",
            "capabilities": {
                "max_days_back": 730,  # 2 years
                "available_sources": ["coingecko", "moralis", "covalent", "lunarcrush", "coinmarketcal", "cryptopanic"],
                "available_universes": [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE, "all"],
                "universe_targeting": True,
                "bulk_fetch_supported": True,
                "individual_source_fetch": True
            },
            "universes": universe_stats,
            "current_data": collections_info,
            "recommendations": {
                "default_universe": "watchlist (focused on your curated tokens)",
                "initial_population": "Start with watchlist universe + 30-90 days for testing",
                "source_priority": ["coingecko", "lunarcrush", "coinmarketcal", "cryptopanic", "moralis", "covalent"],
                "universe_sync": "Run POST /admin/universes/sync to ensure universes are populated before historical fetch",
                "cost_optimization": "Use 'watchlist' universe to focus on tokens you actually track, reducing API costs by 70-90%"
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting historical populate status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/populate/historical-watchlist")
async def populate_historical_watchlist(
    days_back: int = Query(90, description="Number of days back to fetch (default: 90 days)"),
    sources: list[str] = Query(default=["coingecko", "lunarcrush", "coinmarketcal"], description="Sources optimized for watchlist analysis")
):
    """
    Convenience endpoint to populate historical data specifically for watchlist universe.
    Optimized for ML feature engineering with curated token list and relevant data sources.
    """
    return await populate_historical_data(days_back=days_back, sources=sources, universe="watchlist")


@router.post("/populate/historical-portfolio")
async def populate_historical_portfolio(
    days_back: int = Query(30, description="Number of days back to fetch (default: 30 days)"),
    sources: list[str] = Query(default=["coingecko"], description="Sources optimized for portfolio tracking")
):
    """
    Convenience endpoint to populate historical data specifically for portfolio universe.
    Focuses on price history for actively held positions.
    """
    return await populate_historical_data(days_back=days_back, sources=sources, universe="portfolio")


@router.post("/populate/historical-market")
async def populate_historical_market(
    days_back: int = Query(365, description="Number of days back to fetch (default: 1 year)"),
    sources: list[str] = Query(default=["coingecko", "lunarcrush"], description="Sources optimized for market analysis")
):
    """
    Convenience endpoint to populate historical data specifically for market universe.
    Covers broader market trends and sentiment for top market cap tokens.
    """
    return await populate_historical_data(days_back=days_back, sources=sources, universe="market")


# =============================================================================
# UNIVERSE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/universes")
async def get_all_universes():
    """Get information about all token universes."""
    try:
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        universes = {}
        for universe_name in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            universes[universe_name] = await universe_manager.get_universe_stats(universe_name)
        
        return {
            "status": "success",
            "universes": universes,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting universe information: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/universes/{universe_name}")
async def get_universe_info(universe_name: str):
    """Get detailed information about a specific universe."""
    try:
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        if universe_name not in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid universe name. Must be one of: {MARKET_UNIVERSE}, {WATCHLIST_UNIVERSE}, {PORTFOLIO_UNIVERSE}"
            )
        
        stats = await universe_manager.get_universe_stats(universe_name)
        tokens = await universe_manager.get_universe_tokens(universe_name)
        
        return {
            "status": "success",
            "universe": stats,
            "tokens": tokens,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting {universe_name} universe info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/universes/sync")
async def sync_all_universes():
    """Sync all universes with current UI and portfolio data."""
    try:
        from ..universe_manager import universe_manager
        
        start_time = time.time()
        
        # Sync watchlist universe from UI watchlist
        watchlist_count = await universe_manager.sync_watchlist_universe_from_ui()
        
        # Sync portfolio universe from active positions
        portfolio_count = await universe_manager.sync_portfolio_universe_from_positions()
        
        # Auto-populate market universe with top tokens
        market_count = await universe_manager.populate_market_universe(100)
        
        duration = time.time() - start_time
        
        # Log the operation
        write_run("sync_all_universes", watchlist_count + portfolio_count + market_count, "success", duration)
        
        return {
            "status": "success",
            "message": "All universes synced with current data",
            "results": {
                "market_universe": f"{market_count} tokens populated",
                "watchlist_universe": f"{watchlist_count} tokens synced from UI",
                "portfolio_universe": f"{portfolio_count} positions synced"
            },
            "total_tokens": watchlist_count + portfolio_count + market_count,
            "duration": round(duration, 2)
        }
        
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        logging.error(f"Error syncing universes: {e}")
        write_run("sync_all_universes", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/universes/{universe_name}/sync") 
async def sync_specific_universe(universe_name: str):
    """Sync a specific universe with current data."""
    try:
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        if universe_name not in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid universe name. Must be one of: {MARKET_UNIVERSE}, {WATCHLIST_UNIVERSE}, {PORTFOLIO_UNIVERSE}"
            )
        
        start_time = time.time()
        
        if universe_name == WATCHLIST_UNIVERSE:
            count = await universe_manager.sync_watchlist_universe_from_ui()
            message = f"Synced {count} tokens from UI watchlist"
        elif universe_name == PORTFOLIO_UNIVERSE:
            count = await universe_manager.sync_portfolio_universe_from_positions()
            message = f"Synced {count} active positions"
        else:  # MARKET_UNIVERSE
            count = await universe_manager.populate_market_universe(100)
            message = f"Populated {count} top market cap tokens"
        
        duration = time.time() - start_time
        
        # Log the operation
        write_run(f"sync_{universe_name}_universe", count, "success", duration, universe_name)
        
        return {
            "status": "success",
            "message": message,
            "universe": universe_name,
            "tokens_synced": count,
            "duration": round(duration, 2)
        }
        
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        logging.error(f"Error syncing {universe_name} universe: {e}")
        write_run(f"sync_{universe_name}_universe", 0, "error", duration, universe_name)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/universes/{universe_name}/populate")
async def populate_universe(universe_name: str, token_symbols: List[str] = Body(...)):
    """Populate a specific universe with tokens (manual override)."""
    try:
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        if universe_name not in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid universe name. Must be one of: {MARKET_UNIVERSE}, {WATCHLIST_UNIVERSE}, {PORTFOLIO_UNIVERSE}"
            )
        
        start_time = time.time()
        
        if universe_name == MARKET_UNIVERSE:
            # For market universe, populate with top tokens by market cap
            count = await universe_manager.populate_market_universe(len(token_symbols) if token_symbols else 100)
        elif universe_name == WATCHLIST_UNIVERSE:
            # For watchlist, use provided token list (manual override)
            count = await universe_manager.populate_watchlist_universe(token_symbols)
        else:  # portfolio universe
            # For portfolio, add tokens with default trading data
            count = 0
            for symbol in token_symbols:
                token_data = {
                    'tokenId': symbol.lower(),
                    'symbol': symbol.lower(),
                    'name': symbol.upper(),
                    'quantity': 0,
                    'avgEntry': 0,
                    'include': True,
                    'source': 'manual'
                }
                if await universe_manager.add_token_to_universe(PORTFOLIO_UNIVERSE, token_data):
                    count += 1
        
        duration = time.time() - start_time
        
        # Log the operation
        write_run(f"populate_{universe_name}_universe", count, "success", duration, universe_name)
        
        return {
            "status": "success",
            "message": f"Populated {universe_name} universe with {count} tokens",
            "universe": universe_name,
            "tokens_added": count,
            "duration": round(duration, 2)
        }
        
    except Exception as e:
        duration = time.time() - start_time if 'start_time' in locals() else 0
        logging.error(f"Error populating {universe_name} universe: {e}")
        write_run(f"populate_{universe_name}_universe", 0, "error", duration, universe_name)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/universes/{universe_name}/tokens")
async def add_token_to_universe(universe_name: str, token_data: Dict[str, Any] = Body(...)):
    """Add a single token to a specific universe."""
    try:
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        if universe_name not in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid universe name. Must be one of: {MARKET_UNIVERSE}, {WATCHLIST_UNIVERSE}, {PORTFOLIO_UNIVERSE}"
            )
        
        success = await universe_manager.add_token_to_universe(universe_name, token_data)
        
        if success:
            return {
                "status": "success",
                "message": f"Added token to {universe_name} universe",
                "token": token_data
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add token to universe")
            
    except Exception as e:
        logging.error(f"Error adding token to {universe_name} universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/universes/{universe_name}/tokens/{token_id}")
async def remove_token_from_universe(universe_name: str, token_id: str):
    """Remove a token from a specific universe."""
    try:
        from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE
        
        if universe_name not in [MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid universe name. Must be one of: {MARKET_UNIVERSE}, {WATCHLIST_UNIVERSE}, {PORTFOLIO_UNIVERSE}"
            )
        
        success = await universe_manager.remove_token_from_universe(universe_name, token_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Removed token {token_id} from {universe_name} universe"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to remove token from universe")
            
    except Exception as e:
        logging.error(f"Error removing token from {universe_name} universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

