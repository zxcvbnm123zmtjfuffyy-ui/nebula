-- ==========================================
-- جدول 1: accounts
-- معلومات الحسابات + Boost + Nitro
-- ==========================================
CREATE TABLE IF NOT EXISTS accounts (
    id               BIGSERIAL PRIMARY KEY,

    -- معلومات الحساب
    token_hash       TEXT UNIQUE NOT NULL,   -- أول 20 حرف من التوكن
    username         TEXT,
    user_id          TEXT,

    -- بيانات Boost
    boost_status     TEXT,                   -- ready / waiting / no_slots
    cooldown_ends_at TEXT,
    server_id        TEXT,
    last_boost_check TEXT,

    -- بيانات Nitro
    nitro_type       TEXT,                   -- Nitro / Nitro Classic / Basic
    nitro_status     TEXT,                   -- active / canceled / inactive
    nitro_expires_at TEXT,
    nitro_days_left  INT,
    nitro_last_check TEXT,

    -- تتبع
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- جدول 2: check_history
-- سجل كل الفحوصات
-- ==========================================
CREATE TABLE IF NOT EXISTS check_history (
    id          BIGSERIAL PRIMARY KEY,
    token_hash  TEXT        NOT NULL,
    status      TEXT,                        -- ready / waiting / error
    details     JSONB,                       -- تفاصيل إضافية
    checked_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- Index للسرعة
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_accounts_token     ON accounts      (token_hash);
CREATE INDEX IF NOT EXISTS idx_history_token      ON check_history (token_hash);
CREATE INDEX IF NOT EXISTS idx_history_checked_at ON check_history (checked_at DESC);

-- ==========================================
-- تحديث updated_at تلقائياً
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
