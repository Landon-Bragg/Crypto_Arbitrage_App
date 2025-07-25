import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import statistics
from exchanges.base_exchange import Quote
from exchanges.exchange_manager import exchange_manager

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Enhanced arbitrage opportunity with analytics"""
    id: str
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
    confidence_score: float = 0.0
    profit_potential: float = 0.0
    execution_time_estimate: float = 0.0
    risk_level: str = "medium"
    historical_frequency: float = 0.0
    
    def __post_init__(self):
        self.confidence_score = self._calculate_confidence()
        self.profit_potential = self._calculate_profit_potential()
        self.execution_time_estimate = self._estimate_execution_time()
        self.risk_level = self._assess_risk_level()
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence score (0-1) based on multiple factors"""
        base_confidence = 0.4
        
        spread_factor = min(self.spread_percent / 3.0, 0.25)
        
        volume_factor = 0.0
        if self.buy_volume and self.sell_volume:
            min_volume = min(self.buy_volume, self.sell_volume)
            if 'BTC' in self.symbol:
                volume_factor = min(min_volume / 2.0, 0.15)
            elif 'ETH' in self.symbol:
                volume_factor = min(min_volume / 10.0, 0.15)
            else:
                volume_factor = min(min_volume / 100.0, 0.15)
        
        reliable_exchanges = {'kraken'}
        good_exchanges = {'kucoin', 'bitfinex'}
        
        reliability_factor = 0.0
        if self.buy_exchange in reliable_exchanges and self.sell_exchange in reliable_exchanges:
            reliability_factor = 0.15
        elif (self.buy_exchange in reliable_exchanges or self.sell_exchange in reliable_exchanges):
            reliability_factor = 0.10
        elif (self.buy_exchange in good_exchanges and self.sell_exchange in good_exchanges):
            reliability_factor = 0.05
        
        return min(1.0, base_confidence + spread_factor + volume_factor + reliability_factor)
    
    def _calculate_profit_potential(self) -> float:
        """Calculate potential profit in USD"""
        if not self.buy_volume or not self.sell_volume:
            return 0.0
        
        volume_limits = {
            'BTC': 0.5, 'ETH': 5.0, 'XRP': 1000.0, 'LTC': 10.0,
            'ADA': 1000.0, 'DOT': 100.0, 'LINK': 100.0, 'UNI': 100.0
        }
        
        symbol_base = self.symbol.split('/')[0]
        max_volume = volume_limits.get(symbol_base, 100.0)
        
        tradeable_volume = min(self.buy_volume, self.sell_volume, max_volume)
        effective_spread = self.spread * 0.9  # Account for slippage
        
        return effective_spread * tradeable_volume
    
    def _estimate_execution_time(self) -> float:
        """Estimate time window for execution in seconds"""
        base_time = 30.0
        spread_factor = max(0.5, 2.0 - (self.spread_percent / 0.5))
        
        liquidity_factor = 1.0
        if 'BTC' in self.symbol or 'ETH' in self.symbol:
            liquidity_factor = 0.7
        
        return base_time * spread_factor * liquidity_factor
    
    def _assess_risk_level(self) -> str:
        """Assess risk level based on various factors"""
        if self.spread_percent > 1.0:
            return "high"
        elif self.spread_percent > 0.5:
            return "medium-high"
        elif self.spread_percent > 0.2:
            return "medium"
        elif self.spread_percent > 0.1:
            return "medium-low"
        else:
            return "low"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
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
            "confidenceScore": self.confidence_score,
            "profitPotential": self.profit_potential,
            "executionTimeEstimate": self.execution_time_estimate,
            "riskLevel": self.risk_level,
            "historicalFrequency": self.historical_frequency
        }

