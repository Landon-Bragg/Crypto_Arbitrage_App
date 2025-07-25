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
            "id": f"{self.symbol}_{self.buy_exchange}_{self.sell_exchange}_{int(self.timestamp)}",
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
            "confidence": self.calculate_confidence(),
            "profitPotential": self.calculate_profit_potential()
        }
    
    def calculate_confidence(self) -> float:
        """Calculate confidence score based on spread, volume, and exchange reliability"""
        base_confidence = 0.5
        
        # Higher spread = higher confidence (up to a point)
        spread_factor = min(self.spread_percent / 2.0, 0.3)
        
        # Higher volume = higher confidence
        volume_factor = 0.0
        if self.buy_volume and self.sell_volume:
            min_volume = min(self.buy_volume, self.sell_volume)
            # Scale volume factor based on asset type
            if 'BTC' in self.symbol:
                volume_factor = min(min_volume / 5.0, 0.2)  # BTC has lower volume
            else:
                volume_factor = min(min_volume / 50.0, 0.2)  # Other assets have higher volume
        
        # Exchange reliability factor
        reliability_factor = 0.0
        reliable_exchanges = {'kraken', 'kucoin', 'bitfinex'}
        if self.buy_exchange in reliable_exchanges and self.sell_exchange in reliable_exchanges:
            reliability_factor = 0.1
        
        return min(base_confidence + spread_factor + volume_factor + reliability_factor, 1.0)
    
    def calculate_profit_potential(self) -> float:
        """Calculate potential profit in USD"""
        if not self.buy_volume or not self.sell_volume:
            return 0.0
        
        # Use the minimum volume available
        tradeable_volume = min(self.buy_volume, self.sell_volume)
        
        # Limit to reasonable trading amounts
        if 'BTC' in self.symbol:
            tradeable_volume = min(tradeable_volume, 1.0)  # Max 1 BTC
        elif 'ETH' in self.symbol:
            tradeable_volume = min(tradeable_volume, 10.0)  # Max 10 ETH
        else:
            tradeable_volume = min(tradeable_volume, 1000.0)  # Max 1000 for other assets
        
        return self.spread * tradeable_volume

class ArbitrageDetector:
    """Detects arbitrage opportunities across exchanges"""
    
    def __init__(self, min_spread_percent: float = 0.05):  # Lowered threshold to 0.05%
        self.min_spread_percent = min_spread_percent
        self.opportunities = {}
        self.last_quotes = {}
        self.exchange_pairs = [
            ('kraken', 'kucoin'),
            ('kraken', 'bitfinex'),
            ('kucoin', 'bitfinex')
        ]
    
    async def detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities from current market data"""
        opportunities = []
        
        try:
            # Fetch all quotes
            all_quotes = await exchange_manager.fetch_all_quotes()
            self.last_quotes = all_quotes
            
            if not all_quotes:
                logger.warning("⚠️ No quotes received from any exchange")
                return opportunities
            
            # Check each symbol across exchange pairs
            for symbol in exchange_manager.get_supported_symbols():
                symbol_opportunities = self._find_arbitrage_for_symbol(symbol, all_quotes)
                opportunities.extend(symbol_opportunities)
            
            # Sort opportunities by spread percentage (best first)
            opportunities.sort(key=lambda x: x.spread_percent, reverse=True)
            
            # Update opportunities cache
            self.opportunities = {
                f"{opp.symbol}_{opp.buy_exchange}_{opp.sell_exchange}": opp 
                for opp in opportunities
            }
            
            if opportunities:
                logger.info(f"🔍 Found {len(opportunities)} arbitrage opportunities")
                for opp in opportunities[:3]:  # Log top 3
                    logger.info(f"💰 {opp.symbol}: {opp.spread_percent:.3f}% spread "
                              f"({opp.buy_exchange} → {opp.sell_exchange})")
            else:
                logger.info("😴 No arbitrage opportunities found above threshold")
            
        except Exception as e:
            logger.error(f"❌ Error detecting opportunities: {e}")
        
        return opportunities
    
    def _find_arbitrage_for_symbol(self, symbol: str, all_quotes: Dict) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities for a specific symbol"""
        opportunities = []
        
        # Get quotes for this symbol from all exchanges
        symbol_quotes = {}
        for exchange_name, quotes in all_quotes.items():
            if symbol in quotes:
                symbol_quotes[exchange_name] = quotes[symbol]
        
        if len(symbol_quotes) < 2:
            return opportunities
        
        # Check all exchange pairs
        for buy_exchange, sell_exchange in self.exchange_pairs:
            if buy_exchange in symbol_quotes and sell_exchange in symbol_quotes:
                # Check both directions
                opportunities.extend(self._check_arbitrage_pair(
                    symbol, buy_exchange, symbol_quotes[buy_exchange], 
                    sell_exchange, symbol_quotes[sell_exchange]
                ))
                opportunities.extend(self._check_arbitrage_pair(
                    symbol, sell_exchange, symbol_quotes[sell_exchange],
                    buy_exchange, symbol_quotes[buy_exchange]
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
            
            # Only consider positive spreads above our threshold
            if spread > 0 and spread_percent >= self.min_spread_percent:
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
                
                logger.debug(f"💰 Arbitrage found: {symbol} - Buy {buy_exchange} @ ${buy_price:.4f}, "
                           f"Sell {sell_exchange} @ ${sell_price:.4f}, Spread: {spread_percent:.3f}%")
        
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
    
    def get_statistics(self) -> Dict:
        """Get statistics about current opportunities"""
        opportunities = list(self.opportunities.values())
        if not opportunities:
            return {
                "total_opportunities": 0,
                "average_spread": 0.0,
                "best_spread": 0.0,
                "total_profit_potential": 0.0
            }
        
        spreads = [opp.spread_percent for opp in opportunities]
        profits = [opp.calculate_profit_potential() for opp in opportunities]
        
        return {
            "total_opportunities": len(opportunities),
            "average_spread": sum(spreads) / len(spreads),
            "best_spread": max(spreads),
            "total_profit_potential": sum(profits)
        }

# Global detector instance with lower threshold for more opportunities
arbitrage_detector = ArbitrageDetector(min_spread_percent=0.05)  # 0.05% minimum spread
