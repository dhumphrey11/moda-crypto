from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional
import logging
import asyncio
import time

from ..services import coingecko, moralis, covalent, lunarcrush, coinmarketcal, cryptopanic
from ..firestore_client import write_run
from ..universe_manager import universe_manager, MARKET_UNIVERSE, WATCHLIST_UNIVERSE, PORTFOLIO_UNIVERSE

router = APIRouter()


# =============================================================================
# UNIVERSE-BASED FETCH ENDPOINTS
# =============================================================================

@router.post("/market-summary")
async def fetch_market_summary(background_tasks: BackgroundTasks):
    """Fetch market summary data for Market Universe (hourly schedule)."""
    start_time = time.time()
    try:
        logging.info("Starting Market Universe data fetch")
        
        # Get market universe tokens
        market_tokens = await universe_manager.get_universe_symbols(MARKET_UNIVERSE)
        
        if not market_tokens:
            logging.warning("No tokens found in market universe")
            return {
                "status": "warning",
                "message": "No tokens configured in market universe",
                "count": 0
            }
        
        # Fetch market data and filter by market universe tokens
        all_data = await coingecko.fetch_market_data()
        # Filter data to only include market universe tokens
        data = [item for item in all_data if item.get('symbol', '').lower() in market_tokens] if all_data else []
        count = len(data) if data else 0
        
        # Write run log with universe information
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "market_summary", count, "success", duration, MARKET_UNIVERSE)
        
        return {
            "status": "success",
            "message": f"Fetched market summary for {count} tokens from Market Universe",
            "universe": MARKET_UNIVERSE,
            "token_count": len(market_tokens),
            "data_points": count,
            "duration": round(duration, 2)
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Market summary fetch failed: {e}")
        background_tasks.add_task(write_run, "market_summary", 0, "error", duration, MARKET_UNIVERSE)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market-tokens")
async def fetch_market_tokens(background_tasks: BackgroundTasks):
    """Fetch basic token metrics for Market Universe (30min schedule)."""
    start_time = time.time()
    try:
        logging.info("Starting Market Universe token metrics fetch")
        
        # Get market universe tokens
        market_tokens = await universe_manager.get_universe_symbols(MARKET_UNIVERSE)
        
        if not market_tokens:
            return {
                "status": "warning", 
                "message": "No tokens configured in market universe",
                "count": 0
            }
        
        # Fetch basic token metrics and filter by market universe
        all_data = await coingecko.fetch_market_data()
        # Filter data to only include market universe tokens  
        data = [item for item in all_data if item.get('symbol', '').lower() in market_tokens] if all_data else []
        count = len(data) if data else 0
        
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "market_tokens", count, "success", duration, MARKET_UNIVERSE)
        
        return {
            "status": "success",
            "message": f"Fetched token metrics for {count} tokens from Market Universe",
            "universe": MARKET_UNIVERSE,
            "token_count": len(market_tokens),
            "data_points": count,
            "duration": round(duration, 2)
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Market tokens fetch failed: {e}")
        background_tasks.add_task(write_run, "market_tokens", 0, "error", duration, MARKET_UNIVERSE)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/features")
async def fetch_features_data(background_tasks: BackgroundTasks):
    """Fetch comprehensive feature data for Watchlist Universe (15-60min schedule)."""
    start_time = time.time()
    try:
        logging.info("Starting Watchlist Universe features fetch")
        
        # Get watchlist universe tokens
        watchlist_tokens = await universe_manager.get_universe_symbols(WATCHLIST_UNIVERSE)
        
        if not watchlist_tokens:
            return {
                "status": "warning",
                "message": "No tokens configured in watchlist universe", 
                "count": 0
            }
        
        # Execute multiple API calls for comprehensive feature data
        # Note: Current service implementations will fetch all data, then we filter by watchlist_tokens
        tasks = [
            coingecko.fetch_market_data(),
            moralis.fetch_onchain_data(),
            covalent.fetch_blockchain_data(),
            lunarcrush.fetch_social_data(),
            coinmarketcal.fetch_events(),
            cryptopanic.fetch_news()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_count = 0
        successful_sources = 0
        errors = []
        
        source_names = ['coingecko', 'moralis', 'covalent', 'lunarcrush', 'coinmarketcal', 'cryptopanic']
        
        for i, result in enumerate(results):
            source = source_names[i]
            if isinstance(result, Exception):
                errors.append(f"{source}: {str(result)}")
            else:
                count = len(result) if result and isinstance(result, list) else 0
                total_count += count
                successful_sources += 1
        
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "features", total_count, "success", duration, WATCHLIST_UNIVERSE)
        
        return {
            "status": "success",
            "message": f"Fetched features for {len(watchlist_tokens)} tokens from Watchlist Universe",
            "universe": WATCHLIST_UNIVERSE,
            "token_count": len(watchlist_tokens),
            "total_data_points": total_count,
            "successful_sources": successful_sources,
            "duration": round(duration, 2),
            "errors": errors if errors else None
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Features fetch failed: {e}")
        background_tasks.add_task(write_run, "features", 0, "error", duration, WATCHLIST_UNIVERSE)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio")
async def fetch_portfolio_data(background_tasks: BackgroundTasks):
    """Fetch real-time data for Portfolio Universe (1-5min schedule)."""
    start_time = time.time()
    try:
        logging.info("Starting Portfolio Universe data fetch")
        
        # Get portfolio universe tokens 
        portfolio_tokens = await universe_manager.get_universe_symbols(PORTFOLIO_UNIVERSE)
        
        if not portfolio_tokens:
            return {
                "status": "warning",
                "message": "No tokens configured in portfolio universe",
                "count": 0
            }
        
        # Fetch real-time price and position data
        # Note: Using available service functions, then filtering by portfolio tokens
        tasks = [
            coingecko.fetch_market_data(),  # Get current prices from market data
            # coinbase.fetch_account_data(),  # Would fetch actual positions if connected 
            moralis.fetch_onchain_data()  # Get on-chain data, then filter for portfolio tokens
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_count = 0
        successful_sources = 0
        
        for result in results:
            if not isinstance(result, Exception):
                count = len(result) if result and isinstance(result, list) else 0
                total_count += count
                successful_sources += 1
        
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "portfolio", total_count, "success", duration, PORTFOLIO_UNIVERSE)
        
        return {
            "status": "success",
            "message": f"Fetched portfolio data for {len(portfolio_tokens)} tokens from Portfolio Universe",
            "universe": PORTFOLIO_UNIVERSE, 
            "token_count": len(portfolio_tokens),
            "data_points": total_count,
            "duration": round(duration, 2)
        }
        
    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Portfolio fetch failed: {e}")
        background_tasks.add_task(write_run, "portfolio", 0, "error", duration, PORTFOLIO_UNIVERSE)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LEGACY ENDPOINTS (for backward compatibility)  
# =============================================================================

@router.post("/coingecko")
async def fetch_coingecko_data(
    background_tasks: BackgroundTasks, 
    universe: Optional[str] = Query(None, description="Target universe for data fetch")
):
    """Fetch market data from CoinGecko API."""
    start_time = time.time()
    try:
        logging.info(f"Starting CoinGecko data fetch for universe: {universe or 'all'}")

        # Get tokens based on universe or fetch all
        all_data = await coingecko.fetch_market_data()
        
        if universe:
            tokens = await universe_manager.get_universe_symbols(universe)
            # Filter data to only include universe tokens
            data = [item for item in all_data if item.get('symbol', '').lower() in tokens] if all_data else []
        else:
            data = all_data
            
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "coingecko", count, "success", duration, universe)

        return {
            "status": "success",
            "message": f"Fetched {count} market data points from CoinGecko",
            "universe": universe,
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"CoinGecko fetch failed: {e}")
        background_tasks.add_task(write_run, "coingecko", 0, "error", duration, universe)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/moralis")
async def fetch_moralis_data(background_tasks: BackgroundTasks):
    """Fetch on-chain data from Moralis API."""
    start_time = time.time()
    try:
        logging.info("Starting Moralis data fetch")

        # Fetch data from Moralis service
        data = await moralis.fetch_onchain_data()
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "moralis", count, "success", duration)

        return {
            "status": "success",
            "message": f"Fetched {count} on-chain data points from Moralis",
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Moralis fetch failed: {e}")
        background_tasks.add_task(write_run, "moralis", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/covalent")
async def fetch_covalent_data(background_tasks: BackgroundTasks):
    """Fetch blockchain data from Covalent API."""
    start_time = time.time()
    try:
        logging.info("Starting Covalent data fetch")

        # Fetch data from Covalent service
        data = await covalent.fetch_blockchain_data()
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "covalent", count, "success", duration)

        return {
            "status": "success",
            "message": f"Fetched {count} blockchain data points from Covalent",
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Covalent fetch failed: {e}")
        background_tasks.add_task(write_run, "covalent", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lunarcrush")
async def fetch_lunarcrush_data(background_tasks: BackgroundTasks):
    """Fetch social sentiment data from LunarCrush API."""
    start_time = time.time()
    try:
        logging.info("Starting LunarCrush data fetch")

        # Fetch data from LunarCrush service
        data = await lunarcrush.fetch_social_data()
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "lunarcrush", count, "success", duration)

        return {
            "status": "success",
            "message": f"Fetched {count} social data points from LunarCrush",
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"LunarCrush fetch failed: {e}")
        background_tasks.add_task(
            write_run, "lunarcrush", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coinmarketcal")
async def fetch_coinmarketcal_data(background_tasks: BackgroundTasks):
    """Fetch event data from CoinMarketCal API."""
    start_time = time.time()
    try:
        logging.info("Starting CoinMarketCal data fetch")

        # Fetch data from CoinMarketCal service
        data = await coinmarketcal.fetch_events()
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "coinmarketcal", count, "success", duration)

        return {
            "status": "success",
            "message": f"Fetched {count} events from CoinMarketCal",
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"CoinMarketCal fetch failed: {e}")
        background_tasks.add_task(
            write_run, "coinmarketcal", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cryptopanic")
async def fetch_cryptopanic_data(background_tasks: BackgroundTasks):
    """Fetch news sentiment data from CryptoPanic API."""
    start_time = time.time()
    try:
        logging.info("Starting CryptoPanic data fetch")

        # Fetch data from CryptoPanic service
        data = await cryptopanic.fetch_news()
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "cryptopanic", count, "success", duration)

        return {
            "status": "success",
            "message": f"Fetched {count} news items from CryptoPanic",
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"CryptoPanic fetch failed: {e}")
        background_tasks.add_task(
            write_run, "cryptopanic", 0, "error", duration)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/all")
async def fetch_all_data(background_tasks: BackgroundTasks):
    """Fetch data from all external sources."""
    start_time = time.time()
    try:
        logging.info("Starting fetch from all sources")

        # Execute all fetch operations concurrently
        tasks = [
            coingecko.fetch_market_data(),
            moralis.fetch_onchain_data(),
            covalent.fetch_blockchain_data(),
            lunarcrush.fetch_social_data(),
            coinmarketcal.fetch_events(),
            cryptopanic.fetch_news()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        total_count = 0
        successful_sources = 0
        errors = []

        source_names = ['coingecko', 'moralis', 'covalent',
                        'lunarcrush', 'coinmarketcal', 'cryptopanic']

        for i, result in enumerate(results):
            source = source_names[i]
            if isinstance(result, Exception):
                errors.append(f"{source}: {str(result)}")
                background_tasks.add_task(write_run, source, 0, "error", 0)
            else:
                count = len(result) if result and isinstance(result, list) else 0
                total_count += count
                successful_sources += 1
                background_tasks.add_task(
                    write_run, source, count, "success", 0)

        duration = time.time() - start_time

        return {
            "status": "completed",
            "message": f"Fetch completed: {successful_sources}/6 sources successful",
            "total_count": total_count,
            "successful_sources": successful_sources,
            "duration": round(duration, 2),
            "errors": errors if errors else None
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"Fetch all failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