@dataclass
class AlertCondition:
    """User-defined alert condition"""
    id: str
    name: str
    symbol: Optional[str] = None
    min_spread_percent: float = 0.1
    min_profit_potential: float = 0.0
    min_confidence_score: float = 0.5
    preferred_exchanges: List[str] = field(default_factory=list)
    max_risk_level: str = "medium-high"
    enabled: bool = True
    
    def matches(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if opportunity matches this alert condition"""
        if not self.enabled:
            return False
        
        if self.symbol and opportunity.symbol != self.symbol:
            return False
        
        if opportunity.spread_percent < self.min_spread_percent:
            return False
        
        if opportunity.profit_potential < self.min_profit_potential:
            return False
        
        if opportunity.confidence_score < self.min_confidence_score:
            return False
        
        if self.preferred_exchanges:
            if (opportunity.buy_exchange not in self.preferred_exchanges and 
                opportunity.sell_exchange not in self.preferred_exchanges):
                return False
        
        risk_levels = ["low", "medium-low", "medium", "medium-high", "high"]
        if risk_levels.index(opportunity.risk_level) > risk_levels.index(self.max_risk_level):
            return False
        
        return True

class ArbitrageDetector:
    """Advanced arbitrage detector with analytics and alerts"""
    
    def __init__(self, min_spread_percent: float = 0.05):
        self.min_spread_percent = min_spread_percent
        self.opportunities: Dict[str, ArbitrageOpportunity] = {}
        self.historical_opportunities: List[ArbitrageOpportunity] = []
        self.alert_conditions: Dict[str, AlertCondition] = {}
        self.last_detection_time = 0
        self.detection_stats = {
            "total_detections": 0,
            "opportunities_found": 0,
            "avg_detection_time": 0.0,
            "detection_times": []
        }
    
    async def detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """Detect arbitrage opportunities with enhanced analytics"""
        start_time = time.time()
        opportunities = []
        
        try:
            all_quotes = await exchange_manager.fetch_all_quotes()
            
            if len(all_quotes) < 2:
                logger.warning("Need at least 2 exchanges for arbitrage detection")
                return opportunities
            
            for symbol in exchange_manager.get_supported_symbols():
                symbol_opportunities = self._analyze_symbol(symbol, all_quotes)
                opportunities.extend(symbol_opportunities)
            
            opportunities.sort(key=lambda x: x.profit_potential, reverse=True)
            
            self._update_historical_data(opportunities)
            self.opportunities = {opp.id: opp for opp in opportunities}
            
            detection_time = time.time() - start_time
            self._update_detection_stats(detection_time, len(opportunities))
            
            if opportunities:
                logger.info(f"🔍 Found {len(opportunities)} opportunities in {detection_time:.2f}s")
                for opp in opportunities[:3]:
                    logger.info(f"💰 {opp.symbol}: {opp.spread_percent:.3f}% "
                              f"({opp.buy_exchange} → {opp.sell_exchange}) "
                              f"Profit: ${opp.profit_potential:.2f}")
            else:
                logger.debug(f"😴 No opportunities found in {detection_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error in detect_opportunities: {e}")
        
        return opportunities
    
    def _analyze_symbol(self, symbol: str, all_quotes: Dict) -> List[ArbitrageOpportunity]:
        """Analyze arbitrage opportunities for a specific symbol"""
        opportunities = []
        
        symbol_quotes = {}
        for exchange_name, quotes in all_quotes.items():
            if symbol in quotes:
                symbol_quotes[exchange_name] = quotes[symbol]
        
        if len(symbol_quotes) < 2:
            return opportunities
        
        exchanges = list(symbol_quotes.keys())
        for i, buy_exchange in enumerate(exchanges):
            for j, sell_exchange in enumerate(exchanges):
                if i >= j:
                    continue
                
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
        """Check for arbitrage between two exchanges"""
        opportunities = []
        
        try:
            buy_price = buy_quote.ask
            sell_price = sell_quote.bid
            
            if buy_price <= 0 or sell_price <= 0:
                return opportunities
            
            spread = sell_price - buy_price
            spread_percent = (spread / buy_price) * 100
            
            if spread > 0 and spread_percent >= self.min_spread_percent:
                opportunity_id = f"{symbol}_{buy_exchange}_{sell_exchange}_{int(time.time())}"
                
                opportunity = ArbitrageOpportunity(
                    id=opportunity_id,
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
        
        except Exception as e:
            logger.error(f"Error checking arbitrage pair: {e}")
        
        return opportunities
    
    def _update_historical_data(self, opportunities: List[ArbitrageOpportunity]):
        """Update historical opportunity data"""
        self.historical_opportunities.extend(opportunities)
        
        cutoff_time = time.time() - 86400  # 24 hours
        self.historical_opportunities = [
            opp for opp in self.historical_opportunities 
            if opp.timestamp > cutoff_time
        ]
        
        for opportunity in opportunities:
            similar_count = sum(
                1 for hist_opp in self.historical_opportunities
                if (hist_opp.symbol == opportunity.symbol and
                    hist_opp.buy_exchange == opportunity.buy_exchange and
                    hist_opp.sell_exchange == opportunity.sell_exchange)
            )
            opportunity.historical_frequency = similar_count / max(1, len(self.historical_opportunities))
    
    def _update_detection_stats(self, detection_time: float, opportunities_count: int):
        """Update detection statistics"""
        self.detection_stats["total_detections"] += 1
        self.detection_stats["opportunities_found"] += opportunities_count
        
        self.detection_stats["detection_times"].append(detection_time)
        if len(self.detection_stats["detection_times"]) > 100:
            self.detection_stats["detection_times"].pop(0)
        
        self.detection_stats["avg_detection_time"] = statistics.mean(
            self.detection_stats["detection_times"]
        )
    
    def add_alert_condition(self, condition: AlertCondition):
        """Add a new alert condition"""
        self.alert_conditions[condition.id] = condition
        logger.info(f"Added alert condition: {condition.name}")
    
    def remove_alert_condition(self, condition_id: str):
        """Remove an alert condition"""
        if condition_id in self.alert_conditions:
            del self.alert_conditions[condition_id]
            logger.info(f"Removed alert condition: {condition_id}")
    
    def check_alerts(self, opportunities: List[ArbitrageOpportunity]) -> List[Tuple[AlertCondition, ArbitrageOpportunity]]:
        """Check opportunities against alert conditions"""
        triggered_alerts = []
        
        for opportunity in opportunities:
            for condition in self.alert_conditions.values():
                if condition.matches(opportunity):
                    triggered_alerts.append((condition, opportunity))
        
        return triggered_alerts
    
    def get_analytics(self) -> Dict:
        """Get comprehensive analytics"""
        current_time = time.time()
        current_opps = list(self.opportunities.values())
        recent_opps = [
            opp for opp in self.historical_opportunities
            if current_time - opp.timestamp < 86400
        ]
        
        analytics = {
            "current": {
                "total_opportunities": len(current_opps),
                "avg_spread": statistics.mean([opp.spread_percent for opp in current_opps]) if current_opps else 0,
                "max_spread": max([opp.spread_percent for opp in current_opps]) if current_opps else 0,
                "total_profit_potential": sum([opp.profit_potential for opp in current_opps]),
                "avg_confidence": statistics.mean([opp.confidence_score for opp in current_opps]) if current_opps else 0,
            },
            "historical_24h": {
                "total_opportunities": len(recent_opps),
                "avg_spread": statistics.mean([opp.spread_percent for opp in recent_opps]) if recent_opps else 0,
                "max_spread": max([opp.spread_percent for opp in recent_opps]) if recent_opps else 0,
                "opportunities_per_hour": len(recent_opps) / 24,
            },
            "detection_stats": self.detection_stats,
            "alert_conditions": len(self.alert_conditions)
        }
        
        return analytics

# Global detector instance
arbitrage_detector = ArbitrageDetector(min_spread_percent=0.05)
