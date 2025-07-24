from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
from typing import List, Dict, Any
from dataclasses import asdict
import uvicorn

# Import your existing connectors
from connectors import AdvancedTradeConnector, KrakenConnector, OrderBookUpdate

app = FastAPI(title="Crypto Arbitrage API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store current arbitrage opportunities
current_opportunities: Dict[str, Any] = {}
best_prices: Dict[str, Dict[str, Dict[str, float]]] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                dead_connections.append(connection)
        
        # Remove dead connections
        for dead_conn in dead_connections:
            self.active_connections.remove(dead_conn)

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Crypto Arbitrage API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "opportunities_count": len(current_opportunities),
        "connected_websockets": len(manager.active_connections)
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
            "averageSpread": sum(opp.get("spreadPercent", 0) for opp in current_opportunities.values()) / max(len(current_opportunities), 1)
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current opportunities immediately
        if current_opportunities:
            message = {
                "type": "arbitrage_update",
                "data": {
                    "opportunities": list(current_opportunities.values()),
                    "timestamp": time.time()
                }
            }
            await websocket.send_text(json.dumps(message))
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def producer(conn, queue: asyncio.Queue):
    """Read from one connector and push updates into the queue."""
    try:
        async for otu in conn.stream():
            await queue.put(otu)
    except Exception as e:
        print(f"Producer error: {e}")
        # Restart after delay
        await asyncio.sleep(5)

async def arbitrage_detector_service():
    """
    Run your existing arbitrage detection logic and broadcast results
    """
    symbols = ["BTC/USD", "ETH/USD", "XRP/USD"]
    queue = asyncio.Queue()
    threshold = 0.002  # 0.2%
    
    # Start producers
    producers = []
    for s in symbols:
        producers.append(asyncio.create_task(producer(AdvancedTradeConnector(s), queue)))
        producers.append(asyncio.create_task(producer(KrakenConnector(s), queue)))
    
    # Process order book updates
    while True:
        try:
            otu: OrderBookUpdate = await asyncio.wait_for(queue.get(), timeout=1.0)
            ex, sym = otu.exchange, otu.symbol

            # Initialize storage
            if ex not in best_prices:
                best_prices[ex] = {}
            if sym not in best_prices[ex]:
                best_prices[ex][sym] = {}

            # Update best bid/ask
            if otu.bids:
                best_bid = max(otu.bids, key=lambda x: x[0])[0]
                best_prices[ex][sym]['bid'] = best_bid

            if otu.asks:
                best_ask = min(otu.asks, key=lambda x: x[0])[0]
                best_prices[ex][sym]['ask'] = best_ask

            # Check cross-exchange arbitrage for this symbol
            for buy_ex in best_prices:
                for sell_ex in best_prices:
                    if buy_ex == sell_ex:
                        continue

                    buy_data = best_prices[buy_ex].get(sym, {})
                    sell_data = best_prices[sell_ex].get(sym, {})

                    ask = buy_data.get('ask')
                    bid = sell_data.get('bid')

                    if ask and bid:
                        spread = bid - ask
                        pct = spread / ask
                        if pct > threshold:
                            opportunity_id = f"{sym}_{buy_ex}_{sell_ex}"
                            opportunity = {
                                "id": opportunity_id,
                                "symbol": sym,
                                "buyExchange": buy_ex,
                                "sellExchange": sell_ex,
                                "buyPrice": ask,
                                "sellPrice": bid,
                                "spread": spread,
                                "spreadPercent": pct * 100,
                                "timestamp": time.time(),
                                "volume": 1.0,  # You can calculate this based on order book depth
                                "confidence": 0.95
                            }
                            
                            current_opportunities[opportunity_id] = opportunity
                            
                            # Broadcast to all connected WebSocket clients
                            await manager.broadcast(json.dumps({
                                "type": "new_opportunity",
                                "data": opportunity
                            }))
                            
                            print(f"[{time.strftime('%H:%M:%S')}] "
                                  f"Arb ▶ {sym}: buy on {buy_ex} @ {ask:.2f}, "
                                  f"sell on {sell_ex} @ {bid:.2f}, "
                                  f"spread {spread:.2f} USD ({pct*100:.2f}%)")

            queue.task_done()
            
        except asyncio.TimeoutError:
            # Clean up old opportunities (older than 30 seconds)
            current_time = time.time()
            expired_opportunities = [
                opp_id for opp_id, opp in current_opportunities.items()
                if current_time - opp["timestamp"] > 30
            ]
            for opp_id in expired_opportunities:
                del current_opportunities[opp_id]
            
        except Exception as e:
            print(f"Arbitrage detector error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    # Start the arbitrage detection service
    asyncio.create_task(arbitrage_detector_service())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
