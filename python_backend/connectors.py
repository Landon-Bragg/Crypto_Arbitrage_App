import asyncio
import json
import time
import websockets
from dataclasses import dataclass
from typing import List, Tuple, AsyncIterator, Optional

@dataclass
class OrderBookUpdate:
    exchange: str
    symbol: str
    timestamp: float
    bids: List[Tuple[float, float]]
    asks: List[Tuple[float, float]]
    update_id: str

class BaseConnector:
    def __init__(self, symbol: str):
        self.symbol = symbol

    async def connect(self) -> websockets.WebSocketClientProtocol:
        raise NotImplementedError

    async def _parse(self, msg: str) -> Optional[OrderBookUpdate]:
        raise NotImplementedError

    async def stream(self) -> AsyncIterator[OrderBookUpdate]:
        ws = await self.connect()
        async for raw in ws:
            otu = await self._parse(raw)
            if otu:
                yield otu

class AdvancedTradeConnector(BaseConnector):
    WS_URL = "wss://advanced-trade-ws.coinbase.com"

    async def connect(self):
        print(f"[{self.symbol}][adv-trade] Connecting…")
        ws = await websockets.connect(self.WS_URL, max_size=8 * 1024 * 1024)
        # subscribe to level2 for our pair
        subscribe = {
            "type": "subscribe",
            "product_ids": [ self.symbol.replace("/", "-") ],
            "channel": "level2"
        }
        await ws.send(json.dumps(subscribe))
        print(f"[{self.symbol}][adv-trade] Subscribed to level2")
        return ws

    async def _parse(self, msg: str) -> Optional[OrderBookUpdate]:
        # debug: show raw payload
        print(f"[{self.symbol}][adv-trade] RAW: {msg[:200]}…")
        data = json.loads(msg)
        # only handle the order-book channel
        if data.get("channel") != "l2_data":
            return None

        bids: List[Tuple[float,float]] = []
        asks: List[Tuple[float,float]] = []

        # each event in "events" has an "updates" list
        for event in data.get("events", []):
            for u in event.get("updates", []):
                side = u.get("side")
                # try common fields for price/size
                price = float(u.get("price", u.get("price_level", 0)))
                size  = float(u.get("size",  u.get("remaining_size", 0)))
                
                if side == "bid":
                    bids.append((price, size))
                elif side == "ask":
                    asks.append((price, size))

        if not bids and not asks:
            return None

        otu = OrderBookUpdate(
            exchange="coinbase-advanced",
            symbol=self.symbol,
            timestamp=time.time(),
            bids=bids,
            asks=asks,
            update_id=f"{data.get('sequence_num','')}"
        )
        print(f"[{self.symbol}][adv-trade] Parsed → {otu}")
        return otu

class KrakenConnector(BaseConnector):
    WS_URL = "wss://ws.kraken.com"

    async def connect(self):
        ws = await websockets.connect(self.WS_URL)
        subscribe = {
            "event": "subscribe",
            "pair": [self.symbol.replace("BTC","XBT")],
            "subscription": {"name": "book", "depth": 5}
        }
        await ws.send(json.dumps(subscribe))
        return ws

    async def _parse(self, msg: str) -> Optional[OrderBookUpdate]:
        data = json.loads(msg)
        # Only handle order-book messages: [channelID, {b:…, a:…}, channelName, pair]
        if isinstance(data, list) and len(data) >= 4 and isinstance(data[1], dict):
            content = data[1]
            bids = [(float(p), float(v)) for p, v, *_ in content.get("b", [])]
            asks = [(float(p), float(v)) for p, v, *_ in content.get("a", [])]
            pair = data[3].replace("XBT", "BTC")
            return OrderBookUpdate(
                exchange="kraken",
                symbol=pair,
                timestamp=time.time(),
                bids=bids,
                asks=asks,
                update_id=str(data[0])
            )
        return None
