import threading
from flask import Flask
import config
from bot_commands import run_bot
from scheduler import Scheduler
from logger import log_info, log_success
from supabase_client import init_supabase
from web_dashboard import setup_dashboard

app = Flask(__name__)
setup_dashboard(app)

@app.route('/')
def home():
    from supabase_client import get_tokens
    return f"""
    <h1>🚀 Nebula v4.0</h1>
    <p>البوت يعمل بكفاءة ✅</p>
    <p>عدد الحسابات المراقبة: {len(get_tokens())}</p>
    <p><a href="/dashboard">📊 لوحة التحكم</a></p>
    """

@app.route('/ping')
def ping():
    return "PONG", 200

@app.route('/status')
def status():
    from supabase_client import get_tokens
    return {"status": "online", "accounts": len(get_tokens()), "bot": "Nebula v4.0"}, 200

def run_flask():
    app.run(host='0.0.0.0', port=8080, use_reloader=False)

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║        🚀 NEBULA v4.0               ║
    ║    Discord Boost Monitor            ║
    ║    (أوامر عربية + ويب + إمبدات)   ║
    ╚══════════════════════════════════════╝
    """)
    
    # تهيئة Supabase
    init_supabase()
    
    log_info(f"🔒 السيرفر المسموح: {config.ALLOWED_GUILD_ID}")
    log_info(f"⏱️ التأخير بين الطلبات: {config.MIN_DELAY_SECONDS}-{config.MAX_DELAY_SECONDS} ثانية")
    
    # تشغيل Scheduler
    scheduler = Scheduler()
    scheduler_thread = threading.Thread(target=scheduler.run_loop, daemon=True)
    scheduler_thread.start()
    log_success("✅ Scheduler يعمل (فحص كل 24 ساعة + Auto-Ping)")
    
    # تشغيل Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    log_success("✅ Flask يعمل على منفذ 8080")
    
    # تشغيل البوت
    log_info("🤖 تشغيل البوت...")
    run_bot()
