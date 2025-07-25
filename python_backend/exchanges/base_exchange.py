from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class Quote:
    """Normalized quote format across all exchanges"""
    exchange: str
    symbol: str
    bid: float
    ask: float
    timestamp: float
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    last_price: Optional[float] = None
    daily_change: Optional[float] = None
    daily_change_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "timestamp": self.timestamp,
            "bid_volume": self.bid_volume,
            "ask_volume": self.ask_volume,
            "last_price": self.last_price,
            "daily_change": self.daily_change,
            "daily_change_percent": self.daily_change_percent,
            "spread": self.ask - self.bid,
            "spread_percent": ((self.ask - self.bid) / self.bid) * 100 if self.bid > 0 else 0
        }

@dataclass
class ExchangeStatus:
    """Exchange connection and health status"""
    name: str
    connected: bool
    last_update: float
    error_count: int
    avg_response_time: float
    supported_symbols: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "connected": self.connected,
            "last_update": self.last_update,
            "error_count": self.error_count,
            "avg_response_time": self.avg_response_time,
            "supported_symbols": self.supported_symbols,
            "health_score": self.calculate_health_score()
        }
    
    def calculate_health_score(self) -> float:
        """Calculate health score from 0-1 based on connection status and performance"""
        if not self.connected:
            return 0.0
        
        score = 0.5
        error_penalty = min(self.error_count * 0.05, 0.3)
        score -= error_penalty
        
        if self.avg_response_time < 1.0:
            response_bonus = min((1.0 - self.avg_response_time) * 0.2, 0.2)
            score += response_bonus
        elif self.avg_response_time > 3.0:
            response_penalty = min((self.avg_response_time - 3.0) * 0.1, 0.3)
            score -= response_penalty
        
        return max(0.0, min(1.0, score))

class BaseExchange(ABC):
    """Abstract base class for all exchange implementations"""
    
    def __init__(self, name: str, symbols: List[str]):
        self.name = name
        self.symbols = symbols
        self.status = ExchangeStatus(
            name=name,
            connected=False,
            last_update=0,
            error_count=0,
            avg_response_time=0,
            supported_symbols=symbols
        )
        self.response_times = []
        self.max_response_times = 10
    
    @abstractmethod
    async def connect(self) -> bool:
        """Initialize connection to the exchange"""
        pass
    
    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> Optional[Quote]:
        """Fetch ticker data for a specific symbol"""
        pass
    
    @abstractmethod
    def normalize_symbol(self, symbol: str) -> str:
        """Convert standard symbol format to exchange-specific format"""
        pass
    
    async def fetch_all_tickers(self) -> Dict[str, Quote]:
        """Fetch all supported tickers"""
        results = {}
        tasks = []
        
        for symbol in self.symbols:
            task = self.fetch_ticker(symbol)
            tasks.append((symbol, task))
        
        try:
            responses = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (symbol, _), response in zip(tasks, responses):
                if isinstance(response, Exception):
                    logger.error(f"Error fetching {symbol} from {self.name}: {response}")
                    self.status.error_count += 1
                elif response is not None:
                    results[symbol] = response
            
            self.status.last_update = time.time()
            
        except Exception as e:
            logger.error(f"Error fetching all tickers from {self.name}: {e}")
            self.status.error_count += 1
        
        return results
    
    def update_response_time(self, response_time: float):
        """Update average response time tracking"""
        self.response_times.append(response_time)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)
        
        self.status.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    async def health_check(self) -> bool:
        """Perform health check on the exchange"""
        try:
            start_time = time.time()
            test_symbol = self.symbols[0] if self.symbols else "BTC/USD"
            result = await self.fetch_ticker(test_symbol)
            response_time = time.time() - start_time
            
            self.update_response_time(response_time)
            self.status.connected = result is not None
            
            return self.status.connected
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            self.status.connected = False
            self.status.error_count += 1
            return False
