from supabase import create_client, Client
import config
import os

supabase: Client = None

def init_supabase():
    global supabase
    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        print("[✅] تم الاتصال بـ Supabase بنجاح")
        return supabase
    except Exception as e:
        print(f"[❌] فشل الاتصال بـ Supabase: {e}")
        raise

def get_settings():
    """جلب الإعدادات من Supabase مع تعطيل التخزين المؤقت"""
    try:
        if not supabase:
            return None
        # ✅ إضافة headers لمنع التخزين المؤقت
        result = supabase.table("settings").select("*").limit(1).execute(
            headers={"Cache-Control": "no-cache"}
        )
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"[⚠️] فشل جلب الإعدادات من Supabase: {e}")
        return None

def update_settings(settings: dict):
    """تحديث الإعدادات في Supabase"""
    try:
        if not supabase:
            print("[⚠️] Supabase غير متصل، لا يمكن تحديث الإعدادات")
            return
        existing = supabase.table("settings").select("*").limit(1).execute(
            headers={"Cache-Control": "no-cache"}
        )
        if existing.data:
            supabase.table("settings").update(settings).eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("settings").insert(settings).execute()
        print("[✅] تم تحديث الإعدادات في Supabase")
    except Exception as e:
        print(f"[❌] فشل تحديث الإعدادات: {e}")

def get_tokens():
    """جلب قائمة التوكنات (من Supabase أو البيئة)"""
    settings = get_settings()
    if settings and settings.get("tokens"):
        tokens_str = settings["tokens"].strip()
        if tokens_str:
            tokens = [t.strip() for t in tokens_str.split(",") if t.strip()]
            if tokens:
                print(f"[✅] تم جلب {len(tokens)} توكن من Supabase")
                return tokens
    env_tokens = os.getenv("SELF_TOKENS", "")
    if env_tokens:
        tokens = [t.strip() for t in env_tokens.split(",") if t.strip()]
        if tokens:
            print(f"[✅] تم جلب {len(tokens)} توكن من متغير البيئة SELF_TOKENS")
            return tokens
    print("[⚠️] لا توجد توكنات في Supabase ولا في متغير البيئة")
    return []

def update_tokens(tokens: list):
    settings = get_settings() or {}
    settings["tokens"] = ",".join(tokens)
    update_settings(settings)

def get_webhooks():
    settings = get_settings()
    if settings:
        webhook_url = settings.get("webhook_url", "").strip()
        log_webhook_url = settings.get("log_webhook_url", "").strip()
        if webhook_url or log_webhook_url:
            print("[✅] تم جلب روابط الويب هوك من Supabase")
            return {"webhook_url": webhook_url, "log_webhook_url": log_webhook_url}
    webhook_url = os.getenv("WEBHOOK_URL", "").strip()
    log_webhook_url = os.getenv("LOG_WEBHOOK_URL", "").strip()
    if webhook_url or log_webhook_url:
        print("[✅] تم جلب روابط الويب هوك من متغيرات البيئة")
        return {"webhook_url": webhook_url, "log_webhook_url": log_webhook_url}
    print("[⚠️] لا توجد روابط ويب هوك في Supabase ولا في متغيرات البيئة")
    return {"webhook_url": "", "log_webhook_url": ""}

def update_webhooks(webhook_url: str, log_webhook_url: str):
    settings = get_settings() or {}
    settings["webhook_url"] = webhook_url
    settings["log_webhook_url"] = log_webhook_url
    update_settings(settings)