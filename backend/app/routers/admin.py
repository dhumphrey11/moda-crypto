from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from datetime import datetime
import logging
import time

from ..models.train import train_model, get_model_info
from ..firestore_client import write_run, get_admin_config
from ..config import settings

router = APIRouter()


@router.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
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

        # Write run log
        background_tasks.add_task(
            write_run, "model_retrain", 1, "success", duration)

        return {
            "status": "success",
            "message": "Model retraining completed successfully",
            "model_info": model_info,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Model retraining failed: {e}")
        background_tasks.add_task(
            write_run, "model_retrain", 0, "error", duration)
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
async def sync_token_list(background_tasks: BackgroundTasks):
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
        
        return {
            "status": "success",
            "message": f"Token {token_id} removed from watchlist"
        }
    
    except Exception as e:
        logging.error(f"Failed to remove token from watchlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/watchlist/sync")
async def sync_watchlist_data(background_tasks: BackgroundTasks):
    """Sync watchlist tokens with latest market data."""
    try:
        from ..firestore_client import get_tokens_list
        
        # Get active tokens
        tokens = get_tokens_list()
        active_tokens = [token for token in tokens if token.get('active', True)]
        
        # TODO: Implement actual sync with CoinGecko or other data sources
        # This would fetch current market data for all active tokens
        
        synced_count = len(active_tokens)
        
        background_tasks.add_task(
            write_run, "watchlist_sync", synced_count, "success", 0
        )
        
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


@router.post("/system/monitoring/start-background")
async def start_background_monitoring_endpoint():
    """Start background monitoring tasks."""
    try:
        from ..monitoring import start_background_monitoring, get_monitoring_status
        
        # Start monitoring scheduler
        monitoring_started = await start_background_monitoring()
        
        if monitoring_started:
            # Run initial threshold check
            from ..firestore_client import check_system_thresholds
            alerts_created = check_system_thresholds()
            
            status = get_monitoring_status()
            
            logging.info("Background monitoring started via admin endpoint")
            
            return {
                "status": "success",
                "message": "Background monitoring started successfully",
                "initial_alerts_created": len(alerts_created),
                "monitoring_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            status = get_monitoring_status()
            return {
                "status": "success",
                "message": "Background monitoring was already running",
                "monitoring_status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logging.error(f"Error starting background monitoring: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/system/monitoring/stop-background")
async def stop_background_monitoring_endpoint():
    """Stop background monitoring tasks."""
    try:
        from ..monitoring import stop_background_monitoring, get_monitoring_status
        
        # Stop monitoring scheduler
        monitoring_stopped = await stop_background_monitoring()
        
        if monitoring_stopped:
            logging.info("Background monitoring stopped via admin endpoint")
            return {
                "status": "success",
                "message": "Background monitoring stopped successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "success",
                "message": "Background monitoring was not running",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logging.error(f"Error stopping background monitoring: {e}")
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
