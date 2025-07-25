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
        # Focus on symbols with good liquidity across all three exchanges
        self.symbols = ['BTC/USD', 'ETH/USD', 'XRP/USD', 'LTC/USD']
        self.quotes_cache = {}
        self.last_update = {}
        self.setup_exchanges()
    
    def setup_exchanges(self):
        """Initialize exchange connections - using public API only (no keys required)"""
        try:
            # Kraken - reliable, US-based
            self.exchanges['kraken'] = ccxt.kraken({
                'enableRateLimit': True,
                'timeout': 15000,  # 15 second timeout
                'rateLimit': 3000,  # 3 seconds between requests
            })
            logger.info("✅ Kraken exchange initialized")
            
            # KuCoin - good liquidity, works in Texas
            self.exchanges['kucoin'] = ccxt.kucoin({
                'enableRateLimit': True,
                'timeout': 15000,
                'rateLimit': 1000,  # 1 second between requests
            })
            logger.info("✅ KuCoin exchange initialized")
            
            # Bitfinex - excellent for arbitrage opportunities
            self.exchanges['bitfinex'] = ccxt.bitfinex({
                'enableRateLimit': True,
                'timeout': 15000,
                'rateLimit': 1500,  # 1.5 seconds between requests
            })
            logger.info("✅ Bitfinex exchange initialized")
            
        except Exception as e:
            logger.error(f"❌ Error setting up exchanges: {e}")
            raise
    
    def normalize_symbol(self, symbol: str, exchange_name: str) -> str:
        """Normalize symbol format for different exchanges"""
        if exchange_name == 'kraken':
            # Kraken uses XBT instead of BTC and different format
            normalized = symbol.replace('BTC', 'XBT')
            # Kraken sometimes uses different USD notation
            if 'USD' in normalized:
                return normalized
        elif exchange_name == 'bitfinex':
            # Bitfinex uses tXXXUSD format for trading symbols
            base, quote = symbol.split('/')
            if base == 'BTC':
                base = 'BTC'  # Bitfinex uses BTC, not XBT
            return f"t{base}{quote}"
        elif exchange_name == 'kucoin':
            # KuCoin uses standard format
            return symbol
        
        return symbol
    
    async def fetch_ticker(self, exchange_name: str, symbol: str) -> Optional[Quote]:
        """Fetch ticker data from a specific exchange"""
        try:
            exchange = self.exchanges[exchange_name]
            normalized_symbol = self.normalize_symbol(symbol, exchange_name)
            
            # Add retry logic for better reliability
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Fetch ticker data
                    ticker = await asyncio.get_event_loop().run_in_executor(
                        None, exchange.fetch_ticker, normalized_symbol
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(1)  # Wait 1 second before retry
            
            if not ticker or not ticker.get('bid') or not ticker.get('ask'):
                logger.warning(f"⚠️ Invalid ticker data from {exchange_name} for {symbol}")
                return None
            
            # Validate that bid < ask (sanity check)
            if ticker['bid'] >= ticker['ask']:
                logger.warning(f"⚠️ Invalid spread from {exchange_name} for {symbol}: bid={ticker['bid']}, ask={ticker['ask']}")
                return None
            
            quote = Quote(
                exchange=exchange_name,
                symbol=symbol,  # Use original symbol format
                bid=float(ticker['bid']),
                ask=float(ticker['ask']),
                timestamp=time.time(),
                bid_volume=ticker.get('bidVolume'),
                ask_volume=ticker.get('askVolume')
            )
            
            logger.debug(f"📊 {exchange_name} {symbol}: bid=${quote.bid:.4f}, ask=${quote.ask:.4f}")
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
        
        # Create tasks for all exchange-symbol combinations
        tasks = []
        for exchange_name in self.exchanges.keys():
            for symbol in self.symbols:
                task = self.fetch_ticker(exchange_name, symbol)
                tasks.append((exchange_name, symbol, task))
        
        # Execute all requests concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True),
                timeout=30.0  # 30 second total timeout
            )
        except asyncio.TimeoutError:
            logger.error("❌ Timeout fetching quotes from exchanges")
            return all_quotes
        
        # Process results
        successful_fetches = 0
        for (exchange_name, symbol, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"❌ Error fetching {symbol} from {exchange_name}: {result}")
                continue
                
            if result is None:
                continue
                
            if exchange_name not in all_quotes:
                all_quotes[exchange_name] = {}
            
            all_quotes[exchange_name][symbol] = result
            successful_fetches += 1
            
            # Update cache
            cache_key = f"{exchange_name}_{symbol}"
            self.quotes_cache[cache_key] = result
            self.last_update[cache_key] = time.time()
        
        logger.info(f"✅ Successfully fetched {successful_fetches} quotes from {len(all_quotes)} exchanges")
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
