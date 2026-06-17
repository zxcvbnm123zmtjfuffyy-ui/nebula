import random
import time
import requests
from datetime import datetime, timezone
import config
from logger import log_info, log_warning, log_error, log_success

# ===== Cache معلومات الحسابات =====
# ✅ username و user_id ما تتغير، نجلبهم مرة واحدة فقط
_account_cache: dict[str, dict] = {}

# ===== Session واحدة لكل الطلبات =====
_session = requests.Session()


def get_random_headers(token: str) -> dict:
    """توليد هيدرز أقرب للكلاينت الحقيقي"""
    return {
        "Authorization": token,
        "User-Agent": random.choice(config.USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Discord-Locale": "en-US",
        "X-Discord-Timezone": "Asia/Riyadh",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


def get_account_info(token: str) -> dict:
    """جلب معلومات الحساب مع Cache"""
    # ✅ لو عندنا الـ Cache نرجعه مباشرة بدون طلب
    if token in _account_cache:
        return _account_cache[token]

    try:
        resp = _session.get(
            "https://discord.com/api/v9/users/@me",
            headers=get_random_headers(token),
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            # نخزن في الـ Cache
            _account_cache[token] = data
            log_info(f"💾 تم تخزين معلومات {data.get('username')} في Cache")
            return data
        return None
    except Exception as e:
        log_error(f"فشل جلب معلومات الحساب: {e}")
        return None


def get_boost_slots(token: str, retry: int = 0) -> list:
    """جلب Boost Slots مع Exponential Backoff"""
    max_retries = 3

    # ✅ تأخير عشوائي (45-90 ثانية)
    delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
    log_info(f"⏳ تأخير {delay:.0f}ث قبل الطلب...")
    time.sleep(delay)

    try:
        resp = _session.get(
            "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
            headers=get_random_headers(token),
            timeout=20
        )

        if resp.status_code == 200:
            return resp.json()

        elif resp.status_code == 429:
            # ✅ Exponential Backoff بدل انتظار ثابت
            if retry >= max_retries:
                log_error(f"تجاوزنا الحد الأقصى للمحاولات ({max_retries})")
                return None

            retry_after = resp.json().get("retry_after", 5)
            wait_time = retry_after * (2 ** retry)  # 1x → 2x → 4x
            log_warning(f"Rate Limit! انتظار {wait_time:.1f}ث (محاولة {retry + 1}/{max_retries})")
            time.sleep(wait_time)
            return get_boost_slots(token, retry + 1)

        elif resp.status_code == 401:
            log_error(f"توكن منتهي أو غير صالح: {token[:15]}...")
            # ✅ نحذف الـ Cache لو التوكن انتهى
            _account_cache.pop(token, None)
            return None

        else:
            log_warning(f"خطأ {resp.status_code} للتوكن: {token[:15]}...")
            return None

    except Exception as e:
        log_error(f"فشل جلب Boost Slots: {e}")
        return None


def parse_boost_data(slots: list) -> dict:
    """تحليل بيانات الـ Boost"""
    if not slots:
        return {"status": "no_slots", "message": "لا توجد Boost Slots"}

    active_slots = [s for s in slots if s.get("cooldown_ends_at")]

    if not active_slots:
        return {
            "status": "ready",
            "message": "✅ جاهز للضرب!",
            "cooldown_ends": None,
            "cooldown_timestamp": None
        }

    cooldown_end = max(s["cooldown_ends_at"] for s in active_slots)
    end_time     = datetime.fromisoformat(cooldown_end.replace("Z", "+00:00"))
    now          = datetime.now(timezone.utc)

    if end_time <= now:
        return {
            "status": "ready",
            "message": "✅ جاهز للضرب!",
            "cooldown_ends": cooldown_end,
            "cooldown_timestamp": int(end_time.timestamp()),
            "server_id": active_slots[0].get("guild_id")
        }
    else:
        remaining = end_time - now
        days      = remaining.days
        hours     = remaining.seconds // 3600
        minutes   = (remaining.seconds % 3600) // 60

        return {
            "status": "waiting",
            "message": f"⏳ متبقي {days}ي {hours}س {minutes}د",
            "cooldown_ends": cooldown_end,
            "cooldown_timestamp": int(end_time.timestamp()),
            "server_id": active_slots[0].get("guild_id"),
            "remaining": remaining.total_seconds()
        }


def check_single_account(token: str) -> dict:
    """فحص حساب واحد"""
    log_info(f"🔍 فحص: {token[:15]}...")

    info = get_account_info(token)
    if not info:
        return {"error": "فشل جلب معلومات الحساب"}

    username = info.get("username", "Unknown")
    user_id  = info.get("id")

    slots = get_boost_slots(token)
    if slots is None:
        return {"error": "فشل جلب بيانات الـ Boost"}

    status = parse_boost_data(slots)
    status.update({
        "username": username,
        "user_id": user_id,
        "last_check": datetime.now(timezone.utc).isoformat(),
        "token_preview": token[:15] + "..."
    })

    log_success(f"✅ {username}: {status['message']}")
    return status


def check_all_accounts() -> list:
    """فحص جميع الحسابات مع توقفات جماعية"""
    results = []
    tokens  = config.SELF_TOKENS.copy()
    random.shuffle(tokens)
    total = len(tokens)

    for i, token in enumerate(tokens):
        log_info(f"📌 [{i + 1}/{total}]")
        result = check_single_account(token)
        results.append(result)

        # ✅ توقف طويل كل 2 حسابات (يشبه سلوك بشري)
        if (i + 1) % 2 == 0 and i < total - 1:
            long_pause = random.uniform(120, 300)  # 2-5 دقائق
            log_info(f"☕ توقف جماعي: {long_pause:.0f}ث...")
            time.sleep(long_pause)
        elif i < total - 1:
            delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
            log_info(f"⏳ {delay:.0f}ث قبل الحساب التالي...")
            time.sleep(delay)

    return results
