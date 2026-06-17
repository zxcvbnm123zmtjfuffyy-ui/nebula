import random
import time
from datetime import datetime, timedelta
import config
from logger import log_info, log_success, log_error
from boost_checker import check_all_accounts
from nitro_checker import check_all_nitro
from supabase_client import save_account_data

class Scheduler:
    def __init__(self):
        self.running = True
        self.next_run = None

    def schedule_next(self):
        """جدولة الفحص التالي بعد 24 ساعة + عشوائية"""
        now = datetime.now()
        next_time = now + timedelta(hours=24, minutes=random.randint(0, 59))
        self.next_run = next_time.timestamp()
        log_info(f"📅 الفحص القادم: {next_time.strftime('%Y-%m-%d %H:%M')}")

    def run_loop(self):
        log_info("🚀 بدأ تشغيل Scheduler (كل 24 ساعة)")
        self.schedule_next()
        while self.running:
            now = time.time()
            if now >= self.next_run:
                log_info("⏰ حان وقت الفحص الدوري!")
                self.run_checks()
                self.schedule_next()
            time.sleep(60)

    def run_checks(self):
        """تنفيذ الفحص الكامل (Boost + Nitro) لجميع الحسابات"""
        log_info("🔄 بدء الفحص الدوري الشامل...")
        boost_results = check_all_accounts()
        nitro_results = check_all_nitro()
        # دمج النتائج وحفظها في Supabase
        for b in boost_results:
            if "error" in b:
                continue
            # نبحث عن النيترو المقابل
            nitro = next((n for n in nitro_results if n.get("user_id") == b.get("user_id")), {})
            data = {
                "username": b.get("username"),
                "user_id": b.get("user_id"),
                "status": b.get("status"),
                "cooldown_ends": b.get("cooldown_ends"),
                "last_check": b.get("last_check"),
                "server_id": b.get("server_id"),
                "nitro_type": nitro.get("nitro_type"),
                "nitro_status": nitro.get("status"),
                "nitro_expires_at": nitro.get("expires_at"),
                "nitro_days_left": nitro.get("days_left"),
                "nitro_last_check": nitro.get("checked_at"),
            }
            # نبحث عن التوكن الأصلي
            token = next((t for t in config.SELF_TOKENS if t.startswith(b.get("token_preview", "").replace("...", ""))), None)
            if token:
                save_account_data(token, data)
        log_success("✅ انتهى الفحص الدوري الشامل")

    def stop(self):
        self.running = False
        log_info("🛑 تم إيقاف Scheduler")
