import json
import os
import sys
from datetime import datetime, timezone

try:
    import MetaTrader5 as mt5
except Exception as exc:
    print(json.dumps({"error": f"MetaTrader5 import failed: {exc}"}, ensure_ascii=False))
    sys.exit(2)

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M2": mt5.TIMEFRAME_M2,
    "M3": mt5.TIMEFRAME_M3,
    "M4": mt5.TIMEFRAME_M4,
    "M5": mt5.TIMEFRAME_M5,
    "M6": mt5.TIMEFRAME_M6,
    "M10": mt5.TIMEFRAME_M10,
    "M12": mt5.TIMEFRAME_M12,
    "M15": mt5.TIMEFRAME_M15,
    "M20": mt5.TIMEFRAME_M20,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H2": mt5.TIMEFRAME_H2,
    "H3": mt5.TIMEFRAME_H3,
    "H4": mt5.TIMEFRAME_H4,
    "H6": mt5.TIMEFRAME_H6,
    "H8": mt5.TIMEFRAME_H8,
    "H12": mt5.TIMEFRAME_H12,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


def iso_utc(ts):
    if ts is None:
        return None
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def fail(message, code=1, details=None):
    payload = {"error": message}
    if details is not None:
        payload["details"] = details
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(code)


def initialize():
    terminal_path = os.getenv("MT5_TERMINAL_PATH")
    ok = mt5.initialize(path=terminal_path) if terminal_path else mt5.initialize()
    if not ok:
        fail("mt5.initialize() failed", 3, mt5.last_error())


def ensure_symbol(symbol):
    if not mt5.symbol_select(symbol, True):
        fail(f"Unable to select symbol: {symbol}", 4, mt5.last_error())


def tick_dict(tick):
    if tick is None:
        return None
    d = tick._asdict()
    return {
        "time": iso_utc(d.get("time")),
        "time_msc": d.get("time_msc"),
        "bid": d.get("bid"),
        "ask": d.get("ask"),
        "last": d.get("last"),
        "volume": d.get("volume"),
        "volume_real": d.get("volume_real"),
        "flags": d.get("flags"),
    }


def candles(symbol, timeframe, count, closed_only):
    tf = TIMEFRAMES.get(timeframe)
    if tf is None:
        fail(f"Unsupported timeframe: {timeframe}", 5)
    ensure_symbol(symbol)
    start_pos = 1 if closed_only else 0
    rates = mt5.copy_rates_from_pos(symbol, tf, start_pos, int(count))
    if rates is None:
        fail("copy_rates_from_pos failed", 6, mt5.last_error())
    rows = []
    for r in rates:
        rows.append({
            "time": iso_utc(r["time"]),
            "open": float(r["open"]),
            "high": float(r["high"]),
            "low": float(r["low"]),
            "close": float(r["close"]),
            "tick_volume": int(r["tick_volume"]),
            "spread": int(r["spread"]),
            "real_volume": int(r["real_volume"]),
        })
    rows.sort(key=lambda x: x["time"])
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "closed_only": bool(closed_only),
        "count": len(rows),
        "candles": rows,
    }


def main():
    if len(sys.argv) < 2:
        fail("Missing action")
    action = sys.argv[1]
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    initialize()
    try:
        if action == "status":
            terminal = mt5.terminal_info()
            account = mt5.account_info()
            symbol = payload.get("symbol") or os.getenv("MT5_SYMBOL", "XAUUSD_l")
            result = {
                "connected": terminal is not None and account is not None,
                "mt5_version": mt5.version(),
                "terminal": None if terminal is None else {
                    "connected": terminal.connected,
                    "trade_allowed": terminal.trade_allowed,
                    "tradeapi_disabled": terminal.tradeapi_disabled,
                    "company": terminal.company,
                    "name": terminal.name,
                    "path": terminal.path,
                    "data_path": terminal.data_path,
                },
                "account": None if account is None else {
                    "server": account.server,
                    "currency": account.currency,
                    "leverage": account.leverage,
                    "balance": account.balance,
                    "equity": account.equity,
                    "margin": account.margin,
                    "margin_free": account.margin_free,
                    "margin_level": account.margin_level,
                    "trade_allowed": account.trade_allowed,
                    "trade_expert": account.trade_expert,
                },
                "default_symbol": symbol,
            }
        elif action == "symbol_info":
            symbol = payload["symbol"]
            ensure_symbol(symbol)
            info = mt5.symbol_info(symbol)
            if info is None:
                fail(f"symbol_info returned None for {symbol}", 7, mt5.last_error())
            d = info._asdict()
            keys = [
                "name", "description", "path", "digits", "point", "trade_mode",
                "trade_contract_size", "volume_min", "volume_max", "volume_step",
                "spread", "spread_float", "currency_base", "currency_profit", "currency_margin",
                "trade_tick_value", "trade_tick_size", "trade_stops_level", "trade_freeze_level",
            ]
            result = {k: d.get(k) for k in keys}
        elif action == "tick":
            symbol = payload["symbol"]
            ensure_symbol(symbol)
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                fail(f"No tick available for {symbol}", 8, mt5.last_error())
            result = {"symbol": symbol, **tick_dict(tick)}
        elif action == "candles":
            result = candles(
                payload["symbol"],
                payload["timeframe"],
                payload.get("count", 500),
                payload.get("closed_only", True),
            )
        elif action == "snapshot":
            symbol = payload["symbol"]
            ensure_symbol(symbol)
            tick = mt5.symbol_info_tick(symbol)
            result = {
                "symbol": symbol,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "tick": tick_dict(tick),
                "timeframes": {},
            }
            for tf in payload.get("timeframes", ["H1", "M15", "M5", "M1"]):
                result["timeframes"][tf] = candles(
                    symbol,
                    tf,
                    payload.get("bars_per_timeframe", 300),
                    payload.get("closed_only", True),
                )
        elif action == "account_info":
            account = mt5.account_info()
            if account is None:
                fail("account_info returned None", 9, mt5.last_error())
            d = account._asdict()
            keys = [
                "server", "currency", "leverage", "balance", "credit", "profit", "equity",
                "margin", "margin_free", "margin_level", "margin_so_mode", "margin_so_call",
                "margin_so_so", "trade_allowed", "trade_expert",
            ]
            result = {k: d.get(k) for k in keys}
        elif action == "positions":
            symbol = payload.get("symbol")
            positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            if positions is None:
                fail("positions_get failed", 10, mt5.last_error())
            result = {
                "symbol_filter": symbol,
                "count": len(positions),
                "positions": [
                    {
                        "ticket": p.ticket,
                        "time": iso_utc(p.time),
                        "type": "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL",
                        "magic": p.magic,
                        "symbol": p.symbol,
                        "volume": p.volume,
                        "price_open": p.price_open,
                        "sl": p.sl,
                        "tp": p.tp,
                        "price_current": p.price_current,
                        "swap": p.swap,
                        "profit": p.profit,
                        "comment": p.comment,
                    }
                    for p in positions
                ],
            }
        else:
            fail(f"Unknown action: {action}", 11)

        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
