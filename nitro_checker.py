import random
import time
from datetime import datetime, timezone
import requests
import config
from logger import log_info, log_warning, log_error, log_success
from boost_checker import _session, get_random_headers, _account_cache

NITRO_TYPES = {
    0: {"name": "بدون Nitro", "emoji": "⚪"},
    1: {"name": "Nitro Classic", "emoji": "💜"},
    2: {"name": "Nitro", "emoji": "💎"},
    3: {"name": "Nitro Basic", "emoji": "🔵"},
}

def get_nitro_subscriptions(token: str) -> list | None:
    delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
    time.sleep(delay)
    try:
        resp = _session.get(
            "https://discord.com/api/v9/users/@me/billing/subscriptions",
            headers=get_random_headers(token),
            timeout=20
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            log_error(f"توكن منتهي: {token[:15]}...")
            _account_cache.pop(token, None)
            return None
        elif resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 10)
            log_warning(f"Rate Limit! ننتظر {retry_after}ث...")
            time.sleep(retry_after * 2)
            return get_nitro_subscriptions(token)
        else:
            log_warning(f"خطأ {resp.status_code} في جلب Nitro: {token[:15]}...")
            return None
    except Exception as e:
        log_error(f"فشل جلب بيانات Nitro: {e}")
        return None

def parse_nitro_data(subscriptions: list, token: str) -> dict:
    cached = _account_cache.get(token, {})
    premium_type = cached.get("premium_type", 0)
    nitro_info = NITRO_TYPES.get(premium_type, NITRO_TYPES[0])
    if not subscriptions:
        return {
            "has_nitro": False,
            "nitro_type": nitro_info["name"],
            "nitro_emoji": nitro_info["emoji"],
            "expires_at": None,
            "expires_timestamp": None,
            "status": "inactive",
            "message": f"{nitro_info['emoji']} بدون Nitro"
        }
    active_sub = None
    for sub in subscriptions:
        if sub.get("status") in ("active", "past_due"):
            active_sub = sub
            break
    if not active_sub:
        return {
            "has_nitro": False,
            "nitro_type": nitro_info["name"],
            "nitro_emoji": nitro_info["emoji"],
            "expires_at": None,
            "expires_timestamp": None,
            "status": "canceled",
            "message": f"{nitro_info['emoji']} Nitro منتهي الصلاحية"
        }
    expires_raw = active_sub.get("current_period_end")
    if expires_raw:
        if isinstance(expires_raw, (int, float)):
            expires_dt = datetime.fromtimestamp(expires_raw, tz=timezone.utc)
        else:
            expires_dt = datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        remaining = expires_dt - now
        days_left = remaining.days
        if days_left <= 7:
            status_msg = f"⚠️ ينتهي قريباً! <t:{int(expires_dt.timestamp())}:R>"
        else:
            status_msg = f"✅ نشط | ينتهي <t:{int(expires_dt.timestamp())}:R>"
        return {
            "has_nitro": True,
            "nitro_type": nitro_info["name"],
            "nitro_emoji": nitro_info["emoji"],
            "expires_at": expires_dt.isoformat(),
            "expires_timestamp": int(expires_dt.timestamp()),
            "days_left": days_left,
            "status": active_sub.get("status", "active"),
            "message": status_msg
        }
    return {
        "has_nitro": True,
        "nitro_type": nitro_info["name"],
        "nitro_emoji": nitro_info["emoji"],
        "expires_at": None,
        "expires_timestamp": None,
        "status": "active",
        "message": f"{nitro_info['emoji']} {nitro_info['name']} - نشط"
    }

def check_nitro(token: str) -> dict:
    log_info(f"💎 فحص Nitro: {token[:15]}...")
    from boost_checker import get_account_info
    info = get_account_info(token)
    if not info:
        return {"error": "فشل جلب معلومات الحساب"}
    username = info.get("username", "Unknown")
    user_id = info.get("id")
    subscriptions = get_nitro_subscriptions(token)
    if subscriptions is None:
        return {"error": f"فشل جلب بيانات Nitro لـ {username}"}
    result = parse_nitro_data(subscriptions, token)
    result.update({
        "username": username,
        "user_id": user_id,
        "token_preview": token[:15] + "...",
        "checked_at": datetime.now(timezone.utc).isoformat()
    })
    log_success(f"💎 {username}: {result['message']}")
    return result

def check_all_nitro() -> list:
    results = []
    tokens = config.SELF_TOKENS.copy()
    total = len(tokens)
    for i, token in enumerate(tokens):
        log_info(f"📌 [{i + 1}/{total}]")
        result = check_nitro(token)
        results.append(result)
        if i < total - 1:
            if (i + 1) % 2 == 0:
                pause = random.uniform(120, 300)
                log_info(f"☕ توقف جماعي: {pause:.0f}ث...")
                time.sleep(pause)
            else:
                delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
                time.sleep(delay)
    return results
