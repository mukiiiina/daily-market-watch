#!/usr/bin/env python3
"""
Fetch real-time A-share market data.
Supports indices, individual stocks, funds, and sector rankings.
Primary: Tencent Finance API (stable, no key)
Fallback: AKShare (richer data, may be blocked by proxy)
"""

import argparse
import json
import re
import sys
from typing import Optional

try:
    import requests
except ImportError:
    print("Missing dependency: requests. Run: pip install requests", file=sys.stderr)
    sys.exit(1)


def _tencent_url(codes: list[str]) -> str:
    return f"http://qt.gtimg.cn/q={','.join(codes)}"


def _parse_tencent_response(text: str) -> dict:
    """Parse Tencent qt.gtimg.cn response."""
    text = text.strip()
    pattern = r'v_([a-zA-Z0-9]+)="([^"]*)";'
    results = {}
    for code, data in re.findall(pattern, text):
        if not data:
            continue
        fields = data.split("~")
        def _f(idx):
            if len(fields) <= idx or not fields[idx]:
                return None
            try:
                return float(fields[idx])
            except ValueError:
                return None

        # Fields reference (verified against Tencent qt.gtimg.cn 2025-04):
        # 1: name, 2: code, 3: price, 4: prev_close, 5: open,
        # 6: volume, 31: change, 32: change_pct, 33: high, 34: low,
        # 37: amount, 38: turnover_rate(%), 39: pe, 46: pb (A-share only)
        results[code] = {
            "code": code,
            "name": fields[1] if len(fields) > 1 else "",
            "price": _f(3),
            "prev_close": _f(4),
            "open": _f(5),
            "volume": _f(6),
            "change": _f(31),
            "change_pct": _f(32),
            "high": _f(33),
            "low": _f(34),
            "amount": _f(37),
            "turnover_rate": _f(38),
            "pe": _f(39),
            "pb": _f(46),
        }
    return results


def fetch_tencent(codes: list[str]) -> dict:
    if not codes:
        return {}
    url = _tencent_url(codes)
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = "gbk"
        return _parse_tencent_response(resp.text)
    except Exception as e:
        return {"_error": str(e)}


def format_volume(vol: Optional[float], code: str = "") -> str:
    if vol is None:
        return "-"
    code = code.lower()
    # A-share volume is in "hand" (手), 1 hand = 100 shares
    if code.startswith(("sh", "sz", "bj")):
        real_vol = vol * 100
    else:
        real_vol = vol
    if real_vol >= 100_000_000:
        return f"{real_vol / 100_000_000:.2f}亿"
    if real_vol >= 10_000:
        return f"{real_vol / 10_000:.2f}万"
    return f"{real_vol:.0f}"


def format_amount(amount: Optional[float]) -> str:
    if amount is None:
        return "-"
    if amount >= 100_000_000:
        return f"{amount / 100_000_000:.2f}亿"
    if amount >= 10_000:
        return f"{amount / 10_000:.2f}万"
    return f"{amount:.0f}"


def normalize_security_code(code: str) -> str:
    """
    Normalize a security code to Tencent format.
    A-share:
      600519 -> sh600519
      000001 -> sz000001
    HK:
      00700  -> hk00700
      5-digit numbers treated as HK by default
    US:
      TSLA   -> usTSLA
      AAPL   -> usAAPL
    """
    raw = code.strip()
    lowered = raw.lower()
    if lowered.startswith(("sh", "sz", "bj", "hk")):
        return lowered
    # Already has US prefix: preserve ticker case (e.g. usTSLA -> usTSLA)
    if lowered.startswith("us"):
        return f"us{raw[2:]}"
    # Pure letters -> US (e.g. TSLA, AAPL)
    if lowered.isalpha():
        return f"us{raw.upper()}"
    # 5-digit numbers -> HK (e.g. 00700, 09988)
    if lowered.isdigit() and len(lowered) == 5:
        return f"hk{lowered}"
    # 6-digit numbers -> A-share
    if lowered.isdigit() and len(lowered) == 6:
        if lowered.startswith(("600", "601", "603", "605", "688", "689")):
            return f"sh{lowered}"
        if lowered.startswith(("000", "001", "002", "003", "300", "301")):
            return f"sz{lowered}"
        if lowered.startswith(("8", "4", "9")):
            return f"bj{lowered}"
        return f"sh{lowered}"
    # 4-digit or shorter numbers -> try HK first
    if lowered.isdigit():
        return f"hk{lowered.zfill(5)}"
    return lowered


def cmd_indices(args: argparse.Namespace) -> int:
    index_codes = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "hkHSI": "恒生指数",
        "usIXIC": "纳斯达克",
        "usDJI": "道琼斯",
        "usINX": "标普500",
    }
    data = fetch_tencent(list(index_codes.keys()))
    if "_error" in data:
        print(json.dumps({"error": data["_error"]}, ensure_ascii=False))
        return 1

    results = []
    for code, name in index_codes.items():
        item = data.get(code, {})
        results.append({
            "code": code,
            "name": name,
            "price": item.get("price"),
            "change": item.get("change"),
            "change_pct": item.get("change_pct"),
            "volume": item.get("volume"),
            "open": item.get("open"),
            "prev_close": item.get("prev_close"),
            "high": item.get("high"),
            "low": item.get("low"),
        })

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            vol_str = format_volume(r.get("volume"), r["code"])
            print(f"{r['name']} ({r['code']}): {r['price'] or '-'}  {r['change'] or 0:+.2f}  ({r['change_pct'] or 0:+.2f}%)  成交量:{vol_str}")
    return 0


