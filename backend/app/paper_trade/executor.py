import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..firestore_client import (
    init_db, get_recent_signals, get_open_trades, get_portfolio,
    write_trade, update_portfolio, get_admin_config
)
from ..config import settings


async def execute_paper_trades() -> Dict[str, Any]:
    """
    Execute paper trades based on recent high-confidence signals.

    This function:
    1. Gets recent signals above threshold
    2. Applies risk management rules
    3. Executes qualifying trades
    4. Updates portfolio positions

    Returns:
        Dictionary with execution results and statistics
    """
    try:
        logging.info("Starting paper trade execution")

        # Get configuration
        admin_config = get_admin_config()
        min_composite_score = admin_config.get(
            'min_composite_score', settings.min_composite_score)

        # 1. Get recent high-confidence signals
        recent_signals = get_recent_signals(hours=2)  # Last 2 hours
        qualifying_signals = [
            signal for signal in recent_signals
            if signal.get('composite_score', 0) >= min_composite_score
            and signal.get('action') in ['buy', 'sell']
        ]

        logging.info(f"Found {len(qualifying_signals)} qualifying signals")

        # 2. Get current portfolio and open trades
        portfolio = get_portfolio()
        open_trades = get_open_trades()

        # 3. Calculate available cash
        available_cash = _calculate_available_cash(portfolio)

        # 4. Execute trades
        results = {
            'signals_processed': len(qualifying_signals),
            'trades_executed': 0,
            'skipped_reasons': {},
            'executed_trades': []
        }

        for signal in qualifying_signals:
            try:
                trade_result = await _execute_single_trade(
                    signal, portfolio, open_trades, available_cash, admin_config
                )

                if trade_result['executed']:
                    results['trades_executed'] += 1
                    results['executed_trades'].append(trade_result)

                    # Update available cash
                    if signal.get('action') == 'buy':
                        available_cash -= trade_result.get('total_cost', 0)
                else:
                    reason = trade_result.get('skip_reason', 'unknown')
                    results['skipped_reasons'][reason] = results['skipped_reasons'].get(
                        reason, 0) + 1

            except Exception as e:
                logging.error(
                    f"Failed to execute trade for signal {signal.get('id', 'unknown')}: {e}")
                results['skipped_reasons']['execution_error'] = results['skipped_reasons'].get(
                    'execution_error', 0) + 1

        logging.info(
            f"Paper trade execution completed: {results['trades_executed']} trades executed")
        return results

    except Exception as e:
        logging.error(f"Paper trade execution failed: {e}")
        raise


