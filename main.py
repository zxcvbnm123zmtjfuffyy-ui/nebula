#!/usr/bin/env python3
"""
Nebula - Discord Boost Monitor
مراقبة حسابات ديسكورد ومعرفة وقت جاهزية الـBoost
"""

import threading
import time
from flask import Flask
import config
from logger import log_info, log_success, log_error
from supabase_client import init_supabase
from scheduler import Scheduler

# ===== Flask (لـ UptimeRobot) =====
app = Flask(__name__)

@app.route('/')
def home():
    return "Nebula is running!", 200

@app.route('/ping')
def ping():
    return "PONG", 200

@app.route('/status')
def status():
    return {
        "status":   "online",
        "accounts": len(config.SELF_TOKENS),
        "uptime":   round(time.time() - start_time, 2)
    }, 200

def run_flask():
    app.run(host='0.0.0.0', port=8080, use_reloader=False)

# ===== المتغيرات العامة =====
start_time = time.time()
scheduler  = Scheduler()   # global عشان bot_commands يقدر يوصله

# ===== التشغيل الرئيسي =====
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║        🚀 NEBULA v2.0               ║
    ║    Discord Boost Monitor            ║
    ╚══════════════════════════════════════╝
    """)

    log_info(f"📊 عدد الحسابات: {len(config.SELF_TOKENS)}")
    log_info(f"🔒 السيرفر المسموح: {config.ALLOWED_GUILD_ID}")
    log_info(f"⏱️ التأخير: {config.MIN_DELAY_SECONDS}-{config.MAX_DELAY_SECONDS}ث")
    log_info(f"🔑 OWNER_ID: {config.OWNER_ID}")

    # ===== تهيئة Supabase =====
    init_supabase()

    # ===== Flask Thread =====
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    log_success("✅ Flask يعمل على منفذ 8080")

    # ===== Scheduler Thread =====
    scheduler_thread = threading.Thread(target=scheduler.run_loop, daemon=True)
    scheduler_thread.start()
    log_success("✅ Scheduler يعمل")

    # ===== Bot Commands (رئيسي - يبلوك الـ loop) =====
    try:
        from bot_commands import run_bot
        run_bot()
    except KeyboardInterrupt:
        log_info("🛑 تم إيقاف Nebula")
        scheduler.stop()
    except Exception as e:
        log_error(f"❌ خطأ غير متوقع: {e}")
        scheduler.stop()
