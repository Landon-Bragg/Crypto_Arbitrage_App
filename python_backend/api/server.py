from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
import time
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import logging

# Import our modules
from ..exchanges.exchange_manager import exchange_manager
from ..arbitrage.detector import arbitrage_detector, AlertCondition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Professional Crypto Arbitrage API",
    version="3.0.0",
    description="Advanced real-time arbitrage detection across Kraken, KuCoin, and Bitfinex",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "https://*.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    """Enhanced WebSocket connection manager"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_info[websocket] = {
            "connected_at": time.time(),
            "client_info": client_info or {},
            "messages_sent": 0
        }
        logger.info(f"📱 WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            logger.info(f"📱 WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
            if websocket in self.connection_info:
                self.connection_info[websocket]["messages_sent"] += 1
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: str, message_type: str = "general"):
        if not self.active_connections:
            return
        
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
                if connection in self.connection_info:
                    self.connection_info[connection]["messages_sent"] += 1
            except:
                dead_connections.append(connection)
        
        for dead_conn in dead_connections:
            self.disconnect(dead_conn)
        
        logger.debug(f"📡 Broadcasted {message_type} to {len(self.active_connections)} clients")

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("🚀 Starting Professional Crypto Arbitrage API...")
    
    # Initialize exchanges
    await exchange_manager.initialize()
    
    # Start background services
    asyncio.create_task(arbitrage_detection_service())
    asyncio.create_task(health_monitoring_service())
    
    logger.info("✅ Application startup complete")

