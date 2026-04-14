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


def send_lark_webhook(webhook_url: str, title: str, content: str, template: str = "blue"):
    try:
        import requests
        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": template,
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


def fetch_breadth() -> dict:
    data = run_script("fetch_market.py", "--json", "breadth")
    return data if isinstance(data, dict) else {}


def fetch_tech_signals(code: str) -> dict:
    data = run_script("tech_signals.py", "--json", code)
    return data if isinstance(data, dict) else {}


def fetch_news_monitor(code: str, name: str = "") -> dict:
    data = run_script("news_monitor.py", "--json", code, "--name", name or code)
    return data if isinstance(data, dict) else {}


def format_change(pct):
    if pct is None:
        return "-"
    return f"{pct:+.2f}%"


def market_label(code: str) -> str:
    if code.startswith(("sh", "sz", "bj")):
        return "A股"
    if code.startswith("hk"):
        return "港股"
    if code.startswith("us"):
        return "美股"
    return ""


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

    # Market breadth
    if detail == "detailed":
        breadth_data = fetch_breadth()
        b = breadth_data.get("breadth")
        if b and "_error" not in b:
            lines.append("## 市场情绪")
            lines.append(f"- 涨跌分布：涨 {b['up']} / 跌 {b['down']} / 平 {b['flat']} | 涨停 {b['limit_up']} | 跌停 {b['limit_down']} | 等权涨幅 {b['avg_change']:+.2f}%")
            nb = breadth_data.get("northbound")
            if nb:
                nb_str = f"{nb['net_inflow']/1e4:.2f}亿" if abs(nb['net_inflow']) >= 1e4 else f"{nb['net_inflow']:.2f}万"
                lines.append(f"- 北向资金 ({nb['date']}): 净流入 {nb_str}")
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
                qty = s.get("quantity", 0)
                cost = s.get("cost", 0) or 0
                holding_pnl = ((price or 0) - cost) * qty if cost else 0.0
                lbl = market_label(s["code"])
                suffix = f" [{lbl}]" if lbl else ""
                if s["code"].startswith("us"):
                    suffix += "（美股为隔夜收盘数据）"
                pnl_str = f" 持仓盈亏 {holding_pnl:+.2f}" if cost else ""
                news_info = fetch_news_monitor(s["code"], s.get("name", "")) if detail == "detailed" else {}
                news_str = ""
                if news_info and news_info.get("news"):
                    sentiment = news_info.get("sentiment", "neutral")
                    suggestion = news_info.get("suggestion", "")
                    counts = news_info.get("sentiment_counts", {})
                    sc = f"(情绪: 正{counts.get('positive',0)} 负{counts.get('negative',0)} 中{counts.get('neutral',0)})"
                    news_str = f"\n  新闻{s['name']}: {suggestion} {sc}"
                lines.append(f"- {s['name']} ({s['code']}): 昨收 {prev or '-'}，当前 {price or '-'}{pnl_str}，{format_change(q.get('change_pct'))}{suffix}{news_str}")
        if funds:
            fund_codes = [f["code"] for f in funds]
            fund_data = fetch_funds(fund_codes)
            code_map = {f.get("基金代码"): f for f in fund_data}
            for f in funds:
                info = code_map.get(f["code"], {})
                growth = info.get("交易日-估算数据-估算增长率", "-")
                nav = info.get("交易日-公布数据-单位净值", 0)
                try:
                    nav_f = float(nav)
                except (ValueError, TypeError):
                    nav_f = 0.0
                qty = f.get("quantity", 0)
                cost = f.get("cost", 0) or 0
                holding_pnl = (nav_f - cost) * qty if cost else 0.0
                pnl_str = f" 持仓盈亏 {holding_pnl:+.2f}" if cost else ""
                lines.append(f"- {f['name']} ({f['code']}): 估算涨跌 {growth}{pnl_str}")
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
                code = idx.get("code", "").lower()
                # A-share index volume is in "hand" (手), 1 hand = 100 shares
                real_vol = vol * 100 if code.startswith(("sh", "sz", "bj")) else vol
                unit = "手" if code.startswith(("sh", "sz", "bj")) else "股"
                if real_vol >= 1e8:
                    vol_str = f"{real_vol/1e8:.2f}亿{unit}"
                else:
                    vol_str = f"{real_vol/1e4:.2f}万{unit}"
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

    # Market breadth
    if detail == "detailed":
        breadth_data = fetch_breadth()
        b = breadth_data.get("breadth")
        if b and "_error" not in b:
            lines.append("## 市场情绪")
            lines.append(f"- 涨跌分布：涨 {b['up']} / 跌 {b['down']} / 平 {b['flat']} | 涨停 {b['limit_up']} | 跌停 {b['limit_down']} | 等权涨幅 {b['avg_change']:+.2f}%")
            nb = breadth_data.get("northbound")
            if nb:
                nb_str = f"{nb['net_inflow']/1e4:.2f}亿" if abs(nb['net_inflow']) >= 1e4 else f"{nb['net_inflow']:.2f}万"
                lines.append(f"- 北向资金 ({nb['date']}): 净流入 {nb_str}")
            lines.append("")

    # Holdings summary
    lines.append("## 持仓总结")
    stocks = portfolio.get("stocks", [])
    funds = portfolio.get("funds", [])
    if not stocks and not funds:
        lines.append("暂无持仓。")
    else:
        total_day_pnl = 0.0
        total_pnl = 0.0
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
                cost = s.get("cost", 0) or 0
                day_pnl = (price - prev) * qty
                holding_pnl = (price - cost) * qty if cost else 0.0
                total_day_pnl += day_pnl
                total_pnl += holding_pnl
                lbl = market_label(s["code"])
                suffix = f" [{lbl}]" if lbl else ""
                if s["code"].startswith("us"):
                    suffix += "（美股隔夜收盘）"
                cost_str = f"，成本 {cost:.2f}" if cost else ""
                pnl_str = f"{holding_pnl:+.2f}" if cost else "-"
                tech = fetch_tech_signals(s["code"]) if detail == "detailed" else {}
                tech_str = f" | {tech.get('summary', '')}" if tech and tech.get("summary") and "error" not in tech else ""
                news_info = fetch_news_monitor(s["code"], s.get("name", "")) if detail == "detailed" else {}
                news_str = ""
                if news_info and news_info.get("news"):
                    sentiment = news_info.get("sentiment", "neutral")
                    suggestion = news_info.get("suggestion", "")
                    counts = news_info.get("sentiment_counts", {})
                    sc = f"(情绪: 正{counts.get('positive',0)} 负{counts.get('negative',0)} 中{counts.get('neutral',0)})"
                    news_str = f"\n  新闻{s['name']}: {suggestion} {sc}"
                lines.append(f"- {s['name']} ({s['code']}): 收 {price or '-'}{cost_str}，{format_change(q.get('change_pct'))}，当日 {day_pnl:+.2f} / 持仓 {pnl_str}{suffix}{tech_str}{news_str}")
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
                cost = f.get("cost", 0) or 0
                holding_pnl = (nav_f - cost) * qty if cost else 0.0
                total_day_pnl += day_pnl
                total_pnl += holding_pnl
                cost_str = f"，成本 {cost:.3f}" if cost else ""
                pnl_str = f"{holding_pnl:+.2f}" if cost else "-"
                lines.append(f"- {f['name']} ({f['code']}): 估算涨跌 {growth_str}{cost_str}，当日 {day_pnl:+.2f} / 持仓 {pnl_str}")
        lines.append(f"")
        lines.append(f"**当日总预估盈亏: {total_day_pnl:+.2f}  |  持仓总盈亏: {total_pnl:+.2f}**")
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
                price = q.get("price") or 0
                qty = s.get("quantity", 0)
                cost = s.get("cost", 0) or 0
                holding_pnl = (price - cost) * qty if cost else 0.0
                lbl = market_label(s["code"])
                suffix = f" [{lbl}]" if lbl else ""
                if s["code"].startswith("us"):
                    suffix += "（隔夜收盘）"
                pnl_str = f"  持仓盈亏 {holding_pnl:+.2f}" if cost else ""
                lines.append(f"- {s['name']} ({s['code']}): {q.get('price', '-')}  {format_change(q.get('change_pct'))}{pnl_str}{suffix}")
        if funds:
            fund_data = fetch_funds([f["code"] for f in funds])
            code_map = {f.get("基金代码"): f for f in fund_data}
            for f in funds:
                info = code_map.get(f["code"], {})
                growth = info.get("交易日-估算数据-估算增长率", "-")
                nav = info.get("交易日-公布数据-单位净值", 0)
                try:
                    nav_f = float(nav)
                except (ValueError, TypeError):
                    nav_f = 0.0
                qty = f.get("quantity", 0)
                cost = f.get("cost", 0) or 0
                holding_pnl = (nav_f - cost) * qty if cost else 0.0
                pnl_str = f"  持仓盈亏 {holding_pnl:+.2f}" if cost else ""
                lines.append(f"- {f['name']} ({f['code']}): 估算 {growth}{pnl_str}")
        lines.append("")

    lines.append("*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*")
    return "\n".join(lines)


def _handle_report_output(kind: str, report: str, config: dict):
    save_report(kind, report)
    webhook = config.get("lark_webhook", "")
    if webhook:
        title_map = {"morning": "早间盘前预热", "evening": "盘后总结", "intraday": "盘中快照"}
        template_map = {"morning": "green", "evening": "indigo", "intraday": "orange"}
        send_lark_webhook(webhook, title_map.get(kind, kind), report, template_map.get(kind, "blue"))
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
