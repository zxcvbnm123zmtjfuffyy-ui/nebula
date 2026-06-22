from supabase import create_client, Client
import config
import os

supabase: Client = None

def init_supabase():
    """تهيئة الاتصال بـ Supabase"""
    global supabase
    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        print("[✅] تم الاتصال بـ Supabase بنجاح")
        return supabase
    except Exception as e:
        print(f"[❌] فشل الاتصال بـ Supabase: {e}")
        raise

def _get_headers() -> dict:
    """رؤوس تمنع الكاش تماماً"""
    return {"Cache-Control": "no-cache, no-store, must-revalidate"}

def get_settings():
    """جلب الإعدادات من Supabase (بدون كاش)"""
    try:
        if not supabase:
            return None
        result = supabase.table("settings").select("*").limit(1).execute(
            headers=_get_headers()
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[⚠️] فشل جلب الإعدادات: {e}")
        return None

def update_settings(settings: dict):
    """تحديث الإعدادات في Supabase"""
    try:
        if not supabase:
            print("[⚠️] Supabase غير متصل")
            return
        existing = supabase.table("settings").select("*").limit(1).execute(
            headers=_get_headers()
        )
        if existing.data:
            supabase.table("settings").update(settings).eq("id", existing.data[0]["id"]).execute(
                headers=_get_headers()
            )
        else:
            supabase.table("settings").insert(settings).execute(headers=_get_headers())
        print("[✅] تم تحديث الإعدادات")
    except Exception as e:
        print(f"[❌] فشل تحديث الإعدادات: {e}")

def get_tokens() -> list:
    """
    جلب التوكنات:
    1. من Supabase (بدون كاش)
    2. إذا لم توجد، من متغير البيئة SELF_TOKENS
    3. إذا لم توجد، قائمة فارغة
    """
    settings = get_settings()
    if settings and settings.get("tokens"):
        tokens_str = settings["tokens"].strip()
        if tokens_str:
            tokens = [t.strip() for t in tokens_str.split(",") if t.strip()]
            if tokens:
                print(f"[✅] {len(tokens)} توكن من Supabase")
                return tokens
    
    # احتياطي من البيئة
    if config.SELF_TOKENS:
        print(f"[✅] {len(config.SELF_TOKENS)} توكن من البيئة (احتياطي)")
        return config.SELF_TOKENS.copy()
    
    print("[⚠️] لا توجد توكنات")
    return []

def update_tokens(tokens: list):
    """تحديث التوكنات في Supabase"""
    settings = get_settings() or {}
    settings["tokens"] = ",".join(tokens)
    update_settings(settings)
    # تحديث المتغير الاحتياطي
    config.SELF_TOKENS = tokens

def get_webhooks() -> dict:
    """
    جلب روابط الويب هوك:
    1. من Supabase (بدون كاش)
    2. من متغيرات البيئة
    """
    settings = get_settings()
    if settings:
        webhook_url = settings.get("webhook_url", "").strip()
        log_webhook_url = settings.get("log_webhook_url", "").strip()
        if webhook_url or log_webhook_url:
            print("[✅] ويب هوك من Supabase")
            return {"webhook_url": webhook_url, "log_webhook_url": log_webhook_url}
    
    # احتياطي من البيئة
    return {
        "webhook_url": config.WEBHOOK_URL,
        "log_webhook_url": config.LOG_WEBHOOK_URL
    }

def update_webhooks(webhook_url: str, log_webhook_url: str):
    """تحديث روابط الويب هوك في Supabase"""
    settings = get_settings() or {}
    settings["webhook_url"] = webhook_url
    settings["log_webhook_url"] = log_webhook_url
    update_settings(settings)
    # تحديث المتغيرات الاحتياطية
    config.WEBHOOK_URL = webhook_url
    config.LOG_WEBHOOK_URL = log_webhook_url