#!/usr/bin/env python3
"""Compute technical indicator signals for A-share, HK, and US stocks."""

import argparse
import json
import sys

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "akshare and pandas are required"}, ensure_ascii=False))
    sys.exit(1)


def normalize_code(raw: str) -> tuple[str, str]:
    lowered = raw.strip().lower()
    if lowered.startswith(("sh", "sz", "bj")):
        return ("a", lowered)
    if lowered.startswith("hk"):
        return ("hk", lowered[2:])
    if lowered.startswith("us"):
        return ("us", raw[2:].upper())
    if lowered.isalpha():
        return ("us", raw.upper())
    if lowered.isdigit() and len(lowered) == 5:
        return ("hk", lowered)
    if lowered.isdigit() and len(lowered) == 6:
        if lowered.startswith(("600", "601", "603", "605", "688", "689")):
            return ("a", f"sh{lowered}")
        if lowered.startswith(("000", "001", "002", "003", "300", "301")):
            return ("a", f"sz{lowered}")
        if lowered.startswith(("8", "4", "9")):
            return ("a", f"bj{lowered}")
        return ("a", f"sh{lowered}")
    return ("a", lowered)


def fetch_history(market: str, code: str) -> pd.DataFrame:
    if market == "a":
        return ak.stock_zh_a_daily(symbol=code)
    if market == "hk":
        return ak.stock_hk_daily(symbol=code)
    if market == "us":
        df = ak.stock_us_daily(symbol=code)
        if "date" in df.columns and not pd.api.types.is_string_dtype(df["date"]):
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        return df
    return pd.DataFrame()


def compute_signals(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 30:
        return {"error": "Insufficient historical data"}

    df = df.sort_values("date").reset_index(drop=True)
    close = df["close"]

    # Moving averages
    ma5 = close.rolling(window=5).mean()
    ma10 = close.rolling(window=10).mean()
    ma20 = close.rolling(window=20).mean()

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()

    # KDJ (9,3,3)
    low9 = df["low"].rolling(window=9).min()
    high9 = df["high"].rolling(window=9).max()
    rsv = (close - low9) / (high9 - low9) * 100
    rsv = rsv.fillna(50)
    k = rsv.ewm(alpha=1 / 3, adjust=False).mean()
    d = k.ewm(alpha=1 / 3, adjust=False).mean()
    j = 3 * k - 2 * d

    # RSI(6)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=6).mean()
    avg_loss = loss.rolling(window=6).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))

    idx = len(df) - 1
    prev = idx - 1

    signals = []

    # Trend
    if close.iloc[idx] > ma5.iloc[idx] > ma10.iloc[idx] > ma20.iloc[idx]:
        signals.append("多头排列")
    elif close.iloc[idx] < ma20.iloc[idx]:
        signals.append("跌破MA20")
    elif close.iloc[idx] > ma20.iloc[idx]:
        signals.append("站稳MA20")

    # MACD cross
    if dif.iloc[prev] <= dea.iloc[prev] and dif.iloc[idx] > dea.iloc[idx]:
        signals.append("MACD金叉")
    elif dif.iloc[prev] >= dea.iloc[prev] and dif.iloc[idx] < dea.iloc[idx]:
        signals.append("MACD死叉")

    # KDJ cross
    if k.iloc[prev] <= d.iloc[prev] and k.iloc[idx] > d.iloc[idx] and k.iloc[idx] < 20:
        signals.append("KDJ金叉")
    elif k.iloc[prev] >= d.iloc[prev] and k.iloc[idx] < d.iloc[idx] and k.iloc[idx] > 80:
        signals.append("KDJ死叉")

    # RSI
    r = rsi.iloc[idx]
    if pd.notna(r):
        if r > 70:
            signals.append("RSI超买")
        elif r < 30:
            signals.append("RSI超卖")

    return {
        "price": round(float(close.iloc[idx]), 2),
        "ma5": round(float(ma5.iloc[idx]), 2),
        "ma10": round(float(ma10.iloc[idx]), 2),
        "ma20": round(float(ma20.iloc[idx]), 2),
        "macd_dif": round(float(dif.iloc[idx]), 3),
        "macd_dea": round(float(dea.iloc[idx]), 3),
        "kdj_k": round(float(k.iloc[idx]), 2),
        "kdj_d": round(float(d.iloc[idx]), 2),
        "rsi6": round(float(r), 2) if pd.notna(r) else None,
        "summary": " | ".join(signals) if signals else "趋势中性",
    }


def main():
    parser = argparse.ArgumentParser(description="Technical indicator signals")
    parser.add_argument("code", help="Stock code (e.g. 600519, hk00700, TSLA)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    market, code = normalize_code(args.code)
    df = fetch_history(market, code)
    result = compute_signals(df)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for k, v in result.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
