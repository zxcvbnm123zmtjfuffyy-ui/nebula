import discord
from datetime import datetime, timezone
from typing import Dict

def build_boost_embed(result: Dict) -> discord.Embed:
    """بناء إمبد احترافي مع Markdown لنتيجة فحص Boost"""
    username = result.get("username", "Unknown")
    user_id = result.get("user_id", "???")
    avatar_url = result.get("avatar_url")
    status = result.get("status", "waiting")
    message = result.get("message", "—")
    cooldown_ts = result.get("cooldown_timestamp")
    last_boost_ts = result.get("last_boost_timestamp")
    server_id = result.get("server_id")

    color = 0x00ff7f if status == "ready" else 0xff4444

    embed = discord.Embed(
        title="🚀 **Nebula — Boost Status**",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )

    if avatar_url:
        embed.set_thumbnail(url=avatar_url)

    embed.add_field(
        name="👤 **الحساب**",
        value=f"**{username}**\n`{user_id}`",
        inline=True
    )
    embed.add_field(
        name="📊 **الحالة**",
        value=message,
        inline=True
    )

    if last_boost_ts:
        embed.add_field(
            name="📅 **آخر ضربة**",
            value=f"<t:{last_boost_ts}:F>\n<t:{last_boost_ts}:R>",
            inline=False
        )
    else:
        embed.add_field(
            name="📅 **آخر ضربة**",
            value="❌ **لا توجد**",
            inline=False
        )

    if cooldown_ts:
        embed.add_field(
            name="⏳ **ينتهي**",
            value=f"<t:{cooldown_ts}:F>\n<t:{cooldown_ts}:R>",
            inline=True
        )

    if server_id:
        embed.add_field(
            name="🏠 **السيرفر**",
            value=f"`{server_id}`",
            inline=True
        )

    if status == "waiting" and cooldown_ts:
        now = datetime.now(timezone.utc).timestamp()
        remaining = cooldown_ts - now
        total = 604800
        progress = max(0, min(100, int(((total - remaining) / total) * 100)))
        bar_length = 20
        filled = int(progress / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        days = int(remaining // 86400)
        hours = int((remaining % 86400) // 3600)
        minutes = int((remaining % 3600) // 60)
        time_text = f"{days}ي {hours}س {minutes}د"
        embed.add_field(
            name="📊 **التقدم**",
            value=f"`{bar}` **{progress}%**\n⏳ **متبقي:** `{time_text}`",
            inline=False
        )

    embed.set_footer(text=f"Nebula Monitor • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    return embed


def build_nitro_embed(result: Dict) -> discord.Embed:
    """بناء إمبد Nitro مع Markdown"""
    username = result.get("username", "Unknown")
    user_id = result.get("user_id", "???")
    nitro_type = result.get("nitro_type", "بدون Nitro")
    nitro_emoji = result.get("nitro_emoji", "⚪")
    expires_ts = result.get("expires_timestamp")
    days_left = result.get("days_left")
    warn = result.get("warn", False)

    color = 0xffaa00 if warn else result.get("nitro_color", 0xf47fff)

    embed = discord.Embed(
        title="💎 **Nitro Status**",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )

    embed.add_field(
        name="👤 **الحساب**",
        value=f"**{username}**\n`{user_id}`",
        inline=True
    )
    embed.add_field(
        name="💎 **النوع**",
        value=f"{nitro_emoji} **{nitro_type}**",
        inline=True
    )

    if expires_ts:
        embed.add_field(
            name="📅 **ينتهي**",
            value=f"<t:{expires_ts}:F>\n<t:{expires_ts}:R>",
            inline=False
        )
        if days_left is not None:
            embed.add_field(
                name="📆 **الأيام المتبقية**",
                value=f"`{days_left}` يوم" + (" ⚠️" if warn else ""),
                inline=True
            )
    else:
        embed.add_field(
            name="📅 **الانتهاء**",
            value="**غير محدد (نشط)**",
            inline=False
        )

    if warn:
        embed.add_field(
            name="⚠️ **تحذير**",
            value="**ينتهي خلال 7 أيام!**",
            inline=False
        )

    embed.set_footer(text=f"Nebula Monitor • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
    return embed