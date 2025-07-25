import ccxt
import asyncio
import time
import logging
from typing import Optional
from .base_exchange import BaseExchange, Quote

logger = logging.getLogger(__name__)

class BitfinexExchange(BaseExchange):
    """Bitfinex exchange implementation"""
    
    def __init__(self, symbols):
        super().__init__("bitfinex", symbols)
        self.exchange = None
        self.symbol_mapping = {
            'BTC/USD': 'tBTCUSD',
            'ETH/USD': 'tETHUSD',
            'XRP/USD': 'tXRPUSD',
            'LTC/USD': 'tLTCUSD',
            'ADA/USD': 'tADAUSD',
            'DOT/USD': 'tDOTUSD',
            'LINK/USD': 'tLINKUSD',
            'UNI/USD': 'tUNIUSD'
        }
    
    async def connect(self) -> bool:
        try:
            self.exchange = ccxt.bitfinex({
                'enableRateLimit': True,
                'timeout': 15000,
                'rateLimit': 1500,
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
        return self.symbol_mapping.get(symbol, symbol)
    
    async def fetch_ticker(self, symbol: str) -> Optional[Quote]:
        if not self.exchange or not self.status.connected:
            return None
        
        try:
            start_time = time.time()
            bitfinex_symbol = self.normalize_symbol(symbol)
            
            ticker = await asyncio.get_event_loop().run_in_executor(
                None, self.exchange.fetch_ticker, bitfinex_symbol
            )
            
            response_time = time.time() - start_time
            self.update_response_time(response_time)
            
            if not ticker or not ticker.get('bid') or not ticker.get('ask'):
                return None
            
            if ticker['bid'] >= ticker['ask']:
                return None
            
            return Quote(
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
            
        except Exception as e:
            logger.error(f"❌ Error fetching {symbol} from {self.name}: {e}")
            self.status.error_count += 1
            return None
