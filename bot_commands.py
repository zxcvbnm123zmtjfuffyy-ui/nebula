import discord
from discord.ext import commands
import config
from boost_checker import check_account, check_all_accounts
from nitro_checker import check_nitro, check_all_nitro
from notifier import send_ready_notification, send_waiting_notification
from logger import log_info

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f"✅ البوت جاهز: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!مساعدة"))

def is_owner(ctx):
    return ctx.author.id == config.OWNER_ID

@bot.command(name="مساعدة")
async def help_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    embed = discord.Embed(title="📋 أوامر Nebula (عربي)", color=0x00bfff)
    embed.add_field(name="!حالة", value="عرض حالة جميع الحسابات", inline=False)
    embed.add_field(name="!فحص <ID>", value="فحص حساب محدد بواسطة User ID", inline=False)
    embed.add_field(name="!قائمة", value="عرض قائمة مختصرة", inline=False)
    embed.add_field(name="!نيترو", value="عرض حالة Nitro لجميع الحسابات", inline=False)
    embed.add_field(name="!إشعار <ID>", value="إرسال إشعار لحساب معين (يدوياً)", inline=False)
    embed.set_footer(text="جميع الأوامر خاصة بالمالك فقط")
    await ctx.send(embed=embed)

@bot.command(name="حالة")
async def status_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send("⏳ جاري فحص جميع الحسابات...")
    results = check_all_accounts()
    embed = discord.Embed(
        title="📊 Nebula — حالة الحسابات",
        color=0x00ff7f if any(r.get("status") == "ready" for r in results) else 0xff4444,
        timestamp=discord.utils.utcnow()
    )
    for r in results:
        if "error" in r:
            embed.add_field(name="❌ خطأ", value=r["error"], inline=False)
        else:
            emoji = "✅" if r["status"] == "ready" else "⏳"
            cooldown = f"\nينتهي: <t:{r['cooldown_timestamp']}:R>" if r.get("cooldown_timestamp") else ""
            embed.add_field(
                name=f"{emoji} {r['username']}",
                value=f"🆔 `{r['user_id']}`\n{r['message']}{cooldown}",
                inline=False
            )
    embed.set_footer(text=f"عدد الحسابات: {len(results)}")
    await ctx.send(embed=embed)

@bot.command(name="فحص")
async def check_cmd(ctx, user_id: str):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send(f"⏳ جاري فحص الحساب `{user_id}`...")
    for token in config.SELF_TOKENS:
        result = check_account(token)
        if result.get("user_id") == user_id:
            embed = discord.Embed(
                title=f"🔍 نتيجة فحص {result['username']}",
                color=0x00ff7f if result["status"] == "ready" else 0xff4444,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="🆔 ID", value=f"`{result['user_id']}`", inline=True)
            embed.add_field(name="📊 الحالة", value=result["message"], inline=False)
            if result.get("cooldown_timestamp"):
                embed.add_field(
                    name="⏳ ينتهي",
                    value=f"<t:{result['cooldown_timestamp']}:F>\n<t:{result['cooldown_timestamp']}:R>",
                    inline=True
                )
            if result.get("server_id"):
                embed.add_field(name="🏠 آخر سيرفر", value=f"`{result['server_id']}`", inline=True)
            await ctx.send(embed=embed)
            return
    await ctx.send(f"❌ لم أجد حساباً بـ ID: `{user_id}`")

@bot.command(name="قائمة")
async def list_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send("⏳ جاري...")
    results = check_all_accounts()
    lines = []
    for r in results:
        if "error" in r:
            lines.append(f"❌ {r['error']}")
        else:
            emoji = "✅" if r["status"] == "ready" else "⏳"
            lines.append(f"{emoji} `{r['username']}` — {r['message']}")
    embed = discord.Embed(
        title="📋 قائمة الحسابات",
        description="\n".join(lines) or "لا توجد بيانات",
        color=0x00bfff
    )
    embed.set_footer(text=f"عدد الحسابات: {len(results)}")
    await ctx.send(embed=embed)

@bot.command(name="نيترو")
async def nitro_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send("⏳ جاري جلب بيانات Nitro...")
    results = check_all_nitro()
    embed = discord.Embed(
        title="💎 Nebula — حالة Nitro",
        color=0xf47fff,
        timestamp=discord.utils.utcnow()
    )
    for r in results:
        if "error" in r:
            embed.add_field(name="❌ خطأ", value=r["error"], inline=False)
        else:
            embed.add_field(
                name=r["username"],
                value=f"🆔 `{r['user_id']}`\n{r['message']}",
                inline=False
            )
    embed.set_footer(text=f"عدد الحسابات: {len(results)}")
    await ctx.send(embed=embed)

@bot.command(name="إشعار")
async def notify_cmd(ctx, user_id: str):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send(f"⏳ جاري البحث عن الحساب `{user_id}`...")
    for token in config.SELF_TOKENS:
        result = check_account(token)
        if result.get("user_id") == user_id:
            if result["status"] == "ready":
                send_ready_notification(result["username"], result["user_id"], result.get("cooldown_timestamp"))
                await ctx.send("✅ تم إرسال إشعار الجاهزية.")
            else:
                send_waiting_notification(
                    result["username"],
                    result["user_id"],
                    result["cooldown_timestamp"],
                    result["message"]
                )
                await ctx.send("✅ تم إرسال إشعار الانتظار.")
            return
    await ctx.send(f"❌ لم أجد حساباً بـ ID: `{user_id}`")

def run_bot():
    bot.run(config.BOT_TOKEN)
