# Missing Assets

این فایل فقط مواردی را ثبت می‌کند که در سند مرجع نام برده شده‌اند اما نسخه واقعی آن‌ها در مخزن فعلی موجود نیست. محتوای هیچ‌کدام حدس زده نمی‌شود.

## Knowledge / RAG artifacts

- `glossary.md`
- `SKILL.md` — در سند با عبارت «نسخه فعلی ۶لایه+حکم» توصیف شده است.
- `MARKET_PARAMS.md`

## Existing translation pipeline assets mentioned by the map

- BTMM
- MMXM
- ICT London Close Killzone
- Choch Plan
- 1AM CRT
- مجموعه PDFهای ترجمه‌شده‌ای که سند تعداد آن‌ها را ۴۴ فایل ذکر می‌کند

## Named internal systems / skills

- `rtm-fshcd`
- `smcp-v3-architecture`
- `quant-engine-9phase`

## Data / implementation artifacts

- تعریف/نمونه واقعی فرمت `general-platforms` CSV
- نسخه کد یا commit مربوط به رفع باگ `rolling(center=True)`
- Strategy Specifications یا backtest outputs مربوط به سیستم‌های نام‌برده‌شده

## Rule

تا زمانی که فایل واقعی، commit، مسیر repository یا محتوای منبع در اختیار این پروژه قرار نگیرد:

1. نام artifact حفظ می‌شود.
2. وضعیت آن `missing` باقی می‌ماند.
3. هیچ placeholder حاوی محتوای ساختگی با همان نام ایجاد نمی‌شود تا Retrieval آلوده نشود.
