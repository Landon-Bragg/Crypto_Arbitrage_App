#!/usr/bin/env python3
"""
Test script for the focused 3-exchange arbitrage system
"""
import asyncio
import json
import time
from exchanges import exchange_manager
from arbitrage.detector import arbitrage_detector

async def test_exchange_connections():
    """Test connections to our three focused exchanges"""
    print("🔌 Testing connections to our three focused exchanges...")
    results = await exchange_manager.test_connections()
    
    exchange_info = {
        'kraken': '🇺🇸 Kraken - US-based, highly reliable',
        'kucoin': '🌍 KuCoin - International, good liquidity',
        'bitfinex': '🌍 Bitfinex - Excellent for arbitrage'
    }
    
    for exchange, status in results.items():
        status_icon = "✅" if status else "❌"
        info = exchange_info.get(exchange, exchange)
        print(f"{status_icon} {info}: {'Connected' if status else 'Failed'}")
    
    connected_count = sum(results.values())
    print(f"\n📊 {connected_count}/3 exchanges connected")
    
    if connected_count >= 2:
        print("✅ Sufficient exchanges for arbitrage detection!")
    else:
        print("⚠️ Need at least 2 exchanges for arbitrage detection")
    
    return results

async def test_live_quotes():
    """Test fetching live quotes"""
    print("\n📊 Fetching live market data...")
    
    quotes = await exchange_manager.fetch_all_quotes()
    
    if not quotes:
        print("❌ No quotes received")
        return
    
    print(f"✅ Received quotes from {len(quotes)} exchanges")
    
    # Display quotes in a nice table format
    symbols = exchange_manager.get_supported_symbols()
    
    for symbol in symbols:
        print(f"\n💰 {symbol}:")
        print("   Exchange    |    Bid     |    Ask     |  Spread  ")
        print("   ------------|------------|------------|----------")
        
        for exchange, exchange_quotes in quotes.items():
            if symbol in exchange_quotes:
                quote = exchange_quotes[symbol]
                spread_pct = ((quote.ask - quote.bid) / quote.bid * 100)
                print(f"   {exchange:<11} | ${quote.bid:>8.4f} | ${quote.ask:>8.4f} | {spread_pct:>6.3f}%")

async def test_arbitrage_detection():
    """Test arbitrage detection with detailed analysis"""
    print("\n🔍 Detecting arbitrage opportunities...")
    
    opportunities = await arbitrage_detector.detect_opportunities()
    
    if not opportunities:
        print("❌ No arbitrage opportunities found above 0.05% threshold")
        print("💡 This is normal - real arbitrage opportunities are rare!")
        print("💡 Try lowering the threshold or check during high volatility periods")
        return
    
    print(f"✅ Found {len(opportunities)} arbitrage opportunities:")
    
    for i, opp in enumerate(opportunities, 1):
        print(f"\n🏆 Opportunity #{i}: {opp.symbol}")
        print(f"   📈 Buy:  {opp.buy_exchange:<10} @ ${opp.buy_price:>8.4f}")
        print(f"   📉 Sell: {opp.sell_exchange:<10} @ ${opp.sell_price:>8.4f}")
        print(f"   💰 Spread: ${opp.spread:>6.4f} ({opp.spread_percent:>5.3f}%)")
        print(f"   🎯 Confidence: {opp.calculate_confidence():>4.2f}")
        print(f"   💵 Profit Potential: ${opp.calculate_profit_potential():>6.2f}")
        
        if opp.buy_volume and opp.sell_volume:
            min_vol = min(opp.buy_volume, opp.sell_volume)
            print(f"   📊 Available Volume: {min_vol:>6.2f}")

async def continuous_monitoring(duration: int = 120):
    """Monitor for arbitrage opportunities continuously"""
    print(f"\n🔄 Starting continuous monitoring for {duration} seconds...")
    print("💡 Checking every 20 seconds for new opportunities...")
    
    start_time = time.time()
    iteration = 0
    total_opportunities = 0
    best_spread_seen = 0.0
    
    while time.time() - start_time < duration:
        iteration += 1
        elapsed = time.time() - start_time
        print(f"\n--- Iteration {iteration} ({elapsed:.0f}s elapsed) ---")
        
        try:
            detection_start = time.time()
            opportunities = await arbitrage_detector.detect_opportunities()
            detection_time = time.time() - detection_start
            
            if opportunities:
                total_opportunities += len(opportunities)
                best_opp = max(opportunities, key=lambda x: x.spread_percent)
                best_spread_seen = max(best_spread_seen, best_opp.spread_percent)
                
                print(f"🎯 Found {len(opportunities)} opportunities in {detection_time:.2f}s")
                print(f"🏆 Best: {best_opp.symbol} - {best_opp.spread_percent:.3f}% spread")
                print(f"   {best_opp.buy_exchange} → {best_opp.sell_exchange}")
                print(f"   Profit potential: ${best_opp.calculate_profit_potential():.2f}")
            else:
                print(f"😴 No opportunities found in {detection_time:.2f}s")
        
        except Exception as e:
            print(f"❌ Error in iteration {iteration}: {e}")
        
        # Wait before next iteration
        await asyncio.sleep(20)
    
    print(f"\n✅ Monitoring completed after {iteration} iterations")
    print(f"📊 Statistics:")
    print(f"   Total opportunities found: {total_opportunities}")
    print(f"   Best spread seen: {best_spread_seen:.3f}%")
    print(f"   Average opportunities per check: {total_opportunities/iteration:.1f}")

async def main():
    """Main test function"""
    print("🚀 Testing Focused 3-Exchange Arbitrage System\n")
    print("🎯 Exchanges: Kraken, KuCoin, Bitfinex")
    print("💰 Symbols: BTC/USD, ETH/USD, XRP/USD, LTC/USD")
    print("📊 Minimum spread threshold: 0.05%")
    
    try:
        # Test 1: Exchange connections
        connections = await test_exchange_connections()
        connected_count = sum(connections.values())
        
        if connected_count == 0:
            print("❌ No exchanges connected. Check your internet connection.")
            return
        elif connected_count < 2:
            print("⚠️ Need at least 2 exchanges for arbitrage detection.")
            return
        
        # Test 2: Live quotes
        await test_live_quotes()
        
        # Test 3: Arbitrage detection
        await test_arbitrage_detection()
        
        # Test 4: Ask user if they want continuous monitoring
        response = input("\n🤔 Run continuous monitoring for 2 minutes? (y/n): ")
        if response.lower() in ['y', 'yes']:
            await continuous_monitoring(120)
        
        print("\n🎉 All tests completed successfully!")
        print("\n💡 Tips for better arbitrage detection:")
        print("   • Run during high volatility periods")
        print("   • Monitor multiple timeframes")
        print("   • Consider transaction fees in your calculations")
        print("   • Act quickly - opportunities disappear fast!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
