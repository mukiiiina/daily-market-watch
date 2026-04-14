# Daily Market Watch | 每日看盘辅助

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://github.com/mukiiiina/daily-market-watch)

> 一款面向 A 股、港股、美股及国内公募基金的 **OpenClaw Skill**，支持大盘实时监控、持仓管理、涨跌预警、早盘/盘后报告推送与新闻舆情分析。
>
> 数据来自 **腾讯财经、新浪财经、akshare**，**无需 API Key**。

可在 **Claude Code**、**AutoClaw**、**飞书（Lark）** 等 OpenClaw 生态中使用，也支持独立作为 Python CLI 工具运行。

---

## 目录

- [亮点速览](#亮点速览)
- [最近更新](#最近更新)
- [功能总览](#功能总览)
- [数据覆盖](#数据覆盖)
- [快速开始](#快速开始)
- [CLI 使用指南](#cli-使用指南)
- [报告示例](#报告示例)
- [多平台接入](#多平台接入)
- [完整配置手册](#完整配置手册)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [后续增强方向](#后续增强方向)
- [参与贡献](#参与贡献)
- [免责声明](#免责声明)
- [License](#license)

---

## 亮点速览

- **零成本数据**：不依赖任何付费 API，纯 Python + 开源数据源
- **跨市场支持**：A 股（6 位代码）、港股（5 位代码）、美股（字母代码）自动识别
- **三位一体的报告**：早盘预热、盘中快照、盘后总结，支持 `detailed` / `concise` 两种详细程度
- **智能预警**：个股/基金/大盘波动到达阈值时自动推送 Lark/Feishu 卡片
- **情绪分析**：自动抓取持仓个股新闻，基于关键词做正/负/中情绪判定，并给出持仓建议
- **技术指标**：MA / MACD / KDJ / RSI 自动计算，盘中报告标注金叉死叉与趋势状态
- **成本盈亏追踪**：基于持仓成本计算当日盈亏与累计浮盈浮亏

---

## 最近更新

### v0.4.0 — 新闻舆情与持仓建议
- 新增 `news_monitor.py`，基于 akshare 抓取个股相关新闻
- 通过 curated 关键词列表做情绪分析（bullish / bearish）
- `alert.py` 触发个股预警时，自动附带新闻情绪与仓位建议
- `report.py` 早盘/盘后详细模式，逐只持仓展示新闻情绪统计与操作建议

### v0.3.0 — 总盈亏分析 + 市场情绪 + 技术指标
- 盘后报告新增 **当日总预估盈亏** 与 **持仓总盈亏**
- 新增 A 股涨跌家数、涨停跌停数、等权涨幅、北向资金流向
- 新增 `tech_signals.py`：MA5/MA10/MA20、MACD、KDJ、RSI 与趋势摘要

### v0.2.0 — 港股与美股支持
- 支持港股（如 `00700` → `hk00700`）与美股（如 `TSLA`）实时行情
- 指数覆盖恒生指数、纳斯达克、道琼斯、标普 500

---

## 功能总览

| 功能 | 说明 | CLI 入口 |
|------|------|----------|
| **早间盘前预热** | 昨日回顾 + 市场情绪 + 持仓盘前提示 + 今日看盘重点 | `report.py morning` |
| **盘中实时监控** | 主动查询大盘/个股/基金/板块的实时数据 | `fetch_market.py` / 自然语言 |
| **盘后总结** | 大盘总结 + 板块资金 + 市场情绪 + 持仓盈亏 + 技术指标 + 明日预判 | `report.py evening` |
| **持仓管理** | 股票 + 基金，支持批量增删改、成本记录 | `portfolio.py` |
| **涨跌预警** | 个股/基金/大盘波动到达阈值时主动提醒 | `alert.py check` |
| **市场情绪** | A 股涨跌家数、涨停跌停数、等权涨幅、北向资金流向 | `fetch_market.py breadth` |
| **技术指标** | 持仓个股 MA/MACD/KDJ/RSI 金叉死叉与趋势提示 | `tech_signals.py` |
| **新闻舆情监控** | 抓取持仓个股相关新闻，基于关键词做情绪分析并给出持仓建议 | `news_monitor.py` |
| **定时推送** | 通过 Lark/Feishu Webhook 推送图文报告 | OpenClaw Cron |

---

## 数据覆盖

| 市场 | 指数 | 个股 | 特色数据 |
|------|------|------|----------|
| **A 股** | 上证指数、深证成指、创业板指、科创50 | 沪深京全部个股 | 板块排名、涨跌家数、北向资金、技术指标 |
| **港股** | 恒生指数 | 港股通标的 | 实时行情、技术指标 |
| **美股** | 纳斯达克、道琼斯、标普500 | 热门中概股及美股个股 | 隔夜收盘数据、技术指标 |
| **公募基金** | — | 国内公募混合/股票型基金 | 实时估算净值、昨日单位净值 |

> **时区说明**：A 股与港股为北京时间实时数据；美股在北京时间白天展示的是**隔夜收盘数据**，报告中已自动标注。

---

## 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/mukiiiina/daily-market-watch.git
cd daily-market-watch

# 安装依赖
pip install -r requirements.txt
```

依赖包含 `requests`（核心）与 `akshare`（用于 richer 数据与新闻舆情）。

### 2. 将 Skill 接入 OpenClaw（可选）

```bash
git clone https://github.com/mukiiiina/daily-market-watch.git ~/.openclaw/skills/daily-market-watch
```

安装后可直接通过自然语言交互，如：
- "帮我看一下今日大盘"
- "我的持仓怎么样了"
- "茅台现在多少钱"
- "生成盘后总结"

### 3. 初始化配置

#### 添加股票持仓

```bash
# A 股：贵州茅台
python scripts/portfolio.py add stock 600519 \
  --name 贵州茅台 --quantity 100 --cost 1400 \
  --rise-alert 5 --fall-alert -3

# 港股：腾讯控股
python scripts/portfolio.py add stock 00700 \
  --name 腾讯控股 --quantity 100 --cost 500 \
  --rise-alert 5 --fall-alert -5

# 美股：特斯拉
python scripts/portfolio.py add stock TSLA \
  --name 特斯拉 --quantity 50 --cost 250 \
  --rise-alert 5 --fall-alert -5
```

#### 添加基金持仓

```bash
python scripts/portfolio.py add fund 005827 \
  --name 易方达蓝筹 --quantity 10000 --cost 2.5 \
  --rise-alert 3 --fall-alert -2
```

#### 设置偏好

```bash
python scripts/config.py set detail_level detailed
python scripts/config.py set morning_push 0915
python scripts/config.py set evening_push 1530
python scripts/config.py set index_volatility_threshold 1.0
python scripts/config.py set alert_mode enabled
```

---

## CLI 使用指南

### 大盘与行情

```bash
# 主要指数一览
python scripts/fetch_market.py indices

# 个股查询（自动识别市场）
python scripts/fetch_market.py quote 600519      # A 股
python scripts/fetch_market.py quote 00700       # 港股
python scripts/fetch_market.py quote TSLA        # 美股

# 批量持仓行情
python scripts/fetch_market.py quotes sh600519,hk00700,usTSLA

# 热门板块 TOP5
python scripts/fetch_market.py sectors --top 5

# 市场情绪（涨跌家数 + 北向）
python scripts/fetch_market.py breadth
```

### 基金与技术指标

```bash
# 基金估算净值
python scripts/fetch_market.py funds --codes 005827,110022

# 技术指标信号
python scripts/tech_signals.py 600519
python scripts/tech_signals.py hk00700
python scripts/tech_signals.py TSLA
```

### 新闻舆情与预警

```bash
# 新闻监控（支持 --json）
python scripts/news_monitor.py 600519
python scripts/news_monitor.py 00700 --name 腾讯控股
python scripts/news_monitor.py TSLA --name 特斯拉 --json

# 检查预警
python scripts/alert.py check
python scripts/alert.py check --json
```

### 报告生成

```bash
python scripts/report.py morning      # 早盘报告
python scripts/report.py intraday     # 盘中快照
python scripts/report.py evening      # 盘后总结
```

---

## 报告示例

### 早间盘前预热 (`report.py morning`)

```markdown
# 早间盘前预热 (04月14日 09:15)

## 昨日市场回顾
昨日大盘：上证指数 +0.95%，深证成指 +1.61%，创业板指 +2.36%...

## 市场情绪
- 涨跌分布：涨 3722 / 跌 1594 / 平 185 | 涨停 83 | 跌停 3 | 等权涨幅 +0.97%
- 北向资金 (2024-08-16): 净流入 -67.75万

## 热门板块动向
- 电解液: 涨跌 +4.15%  领涨 石大胜华(+10.01%)
...

## 持仓盘前提示
- 贵州茅台 (sh600519): 昨收 1443.31，当前 1446.9 持仓盈亏 +4690.00，+0.25% [A股]
  新闻贵州茅台: 出现利空新闻但股价暂未明显反应，建议密切关注。 (情绪: 正0 负1 中4)

## 今日看盘重点
- 关注 创业板指 开盘后的方向选择（当前波动预期 +2.36%）。
- 盘中如遇大盘波动超过 1%，注意控制仓位风险。
```

### 盘中快照 (`report.py intraday`)

```markdown
# 盘中快照 (04月14日 10:30)

## 大盘
- 上证指数: 4026.63  +0.95%
- 创业板指: 3558.53  +2.36%
...

## 持仓
- 贵州茅台 (sh600519): 1446.9  +0.25%  持仓盈亏 +4690.00 [A股]
- 腾讯控股 (hk00700): 491.2  +0.24%  持仓盈亏 +2240.00 [港股]
- 特斯拉 (usTSLA): 352.42  +0.99%  持仓盈亏 +5121.00 [美股]（隔夜收盘）
- 易方达蓝筹 (005827): 估算 -1.5434%  持仓盈亏 -7585.00
```

### 盘后总结 (`report.py evening`)

```markdown
# 盘后总结 (04月14日 15:30)

## 当日大盘总结
今日收盘：上证指数 +0.95%，深证成指 +1.61%，创业板指 +2.36%...
- 上证指数: 收 4026.63，成交 570.26亿手
- 恒生指数: 收 25859.17，成交 1832.15万股

## 板块资金流向
- 电解液: 涨跌 +4.15%  成交额 314.66亿  领涨 石大胜华(+10.01%)
...

## 市场情绪
- 涨跌分布：涨 3722 / 跌 1594 / 平 185 | 涨停 83 | 跌停 3 | 等权涨幅 +0.97%
- 北向资金 (2024-08-16): 净流入 -67.75万

## 持仓总结
### 股票
- 贵州茅台 (sh600519): 收 1446.9，成本 1400.00，+0.25%，当日 +359.00 / 持仓 +4690.00 [A股] | 跌破MA20
  新闻贵州茅台: 出现利空新闻但股价暂未明显反应，建议密切关注。 (情绪: 正0 负1 中4)
- 腾讯控股 (hk00700): 收 491.4，成本 480.00，+0.29%，当日 +280.00 / 持仓 +2280.00 [港股] | 跌破MA20
- 特斯拉 (usTSLA): 收 352.42，成本 250.00，+0.99%，当日 +173.50 / 持仓 +5121.00 [美股]（美股隔夜收盘） | 跌破MA20

### 基金
- 易方达蓝筹 (005827): 估算涨跌 -1.5434%，成本 2.500，当日 -268.78 / 持仓 -7585.00

**当日总预估盈亏: +543.72  |  持仓总盈亏: +4506.00**

## 明日看盘预判
- 今日市场情绪偏强，明日可关注量能能否持续，谨防冲高回落。
- 晚间关注美股走势及政策/行业公告，可能影响次日开盘情绪。
```

### 预警通知 (`alert.py check`)

```markdown
🚨 看盘预警提醒

- 深证成指 指数波动 +1.61%，超过阈值 1.0%
- 创业板指 指数波动 +2.36%，超过阈值 1.0%
- 贵州茅台(600519) 当前 1446.9 涨跌 +0.25%，触及上涨预警线
  - 新闻建议: 出现利空新闻但股价暂未明显反应，建议密切关注。

*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*
```

---

## 多平台接入

### Claude Code / AutoClaw / OpenClaw

安装 Skill 后，直接通过自然语言交互：

- "帮我看一下今日大盘"
- "我的持仓怎么样了"
- "茅台现在多少钱"
- "设置一个涨跌预警"
- "生成盘后总结"
- "查看茅台的新闻舆情"

### 飞书 / Lark 彩色卡片推送

配置机器人 Webhook 后，早盘/盘后报告与实时预警会自动以 **Lark Interactive Card** 形式推送到飞书群，呈现为**彩色 Markdown 卡片**：

- **翠绿色标题栏**：醒目展示报告类型（早盘/盘后/预警）与推送时间
- **涨跌双色标注**：上涨数字以 🔴 红色高亮，下跌数字以 🟢 绿色高亮，一眼识别盈亏
- **分层信息块**：大盘指数、板块排行、持仓明细、新闻舆情、技术指标分别置于独立卡片区块，配有 Emoji 图标点缀
- **底部免责声明**：浅灰色细边框收尾，风险提示清晰优雅

配置方式：

```bash
python scripts/config.py set lark_webhook https://open.feishu.cn/open-apis/bot/v2/hook/xxxx
```

效果示例：

```markdown
┌─────────────────────────────────────┐
│  🌅 早间盘前预热  04月14日 09:15    │
├─────────────────────────────────────┤
│  📈 大盘指数                        │
│  上证指数 +0.95%  深证成指 +1.61%   │
│  创业板指 +2.36%  科创50 +2.17%     │
├─────────────────────────────────────┤
│  💼 持仓盘前提示                    │
│  贵州茅台 +0.25%  [A股]             │
│  新闻舆情: 出现利空新闻但股价暂未   │
│  明显反应，建议密切关注             │
│  (情绪: 正0 负1 中4)                │
├─────────────────────────────────────┤
│  ⚠️ 本 Skill 仅提供看盘辅助...      │
└─────────────────────────────────────┘
```

卡片在移动端飞书 App 中自适应排版，支持长按复制与一键转发。

---

## 完整配置手册

### 数据存储位置

所有个人数据保存在 `~/.config/daily-market-watch/`：

| 文件 | 用途 |
|------|------|
| `portfolio.json` | 持仓明细与每只标的的预警规则 |
| `config.json` | 用户偏好、推送时间、大盘波动阈值、Webhook 地址 |
| `history/` | 每日报告快照（可手动清理或配置 Cron 定期归档） |

### `portfolio.json` 结构示例

```json
{
  "version": 1,
  "stocks": [
    {
      "code": "sh600519",
      "name": "贵州茅台",
      "quantity": 100,
      "cost": 1400.0,
      "alerts": { "rise": 5.0, "fall": -3.0 }
    }
  ],
  "funds": [
    {
      "code": "005827",
      "name": "易方达蓝筹精选",
      "quantity": 10000,
      "cost": 2.5,
      "alerts": { "rise": 3.0, "fall": -2.0 }
    }
  ]
}
```

### `config.json` 结构示例

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

### 定时任务推荐（OpenClaw Cron）

```bash
# 早盘推送：工作日 9:15
openclaw cron add --name dmw:morning \
  --schedule "15 9 * * 1-5" \
  -- python ~/.openclaw/skills/daily-market-watch/scripts/report.py morning

# 盘后推送：工作日 15:30
openclaw cron add --name dmw:evening \
  --schedule "30 15 * * 1-5" \
  -- python ~/.openclaw/skills/daily-market-watch/scripts/report.py evening

# 盘中预警检查：工作日 9-11 点、13-15 点每小时
openclaw cron add --name dmw:alerts \
  --schedule "0 9-11,13-15 * * 1-5" \
  -- python ~/.openclaw/skills/daily-market-watch/scripts/alert.py check
```

---

## 项目结构

```
daily-market-watch/
├── SKILL.md                      # OpenClaw Skill 定义与触发词
├── README.md                     # 本文件
├── requirements.txt              # Python 依赖
├── scripts/
│   ├── fetch_market.py           # 大盘/个股/基金/板块/市场情绪数据获取
│   ├── portfolio.py              # 持仓 CRUD 与自动市场识别
│   ├── config.py                 # 配置管理
│   ├── alert.py                  # 预警检查与 Lark 通知
│   ├── report.py                 # 早盘/盘中/盘后报告生成
│   ├── tech_signals.py           # 技术指标计算（MA/MACD/KDJ/RSI）
│   └── news_monitor.py           # 个股新闻舆情与持仓建议
└── references/
    ├── data-sources.md           # API 端点与字段映射
    └── config-schema.md          # 配置与数据结构参考
```

---

## 常见问题

**Q: 为什么美股数据显示的是隔夜收盘？**  
A: 美股交易时间为美东时间 9:30-16:00，对应北京时间 21:30-次日 4:00（夏令时）或 22:30-次日 5:00（冬令时）。因此在北京时间白天查询时，看到的是上一个美股交易日的收盘数据，报告中已自动标注。

**Q: 港股 5 位代码和 A 股 6 位代码会自动区分吗？**  
A: 会。`portfolio.py` 和 `fetch_market.py` 内置了 `normalize_security_code` 函数：6 位数字自动识别为 A 股，5 位数字为港股，纯字母为美股。

**Q: 可以同时持有同一基金的 A/C 份额吗？**  
A: 可以。基金以 `code` 为唯一标识，只要代码不同即可分别记录。

**Q: 报告历史会保留多久？**  
A: 当前版本保留在 `~/.config/daily-market-watch/history/` 目录下，文件名为 `{kind}_{YYYYMMDD}.md`。可定期手动清理，或配置系统 Cron 做 7 天轮转。

**Q: 新闻舆情的数据来源是什么？**  
A: 通过 `akshare.stock_news_em()` 抓取东方财富相关新闻，使用基于 curated 关键词列表的轻量级 sentiment analyzer，无需调用外部 NLP API。

---

## 后续增强方向

从专业投资者视角出发，以下功能可进一步提升该工具的实用价值（欢迎社区贡献）：

- ✅ **持仓成本盈亏分析**：基于 `cost` 字段计算总持仓市值、累计浮盈/浮亏、收益率
- ✅ **市场情绪与北向资金**：A 股涨跌家数、涨停跌停数、等权涨幅、北向历史净流入
- ✅ **技术分析指标**：MACD、KDJ、RSI、均线（MA5/MA10/MA20）金叉死叉提示
- ✅ **新闻舆情与持仓建议**：基于 akshare 抓取个股新闻并做情绪分析，在报告和预警中给出仓位建议
- **个股资金流向**：引入主力净流入/大单动向，辅助判断筹码分布
- **龙虎榜数据**：涨停/跌停个股的营业部买卖席位追踪
- **融资融券余额**：个股两融余额变化，判断杠杆情绪
- **汇率联动**：港股持仓受人民币汇率影响，可加入离岸人民币(CNH)走势
- **ETF 折溢价监控**：场内 ETF 实时价格 vs 净值折溢价率
- **组合收益率曲线**：基于历史净值绘制累计收益 vs 沪深300 基准对比
- **财报日历/分红送转提醒**：持仓个股的重要公告、除权除息日提醒
- **打新提醒**：根据持仓市值自动计算沪深两市申购额度并提醒
- **动态仓位建议**：基于大盘波动率(VIX 或 A 股涨跌停家数)的轻量级仓位参考

---

## 参与贡献

欢迎提交 Issue 和 Pull Request！

如果你有以下想法，特别欢迎：
- 增加新的数据源或市场（如可转债、期货、期权）
- 优化技术指标的计算逻辑或增加新的信号
- 改进新闻情绪分析的准确率
- 增加可视化输出（如收益曲线图）

---

## 免责声明

**本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。**

所有分析、预判均基于公开实时数据，不推荐个股、不指导买卖操作。使用者应独立判断并自行承担投资风险。

---

## License

MIT © [mukiiiina](https://github.com/mukiiiina)
