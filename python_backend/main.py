import asyncio
import time
from connectors import AdvancedTradeConnector, KrakenConnector, OrderBookUpdate

async def producer(conn, queue: asyncio.Queue):
    """Read from one connector and push updates into the queue."""
    async for otu in conn.stream():
        await queue.put(otu)

async def arbitrage_detector(queue: asyncio.Queue,
                             threshold: float = 0.002):
    """
    Consume OrderBookUpdates, maintain best bids/asks per exchange/symbol,
    and print whenever spread > threshold (0.2% by default).
    """
    best = {}  # best[exchange][symbol] = {'bid': float, 'ask': float}

    while True:
        otu: OrderBookUpdate = await queue.get()
        ex, sym = otu.exchange, otu.symbol

        # init storage
        best.setdefault(ex, {})
        best[ex].setdefault(sym, {})

        # update best bid/ask
        if otu.bids:
            best_bid = max(otu.bids, key=lambda x: x[0])[0]
            best[ex][sym]['bid'] = best_bid

        if otu.asks:
            best_ask = min(otu.asks, key=lambda x: x[0])[0]
            best[ex][sym]['ask'] = best_ask

        # check cross-exchange arbitrage for this symbol
        for buy_ex in best:
            for sell_ex in best:
                if buy_ex == sell_ex: 
                    continue

                buy_data  = best[buy_ex].get(sym, {})
                sell_data = best[sell_ex].get(sym, {})

                ask = buy_data.get('ask')
                bid = sell_data.get('bid')

                if ask and bid:
                    spread = bid - ask
                    pct = spread / ask
                    if pct > threshold:
                        print(f"[{time.strftime('%H:%M:%S')}] "
                              f"Arb ▶ {sym}: buy on {buy_ex} @ {ask:.2f}, "
                              f"sell on {sell_ex} @ {bid:.2f}, "
                              f"spread {spread:.2f} USD ({pct*100:.2f}%)")

        queue.task_done()

async def main():
    symbols = ["BTC/USD", "ETH/USD", "XRP/USD"]
    queue = asyncio.Queue()

    # start producers
    producers = []
    for s in symbols:
        producers.append(asyncio.create_task(producer(AdvancedTradeConnector(s), queue)))
        producers.append(asyncio.create_task(producer(KrakenConnector(s),      queue)))

    # start detector
    detector = asyncio.create_task(arbitrage_detector(queue, threshold=0.002))

    # run forever (press Ctrl+C to stop)
    await asyncio.gather(*producers, detector)

if __name__ == "__main__":
    asyncio.run(main())
