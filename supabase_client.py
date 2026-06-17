from supabase import create_client, Client
from datetime import datetime
import config
from logger import log_error, log_info

# ===== متغيرات =====
supabase: Client = None

def init_supabase():
    """تهيئة الاتصال بـ Supabase"""
    global supabase
    
    if not config.SUPABASE_URL or not config.SUPABASE_KEY:
        log_info("⚠️ Supabase غير مضبوط، سيتم استخدام JSON محلي")
        return None
    
    try:
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        log_info("✅ تم الاتصال بـ Supabase بنجاح")
        return supabase
    except Exception as e:
        log_error(f"فشل الاتصال بـ Supabase: {e}")
        return None

def save_account_data(token: str, data: dict):
    """حفظ بيانات حساب في Supabase"""
    if not supabase:
        return None
    
    try:
        # نبحث إذا كان الحساب موجود
        existing = supabase.table("accounts").select("*").eq("token_hash", token[:20]).execute()
        
        if existing.data:
            # تحديث
            supabase.table("accounts").update({
                "username": data.get("username"),
                "user_id": data.get("user_id"),
                "status": data.get("status"),
                "cooldown_ends": data.get("cooldown_ends"),
                "last_check": data.get("last_check"),
                "server_id": data.get("server_id"),
                "server_name": data.get("server_name")
            }).eq("token_hash", token[:20]).execute()
        else:
            # إدراج جديد
            supabase.table("accounts").insert({
                "token_hash": token[:20],
                "username": data.get("username"),
                "user_id": data.get("user_id"),
                "status": data.get("status"),
                "cooldown_ends": data.get("cooldown_ends"),
                "last_check": data.get("last_check"),
                "server_id": data.get("server_id"),
                "server_name": data.get("server_name")
            }).execute()
        
        return True
    except Exception as e:
        log_error(f"فشل حفظ البيانات في Supabase: {e}")
        return None

def get_all_accounts():
    """جلب جميع الحسابات من Supabase"""
    if not supabase:
        return []
    
    try:
        result = supabase.table("accounts").select("*").execute()
        return result.data
    except Exception as e:
        log_error(f"فشل جلب البيانات من Supabase: {e}")
        return []

def save_nitro_data(token: str, data: dict):
    """حفظ بيانات Nitro في Supabase"""
    if not supabase:
        return None

    try:
        existing = supabase.table("accounts").select("*").eq("token_hash", token[:20]).execute()

        nitro_fields = {
            "nitro_type":        data.get("nitro_type"),
            "nitro_expires_at":  data.get("expires_at"),
            "nitro_status":      data.get("status"),
            "nitro_days_left":   data.get("days_left"),
            "nitro_last_check":  data.get("checked_at"),
        }

        if existing.data:
            supabase.table("accounts").update(nitro_fields).eq("token_hash", token[:20]).execute()
        else:
            nitro_fields["token_hash"] = token[:20]
            nitro_fields["username"]   = data.get("username")
            nitro_fields["user_id"]    = data.get("user_id")
            supabase.table("accounts").insert(nitro_fields).execute()

        return True
    except Exception as e:
        log_error(f"فشل حفظ بيانات Nitro في Supabase: {e}")
        return None


def log_check_history(token: str, status: str, details: dict = None):
    """تسجيل عملية فحص في جدول history"""
    if not supabase:
        return None
    
    try:
        supabase.table("check_history").insert({
            "token_hash": token[:20],
            "status": status,
            "details": details,
            "checked_at": datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        log_error(f"فشل تسجيل التاريخ في Supabase: {e}")
        return None