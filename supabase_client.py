from supabase import create_client, Client
import config
from logger import log_info, log_error

supabase: Client = None

def init_supabase():
    global supabase
    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        log_info("✅ تم الاتصال بـ Supabase بنجاح")
        return supabase
    except Exception as e:
        log_error(f"❌ فشل الاتصال بـ Supabase: {e}")
        raise

def get_settings():
    """جلب الإعدادات من Supabase (التوكنات والويب هوك)"""
    try:
        result = supabase.table("settings").select("*").limit(1).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        log_error(f"فشل جلب الإعدادات: {e}")
        return None

def update_settings(settings: dict):
    """تحديث الإعدادات في Supabase"""
    try:
        existing = supabase.table("settings").select("*").limit(1).execute()
        if existing.data:
            supabase.table("settings").update(settings).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("settings").insert(settings).execute()
        log_info("✅ تم تحديث الإعدادات")
    except Exception as e:
        log_error(f"فشل تحديث الإعدادات: {e}")

def get_tokens():
    """جلب قائمة التوكنات من Supabase"""
    settings = get_settings()
    if settings and settings.get("tokens"):
        return [t.strip() for t in settings["tokens"].split(",") if t.strip()]
    return []

def update_tokens(tokens: list):
    """تحديث قائمة التوكنات"""
    settings = get_settings() or {}
    settings["tokens"] = ",".join(tokens)
    update_settings(settings)

def get_webhooks():
    """جلب روابط الويب هوك"""
    settings = get_settings()
    if settings:
        return {
            "webhook_url": settings.get("webhook_url", ""),
            "log_webhook_url": settings.get("log_webhook_url", "")
        }
    return {"webhook_url": "", "log_webhook_url": ""}

def update_webhooks(webhook_url: str, log_webhook_url: str):
    """تحديث روابط الويب هوك"""
    settings = get_settings() or {}
    settings["webhook_url"] = webhook_url
    settings["log_webhook_url"] = log_webhook_url
    update_settings(settings)