# P — Trading Knowledge, Data & Research Core

این مخزن بر اساس `docs/resource-connector-map.md` سازمان‌دهی شده و یک هسته‌ی پژوهشی برای **دانش، داده، Quant/Backtesting و Retrieval در ChatGPT** است. این پروژه MCP Server نیست و هیچ کد اجرای سفارش ندارد.

## وضعیت

**Operational core: complete.** زیرساخت مستندسازی، Source Registry، Provenance، Data Validation، Lookahead Audit، Quant templates، Backtest metrics و Curated retrieval artifacts ایجاد شده‌اند.

**Historical asset recovery: incomplete by evidence.** فایل‌های قدیمی نام‌برده‌شده در سند مرجع مانند نسخه اصلی `glossary.md`، `SKILL.md`، `MARKET_PARAMS.md`، `rtm-fshcd`، `smcp-v3-architecture`، `quant-engine-9phase` و مجموعه PDFهای ترجمه‌شده تا زمان دریافت اصل فایل/commit به‌عنوان `missing` باقی می‌مانند. نسخه‌های generated جای اصل تاریخی را نمی‌گیرند.

## Source of Truth

1. `docs/resource-connector-map.md` — سند مرجع پروژه
2. `config/source-registry.yaml` — Registry منابع
3. `docs/SOURCE_POLICY.md` — سیاست منبع و provenance
4. `docs/ASSET_DEFINITION_AUDIT.md` — ممیزی تعاریف و نام‌های داخلی
5. `docs/PROJECT_COMPLETION_STATUS.md` — وضعیت تکمیل

## ساختار

```text
po/
├── docs/                 # architecture, policies, protocols, canonical map
├── config/               # source registry, pipeline, quality gates, market params example
├── knowledge/            # framework-isolated notes + curated retrieval artifacts
├── data/                 # market-specific intake rules + JSON schemas
├── quant/                # strategy/backtest templates and research rules
├── research_core/        # reusable Python validation/metrics/provenance logic
├── tools/                # CLI utilities
├── tests/                # unit tests
├── connectors/           # integration policy; no MCP runtime
└── .github/workflows/    # quality checks
```

## Quick start

```powershell
git clone https://github.com/0022249141/po.git
cd po
py -m pip install -e .
py -m unittest discover -s tests -v
py tools\validate_registry.py
py tools\audit_lookahead.py . --fail-on high
```

### Validate a market CSV

OHLC example:

```powershell
py tools\validate_market_csv.py path\to\XAUUSD_M5.csv --type ohlc --timeframe M5
```

Tick example:

```powershell
py tools\validate_market_csv.py path\to\ticks.csv --type tick
```

### Create provenance manifest

```powershell
py tools\init_manifest.py path\to\XAUUSD_M5.csv --source-id user_mt5_export --market xauusd --symbol XAUUSD --data-type ohlc --timeframe M5 --timezone UTC
```

### Summarize a backtest trade export

CSV must contain `pnl`; optional `side`:

```powershell
py tools\summarize_backtest.py trades.csv --initial-capital 10000
```

## Non-negotiable research rules

- Primary-source first.
- Observed Data, Source Definition, Interpretation, Hypothesis and Backtested Evidence are separate evidence classes.
- Every dataset requires provenance, timezone, cutoff and validation status.
- Strategy rules are frozen before implementation.
- Lookahead/repainting/future leakage are audited before accepting results.
- Transaction costs and fill assumptions must be explicit.
- No edge is labelled validated without reproducible IS/OOS evidence.
- Frameworks remain independent: RTM is not silently rewritten as ICT/SMC, and academic microstructure is not treated as direct visibility into dealer orders.

## Generated vs recovered artifacts

Files ending in `.generated.md` are **new operational artifacts created for this repository**. They are not claims that the historical files referenced by the Resource Connector Map were recovered.

See `docs/MISSING_ASSETS.md` and `docs/RECOVERY_PROTOCOL.md`.