async def _execute_single_trade(
    signal: Dict[str, Any],
    portfolio: Dict[str, Any],
    open_trades: List[Dict[str, Any]],
    available_cash: float,
    admin_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a single paper trade based on signal."""
    try:
        token_id = signal['token_id']
        action = signal['action']
        composite_score = signal.get('composite_score', 0)

        # 1. Check if we already have an open position for this token
        existing_position = portfolio.get(token_id)
        existing_open_trades = [
            t for t in open_trades if t.get('token_id') == token_id]

        if action == 'buy':
            # Check if we already have an open buy position
            if existing_open_trades:
                return {
                    'executed': False,
                    'skip_reason': 'existing_open_trade',
                    'token_id': token_id
                }

            # 2. Risk management checks
            risk_check = _check_buy_risk_rules(
                token_id, signal, available_cash, portfolio, admin_config
            )

            if not risk_check['allowed']:
                return {
                    'executed': False,
                    'skip_reason': risk_check['reason'],
                    'token_id': token_id
                }

            # 3. Calculate position size
            position_size = _calculate_position_size(
                available_cash, composite_score, admin_config
            )

            # 4. Get current market price (simplified)
            current_price = _get_current_price(token_id)
            if current_price <= 0:
                return {
                    'executed': False,
                    'skip_reason': 'no_price_data',
                    'token_id': token_id
                }

            # 5. Calculate quantity
            quantity = position_size / current_price
            total_cost = quantity * current_price

            # 6. Execute buy trade
            trade_data = {
                'signal_id': signal.get('id', ''),
                'token_id': token_id,
                'action': 'buy',
                'quantity': quantity,
                'price': current_price,
                'total_cost': total_cost,
                'composite_score': composite_score,
                'status': 'open',
                'timestamp': datetime.utcnow()
            }

            trade_id = write_trade(trade_data)

            # 7. Update portfolio
            if existing_position:
                # Average down/up
                existing_qty = existing_position.get('quantity', 0)
                existing_cost = existing_position.get('avg_cost', 0)

                new_qty = existing_qty + quantity
                new_avg_cost = (
                    (existing_qty * existing_cost) + total_cost) / new_qty

                update_portfolio(token_id, new_qty, new_avg_cost)
            else:
                # New position
                update_portfolio(token_id, quantity, current_price)

            return {
                'executed': True,
                'trade_id': trade_id,
                'token_id': token_id,
                'action': 'buy',
                'quantity': quantity,
                'price': current_price,
                'total_cost': total_cost
            }

        elif action == 'sell':
            # Check if we have a position to sell
            if not existing_position or existing_position.get('quantity', 0) <= 0:
                return {
                    'executed': False,
                    'skip_reason': 'no_position_to_sell',
                    'token_id': token_id
                }

            # 3. Get current market price
            current_price = _get_current_price(token_id)
            if current_price <= 0:
                return {
                    'executed': False,
                    'skip_reason': 'no_price_data',
                    'token_id': token_id
                }

            # 4. Calculate sell quantity (sell entire position for simplicity)
            sell_quantity = existing_position['quantity']
            total_proceeds = sell_quantity * current_price

            # 5. Calculate P&L
            avg_cost = existing_position.get('avg_cost', 0)
            cost_basis = sell_quantity * avg_cost
            pnl = total_proceeds - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0

            # 6. Execute sell trade
            trade_data = {
                'signal_id': signal.get('id', ''),
                'token_id': token_id,
                'action': 'sell',
                'quantity': sell_quantity,
                'price': current_price,
                'total_proceeds': total_proceeds,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'composite_score': composite_score,
                'status': 'closed',
                'timestamp': datetime.utcnow()
            }

            trade_id = write_trade(trade_data)

            # 7. Update portfolio (remove position)
            update_portfolio(token_id, 0, 0)

            return {
                'executed': True,
                'trade_id': trade_id,
                'token_id': token_id,
                'action': 'sell',
                'quantity': sell_quantity,
                'price': current_price,
                'total_proceeds': total_proceeds,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            }

        return {
            'executed': False,
            'skip_reason': 'invalid_action',
            'token_id': token_id
        }

    except Exception as e:
        logging.error(f"Single trade execution failed: {e}")
        return {
            'executed': False,
            'skip_reason': 'execution_error',
            'error': str(e)
        }


def _calculate_available_cash(portfolio: Dict[str, Any]) -> float:
    """Calculate available cash for trading."""
    try:
        # Start with initial cash
        total_cash = settings.initial_cash

        # Subtract current position values (simplified calculation)
        used_cash = 0
        for token_id, position in portfolio.items():
            quantity = position.get('quantity', 0)
            avg_cost = position.get('avg_cost', 0)
            used_cash += quantity * avg_cost

        available_cash = total_cash - used_cash
        return max(available_cash, 0)

    except Exception as e:
        logging.error(f"Failed to calculate available cash: {e}")
        return 0


def _check_buy_risk_rules(
    token_id: str,
    signal: Dict[str, Any],
    available_cash: float,
    portfolio: Dict[str, Any],
    admin_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Check risk management rules for buy orders."""
    try:
        # 1. Check minimum liquidity (placeholder - would need real liquidity data)
        min_liquidity = settings.min_liquidity_usd
        # For demo, assume all tokens meet liquidity requirements

        # 2. Check available cash
        max_position_size = available_cash * settings.max_position_size
        if max_position_size < 100:  # Minimum $100 trade
            return {
                'allowed': False,
                'reason': 'insufficient_cash'
            }

        # 3. Check maximum allocation per token
        current_position = portfolio.get(token_id, {})
        current_value = current_position.get(
            'quantity', 0) * current_position.get('avg_cost', 0)
        max_token_allocation = settings.initial_cash * settings.max_token_allocation

        if current_value >= max_token_allocation:
            return {
                'allowed': False,
                'reason': 'max_allocation_reached'
            }

        # 4. Check if we would exceed max allocation with this trade
        if (current_value + max_position_size) > max_token_allocation:
            return {
                'allowed': False,
                'reason': 'would_exceed_max_allocation'
            }

        # 5. Check signal confidence
        composite_score = signal.get('composite_score', 0)
        if composite_score < admin_config.get('min_composite_score', settings.min_composite_score):
            return {
                'allowed': False,
                'reason': 'insufficient_confidence'
            }

        return {
            'allowed': True,
            'reason': 'passed_all_checks'
        }

    except Exception as e:
        logging.error(f"Risk check failed: {e}")
        return {
            'allowed': False,
            'reason': 'risk_check_error'
        }


def _calculate_position_size(available_cash: float, composite_score: float, admin_config: Dict[str, Any]) -> float:
    """Calculate position size based on available cash and signal confidence."""
    try:
        # Base position size
        base_size = available_cash * settings.max_position_size

        # Adjust based on signal confidence
        # Scale 0.5-1.0 signal to 1.0-2.0 multiplier
        confidence_multiplier = min(composite_score / 0.5, 2.0)

        # Apply confidence adjustment
        position_size = base_size * confidence_multiplier

        # Cap at maximum position size
        max_size = available_cash * settings.max_position_size
        position_size = min(position_size, max_size)

        # Minimum position size
        min_size = 100  # $100 minimum
        position_size = max(position_size, min_size)

        return position_size

    except Exception as e:
        logging.error(f"Position size calculation failed: {e}")
        return 100  # Default minimum


def _get_current_price(token_id: str) -> float:
    """Get current market price for a token."""
    try:
        # In a real implementation, this would fetch current price from an exchange API
        # For demo purposes, we'll get the last known price from features

        db = init_db()

        # Get most recent price data
        docs = db.collection('features')\
                 .where('token_id', '==', token_id)\
                 .where('current_price', '>', 0)\
                 .order_by('timestamp', direction='DESCENDING')\
                 .limit(1)\
                 .stream()

        for doc in docs:
            data = doc.to_dict()
            price = data.get('current_price', 0)
            if price > 0:
                return float(price)

        # Fallback: use some default prices for demo
        default_prices = {
            'BTC': 45000,
            'ETH': 3000,
            'ADA': 0.5,
            'SOL': 100,
            'DOT': 7,
            'MATIC': 0.8,
            'LINK': 15,
            'UNI': 6
        }

        return default_prices.get(token_id, 1.0)

    except Exception as e:
        logging.error(f"Failed to get current price for {token_id}: {e}")
        return 0
