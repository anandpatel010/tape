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
    threshold = 0.001  # Show only aggregated trades where total BTC amount > this
    square_threshold = 10000  # USD threshold for squares
    square_char = "■"

    print(f"Watching large trades (>{threshold} BTC) for BTC/USDT on Binance...")
    print("Timestamp | Side | $Value (BTC Amount) @ Avg Price (USDT)")

    current_time = None
    totals = {
        'BUY': {'total_amount': 0.0, 'total_value': 0.0},
        'SELL': {'total_amount': 0.0, 'total_value': 0.0}
    }

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

                        this_time = time.strftime('%H:%M:%S', time.localtime(ts / 1000))

                        if this_time != current_time:
                            if current_time is not None:
                                for side, data in totals.items():
                                    if data['total_amount'] > threshold:
                                        avg_price = data['total_value'] / data['total_amount'] if data['total_amount'] > 0 else 0
                                        value = data['total_value']
                                        amount = data['total_amount']
                                        color = GREEN if side == 'BUY' else PURPLE
                                        num_squares = int(value // square_threshold) if value > square_threshold else 0
                                        squares = (color + square_char + RESET) * num_squares
                                        print(f"{current_time} | {color}{side}{RESET} | ${value:,.0f} ({amount:.4f} BTC) @ {avg_price:.2f}" + (f" {squares}" if num_squares > 0 else ""))

                            current_time = this_time
                            totals['BUY']['total_amount'] = 0.0
                            totals['BUY']['total_value'] = 0.0
                            totals['SELL']['total_amount'] = 0.0
                            totals['SELL']['total_value'] = 0.0

                        side = 'SELL' if is_buyer_maker else 'BUY'
                        totals[side]['total_amount'] += amount
                        totals[side]['total_value'] += amount * price
        except Exception as e:
            print(f"Error: {e}. Reconnecting in 1s...")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())