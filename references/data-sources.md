# Data Sources Reference

This document describes the external data sources used by the Daily Market Watch skill.

## Individual Stocks & Indices

**Source**: Tencent Finance API (`http://qt.gtimg.cn/q=`)

- No API key required.
- Real-time quotes for A-shares (Shanghai, Shenzhen, Beijing) and major indices.
- Symbol prefixes:
  - `sh` — Shanghai (e.g., `sh600519`, `sh000001`)
  - `sz` — Shenzhen (e.g., `sz000001`, `sz399006`)
  - `bj` — Beijing Exchange (e.g., `bj430047`)

Key fields returned:
- `price` — latest price
- `prev_close` — previous close
- `open` — opening price
- `high` / `low` — day high / low
- `change` — absolute change
- `change_pct` — percentage change
- `volume` — in "hand" (手), 1 hand = 100 shares
- `amount` — turnover in 10k CNY
- `turnover_rate` — turnover rate (%)
- `pe` — P/E ratio
- `pb` — P/B ratio

## Funds

**Source**: Tencent Finance API (`http://qt.gtimg.cn/q=jj{code}`)

- No API key required.
- Returns estimated NAV and estimated change percentage for public funds.
- Prefix fund codes with `jj` when calling the raw endpoint.

Key fields returned:
- `基金代码` — fund code
- `基金名称` — fund name
- `交易日-估算数据-估算值` — estimated NAV (may be `0.0000` before estimate update)
- `交易日-估算数据-估算增长率` — estimated change (%)
- `交易日-公布数据-单位净值` — last published NAV

## Sector Rankings

**Source**: Sina Finance (`http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class`)

- No API key required.
- Returns concept/industry sector rankings with leading stocks.

Key fields returned:
- `name` — sector name
- `change_pct` — sector average change (%)
- `amount` — total turnover
- `leading_name` — top performing stock in the sector
- `leading_change_pct` — change of the leading stock

## Optional: AKShare

Some environments can reach East Money servers without proxy issues. In those environments, `akshare` can be used for richer historical data. The core skill does not depend on it.
