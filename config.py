import os
from dotenv import load_dotenv

load_dotenv()

# ===== التوكنات =====
SELF_TOKENS = [t.strip() for t in os.getenv("SELF_TOKENS", "").split(",") if t.strip()]
BOT_TOKEN    = os.getenv("BOT_TOKEN")

# ===== الأمان =====
OWNER_ID         = int(os.getenv("OWNER_ID", "0"))
ALLOWED_GUILD_ID = int(os.getenv("ALLOWED_GUILD_ID", "0")) if os.getenv("ALLOWED_GUILD_ID") else None

# ===== ويب هوك =====
WEBHOOK_URL     = os.getenv("WEBHOOK_URL")
LOG_WEBHOOK_URL = os.getenv("LOG_WEBHOOK_URL")

# ===== Supabase =====
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ===== إعدادات الفحص =====
# ✅ رفعنا الـ Delay من 20-40 إلى 45-90 لتقليل نسبة الخطر
MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "45"))
MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "90"))

# ===== User-Agents محدّثة (Chrome 124) =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

# ===== التحقق من المتغيرات الأساسية =====
if not SELF_TOKENS:
    raise ValueError("❌ SELF_TOKENS غير موجودة في .env")

if not WEBHOOK_URL:
    raise ValueError("❌ WEBHOOK_URL غير موجود في .env")

if not OWNER_ID:
    print("⚠️ تحذير: OWNER_ID غير مضبوط، أوامر البوت لن تكون محمية")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ تحذير: Supabase غير مضبوط، سيتم استخدام JSON محلي")

print(f"[✅] تم تحميل {len(SELF_TOKENS)} توكن")
print(f"[✅] OWNER_ID: {OWNER_ID}")
print(f"[✅] ALLOWED_GUILD_ID: {ALLOWED_GUILD_ID}")
print(f"[✅] DELAY: {MIN_DELAY_SECONDS}-{MAX_DELAY_SECONDS} ثانية")