def cmd_quote(args: argparse.Namespace) -> int:
    code = normalize_security_code(args.code)
    data = fetch_tencent([code])
    if "_error" in data:
        print(json.dumps({"error": data["_error"]}, ensure_ascii=False))
        return 1
    item = data.get(code)
    if not item:
        print(json.dumps({"error": f"No data for {code}"}, ensure_ascii=False))
        return 1
    if args.json:
        print(json.dumps(item, ensure_ascii=False, indent=2))
    else:
        vol_str = format_volume(item.get("volume"), item["code"])
        print(f"{item['name']} ({item['code']})")
        print(f"  当前价: {item['price'] or '-'}")
        print(f"  涨跌额: {item['change'] or 0:+.2f}")
        print(f"  涨跌幅: {item['change_pct'] or 0:+.2f}%")
        print(f"  今开: {item['open'] or '-'}")
        print(f"  昨收: {item['prev_close'] or '-'}")
        print(f"  最高: {item['high'] or '-'}")
        print(f"  最低: {item['low'] or '-'}")
        print(f"  成交量: {vol_str}")
        print(f"  换手率: {item['turnover_rate'] or '-'}%")
    return 0


def cmd_quotes(args: argparse.Namespace) -> int:
    codes = [normalize_security_code(c) for c in args.codes.split(",")]
    data = fetch_tencent(codes)
    if "_error" in data:
        print(json.dumps({"error": data["_error"]}, ensure_ascii=False))
        return 1
    results = []
    for c in codes:
        item = data.get(c)
        if item:
            results.append(item)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for item in results:
            vol_str = format_volume(item.get("volume"), item["code"])
            print(f"{item['name']} ({item['code']}): {item['price'] or '-'}  {item['change'] or 0:+.2f}  ({item['change_pct'] or 0:+.2f}%)  成交量:{vol_str}")
    return 0


def fetch_sina_sectors() -> list[dict]:
    """Fetch industry sector rankings from Sina Finance."""
    url = "http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class"
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = "gbk"
        text = resp.text
        # Extract JSON object from JavaScript by finding first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return []
        data = json.loads(text[start:end + 1])
        results = []
        for key, value in data.items():
            parts = value.split(",")
            if len(parts) < 10:
                continue
            try:
                results.append({
                    "code": parts[0],
                    "name": parts[1],
                    "stock_count": int(parts[2]) if parts[2] else 0,
                    "avg_price": float(parts[3]) if parts[3] else 0.0,
                    "change": float(parts[4]) if parts[4] else 0.0,
                    "change_pct": float(parts[5]) if parts[5] else 0.0,
                    "volume": float(parts[6]) if parts[6] else 0.0,
                    "amount": float(parts[7]) if parts[7] else 0.0,
                    "leading_code": parts[8],
                    "leading_change_pct": float(parts[9]) if parts[9] else 0.0,
                    "leading_price": float(parts[10]) if len(parts) > 10 and parts[10] else 0.0,
                    "leading_change": float(parts[11]) if len(parts) > 11 and parts[11] else 0.0,
                    "leading_name": parts[12] if len(parts) > 12 else "",
                })
            except (ValueError, IndexError):
                continue
        # Sort by change_pct descending
        results.sort(key=lambda x: x["change_pct"], reverse=True)
        return results
    except Exception:
        return []


def cmd_sectors(args: argparse.Namespace) -> int:
    records = fetch_sina_sectors()
    if not records:
        print(json.dumps({"error": "Unable to fetch sector data from Sina"}, ensure_ascii=False))
        return 1
    records = records[:args.top]
    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        for r in records:
            amount_str = "-"
            if r["amount"] >= 1e8:
                amount_str = f"{r['amount'] / 1e8:.2f}亿"
            elif r["amount"] >= 1e4:
                amount_str = f"{r['amount'] / 1e4:.2f}万"
            print(f"{r['name']}: 涨跌 {r['change_pct']:+.2f}%  成交额:{amount_str}  领涨:{r['leading_name']}({r['leading_change_pct']:+.2f}%)")
    return 0


