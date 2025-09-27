import asyncio
import websockets
import json
import time

# ANSI colors
GREEN = "\033[32m"
PURPLE = "\033[35m"
RESET = "\033[0m"

async def main():
    symbol = 'btcusdt'  # Lowercase for WS stream
    ws_url = f"wss://stream.binance.com:9443/ws/{symbol}@trade"
    threshold = 0.001  # Show only trades larger than this amount (in BTC)

    print(f"Watching large trades (>{threshold} BTC) for BTC/USDT on Binance...")
    print("Timestamp | Side | Amount (BTC) @ Price (USDT)")

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    message = await ws.recv()
                    trade = json.loads(message)
                    if trade['e'] == 'trade':
                        price = float(trade['p'])
                        amount = float(trade['q'])
                        ts = trade['T']  # ms timestamp
                        is_buyer_maker = trade['m']  # True: sell (aggressor sell), False: buy (aggressor buy)

                        if amount > threshold:
                            side = 'SELL' if is_buyer_maker else 'BUY'
                            color = PURPLE if is_buyer_maker else GREEN
                            formatted_time = time.strftime('%H:%M:%S', time.localtime(ts / 1000))
                            print(f"{formatted_time} | {color}{side}{RESET} | {amount:.2f} @ {price:.2f}")
        except Exception as e:
            print(f"Error: {e}. Reconnecting in 1s...")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())