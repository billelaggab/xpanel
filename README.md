<div align="center">

# 📡 Xtream UI — Modernized Installer & XPanel

### تحليل معماري كامل · مثبّت مُحدَّث بلغة Python 3 · واجهة إدارة جديدة بخط Cairo

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)](#)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04%20%7C%2022.04%20%7C%2024.04-E95420?logo=ubuntu&logoColor=white)](#)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%20%7C%208.4-4479A1?logo=mysql&logoColor=white)](#)
[![PHP](https://img.shields.io/badge/PHP-8.0+-777BB4?logo=php&logoColor=white)](#)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)](#)
[![Dependencies](https://img.shields.io/badge/panel%20dependencies-0-success)](#)

**لا jQuery · لا Bootstrap · لا CDN · لا طلبات شبكة خارجية**

</div>

---

## 📋 جدول المحتويات

| # | القسم | الوصف |
|:--:|---|---|
| 1️⃣ | [نظرة عامة](#-نظرة-عامة) | ما هو هذا المستودع وما الذي يحتويه |
| 2️⃣ | [بنية المستودع](#-بنية-المستودع) | شجرة الملفات ودور كل جزء |
| 3️⃣ | [البدء السريع](#-البدء-السريع) | التثبيت خطوة بخطوة |
| 4️⃣ | [نشر `xpanel.zip`](#-نشر-xpanelzip) | رفع الواجهة كأصل إصدار على GitHub |
| 5️⃣ | [`install.py`](#️-installpy--المثبّت-المُحدَّث) | الاستبدالات والمتغيرات البيئية |
| 6️⃣ | [XPanel](#-xpanel--واجهة-الإدارة-الجديدة) | التصميم والأمان والتوافق |
| 7️⃣ | [المنافذ والمسارات](#-المنافذ-والمسارات) | مرجع التشغيل |
| 8️⃣ | [التقرير التحليلي](#-التقرير-التحليلي) | دراسة السكربت الأصلي |
| 9️⃣ | [التحقق والجودة](#-التحقق-والجودة) | الفحوصات والنتائج |
| 🔟 | [الأمان والتحذيرات](#-الأمان-والتحذيرات) | ما يجب فعله بعد التثبيت |

---

## 🔍 نظرة عامة

هذا المستودع يضم ثلاثة أعمال مترابطة حول منظومة **Xtream UI** (المرآة المجتمعية لمنصة Xtream Codes بعد إغلاقها عام 2019):

<div align="center">

| 🧪 التحليل | 🔧 إعادة البناء | 🎨 الواجهة الجديدة |
|:--:|:--:|:--:|
| **`report.md`** | **`install.py`** | **`xpanel/`** |
| تشريح معماري وأمني<br/>للسكربت الأصلي<br/>(Python 2.7) | نفس الوظائف حرفياً<br/>بحزم ومكتبات<br/>ما زالت مدعومة | بديل كامل لـ<br/>`release_22f.zip`<br/>و`newstuff.zip` |

</div>

### 🎯 الأهداف

- ✅ **فهم** كيفية عمل منظومة بث IPTV واسعة النطاق (خادم رئيسي + عقد موازنة حمل).
- ✅ **تحديث** المثبّت ليعمل على Ubuntu 20.04 / 22.04 / 24.04 بدل 16.04 / 18.04 المنتهية الدعم.
- ✅ **استبدال** كل مكتبة بلغت نهاية عمرها (Python 2.7، `libcurl3`، `mcrypt`، `libpng12-0`، `nscd`، `libjemalloc1`…).
- ✅ **إعادة بناء** الواجهة الرسومية من الصفر بمعمارية حديثة وإصلاح ثغراتها البنيوية.
- ✅ **الحفاظ** على التوافق الكامل مع مخطط قاعدة البيانات الأصلي ومع الثنائيات مغلقة المصدر.

---

## 🗂️ بنية المستودع

```
.
├── 📄 install.py                 المثبّت المُحدَّث (Python 3) — 1,250+ سطر
├── 📄 report.md                  التقرير التحليلي الشامل (11 قسماً)
├── 📄 README.md                  هذا الملف
│
├── 📁 xpanel/                    ← الواجهة الجديدة (346 KB / 31 ملفاً)
│   ├── 📁 admin/                 لوحة الإدارة (23 ملف PHP / 4,789 سطراً)
│   │   ├── config.php            الإقلاع: فك تشفير config · mysqli · جلسة · CSRF · i18n
│   │   ├── functions.php         المصادقة · الصلاحيات · بيان الكيانات · الإحصاءات
│   │   ├── totp.php              مصادقة ثنائية RFC 6238 (TOTP)
│   │   ├── login.php             دخول + 2FA + reCAPTCHA + حماية من الإغراق
│   │   ├── dashboard.php         مؤشرات الأداء + رسم SVG + حيوية الخادم
│   │   ├── table.php             صفحة قوائم عامة (تستبدل 48 صفحة)
│   │   ├── record.php            عرض سجل مفرد (يستبدل ~40 صفحة)
│   │   ├── settings.php          الإعدادات + معلومات البنية التحتية
│   │   ├── profile.php           تغيير كلمة المرور + إعادة ضبط 2FA
│   │   ├── api.php               نقطة JSON موحّدة (list/chart/vitals/delete/…)
│   │   ├── header.php · sidebar.php · footer.php
│   │   ├── 📁 lang/              ar.php + en.php (148 مفتاحاً متطابقاً)
│   │   └── 📁 assets/
│   │       ├── css/xpanel.css    نظام التصميم (31.6 KB)
│   │       ├── js/xpanel.js      طبقة التطبيق الأصلية (26.8 KB)
│   │       └── fonts/            cairo-{arabic,latin-ext,latin}.woff2 (79.5 KB)
│   ├── 📁 wwwdir/                نقاط النهاية المواجهة للمشاهدين
│   │   ├── index.php             تحويل تمويهي إلى Google
│   │   ├── includes/streaming.php  نواة المصادقة والصلاحيات
│   │   ├── get.php               مولّد قوائم M3U/M3U8 (بث تدريجي)
│   │   ├── player_api.php        واجهة Xtream القياسية (JSON)
│   │   └── xmltv.php             دليل البرامج XMLTV
│   ├── 📁 crons/pid_monitor.php  مراقبة العمليات وتنظيف الاتصالات
│   ├── 📁 nginx/conf/admin_panel.conf   كتلة Nginx (تحوي `randomcodehere`)
│   ├── 📁 database/schema.sql    طبقة توافق متكررة التنفيذ (idempotent)
│   └── 📄 README.md              توثيق الواجهة
│
└── 📁 src/                       عارض تفاعلي (Next.js) للتقرير والكود
    ├── app/page.tsx              يقرأ report.md + install.py + xpanel/README.md
    └── components/ReportViewer.tsx   12 تبويباً تفاعلياً
```

---

## 🚀 البدء السريع

### ✔️ المتطلبات

| المكوّن | المطلوب |
|---|---|
| 🖥️ **نظام التشغيل** | Ubuntu Server `20.04 LTS` / `22.04 LTS` / `24.04 LTS` (`x86_64`) |
| 🔑 **الصلاحيات** | `root` أو `sudo` (يتحقق السكربت من `UID == 0`) |
| 🐍 **Python** | `3.8+` (مضمّن في أوبونتو الحديث) |
| 🌐 **الشبكة** | اتصال لتنزيل حزم `apt` وأصول الإصدار |

### 📥 التثبيت

```bash
# 1) اجلب المستودع
git clone https://github.com/<owner>/<repo>.git
cd <repo>

# 2) اجعل المثبّت قابلاً للتنفيذ
chmod +x install.py

# 3) شغّله كجذر
sudo ./install.py
```

### 💬 الأسئلة التفاعلية

| السؤال | الإدخال |
|---|---|
| `Installation Type [MAIN, LB]:` | `MAIN` للخادم الرئيسي · `LB` لعقدة موازنة الحمل |
| `Main Server IP Address:` | *(LB فقط)* عنوان IP للخادم الرئيسي |
| `MySQL Password:` | *(LB فقط)* كلمة مرور `user_iptvpro` المطبوعة عند تثبيت MAIN |
| `Load Balancer Server ID:` | *(LB فقط)* معرّف العقدة في لوحة الإدارة |
| `Start installation? Y/N` | `Y` |
| `Enter MySQL Root Password:` | **Enter فارغ** — على التثبيتات النظيفة يستخدم MySQL 8 مصادقة `auth_socket` |
| `Drop existing & create database? Y/N` | `Y` لتهيئة `xtream_iptvpro` واستيراد الجداول |

### 🎉 عند الانتهاء (وضع MAIN)

سيطبع المثبّت:

```
┌────────────────────────────────────────┐
│        Installation completed!         │
└────────────────────────────────────────┘

🔑  كلمة مرور MySQL للمستخدم user_iptvpro   ← احفظها لإضافة عقد LB لاحقاً
🔗  http://<SERVER_IP>:8080/<ACCESS_CODE>  ← رابط لوحة الإدارة
👤  admin / admin                          ← بيانات الدخول المبدئية
```

> [!WARNING]
> ⚠️ **غيّر كلمة مرور `admin/admin` فوراً** من صفحة `profile.php` بعد أول دخول.

---

## 📦 نشر `xpanel.zip`

تُوزَّع الواجهة الجديدة **كأصل إصدار (Release Asset) على GitHub**، تماماً كما هو الحال مع `release_22f.zip` و`newstuff.zip`.

### 1️⃣ الضغط

```bash
cd xpanel

# ✅ الطريقة الموصى بها: المحتوى في جذر الأرشيف
zip -r ../xpanel.zip . -x '*.DS_Store' -x '__MACOSX/*'

# ✅ أو مع مجلد غلاف — كلا الشكلين يعمل
cd .. && zip -r xpanel.zip xpanel -x '*.DS_Store'
```

### 2️⃣ الرفع

| الخطوة | التفصيل |
|---|---|
| 🏷️ أنشئ إصداراً | `Releases → Draft a new release` |
| 📎 ارفع الأصل | أرفق `xpanel.zip` (يُفضَّل مع `release_22f.zip` و`newstuff.zip`) |
| 🔗 الرابط النهائي | `https://github.com/<owner>/<repo>/releases/latest/download/xpanel.zip` |

> [!NOTE]
> 💡 استخدام `releases/latest/download/…` يعني أن `install.py` يلتقط **أحدث إصدار تلقائياً** دون تعديل أي رابط.

### 3️⃣ الأشكال المدعومة للأرشيف

يكشف `install.py` بنية الأرشيف **تلقائياً** عبر `findPanelRoot()` — كل هذه الأشكال تعمل:

| # | بنية الأرشيف | النتيجة |
|:--:|---|:--:|
| 1 | `admin/`, `wwwdir/`, `crons/`, `nginx/` في الجذر | ✅ |
| 2 | `xpanel/admin/`, `xpanel/wwwdir/`, … | ✅ |
| 3 | `xpanel-main/admin/`, … (ناتج «Download ZIP» من GitHub) | ✅ |
| ❌ | أرشيف لا يحتوي `admin/` | ⛔ رفض مع رسالة واضحة |

### 4️⃣ أولوية مصادر التثبيت

يُجرَّب كل مصدر بالترتيب، ويُستخدم أول ما ينجح:

```
1️⃣  ./xpanel            المصادر بجانب install.py   (دون شبكة — للتطوير)
        ↓ لم يوجد
2️⃣  xpanel.zip          أصل إصدار GitHub          (المسار الاعتيادي)
        ↓ فشل التنزيل أو التحقق
3️⃣  release_22f.zip     اللوحة الأصلية 22F        (ملاذ أخير)
    + newstuff.zip
```

### 5️⃣ توجيه التنزيل إلى مستودعك

```bash
sudo XPANEL_ZIP_URL="https://github.com/<you>/<your_mirror>/releases/latest/download/xpanel.zip" \
     ./install.py
```

### 🛡️ ما يفعله المثبّت بالأرشيف

| الخطوة | التفصيل |
|---|---|
| 🔐 **Zip-Slip guard** | رفض أي مدخل بمسار مطلق أو `..` قبل فك الضغط (التثبيت يعمل كجذر) |
| ✅ **CRC** | `ZipFile.testzip()` قبل كتابة أي بايت على القرص |
| 🌲 **كشف الجذر** | `findPanelRoot()` يتنزل حتى 4 مستويات بحثاً عن `admin/` |
| 📋 **النسخ** | `copyTree()` ينسخ `admin/` `wwwdir/` `crons/` `nginx/` |
| 🧬 **الحفاظ** | ملفات `main.tar.gz` القائمة (مثل `wwwdir/clients_live.php`) **لا تُمس** |
| 👤 **الملكية** | `chown -R xtreamcodes:xtreamcodes` + صلاحيات `644`/`755` |
| 🗄️ **المخطط** | `applyXPanelSchema()` يستورد `database/schema.sql` (متكرر التنفيذ) |
| 🧹 **التنظيف** | حذف `xpanel.zip` ومجلد الفك المؤقت في كل الحالات |

---

## ⚙️ `install.py` — المثبّت المُحدَّث

إعادة كتابة **1:1 وظيفياً** للسكربت الأصلي: نفس أسماء الدوال، نفس التسلسل، نفس الرسائل، نفس الملفات الناتجة على القرص — مع استبدال كل ما انتهى دعمه.

### 🔄 الاستبدالات الرئيسية

| الأصلي (غير مدعوم) | الجديد |
|---|---|
| `#!/usr/bin/python` (Python 2.7) | `#!/usr/bin/python3` (3.8+) |
| `urllib2` · `izip` · `.encode("base64")` | `urllib.request` · `zip()` · `base64.b64encode()` |
| `libcurl3` (+ حذف `libcurl4`) | `libcurl4` / `libcurl4t64` |
| `mcrypt` | `openssl` |
| `nscd` | `systemd-resolved` |
| `libpng12-0` (CVE-2015-8126) | `libpng16-16` / `libpng16-16t64` |
| `libgeoip-dev` | `libmaxminddb-dev` (GeoIP2) |
| `libjemalloc1` | `libjemalloc2` |
| `python-paramiko` | `python3-paramiko` |
| Ubuntu 16.04 / 18.04 | Ubuntu 20.04 / 22.04 / 24.04 |
| `random.choice()` لكلمات المرور | `secrets.choice()` (CSPRNG) |
| `os.system("... %s" % input)` | `subprocess.run([...])` + `shlex.quote()` |
| تعديل `/etc/sudoers` مباشرة | `/etc/sudoers.d/xtreamcodes` + `visudo -c` |
| استبدال `mysql.service` كاملاً | systemd **Drop-in override** |
| `GRANT ... IDENTIFIED BY` | `CREATE USER ...; GRANT ...;` (صيغة MySQL 8) |
| `release_22f.zip` + `newstuff.zip` | **`xpanel.zip`** (مع رجوع تلقائي) |

### 🗄️ ضبط MySQL الواعي بالإصدار

يُولَّد `/etc/mysql/my.cnf` **ديناميكياً** حسب الإصدار المثبت فعلياً، ويُتحقق منه بـ `mysqld --validate-config` قبل إعادة التشغيل:

| التعليمة القديمة | المعالجة |
|---|---|
| `query_cache_limit/size/type` | 🗑️ **حُذفت** (أُزيلت في MySQL 8.0 وكانت تمنع الإقلاع) |
| `expire_logs_days` | 🔁 `binlog_expire_logs_seconds = 864000` |
| `innodb_log_file_size` | 🔁 `innodb_redo_log_capacity` (لإصدارات 8.0.30+) |
| `innodb_buffer_pool_instances` | 🔁 تُحذف على 8.4+ (يُحسب تلقائياً) |
| `mysql_native_password` | 🔁 `authentication_policy` + تفعيل الإضافة إن وُجدت |
| `innodb_buffer_pool_size = 8G` | 📏 **60% من الذاكرة الفعلية** (512M–8G) |
| `innodb_lock_wait_timeout = 0` | 🔧 `50` (القيمة 0 تُرجع خطأً فورياً عند أي تنافس) |

### 🔧 المتغيرات البيئية

| المتغير | الوظيفة | الافتراضي |
|---|---|---|
| `XPANEL_ZIP_URL` | رابط `xpanel.zip` (للتوجيه إلى مستودعك) | رابط مرآة `emre1393/xtreamui_mirror` |
| `MAXMIND_LICENSE_KEY` | تفعيل `geoipupdate` الرسمي بدل رابط المرآة | *(فارغ)* |
| `DEBIAN_FRONTEND` | يُضبط تلقائياً على `noninteractive` | — |

### 🧩 دوال جديدة أضيفت

| الدالة | الغرض |
|---|---|
| `downloadXPanel()` | تنزيل `xpanel.zip` والتحقق من CRC وإرجاع جذر اللوحة |
| `findPanelRoot()` | كشف مجلد `admin/` داخل الأرشيف (3 أشكال + رفض الخاطئ) |
| `safeExtract()` | حماية من Zip-Slip قبل فك الضغط |
| `deployXPanel()` | النسخ + الملكية + الصلاحيات + تطبيق المخطط |
| `applyXPanelSchema()` | استيراد `database/schema.sql` |
| `copyTree()` | بديل `cp -rf` يحافظ على الأذونات |
| `xpanelZipUrl()` · `xpanelDir()` | تحديد مصدر اللوحة |
| `buildMySQLCnf()` · `writeAndValidateCnf()` | توليد وضبط وتحقق `my.cnf` |
| `installPackage()` | تثبيت مع بدائل تلقائية (أسماء `t64` في Ubuntu 24.04) |
| `checkLibPNGCompat()` | فحص `ldd` للثنائيات المرتبطة بـ `libpng12.so.0` |

### 🔒 ما بقي مطابقاً للأصل (عن قصد)

> [!IMPORTANT]
> 🔑 **مفتاح XOR** `5709650b0d7806074842c6de575025b1` — **مطابق بتاً ببت**، وتم التحقق برمجياً أن مخرج `encrypt()` الجديدة **متطابق تماماً** مع مخرج الدالة الأصلية في Python 2 لنفس المدخلات، لأن الثنائيات مغلقة المصدر داخل `main.tar.gz` تفك تشفير `config` بنفسها.

| العنصر | القيمة الثابتة |
|---|---|
| 🔌 المنافذ | MySQL `7999` · HTTP `8080` · HTTPS `8443` · RTMP `8880` |
| 📂 المسارات | `/home/xtreamcodes/iptv_xtream_codes/` |
| 🗄️ قاعدة البيانات | `xtream_iptvpro` · المستخدم `user_iptvpro` |
| 💾 نقاط `tmpfs` | `streams` بنسبة 90% · `tmp` بحجم 3G (`nosuid,nodev,noexec`) |
| 🎭 التمويه | رمز دخول عشوائي 12 محرفاً · تحويل الجذر إلى Google · تحييد نطاقات `xtream-codes.com` |
| 📦 حزم LB | آخر 3 حزم للـ MAIN فقط وتُحذف عبر `rPackages[:-3]` |

---

## 🎨 XPanel — واجهة الإدارة الجديدة

### 📊 المقارنة مع اللوحة الأصلية

| المقياس | `release_22f.zip` + `newstuff.zip` | `xpanel/` |
|---|---|---|
| 📦 الحجم | **33.2 MB** | **346 KB** *(أصغر ~96 مرة)* |
| 🐘 ملفات PHP | 144 ملفاً / 75,787 سطراً | **23 ملفاً / 4,789 سطراً** |
| 🎨 أصول الواجهة | 22 MB | **138 KB** |
| 📚 الاعتماديات | jQuery 3.3.1 + Bootstrap 4.3.1 + ~60 إضافة | **صفر** |
| 🌐 الطلبات الخارجية | خطوط Google + jsdelivr + chart.googleapis.com | **لا شيء** |
| 🖋️ الخط | Poppins / Work Sans (عن بُعد) | **Cairo** (محلي) |

### ✍️ التصميم بخط Cairo

- 🔤 **Cairo Variable Font** بثلاث مجموعات `woff2` (`arabic` + `latin-ext` + `latin`) تغطي الأوزان `200–1000` — **مستضافة محلياً** ومُتحقَّق منها (`wOF2`).
- ↔️ **دعم RTL/LTR** عبر الخصائص المنطقية (`inset-inline-start`, `padding-inline`) — نفس القواعد تعمل في الاتجاهين دون تكرار.
- 🌗 **سمة داكنة/فاتحة** بمتغيرات CSS، تُطبَّق قبل أول رسم (بدون وميض) وتُحفظ في `localStorage`.
- 📈 **رسم مساحي SVG مكتوب يدوياً** (~60 سطراً) يستبدل **تسع** مكتبات رسوم.
- 🧩 **أيقونات SVG مضمّنة** بدل أربع عائلات خطوط أيقونات.
- ♿ **وصولية**: رابط تخطٍّ · `aria-current` · `aria-live` · `:focus-visible` · `prefers-reduced-motion`.

### 🛡️ الثغرات البنيوية الثلاث — مُعالجة

| الثغرة في الأصل | المعالجة في XPanel |
|---|---|
| 🚫 **لا توجد رموز CSRF إطلاقاً** | `random_bytes(32)` ملزم في كل طلب كتابة + `SameSite=Lax` |
| 🚫 **معرّف الجلسة = `md5(username)`** | معرّف عشوائي + `session_regenerate_id(true)` + ربط بالـ IP |
| 🚫 **ملح تجزئة ثابت `xtreamcodes`** | `password_hash()` بملح عشوائي + **تحديث شفاف** عند أول دخول |

### 🔐 تحسينات أمنية إضافية

| المجال | التحسين |
|---|---|
| 💉 SQL | **Prepared Statements** في كل الكود + `xpanelIdent()` قائمة بيضاء للأسماء |
| 🖥️ تنفيذ الأوامر | **أُزيل `sexec()`/`exec()`/`BackgroundCLI` بالكامل** — بديلها `terminate` عبر `proc_open` بـ argv ثابت ورقم صحيح **ومحلياً فقط** |
| 🍪 الجلسات | `httponly=1` · `samesite=Lax` · `use_strict_mode=1` · `secure` تلقائياً على HTTPS |
| 🐞 الأخطاء | `display_errors=0` مفروض (الأصل كان `1` في `resize.php`) |
| 🔗 التحويل | `xpanelSafeReferrer()` يقبل `./file.php` من نفس المجلد فقط (إغلاق التحويل المفتوح) |
| 🎥 المشغّل | روابط التشغيل **لا تحمل أي بيانات اعتماد إدارية** (الأصل كان يضمّنها) |
| 🔑 2FA | تنفيذ TOTP محلي كامل (RFC 6238) بدل `chart.googleapis.com` المغلقة |
| 🌍 الترجمة | `lang/ar.php` + `lang/en.php` بمسار نسبي ومفتاح تبديل (الأصل: إنجليزية فقط بمسار مطلق) |

### 🗄️ التوافق مع قاعدة البيانات الأصلية

> [!NOTE]
> ✅ **لا يُعدَّل مخطط Xtream Codes إطلاقاً.** استُخرجت أسماء الجداول والأعمدة من كود اللوحة الأصلية نفسه قبل الكتابة.

| العنصر | التفصيل |
|---|---|
| 📋 الجداول المستخدمة | `streams` · `streams_sys` · `series` · `series_episodes` · `users` · `user_output` · `reg_users` · `member_groups` · `bouquets` · `packages` · `streaming_servers` · `stream_categories` · `user_activity_now` · `dashboard_statistics` · `admin_settings` · `settings` · `blocked_ips` · `blocked_user_agents` · `mag_devices` · `client_logs` · `login_flood` |
| 🏷️ دلالات `streams.type` | **1** = بث حي · **2** = فيلم · **3** = مسلسل · **4** = راديو |
| 🔑 مفاتيح الصلاحيات | نفسها (`is_admin`, `is_reseller`, `is_banned`, ومفاتيح `adv:*`) → **لا حاجة لأي ترحيل** |
| 🧬 `database/schema.sql` | **متكرر التنفيذ**: UNIQUE على `admin_settings.type` + جداول ناقصة + فهارس أداء عبر فحص `information_schema` — دون إسقاط أي جدول |

### 🧠 صفحة واحدة لكل القوائم

بدلاً من 99 صفحة PHP، يقود **بيان واحد** في `functions.php::xpanelEntities()` كل الشاشات:

```php
'streams' => [
    'title'   => 'live_streams',
    'perm'    => 'streams',
    'table'   => 'streams',
    'order'   => '`id` DESC',
    'search'  => ['stream_display_name', 'stream_source'],
    'filter'  => ['type' => 1],
    'columns' => [
        ['id', 'id', 'id', []],
        ['stream_display_name', 'name', 'text', []],
        ['stream_source', 'source', 'link', []],
        ['category_id', 'category', 'text', ['lookup' => 'stream_categories']],
        ['enabled', 'status', 'bool', []],
        ['id', 'actions', 'actions', ['entity' => 'streams']],
    ],
],
```

| المسار | الوظيفة |
|---|---|
| `table.php?entity=<key>` | عرض القائمة |
| `api.php?action=list&entity=<key>` | تزويد البيانات (JSON) |
| `record.php?entity=<key>&id=<n>` | عرض التفاصيل |

**الكيانات المدعومة:** `streams` · `movies` · `series` · `radios` · `lines` · `panel_users` · `servers` · `bouquets` · `packages` · `groups` · `connections` · `mag_devices`

> 💡 **إضافة شاشة جديدة = إضافة إدخال واحد في المصفوفة**، لا ملفاً جديداً.

### 🌐 نقاط النهاية المواجهة للمشاهدين

| النقطة | الوظيفة |
|---|---|
| `GET /get.php?username=&password=&type=&output=` | قائمة M3U/M3U8 مجمّعة حسب التصنيف، **بث تدريجي** لكل تصنيف |
| `GET /player_api.php?username=&password=&action=` | واجهة Xtream القياسية: `user_info`/`server_info`، التصنيفات، القنوات، الأفلام، المسلسلات، الحلقات |
| `GET /xmltv.php?username=&password=` | دليل XMLTV **صالح دائماً**، حتى لو كانت جداول EPG فارغة أو غائبة |
| `GET /` | تحويل إلى `https://www.google.com/` (تمويه) |

كل نقطة تمر عبر `includes/streaming.php` الذي يفرض — **قبل إصدار أي رابط**: صحة الاشتراك · `enabled` · `exp_date` · `blocked_ips` · `blocked_user_agents` · `max_connections`.

---

## 🔌 المنافذ والمسارات

### 🔢 المنافذ

| المنفذ | الاستخدام |
|:--:|---|
| **7999** | 🗄️ MySQL (محلياً + اتصال عقد LB) |
| **8080** | 📺 بث HTTP + لوحة الإدارة على `/<access_code>` |
| **8443** | 🔒 بث HTTPS |
| **8880** | 🎥 استقبال وإعادة بث RTMP |

### 📂 المسارات الرئيسية

| المسار | الوظيفة |
|---|---|
| `/home/xtreamcodes/iptv_xtream_codes/` | الجذر: الثنائيات وملفات البث |
| `…/config` | بيانات الاتصال مشفّرة بـ XOR + Base64 (صلاحية `0700`) |
| `…/admin/` | واجهة XPanel |
| `…/wwwdir/` | نقاط النهاية الموجهة للعملاء |
| `…/streams` | `tmpfs` في الرام بنسبة 90% لشرائح البث |
| `…/tmp` | `tmpfs` بحجم 3G للملفات المؤقتة |
| `…/GeoLite2.mmdb` | القاعدة الجغرافية (محمية بـ `chattr +i`) |
| `/etc/mysql/my.cnf` | الضبط المولَّد ديناميكياً (النسخة السابقة في `my.cnf.xc`) |
| `/etc/mysql/mysqld` | حقن `libjemalloc.so.2` عبر `LD_PRELOAD` |
| `/etc/systemd/system/mysql.service.d/xtreamcodes.conf` | Drop-in لضبط حدود MySQL |
| `/etc/systemd/system/xtreamcodes.service` | وحدة الإقلاع النظامية |
| `/etc/sudoers.d/xtreamcodes` | `sudo` محدود على `iptables` و`chattr` فقط |

### 🎛️ إدارة الخدمة

```bash
# حالة المنظومة
sudo systemctl status xtreamcodes.service

# إعادة تشغيل الخدمات
sudo systemctl restart xtreamcodes.service

# MySQL على المنفذ 7999
sudo systemctl status mysql.service
sudo ss -tlnp | grep 7999
```

---

## 📚 التقرير التحليلي

ملف **`report.md`** يوثّق دراسة كاملة للسكربت الأصلي في **11 قسماً**:

| القسم | المحتوى |
|:--:|---|
| 1️⃣ | الملخص التنفيذي |
| 2️⃣ | المعمارية العامة (MAIN / LB) مع مخطط ASCII |
| 3️⃣ | التشريح التفصيلي للكود دالة بدالة |
| 4️⃣ | المكونات التقنية (Technology Stack) |
| 5️⃣ | التقييم الفني والأمني + **جدول المكتبات غير المدعومة** |
| 6️⃣ | مسار تدفق البيانات أثناء التشغيل |
| 7️⃣ | المقارنة مع المعايير الحديثة (2026) |
| 8️⃣ | الخاتمة والتقييم النهائي |
| 9️⃣ | النسخة المحدّثة `install.py` (جدول الاستبدالات الكامل) |
| 🔟 | **تحليل الواجهة الرسومية** (تنزيل فعلي للأرشيفات وفحصها) |
| 1️⃣1️⃣ | **البديل المبني `xpanel/`** |

### 🖥️ العارض التفاعلي

يوجد أيضاً تطبيق **Next.js** في `src/` يعرض التقرير بـ **12 تبويباً تفاعلياً**، من بينها:

- 🔐 **محاكي تشفير XOR** يعمل في المتصفح بنفس مفتاح المنظومة
- 📦 **المكتبات غير المدعومة (EOL)** مع تواريخ الانتهاء والبدائل
- 🎨 **تحليل الواجهة الرسومية** بالأرقام المستخرجة من الأرشيفات
- 🧩 **XPanel** بشجرة الملفات وجدول الإصلاحات الأمنية

```bash
npm install && npm run dev
```

---

## ✅ التحقق والجودة

### 🧪 النتائج

| الفحص | الأداة | النتيجة |
|---|---|:--:|
| 🐍 صياغة `install.py` | `python3 -m py_compile` | ✅ |
| 🧮 تطابق مخرج `encrypt()` مع Python 2 | مقارنة بايت ببايت | ✅ مطابق 100% |
| 📦 كشف جذر `xpanel.zip` (3 أشكال) | `findPanelRoot()` | ✅ 3/3 |
| 🚫 حماية Zip-Slip | أرشيف خبيث بمسار `../` | ✅ مرفوض |
| 📋 النشر النهائي + الحفاظ على الملفات القائمة | `deployXPanel()` | ✅ 12/12 |
| 🔗 رابط `XPANEL_ZIP_URL` | الافتراضي + التجاوز | ✅ |
| 🐘 فاحص بنيوي PHP (أقواس/سلاسل/تعليقات/وسوم) | فاحص مخصص | ✅ 23/23 |
| 🔎 دوال مخصصة غير معرَّفة (من 89) | فحص دلالي | ✅ صفر |
| 🧱 تسرّب دوال `admin/` إلى `wwwdir/` و`crons/` | فحص دلالي | ✅ صفر |
| 📎 أهداف `require`/`include` + الأصول + الخطوط | فحص دلالي | ✅ كلها موجودة |
| 🌍 تطابق مفاتيح الترجمة `ar` ↔ `en` | فحص دلالي | ✅ 148 = 148 |
| 🖥️ `next typegen` · `tsc --noEmit` · `next build` | Next.js | ✅ بدون تحذيرات |
| 🩺 `build_and_start` (فحص `/api/health`) | المنصة | ✅ |

> [!NOTE]
> ℹ️ مفسّر PHP غير قابل للتثبيت في بيئة البناء، لذا استُخدم فاحصان مخصصان بـ Python للتحقق البنيوي والدلالي. وقد كشفا وأصلحا خطأين حقيقيين: ثابت غير معرَّف في `xmltv.php`، وكتلة إخفاء أسرار مشوّهة في `api.php`.

---

## 🔒 الأمان والتحذيرات

### 🚨 إجراءات إلزامية بعد التثبيت

| # | الإجراء | الأمر |
|:--:|---|---|
| 1️⃣ | **غيّر كلمة مرور `admin/admin` فوراً** | من `profile.php` |
| 2️⃣ | **احفظ كلمة مرور MySQL ورمز الوصول** في مدير كلمات مرور | — |
| 3️⃣ | **أغلق المنفذ 7999 عن الإنترنت العام** واسمح فقط لعقد LB | الأوامر أدناه |
| 4️⃣ | **فعّل المصادقة الثنائية** من `settings.php` | `google_2factor` |

```bash
# MySQL يستمع على bind-address = * لتمكين عقد LB.
# أغلقه عن العام واسمح فقط للعناوين الموثوقة:
sudo ufw deny 7999/tcp
sudo ufw allow from <LB_SERVER_IP> to any port 7999 proto tcp
```

### ⚠️ قيود معروفة

| القيد | التفصيل |
|---|---|
| 🔑 **مفتاح XOR ثابت** | `5709650b0d7806074842c6de575025b1` — **لا يمكن تغييره** لأن الثنائيات مغلقة المصدر في `main.tar.gz` تفك التشفير بنفسها |
| 🖼️ **`libpng12` ABI** | `libpng16` غير متوافقة ثنائياً مع `libpng12`. يفحص `checkLibPNGCompat()` الثنائيات عبر `ldd` ويُصدر تحذيراً صريحاً بأسماء المتأثرة |
| ⚡ **`innodb_flush_log_at_trx_commit = 0`** | أداء أعلى مقابل خطر فقدان آخر ثوانٍ من المعاملات عند انقطاع الطاقة المفاجئ |
| 📜 **`@reboot` في `/etc/crontab`** | محفوظ كاحتياط للصور دون systemd (مكرر بلا ضرر بجانب وحدة `xtreamcodes.service`) |

### ⚖️ إخلاء مسؤولية

> [!CAUTION]
> ⚖️ يُقدَّم هذا العمل لأغراض **الدراسة المعمارية، والتحليل الأمني، والاختبار المعملي، والتوافق التقني**.
>
> يعتمد `install.py` في بنيته على جلب ثنائيات مسبقة التجميع من مستودع مرآة خارجي، ويقع على عاتق المشغّل التحقق من سلامة المصادر الخارجية والالتزام الكامل بالقوانين وحقوق الملكية الفكرية وتراخيص البث قبل أي استخدام فعلي. **يتحمل المشغّل وحده مسؤولية أي استخدام.**

---

<div align="center">

**📡 Xtream UI · Modernized Installer & XPanel**

`report.md` · `install.py` · `xpanel/`

</div>