def fetch_market_breadth() -> dict:
    try:
        import akshare as ak
        import pandas as pd
    except ImportError:
        return {"_error": "akshare or pandas not installed"}

    result: dict = {}
    # A-share market breadth
    try:
        df = ak.stock_zh_a_spot()
        change = pd.to_numeric(df["涨跌幅"], errors="coerce")
        up = int((change > 0).sum())
        down = int((change < 0).sum())
        flat = int((change == 0).sum())
        limit_up = int((change >= 9.9).sum())
        limit_down = int((change <= -9.9).sum())
        avg_change = float(change.mean())
        result["breadth"] = {
            "up": up,
            "down": down,
            "flat": flat,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "avg_change": round(avg_change, 2),
        }
    except Exception as e:
        result["breadth"] = {"_error": str(e)}

    # Northbound capital (historical daily, fallback to latest valid row)
    try:
        df_nb = ak.stock_hsgt_hist_em()
        col = "当日成交净买额"
        if col in df_nb.columns:
            df_nb[col] = pd.to_numeric(df_nb[col], errors="coerce")
            valid = df_nb[df_nb[col].notna()]
            if not valid.empty:
                latest = valid.iloc[-1]
                result["northbound"] = {
                    "date": str(latest["日期"]),
                    "net_inflow": float(latest[col]),
                }
    except Exception:
        pass
    return result


def cmd_breadth(args: argparse.Namespace) -> int:
    data = fetch_market_breadth()
    if "_error" in data:
        print(json.dumps({"error": data["_error"]}, ensure_ascii=False))
        return 1
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        b = data.get("breadth", {})
        if "_error" not in b:
            print(f"涨跌分布: 涨 {b['up']} | 跌 {b['down']} | 平 {b['flat']} | 涨停 {b['limit_up']} | 跌停 {b['limit_down']} | 等权涨幅 {b['avg_change']:+.2f}%")
        nb = data.get("northbound")
        if nb:
            nb_str = f"{nb['net_inflow']/1e4:.2f}亿" if abs(nb['net_inflow']) >= 1e4 else f"{nb['net_inflow']:.2f}万"
            print(f"北向资金 ({nb['date']}): 净流入 {nb_str}")
    return 0


def fetch_tencent_funds(codes: list[str]) -> dict:
    """Fetch fund NAV estimates via Tencent API (jj prefix)."""
    if not codes:
        return {}
    tencent_codes = [f"jj{c}" if not c.startswith("jj") else c for c in codes]
    url = f"http://qt.gtimg.cn/q={','.join(tencent_codes)}"
    try:
        resp = requests.get(url, timeout=15)
        resp.encoding = "gbk"
        text = resp.text.strip()
        pattern = r'v_(jj\d+)="([^"]*)";'
        results = {}
        for code, data in re.findall(pattern, text):
            if not data:
                continue
            fields = data.split("~")
            # Verified format: 0=code, 1=name, 2=est_nav, 5=nav, 7=est_growth_pct, 8=date
            raw_fund_code = code.replace("jj", "")
            results[raw_fund_code] = {
                "基金代码": raw_fund_code,
                "基金名称": fields[1] if len(fields) > 1 else "",
                "交易日-估算数据-估算值": fields[2] if len(fields) > 2 else "-",
                "交易日-公布数据-单位净值": fields[5] if len(fields) > 5 else "-",
                "交易日-估算数据-估算增长率": f"{fields[7]}%" if len(fields) > 7 and fields[7] else "-",
            }
        return results
    except Exception as e:
        return {"_error": str(e)}


def cmd_funds(args: argparse.Namespace) -> int:
    codes = [c.strip() for c in args.codes.split(",") if c.strip()] if args.codes else []
    if not codes:
        print(json.dumps({"error": "Please provide fund codes with --codes"}, ensure_ascii=False))
        return 1
    data = fetch_tencent_funds(codes)
    if "_error" in data:
        print(json.dumps({"error": data["_error"]}, ensure_ascii=False))
        return 1
    records = []
    for c in codes:
        item = data.get(c)
        if item:
            records.append(item)
    if args.json:
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        for r in records:
            est = r.get("交易日-估算数据-估算值", "-")
            growth = r.get("交易日-估算数据-估算增长率", "-")
            nav = r.get("交易日-公布数据-单位净值", "-")
            print(f"{r['基金名称']} ({r['基金代码']}): 估算净值 {est}  ({growth})  昨日净值 {nav}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch A-share market data")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p_indices = sub.add_parser("indices", help="Major indices")
    p_indices.set_defaults(func=cmd_indices)

    p_quote = sub.add_parser("quote", help="Single stock quote")
    p_quote.add_argument("code", help="Stock code (e.g. 600519 or sh600519)")
    p_quote.set_defaults(func=cmd_quote)

    p_quotes = sub.add_parser("quotes", help="Multiple stock quotes")
    p_quotes.add_argument("codes", help="Comma-separated stock codes")
    p_quotes.set_defaults(func=cmd_quotes)

    p_sectors = sub.add_parser("sectors", help="Industry sector rankings")
    p_sectors.add_argument("--top", type=int, default=10, help="Number of sectors to show")
    p_sectors.set_defaults(func=cmd_sectors)

    p_funds = sub.add_parser("funds", help="Fund NAV estimates")
    p_funds.add_argument("--top", type=int, default=10, help="Number of funds to show")
    p_funds.add_argument("--codes", default="", help="Comma-separated fund codes")
    p_funds.set_defaults(func=cmd_funds)

    p_breadth = sub.add_parser("breadth", help="A-share market breadth and northbound flow")
    p_breadth.set_defaults(func=cmd_breadth)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
