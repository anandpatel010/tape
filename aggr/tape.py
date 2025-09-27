import asyncio
import websockets
import json
import time
import threading
import queue as thread_queue

# ANSI colors
CYAN = "\033[36m"  # For BUY and connection messages
RED = "\033[31m"   # For SELL and errors
GOLD = "\033[33m"  # For $1M+ trades
RESET = "\033[0m"

async def main():
    current_symbol = 'btcusdt'  # Start with BTC/USDT
    value_threshold = 100.0  # Show only aggregated trades where total $ value > this
    million_threshold = 1000000.0  # Use gold for trades >= $1M
    bar_threshold = 10000  # USD per bar segment
    bar_char = "▬"
    last_amount = None  # For noise filtering
    last_time_prefix = None  # Track second for noise filter

    # Thread for CLI input
    input_queue = thread_queue.Queue()  # Thread-safe queue
    def input_thread():
        while True:
            new_input = input().strip().lower()
            if new_input:
                new_symbol = new_input + 'usdt' if not new_input.endswith('usdt') else new_input
                input_queue.put(new_symbol)

    threading.Thread(target=input_thread, daemon=True).start()

    # Initial connection message
    upper_symbol = current_symbol.upper().replace('USDT', '/USDT')
    print(f"{CYAN}Connected to WebSocket for {upper_symbol}{RESET}")

    while True:
        # Check for new symbol from input
        try:
            new_symbol = input_queue.get_nowait()
            current_symbol = new_symbol
            upper_symbol = current_symbol.upper().replace('USDT', '/USDT')
            print(f"{CYAN}Connected to WebSocket for {upper_symbol}{RESET}")
            last_amount = None  # Reset noise filter on symbol change
            last_time_prefix = None
        except thread_queue.Empty:
            pass

        ws_url = f"wss://stream.binance.com:9443/ws/{current_symbol}@trade"
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

                        # Convert timestamp to seconds and milliseconds
                        seconds = ts / 1000
                        formatted_time = time.strftime('%H:%M:%S', time.localtime(seconds)) + f".{int((seconds % 1) * 1000):03d}"
                        time_prefix = formatted_time[:8]  # HH:MM:SS for noise filter

                        # Noise filter: Skip if amount is nearly identical in same second
                        if last_amount is not None and last_time_prefix == time_prefix:
                            if abs(amount - last_amount) < 0.0001:  # Tolerance for "same" amount
                                continue
                        last_amount = amount
                        last_time_prefix = time_prefix

                        side = 'SELL' if is_buyer_maker else 'BUY'

                        if formatted_time != current_time:
                            # Print previous bucket if it exists and meets threshold
                            if current_time is not None:
                                for side, data in totals.items():
                                    if data['total_value'] > value_threshold:
                                        avg_price = data['total_value'] / data['total_amount'] if data['total_amount'] > 0 else 0
                                        value = data['total_value']
                                        amount = data['total_amount']
                                        color = GOLD if value >= million_threshold else (CYAN if side == 'BUY' else RED)
                                        num_bars = int(value // bar_threshold)
                                        bars = (color + bar_char + RESET) * num_bars
                                        print(f"{current_time} | {color}{side}{RESET} | ${value:,.0f} ({amount:.4f} Base) @ {avg_price:.2f}" + (f" {bars}" if num_bars > 0 else ""))

                            # Reset totals for new timestamp
                            totals = {
                                'BUY': {'total_amount': 0.0, 'total_value': 0.0},
                                'SELL': {'total_amount': 0.0, 'total_value': 0.0}
                            }
                            current_time = formatted_time

                        # Accumulate trade into current timestamp bucket
                        totals[side]['total_amount'] += amount
                        totals[side]['total_value'] += amount * price

        except Exception as e:
            print(f"{RED}Connection Error for {upper_symbol}: {e}. Reconnecting in 1s...{RESET}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())