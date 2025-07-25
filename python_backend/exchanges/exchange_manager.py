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
    """Enhanced exchange manager with health monitoring"""
    
    def __init__(self):
        self.symbols = [
            'BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'LTC/USDT', 
            'ADA/USDT', 'DOT/USDT', 'LINK/USDT'
        ]

        
        self.exchanges: Dict[str, BaseExchange] = {
            'kraken': KrakenExchange(self.symbols),
            'kucoin': KuCoinExchange(self.symbols),
            'bitfinex': BitfinexExchange(self.symbols)
        }
        
        self.quotes_cache: Dict[str, Dict[str, Quote]] = {}
        self.last_update = 0
        self.health_check_interval = 60
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
        
        if time.time() - self.last_health_check > self.health_check_interval:
            await self.perform_health_checks()
        
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
        if (exchange in self.quotes_cache and 
            symbol in self.quotes_cache[exchange] and
            time.time() - self.last_update < 30):
            return self.quotes_cache[exchange][symbol]
        
        if exchange in self.exchanges and self.exchanges[exchange].status.connected:
            return await self.exchanges[exchange].fetch_ticker(symbol)
        
        return None

# Global instance
exchange_manager = ExchangeManager()
