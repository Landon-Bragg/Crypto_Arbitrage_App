import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from .base_exchange import BaseExchange, Quote, ExchangeStatus
from .kraken_exchange import KrakenExchange
from .kucoin_exchange import KuCoinExchange
from .bitfinex_exchange import BitfinexExchange

logger = logging.getLogger(__name__)

class ExchangeManager:
    """Enhanced exchange manager with health monitoring and failover"""
    
    def __init__(self):
        # Supported symbols - focusing on high-liquidity pairs
        self.symbols = [
            'BTC/USD', 'ETH/USD', 'XRP/USD', 'LTC/USD', 
            'ADA/USD', 'DOT/USD', 'LINK/USD', 'UNI/USD'
        ]
        
        # Initialize exchanges
        self.exchanges: Dict[str, BaseExchange] = {
            'kraken': KrakenExchange(self.symbols),
            'kucoin': KuCoinExchange(self.symbols),
            'bitfinex': BitfinexExchange(self.symbols)
        }
        
        self.quotes_cache: Dict[str, Dict[str, Quote]] = {}
        self.last_update = 0
        self.health_check_interval = 60  # Check health every minute
        self.last_health_check = 0
    
    async def initialize(self) -> Dict[str, bool]:
        """Initialize all exchanges"""
        results = {}
        
        for name, exchange in self.exchanges.items():
            try:
                success = await exchange.connect()
                results[name] = success
                logger.info(f"Exchange {name}: {'✅ Connected' if success else '❌ Failed'}")
            except Exception as e:
                logger.error(f"Failed to initialize {name}: {e}")
                results[name] = False
        
        return results
    
    async def fetch_all_quotes(self) -> Dict[str, Dict[str, Quote]]:
        """Fetch quotes from all connected exchanges"""
        all_quotes = {}
        
        # Perform health checks if needed
        if time.time() - self.last_health_check > self.health_check_interval:
            await self.perform_health_checks()
        
        # Fetch from all exchanges concurrently
        tasks = []
        for name, exchange in self.exchanges.items():
            if exchange.status.connected:
                task = exchange.fetch_all_tickers()
                tasks.append((name, task))
        
        if not tasks:
            logger.warning("No exchanges available for fetching quotes")
            return all_quotes
        
        try:
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching from {name}: {result}")
                    self.exchanges[name].status.error_count += 1
                elif result:
                    all_quotes[name] = result
            
            # Update cache
            self.quotes_cache = all_quotes
            self.last_update = time.time()
            
            logger.info(f"✅ Fetched quotes from {len(all_quotes)} exchanges")
            
        except Exception as e:
            logger.error(f"Error in fetch_all_quotes: {e}")
        
        return all_quotes
    
    async def perform_health_checks(self):
        """Perform health checks on all exchanges"""
        logger.info("🔍 Performing health checks...")
        
        tasks = []
        for name, exchange in self.exchanges.items():
            task = exchange.health_check()
            tasks.append((name, task))
        
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for (name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {name}: {result}")
                self.exchanges[name].status.connected = False
            else:
                status = "✅ Healthy" if result else "❌ Unhealthy"
                health_score = self.exchanges[name].status.calculate_health_score()
                logger.info(f"{name}: {status} (Score: {health_score:.2f})")
        
        self.last_health_check = time.time()
    
    def get_exchange_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all exchanges"""
        return {
            name: exchange.status.to_dict() 
            for name, exchange in self.exchanges.items()
        }
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.symbols.copy()
    
    def get_connected_exchanges(self) -> List[str]:
        """Get list of currently connected exchanges"""
        return [
            name for name, exchange in self.exchanges.items() 
            if exchange.status.connected
        ]
    
    async def get_quote(self, exchange: str, symbol: str) -> Optional[Quote]:
        """Get a specific quote from cache or fetch fresh"""
        # Try cache first
        if (exchange in self.quotes_cache and 
            symbol in self.quotes_cache[exchange] and
            time.time() - self.last_update < 30):  # 30 second cache
            return self.quotes_cache[exchange][symbol]
        
        # Fetch fresh if exchange is available
        if exchange in self.exchanges and self.exchanges[exchange].status.connected:
            return await self.exchanges[exchange].fetch_ticker(symbol)
        
        return None
    
    def get_market_summary(self) -> Dict[str, Any]:
        """Get market summary statistics"""
        if not self.quotes_cache:
            return {}
        
        summary = {
            "total_symbols": len(self.symbols),
            "connected_exchanges": len([e for e in self.exchanges.values() if e.status.connected]),
            "total_exchanges": len(self.exchanges),
            "last_update": self.last_update,
            "symbols": {}
        }
        
        # Calculate statistics for each symbol
        for symbol in self.symbols:
            symbol_data = {
                "prices": {},
                "spreads": {},
                "volumes": {},
                "min_price": float('inf'),
                "max_price": 0,
                "avg_price": 0,
                "price_variance": 0
            }
            
            prices = []
            for exchange_name, quotes in self.quotes_cache.items():
                if symbol in quotes:
                    quote = quotes[symbol]
                    mid_price = (quote.bid + quote.ask) / 2
                    
                    symbol_data["prices"][exchange_name] = {
                        "bid": quote.bid,
                        "ask": quote.ask,
                        "mid": mid_price,
                        "last": quote.last_price
                    }
                    
                    symbol_data["spreads"][exchange_name] = {
                        "absolute": quote.ask - quote.bid,
                        "percent": ((quote.ask - quote.bid) / quote.bid) * 100
                    }
                    
                    if quote.bid_volume and quote.ask_volume:
                        symbol_data["volumes"][exchange_name] = {
                            "bid": quote.bid_volume,
                            "ask": quote.ask_volume
                        }
                    
                    prices.append(mid_price)
                    symbol_data["min_price"] = min(symbol_data["min_price"], mid_price)
                    symbol_data["max_price"] = max(symbol_data["max_price"], mid_price)
            
            if prices:
                symbol_data["avg_price"] = sum(prices) / len(prices)
                if len(prices) > 1:
                    variance = sum((p - symbol_data["avg_price"]) ** 2 for p in prices) / len(prices)
                    symbol_data["price_variance"] = variance ** 0.5
            
            summary["symbols"][symbol] = symbol_data
        
        return summary

# Global instance
exchange_manager = ExchangeManager()
