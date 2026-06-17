import discord
from discord.ext import commands
import requests
import config
from logger import log_info

API_URL = "http://localhost:5000"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"✅ البوت العادي جاهز: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!help"))

def is_owner(ctx):
    return ctx.author.id == config.OWNER_ID

@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="📋 أوامر Nebula", color=0x00bfff)
    embed.add_field(name="!status", value="عرض حالة جميع الحسابات", inline=False)
    embed.add_field(name="!check <ID>", value="فحص حساب معين (بواسطة User ID)", inline=False)
    embed.add_field(name="!nitro", value="عرض حالة Nitro لجميع الحسابات", inline=False)
    embed.add_field(name="!next", value="أقرب حساب سيصير جاهز", inline=False)
    embed.add_field(name="!pause", value="إيقاف السكربت مؤقتاً", inline=False)
    embed.add_field(name="!resume", value="استئناف السكربت", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="status")
async def status_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send("⏳ جاري جلب البيانات...")
    try:
        resp = requests.get(f"{API_URL}/status", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            embed = discord.Embed(title="📊 حالة الحسابات", color=0x00ff7f)
            for acc in data:
                status_text = acc.get('boost_status', 'غير معروف')
                embed.add_field(
                    name=acc.get('username', 'Unknown'),
                    value=f"🆔 `{acc.get('user_id')}`\n📊 {status_text}",
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ السكربت لا يستجيب.")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)[:50]}")

@bot.command(name="check")
async def check_cmd(ctx, user_id: str):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send(f"⏳ جاري فحص الحساب `{user_id}`...")
    try:
        resp = requests.get(f"{API_URL}/check/{user_id}", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            embed = discord.Embed(
                title=f"🔍 نتيجة فحص {data.get('username', 'Unknown')}",
                color=0x00ff7f if data.get('boost_status') == 'ready' else 0xff4444
            )
            embed.add_field(name="🆔 ID", value=f"`{data.get('user_id')}`", inline=True)
            embed.add_field(name="📊 الحالة", value=data.get('boost_status', '—'), inline=False)
            if data.get('cooldown_ends_at'):
                embed.add_field(name="⏳ ينتهي", value=f"<t:{int(data['cooldown_ends_at'])}:R>", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ السكربت لا يستجيب.")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)[:50]}")

@bot.command(name="nitro")
async def nitro_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    await ctx.send("⏳ جاري جلب بيانات Nitro...")
    try:
        resp = requests.get(f"{API_URL}/nitro", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            embed = discord.Embed(title="💎 حالة Nitro", color=0xf47fff)
            for acc in data:
                nitro_type = acc.get('nitro_type', 'بدون Nitro')
                embed.add_field(
                    name=acc.get('username', 'Unknown'),
                    value=f"{nitro_type}\n🆔 `{acc.get('user_id')}`",
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ السكربت لا يستجيب.")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)[:50]}")

@bot.command(name="next")
async def next_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    try:
        resp = requests.get(f"{API_URL}/next", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            embed = discord.Embed(
                title="⏳ أقرب حساب جاهز",
                color=0xffcc00
            )
            embed.add_field(name="👤 الحساب", value=data.get('username', 'Unknown'), inline=True)
            embed.add_field(name="📊 الحالة", value=data.get('boost_status', '—'), inline=True)
            if data.get('cooldown_ends_at'):
                embed.add_field(name="⏳ ينتهي", value=f"<t:{int(data['cooldown_ends_at'])}:R>", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("⚠️ السكربت لا يستجيب.")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)[:50]}")

@bot.command(name="pause")
async def pause_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    try:
        resp = requests.post(f"{API_URL}/pause", timeout=5)
        if resp.status_code == 200:
            await ctx.send("⏸️ تم إيقاف السكربت مؤقتاً.")
        else:
            await ctx.send("⚠️ فشل إيقاف السكربت.")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)[:50]}")

@bot.command(name="resume")
async def resume_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ غير مصرح لك.")
    try:
        resp = requests.post(f"{API_URL}/resume", timeout=5)
        if resp.status_code == 200:
            await ctx.send("▶️ تم استئناف السكربت.")
        else:
            await ctx.send("⚠️ فشل استئناف السكربت.")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {str(e)[:50]}")

def run_bot():
    bot.run(config.BOT_TOKEN)
