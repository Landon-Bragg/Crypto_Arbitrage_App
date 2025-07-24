from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from typing import List, Dict, Any
from dataclasses import asdict
import uvicorn

# Import your existing connectors
# from connectors import AdvancedTradeConnector, KrakenConnector, OrderBookUpdate

app = FastAPI(title="Crypto Arbitrage API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []

# Store current arbitrage opportunities
current_opportunities: Dict[str, Any] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Crypto Arbitrage API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "opportunities_count": len(current_opportunities)
    }

@app.get("/arbitrage")
async def get_arbitrage_opportunities():
    """Get current arbitrage opportunities"""
    return {
        "opportunities": list(current_opportunities.values()),
        "metadata": {
            "lastUpdate": time.time(),
            "exchangesConnected": ["coinbase-advanced", "kraken"],
            "totalOpportunities": len(current_opportunities),
            "averageSpread": 0.485
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send current opportunities every 2 seconds
            await asyncio.sleep(2)
            message = {
                "type": "arbitrage_update",
                "data": {
                    "opportunities": list(current_opportunities.values()),
                    "timestamp": time.time()
                }
            }
            await manager.send_personal_message(json.dumps(message), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def arbitrage_detector_service():
    """
    This would run your existing arbitrage detection logic
    and update current_opportunities
    """
    symbols = ["BTC/USD", "ETH/USD", "XRP/USD"]
    
    while True:
        # Mock data for now - replace with your actual connector logic
        mock_opportunity = {
            "id": f"btc_usd_{int(time.time())}",
            "symbol": "BTC/USD",
            "buyExchange": "coinbase-advanced",
            "sellExchange": "kraken",
            "buyPrice": 43250.50 + (time.time() % 100),
            "sellPrice": 43380.25 + (time.time() % 100),
            "spread": 129.75,
            "spreadPercent": 0.30,
            "timestamp": time.time(),
            "volume": 2.5,
            "confidence": 0.95
        }
        
        current_opportunities["BTC/USD"] = mock_opportunity
        
        # Broadcast to all connected WebSocket clients
        await manager.broadcast(json.dumps({
            "type": "new_opportunity",
            "data": mock_opportunity
        }))
        
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Start the arbitrage detection service
    asyncio.create_task(arbitrage_detector_service())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
