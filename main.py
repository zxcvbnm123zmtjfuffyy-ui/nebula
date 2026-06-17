import threading
import time
from api import run_api
from self_bot import run_self_bot, stop_self_bot
from bot_commands import run_bot
from logger import log_info, log_error, log_success
from supabase_client import init_supabase
import config

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║        🚀 NEBULA v3.0               ║
    ║    Discord Boost Monitor            ║
    ╚══════════════════════════════════════╝
    """)
    
    log_info(f"📊 عدد الحسابات: {len(config.SELF_TOKENS)}")
    log_info(f"🔒 السيرفر المسموح: {config.ALLOWED_GUILD_ID}")
    log_info(f"⏱️ التأخير: {config.MIN_DELAY_SECONDS}-{config.MAX_DELAY_SECONDS}ث")
    log_info(f"🔑 OWNER_ID: {config.OWNER_ID}")
    log_info("🔄 وضع الفحص: كل 24 ساعة مع توزيع عشوائي")

    # Supabase
    init_supabase()

    # تشغيل API في خيط منفصل
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    log_success("✅ API يعمل على منفذ 5000")

    # تشغيل Self-Bot في خيط منفصل
    self_bot_thread = threading.Thread(target=run_self_bot, daemon=True)
    self_bot_thread.start()
    log_success("✅ Self-Bot يعمل في الخلفية")

    # تشغيل البوت العادي في الخيط الرئيسي
    try:
        run_bot()
    except KeyboardInterrupt:
        log_info("🛑 تم إيقاف Nebula بواسطة المستخدم")
        stop_self_bot()
    except Exception as e:
        log_error(f"❌ خطأ غير متوقع: {e}")
        stop_self_bot()
