#!/usr/bin/env python3
"""Generate morning, intraday, and evening market watch reports."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
HISTORY_DIR = Path.home() / ".config" / "daily-market-watch" / "history"


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


def ensure_history_dir():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def save_report(kind: str, content: str):
    ensure_history_dir()
    today = datetime.now().strftime("%Y%m%d")
    file_path = HISTORY_DIR / f"{kind}_{today}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def send_lark_webhook(webhook_url: str, title: str, content: str):
    try:
        import requests
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": content},
                    }
                ],
            },
        }
        requests.post(webhook_url, json=payload, timeout=10)
    except Exception:
        pass


def load_config() -> dict:
    return run_script("config.py", "--json", "list")


def load_portfolio() -> dict:
    return run_script("portfolio.py", "--json", "list")


def fetch_indices() -> list:
    data = run_script("fetch_market.py", "--json", "indices")
    return data if isinstance(data, list) else []


def fetch_quotes(codes: list[str]) -> list:
    if not codes:
        return []
    data = run_script("fetch_market.py", "--json", "quotes", ",".join(codes))
    return data if isinstance(data, list) else []


def fetch_sectors(top: int = 5) -> list:
    data = run_script("fetch_market.py", "--json", "sectors", "--top", str(top))
    return data if isinstance(data, list) else []


def fetch_funds(codes: list[str]) -> list:
    if not codes:
        return []
    data = run_script("fetch_market.py", "--json", "funds", "--codes", ",".join(codes))
    return data if isinstance(data, list) else []


def format_change(pct):
    if pct is None:
        return "-"
    return f"{pct:+.2f}%"


def build_index_summary(indices: list) -> str:
    parts = []
    for idx in indices:
        parts.append(f"{idx.get('name')} {format_change(idx.get('change_pct'))}")
    return "，".join(parts)


def build_morning_report(config: dict, portfolio: dict, indices: list, sectors: list) -> str:
    detail = config.get("detail_level", "detailed")
    lines = []
    now = datetime.now().strftime("%m月%d日 %H:%M")
    lines.append(f"# 早间盘前预热 ({now})")
    lines.append("")

    # Market review (based on current pre-market / previous close context)
    lines.append("## 昨日市场回顾")
    if indices:
        lines.append(f"昨日大盘：{build_index_summary(indices)}。主要指数前收情况如下：")
        for idx in indices:
            lines.append(f"- {idx['name']}: 昨收 {idx.get('prev_close', '-')}，当前预估 {idx.get('price', '-')}")
    else:
        lines.append("暂无法获取大盘数据。")
    lines.append("")

    # Sectors
    if detail == "detailed" and sectors:
        lines.append("## 热门板块动向")
        for s in sectors[:5]:
            lines.append(f"- {s['name']}: 涨跌 {s['change_pct']:+.2f}%  领涨 {s['leading_name']}({s['leading_change_pct']:+.2f}%)")
        lines.append("")

    # Holdings pre-market
    lines.append("## 持仓盘前提示")
    stocks = portfolio.get("stocks", [])
    funds = portfolio.get("funds", [])
    if not stocks and not funds:
        lines.append("暂无持仓。请使用 `portfolio.py add` 添加持仓。")
    else:
        if stocks:
            stock_codes = [s["code"] for s in stocks]
            quotes = fetch_quotes(stock_codes)
            code_map = {q["code"]: q for q in quotes}
            for s in stocks:
                q = code_map.get(s["code"], {})
                prev = q.get("prev_close")
                price = q.get("price")
                lines.append(f"- {s['name']} ({s['code']}): 昨收 {prev or '-'}，当前 {price or '-'}，{format_change(q.get('change_pct'))}")
        if funds:
            fund_codes = [f["code"] for f in funds]
            fund_data = fetch_funds(fund_codes)
            code_map = {f.get("基金代码"): f for f in fund_data}
            for f in funds:
                info = code_map.get(f["code"], {})
                growth = info.get("交易日-估算数据-估算增长率", "-")
                lines.append(f"- {f['name']} ({f['code']}): 估算涨跌 {growth}")
    lines.append("")

    # Watch focus
    lines.append("## 今日看盘重点")
    if indices:
        max_idx = max(indices, key=lambda x: abs(x.get("change_pct") or 0))
        lines.append(f"- 关注 {max_idx['name']} 开盘后的方向选择（当前波动预期 {format_change(max_idx.get('change_pct'))}）。")
    lines.append("- 关注持仓个股是否出现利好/利空消息及集合竞价异动。")
    lines.append("- 盘中如遇大盘波动超过 1%，注意控制仓位风险。")
    lines.append("")

    lines.append("*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*")
    return "\n".join(lines)


def build_evening_report(config: dict, portfolio: dict, indices: list, sectors: list) -> str:
    detail = config.get("detail_level", "detailed")
    lines = []
    now = datetime.now().strftime("%m月%d日 %H:%M")
    lines.append(f"# 盘后总结 ({now})")
    lines.append("")

    # Market summary
    lines.append("## 当日大盘总结")
    if indices:
        lines.append(f"今日收盘：{build_index_summary(indices)}。")
        for idx in indices:
            vol = idx.get("volume")
            vol_str = "-"
            if vol is not None:
                real_vol = vol * 100
                if real_vol >= 1e8:
                    vol_str = f"{real_vol/1e8:.2f}亿手"
                else:
                    vol_str = f"{real_vol/1e4:.2f}万手"
            lines.append(f"- {idx['name']}: 收 {idx.get('price', '-')}，成交 {vol_str}")
    else:
        lines.append("暂无法获取大盘数据。")
    lines.append("")

    if detail == "detailed" and sectors:
        lines.append("## 板块资金流向")
        for s in sectors[:5]:
            amount = s.get('amount', 0)
            amount_str = f"{amount/1e8:.2f}亿" if amount >= 1e8 else f"{amount/1e4:.2f}万"
            lines.append(f"- {s['name']}: 涨跌 {s['change_pct']:+.2f}%  成交额 {amount_str}  领涨 {s['leading_name']}({s['leading_change_pct']:+.2f}%)")
        lines.append("")

    # Holdings summary
    lines.append("## 持仓总结")
    stocks = portfolio.get("stocks", [])
    funds = portfolio.get("funds", [])
    if not stocks and not funds:
        lines.append("暂无持仓。")
    else:
        total_day_pnl = 0.0
        if stocks:
            stock_codes = [s["code"] for s in stocks]
            quotes = fetch_quotes(stock_codes)
            code_map = {q["code"]: q for q in quotes}
            lines.append("### 股票")
            for s in stocks:
                q = code_map.get(s["code"], {})
                price = q.get("price") or 0
                prev = q.get("prev_close") or price
                qty = s.get("quantity", 0)
                day_pnl = (price - prev) * qty
                total_day_pnl += day_pnl
                lines.append(f"- {s['name']} ({s['code']}): 收 {price or '-'}，{format_change(q.get('change_pct'))}，当日预估盈亏 {day_pnl:+.2f}")
        if funds:
            fund_codes = [f["code"] for f in funds]
            fund_data = fetch_funds(fund_codes)
            code_map = {f.get("基金代码"): f for f in fund_data}
            lines.append("### 基金")
            for f in funds:
                info = code_map.get(f["code"], {})
                growth_str = info.get("交易日-估算数据-估算增长率", "0%")
                try:
                    growth = float(growth_str.replace("%", "")) / 100
                except (ValueError, TypeError):
                    growth = 0.0
                qty = f.get("quantity", 0)
                nav = info.get("交易日-公布数据-单位净值", 0)
                try:
                    nav_f = float(nav)
                except (ValueError, TypeError):
                    nav_f = 0.0
                day_pnl = nav_f * qty * growth
                total_day_pnl += day_pnl
                lines.append(f"- {f['name']} ({f['code']}): 估算涨跌 {growth_str}，当日预估盈亏 {day_pnl:+.2f}")
        lines.append(f"")
        lines.append(f"**当日总预估盈亏: {total_day_pnl:+.2f}**")
    lines.append("")

    # Tomorrow outlook (lightweight, no professional advice)
    lines.append("## 明日看盘预判")
    if indices:
        avg_change = sum(i.get("change_pct", 0) or 0 for i in indices) / len(indices)
        if avg_change > 1:
            lines.append("- 今日市场情绪偏强，明日可关注量能能否持续，谨防冲高回落。")
        elif avg_change < -1:
            lines.append("- 今日市场承压，明日关注下方支撑力度，宜控制仓位观望。")
        else:
            lines.append("- 今日市场震荡整理，明日或维持结构性行情，关注热点轮动。")
    lines.append("- 晚间关注美股走势及政策/行业公告，可能影响次日开盘情绪。")
    lines.append("")

    lines.append("*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*")
    return "\n".join(lines)


def build_intraday_report(config: dict, portfolio: dict, indices: list) -> str:
    lines = []
    now = datetime.now().strftime("%m月%d日 %H:%M")
    lines.append(f"# 盘中快照 ({now})")
    lines.append("")

    if indices:
        lines.append("## 大盘")
        for idx in indices:
            lines.append(f"- {idx['name']}: {idx.get('price', '-')}  {format_change(idx.get('change_pct'))}")
        lines.append("")

    stocks = portfolio.get("stocks", [])
    funds = portfolio.get("funds", [])
    if stocks or funds:
        lines.append("## 持仓")
        if stocks:
            quotes = fetch_quotes([s["code"] for s in stocks])
            code_map = {q["code"]: q for q in quotes}
            for s in stocks:
                q = code_map.get(s["code"], {})
                lines.append(f"- {s['name']} ({s['code']}): {q.get('price', '-')}  {format_change(q.get('change_pct'))}")
        if funds:
            fund_data = fetch_funds([f["code"] for f in funds])
            code_map = {f.get("基金代码"): f for f in fund_data}
            for f in funds:
                info = code_map.get(f["code"], {})
                growth = info.get("交易日-估算数据-估算增长率", "-")
                lines.append(f"- {f['name']} ({f['code']}): 估算 {growth}")
        lines.append("")

    lines.append("*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*")
    return "\n".join(lines)


def _handle_report_output(kind: str, report: str, config: dict):
    save_report(kind, report)
    webhook = config.get("lark_webhook", "")
    if webhook:
        title_map = {"morning": "早间盘前预热", "evening": "盘后总结", "intraday": "盘中快照"}
        send_lark_webhook(webhook, title_map.get(kind, kind), report)
    print(report)


def cmd_morning(args: argparse.Namespace) -> int:
    config = load_config()
    portfolio = load_portfolio()
    indices = fetch_indices()
    sectors = fetch_sectors(5)
    report = build_morning_report(config, portfolio, indices, sectors)
    _handle_report_output("morning", report, config)
    return 0


def cmd_evening(args: argparse.Namespace) -> int:
    config = load_config()
    portfolio = load_portfolio()
    indices = fetch_indices()
    sectors = fetch_sectors(5)
    report = build_evening_report(config, portfolio, indices, sectors)
    _handle_report_output("evening", report, config)
    return 0


def cmd_intraday(args: argparse.Namespace) -> int:
    config = load_config()
    portfolio = load_portfolio()
    indices = fetch_indices()
    report = build_intraday_report(config, portfolio, indices)
    _handle_report_output("intraday", report, config)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Report generator")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("morning", help="Generate pre-market morning report").set_defaults(func=cmd_morning)
    sub.add_parser("evening", help="Generate post-market evening report").set_defaults(func=cmd_evening)
    sub.add_parser("intraday", help="Generate intraday snapshot report").set_defaults(func=cmd_intraday)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
