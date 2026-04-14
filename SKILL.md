---
name: daily-market-watch
description: Daily A-share market watch assistant for Chinese stocks and funds. Use when the user asks about 看盘, 大盘, 持仓, 预警, stock alerts, fund NAV, market summary, or wants scheduled morning/evening market reports.
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

Help users track A-share stocks and public funds with pre-market briefings, intraday snapshots, post-market summaries, and price alerts.

## When to Use

Use this skill for queries like:

- "帮我看一下今日大盘"
- "我的持仓怎么样了"
- "茅台现在多少钱"
- "设置一个涨跌预警"
- "生成盘后总结"
- "早间看盘预热"

## First-Time Setup

If the user has no holdings configured, guide them to add holdings before personalized reports can be generated.

1. Add holdings:
   - `python {baseDir}/scripts/portfolio.py add stock 600519 --name 贵州茅台 --quantity 100 --cost 1400 --rise-alert 5 --fall-alert -3`
   - `python {baseDir}/scripts/portfolio.py add fund 005827 --name 易方达蓝筹 --quantity 10000 --cost 2.5 --rise-alert 3`
2. Set preferences:
   - `python {baseDir}/scripts/config.py set detail_level detailed`  # or concise
   - `python {baseDir}/scripts/config.py set morning_push 0915`
   - `python {baseDir}/scripts/config.py set evening_push 1530`
   - `python {baseDir}/scripts/config.py set index_volatility_threshold 1.0`
3. Optionally configure a Lark/Feishu webhook for true push delivery:
   - `python {baseDir}/scripts/config.py set lark_webhook https://open.feishu.cn/open-apis/bot/v2/hook/...`

State is persisted in `~/.config/daily-market-watch/`.

## Common Queries

Always prefer calling the provided scripts rather than inventing external commands.

### Market Overview

- Indices: `python {baseDir}/scripts/fetch_market.py indices`
- Single quote: `python {baseDir}/scripts/fetch_market.py quote 600519`
- Multiple quotes: `python {baseDir}/scripts/fetch_market.py quotes sh600519,sz000001`
- Sectors: `python {baseDir}/scripts/fetch_market.py sectors --top 5`
- Funds: `python {baseDir}/scripts/fetch_market.py funds --codes 005827,110022`

### Portfolio & Alerts

- List holdings: `python {baseDir}/scripts/portfolio.py --json list`
- Check alerts: `python {baseDir}/scripts/alert.py check`

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

If `lark_webhook` is set, the report scripts will POST the markdown report to the webhook. If not set, the report is written to the history directory and the user can query it interactively.

## Natural Language Mapping

Map common phrases to script calls:

- "今天大盘怎么样" → `fetch_market.py indices`
- "帮我看一下持仓" → `portfolio.py --json list` + `fetch_market.py quotes <codes>`
- "茅台多少钱" → `fetch_market.py quote 600519`
- "热门板块" → `fetch_market.py sectors --top 5`
- "预警" / "有没有触发" → `alert.py check`
- "早盘" / "早间" → `report.py morning`
- "盘后总结" / "收盘总结" → read latest `~/.config/daily-market-watch/history/evening_YYYYMMDD.md` or run `report.py evening`

## Data Sources

- Stocks/indices: Tencent Finance API (no key)
- Funds: Tencent Finance API `jj` endpoint (no key)
- Sectors: Sina Finance sector API (no key)

## Important Disclaimer

All outputs must include or be prefaced with the disclaimer:

> 本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。

Do not provide buy/sell recommendations or professional investment advice.

## Additional Resources

- **`references/data-sources.md`** — API endpoints and field mappings
- **`references/config-schema.md`** — Portfolio/config JSON schema and script examples
