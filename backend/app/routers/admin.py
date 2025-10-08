from fastapi import APIRouter, HTTPException, BackgroundTasks
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
    ml_weight: float = None,
    rule_weight: float = None,
    sentiment_weight: float = None,
    event_weight: float = None,
    min_composite_score: float = None
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
