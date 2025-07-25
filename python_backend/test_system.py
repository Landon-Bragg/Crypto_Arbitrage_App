#!/usr/bin/env python3
"""
Simple test script for the arbitrage system
"""
import asyncio
import logging
from exchanges.exchange_manager import exchange_manager
from arbitrage.detector import arbitrage_detector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test the system"""
    logger.info("🚀 Testing Crypto Arbitrage System")
    
    try:
        # Initialize exchanges
        logger.info("🔌 Initializing exchanges...")
        results = await exchange_manager.initialize()
        
        connected = sum(results.values())
        logger.info(f"✅ {connected}/3 exchanges connected")
        
        if connected < 2:
            logger.error("❌ Need at least 2 exchanges for testing")
            return
        
        # Test quote fetching
        logger.info("📊 Fetching quotes...")
        quotes = await exchange_manager.fetch_all_quotes()
        logger.info(f"✅ Received quotes from {len(quotes)} exchanges")
        
        # Test arbitrage detection
        logger.info("🔍 Detecting arbitrage opportunities...")
        opportunities = await arbitrage_detector.detect_opportunities()
        logger.info(f"✅ Found {len(opportunities)} opportunities")
        
        for opp in opportunities[:3]:
            logger.info(f"💰 {opp.symbol}: {opp.spread_percent:.3f}% "
                       f"({opp.buy_exchange} → {opp.sell_exchange})")
        
        logger.info("🎉 System test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
