# Pouria MT5 MCP

Read-only Model Context Protocol (MCP) server for MetaTrader 5.

The server exposes MT5 market/account data to an MCP-compatible client without placing, modifying, or closing orders.

## Tools

- `mt5_status` — check MT5 terminal/Python connectivity
- `get_symbol_info` — symbol specification and trading properties
- `get_tick` — latest bid/ask/last tick
- `get_candles` — recent OHLC candles; closed candles only by default
- `get_market_snapshot` — multi-timeframe candles plus latest tick in one call
- `get_account_info` — balance/equity/margin/leverage metrics
- `get_positions` — open positions, optionally filtered by symbol

Default symbol: `XAUUSD_l`.

## Architecture

```text
MCP client
   |
   | stdio
   v
server.js (Node.js / MCP TypeScript SDK)
   |
   | child process + JSON
   v
bridge/mt5_bridge.py
   |
   v
MetaTrader 5 terminal
```

## Windows setup

Prerequisites:

- Node.js 20+
- Python with the `MetaTrader5` package installed
- MetaTrader 5 terminal installed and logged in

Clone and install:

```powershell
git clone https://github.com/0022249141/po.git
cd po
npm install
py -m pip install MetaTrader5
```

If the `MetaTrader5` package is installed in a specific Python executable, set `PYTHON_BIN` before starting the MCP server:

```powershell
$env:PYTHON_BIN="C:\Users\pouria.sl\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$env:MT5_SYMBOL="XAUUSD_l"
npm start
```

If `mt5.initialize()` cannot discover the terminal automatically, also set:

```powershell
$env:MT5_TERMINAL_PATH="C:\Program Files\MetaTrader 5\terminal64.exe"
```

Run a syntax check:

```powershell
npm run check
```

## MCP client configuration

For a local client that supports stdio MCP servers, point it to `server.js`.

Example configuration shape:

```json
{
  "mcpServers": {
    "pouria-mt5": {
      "command": "node",
      "args": ["C:\\path\\to\\po\\server.js"],
      "env": {
        "PYTHON_BIN": "C:\\path\\to\\python.exe",
        "MT5_SYMBOL": "XAUUSD_l"
      }
    }
  }
}
```

## Data rules

`get_candles` and `get_market_snapshot` use `closed_only=true` by default. In that mode MT5 bar position `0` (the forming candle) is excluded and data starts from bar position `1`.

Timestamps returned by the Python bridge are normalized to UTC ISO-8601 strings. MT5 `tick_volume`, `spread`, and `real_volume` are returned as provided by the terminal; the server does not reinterpret them as exchange order-flow data.

## Security scope

Version `0.1.0` is intentionally read-only. There is no tool for `order_send`, position closing, stop modification, or account credential handling.

Do not commit `.env`, passwords, API keys, or broker credentials. `.gitignore` excludes local environment files and `node_modules`.