@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation homepage"""
    return """
    <html>
        <head>
            <title>Professional Crypto Arbitrage API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { color: #2c3e50; }
                .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .status { color: #27ae60; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1 class="header">🚀 Professional Crypto Arbitrage API v3.0</h1>
            <p class="status">Status: Operational</p>
            <p>Advanced real-time arbitrage detection across Kraken, KuCoin, and Bitfinex</p>
            
            <h2>Key Features:</h2>
            <ul>
                <li>Real-time price monitoring across 3 major exchanges</li>
                <li>Advanced arbitrage detection with confidence scoring</li>
                <li>Customizable alerts and notifications</li>
                <li>Historical analytics and trend analysis</li>
                <li>WebSocket real-time updates</li>
                <li>Professional-grade error handling and monitoring</li>
            </ul>
            
            <h2>Quick Links:</h2>
            <div class="endpoint"><a href="/docs">📚 Interactive API Documentation</a></div>
            <div class="endpoint"><a href="/health">🔍 System Health Check</a></div>
            <div class="endpoint"><a href="/arbitrage">💰 Current Opportunities</a></div>
            <div class="endpoint"><a href="/analytics">📊 Analytics Dashboard</a></div>
            
            <p><em>Built for professional traders and developers</em></p>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Comprehensive system health check"""
    exchange_statuses = exchange_manager.get_exchange_statuses()
    connected_exchanges = exchange_manager.get_connected_exchanges()
    analytics = arbitrage_detector.get_analytics()
    
    health_score = len(connected_exchanges) / len(exchange_statuses) if exchange_statuses else 0
    
    return {
        "status": "healthy" if health_score > 0.5 else "degraded",
        "timestamp": time.time(),
        "health_score": health_score,
        "exchanges": {
            "total": len(exchange_statuses),
            "connected": len(connected_exchanges),
            "statuses": exchange_statuses
        },
        "arbitrage_detector": {
            "total_detections": analytics["detection_stats"]["total_detections"],
            "avg_detection_time": analytics["detection_stats"]["avg_detection_time"],
            "current_opportunities": analytics["current"]["total_opportunities"]
        },
        "websocket_connections": len(manager.active_connections),
        "uptime": time.time() - startup_time if 'startup_time' in globals() else 0
    }

@app.get("/exchanges")
async def get_exchanges():
    """Get detailed exchange information"""
    statuses = exchange_manager.get_exchange_statuses()
    market_summary = exchange_manager.get_market_summary()
    
    return {
        "exchanges": statuses,
        "supported_symbols": exchange_manager.get_supported_symbols(),
        "connected_exchanges": exchange_manager.get_connected_exchanges(),
        "market_summary": market_summary,
        "timestamp": time.time()
    }

@app.get("/quotes")
async def get_live_quotes():
    """Get current live quotes from all exchanges"""
    try:
        quotes = await exchange_manager.fetch_all_quotes()
        market_summary = exchange_manager.get_market_summary()
        
        return {
            "quotes": {
                exchange: {
                    symbol: quote.to_dict() 
                    for symbol, quote in symbols.items()
                }
                for exchange, symbols in quotes.items()
            },
            "market_summary": market_summary,
            "timestamp": time.time(),
            "total_quotes": sum(len(symbols) for symbols in quotes.values())
        }
    except Exception as e:
        logger.error(f"Error fetching quotes: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching quotes: {str(e)}")

@app.get("/quotes/{exchange}")
async def get_exchange_quotes(exchange: str):
    """Get quotes from a specific exchange"""
    if exchange not in exchange_manager.exchanges:
        raise HTTPException(status_code=404, detail="Exchange not found")
    
    try:
        quotes = await exchange_manager.exchanges[exchange].fetch_all_tickers()
        return {
            "exchange": exchange,
            "quotes": {symbol: quote.to_dict() for symbol, quote in quotes.items()},
            "timestamp": time.time(),
            "count": len(quotes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quotes from {exchange}: {str(e)}")

@app.get("/quotes/{exchange}/{symbol}")
async def get_specific_quote(exchange: str, symbol: str):
    """Get a specific quote from an exchange"""
    try:
        quote = await exchange_manager.get_quote(exchange, symbol)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        return quote.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quote: {str(e)}")

@app.get("/arbitrage")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    opportunities = list(arbitrage_detector.opportunities.values())
    analytics = arbitrage_detector.get_analytics()
    
    return {
        "opportunities": [opp.to_dict() for opp in opportunities],
        "metadata": {
            "total_opportunities": len(opportunities),
            "timestamp": time.time(),
            "connected_exchanges": exchange_manager.get_connected_exchanges(),
            "detection_stats": analytics["detection_stats"],
            "current_analytics": analytics["current"]
        }
    }

@app.get("/arbitrage/{symbol}")
async def get_arbitrage_for_symbol(symbol: str):
    """Get arbitrage opportunities for a specific symbol"""
    opportunities = [
        opp for opp in arbitrage_detector.opportunities.values()
        if opp.symbol == symbol
    ]
    
    return {
        "symbol": symbol,
        "opportunities": [opp.to_dict() for opp in opportunities],
        "count": len(opportunities),
        "timestamp": time.time()
    }

@app.get("/analytics")
async def get_analytics():
    """Get comprehensive analytics"""
    analytics = arbitrage_detector.get_analytics()
    exchange_statuses = exchange_manager.get_exchange_statuses()
    market_summary = exchange_manager.get_market_summary()
    
    return {
        "arbitrage_analytics": analytics,
        "exchange_analytics": {
            "statuses": exchange_statuses,
            "market_summary": market_summary
        },
        "system_analytics": {
            "websocket_connections": len(manager.active_connections),
            "uptime": time.time() - startup_time if 'startup_time' in globals() else 0
        },
        "timestamp": time.time()
    }

@app.post("/alerts")
async def create_alert(alert_data: Dict[str, Any]):
    """Create a new alert condition"""
    try:
        condition = AlertCondition(
            id=alert_data.get("id", f"alert_{int(time.time())}"),
            name=alert_data["name"],
            symbol=alert_data.get("symbol"),
            min_spread_percent=alert_data.get("min_spread_percent", 0.1),
            min_profit_potential=alert_data.get("min_profit_potential", 0.0),
            min_confidence_score=alert_data.get("min_confidence_score", 0.5),
            preferred_exchanges=alert_data.get("preferred_exchanges", []),
            max_risk_level=alert_data.get("max_risk_level", "medium-high"),
            enabled=alert_data.get("enabled", True)
        )
        
        arbitrage_detector.add_alert_condition(condition)
        
        return {
            "success": True,
            "alert_id": condition.id,
            "message": f"Alert '{condition.name}' created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating alert: {str(e)}")

@app.get("/alerts")
async def get_alerts():
    """Get all alert conditions"""
    return {
        "alerts": {
            alert_id: {
                "id": condition.id,
                "name": condition.name,
                "symbol": condition.symbol,
                "min_spread_percent": condition.min_spread_percent,
                "min_profit_potential": condition.min_profit_potential,
                "min_confidence_score": condition.min_confidence_score,
                "preferred_exchanges": condition.preferred_exchanges,
                "max_risk_level": condition.max_risk_level,
                "enabled": condition.enabled
            }
            for alert_id, condition in arbitrage_detector.alert_conditions.items()
        },
        "count": len(arbitrage_detector.alert_conditions),
        "timestamp": time.time()
    }

@app.delete("/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert condition"""
    if alert_id not in arbitrage_detector.alert_conditions:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    arbitrage_detector.remove_alert_condition(alert_id)
    return {"success": True, "message": f"Alert {alert_id} deleted successfully"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with multiple data streams"""
    await manager.connect(websocket)
    
    try:
        # Send initial data
        opportunities = list(arbitrage_detector.opportunities.values())
        if opportunities:
            initial_message = {
                "type": "initial_data",
                "data": {
                    "opportunities": [opp.to_dict() for opp in opportunities],
                    "timestamp": time.time(),
                    "connected_exchanges": exchange_manager.get_connected_exchanges()
                }
            }
            await manager.send_personal_message(json.dumps(initial_message), websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (for future interactive features)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle client messages here if needed
            except asyncio.TimeoutError:
                # Send periodic heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "timestamp": time.time(),
                    "connections": len(manager.active_connections)
                }
                await manager.send_personal_message(json.dumps(heartbeat), websocket)
                await asyncio.sleep(30)  # Wait 30 seconds before next heartbeat
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def arbitrage_detection_service():
    """Enhanced background arbitrage detection service"""
    logger.info("🔍 Starting arbitrage detection service...")
    
    while True:
        try:
            start_time = time.time()
            
            # Detect opportunities
            opportunities = await arbitrage_detector.detect_opportunities()
            
            # Check for alerts
            triggered_alerts = arbitrage_detector.check_alerts(opportunities)
            
            detection_time = time.time() - start_time
            
            # Broadcast opportunities to WebSocket clients
            if opportunities or len(manager.active_connections) > 0:
                message = {
                    "type": "arbitrage_update",
                    "data": {
                        "opportunities": [opp.to_dict() for opp in opportunities],
                        "timestamp": time.time(),
                        "detection_time": detection_time,
                        "connected_exchanges": exchange_manager.get_connected_exchanges(),
                        "triggered_alerts": len(triggered_alerts)
                    }
                }
                await manager.broadcast(json.dumps(message), "arbitrage_update")
            
            # Handle triggered alerts
            if triggered_alerts:
                alert_message = {
                    "type": "alert_triggered",
                    "data": {
                        "alerts": [
                            {
                                "condition": condition.name,
                                "opportunity": opportunity.to_dict()
                            }
                            for condition, opportunity in triggered_alerts
                        ],
                        "timestamp": time.time()
                    }
                }
                await manager.broadcast(json.dumps(alert_message), "alert")
                logger.info(f"🚨 {len(triggered_alerts)} alerts triggered")
            
            # Log performance
            if opportunities:
                best_opp = max(opportunities, key=lambda x: x.profit_potential)
                logger.info(f"🏆 Best opportunity: {best_opp.symbol} "
                          f"{best_opp.spread_percent:.3f}% (${best_opp.profit_potential:.2f})")
            
            # Wait before next detection cycle
            await asyncio.sleep(15)  # Check every 15 seconds
            
        except Exception as e:
            logger.error(f"❌ Error in arbitrage detection service: {e}")
            await asyncio.sleep(10)

async def health_monitoring_service():
    """Background health monitoring service"""
    logger.info("🏥 Starting health monitoring service...")
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            
            # Perform health checks
            await exchange_manager.perform_health_checks()
            
            # Send health update to WebSocket clients
            health_data = {
                "type": "health_update",
                "data": {
                    "exchange_statuses": exchange_manager.get_exchange_statuses(),
                    "connected_exchanges": exchange_manager.get_connected_exchanges(),
                    "timestamp": time.time()
                }
            }
            await manager.broadcast(json.dumps(health_data), "health_update")
            
        except Exception as e:
            logger.error(f"❌ Error in health monitoring service: {e}")

# Global startup time tracking
startup_time = time.time()

if __name__ == "__main__":
    logger.info("🚀 Starting Professional Crypto Arbitrage API server...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )
