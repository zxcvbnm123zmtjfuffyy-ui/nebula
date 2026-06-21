import random
import time
import threading
from datetime import datetime, timedelta
import config
from logger import log_info, log_success, log_error
from boost_checker import check_all_accounts, auto_ping_all

class Scheduler:
    def __init__(self):
        self.running = True
        self.next_check = None
        self.last_ping = None

    def schedule_next_check(self):
        now = datetime.now()
        next_time = now + timedelta(hours=24, minutes=random.randint(0, 59))
        self.next_check = next_time.timestamp()
        log_info(f"📅 الفحص القادم: {next_time.strftime('%Y-%m-%d %H:%M')}")

    def run_loop(self):
        log_info("🚀 بدأ تشغيل Scheduler (كل 24 ساعة)")
        self.schedule_next_check()
        self.last_ping = time.time()

        while self.running:
            now = time.time()
            
            if now >= self.next_check:
                log_info("⏰ حان وقت الفحص الدوري!")
                self.run_checks()
                self.schedule_next_check()
            
            if now - self.last_ping >= 3600:
                log_info("🔄 Auto-Ping: تحديث نشاط الحسابات...")
                auto_ping_all()
                self.last_ping = now
            
            time.sleep(60)

    def run_checks(self):
        log_info("🔄 بدء الفحص الدوري الشامل...")
        from notifier import send_ready_notification
        from supabase_client import get_webhooks
        from boost_checker import check_all_accounts
        
        results = check_all_accounts()
        ready_count = 0
        for r in results:
            if "error" in r:
                log_error(f"❌ خطأ في {r.get('username', 'Unknown')}: {r['error']}")
            elif r.get("status") == "ready":
                ready_count += 1
                send_ready_notification(
                    r["username"],
                    r["user_id"],
                    r.get("cooldown_timestamp")
                )
                log_success(f"✅ {r['username']} جاهز! تم إرسال الإشعار")
            else:
                log_info(f"⏳ {r['username']}: {r['message']}")
        
        log_success(f"✅ انتهى الفحص الدوري - {ready_count} حسابات جاهزة")

    def stop(self):
        self.running = False
        log_info("🛑 تم إيقاف Scheduler")