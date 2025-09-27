# Binance Spot Trade Tape

A lightweight Python CLI tool to monitor large spot trades on Binance for any USDT pair, inspired by [Aggr](https://github.com/Tucsky/aggr). Streams real-time trades, aggregates by millisecond timestamp, and displays with colored bars for size.

## Features
- **Real-time Trade Feed**: Streams spot trades via Binance WebSocket (`wss://stream.binance.com:9443`).
- **Dynamic Pair Switching**: Start with BTC/USDT; type a symbol (e.g., `doge`) and press Enter to switch to `[symbol]usdt`.
- **Aggregation**: Combines trades per millisecond (e.g., `12:34:56.123`) for BUY/SELL sides.
- **Filtering**: Shows only trades with total value >$100 (configurable).
- **Visuals**: Colored bars (green for BUY, purple for SELL) appended for trades >$10,000, one bar per $10k.
- **Output Format**: `Timestamp | Side | $Value (Base Amount) @ Avg Price (USDT) [bars]`.

## Requirements
- Python 3.7+
- `websockets` library (`pip install websockets`)

## Usage
1. Save the script as `aggr.py`.
2. Install dependency: `pip install websockets`
3. Run: `python aggr.py`
4. Monitor trades for BTC/USDT. Enter a new symbol (e.g., `eth`, `doge`) to switch pairs.
5. Ctrl+C to exit.

## Example Output


<img width="679" height="413" alt="image" src="https://github.com/user-attachments/assets/e19ae5e7-940e-4e89-86f7-f15976d093bf" />
