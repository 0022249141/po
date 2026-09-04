# Missing Assets

این فایل فقط مواردی را ثبت می‌کند که در سند مرجع نام برده شده‌اند اما نسخه واقعی آن‌ها در مخزن فعلی موجود نیست. محتوای هیچ‌کدام حدس زده نمی‌شود.

> توضیحات تکمیلی کاربر درباره این نام‌ها دریافت و در `docs/ASSET_DEFINITION_AUDIT.md` ممیزی شده است. این توضیحات به‌خودی‌خود به معنی بازیابی Artifact اصلی نیستند.

## Knowledge / RAG artifacts

- `glossary.md` — توضیح نقش عمومی دریافت شده؛ فایل اصلی هنوز `missing` است.
- `SKILL.md` — توضیح نقش عمومی دریافت شده؛ نسخه واقعی «۶لایه+حکم» هنوز `missing` است.
- `MARKET_PARAMS.md` — تعریف DeFi پیشنهادی با Scope این پروژه ناسازگار تشخیص داده شد؛ فایل اصلی هنوز `missing` است.

## Existing translation pipeline assets mentioned by the map

- BTMM — نام عمومی به‌صورت **Beat the Market Maker** ممیزی شد؛ ترجمه/Artifact اصلی پروژه هنوز `missing` است.
- MMXM — نام عمومی به‌صورت **Market Maker Model** ممیزی شد؛ ترجمه/Artifact اصلی پروژه هنوز `missing` است.
- ICT London Close Killzone — مفهوم عمومی و Session timing ممیزی شد؛ Artifact ترجمه‌شده اصلی هنوز `missing` است.
- Choch Plan — توضیح عمومی CHoCH کافی برای بازسازی Plan نیست؛ Artifact اصلی هنوز `missing` است.
- 1AM CRT — توضیح عمومی دریافت شد اما expansion/timezone پیشنهادی canonical تلقی نشد؛ Artifact اصلی هنوز `missing` است.
- مجموعه PDFهای ترجمه‌شده‌ای که سند تعداد آن‌ها را ۴۴ فایل ذکر می‌کند — inventory واقعی هنوز `missing` است.

## Named internal systems / skills

- `rtm-fshcd` — expansion پیشنهادی speculative است؛ اصل asset هنوز `missing` است.
- `smcp-v3-architecture` — تعبیر Secure Model Context Protocol پشتیبانی نشد؛ اصل asset هنوز `missing` است.
- `quant-engine-9phase` — workflow عمومی ۹مرحله‌ای فقط reference است و specification داخلی محسوب نمی‌شود؛ اصل asset هنوز `missing` است.

## Data / implementation artifacts

- تعریف/نمونه واقعی فرمت `general-platforms` CSV — تفسیر trade-history تأیید نشد؛ sample/spec واقعی هنوز `missing` است.
- نسخه کد یا commit مربوط به رفع باگ `rolling(center=True)` — توضیح «باگ قدیمی pandas» تأیید نشد؛ exact code/commit هنوز `missing` است و باید برای lookahead/future leakage ممیزی شود.
- Strategy Specifications یا backtest outputs مربوط به سیستم‌های نام‌برده‌شده — هنوز `missing` هستند.

## Audit reference

برای وضعیت `supported / unsupported / mismatch / externally verified` هر مورد به:

- `docs/ASSET_DEFINITION_AUDIT.md`

مراجعه شود.

## Rule

تا زمانی که فایل واقعی، commit، مسیر repository یا محتوای منبع در اختیار این پروژه قرار نگیرد:

1. نام artifact حفظ می‌شود.
2. وضعیت آن `missing` باقی می‌ماند.
3. توضیح عمومی یا expansion حدسی جای Artifact واقعی را نمی‌گیرد.
4. هیچ placeholder حاوی محتوای ساختگی با همان نام ایجاد نمی‌شود تا Retrieval آلوده نشود.
5. هر مورد externally verified فقط در حد terminology عمومی معتبر است، نه به‌عنوان specification داخلی پروژه.
