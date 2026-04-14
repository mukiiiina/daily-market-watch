#!/usr/bin/env python3
"""Check price alerts against live market data."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def run_script(name: str, *args) -> dict:
    cmd = [sys.executable, str(SCRIPT_DIR / name), *args]
    result = subprocess.run(cmd, capture_output=True)
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    if result.returncode != 0:
        return {"error": stderr.strip() or "Unknown error"}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"raw": stdout.strip()}


def cmd_check(args: argparse.Namespace) -> int:
    portfolio = run_script("portfolio.py", "--json", "list")
    if "error" in portfolio:
        print(json.dumps({"error": portfolio["error"]}, ensure_ascii=False))
        return 1

    config = run_script("config.py", "--json", "list")
    if "error" in config:
        print(json.dumps({"error": config["error"]}, ensure_ascii=False))
        return 1

    alert_mode = config.get("alert_mode", "enabled")
    if alert_mode == "disabled":
        print(json.dumps({"alerts": [], "message": "Alert mode is disabled"}, ensure_ascii=False))
        return 0

    index_threshold = config.get("index_volatility_threshold", 1.0)

    triggered = []

    # 1) Index volatility check
    indices_data = run_script("fetch_market.py", "--json", "indices")
    if "error" not in indices_data and isinstance(indices_data, list):
        for idx in indices_data:
            pct = idx.get("change_pct") or 0
            if abs(pct) >= index_threshold:
                triggered.append({
                    "type": "index",
                    "code": idx.get("code"),
                    "name": idx.get("name"),
                    "price": idx.get("price"),
                    "change_pct": pct,
                    "threshold": index_threshold,
                    "direction": "rise" if pct > 0 else "fall",
                })

    # 2) Stock alerts
    stocks = portfolio.get("stocks", [])
    if stocks:
        codes = ",".join([s["code"] for s in stocks if s.get("code")])
        quotes = run_script("fetch_market.py", "--json", "quotes", codes)
        if isinstance(quotes, list):
            code_to_quote = {q["code"]: q for q in quotes}
            for s in stocks:
                code = s.get("code")
                alerts = s.get("alerts", {})
                if not alerts:
                    continue
                q = code_to_quote.get(code, {})
                pct = q.get("change_pct")
                if pct is None:
                    continue
                rise = alerts.get("rise")
                fall = alerts.get("fall")
                if rise is not None and pct >= rise:
                    triggered.append({
                        "type": "stock",
                        "code": code,
                        "name": s.get("name") or q.get("name"),
                        "price": q.get("price"),
                        "change_pct": pct,
                        "threshold": rise,
                        "direction": "rise",
                    })
                if fall is not None and pct <= fall:
                    triggered.append({
                        "type": "stock",
                        "code": code,
                        "name": s.get("name") or q.get("name"),
                        "price": q.get("price"),
                        "change_pct": pct,
                        "threshold": fall,
                        "direction": "fall",
                    })

    # 3) Fund alerts (using akshare fund estimates)
    funds = portfolio.get("funds", [])
    if funds:
        codes = ",".join([f["code"] for f in funds if f.get("code")])
        fund_data = run_script("fetch_market.py", "--json", "funds", "--codes", codes)
        if isinstance(fund_data, list):
            code_to_fund = {f.get("基金代码"): f for f in fund_data}
            for fd in funds:
                code = fd.get("code")
                alerts = fd.get("alerts", {})
                if not alerts:
                    continue
                info = code_to_fund.get(code, {})
                growth_str = info.get("交易日-估算数据-估算增长率", "")
                try:
                    pct = float(growth_str.replace("%", ""))
                except (ValueError, TypeError):
                    continue
                rise = alerts.get("rise")
                fall = alerts.get("fall")
                if rise is not None and pct >= rise:
                    triggered.append({
                        "type": "fund",
                        "code": code,
                        "name": fd.get("name") or info.get("基金名称"),
                        "estimated_growth": pct,
                        "threshold": rise,
                        "direction": "rise",
                    })
                if fall is not None and pct <= fall:
                    triggered.append({
                        "type": "fund",
                        "code": code,
                        "name": fd.get("name") or info.get("基金名称"),
                        "estimated_growth": pct,
                        "threshold": fall,
                        "direction": "fall",
                    })

    # Send webhook if configured and alerts triggered
    webhook = config.get("lark_webhook", "")
    if triggered and webhook:
        try:
            import requests
            lines = ["**\U0001f6a8 看盘预警提醒**", ""]
            for a in triggered:
                if a["type"] == "index":
                    lines.append(f"- **{a['name']}** 指数波动 {a['change_pct']:+.2f}%，超过阈值 {a['threshold']}%")
                elif a["type"] == "fund":
                    lines.append(f"- **{a['name']}({a['code']})** 估算涨跌 {a['estimated_growth']:+.2f}%，触及{'上涨' if a['direction']=='rise' else '下跌'}预警线")
                else:
                    lines.append(f"- **{a['name']}({a['code']})** 当前 {a['price']} 涨跌 {a['change_pct']:+.2f}%，触及{'上涨' if a['direction']=='rise' else '下跌'}预警线")
            lines.append("")
            lines.append("*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*")
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {"title": {"tag": "plain_text", "content": "每日看盘预警"}},
                    "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}}],
                },
            }
            requests.post(webhook, json=payload, timeout=10)
        except Exception:
            pass

    output = {"alerts": triggered, "count": len(triggered)}
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        if not triggered:
            print("暂无触发预警。")
        else:
            print(f"共触发 {len(triggered)} 条预警:")
            for a in triggered:
                if a["type"] == "index":
                    print(f"  [{a['name']}] 指数波动 {a['change_pct']:+.2f}%，超过阈值 {a['threshold']}%")
                elif a["type"] == "fund":
                    print(f"  [{a['name']}({a['code']})] 估算涨跌 {a['estimated_growth']:+.2f}%，触及{a['direction']=='rise' and '上涨' or '下跌'}预警线")
                else:
                    print(f"  [{a['name']}({a['code']})] 当前 {a['price']} 涨跌 {a['change_pct']:+.2f}%，触及{a['direction']=='rise' and '上涨' or '下跌'}预警线")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Alert checker")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="command", required=True)
    p_check = sub.add_parser("check", help="Check all alerts now")
    p_check.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
