from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from typing import List, Dict, Any
import uvicorn

# Import our new modules
from exchanges import exchange_manager
from arbitrage_detector import arbitrage_detector

# Define lifespan context manager without pydantic
async def startup_event():
    # Start the arbitrage detection service
    print("🚀 Starting arbitrage detection service...")
    asyncio.create_task(arbitrage_detector_service())

app = FastAPI(title="Crypto Arbitrage API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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
        "message": "Crypto Arbitrage API v2.0 - Now with live market data!",
        "exchanges": exchange_manager.get_supported_exchanges(),
        "symbols": exchange_manager.get_supported_symbols()
    }

@app.get("/health")
async def health_check():
    # Test exchange connections
    connections = await exchange_manager.test_connections()
    
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "exchanges": connections,
        "opportunities_count": len(arbitrage_detector.get_current_opportunities()),
        "connected_websockets": len(manager.active_connections)
    }

@app.get("/exchanges")
async def get_exchanges():
    """Get supported exchanges and their connection status"""
    connections = await exchange_manager.test_connections()
    return {
        "exchanges": exchange_manager.get_supported_exchanges(),
        "symbols": exchange_manager.get_supported_symbols(),
        "connections": connections
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
            "timestamp": time.time()
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
    
    return {
        "opportunities": opportunities,
        "metadata": {
            "lastUpdate": time.time(),
            "exchangesConnected": list(quotes.keys()),
            "totalOpportunities": len(opportunities),
            "averageSpread": sum(opp.get("spreadPercent", 0) for opp in opportunities) / max(len(opportunities), 1) if opportunities else 0,
            "symbols": exchange_manager.get_supported_symbols()
        }
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
                    "timestamp": time.time()
                }
            }
            await websocket.send_text(json.dumps(message))
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def arbitrage_detector_service():
    """Background service that continuously detects arbitrage opportunities"""
    print("🔍 Arbitrage detector service started")
    
    while True:
        try:
            # Detect opportunities
            opportunities = await arbitrage_detector.detect_opportunities()
            
            if opportunities:
                # Broadcast to all connected WebSocket clients
                message = {
                    "type": "arbitrage_update",
                    "data": {
                        "opportunities": [opp.to_dict() for opp in opportunities],
                        "timestamp": time.time()
                    }
                }
                await manager.broadcast(json.dumps(message))
                
                print(f"📡 Broadcasted {len(opportunities)} opportunities to {len(manager.active_connections)} clients")
            
            # Wait before next detection cycle
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            print(f"❌ Error in arbitrage detector service: {e}")
            await asyncio.sleep(10)  # Wait before retrying

@app.on_event("startup")
async def on_startup():
    await startup_event()

if __name__ == "__main__":
    print("🚀 Starting Crypto Arbitrage API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
