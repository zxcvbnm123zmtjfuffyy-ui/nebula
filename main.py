#!/usr/bin/env python3
"""
Nebula v4.0 - Discord Boost Monitor
"""

import config
from bot_commands import run_bot

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════╗
    ║        🚀 NEBULA v4.0               ║
    ║    Discord Boost Monitor            ║
    ║    (أوامر عربية بالكامل)           ║
    ╚══════════════════════════════════════╝
    """)
    print(f"📊 عدد الحسابات المراقبة: {len(config.SELF_TOKENS)}")
    print(f"🔒 السيرفر المسموح: {config.ALLOWED_GUILD_ID}")
    print(f"⏱️ التأخير بين الطلبات: {config.MIN_DELAY_SECONDS}-{config.MAX_DELAY_SECONDS} ثانية")
    print("🤖 تشغيل البوت...")
    run_bot()
