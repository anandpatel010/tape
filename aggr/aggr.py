import asyncio
import websockets
import json
import time
import threading
import queue as thread_queue

# ANSI colors
GREEN = "\033[32m"
PURPLE = "\033[35m"
RESET = "\033[0m"

async def main():
    symbol_queue = asyncio.Queue()  # Async queue for symbol changes
    current_symbol = 'btcusdt'  # Start with BTC/USDT
    value_threshold = 100.0  # Show only aggregated trades where total $ value > this
    square_threshold = 10000  # USD threshold for squares
    square_char = "▬"

    # Thread for CLI input
    input_queue = thread_queue.Queue()  # Thread-safe queue
    def input_thread():
        while True:
            new_input = input().strip().lower()
            if new_input:
                # Assume USDT pair; append 'usdt' if not present
                new_symbol = new_input + 'usdt' if not new_input.endswith('usdt') else new_input
                input_queue.put(new_symbol)

    threading.Thread(target=input_thread, daemon=True).start()

    while True:
        # Check for new symbol from input
        try:
            new_symbol = input_queue.get_nowait()
            current_symbol = new_symbol
        except thread_queue.Empty:
            pass

        ws_url = f"wss://stream.binance.com:9443/ws/{current_symbol}@trade"
        upper_symbol = current_symbol.upper().replace('USDT', '/USDT')

        print(f"\nWatching large trades (>${value_threshold}) for {upper_symbol} on Binance... (Enter new symbol like 'doge' to switch)")
        print("Timestamp | Side | $Value (Base Amount) @ Avg Price (USDT)")

        current_time = None
        totals = {
            'BUY': {'total_amount': 0.0, 'total_value': 0.0},
            'SELL': {'total_amount': 0.0, 'total_value': 0.0}
        }

        try:
            async with websockets.connect(ws_url) as ws:
                while True:
                    # Non-blocking check for new symbol
                    try:
                        new_symbol = input_queue.get_nowait()
                        current_symbol = new_symbol
                        await ws.close()  # Close current WS to trigger reconnect with new symbol
                        break
                    except thread_queue.Empty:
                        pass

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
                                    if data['total_value'] > value_threshold:
                                        avg_price = data['total_value'] / data['total_amount'] if data['total_amount'] > 0 else 0
                                        value = data['total_value']
                                        amount = data['total_amount']
                                        color = GREEN if side == 'BUY' else PURPLE
                                        num_squares = int(value // square_threshold) if value > square_threshold else 0
                                        squares = (color + square_char + RESET) * num_squares
                                        print(f"{current_time} | {color}{side}{RESET} | ${value:,.0f} ({amount:.4f} Base) @ {avg_price:.2f}" + (f" {squares}" if num_squares > 0 else ""))

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