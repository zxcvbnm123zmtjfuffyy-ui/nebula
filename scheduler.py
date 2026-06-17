import random
import time
import threading
from datetime import datetime, timedelta
import config
from logger import log_info, log_success, log_error
from boost_checker import check_single_account


class Scheduler:
    """جدولة الفحص الموزع على مدار اليوم"""

    def __init__(self):
        self.running = True
        # ✅ الإصلاح 4: check_history يخزن timestamp الفحص القادم لكل token
        self.check_history: dict[str, float] = {}

    def get_next_check_time(self, index: int, total: int) -> float:
        """
        حساب وقت الفحص التالي لحساب معين
        يوزع الحسابات على مدار اليوم
        """
        # توزيع الحسابات على 24 ساعة
        base_hour = (index / total) * 24

        # إضافة عشوائية (± ساعتين)
        random_offset = random.uniform(-2, 2)
        hour = (base_hour + random_offset) % 24

        now = datetime.now()

        # حساب وقت الفحص التالي في اليوم الحالي
        next_time = now.replace(
            hour=int(hour),
            minute=random.randint(0, 59),
            second=0,
            microsecond=0
        )

        # ✅ الإصلاح 3: timedelta بدل replace(day=+1) لتجنب كسر نهاية الشهر
        if next_time <= now:
            next_time += timedelta(days=1)

        return next_time.timestamp()

    def run_single_check(self, token: str, index: int, total: int):
        """تنفيذ فحص لحساب واحد"""
        log_info(f"🔄 بدء فحص الحساب {index + 1}/{total}")

        try:
            result = check_single_account(token)

            if result and result.get("status") == "ready":
                from notifier import send_notification
                send_notification(result)
                log_success(f"✅ {result.get('username')} جاهز للضرب!")
            elif result and result.get("error"):
                log_error(f"❌ فشل فحص {token[:15]}: {result['error']}")
            else:
                log_info(f"📊 {result.get('username')}: {result.get('message', '')}")

        except Exception as e:
            log_error(f"❌ خطأ في فحص الحساب: {e}")

    def run_loop(self):
        """الحلقة الرئيسية للجدولة"""
        log_info("🚀 بدأ تشغيل Scheduler")

        tokens = config.SELF_TOKENS.copy()
        total = len(tokens)

        # ✅ الإصلاح 4: نجدول كل حساب مرة واحدة عند البداية
        for i, token in enumerate(tokens):
            self.check_history[token] = self.get_next_check_time(i, total)
            log_info(
                f"📅 جُدول الحساب {i + 1}: "
                f"{datetime.fromtimestamp(self.check_history[token]).strftime('%H:%M')}"
            )

        while self.running:
            now = time.time()

            for i, token in enumerate(tokens):
                next_check = self.check_history.get(token, 0)

                # ✅ الإصلاح 4: نتحقق من check_history وليس get_next_check_time في كل دورة
                if next_check <= now:
                    log_info(f"⏰ حان وقت فحص الحساب {i + 1}")
                    self.run_single_check(token, i, total)

                    # نجدول الفحص القادم بعد 24 ساعة + عشوائية
                    next_interval = timedelta(
                        hours=22 + random.uniform(0, 4),
                        minutes=random.randint(0, 59)
                    )
                    self.check_history[token] = now + next_interval.total_seconds()

                    next_dt = datetime.fromtimestamp(self.check_history[token])
                    log_info(f"📅 الفحص القادم للحساب {i + 1}: {next_dt.strftime('%Y-%m-%d %H:%M')}")

                    # توقف بين الحسابات
                    time.sleep(random.uniform(5, 15))

            # نتحقق كل دقيقة
            time.sleep(60)

    def stop(self):
        """إيقاف الجدولة"""
        self.running = False
        log_info("🛑 تم إيقاف Scheduler")
