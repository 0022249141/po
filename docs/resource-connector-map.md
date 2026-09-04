# نقشه منابع و اتصالات — تغذیه دانش چارچوب ICT/SMC/RTM/Dealer-Inventory به ChatGPT
*بررسی‌شده: سپتامبر ۲۰۲۶*

**نتیجه:** فهرست زیر در ۸ دسته — از شالوده نظری تا اتصال داده و روش فنی اتصال به ChatGPT. منابعی که از قبل در پایپ‌لاین ترجمه PDF شما پوشش داده شده‌اند (BTMM، MMXM، ICT London Close Killzone، Choch Plan، 1AM CRT) تکرار نشده؛ تمرکز روی منابع **جدید و مکمل**.

---

## ۱) شالوده ICT / Smart Money Concepts (SMC) و Wyckoff
- **Inner Circle Trader (ICT)** — یوتیوب [@innercircletrader](https://youtube.com/@innercircletrader) | ایکس [@I_Am_The_ICT](https://x.com/I_Am_The_ICT). نکته: ICT هرگز عضویت پولی درخواست نمی‌کند؛ هر صفحه با ادعای «منتورشیپ پولی ICT» جعلی است.
- **Wyckoff Method** — منبع اصلی مفهوم Accumulation/Distribution/Composite Man که خودِ ICT و SMC هم از آن وام گرفته‌اند: [wyckoffanalytics.com](https://www.wyckoffanalytics.com) (بنیان‌گذار Roman Bogomazov، مدرس سابق Golden Gate University) با Primer رایگان؛ دوره دانشگاهی رسمی: Golden Gate University, course FI-354.
- برای گسترش پایپ‌لاین ترجمه به منابع تازه (فراتر از BTMM/MMXM موجود)، همین دو کانال منابع اصلی (نه بازنشر شخص ثالث) این مکتب فکری‌اند.

## ۲) منبع اصلی RTM (Read The Market) — IF Myante
- **[readthemarket.com](https://readthemarket.com)** — سایت رسمی انجمن؛ نوشته‌های مستقیم IF Myante + «Markepedia» (پایه واژگان FTR / BSZ / MPL / Quasimodo / Compression که در اسکیل `rtm-fshcd` شما فرمالیزه شده‌اند).
- **[rtmacademy.com](https://www.rtmacademy.com)** — نسخه دوره‌ای و ساختاریافته‌تر همان محتوا.
- نکته بی‌طرفانه: در انجمن‌هایی مثل ForexFactory بحث واقعی درباره میزان شفافیت IF Myante در مقایسه با نسل قدیمی‌تر RTM (Redsword، KennyZ) وجود دارد. برای تغذیه دانش ChatGPT فقط از این دو منبع رسمی استفاده کنید، نه کپی‌های بازنشرشده در سایت‌های اشتراک PDF.

## ۳) میکروساختار بازارساز و موجودی — سطح آکادمیک (فرمول‌بندی Dealer State Machine)
- مقالات کلاسیک (در هر پایگاه جست‌وجوی آکادمیک قابل‌یافتن): **Kyle 1985**، **Glosten–Milgrom 1985**، **Ho & Stoll 1981**، **Grossman–Miller 1988** — پایه نظریه ریسک موجودی و معامله‌گر مطلع؛ منبع نظری واقعیِ پشتِ اصطلاح «Dealer Inventory Logic» خودتان.
- نسخه محاسباتی مدرن، رایگان روی arXiv: [arxiv.org/abs/2003.05958](https://arxiv.org/abs/2003.05958) («Optimal Market Making with Persistent Order Flow») و [arxiv.org/abs/2407.17393](https://arxiv.org/abs/2407.17393) — الهام کمّی برای لایه Quant Gate و امتیازدهی Confluence Score، نه برای روایت روزانه.

## ۴) Auction Market Theory / Market Profile — مکمل طبیعی واژه «مزایده»
چون کل چارچوب شما بر پایه استعاره auction بنا شده، این دو منبع مستقیماً هم‌راستا هستند:
- **James Dalton — «Mind Over Markets»** و **«Markets in Profile»**: کدگذاری رسمی نظریه Steidlmayer (CBOT).
- **[cmegroup.com](https://www.cmegroup.com) — بخش Market Profile Education**: آموزش رایگان رسمی بورس؛ واژگان Value Area / POC / Initiative vs. Responsive مستقیماً روی لایه Dealing Range شما قابل‌تطبیق است.

## ۵) اتصال داده — بازار آبشده / ایران
- **[tgju.org](https://www.tgju.org) — بخش «قیمت آبشده»** (نقدی / بنکداری / کمتر از کیلو): مرجع صحت‌سنجی لحظه‌ای مستقل از فید MT5 بروکرتان (API رسمی مستند عمومی ندارد؛ برای اتصال خودکار نیاز به استخراج صفحه است).
- فید فعلی‌تان (فرمت `general-platforms` CSV) طبق یادداشت‌های قبلی همچنان تنها فرمت قابل‌اتکا برای اینترادی است؛ چیزی برای تعویض نیست.

## ۶) اتصال داده — XAUUSD / جهانی
- **[dukascopy.com](https://www.dukascopy.com)** — دیتای تیک/دقیقه‌ای رایگان XAUUSD (بخش Historical Data) برای بک‌تست موازی با MT5.
- **TradingView** — کراس‌چک بصری + اسکریپت‌های متن‌باز جامعه (Wyckoff، SMC، Order-Block) برای اعتبارسنجی منطق سوئینگ در `smcp-v3-architecture`.
- **[tradingeconomics.com/api](https://tradingeconomics.com/api)** و **[forexfactory.com/calendar](https://www.forexfactory.com/calendar)** — رویدادهای کلان (FOMC/NFP/CPI) برای لایه Time Logic / Volatility State.

## ۷) ابزار کدنویسی و بک‌تست — برای ریپوی `0022249141/P`
- پکیج رسمی پایتون متاکوتز: `pip install MetaTrader5` — پل مستقیم پایتون↔MT5.
- **[mql5.com/en/articles](https://www.mql5.com/en/articles)** — همان منبعی که quant-engine-9phase از آن سرچشمه گرفته؛ آرشیو بزرگ مقاله+کد آماده تطبیق.
- گیت‌هاب — جست‌وجوی تاپیک‌های `smart-money-concepts` و `ict-trading` برای پیاده‌سازی‌های متن‌باز OB/FVG، جهت کراس-چک منطق سوئینگ (بعد از رفع باگ `rolling(center=True)` در ادیت اخیر).

## ۸) اتصال عملی این منابع به ChatGPT
- **Knowledge files در Custom GPT**: تا ۲۰ فایل به‌ازای هر GPT (PDF/TXT/DOCX/CSV/JSON)، بازیابی از نوع RAG. فایل‌های سبک و متراکم (`glossary.md`، نسخه فعلی SKILL.md ۶لایه+حکم، `MARKET_PARAMS.md`) را نسبت به ۴۴ PDF خام در اولویت بگذارید — دقت RAG روی فایل‌های حجیم افت می‌کند؛ دقیقاً همان جهتی که با کوچک‌سازی از ۲۰ لایه به ۷/۶ لایه رفتید.
- **Connectors (Google Drive / GitHub)**: به‌جای آپلود دستی مکرر، پوشه PDFهای ترجمه‌شده یا ریپوی `0022249141/P` را یک‌بار وصل کنید تا با هر commit/تغییر به‌صورت خودکار sync شود.
- نیازمند پلن ChatGPT Plus/Team/Enterprise برای ساخت Custom GPT.
