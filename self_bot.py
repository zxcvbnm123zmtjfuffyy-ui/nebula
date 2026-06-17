import threading
import time
from scheduler import Scheduler
from logger import log_info, log_error, log_success

scheduler = Scheduler()

def run_self_bot():
    log_info("🚀 بدأ تشغيل Self-Bot")
    try:
        scheduler.run_loop()
    except Exception as e:
        log_error(f"❌ خطأ في Self-Bot: {e}")

def stop_self_bot():
    scheduler.stop()