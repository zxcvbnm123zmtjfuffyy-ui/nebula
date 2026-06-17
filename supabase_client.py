from supabase import create_client, Client
from datetime import datetime
import config
from logger import log_error, log_info

supabase: Client = None

def init_supabase():
    global supabase
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        log_info("⚠️ Supabase غير مضبوط، سيتم استخدام JSON محلي")
        return None
    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        log_info("✅ تم الاتصال بـ Supabase بنجاح")
        return supabase
    except Exception as e:
        log_error(f"❌ فشل الاتصال بـ Supabase: {e}")
        return None

def save_account_data(token: str, data: dict):
    if not supabase:
        return None
    try:
        existing = supabase.table("accounts").select("*").eq("token_hash", token[:20]).execute()
        if existing.data:
            supabase.table("accounts").update({
                "username": data.get("username"),
                "user_id": data.get("user_id"),
                "boost_status": data.get("status"),
                "cooldown_ends_at": data.get("cooldown_ends"),
                "last_boost_check": data.get("last_check"),
                "server_id": data.get("server_id"),
                "nitro_type": data.get("nitro_type"),
                "nitro_status": data.get("nitro_status"),
                "nitro_expires_at": data.get("nitro_expires_at"),
                "nitro_days_left": data.get("nitro_days_left"),
                "nitro_last_check": data.get("nitro_last_check"),
            }).eq("token_hash", token[:20]).execute()
        else:
            supabase.table("accounts").insert({
                "token_hash": token[:20],
                "username": data.get("username"),
                "user_id": data.get("user_id"),
                "boost_status": data.get("status"),
                "cooldown_ends_at": data.get("cooldown_ends"),
                "last_boost_check": data.get("last_check"),
                "server_id": data.get("server_id"),
                "nitro_type": data.get("nitro_type"),
                "nitro_status": data.get("nitro_status"),
                "nitro_expires_at": data.get("nitro_expires_at"),
                "nitro_days_left": data.get("nitro_days_left"),
                "nitro_last_check": data.get("nitro_last_check"),
            }).execute()
        return True
    except Exception as e:
        log_error(f"فشل حفظ البيانات في Supabase: {e}")
        return None

def get_all_accounts():
    if not supabase:
        return []
    try:
        result = supabase.table("accounts").select("*").execute()
        return result.data
    except Exception as e:
        log_error(f"فشل جلب البيانات من Supabase: {e}")
        return []