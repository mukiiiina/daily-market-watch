# Configuration & Portfolio Schema

## File Locations

All state is stored under `~/.config/daily-market-watch/`:

- `portfolio.json` — holdings and per-holding alert rules
- `config.json` — user preferences and push settings
- `history/` — generated report snapshots (rotated manually or by cron)

## portfolio.json

```json
{
  "version": 1,
  "stocks": [
    {
      "code": "sh600519",
      "name": "贵州茅台",
      "quantity": 100,
      "cost": 1400.0,
      "alerts": {
        "rise": 5.0,
        "fall": -3.0
      }
    }
  ],
  "funds": [
    {
      "code": "005827",
      "name": "易方达蓝筹精选",
      "quantity": 10000,
      "cost": 2.5,
      "alerts": {
        "rise": 3.0,
        "fall": -2.0
      }
    }
  ]
}
```

### Fields

- `code` — normalized code (`sh`/`sz`/`bj`/`hk`/`us` prefix for stocks; plain 6-digit for funds)
- `name` — display name
- `quantity` — holding quantity (shares for stocks, units for funds)
- `cost` — average cost price (used for PnL estimation)
- `alerts.rise` — alert when `change_pct` rises to or above this value
- `alerts.fall` — alert when `change_pct` falls to or below this value

## config.json

```json
{
  "morning_push": "0915",
  "evening_push": "1530",
  "detail_level": "detailed",
  "alert_mode": "enabled",
  "index_volatility_threshold": 1.0,
  "lark_webhook": ""
}
```

### Fields

- `morning_push` — time for pre-market report (HHMM)
- `evening_push` — time for post-market summary (HHMM)
- `detail_level` — `concise` or `detailed`
- `alert_mode` — `enabled` or `disabled`
- `index_volatility_threshold` — index change % that triggers an alert
- `lark_webhook` — optional Feishu/Lark bot webhook URL for scheduled push

## Scripts Reference

### `portfolio.py`

```bash
# Add A-share
python scripts/portfolio.py add stock 600519 --name 贵州茅台 --quantity 100 --cost 1400 --rise-alert 5 --fall-alert -3

# Add HK stock
python scripts/portfolio.py add stock 00700 --name 腾讯控股 --quantity 100 --cost 500 --rise-alert 5

# Add US stock
python scripts/portfolio.py add stock TSLA --name 特斯拉 --quantity 50 --cost 250 --rise-alert 5

# Add fund
python scripts/portfolio.py add fund 005827 --name 易方达蓝筹 --quantity 10000 --cost 2.5 --rise-alert 3

# Remove
python scripts/portfolio.py remove stock 600519

# List
python scripts/portfolio.py --json list
```

### `config.py`

```bash
python scripts/config.py set detail_level concise
python scripts/config.py set morning_push 0900
python scripts/config.py set alert_mode enabled
python scripts/config.py --json list
```

### `fetch_market.py`

```bash
python scripts/fetch_market.py indices
python scripts/fetch_market.py quote 600519
python scripts/fetch_market.py quote 00700
python scripts/fetch_market.py quote TSLA
python scripts/fetch_market.py quotes sh600519,hk00700,usTSLA
python scripts/fetch_market.py sectors --top 5
python scripts/fetch_market.py funds --codes 005827,110022
```

### `alert.py`

```bash
python scripts/alert.py check
```

### `report.py`

```bash
python scripts/report.py morning
python scripts/report.py intraday
python scripts/report.py evening
```

### `tech_signals.py`

```bash
python scripts/tech_signals.py 600519
python scripts/tech_signals.py hk00700
python scripts/tech_signals.py TSLA
```

### `news_monitor.py`

```bash
python scripts/news_monitor.py 600519
python scripts/news_monitor.py 00700 --name 腾讯控股
python scripts/news_monitor.py TSLA --name 特斯拉 --json
```

**Output schema (JSON)**:

```json
{
  "code": "600519",
  "name": "贵州茅台",
  "price": 1438.0,
  "change_pct": -0.37,
  "news": [
    {
      "title": "...",
      "content": "...",
      "date": "2025-04-14",
      "source": "东方财富",
      "url": "..."
    }
  ],
  "sentiment_counts": {
    "positive": 1,
    "negative": 2,
    "neutral": 2
  },
  "sentiment": "negative",
  "suggestion": "出现利空新闻但股价暂未明显反应，建议密切关注。"
}
```

**Sentiment logic**:
- Scans each news title against curated bullish/bearish keyword lists.
- `positive` > `negative` → `sentiment: positive`
- `negative` > `positive` → `sentiment: negative`
- Otherwise → `sentiment: neutral`

**Suggestion logic**:
- Combines overall sentiment with current `change_pct` to generate a position-adjustment suggestion (e.g., reduce on bad news + large drop, hold on good news + moderate rise).
