# Daily Market Watch | 每日看盘辅助

> 一款面向 A 股、港股、美股及国内公募基金的 OpenClaw Skill，支持大盘实时监控、持仓管理、涨跌预警、早盘/盘后报告推送。

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

可在 **Claude Code**、**AutoClaw**、**飞书（Lark）** 等 OpenClaw 生态中使用。数据来自腾讯财经、新浪财经，**无需 API Key**。

---

## 目录

- [功能总览](#功能总览)
- [数据覆盖](#数据覆盖)
- [快速开始](#快速开始)
- [报告示例](#报告示例)
- [多平台接入](#多平台接入)
- [完整配置手册](#完整配置手册)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [后续增强方向](#后续增强方向)
- [免责声明](#免责声明)
- [License](#license)

---

## 功能总览

| 功能 | 说明 | 触发方式 |
|------|------|----------|
| **早间盘前预热** | 昨日回顾 + 持仓盘前提示 + 今日看盘重点 | `report.py morning` / OpenClaw Cron |
| **盘中实时监控** | 主动查询大盘/个股/基金/板块的实时数据 | 自然语言指令或 CLI |
| **盘后总结** | 当日大盘总结 + 持仓盈亏 + 明日预判 | `report.py evening` / OpenClaw Cron |
| **持仓管理** | 股票 + 基金，支持批量增删改、成本记录 | `portfolio.py` |
| **涨跌预警** | 个股/基金/大盘波动到达阈值时主动提醒 | `alert.py check` / Cron |
| **定时推送** | 通过 Lark/Feishu Webhook 推送图文报告 | OpenClaw Cron |

---

## 数据覆盖

### A 股市场
- **主要指数**：上证指数 (`sh000001`)、深证成指 (`sz399001`)、创业板指 (`sz399006`)、科创50 (`sh000688`)
- **个股**：沪深京全部个股，支持 6 位数字代码自动识别
- **板块排名**：A 股概念/行业板块涨跌榜、领涨股、成交额

### 港股市场
- **主要指数**：恒生指数 (`hkHSI`)
- **个股**：港股通标的，支持 5 位数字代码自动识别（例：`00700` → `hk00700`）

### 美股市场
- **主要指数**：纳斯达克 (`usIXIC`)、道琼斯 (`usDJI`)、标普500 (`usINX`)
- **个股**：热门中概股及美股个股，支持字母代码自动识别（例：`TSLA`、`AAPL`）

### 国内公募基金
- **实时估算净值**：腾讯财经 `jj` 接口，支持多只基金同时查询
- **公布净值**：上一交易日单位净值

> **时区说明**：A 股与港股为北京时间实时数据；美股在北京时间白天展示的是**隔夜收盘数据**，报告中会自动标注。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

依赖仅包含 `requests`（核心）和可选的 `akshare`（ richer 数据备用）。

### 2. 将 Skill 接入 OpenClaw

```bash
git clone https://github.com/mukiiiina/daily-market-watch.git ~/.openclaw/skills/daily-market-watch
```

### 3. 初始化配置

#### 添加持仓（股票）

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

#### 添加持仓（基金）

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

### 4. 日常查询

```bash
# 大盘指数
python scripts/fetch_market.py indices

# 个股查询（支持跨市场自动识别）
python scripts/fetch_market.py quote 600519      # A 股
python scripts/fetch_market.py quote 00700       # 港股
python scripts/fetch_market.py quote TSLA        # 美股

# 批量持仓行情
python scripts/fetch_market.py quotes sh600519,hk00700,usTSLA

# 热门板块 TOP5
python scripts/fetch_market.py sectors --top 5

# 基金估算净值
python scripts/fetch_market.py funds --codes 005827,110022

# 检查预警
python scripts/alert.py check

# 生成报告
python scripts/report.py morning      # 早盘
python scripts/report.py intraday     # 盘中
python scripts/report.py evening      # 盘后
```

---

## 报告示例

### 盘后总结 (`report.py evening`)

```markdown
# 盘后总结 (04月14日 15:30)

## 当日大盘总结
今日收盘：上证指数 +0.55%，深证成指 +1.36%，创业板指 +2.13%，科创50 +2.46%，恒生指数 +0.43%，纳斯达克 +1.23%，道琼斯 +0.63%，标普500 +1.02%。
- 上证指数: 收 4010.45，成交 357.63亿手
- 深证成指: 收 14603.34，成交 428.29亿手
- 恒生指数: 收 25770.4，成交 1214.03万股
- 纳斯达克: 收 23183.74，成交 68.30亿股

## 板块资金流向
- 充电桩: 涨跌 +2.65%  成交额 280.53亿  领涨 中恒电气(+9.99%)
- 华为概念: 涨跌 +2.46%  成交额 794.35亿  领涨 京泉华(+10.00%)

## 持仓总结
### 股票
- 贵州茅台 (sh600519): 收 1438.0，-0.37%，当日预估盈亏 -531.00 [A股]
- 腾讯控股 (hk00700): 收 488.8，-0.24%，当日预估盈亏 -240.00 [港股]
- 特斯拉 (usTSLA): 收 352.42，+0.99%，当日预估盈亏 +173.50 [美股]（美股隔夜收盘）
### 基金
- 易方达蓝筹 (005827): 估算涨跌 -1.5434%，当日预估盈亏 -268.78

**当日总预估盈亏: -866.28**

## 明日看盘预判
- 今日市场情绪偏强，明日可关注量能能否持续，谨防冲高回落。
- 晚间关注美股走势及政策/行业公告，可能影响次日开盘情绪。

*本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。*
```

---

## 多平台接入

### Claude Code / AutoClaw

安装 Skill 后，直接通过自然语言交互：

- "帮我看一下今日大盘"
- "我的持仓怎么样了"
- "茅台现在多少钱"
- "设置一个涨跌预警"
- "生成盘后总结"

### 飞书 / Lark 推送

配置机器人 Webhook 后，报告和预警会自动以 **Interactive Card** 形式推送到飞书群：

```bash
python scripts/config.py set lark_webhook https://open.feishu.cn/open-apis/bot/v2/hook/xxxx
```

推送内容包含格式化 Markdown 卡片，支持移动端直接阅读。

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
│   ├── fetch_market.py           # 大盘/个股/基金/板块数据获取
│   ├── portfolio.py              # 持仓 CRUD 与自动市场识别
│   ├── config.py                 # 配置管理
│   ├── alert.py                  # 预警检查与 Lark 通知
│   └── report.py                 # 早盘/盘中/盘后报告生成
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

---

## 后续增强方向

从专业投资者视角出发，以下功能可进一步提升该工具的实用价值（欢迎社区贡献）：

- **持仓成本盈亏分析**：基于 `cost` 字段计算总持仓市值、累计浮盈/浮亏、收益率
- **个股资金流向**：引入主力净流入/大单动向，辅助判断筹码分布
- **龙虎榜数据**：涨停/跌停个股的营业部买卖席位追踪
- **北向资金流向**：沪股通、深股通实时净流入数据
- **融资融券余额**：个股两融余额变化，判断杠杆情绪
- **技术分析指标**：MACD、KDJ、RSI、均线（MA5/MA10/MA20）金叉死叉提示
- **汇率联动**：港股持仓受人民币汇率影响，可加入离岸人民币(CNH)走势
- **ETF 折溢价监控**：场内 ETF 实时价格 vs 净值折溢价率
- **组合收益率曲线**：基于历史净值绘制累计收益 vs 沪深300 基准对比
- **财报日历/分红送转提醒**：持仓个股的重要公告、除权除息日提醒
- **打新提醒**：根据持仓市值自动计算沪深两市申购额度并提醒
- **动态仓位建议**：基于大盘波动率(VIX 或 A 股涨跌停家数)的轻量级仓位参考

---

## 免责声明

**本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。**

所有分析、预判均基于公开实时数据，不推荐个股、不指导买卖操作。使用者应独立判断并自行承担投资风险。

---

## License

MIT © mukiiiina
