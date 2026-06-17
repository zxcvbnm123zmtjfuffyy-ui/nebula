import requests
from datetime import datetime, timezone
import config
from logger import log_info, log_error

def send_webhook(embed_data: dict):
    if not config.WEBHOOK_URL:
        return
    payload = {"username": "Nebula", "embeds": [embed_data]}
    try:
        resp = requests.post(config.WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            log_info("✅ تم إرسال الإشعار")
        else:
            log_error(f"فشل إرسال الإشعار: {resp.status_code}")
    except Exception as e:
        log_error(f"فشل إرسال الإشعار: {e}")

def send_ready_notification(username: str, user_id: str, cooldown_ts: int = None):
    embed = {
        "title": "🚀 **حساب جاهز للبوست!**",
        "description": f"الحساب **{username}** أصبح جاهزاً.",
        "color": 0x00ff7f,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {"name": "👤 **اليوزر**", "value": f"**{username}**", "inline": True},
            {"name": "🆔 **ID**", "value": f"`{user_id}`", "inline": True},
        ],
        "footer": {"text": "Nebula Monitor"}
    }
    if cooldown_ts:
        embed["fields"].append({"name": "⏳ **انتهاء التبريد**", "value": f"<t:{cooldown_ts}:F>", "inline": True})
    send_webhook(embed)

def send_waiting_notification(username: str, user_id: str, cooldown_ts: int, remaining_text: str):
    embed = {
        "title": "⏳ **حساب في فترة التبريد**",
        "description": f"الحساب **{username}** لا يزال في الانتظار.",
        "color": 0xff4444,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {"name": "👤 **اليوزر**", "value": f"**{username}**", "inline": True},
            {"name": "🆔 **ID**", "value": f"`{user_id}`", "inline": True},
            {"name": "⏳ **الوقت المتبقي**", "value": remaining_text, "inline": True},
            {"name": "📅 **ينتهي**", "value": f"<t:{cooldown_ts}:R>", "inline": True},
        ],
        "footer": {"text": "Nebula Monitor"}
    }
    send_webhook(embed)
