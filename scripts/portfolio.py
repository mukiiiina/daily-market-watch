#!/usr/bin/env python3
"""Portfolio CRUD for stocks and funds."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".config" / "daily-market-watch"
PORTFOLIO_FILE = CONFIG_DIR / "portfolio.json"


def ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_portfolio() -> dict:
    ensure_dir()
    if not PORTFOLIO_FILE.exists():
        return {"version": 1, "stocks": [], "funds": []}
    with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_portfolio(data: dict):
    ensure_dir()
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_stock_code(code: str) -> str:
    code = code.strip().lower()
    if code.startswith(("sh", "sz", "bj")):
        return code
    if len(code) != 6:
        return code
    if code.startswith(("600", "601", "603", "605", "688", "689")):
        return f"sh{code}"
    if code.startswith(("000", "001", "002", "003", "300", "301")):
        return f"sz{code}"
    if code.startswith(("8", "4", "9")):
        return f"bj{code}"
    return f"sh{code}"


def cmd_add(args: argparse.Namespace) -> int:
    data = load_portfolio()
    if args.type == "stock":
        code = normalize_stock_code(args.code)
        # Remove existing entry with same code
        data["stocks"] = [s for s in data["stocks"] if s["code"] != code]
        entry = {
            "code": code,
            "name": args.name or "",
            "quantity": args.quantity or 0,
            "cost": args.cost or 0.0,
            "alerts": {},
        }
        if args.rise_alert is not None:
            entry["alerts"]["rise"] = args.rise_alert
        if args.fall_alert is not None:
            entry["alerts"]["fall"] = args.fall_alert
        data["stocks"].append(entry)
    else:
        code = args.code.strip()
        data["funds"] = [f for f in data["funds"] if f["code"] != code]
        entry = {
            "code": code,
            "name": args.name or "",
            "quantity": args.quantity or 0,
            "cost": args.cost or 0.0,
            "alerts": {},
        }
        if args.rise_alert is not None:
            entry["alerts"]["rise"] = args.rise_alert
        if args.fall_alert is not None:
            entry["alerts"]["fall"] = args.fall_alert
        data["funds"].append(entry)
    save_portfolio(data)
    print(json.dumps({"ok": True, "added": entry}, ensure_ascii=False))
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    data = load_portfolio()
    if args.type == "stock":
        code = normalize_stock_code(args.code)
        before = len(data["stocks"])
        data["stocks"] = [s for s in data["stocks"] if s["code"] != code]
        save_portfolio(data)
        print(json.dumps({"ok": True, "removed": before - len(data["stocks"])}, ensure_ascii=False))
    else:
        code = args.code.strip()
        before = len(data["funds"])
        data["funds"] = [f for f in data["funds"] if f["code"] != code]
        save_portfolio(data)
        print(json.dumps({"ok": True, "removed": before - len(data["funds"])}, ensure_ascii=False))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    data = load_portfolio()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("股票持仓:")
        for s in data["stocks"]:
            alerts = s.get("alerts", {})
            alert_str = ""
            if alerts:
                parts = []
                if "rise" in alerts:
                    parts.append(f"涨≥{alerts['rise']}%")
                if "fall" in alerts:
                    parts.append(f"跌≤{alerts['fall']}%")
                alert_str = f" 预警:({', '.join(parts)})"
            print(f"  {s['name']} ({s['code']}) 数量:{s['quantity']} 成本:{s['cost']}{alert_str}")
        print("基金持仓:")
        for f in data["funds"]:
            alerts = f.get("alerts", {})
            alert_str = ""
            if alerts:
                parts = []
                if "rise" in alerts:
                    parts.append(f"涨≥{alerts['rise']}%")
                if "fall" in alerts:
                    parts.append(f"跌≤{alerts['fall']}%")
                alert_str = f" 预警:({', '.join(parts)})"
            print(f"  {f['name']} ({f['code']}) 数量:{f['quantity']} 成本:{f['cost']}{alert_str}")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    save_portfolio({"version": 1, "stocks": [], "funds": []})
    print(json.dumps({"ok": True}, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Portfolio manager")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add holding")
    p_add.add_argument("type", choices=["stock", "fund"])
    p_add.add_argument("code", help="Stock/fund code")
    p_add.add_argument("--name", default="")
    p_add.add_argument("--quantity", type=int, default=0)
    p_add.add_argument("--cost", type=float, default=0.0)
    p_add.add_argument("--rise-alert", type=float, default=None)
    p_add.add_argument("--fall-alert", type=float, default=None)
    p_add.set_defaults(func=cmd_add)

    p_remove = sub.add_parser("remove", help="Remove holding")
    p_remove.add_argument("type", choices=["stock", "fund"])
    p_remove.add_argument("code", help="Stock/fund code")
    p_remove.set_defaults(func=cmd_remove)

    p_list = sub.add_parser("list", help="List holdings")
    p_list.set_defaults(func=cmd_list)

    p_clear = sub.add_parser("clear", help="Clear all holdings")
    p_clear.set_defaults(func=cmd_clear)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
