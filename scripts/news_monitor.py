#!/usr/bin/env python3
"""Fetch stock-related news and suggest position adjustments based on sentiment and price movement."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def run_script(name: str, *args) -> dict:
    cmd = [sys.executable, str(SCRIPT_DIR / name), *args]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return {"error": result.stderr.strip() or "Unknown error"}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw": result.stdout.strip()}


def fetch_news(symbol: str, name: str = "") -> list[dict]:
    try:
        import akshare as ak
    except ImportError:
        return []
    keywords = [symbol]
    if name:
        keywords.append(name)
    results = []
    for kw in keywords:
        try:
            df = ak.stock_news_em(kw)
            if df.empty:
                continue
            for i in range(min(5, len(df))):
                results.append({
                    "title": str(df.iloc[i, 1]),
                    "content": str(df.iloc[i, 2])[:200],
                    "date": str(df.iloc[i, 3]),
                    "source": str(df.iloc[i, 4]),
                    "url": str(df.iloc[i, 5]),
                })
            break
        except Exception:
            continue
    return results


def analyze_sentiment(title: str) -> str:
    title_lower = title.lower()
    bearish = ["下跌", "减持", "跌停", "亏损", "暴雷", "处罚", "退市", "监管", "调查", "业绩下滑", "裁员", "违约", "利空", "风险", "警告", "下滑", "跌破", "暴跌", "召回", "立案调查"]
    bullish = ["上涨", "增持", "涨停", "盈利", "增长", "突破", "利好", "收购", "合作", "超预期", "扩张", "订单", "获批", "创新高", "反弹", "分红", "回购"]
    b_score = sum(1 for w in bearish if w in title_lower)
    u_score = sum(1 for w in bullish if w in title_lower)
    if b_score > u_score:
        return "negative"
    if u_score > b_score:
        return "positive"
    return "neutral"


def suggest_position(change_pct: float | None, sentiment: str) -> str:
    pct = change_pct or 0
    if sentiment == "negative":
        if pct <= -3:
            return "出现利空新闻且跌幅较大，建议关注风险，必要时减仓观望。"
        elif pct <= -1:
            return "出现利空新闻，建议保持谨慎，观察后续走势。"
        else:
            return "出现利空新闻但股价暂未明显反应，建议密切关注。"
    elif sentiment == "positive":
        if pct >= 3:
            return "利好新闻推动股价上涨，情绪较高，建议谨慎追高，可考虑逢高减仓。"
        elif pct >= 1:
            return "出现利好新闻，股价有所反应，建议继续持有观察。"
        else:
            return "出现利好新闻但股价反应平淡，建议观察是否有资金跟进。"
    else:
        if abs(pct) >= 2:
            return f"股价波动{pct:+.2f}%较大，但暂无明确利好/利空新闻，建议关注盘面变化。"
        return "暂无重大新闻，建议按原有交易计划执行。"


def build_report(code: str, name: str = "") -> dict:
    quote_data = run_script("fetch_market.py", "--json", "quote", code)
    price = None
    change_pct = None
    if isinstance(quote_data, dict) and "price" in quote_data:
        price = quote_data.get("price")
        change_pct = quote_data.get("change_pct")

    news = fetch_news(code, name)
    if not news:
        return {
            "code": code,
            "name": name,
            "price": price,
            "change_pct": change_pct,
            "news": [],
            "sentiment": "neutral",
            "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0},
            "suggestion": suggest_position(change_pct, "neutral"),
        }

    sentiments = [analyze_sentiment(n["title"]) for n in news]
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    neu = sentiments.count("neutral")
    if neg > pos and neg > 0:
        overall = "negative"
    elif pos > neg and pos > 0:
        overall = "positive"
    else:
        overall = "neutral"

    return {
        "code": code,
        "name": name,
        "price": price,
        "change_pct": change_pct,
        "news": news,
        "sentiment_counts": {"positive": pos, "negative": neg, "neutral": neu},
        "sentiment": overall,
        "suggestion": suggest_position(change_pct, overall),
    }


def main():
    parser = argparse.ArgumentParser(description="Stock news monitor with position suggestions")
    parser.add_argument("code", help="Stock code (e.g. 600519, hk00700, TSLA)")
    parser.add_argument("--name", default="", help="Stock display name")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = build_report(args.code, args.name)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['name'] or report['code']} 新闻监控")
        print(f"当前价格: {report['price'] or '-'}  涨跌幅: {report['change_pct'] or 0:+.2f}%")
        if report.get("news"):
            print(f"新闻情绪: {report['sentiment']}  (正{report['sentiment_counts']['positive']} 负{report['sentiment_counts']['negative']} 中{report['sentiment_counts']['neutral']})")
            print("最新新闻:")
            for n in report["news"][:3]:
                print(f"  [{n['date']}] {n['title']} ({n['source']})")
        print(f"建议: {report['suggestion']}")


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    main()
