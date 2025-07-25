#!/usr/bin/env python3
"""
Test script to demonstrate live market data fetching
"""
import asyncio
import json
import time
from exchanges import exchange_manager
from arbitrage_detector import arbitrage_detector

async def test_exchange_connections():
    """Test connections to all exchanges"""
    print("🔌 Testing exchange connections...")
    results = await exchange_manager.test_connections()
    
    for exchange, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {exchange}: {'Connected' if status else 'Failed'}")
    
    return results

async def test_live_quotes():
    """Test fetching live quotes"""
    print("\n📊 Fetching live market data...")
    
    quotes = await exchange_manager.fetch_all_quotes()
    
    if not quotes:
        print("❌ No quotes received")
        return
    
    print(f"✅ Received quotes from {len(quotes)} exchanges")
    
    for exchange, symbols in quotes.items():
        print(f"\n📈 {exchange.upper()}:")
        for symbol, quote in symbols.items():
            print(f"  {symbol}: bid={quote.bid:.4f}, ask={quote.ask:.4f}, "
                  f"spread={((quote.ask - quote.bid) / quote.bid * 100):.3f}%")

async def test_arbitrage_detection():
    """Test arbitrage detection"""
    print("\n🔍 Detecting arbitrage opportunities...")
    
    opportunities = await arbitrage_detector.detect_opportunities()
    
    if not opportunities:
        print("❌ No arbitrage opportunities found")
        return
    
    print(f"✅ Found {len(opportunities)} arbitrage opportunities:")
    
    for opp in opportunities:
        print(f"\n💰 {opp.symbol}:")
        print(f"   Buy:  {opp.buy_exchange} @ {opp.buy_price:.4f}")
        print(f"   Sell: {opp.sell_exchange} @ {opp.sell_price:.4f}")
        print(f"   Spread: {opp.spread:.4f} ({opp.spread_percent:.2f}%)")
        print(f"   Confidence: {opp.calculate_confidence():.2f}")

async def continuous_monitoring(duration: int = 60):
    """Monitor for arbitrage opportunities continuously"""
    print(f"\n🔄 Starting continuous monitoring for {duration} seconds...")
    
    start_time = time.time()
    iteration = 0
    
    while time.time() - start_time < duration:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        try:
            opportunities = await arbitrage_detector.detect_opportunities()
            
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.spread_percent)
                print(f"🎯 Best opportunity: {best_opp.symbol} - {best_opp.spread_percent:.2f}% spread")
            else:
                print("😴 No opportunities found this iteration")
        
        except Exception as e:
            print(f"❌ Error in iteration {iteration}: {e}")
        
        # Wait before next iteration
        await asyncio.sleep(10)
    
    print(f"\n✅ Monitoring completed after {iteration} iterations")

async def main():
    """Main test function"""
    print("🚀 Starting live market data test...\n")
    
    try:
        # Test 1: Exchange connections
        connections = await test_exchange_connections()
        if not any(connections.values()):
            print("❌ No exchanges connected. Check your configuration.")
            return
        
        # Test 2: Live quotes
        await test_live_quotes()
        
        # Test 3: Arbitrage detection
        await test_arbitrage_detection()
        
        # Test 4: Ask user if they want continuous monitoring
        response = input("\n🤔 Run continuous monitoring for 60 seconds? (y/n): ")
        if response.lower() in ['y', 'yes']:
            await continuous_monitoring(60)
        
        print("\n🎉 All tests completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
