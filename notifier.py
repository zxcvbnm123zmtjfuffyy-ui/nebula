import requests
from datetime import datetime, timezone
import config
from logger import log_info, log_error, log_warning


# ===== الألوان =====
COLOR_READY   = 0x00ff7f   # أخضر - جاهز للبوست
COLOR_WAITING = 0xff4444   # أحمر  - في انتظار
COLOR_WARNING = 0xffaa00   # برتقالي - تحذير (Nitro قريب الانتهاء)
COLOR_ERROR   = 0x747f8d   # رمادي - خطأ
COLOR_NITRO   = 0xf47fff   # وردي  - Nitro


# ===== Progress Bar =====
def make_progress_bar(remaining_seconds: float, total_seconds: float = 604800) -> str:
    """
    Progress bar ذكي مع تفاصيل الوقت المتبقي نصياً
    total_seconds = 7 أيام (604800 ثانية) = مدة Boost Cooldown
    """
    remaining_seconds = max(0, remaining_seconds)
    filled     = max(0, min(10, int((1 - remaining_seconds / total_seconds) * 10)))
    empty      = 10 - filled
    percentage = int((1 - remaining_seconds / total_seconds) * 100)
    bar        = "█" * filled + "░" * empty

    # حساب الوقت المتبقي بالتفصيل
    days    = int(remaining_seconds // 86400)
    hours   = int((remaining_seconds % 86400) // 3600)
    minutes = int((remaining_seconds % 3600) // 60)

    # بناء نص الوقت المتبقي بذكاء (ما نعرض 0)
    parts = []
    if days:    parts.append(f"{days}ي")
    if hours:   parts.append(f"{hours}س")
    if minutes: parts.append(f"{minutes}د")
    if not parts:
        time_text = "أقل من دقيقة"
    else:
        time_text = " ".join(parts)

    return f"`[{bar}]` **{percentage}%** — متبقي: `{time_text}`"


# ===== إرسال عبر Webhook مباشرة (بدون discord.py) =====
def _send_webhook(url: str, payload: dict) -> bool:
    """إرسال payload لـ webhook"""
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code in (200, 204):
            return True
        log_warning(f"Webhook رجع {resp.status_code}: {resp.text[:100]}")
        return False
    except Exception as e:
        log_error(f"فشل إرسال Webhook: {e}")
        return False


# ===========================
# 🚀 إشعار: حساب جاهز للبوست
# ===========================
def send_ready_notification(account_data: dict):
    """إشعار فردي لما حساب يصير جاهز"""
    if not config.WEBHOOK_URL:
        log_error("WEBHOOK_URL غير مضبوط")
        return

    username   = account_data.get("username", "Unknown")
    user_id    = account_data.get("user_id", "???")
    server_id  = account_data.get("server_id")
    checked_at = int(datetime.now(timezone.utc).timestamp())

    # تاريخ انتهاء آخر Cooldown (Discord Timestamp)
    cooldown_ts = account_data.get("cooldown_timestamp")
    cooldown_field = (
        f"<t:{cooldown_ts}:F>" if cooldown_ts else "أول بوست"
    )

    fields = [
        {"name": "👤 اليوزر",      "value": f"`{username}`",              "inline": True},
        {"name": "🆔 ID",           "value": f"`{user_id}`",               "inline": True},
        {"name": "⏰ وقت الجاهزية", "value": f"<t:{checked_at}:R>",        "inline": True},
        {"name": "🕐 آخر Cooldown", "value": cooldown_field,               "inline": True},
    ]

    if server_id:
        fields.append({"name": "🏠 آخر سيرفر", "value": f"`{server_id}`", "inline": True})

    payload = {
        "username":   "Nebula",
        "embeds": [{
            "title":       "🚀 حساب جاهز للبوست!",
            "description": f"الحساب **{username}** أصبح جاهزاً، يمكنك البوست الآن!",
            "color":       COLOR_READY,
            "fields":      fields,
            "footer":      {"text": "Nebula Monitor • Boost Ready"},
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        }]
    }

    if _send_webhook(config.WEBHOOK_URL, payload):
        log_info(f"✅ إشعار جاهزية أُرسل لـ {username}")


# ==============================
# ⏳ إشعار: حساب لا يزال ينتظر
# ==============================
def send_waiting_notification(account_data: dict):
    """إشعار لما حساب لا يزال في Cooldown"""
    if not config.WEBHOOK_URL:
        return

    username    = account_data.get("username", "Unknown")
    user_id     = account_data.get("user_id", "???")
    cooldown_ts = account_data.get("cooldown_timestamp")
    remaining   = account_data.get("remaining", 0)
    server_id   = account_data.get("server_id")

    # Progress Bar
    progress = make_progress_bar(remaining) if remaining else "`[██████████]` 100%"

    # Discord Timestamp للوقت المتبقي
    cooldown_field = f"<t:{cooldown_ts}:R>" if cooldown_ts else "غير معروف"
    cooldown_full  = f"<t:{cooldown_ts}:F>" if cooldown_ts else "غير معروف"

    fields = [
        {"name": "👤 اليوزر",       "value": f"`{username}`",   "inline": True},
        {"name": "🆔 ID",            "value": f"`{user_id}`",    "inline": True},
        {"name": "⏳ ينتهي",         "value": cooldown_field,    "inline": True},
        {"name": "📅 تاريخ الانتهاء","value": cooldown_full,     "inline": True},
        {"name": "📊 التقدم",         "value": progress,         "inline": False},
    ]

    if server_id:
        fields.append({"name": "🏠 السيرفر", "value": f"`{server_id}`", "inline": True})

    payload = {
        "username":   "Nebula",
        "embeds": [{
            "title":       "⏳ الحساب لا يزال في Cooldown",
            "description": f"**{username}** لم يصبح جاهزاً بعد.",
            "color":       COLOR_WAITING,
            "fields":      fields,
            "footer":      {"text": "Nebula Monitor • Still Waiting"},
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        }]
    }

    if _send_webhook(config.WEBHOOK_URL, payload):
        log_info(f"📊 إشعار انتظار أُرسل لـ {username}")


# ==============================
# 💎 إشعار: حالة Nitro
# ==============================
def send_nitro_notification(nitro_data: dict):
    """إشعار حالة Nitro لحساب واحد"""
    if not config.WEBHOOK_URL:
        return

    username    = nitro_data.get("username", "Unknown")
    user_id     = nitro_data.get("user_id", "???")
    nitro_type  = nitro_data.get("nitro_type", "بدون Nitro")
    nitro_emoji = nitro_data.get("nitro_emoji", "⚪")
    expires_ts  = nitro_data.get("expires_timestamp")
    days_left   = nitro_data.get("days_left")
    has_nitro   = nitro_data.get("has_nitro", False)
    color       = COLOR_WARNING if (days_left and days_left <= 7) else COLOR_NITRO

    # حقل انتهاء الـ Nitro
    if expires_ts:
        expires_field = f"<t:{expires_ts}:F>\n<t:{expires_ts}:R>"
    else:
        expires_field = "غير محدد" if has_nitro else "—"

    fields = [
        {"name": "👤 اليوزر",     "value": f"`{username}`",                      "inline": True},
        {"name": "🆔 ID",          "value": f"`{user_id}`",                       "inline": True},
        {"name": "💎 النوع",       "value": f"{nitro_emoji} {nitro_type}",        "inline": True},
        {"name": "📅 الانتهاء",    "value": expires_field,                        "inline": True},
    ]

    if days_left is not None:
        warn = " ⚠️" if days_left <= 7 else ""
        fields.append({
            "name": "📆 الأيام المتبقية",
            "value": f"`{days_left}` يوم{warn}",
            "inline": True
        })

    title = (
        f"⚠️ تحذير: Nitro ينتهي قريباً! ({days_left}د)"
        if (days_left and days_left <= 7)
        else f"💎 Nitro - {username}"
    )

    payload = {
        "username":   "Nebula",
        "embeds": [{
            "title":       title,
            "description": nitro_data.get("message", ""),
            "color":       color,
            "fields":      fields,
            "footer":      {"text": "Nebula Monitor • Nitro Status"},
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        }]
    }

    if _send_webhook(config.WEBHOOK_URL, payload):
        log_info(f"💎 إشعار Nitro أُرسل لـ {username}")


# ==============================
# 📋 ملخص كل الحسابات (Status)
# ==============================
def send_status_summary(results: list):
    """ملخص شامل لكل الحسابات - يُستخدم مع أمر /status"""
    if not config.WEBHOOK_URL:
        return

    ready   = [r for r in results if r.get("status") == "ready"]
    waiting = [r for r in results if r.get("status") == "waiting"]
    errors  = [r for r in results if r.get("error")]

    # بناء قائمة الحسابات
    lines = []
    for r in results:
        if r.get("error"):
            lines.append(f"❌ `{r.get('token_preview', '???')}` — خطأ")
            continue

        name = r.get("username", "Unknown")
        if r.get("status") == "ready":
            lines.append(f"✅ `{name}` — جاهز!")
        else:
            ts = r.get("cooldown_timestamp")
            ts_field = f"<t:{ts}:R>" if ts else r.get("message", "")
            lines.append(f"⏳ `{name}` — {ts_field}")

    accounts_text = "\n".join(lines) if lines else "لا توجد بيانات"

    fields = [
        {"name": "✅ جاهز",   "value": str(len(ready)),   "inline": True},
        {"name": "⏳ انتظار", "value": str(len(waiting)), "inline": True},
        {"name": "❌ خطأ",    "value": str(len(errors)),  "inline": True},
        {"name": "📋 التفاصيل", "value": accounts_text,  "inline": False},
    ]

    payload = {
        "username":   "Nebula",
        "embeds": [{
            "title":       "📊 Nebula — حالة الحسابات",
            "color":       COLOR_READY if len(ready) > 0 else COLOR_WAITING,
            "fields":      fields,
            "footer":      {"text": f"Nebula Monitor • {len(results)} حساب"},
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        }]
    }

    if _send_webhook(config.WEBHOOK_URL, payload):
        log_info("📊 ملخص الحسابات أُرسل")


# ===== دالة قديمة للتوافق مع scheduler.py =====
def send_notification(account_data: dict):
    """تحويل للدالة الجديدة"""
    send_ready_notification(account_data)
