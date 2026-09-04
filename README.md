# P — Trading Knowledge, Data & Research Repository

این مخزن از این پس بر اساس سند مرجع `docs/resource-connector-map.md` سازمان‌دهی می‌شود. هدف پروژه ساخت یک پایپ‌لاین منظم برای **دانش، داده، پژوهش، Backtesting و اتصال منابع به ChatGPT** در حوزه‌های ICT/SMC، RTM، Wyckoff، Dealer/Market Microstructure، Auction Market Theory، XAUUSD و طلای آبشده است.

> وضعیت معماری: MCP محلی MT5 از مخزن حذف شده است. این ریپو دیگر یک MCP Server نیست.

## سند مرجع

- `docs/resource-connector-map.md` — نسخه‌ی اصلی Resource Connector Map و مبنای تصمیم‌گیری معماری.
- `docs/ARCHITECTURE.md` — معماری اجرایی استخراج‌شده از سند مرجع.
- `docs/SOURCE_POLICY.md` — قواعد کیفیت، منبع، provenance و جلوگیری از مخلوط‌شدن Fact/Interpretation.
- `docs/MISSING_ASSETS.md` — دارایی‌هایی که در سند مرجع نام برده شده‌اند اما هنوز در این مخزن موجود نیستند.
- `docs/IMPLEMENTATION_PLAN.md` — مراحل اجرای پروژه و معیار تکمیل هر مرحله.

## ساختار پروژه

```text
po/
├── README.md
├── .gitignore
├── docs/
│   ├── resource-connector-map.md
│   ├── ARCHITECTURE.md
│   ├── SOURCE_POLICY.md
│   ├── MISSING_ASSETS.md
│   └── IMPLEMENTATION_PLAN.md
├── config/
│   ├── source-registry.yaml
│   └── pipeline-manifest.yaml
├── knowledge/
│   ├── 01-ict-smc-wyckoff/
│   ├── 02-rtm/
│   ├── 03-dealer-microstructure/
│   └── 04-auction-market-theory/
├── data/
│   ├── iran-gold/
│   ├── xauusd/
│   └── schema/
├── quant/
└── connectors/
```

## هشت محور سند مرجع

| # | محور | وضعیت در این ریپو |
|---|---|---|
| 1 | ICT / SMC / Wyckoff | ساختار و registry ایجاد شده؛ محتوای منبع هنوز ingest نشده |
| 2 | RTM / IF Myante | ساختار و registry ایجاد شده؛ محتوای منبع هنوز ingest نشده |
| 3 | Dealer / Market Microstructure | فهرست منابع آکادمیک و نقش آن‌ها ثبت شده |
| 4 | Auction Market Theory / Market Profile | ساختار منابع Dalton/CME ثبت شده |
| 5 | طلای آبشده / ایران | لایه‌ی داده و provenance تعریف شده؛ scraper/API ساخته نشده |
| 6 | XAUUSD / جهانی | Dukascopy/TradingView/TradingEconomics/ForexFactory در registry ثبت شده‌اند |
| 7 | Coding / Backtesting | لایه quant تعریف شده؛ موتورهای اشاره‌شده در سند مرجع هنوز در ریپو موجود نیستند |
| 8 | ChatGPT integration | سیاست Knowledge Files / GitHub / connectors مستندسازی شده؛ MCP حذف شده |

## اصل‌های غیرقابل‌تغییر پروژه

1. **Primary-source first** — در هر مکتب، منبع رسمی یا اولیه بر بازنشر شخص ثالث اولویت دارد.
2. **No fabrication** — هر فایلی که سند مرجع نام می‌برد ولی در ریپو موجود نیست، به‌عنوان Missing Asset ثبت می‌شود و محتوای آن حدس زده نمی‌شود.
3. **Provenance required** — هر داده یا متن ingest‌شده باید منبع، تاریخ/نسخه، روش دریافت و وضعیت پردازش داشته باشد.
4. **Observed ≠ Interpretation** — داده مشاهده‌شده، تعریف منبع، تفسیر تحلیلی و فرضیه Quant باید جدا نگهداری شوند.
5. **No silent rule mutation** — در تبدیل مفاهیم به Strategy Specification یا کد، Ruleها بدون ثبت تغییر نمی‌کنند.
6. **Backtest before claim** — هیچ Edge یا Rule به‌عنوان validated معرفی نمی‌شود مگر با تست بازتولیدپذیر.
7. **Raw sources are not knowledge files** — PDF/ویدئو/صفحه خام ابتدا باید index، summarize و normalize شوند؛ سپس نسخه‌ی curated وارد لایه Knowledge شود.

## وضعیت فعلی

اسکلت اصلی پروژه بر اساس Resource Connector Map ساخته شده است. مرحله‌ی بعدی، ورود و صحت‌سنجی **دارایی‌های موجود قبلی** (مانند glossary، SKILL، MARKET_PARAMS، ترجمه‌های PDF و موتورهای نام‌برده‌شده) و سپس ingest کنترل‌شده‌ی منابع رسمی است.
