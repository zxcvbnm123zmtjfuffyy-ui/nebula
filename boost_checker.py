import requests
import random
import time
from datetime import datetime, timezone
import config
from logger import log_info, log_warning, log_error, log_success

_account_cache = {}

def get_headers(token: str) -> dict:
    """توليد هيدرز عشوائية للطلب"""
    return {
        "Authorization": token,
        "User-Agent": random.choice(config.USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

def get_account_info(token: str) -> dict:
    """جلب معلومات الحساب (مع cache)"""
    if token in _account_cache:
        return _account_cache[token]
    try:
        resp = requests.get(
            "https://discord.com/api/v9/users/@me",
            headers=get_headers(token),
            timeout=15
        )
        if resp.status_code == 200:
            data = resp.json()
            _account_cache[token] = data
            return data
        else:
            log_warning(f"فشل جلب معلومات الحساب: {resp.status_code}")
            return None
    except Exception as e:
        log_error(f"خطأ في جلب معلومات الحساب: {e}")
        return None

def get_boost_slots(token: str, retry: int = 0) -> list:
    """جلب بيانات Boost Slots مع إعادة محاولة عند Rate Limit"""
    max_retries = 3
    # تأخير عشوائي قبل الطلب
    time.sleep(random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS))
    try:
        resp = requests.get(
            "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
            headers=get_headers(token),
            timeout=20
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 429:
            if retry >= max_retries:
                log_error(f"تجاوزنا الحد الأقصى للمحاولات ({max_retries})")
                return None
            retry_after = resp.json().get("retry_after", 5)
            wait = retry_after * (2 ** retry)
            log_warning(f"Rate Limit! ننتظر {wait:.1f} ثانية (محاولة {retry+1}/{max_retries})")
            time.sleep(wait)
            return get_boost_slots(token, retry + 1)
        elif resp.status_code == 401:
            log_error(f"توكن غير صالح أو منتهي: {token[:15]}...")
            _account_cache.pop(token, None)
            return None
        else:
            log_warning(f"خطأ {resp.status_code} للتوكن: {token[:15]}...")
            return None
    except Exception as e:
        log_error(f"فشل جلب Boost Slots: {e}")
        return None

def check_account(token: str) -> dict:
    """فحص حساب واحد وعودة معلوماته الكاملة"""
    log_info(f"🔍 فحص: {token[:15]}...")
    info = get_account_info(token)
    if not info:
        return {"error": "فشل جلب معلومات الحساب"}

    slots = get_boost_slots(token)
    if slots is None:
        return {"error": "فشل جلب بيانات Boost"}

    # تحليل الـ Slots النشطة
    active = [s for s in slots if s.get("cooldown_ends_at")]
    if not active:
        result = {
            "username": info["username"],
            "user_id": info["id"],
            "status": "ready",
            "message": "✅ جاهز للضرب!",
            "cooldown_timestamp": None,
            "server_id": None
        }
        log_success(f"{info['username']}: جاهز!")
        return result

    # أحدث تاريخ انتهاء
    cooldown_end = max(s["cooldown_ends_at"] for s in active)
    try:
        end_time = datetime.fromisoformat(cooldown_end.replace("Z", "+00:00"))
    except:
        end_time = datetime.fromisoformat(cooldown_end)

    now = datetime.now(timezone.utc)
    if end_time <= now:
        result = {
            "username": info["username"],
            "user_id": info["id"],
            "status": "ready",
            "message": "✅ جاهز للضرب!",
            "cooldown_timestamp": int(end_time.timestamp()),
            "server_id": active[0].get("guild_id")
        }
        log_success(f"{info['username']}: جاهز!")
    else:
        remaining = end_time - now
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        remaining_text = f"{days}ي {hours}س {minutes}د"
        result = {
            "username": info["username"],
            "user_id": info["id"],
            "status": "waiting",
            "message": f"⏳ متبقي {remaining_text}",
            "cooldown_timestamp": int(end_time.timestamp()),
            "server_id": active[0].get("guild_id")
        }
        log_info(f"{info['username']}: ينتظر {remaining_text}")

    return result

def check_all_accounts() -> list:
    """فحص جميع الحسابات"""
    results = []
    tokens = config.SELF_TOKENS.copy()
    random.shuffle(tokens)  # تغيير الترتيب لتجنب النمط

    for i, token in enumerate(tokens):
        log_info(f"📌 [{i+1}/{len(tokens)}]")
        result = check_account(token)
        results.append(result)
        # تأخير بين الحسابات
        if i < len(tokens) - 1:
            delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
            log_info(f"⏳ ننتظر {delay:.0f} ثانية قبل الحساب التالي...")
            time.sleep(delay)

    return results
