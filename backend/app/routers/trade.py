from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import logging
import time

from ..paper_trade.executor import execute_paper_trades
from ..firestore_client import (
    write_run, get_open_trades, get_portfolio, 
    get_recent_trades, get_portfolio_history, get_trades_paginated,
    write_portfolio_snapshot
)

router = APIRouter()


@router.post("/execute")
async def execute_trades(background_tasks: BackgroundTasks):
    """
    Execute paper trades based on recent signals.
    Processes signals with composite_score >= min_threshold and executes trades
    according to risk management rules.
    """
    start_time = time.time()
    try:
        logging.info("Starting paper trade execution")

        # Execute paper trades
        result = await execute_paper_trades()

        duration = time.time() - start_time
        trades_executed = result.get('trades_executed', 0)

        # Write run log
        background_tasks.add_task(
            write_run, "paper_trade", trades_executed, "success", duration)

        return {
            "status": "success",
            "message": f"Paper trade execution completed",
            "trades_executed": trades_executed,
            "signals_processed": result.get('signals_processed', 0),
            "skipped_reasons": result.get('skipped_reasons', {}),
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Paper trade execution failed: {e}")
        background_tasks.add_task(
            write_run, "paper_trade", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio")
async def get_current_portfolio():
    """Get current portfolio positions and performance."""
    try:
        portfolio = get_portfolio()

        # Calculate portfolio summary
        total_value = 0
        total_cost = 0
        positions = []

        for token_id, position in portfolio.items():
            current_value = position.get('current_value', 0)
            cost_basis = position.get(
                'quantity', 0) * position.get('avg_cost', 0)
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            total_value += current_value
            total_cost += cost_basis

            positions.append({
                'token_id': token_id,
                'quantity': position.get('quantity', 0),
                'avg_cost': position.get('avg_cost', 0),
                'current_value': current_value,
                'cost_basis': cost_basis,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'last_updated': position.get('last_updated')
            })

        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        return {
            "status": "success",
            "portfolio": {
                "positions": positions,
                "summary": {
                    "total_value": total_value,
                    "total_cost": total_cost,
                    "total_pnl": total_pnl,
                    "total_pnl_pct": total_pnl_pct,
                    "position_count": len(positions)
                }
            }
        }

    except Exception as e:
        logging.error(f"Failed to get portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades")
async def get_trades(status: str | None = None, limit: int = 50):
    """Get trade history with optional status filter."""
    try:
        if status:
            # Get trades with specific status
            if status == "open":
                trades = get_open_trades()
            else:
                # TODO: Implement get_trades_by_status function
                trades = []
        else:
            # Get all recent trades
            # TODO: Implement get_recent_trades function
            trades = []

        # Limit results
        trades = trades[:limit]

        return {
            "status": "success",
            "trades": trades,
            "count": len(trades),
            "filter": {"status": status, "limit": limit}
        }

    except Exception as e:
        logging.error(f"Failed to get trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_performance_metrics():
    """Get paper trading performance metrics."""
    try:
        # Get portfolio and trade data
        portfolio = get_portfolio()
        open_trades = get_open_trades()

        # TODO: Implement comprehensive performance calculations
        # This would include metrics like:
        # - Total return %
        # - Sharpe ratio
        # - Max drawdown
        # - Win rate
        # - Average hold time
        # - Best/worst trades

        metrics = {
            "total_positions": len(portfolio),
            "open_trades": len(open_trades),
            "portfolio_value": sum(p.get('current_value', 0) for p in portfolio.values()),
            # Add more sophisticated metrics here
        }

        return {
            "status": "success",
            "performance": metrics,
            "updated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logging.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close/{trade_id}")
async def close_trade(trade_id: str, background_tasks: BackgroundTasks):
    """Manually close a specific trade."""
    try:
        # TODO: Implement manual trade closure
        # This would:
        # 1. Get the trade details
        # 2. Get current market price
        # 3. Calculate PnL
        # 4. Update trade status to 'closed'
        # 5. Update portfolio position

        logging.info(f"Manual trade closure requested for trade {trade_id}")

        return {
            "status": "success",
            "message": f"Trade {trade_id} closed manually",
            "trade_id": trade_id
        }

    except Exception as e:
        logging.error(f"Failed to close trade {trade_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/history")
async def get_portfolio_history_endpoint(days: int = 30):
    """Get portfolio value history for dashboard charts."""
    try:
        history = get_portfolio_history(days)
        
        # Transform data for frontend consumption
        chart_data = []
        for snapshot in history:
            chart_data.append({
                "date": snapshot.get("timestamp", datetime.utcnow()).isoformat(),
                "value": snapshot.get("total_value", 0),
                "pnl": snapshot.get("total_pnl", 0),
                "pnl_pct": snapshot.get("total_pnl_pct", 0),
                "positions_count": snapshot.get("positions_count", 0)
            })
        
        return {
            "status": "success",
            "data": chart_data,
            "period_days": days,
            "data_points": len(chart_data)
        }
        
    except Exception as e:
        logging.error(f"Failed to get portfolio history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/recent")
async def get_recent_trades_endpoint(limit: int = 10):
    """Get recent trades for dashboard display."""
    try:
        trades = get_recent_trades(limit)
        
        # Transform for frontend
        recent_trades = []
        for trade in trades:
            recent_trades.append({
                "id": trade.get("id"),
                "token_id": trade.get("token_id"),
                "action": trade.get("action"),
                "quantity": trade.get("quantity", 0),
                "price": trade.get("price", 0),
                "total_value": trade.get("total_value", 0),
                "timestamp": trade.get("timestamp", datetime.utcnow()).isoformat(),
                "status": trade.get("status", "unknown")
            })
        
        return {
            "status": "success",
            "trades": recent_trades,
            "count": len(recent_trades)
        }
        
    except Exception as e:
        logging.error(f"Failed to get recent trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/paginated")
async def get_trades_paginated_endpoint(page: int = 1, limit: int = 20, status: str | None = None):
    """Get paginated trades with optional status filter."""
    try:
        result = get_trades_paginated(page, limit, status)
        
        # Transform trades for frontend
        trades = []
        for trade in result.get("trades", []):
            trades.append({
                "id": trade.get("id"),
                "token_id": trade.get("token_id"),
                "action": trade.get("action"),
                "quantity": trade.get("quantity", 0),
                "price": trade.get("price", 0),
                "total_value": trade.get("total_value", 0),
                "timestamp": trade.get("timestamp", datetime.utcnow()).isoformat(),
                "status": trade.get("status", "unknown"),
                "signal_confidence": trade.get("signal_confidence", 0),
                "pnl": trade.get("pnl", 0),
                "pnl_pct": trade.get("pnl_pct", 0)
            })
        
        return {
            "status": "success",
            "trades": trades,
            "pagination": result.get("pagination", {})
        }
        
    except Exception as e:
        logging.error(f"Failed to get paginated trades: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/snapshot")
async def create_portfolio_snapshot():
    """Create a portfolio snapshot for historical tracking."""
    try:
        # Get current portfolio
        portfolio = get_portfolio()
        
        # Calculate summary
        total_value = 0
        total_cost = 0
        positions = []
        
        for token_id, position in portfolio.items():
            current_value = position.get('current_value', 0)
            cost_basis = position.get('quantity', 0) * position.get('avg_cost', 0)
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            total_value += current_value
            total_cost += cost_basis
            
            positions.append({
                'token_id': token_id,
                'quantity': position.get('quantity', 0),
                'avg_cost': position.get('avg_cost', 0),
                'current_value': current_value,
                'cost_basis': cost_basis,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # Create snapshot data
        snapshot_data = {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions_count": len(positions),
            "positions": positions
        }
        
        # Write snapshot
        snapshot_id = write_portfolio_snapshot(snapshot_data)
        
        return {
            "status": "success",
            "message": "Portfolio snapshot created",
            "snapshot_id": snapshot_id,
            "snapshot": snapshot_data
        }
        
    except Exception as e:
        logging.error(f"Failed to create portfolio snapshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))
