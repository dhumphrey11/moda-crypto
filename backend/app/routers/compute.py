from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import logging
import time

from ..features.feature_engineer import engineer_features
from ..models.predict import predict_signals
from ..firestore_client import get_tokens_list, write_run

router = APIRouter()


@router.post("/signals")
async def compute_signals(background_tasks: BackgroundTasks):
    """
    Compute trading signals for all tokens.
    This endpoint triggers the full signal computation pipeline:
    1. Feature engineering
    2. ML prediction
    3. Signal generation
    """
    start_time = time.time()
    try:
        logging.info("Starting signal computation pipeline")

        # Get list of tokens to process
        tokens = get_tokens_list()
        if not tokens:
            raise HTTPException(
                status_code=404, detail="No tokens found in database")

        processed_count = 0

        # Process each token
        for token in tokens:
            try:
                token_id = token.get('id') or token.get('symbol', 'unknown')

                # Step 1: Engineer features for this token
                logging.debug(f"Engineering features for {token_id}")
                features = await engineer_features(token)

                if not features:
                    logging.warning(f"No features generated for {token_id}")
                    continue

                # Step 2: Generate prediction and signal
                logging.debug(f"Generating signal for {token_id}")
                signal = await predict_signals(token, features)

                if signal:
                    processed_count += 1
                    logging.debug(
                        f"Signal generated for {token_id}: score={signal.get('composite_score', 0)}")

            except Exception as e:
                logging.error(
                    f"Failed to process token {token.get('symbol', 'unknown')}: {e}")
                continue

        duration = time.time() - start_time

        # Write run log
        background_tasks.add_task(
            write_run, "signal_compute", processed_count, "success", duration)

        return {
            "status": "success",
            "message": f"Computed signals for {processed_count}/{len(tokens)} tokens",
            "processed_count": processed_count,
            "total_tokens": len(tokens),
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Signal computation failed: {e}")
        background_tasks.add_task(
            write_run, "signal_compute", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/features")
async def compute_features_only(background_tasks: BackgroundTasks):
    """
    Compute features only (without predictions) for all tokens.
    Useful for debugging or manual feature inspection.
    """
    start_time = time.time()
    try:
        logging.info("Starting feature computation")

        # Get list of tokens to process
        tokens = get_tokens_list()
        if not tokens:
            raise HTTPException(
                status_code=404, detail="No tokens found in database")

        processed_count = 0

        # Process each token
        for token in tokens:
            try:
                token_id = token.get('id') or token.get('symbol', 'unknown')

                # Engineer features for this token
                logging.debug(f"Engineering features for {token_id}")
                features = await engineer_features(token)

                if features:
                    processed_count += 1

            except Exception as e:
                logging.error(
                    f"Failed to process features for token {token.get('symbol', 'unknown')}: {e}")
                continue

        duration = time.time() - start_time

        # Write run log
        background_tasks.add_task(
            write_run, "feature_engineer", processed_count, "success", duration)

        return {
            "status": "success",
            "message": f"Computed features for {processed_count}/{len(tokens)} tokens",
            "processed_count": processed_count,
            "total_tokens": len(tokens),
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Feature computation failed: {e}")
        background_tasks.add_task(
            write_run, "feature_engineer", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/recent")
async def get_recent_signals(hours: int = 24):
    """Get recent signals from the database."""
    try:
        from ..firestore_client import get_recent_signals

        signals = get_recent_signals(hours=hours)

        return {
            "status": "success",
            "signals": signals,
            "count": len(signals),
            "hours": hours
        }

    except Exception as e:
        logging.error(f"Failed to get recent signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/top")
async def get_top_signals(limit: int = 10, min_score: float = 0.7):
    """Get top signals by composite score."""
    try:
        from ..firestore_client import get_recent_signals

        # Get recent signals and filter by score
        all_signals = get_recent_signals(hours=24)

        # Filter and sort by composite score
        top_signals = [
            signal for signal in all_signals
            if signal.get('composite_score', 0) >= min_score
        ]

        top_signals.sort(key=lambda x: x.get(
            'composite_score', 0), reverse=True)
        top_signals = top_signals[:limit]

        return {
            "status": "success",
            "signals": top_signals,
            "count": len(top_signals),
            "min_score": min_score,
            "limit": limit
        }

    except Exception as e:
        logging.error(f"Failed to get top signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
