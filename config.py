import os
from dotenv import load_dotenv

load_dotenv()

SELF_TOKENS = [t.strip() for t in os.getenv("SELF_TOKENS", "").split(",") if t.strip()]
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
ALLOWED_GUILD_ID = int(os.getenv("ALLOWED_GUILD_ID", "0")) if os.getenv("ALLOWED_GUILD_ID") else None
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
LOG_WEBHOOK_URL = os.getenv("LOG_WEBHOOK_URL")
MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "30"))
MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "60"))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

if not SELF_TOKENS:
    raise ValueError("❌ SELF_TOKENS غير موجودة في .env")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود في .env")

print(f"[✅] تم تحميل {len(SELF_TOKENS)} توكن")
print(f"[✅] OWNER_ID: {OWNER_ID}")
