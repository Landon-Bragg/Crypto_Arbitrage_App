import ccxt
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from decouple import config
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Quote:
    """Normalized quote format"""
    exchange: str
    symbol: str
    bid: float
    ask: float
    timestamp: float
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "timestamp": self.timestamp,
            "bid_volume": self.bid_volume,
            "ask_volume": self.ask_volume
        }

class ExchangeManager:
    """Manages connections to multiple exchanges and fetches live market data"""
    
    def __init__(self):
        self.exchanges = {}
        self.symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT']  # Using USDT for better liquidity
        self.quotes_cache = {}
        self.last_update = {}
        self.setup_exchanges()
    
    def setup_exchanges(self):
        """Initialize exchange connections - using public API only (no keys required)"""
        try:
            # Binance setup - no API keys needed for public data
            self.exchanges['binance'] = ccxt.binance({
                'enableRateLimit': True,
            })
            logger.info("✅ Binance exchange initialized")
            
            # Coinbase Pro setup - no API keys needed for public data
            self.exchanges['coinbasepro'] = ccxt.coinbasepro({
                'enableRateLimit': True,
            })
            logger.info("✅ Coinbase Pro exchange initialized")
            
            # Kraken setup - no API keys needed for public data
            self.exchanges['kraken'] = ccxt.kraken({
                'enableRateLimit': True,
            })
            logger.info("✅ Kraken exchange initialized")
            
        except Exception as e:
            logger.error(f"❌ Error setting up exchanges: {e}")
            raise
    
    async def fetch_ticker(self, exchange_name: str, symbol: str) -> Optional[Quote]:
        """Fetch ticker data from a specific exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            
            # Fetch ticker data
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, exchange.fetch_ticker, symbol
            )
            
            if not ticker or not ticker.get('bid') or not ticker.get('ask'):
                logger.warning(f"⚠️ Invalid ticker data from {exchange_name} for {symbol}")
                return None
            
            quote = Quote(
                exchange=exchange_name,
                symbol=symbol,
                bid=float(ticker['bid']),
                ask=float(ticker['ask']),
                timestamp=time.time(),
                bid_volume=ticker.get('bidVolume'),
                ask_volume=ticker.get('askVolume')
            )
            
            logger.debug(f"📊 {exchange_name} {symbol}: bid={quote.bid}, ask={quote.ask}")
            return quote
            
        except ccxt.NetworkError as e:
            logger.error(f"🌐 Network error fetching {symbol} from {exchange_name}: {e}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"💱 Exchange error fetching {symbol} from {exchange_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {symbol} from {exchange_name}: {e}")
            return None
    
    async def fetch_all_quotes(self) -> Dict[str, Dict[str, Quote]]:
        """Fetch quotes from all exchanges for all symbols"""
        all_quotes = {}
        
        tasks = []
        for exchange_name in self.exchanges.keys():
            for symbol in self.symbols:
                task = self.fetch_ticker(exchange_name, symbol)
                tasks.append((exchange_name, symbol, task))
        
        # Execute all requests concurrently
        results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
        
        # Process results
        for (exchange_name, symbol, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Error fetching {symbol} from {exchange_name}: {result}")
                continue
                
            if result is None:
                continue
                
            if exchange_name not in all_quotes:
                all_quotes[exchange_name] = {}
            
            all_quotes[exchange_name][symbol] = result
            
            # Update cache
            cache_key = f"{exchange_name}_{symbol}"
            self.quotes_cache[cache_key] = result
            self.last_update[cache_key] = time.time()
        
        return all_quotes
    
    async def get_cached_quote(self, exchange: str, symbol: str, max_age: float = 30.0) -> Optional[Quote]:
        """Get cached quote if it's fresh enough"""
        cache_key = f"{exchange}_{symbol}"
        
        if cache_key not in self.quotes_cache:
            return None
        
        last_update = self.last_update.get(cache_key, 0)
        if time.time() - last_update > max_age:
            return None
        
        return self.quotes_cache[cache_key]
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of supported exchange names"""
        return list(self.exchanges.keys())
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported symbols"""
        return self.symbols.copy()
    
    async def test_connections(self) -> Dict[str, bool]:
        """Test connections to all exchanges"""
        results = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                # Try to fetch markets to test connection
                await asyncio.get_event_loop().run_in_executor(
                    None, exchange.load_markets
                )
                results[exchange_name] = True
                logger.info(f"✅ {exchange_name} connection successful")
            except Exception as e:
                results[exchange_name] = False
                logger.error(f"❌ {exchange_name} connection failed: {e}")
        
        return results

# Global instance
exchange_manager = ExchangeManager()

async def get_live_quotes() -> Dict[str, Dict[str, Quote]]:
    """Get live quotes from all exchanges"""
    return await exchange_manager.fetch_all_quotes()

async def get_quote(exchange: str, symbol: str) -> Optional[Quote]:
    """Get a single quote from cache or fetch fresh"""
    # Try cache first
    cached = await exchange_manager.get_cached_quote(exchange, symbol)
    if cached:
        return cached
    
    # Fetch fresh data
    return await exchange_manager.fetch_ticker(exchange, symbol)
