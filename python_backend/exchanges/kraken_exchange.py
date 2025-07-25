import ccxt
import asyncio
import time
import logging
from typing import Optional, List
from .base_exchange import BaseExchange, Quote

logger = logging.getLogger(__name__)

class KrakenExchange(BaseExchange):
    """Enhanced Kraken exchange implementation"""
    
    def __init__(self, symbols: List[str]):
        super().__init__("kraken", symbols)
        self.exchange = None
        self.symbol_mapping = {
            'BTC/USD': 'XBTUSD',
            'ETH/USD': 'ETHUSD', 
            'XRP/USD': 'XRPUSD',
            'LTC/USD': 'LTCUSD',
            'ADA/USD': 'ADAUSD',
            'DOT/USD': 'DOTUSD',
            'LINK/USD': 'LINKUSD',
            'UNI/USD': 'UNIUSD'
        }
    
    async def connect(self) -> bool:
        """Initialize connection to Kraken"""
        try:
            self.exchange = ccxt.kraken({
                'enableRateLimit': True,
                'timeout': 15000,
                'rateLimit': 3000,
                'options': {
                    'adjustForTimeDifference': True,
                }
            })
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.exchange.load_markets
            )
            
            self.status.connected = True
            logger.info(f"✅ {self.name} connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.name}: {e}")
            self.status.connected = False
            self.status.error_count += 1
            return False
    
    def normalize_symbol(self, symbol: str) -> str:
        """Convert standard symbol to Kraken format"""
        return self.symbol_mapping.get(symbol, symbol)
    
    async def fetch_ticker(self, symbol: str) -> Optional[Quote]:
        """Fetch ticker data from Kraken"""
        if not self.exchange or not self.status.connected:
            return None
        
        try:
            start_time = time.time()
            kraken_symbol = self.normalize_symbol(symbol)
            
            max_retries = 3
            ticker = None
            
            for attempt in range(max_retries):
                try:
                    ticker = await asyncio.get_event_loop().run_in_executor(
                        None, self.exchange.fetch_ticker, kraken_symbol
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    await asyncio.sleep(1)
            
            response_time = time.time() - start_time
            self.update_response_time(response_time)
            
            if not ticker or not ticker.get('bid') or not ticker.get('ask'):
                logger.warning(f"⚠️ Invalid ticker data from {self.name} for {symbol}")
                return None
            
            if ticker['bid'] >= ticker['ask']:
                logger.warning(f"⚠️ Invalid spread from {self.name} for {symbol}")
                return None
            
            quote = Quote(
                exchange=self.name,
                symbol=symbol,
                bid=float(ticker['bid']),
                ask=float(ticker['ask']),
                timestamp=time.time(),
                bid_volume=ticker.get('bidVolume'),
                ask_volume=ticker.get('askVolume'),
                last_price=ticker.get('last'),
                daily_change=ticker.get('change'),
                daily_change_percent=ticker.get('percentage')
            )
            
            logger.debug(f"📊 {self.name} {symbol}: ${quote.bid:.4f}/${quote.ask:.4f}")
            return quote
            
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol} from {self.name}: {e}")
            self.status.error_count += 1
            return None
