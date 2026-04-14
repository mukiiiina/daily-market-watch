# Daily Market Watch | 每日看盘辅助

一款面向 A 股散户和基金投资者的 OpenClaw Skill，支持大盘实时监控、持仓管理、涨跌预警、早盘/盘后报告推送。可在 Claude Code、AutoClaw、飞书（Lark）等 OpenClaw 生态中使用。

## 核心功能

- **早间盘前预热**（9:15 前）: 昨日回顾 + 持仓提示 + 看盘重点
- **盘中实时监控**: 主动查询大盘/个股/基金/板块，自动触发涨跌预警
- **盘后总结**（15:30 前）: 当日大盘总结 + 持仓盈亏 + 明日预判
- **持仓管理**: 股票 + 基金，支持批量添加、删除、预警设置
- **多平台推送**: 支持 Lark/Feishu 机器人 webhook 主动推送

## 数据覆盖

- **A 股市场**: 上证、深证、创业板、科创板
- **国内公募基金**: 实时估算净值与涨跌幅
- **板块排名**: 概念/行业板块涨跌与领涨股

> 数据来源: 腾讯财经、新浪财经（无需 API Key）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 将 Skill 接入 OpenClaw

```bash
# 克隆到 OpenClaw skills 目录
git clone https://github.com/<your-username>/daily-market-watch.git ~/.openclaw/skills/daily-market-watch
```

### 3. 初始化配置

```bash
# 添加持仓
python scripts/portfolio.py add stock 600519 --name 贵州茅台 --quantity 100 --cost 1400 --rise-alert 5 --fall-alert -3
python scripts/portfolio.py add fund 005827 --name 易方达蓝筹 --quantity 10000 --cost 2.5 --rise-alert 3

# 设置偏好
python scripts/config.py set detail_level detailed
python scripts/config.py set morning_push 0915
python scripts/config.py set evening_push 1530
python scripts/config.py set index_volatility_threshold 1.0
```

### 4. 日常查询

```bash
python scripts/fetch_market.py indices          # 大盘指数
python scripts/fetch_market.py quote 600519     # 个股行情
python scripts/fetch_market.py sectors --top 5  # 热门板块
python scripts/alert.py check                   # 检查预警
python scripts/report.py morning                # 生成早盘报告
python scripts/report.py evening                # 生成盘后报告
```

### 5. 设置定时推送（OpenClaw Cron）

```bash
# 早盘推送
openclaw cron add --name dmw:morning --schedule "15 9 * * 1-5" -- python ~/.openclaw/skills/daily-market-watch/scripts/report.py morning

# 盘后推送
openclaw cron add --name dmw:evening --schedule "30 15 * * 1-5" -- python ~/.openclaw/skills/daily-market-watch/scripts/report.py evening

# 盘中预警检查（每小时）
openclaw cron add --name dmw:alerts --schedule "0 9-11,13-15 * * 1-5" -- python ~/.openclaw/skills/daily-market-watch/scripts/alert.py check
```

### 6. 飞书/Lark 推送（可选）

配置机器人 webhook 后，报告和预警会自动 POST 到飞书：

```bash
python scripts/config.py set lark_webhook https://open.feishu.cn/open-apis/bot/v2/hook/xxxx
```

## 项目结构

```
daily-market-watch/
├── SKILL.md                      # OpenClaw Skill 定义
├── scripts/
│   ├── fetch_market.py           # 大盘/个股/基金/板块数据获取
│   ├── portfolio.py              # 持仓管理
│   ├── config.py                 # 配置管理
│   ├── alert.py                  # 预警检查
│   └── report.py                 # 报告生成
├── references/
│   ├── data-sources.md           # 数据源说明
│   └── config-schema.md          # 配置与数据结构
├── requirements.txt
└── README.md
```

## 配置与数据存储

所有个人数据保存在 `~/.config/daily-market-watch/`：

- `portfolio.json` — 持仓与预警规则
- `config.json` — 用户偏好与推送时间
- `history/` — 近 7 天报告快照

## 免责声明

**本 Skill 仅提供看盘辅助，不构成投资建议，投资有风险。**

所有分析、预判均基于公开实时数据，不推荐个股、不指导买卖操作。

## License

MIT
