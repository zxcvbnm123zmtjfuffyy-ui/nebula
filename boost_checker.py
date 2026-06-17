import requests
import random
import time
from datetime import datetime, timezone, timedelta
import config
from logger import log_info, log_warning, log_error

_account_cache = {}

def get_headers(token: str) -> dict:
    return {
        "Authorization": token,
        "User-Agent": random.choice(config.USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

def get_account_info(token: str) -> dict:
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
        return None
    except Exception as e:
        log_error(f"فشل جلب معلومات الحساب: {e}")
        return None

def get_boost_slots(token: str, retry: int = 0) -> list:
    max_retries = 3
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
                return None
            retry_after = resp.json().get("retry_after", 5)
            wait = retry_after * (2 ** retry)
            log_warning(f"Rate Limit! ننتظر {wait:.1f} ثانية")
            time.sleep(wait)
            return get_boost_slots(token, retry + 1)
        elif resp.status_code == 401:
            log_error(f"توكن غير صالح: {token[:15]}...")
            _account_cache.pop(token, None)
            return None
        return None
    except Exception as e:
        log_error(f"فشل جلب Boost: {e}")
        return None

def check_account(token: str) -> dict:
    log_info(f"🔍 فحص: {token[:15]}...")
    info = get_account_info(token)
    if not info:
        return {"error": "فشل جلب معلومات الحساب"}
    slots = get_boost_slots(token)
    if slots is None:
        return {"error": "فشل جلب بيانات Boost"}

    # جلب الصورة
    avatar_hash = info.get("avatar")
    avatar_url = f"https://cdn.discordapp.com/avatars/{info['id']}/{avatar_hash}.png" if avatar_hash else None

    active = [s for s in slots if s.get("cooldown_ends_at")]
    if not active:
        return {
            "username": info["username"],
            "user_id": info["id"],
            "avatar_url": avatar_url,
            "status": "ready",
            "message": "✅ **جاهز للضرب!**",
            "cooldown_timestamp": None,
            "last_boost_timestamp": None,
            "server_id": None
        }

    cooldown_end = max(s["cooldown_ends_at"] for s in active)
    try:
        end_time = datetime.fromisoformat(cooldown_end.replace("Z", "+00:00"))
    except:
        end_time = datetime.fromisoformat(cooldown_end)

    # حساب آخر ضربة (ناقص 7 أيام)
    last_boost_time = end_time - timedelta(days=7)
    last_boost_ts = int(last_boost_time.timestamp())

    now = datetime.now(timezone.utc)
    if end_time <= now:
        return {
            "username": info["username"],
            "user_id": info["id"],
            "avatar_url": avatar_url,
            "status": "ready",
            "message": "✅ **جاهز للضرب!**",
            "cooldown_timestamp": int(end_time.timestamp()),
            "last_boost_timestamp": last_boost_ts,
            "server_id": active[0].get("guild_id")
        }
    else:
        remaining = end_time - now
        days = remaining.days
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        text = f"{days}ي {hours}س {minutes}د"
        return {
            "username": info["username"],
            "user_id": info["id"],
            "avatar_url": avatar_url,
            "status": "waiting",
            "message": f"⏳ **متبقي** {text}",
            "cooldown_timestamp": int(end_time.timestamp()),
            "last_boost_timestamp": last_boost_ts,
            "server_id": active[0].get("guild_id")
        }

def check_all_accounts() -> list:
    results = []
    tokens = config.SELF_TOKENS.copy()
    random.shuffle(tokens)
    for i, token in enumerate(tokens):
        log_info(f"📌 [{i+1}/{len(tokens)}]")
        results.append(check_account(token))
        if i < len(tokens) - 1:
            delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
            time.sleep(delay)
    return results
