from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import asyncio
import time

from ..services import coingecko, moralis, covalent, lunarcrush, coinmarketcal, cryptopanic
from ..firestore_client import write_run

router = APIRouter()


@router.post("/coingecko")
async def fetch_coingecko_data(background_tasks: BackgroundTasks):
    """Fetch market data from CoinGecko API."""
    start_time = time.time()
    try:
        logging.info("Starting CoinGecko data fetch")

        # Fetch data from CoinGecko service
        data = await coingecko.fetch_market_data()
        count = len(data) if data else 0

        # Write run log
        duration = time.time() - start_time
        background_tasks.add_task(
            write_run, "coingecko", count, "success", duration)

        return {
            "status": "success",
            "message": f"Fetched {count} market data points from CoinGecko",
            "count": count,
            "duration": round(duration, 2)
        }

    except Exception as e:
        duration = time.time() - start_time
        logging.error(f"CoinGecko fetch failed: {e}")
        background_tasks.add_task(write_run, "coingecko", 0, "error", duration)
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
