---
name: daily-market-watch
description: Daily market watch assistant for A-shares, Hong Kong stocks, US stocks, and Chinese public funds. Use when the user asks about 看盘, 大盘, 持仓, 预警, stock alerts, fund NAV, market summary, news sentiment, position suggestions, or wants scheduled morning/evening market reports pushed to Lark/Feishu as colorful interactive cards.
metadata:
  {
    "openclaw":
      {
        "emoji": "\U0001F4C8",
        "requires": { "bins": ["python3"] },
        "install":
          [
            {
              "id": "pip",
              "kind": "uv",
              "package": "akshare requests pandas",
              "label": "Install Python dependencies (uv/pip)",
            },
          ],
      },
  }
---

# Daily Market Watch

Help users track A-share, Hong Kong, and US stocks, plus Chinese public funds, with pre-market briefings, intraday snapshots, post-market summaries, price alerts, technical indicator signals, and news-based sentiment analysis with position suggestions. Reports and alerts can be delivered as colorful Lark/Feishu interactive cards.

## When to Use

Use this skill for queries like:

- "帮我看一下今日大盘"
- "我的持仓怎么样了"
- "茅台现在多少钱"
- "设置一个涨跌预警"
- "生成盘后总结"
- "早间看盘预热"
- "茅台最近有什么新闻"
- "帮我看看茅台的舆情"
- "推送一份早盘报告到飞书"

## First-Time Setup

If the user has no holdings configured, guide them to add holdings before personalized reports can be generated.

1. Add holdings:
   - A-share: `python {baseDir}/scripts/portfolio.py add stock 600519 --name 贵州茅台 --quantity 100 --cost 1400 --rise-alert 5 --fall-alert -3`
   - HK: `python {baseDir}/scripts/portfolio.py add stock 00700 --name 腾讯控股 --quantity 100 --cost 500 --rise-alert 5`
   - US: `python {baseDir}/scripts/portfolio.py add stock TSLA --name 特斯拉 --quantity 50 --cost 250 --rise-alert 5`
   - Fund: `python {baseDir}/scripts/portfolio.py add fund 005827 --name 易方达蓝筹 --quantity 10000 --cost 2.5 --rise-alert 3`
2. Set preferences:
   - `python {baseDir}/scripts/config.py set detail_level detailed`  # or concise
   - `python {baseDir}/scripts/config.py set morning_push 0915`
   - `python {baseDir}/scripts/config.py set evening_push 1530`
   - `python {baseDir}/scripts/config.py set index_volatility_threshold 1.0`
   - `python {baseDir}/scripts/config.py set alert_mode enabled`
3. Optionally configure a Lark/Feishu webhook for true push delivery:
   - `python {baseDir}/scripts/config.py set lark_webhook https://open.feishu.cn/open-apis/bot/v2/hook/...`
   - Once set, `report.py` and `alert.py` will post **colorful interactive cards** (green header for morning, indigo for evening, orange for intraday, red for alerts).

State is persisted in `~/.config/daily-market-watch/`.

## Common Queries

Always prefer calling the provided scripts rather than inventing external commands.

### Market Overview

- Indices: `python {baseDir}/scripts/fetch_market.py indices`
- Single quote: `python {baseDir}/scripts/fetch_market.py quote 600519`
- Multiple quotes: `python {baseDir}/scripts/fetch_market.py quotes sh600519,hk00700,usTSLA`
- Sectors: `python {baseDir}/scripts/fetch_market.py sectors --top 5`
- Funds: `python {baseDir}/scripts/fetch_market.py funds --codes 005827,110022`
- Market breadth & northbound: `python {baseDir}/scripts/fetch_market.py breadth`
- Tech signals: `python {baseDir}/scripts/tech_signals.py 600519`

### News & Sentiment

- News monitor (text): `python {baseDir}/scripts/news_monitor.py 600519 --name 贵州茅台`
- News monitor (JSON): `python {baseDir}/scripts/news_monitor.py TSLA --name 特斯拉 --json`

### Portfolio & Alerts

- List holdings: `python {baseDir}/scripts/portfolio.py --json list`
- Check alerts: `python {baseDir}/scripts/alert.py check`
- Check alerts (JSON): `python {baseDir}/scripts/alert.py check --json`

### Reports

- Morning briefing: `python {baseDir}/scripts/report.py morning`
- Intraday snapshot: `python {baseDir}/scripts/report.py intraday`
- Evening summary: `python {baseDir}/scripts/report.py evening`

Reports are also saved to `~/.config/daily-market-watch/history/` so the user can ask "给我看看今天的盘后总结" and you can read the latest file directly.

## Scheduled Push Setup

Because the skill is passive, scheduled reports rely on OpenClaw cron. After verifying the user wants pushes, create cron jobs:

- Morning: `openclaw cron add --name dmw:morning --schedule "15 9 * * 1-5" -- python {baseDir}/scripts/report.py morning`
- Evening: `openclaw cron add --name dmw:evening --schedule "30 15 * * 1-5" -- python {baseDir}/scripts/report.py evening`
- Hourly alert check (optional): `openclaw cron add --name dmw:alerts --schedule "0 9-11,13-15 * * 1-5" -- python {baseDir}/scripts/alert.py check`

If `lark_webhook` is set:
- `report.py` posts a **Lark Interactive Card** with a colored header (green for morning 🌅, indigo for evening 🌙, orange for intraday 📊).
- `alert.py` posts a **red-header card** 🚨 with triggered alerts and news suggestions.
- If no webhook is set, the report is written to the history directory and the user can query it interactively.

## Natural Language Mapping

Map common phrases to script calls:

- "今天大盘怎么样" → `fetch_market.py indices`
- "帮我看一下持仓" → `portfolio.py --json list` + `fetch_market.py quotes <codes>`
- "茅台多少钱" → `fetch_market.py quote 600519`
- "热门板块" → `fetch_market.py sectors --top 5`
- "市场情绪怎么样" / "涨跌家数" → `fetch_market.py breadth`
- "茅台技术面怎么样" → `tech_signals.py 600519`
- "茅台新闻" / "茅台舆情" / "查看茅台的新闻" → `news_monitor.py 600519 --name 贵州茅台`
- "预警" / "有没有触发" → `alert.py check`
- "早盘" / "早间" → `report.py morning`
- "盘后总结" / "收盘总结" → read latest `~/.config/daily-market-watch/history/evening_YYYYMMDD.md` or run `report.py evening`
- "推送到飞书" / "发到飞书" (with report context) → ensure `lark_webhook` is set, then run the relevant report or alert script

## Data Sources

- A-share/HK/US stocks and indices: Tencent Finance API (no key)
- Funds: Tencent Finance API `jj` endpoint (no key)
- Sectors: Sina Finance sector API (A-share only, no key)
- Market breadth, northbound flow, and stock news: AKShare (no key)

## Important Disclaimer

All outputs must include or be prefaced with the disclaimer:

> 本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。

Do not provide buy/sell recommendations or professional investment advice.

## Additional Resources

- **`references/data-sources.md`** — API endpoints and field mappings
- **`references/config-schema.md`** — Portfolio/config JSON schema, news output schema, and script examples
