# Salem Makki — Personal Portfolio

**Salem Makki | Programmer & Systems Analyst** — موقع شخصي احترافي ثنائي اللغة (عربي RTL / إنجليزي LTR)، مع لوحة تحكم كاملة لإدارة المحتوى دون الحاجة لتعديل الكود.

> **Makki Developer** · Flask · SQLAlchemy · MySQL · Vanilla JS/CSS

---

## المحتويات
1. [المزايا](#المزايا)
2. [التصور المعماري](#التصور-المعماري)
3. [هيكل المجلدات](#هيكل-المجلدات)
4. [تصميم قاعدة البيانات](#تصميم-قاعدة-البيانات)
5. [التثبيت والتشغيل محلياً](#التثبيت-والتشغيل-محلياً)
6. [استخدام لوحة التحكم](#استخدام-لوحة-التحكم)
7. [الأمان](#الأمان)
8. [الاختبارات](#الاختبارات)
9. [النشر على خادم](#النشر-على-خادم-production)
10. [التخصيص والتوسعة](#التخصيص-والتوسعة)

---

## المزايا

**واجهة الزوار**
- هوية بصرية "System Blueprint": شبكة مخطط تقني، عُقد متحركة تفاعلية (Canvas)، بطاقة Terminal، تدرجات أزرق/بنفسجي.
- وضع داكن / فاتح (يُحفظ اختيار الزائر ويحترم إعداد النظام).
- عربي RTL وإنجليزي LTR مع زر تبديل؛ كل المحتوى قابل للإدخال باللغتين (مع رجوع تلقائي للغة الأخرى إن كان الحقل فارغاً).
- الأقسام: الواجهة (Hero) · من أنا · المهارات · الخدمات · المشاريع · التعليم والخبرات · معرض الصور · التواصل.
- صفحات مستقلة لكل قسم + صفحة تفاصيل لكل مشروع مع معرض صور وعارض (Lightbox) بلوحة المفاتيح واللمس.
- نموذج تواصل يعمل بـ AJAX مع رسائل نجاح/خطأ واضحة لكل حقل (ويعمل بدون JavaScript أيضاً).
- نسخ البريد بنقرة، رابط واتساب مباشر، روابط GitHub / Facebook / LinkedIn (الروابط الفارغة لا تظهر أبداً).
- SEO: عناوين ووصف لكل صفحة، Open Graph، `hreflang`، JSON-LD (Person)، `sitemap.xml`، `robots.txt`.
- إمكانية الوصول: Skip link، تركيز واضح، ARIA للتبويبات والعارض، احترام `prefers-reduced-motion`.
- متجاوب بالكامل (هاتف / لوحي / حاسوب) وبدون أي مكتبات JavaScript خارجية.

**لوحة التحكم** (`/admin` — قابل للتغيير)
- تسجيل دخول آمن، تعديل البيانات الشخصية والصور (شخصية / من أنا / غلاف).
- إدارة المشاريع (صور متعددة، ترتيب، غلاف، تصنيفات، روابط GitHub/Demo، نشر/مسودة، مميز).
- إدارة المهارات وتصنيفاتها (مستوى إتقان اختياري — لا نسب مئوية وهمية).
- إدارة الخدمات، التعليم والخبرات (تعليم، خبرة، دورة، شهادة، إنجاز)، ومعرض الصور.
- صندوق الرسائل الواردة (مقروء/غير مقروء، حذف، رد عبر البريد).
- إخفاء/إظهار الأقسام وإعادة ترتيبها، تعديل روابط التواصل ونصوص الواجهة وSEO.
- قائمة "اكتمال الملف" لتذكيرك بما تبقى (الصورة، البريد، الروابط، أول مشروع حقيقي...).

---

## التصور المعماري

```
┌──────────────┐   HTTP    ┌───────────────────────────── Flask app ─────────────────────────────┐
│  المتصفح      │ ───────▶ │  before_request: اللغة + CSP nonce     after_request: رؤوس الأمان   │
│ HTML/CSS/JS   │          │                                                                     │
└──────────────┘          │  Blueprint public  (/ , /projects/<slug>, /contact, ...)            │
                           │  Blueprint admin   (/admin/...)  ← login_required + CSRF            │
                           │        │                     │                                      │
                           │   templates (Jinja2)    utils: uploads (Pillow) · security · mailer │
                           │        │                     │                                      │
                           │        └──── SQLAlchemy ORM (models.py) ────┐                       │
                           └────────────────────────────────────────────┼───────────────────────┘
                                                                        ▼
                                              MySQL (utf8mb4)     static/uploads/ (WebP)
```

**لماذا هذه التقنيات؟**
- **Flask + SQLAlchemy + MySQL** كما طلبت: خفيفة، منظمة، سهلة الاستضافة، وقابلة للتوسع (Blueprints + ORM).
- **Jinja (Server-side rendering) + Vanilla JS** بدلاً من React/Vue: صفحات تُعرض كاملة من الخادم ← أسرع تحميلاً وأفضل لمحركات البحث، ولا حاجة لخطوة build.
- **Pillow** للتحقق من الصور وإعادة ترميزها إلى WebP (أمان + سرعة).
- **Flask-WTF** لحماية CSRF على كل النماذج.

---

## هيكل المجلدات

```
portfolio/
├── run.py / wsgi.py          نقطة التشغيل
├── config.py                 الإعدادات (كلها من متغيرات البيئة)
├── .env.example              نموذج ملف البيئة
├── requirements.txt
├── database/schema.sql       مخطط MySQL الكامل (مولَّد من النماذج)
├── tests/                    اختبارات pytest (23 اختبار)
└── app/
    ├── __init__.py           Application factory + رؤوس الأمان + معالجات الأخطاء
    ├── models.py             جداول قاعدة البيانات
    ├── content.py            الملف الشخصي والأقسام (مشترك)
    ├── i18n.py               نصوص الواجهة عربي/إنجليزي
    ├── icons.py              أيقونات SVG مضمّنة
    ├── cli.py                أوامر: init-db, create-admin, seed, clear-demo, export-schema
    ├── public/routes.py      صفحات الزوار
    ├── admin/routes.py       لوحة التحكم
    ├── utils/                uploads.py · security.py · mailer.py
    ├── templates/
    │   ├── base.html, partials/_macros.html
    │   ├── public/ (home, page, projects, project_detail, sections/_*.html)
    │   ├── admin/  (login, dashboard, profile, projects, skills, ...)
    │   └── errors/error.html
    └── static/
        ├── css/main.css, css/admin.css
        ├── js/main.js, js/admin.js
        ├── img/favicon.svg
        └── uploads/          الصور المرفوعة (غير مضمّنة في git)
```

---

## تصميم قاعدة البيانات

```
admin_users ── (مستقل)                 login_attempts ── (سجل محاولات الدخول)
profile      ── صف واحد: الهوية، النصوص، الصور، روابط التواصل، SEO
sections     ── key, is_visible, sort_order   (ترتيب وظهور أقسام الرئيسية)

skill_categories 1 ──< skills               (ON DELETE CASCADE)
project_categories 1 ──< projects           (ON DELETE SET NULL)
projects 1 ──< project_images               (ON DELETE CASCADE)
services · timeline_entries(kind) · gallery_images(category) · messages
```

- كل حقل نصي يظهر للزوار له نسختان: `*_ar` و `*_en`.
- الصور تُخزَّن كملفات في `static/uploads/<folder>/` ويُحفظ مسارها فقط في القاعدة.
- الترميز `utf8mb4` لدعم العربية والرموز التعبيرية.
- الملف الكامل: [`database/schema.sql`](database/schema.sql) (يُعاد توليده بـ `flask export-schema`).

---

## التثبيت والتشغيل محلياً

### المتطلبات
- Python 3.10+
- MySQL 8 أو MariaDB 10.5+

### 1) تجهيز البيئة
```bash
cd portfolio
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
```

ولّد مفتاحاً سرياً وضعه في `SECRET_KEY` داخل `.env`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2) إنشاء قاعدة البيانات (MySQL)
```sql
-- داخل mysql -u root -p
CREATE DATABASE salem_portfolio CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'portfolio_user'@'localhost' IDENTIFIED BY 'ضع_كلمة_مرور_قوية';
GRANT ALL PRIVILEGES ON salem_portfolio.* TO 'portfolio_user'@'localhost';
FLUSH PRIVILEGES;
```
ثم عدّل `DATABASE_URL` في `.env`:
```
DATABASE_URL=mysql+pymysql://portfolio_user:كلمة_المرور@localhost:3306/salem_portfolio?charset=utf8mb4
```

### 3) إنشاء الجداول والمحتوى الأولي وحساب المدير
```bash
export FLASK_APP=run.py            # Windows PowerShell: $env:FLASK_APP="run.py"
flask init-db                      # ينشئ الجداول (أو استخدم: mysql -u root -p < database/schema.sql)
flask seed                         # بياناتك المعروفة + محتوى تجريبي مُعلَّم بوضوح
flask create-admin                 # يطلب اسم المستخدم وكلمة المرور (10 أحرف على الأقل)
```
> استخدم `flask seed --no-demo` إن لم ترغب في أي محتوى تجريبي.

### 4) التشغيل
```bash
flask run --debug
```
- الموقع: <http://localhost:5000>
- لوحة التحكم: <http://localhost:5000/admin>

> **تشغيل سريع بدون MySQL (للتجربة فقط):** إن لم تضع `DATABASE_URL` يستخدم التطبيق SQLite تلقائياً في `instance/dev.sqlite`.

---

## استخدام لوحة التحكم

| ما تريد فعله | المكان |
|---|---|
| تغيير الصورة الشخصية / صورة "من أنا" / الغلاف | البيانات الشخصية ← الصور |
| تعديل العبارة التعريفية والوصف المختصر | البيانات الشخصية ← الواجهة الرئيسية |
| البريد، واتساب، GitHub، Facebook، LinkedIn | البيانات الشخصية ← التواصل |
| إضافة مشروع مع عدة صور | المشاريع ← إضافة مشروع |
| تصنيفات المشاريع | أسفل صفحة المشاريع |
| المهارات وتصنيفاتها | المهارات |
| المؤهل، الدورات، الشهادات، الخبرات، الإنجازات | التعليم والخبرات |
| رفع صور للمعرض | معرض الصور |
| إخفاء قسم أو تغيير ترتيبه | الأقسام وترتيبها |
| قراءة الرسائل والرد عليها | الرسائل |
| تغيير اسم المستخدم أو كلمة المرور | الحساب والأمان |

### عن المحتوى التجريبي
الأمر `flask seed` يضيف **فقط** المعلومات التي قدّمتها (الاسم، المسمى، العلامة، الوصف، التقنيات، الخدمات)، ويضيف عناصر تجريبية **مُعلَّمة بـ `[تجريبي]` / `[Demo]`** (3 مشاريع، 3 عناصر تعليم/دورات/شهادات، 4 صور معرض، ونص أهداف مهنية) لتوضيح شكل التصميم.
لا توجد أي شهادات أو خبرات أو أرقام حقيقية مخترعة. لحذف كل العناصر التجريبية دفعة واحدة:
```bash
flask clear-demo
```
حقول التواصل (البريد، واتساب، الروابط) تُترك **فارغة** حتى تملأها أنت، والفارغ منها لا يظهر في الموقع.

---

## الأمان

- **لا أسرار في الكود:** كل المفاتيح وكلمات المرور في `.env` (مستثنى من git). في `APP_ENV=production` يرفض التطبيق العمل بدون `SECRET_KEY`.
- **كلمات المرور** مُشفّرة (Werkzeug scrypt/pbkdf2). تغيير كلمة المرور يُبطل كل الجلسات القديمة.
- **الجلسات:** `HttpOnly`، `SameSite=Lax`، `Secure` (عند HTTPS)، تجديد الجلسة عند الدخول (منع Session Fixation)، مدة محددة.
- **منع التخمين:** قفل مؤقت بعد 5 محاولات فاشلة لكل IP لمدة 15 دقيقة (قابل للتعديل).
- **CSRF** على كل النماذج وكل عمليات الحذف (POST فقط).
- **رفع الملفات:** امتدادات محددة + فحص فعلي بـ Pillow + حد للحجم وللأبعاد (منع Decompression bomb) + إعادة ترميز إلى WebP (تُزال البيانات الوصفية وأي محتوى مدسوس) + أسماء عشوائية + لا حذف خارج مجلد الرفع.
- **XSS:** كل المحتوى يُعرض مع escaping تلقائي؛ الروابط تقبل `http/https` فقط (يُرفض `javascript:` وغيرها).
- **رؤوس أمان:** CSP بـ nonce، `X-Frame-Options: DENY`، `nosniff`، `Referrer-Policy`، HSTS (مع HTTPS)، و`noindex` + `no-store` لصفحات الإدارة.
- **نموذج التواصل:** حقل Honeypot ضد الروبوتات + حد للرسائل لكل IP في الساعة.
- **Open redirect:** روابط `next` تُقبل فقط إن كانت داخلية.
- يمكنك تغيير مسار الإدارة عبر `ADMIN_URL_PREFIX` لإخفائه عن الروبوتات.

---

## الاختبارات

```bash
pip install -r requirements-dev.txt
python -m pytest -q
# على MySQL حقيقية (قاعدة اختبار منفصلة!):
TEST_DATABASE_URL="mysql+pymysql://user:pass@localhost/salem_test?charset=utf8mb4" python -m pytest -q
```
تغطي الاختبارات: كل الصفحات، تبديل اللغة، رؤوس الأمان، XSS، نموذج التواصل (نجاح، أخطاء، Honeypot، حد الإرسال)، الحماية بتسجيل الدخول، قفل التخمين، إبطال الجلسات، رفع الصور ورفض الملفات الضارة، CRUD للمشاريع والمهارات والخدمات والخبرات، ترتيب الأقسام، الرسائل، وفرض CSRF.

---

## النشر على خادم (Production)

1. اضبط في `.env`: `APP_ENV=production`، `SECRET_KEY` قوي، `SESSION_COOKIE_SECURE=true`، `SITE_URL=https://your-domain`، و`PROXY_FIX=true` إن كان خلف Nginx.
2. شغّل عبر Gunicorn:
   ```bash
   gunicorn -w 3 -b 127.0.0.1:8000 run:app
   ```
3. مثال Nginx مختصر:
   ```nginx
   server {
       server_name your-domain.com;
       client_max_body_size 25M;
       location /static/ { alias /path/to/portfolio/app/static/; expires 30d; }
       location / { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host;
                    proxy_set_header X-Forwarded-For $remote_addr; proxy_set_header X-Forwarded-Proto $scheme; }
   }
   ```
4. فعّل HTTPS (مثلاً Let's Encrypt / certbot)، واحتفظ بنسخ احتياطية من قاعدة البيانات ومجلد `app/static/uploads/`.
5. (اختياري) لاستقبال إشعار بريدي عند وصول رسالة جديدة املأ متغيرات `MAIL_*`.

---

## التخصيص والتوسعة

- **الألوان والخطوط:** متغيرات CSS في أعلى `app/static/css/main.css` (`--blue`, `--violet`, ...).
- **نصوص الواجهة الثابتة:** `app/i18n.py`.
- **أيقونات جديدة:** أضفها في `app/icons.py` (وإلى `ICON_NAMES` لتظهر في منتقي الأيقونات).
- **قسم جديد:** نموذج في `models.py` ← مسار في `public/routes.py` ← قالب `templates/public/sections/_new.html` ← أضف المفتاح في `content.SECTION_META`.
- **لغة ثالثة:** أضفها إلى `LANGUAGES` في `i18n.py` وأضف أعمدة `*_xx` للنماذج.
