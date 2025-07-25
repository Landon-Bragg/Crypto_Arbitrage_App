from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from typing import List, Dict, Any
import uvicorn

# Import our modules
from exchanges import exchange_manager
from arbitrage_detector import arbitrage_detector

app = FastAPI(title="Crypto Arbitrage API", version="2.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📱 WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"📱 WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                dead_connections.append(connection)
        
        for dead_conn in dead_connections:
            self.active_connections.remove(dead_conn)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {
        "message": "Crypto Arbitrage API v2.1 - Focused on Kraken, KuCoin & Bitfinex",
        "exchanges": exchange_manager.get_supported_exchanges(),
        "symbols": exchange_manager.get_supported_symbols(),
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    # Test exchange connections
    connections = await exchange_manager.test_connections()
    stats = arbitrage_detector.get_statistics()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "exchanges": connections,
        "connected_exchanges": sum(connections.values()),
        "total_exchanges": len(connections),
        "opportunities_count": stats["total_opportunities"],
        "connected_websockets": len(manager.active_connections),
        "best_spread": stats["best_spread"],
        "total_profit_potential": stats["total_profit_potential"]
    }

@app.get("/exchanges")
async def get_exchanges():
    """Get supported exchanges and their connection status"""
    connections = await exchange_manager.test_connections()
    return {
        "exchanges": exchange_manager.get_supported_exchanges(),
        "symbols": exchange_manager.get_supported_symbols(),
        "connections": connections,
        "exchange_info": {
            "kraken": "US-based, highly reliable, good for BTC/ETH",
            "kucoin": "International, good liquidity, wide selection",
            "bitfinex": "International, excellent for arbitrage, high liquidity"
        }
    }

@app.get("/quotes")
async def get_live_quotes():
    """Get current live quotes from all exchanges"""
    try:
        quotes = await exchange_manager.fetch_all_quotes()
        return {
            "quotes": {
                exchange: {
                    symbol: quote.to_dict() 
                    for symbol, quote in symbols.items()
                }
                for exchange, symbols in quotes.items()
            },
            "timestamp": time.time(),
            "total_quotes": sum(len(symbols) for symbols in quotes.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quotes: {str(e)}")

@app.get("/quotes/{exchange}/{symbol}")
async def get_quote(exchange: str, symbol: str):
    """Get a specific quote from an exchange"""
    try:
        quote = await exchange_manager.fetch_ticker(exchange, symbol)
        if not quote:
            raise HTTPException(status_code=404, detail="Quote not found")
        return quote.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quote: {str(e)}")

@app.get("/arbitrage")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    opportunities = arbitrage_detector.get_current_opportunities()
    quotes = arbitrage_detector.get_last_quotes()
    stats = arbitrage_detector.get_statistics()
    
    return {
        "opportunities": opportunities,
        "metadata": {
            "lastUpdate": time.time(),
            "exchangesConnected": list(quotes.keys()),
            "totalOpportunities": stats["total_opportunities"],
            "averageSpread": stats["average_spread"],
            "bestSpread": stats["best_spread"],
            "totalProfitPotential": stats["total_profit_potential"],
            "symbols": exchange_manager.get_supported_symbols(),
            "minSpreadThreshold": arbitrage_detector.min_spread_percent
        }
    }

@app.get("/arbitrage/{symbol}")
async def get_arbitrage_for_symbol(symbol: str):
    """Get arbitrage opportunities for a specific symbol"""
    all_opportunities = arbitrage_detector.get_current_opportunities()
    symbol_opportunities = [opp for opp in all_opportunities if opp["symbol"] == symbol]
    
    return {
        "symbol": symbol,
        "opportunities": symbol_opportunities,
        "count": len(symbol_opportunities),
        "timestamp": time.time()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current opportunities immediately
        opportunities = arbitrage_detector.get_current_opportunities()
        if opportunities:
            message = {
                "type": "arbitrage_update",
                "data": {
                    "opportunities": opportunities,
                    "timestamp": time.time(),
                    "count": len(opportunities)
                }
            }
            await websocket.send_text(json.dumps(message))
        
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(30)  # Send update every 30 seconds
            opportunities = arbitrage_detector.get_current_opportunities()
            message = {
                "type": "arbitrage_update",
                "data": {
                    "opportunities": opportunities,
                    "timestamp": time.time(),
                    "count": len(opportunities)
                }
            }
            await websocket.send_text(json.dumps(message))
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def arbitrage_detector_service():
    """Background service that continuously detects arbitrage opportunities"""
    print("🔍 Arbitrage detector service started")
    print("🎯 Monitoring Kraken, KuCoin, and Bitfinex for opportunities...")
    
    while True:
        try:
            start_time = time.time()
            
            # Detect opportunities
            opportunities = await arbitrage_detector.detect_opportunities()
            
            detection_time = time.time() - start_time
            
            if opportunities:
                # Broadcast to all connected WebSocket clients
                message = {
                    "type": "arbitrage_update",
                    "data": {
                        "opportunities": [opp.to_dict() for opp in opportunities],
                        "timestamp": time.time(),
                        "count": len(opportunities),
                        "detection_time": detection_time
                    }
                }
                await manager.broadcast(json.dumps(message))
                
                print(f"📡 Found {len(opportunities)} opportunities in {detection_time:.2f}s, "
                      f"broadcasted to {len(manager.active_connections)} clients")
                
                # Log best opportunity
                best = max(opportunities, key=lambda x: x.spread_percent)
                print(f"🏆 Best: {best.symbol} {best.spread_percent:.3f}% "
                      f"({best.buy_exchange} → {best.sell_exchange})")
            else:
                print(f"😴 No opportunities found in {detection_time:.2f}s")
            
            # Wait before next detection cycle (reduced to 20 seconds for more frequent updates)
            await asyncio.sleep(20)
            
        except Exception as e:
            print(f"❌ Error in arbitrage detector service: {e}")
            await asyncio.sleep(10)  # Wait before retrying

@app.on_event("startup")
async def on_startup():
    print("🚀 Starting arbitrage detection service...")
    asyncio.create_task(arbitrage_detector_service())

if __name__ == "__main__":
    print("🚀 Starting Crypto Arbitrage API server...")
    print("🎯 Focused on Kraken, KuCoin, and Bitfinex")
    print("📊 Monitoring BTC, ETH, XRP, and LTC")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
