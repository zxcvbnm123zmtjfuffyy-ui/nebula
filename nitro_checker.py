import requests
import random
import time
from datetime import datetime, timezone
import config
from logger import log_info, log_warning, log_error, log_success
from boost_checker import get_account_info

def get_headers(token: str) -> dict:
    return {
        "Authorization": token,
        "User-Agent": random.choice(config.USER_AGENTS),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

def get_nitro_subscriptions(token: str, retry: int = 0) -> list:
    max_retries = 3
    time.sleep(random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS))
    try:
        resp = requests.get(
            "https://discord.com/api/v9/users/@me/billing/subscriptions",
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
            log_warning(f"Rate Limit (Nitro)! ننتظر {wait:.1f} ثانية")
            time.sleep(wait)
            return get_nitro_subscriptions(token, retry + 1)
        elif resp.status_code == 401:
            log_error(f"توكن غير صالح: {token[:15]}...")
            return None
        return None
    except Exception as e:
        log_error(f"فشل جلب Nitro: {e}")
        return None

def check_nitro(token: str) -> dict:
    log_info(f"💎 فحص Nitro: {token[:15]}...")
    info = get_account_info(token)
    if not info:
        return {"error": "فشل جلب معلومات الحساب"}
    subs = get_nitro_subscriptions(token)
    if subs is None:
        return {"error": "فشل جلب بيانات Nitro"}

    active = [s for s in subs if s.get("status") in ("active", "past_due")]
    if not active:
        return {
            "username": info["username"],
            "user_id": info["id"],
            "has_nitro": False,
            "message": "⚪ بدون Nitro"
        }

    sub = active[0]
    expires_raw = sub.get("current_period_end")
    if expires_raw:
        if isinstance(expires_raw, (int, float)):
            expires_dt = datetime.fromtimestamp(expires_raw, tz=timezone.utc)
        else:
            expires_dt = datetime.fromisoformat(str(expires_raw).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_left = (expires_dt - now).days
        if days_left <= 7:
            msg = f"⚠️ ينتهي قريباً <t:{int(expires_dt.timestamp())}:R>"
        else:
            msg = f"✅ ينتهي <t:{int(expires_dt.timestamp())}:R>"
        return {
            "username": info["username"],
            "user_id": info["id"],
            "has_nitro": True,
            "nitro_type": "Nitro",
            "days_left": days_left,
            "expires_timestamp": int(expires_dt.timestamp()),
            "message": msg
        }

    return {
        "username": info["username"],
        "user_id": info["id"],
        "has_nitro": True,
        "nitro_type": "Nitro",
        "message": "💎 Nitro نشط (بدون تاريخ انتهاء)"
    }

def check_all_nitro() -> list:
    results = []
    tokens = config.SELF_TOKENS.copy()
    random.shuffle(tokens)
    for i, token in enumerate(tokens):
        log_info(f"💎 [{i+1}/{len(tokens)}]")
        results.append(check_nitro(token))
        if i < len(tokens) - 1:
            delay = random.uniform(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS)
            time.sleep(delay)
    return results
