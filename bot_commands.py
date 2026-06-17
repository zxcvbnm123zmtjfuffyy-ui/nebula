import discord
from discord import app_commands
from datetime import datetime, timezone
import config
from logger import log_info, log_error, log_success


# ===== الألوان =====
COLOR_READY   = 0x00ff7f
COLOR_WAITING = 0xff4444
COLOR_NITRO   = 0xf47fff
COLOR_WARNING = 0xffaa00
COLOR_ERROR   = 0x747f8d


# ===========================
# 🔒 فحص صلاحية المالك
# ===========================
def is_owner(interaction: discord.Interaction) -> bool:
    return interaction.user.id == config.OWNER_ID


def owner_only():
    """Decorator يمنع غير المالك من استخدام الأوامر"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not is_owner(interaction):
            await interaction.response.send_message(
                embed=discord.Embed(
                    description="❌ هذا البوت خاص ولا يمكنك استخدامه.",
                    color=COLOR_ERROR
                ),
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)


# ===========================
# 🤖 إعداد البوت
# ===========================
class NebulaBotClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        log_success("✅ تم مزامنة Slash Commands")

    async def on_ready(self):
        log_success(f"✅ البوت شغّال: {self.user} | OWNER: {config.OWNER_ID}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="🚀 Nebula Monitor"
            )
        )


bot = NebulaBotClient()


# ===========================
# /status — حالة كل الحسابات
# ===========================
@bot.tree.command(name="status", description="عرض حالة جميع الحسابات")
async def cmd_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    from boost_checker import check_all_accounts
    results = await interaction.client.loop.run_in_executor(None, check_all_accounts)

    ready   = [r for r in results if r.get("status") == "ready"]
    waiting = [r for r in results if r.get("status") == "waiting"]
    errors  = [r for r in results if r.get("error")]

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
            lines.append(f"⏳ `{name}` — <t:{ts}:R>" if ts else f"⏳ `{name}` — {r.get('message')}")

    embed = discord.Embed(
        title="📊 Nebula — حالة الحسابات",
        description="\n".join(lines) or "لا توجد بيانات",
        color=COLOR_READY if ready else COLOR_WAITING,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="✅ جاهز",   value=str(len(ready)),   inline=True)
    embed.add_field(name="⏳ انتظار", value=str(len(waiting)), inline=True)
    embed.add_field(name="❌ خطأ",    value=str(len(errors)),  inline=True)
    embed.set_footer(text=f"Nebula Monitor • {len(results)} حساب")

    await interaction.followup.send(embed=embed, ephemeral=True)
    log_info(f"📊 /status نُفِّذ من {interaction.user}")


# ===========================
# /check — فحص حساب محدد
# ===========================
@bot.tree.command(name="check", description="فحص حساب محدد فوراً")
@app_commands.describe(account="رقم الحساب (1 - عدد الحسابات)")
async def cmd_check(interaction: discord.Interaction, account: int):
    await interaction.response.defer(ephemeral=True)

    tokens = config.SELF_TOKENS
    if account < 1 or account > len(tokens):
        await interaction.followup.send(
            embed=discord.Embed(
                description=f"❌ رقم غير صحيح. اختر بين 1 و {len(tokens)}",
                color=COLOR_ERROR
            ),
            ephemeral=True
        )
        return

    token = tokens[account - 1]
    from boost_checker import check_single_account
    result = await interaction.client.loop.run_in_executor(None, check_single_account, token)

    if result.get("error"):
        embed = discord.Embed(
            title=f"❌ فشل فحص الحساب {account}",
            description=result["error"],
            color=COLOR_ERROR,
            timestamp=datetime.now(timezone.utc)
        )
    else:
        color = COLOR_READY if result.get("status") == "ready" else COLOR_WAITING
        ts    = result.get("cooldown_timestamp")

        embed = discord.Embed(
            title=f"🔍 نتيجة فحص الحساب {account}",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="👤 اليوزر",  value=f"`{result.get('username')}`",  inline=True)
        embed.add_field(name="🆔 ID",       value=f"`{result.get('user_id')}`",   inline=True)
        embed.add_field(name="📊 الحالة",   value=result.get("message", "—"),     inline=False)

        if ts and result.get("status") == "waiting":
            from notifier import make_progress_bar
            progress = make_progress_bar(result.get("remaining", 0))
            embed.add_field(name="⏳ ينتهي",   value=f"<t:{ts}:F>\n<t:{ts}:R>", inline=True)
            embed.add_field(name="📊 التقدم",   value=progress,                  inline=False)

    embed.set_footer(text="Nebula Monitor • /check")
    await interaction.followup.send(embed=embed, ephemeral=True)
    log_info(f"🔍 /check {account} نُفِّذ من {interaction.user}")


# ===========================
# /nitro — Nitro كل الحسابات
# ===========================
@bot.tree.command(name="nitro", description="عرض حالة Nitro لجميع الحسابات")
@owner_only()
async def cmd_nitro(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    from nitro_checker import check_all_nitro
    results = await interaction.client.loop.run_in_executor(None, check_all_nitro)

    lines = []
    warn_count = 0
    for r in results:
        if r.get("error"):
            lines.append(f"❌ `{r.get('token_preview', '???')}` — خطأ")
            continue

        name       = r.get("username", "Unknown")
        emoji      = r.get("nitro_emoji", "⚪")
        ntype      = r.get("nitro_type", "—")
        expires_ts = r.get("expires_timestamp")
        days_left  = r.get("days_left")

        warn = " ⚠️" if (days_left and days_left <= 7) else ""
        if warn:
            warn_count += 1

        ts_text = f"<t:{expires_ts}:R>" if expires_ts else "—"
        lines.append(f"{emoji} `{name}` — {ntype} | {ts_text}{warn}")

    color = COLOR_WARNING if warn_count > 0 else COLOR_NITRO
    embed = discord.Embed(
        title="💎 Nebula — حالة Nitro",
        description="\n".join(lines) or "لا توجد بيانات",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    if warn_count:
        embed.add_field(
            name="⚠️ تحذير",
            value=f"`{warn_count}` حساب Nitro ينتهي خلال 7 أيام!",
            inline=False
        )
    embed.set_footer(text=f"Nebula Monitor • {len(results)} حساب")

    await interaction.followup.send(embed=embed, ephemeral=True)
    log_info(f"💎 /nitro نُفِّذ من {interaction.user}")


# ===========================
# /next — أقرب حساب جاهز
# ===========================
@bot.tree.command(name="next", description="عرض أقرب حساب سيصير جاهز")
@owner_only()
async def cmd_next(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    from boost_checker import check_all_accounts
    results = await interaction.client.loop.run_in_executor(None, check_all_accounts)

    ready   = [r for r in results if r.get("status") == "ready"]
    waiting = [r for r in results if r.get("status") == "waiting" and r.get("remaining")]

    if ready:
        names = ", ".join(f"`{r.get('username')}`" for r in ready)
        embed = discord.Embed(
            title="🚀 حسابات جاهزة الآن!",
            description=f"هذي الحسابات جاهزة للبوست:\n{names}",
            color=COLOR_READY,
            timestamp=datetime.now(timezone.utc)
        )
    elif waiting:
        # أقرب حساب حسب remaining
        nearest = min(waiting, key=lambda r: r["remaining"])
        ts      = nearest.get("cooldown_timestamp")

        from notifier import make_progress_bar
        progress = make_progress_bar(nearest["remaining"])

        embed = discord.Embed(
            title="⏳ أقرب حساب جاهز",
            color=COLOR_WAITING,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="👤 الحساب",  value=f"`{nearest.get('username')}`", inline=True)
        embed.add_field(name="⏳ ينتهي",   value=f"<t:{ts}:R>" if ts else "—",   inline=True)
        embed.add_field(name="📅 التاريخ", value=f"<t:{ts}:F>" if ts else "—",   inline=True)
        embed.add_field(name="📊 التقدم",  value=progress,                        inline=False)
    else:
        embed = discord.Embed(
            description="❌ لا توجد بيانات كافية.",
            color=COLOR_ERROR
        )

    embed.set_footer(text="Nebula Monitor • /next")
    await interaction.followup.send(embed=embed, ephemeral=True)
    log_info(f"⏭️ /next نُفِّذ من {interaction.user}")


# ===========================
# /pause — إيقاف مؤقت
# ===========================
@bot.tree.command(name="pause", description="إيقاف المراقبة مؤقتاً")
@owner_only()
async def cmd_pause(interaction: discord.Interaction):
    # نستورد الـ scheduler من main عند الحاجة
    try:
        from main import scheduler
        scheduler.running = False
        embed = discord.Embed(
            title="⏸️ تم إيقاف المراقبة",
            description="الـ Scheduler توقف. استخدم `/resume` لاستئنافه.",
            color=COLOR_WARNING,
            timestamp=datetime.now(timezone.utc)
        )
        log_info(f"⏸️ /pause نُفِّذ من {interaction.user}")
    except Exception as e:
        embed = discord.Embed(
            description=f"❌ فشل الإيقاف: {e}",
            color=COLOR_ERROR
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===========================
# /resume — استئناف المراقبة
# ===========================
@bot.tree.command(name="resume", description="استئناف المراقبة بعد الإيقاف")
@owner_only()
async def cmd_resume(interaction: discord.Interaction):
    try:
        import threading
        from main import scheduler
        scheduler.running = True
        t = threading.Thread(target=scheduler.run_loop, daemon=True)
        t.start()
        embed = discord.Embed(
            title="▶️ تم استئناف المراقبة",
            description="الـ Scheduler يعمل مجدداً!",
            color=COLOR_READY,
            timestamp=datetime.now(timezone.utc)
        )
        log_success(f"▶️ /resume نُفِّذ من {interaction.user}")
    except Exception as e:
        embed = discord.Embed(
            description=f"❌ فشل الاستئناف: {e}",
            color=COLOR_ERROR
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ===========================
# تشغيل البوت
# ===========================
def run_bot():
    if not config.BOT_TOKEN:
        log_error("BOT_TOKEN غير مضبوط، لن يتم تشغيل البوت")
        return
    log_info("🤖 تشغيل بوت الأوامر...")
    bot.run(config.BOT_TOKEN)
