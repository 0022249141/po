# Architecture

این معماری مستقیماً از `resource-connector-map.md` استخراج شده است و هیچ جزء محتوایی خارج از سند مرجع را به‌عنوان واقعیت پروژه فرض نمی‌کند.

## 1. Source Layer

منابع به چهار کلاس تقسیم می‌شوند:

- **Primary practitioner sources:** ICT official channels، Wyckoff Analytics، ReadTheMarket، RTM Academy، CME education.
- **Academic sources:** Kyle 1985، Glosten–Milgrom 1985، Ho & Stoll 1981، Grossman–Miller 1988، و دو مقاله arXiv مشخص‌شده در سند.
- **Market/data sources:** TGJU، Dukascopy، TradingView، TradingEconomics، ForexFactory، MT5 data.
- **Implementation references:** MetaTrader5 Python package، MQL5 Articles، GitHub topic searches.

## 2. Knowledge Layer

چهار حوزه مستقل نگهداری می‌شوند و تا زمان نیاز با یکدیگر ادغام نمی‌شوند:

1. ICT / SMC / Wyckoff
2. RTM
3. Dealer / Market Microstructure
4. Auction Market Theory / Market Profile

برای هر حوزه باید چهار نوع artifact از هم جدا باشد:

- `source-notes` — یادداشت وفادار به منبع
- `glossary` — تعریف واژگان
- `rules` — قواعد operational/testable
- `crosswalk` — نگاشت بین مکاتب، فقط پس از تعریف مستقل هر مکتب

## 3. Data Layer

### Iran Gold

- TGJU فقط برای cross-check لحظه‌ای و validation ثانویه در سند مرجع معرفی شده است.
- `general-platforms` CSV منبع اینترادی فعلی معرفی شده است.
- هر dataset باید timezone، symbol/instrument، timestamp cutoff، OHLC/tick fields و missing-data notes داشته باشد.

### XAUUSD

- Dukascopy: historical tick/minute برای backtest موازی.
- MT5: فید عملی کاربر، در صورت ارائه داده.
- TradingView: cross-check بصری و منطق اسکریپت‌ها.
- TradingEconomics / ForexFactory: macro-event metadata برای Time Logic / Volatility State.

## 4. Quant / Backtest Layer

وظیفه این لایه تبدیل مفهوم به specification و سپس test است. ترتیب اجباری:

1. تعریف دقیق مفهوم
2. تعریف inputs و state
3. operational rule
4. invalidation
5. implementation
6. bias/repaint/lookahead audit
7. baseline backtest
8. OOS / robustness
9. ثبت نتایج

هیچ مفهوم روایی مانند Dealer Inventory یا Confluence Score بدون تعریف محاسباتی وارد backtest نمی‌شود.

## 5. Retrieval / ChatGPT Layer

سند مرجع توصیه می‌کند فایل‌های سبک و curated نسبت به انباشت PDF خام در اولویت باشند. بنابراین ساختار retrieval باید به‌جای PDF dump، روی artifactهای فشرده و provenance-aware بنا شود.

Artifactهای نام‌برده‌شده در سند:

- `glossary.md`
- `SKILL.md`
- `MARKET_PARAMS.md`

تا زمانی که نسخه واقعی آن‌ها ارائه نشود، محتوایشان ساخته یا حدس زده نمی‌شود.

## 6. Pipeline

```text
Official/Academic/Data Sources
        ↓
Source Registry
        ↓
Acquisition + Provenance
        ↓
Normalization
        ↓
Source Notes
        ↓
Operational Definitions
        ↓
Strategy Specification
        ↓
Implementation / Backtest
        ↓
Curated Knowledge Files
        ↓
ChatGPT Retrieval / GitHub Connector
```

## 7. Repository Boundaries

این repository در وضعیت فعلی **MCP Server نیست**. هیچ local execution bridge یا order-execution component در معماری پایه وجود ندارد. اگر در آینده connector اجرایی لازم شود باید به‌عنوان پروژه/ماژول جداگانه و با specification مستقل اضافه شود، نه در لایه Knowledge.
