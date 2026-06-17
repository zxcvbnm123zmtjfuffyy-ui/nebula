import threading
from flask import Flask
import config
from bot_commands import run_bot
from logger import log_info, log_success

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>🚀 Nebula v4.0</h1>
    <p>البوت يعمل بكفاءة ✅</p>
    <p>عدد الحسابات المراقبة: {}</p>
    <p>الوقت: {}</p>
    """.format(len(config.SELF_TOKENS), __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/ping')
def ping():
    return "PONG", 200

@app.route('/status')
def status():
    return {
        "status": "online",
        "accounts": len(config.SELF_TOKENS),
        "bot": "Nebula v4.0"
    }, 200

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
    
    log_info(f"📊 عدد الحسابات المراقبة: {len(config.SELF_TOKENS)}")
    log_info(f"🔒 السيرفر المسموح: {config.ALLOWED_GUILD_ID}")
    log_info(f"⏱️ التأخير بين الطلبات: {config.MIN_DELAY_SECONDS}-{config.MAX_DELAY_SECONDS} ثانية")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    log_success("✅ Flask يعمل على منفذ 8080")
    
    log_info("🤖 تشغيل البوت...")
    run_bot()
