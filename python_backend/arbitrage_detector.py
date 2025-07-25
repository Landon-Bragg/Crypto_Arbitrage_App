import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from exchanges import exchange_manager, Quote

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread: float
    spread_percent: float
    timestamp: float
    buy_volume: Optional[float] = None
    sell_volume: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": f"{self.symbol}_{self.buy_exchange}_{self.sell_exchange}",
            "symbol": self.symbol,
            "buyExchange": self.buy_exchange,
            "sellExchange": self.sell_exchange,
            "buyPrice": self.buy_price,
            "sellPrice": self.sell_price,
            "spread": self.spread,
            "spreadPercent": self.spread_percent,
            "timestamp": self.timestamp,
            "buyVolume": self.buy_volume,
            "sellVolume": self.sell_volume,
            "confidence": self.calculate_confidence()
        }
    
    def calculate_confidence(self) -> float:
        """Calculate confidence score based on spread and volume"""
        base_confidence = 0.5
        
        # Higher spread = higher confidence (up to a point)
        spread_factor = min(self.spread_percent / 2.0, 0.3)
        
        # Higher volume = higher confidence
        volume_factor = 0.0
        if self.buy_volume and self.sell_volume:
            min_volume = min(self.buy_volume, self.sell_volume)
            volume_factor = min(min_volume / 10.0, 0.2)  # Max 0.2 boost for volume
        
        return min(base_confidence + spread_factor + volume_factor, 1.0)

class ArbitrageDetector:
    """Detects arbitrage opportunities across exchanges"""
    
    def __init__(self, min_spread_percent: float = 0.1):
        self.min_spread_percent = min_spread_percent
        self.opportunities = {}
        self.last_quotes = {}
    
    async def detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities from current market data"""
        opportunities = []
        
        try:
            # Fetch all quotes
            all_quotes = await exchange_manager.fetch_all_quotes()
            self.last_quotes = all_quotes
            
            # Check each symbol
            for symbol in exchange_manager.get_supported_symbols():
                symbol_opportunities = self._find_arbitrage_for_symbol(symbol, all_quotes)
                opportunities.extend(symbol_opportunities)
            
            # Update opportunities cache
            self.opportunities = {opp.symbol + "_" + opp.buy_exchange + "_" + opp.sell_exchange: opp 
                               for opp in opportunities}
            
            logger.info(f"🔍 Found {len(opportunities)} arbitrage opportunities")
            
        except Exception as e:
            logger.error(f"❌ Error detecting opportunities: {e}")
        
        return opportunities
    
    def _find_arbitrage_for_symbol(self, symbol: str, all_quotes: Dict) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities for a specific symbol"""
        opportunities = []
        exchanges_with_data = []
        
        # Collect exchanges that have data for this symbol
        for exchange_name, quotes in all_quotes.items():
            if symbol in quotes:
                exchanges_with_data.append((exchange_name, quotes[symbol]))
        
        if len(exchanges_with_data) < 2:
            return opportunities
        
        # Compare all pairs of exchanges
        for i, (buy_exchange, buy_quote) in enumerate(exchanges_with_data):
            for j, (sell_exchange, sell_quote) in enumerate(exchanges_with_data):
                if i >= j:  # Avoid duplicate comparisons
                    continue
                
                # Check both directions
                opportunities.extend(self._check_arbitrage_pair(
                    symbol, buy_exchange, buy_quote, sell_exchange, sell_quote
                ))
                opportunities.extend(self._check_arbitrage_pair(
                    symbol, sell_exchange, sell_quote, buy_exchange, buy_quote
                ))
        
        return opportunities
    
    def _check_arbitrage_pair(self, symbol: str, buy_exchange: str, buy_quote: Quote, 
                            sell_exchange: str, sell_quote: Quote) -> List[ArbitrageOpportunity]:
        """Check for arbitrage between two specific exchanges"""
        opportunities = []
        
        try:
            buy_price = buy_quote.ask  # We buy at the ask price
            sell_price = sell_quote.bid  # We sell at the bid price
            
            if buy_price <= 0 or sell_price <= 0:
                return opportunities
            
            spread = sell_price - buy_price
            spread_percent = (spread / buy_price) * 100
            
            if spread_percent >= self.min_spread_percent:
                opportunity = ArbitrageOpportunity(
                    symbol=symbol,
                    buy_exchange=buy_exchange,
                    sell_exchange=sell_exchange,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    spread=spread,
                    spread_percent=spread_percent,
                    timestamp=time.time(),
                    buy_volume=buy_quote.ask_volume,
                    sell_volume=sell_quote.bid_volume
                )
                opportunities.append(opportunity)
                
                logger.info(f"💰 Arbitrage found: {symbol} - Buy {buy_exchange} @ {buy_price:.4f}, "
                          f"Sell {sell_exchange} @ {sell_price:.4f}, Spread: {spread_percent:.2f}%")
        
        except Exception as e:
            logger.error(f"❌ Error checking arbitrage pair: {e}")
        
        return opportunities
    
    def get_current_opportunities(self) -> List[Dict]:
        """Get current opportunities as dictionaries"""
        return [opp.to_dict() for opp in self.opportunities.values()]
    
    def get_last_quotes(self) -> Dict:
        """Get the last fetched quotes"""
        result = {}
        for exchange, quotes in self.last_quotes.items():
            result[exchange] = {}
            for symbol, quote in quotes.items():
                result[exchange][symbol] = quote.to_dict()
        return result

# Global detector instance
arbitrage_detector = ArbitrageDetector(min_spread_percent=0.1)  # 0.1% minimum spread
