import discord
from discord.ext import commands
import config
from boost_checker import check_account, check_all_accounts, search_account_by_username
from nitro_checker import check_nitro, check_all_nitro
from notifier import send_ready_notification, send_waiting_notification
from embeds import build_boost_embed, build_nitro_embed
from logger import log_info

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')

LOADING_EMOJI = "<a:1000060120:1516852528631779460>"

@bot.event
async def on_ready():
    print(f"✅ البوت جاهز: {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!مساعدة"))

def is_owner(ctx):
    return ctx.author.id == config.OWNER_ID

# ========== الأوامر العامة ==========

@bot.command(name="مساعدة")
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📋 **أوامر Nebula**",
        description="**البوت خاص بمراقبة حسابات Boost و Nitro**",
        color=0x00bfff
    )
    embed.add_field(name="**!مساعدة**", value="عرض هذه القائمة", inline=False)
    embed.add_field(name="**!فحص <ID>**", value="فحص حساب محدد بـ **User ID**", inline=False)
    embed.add_field(name="**!بحث <اسم>**", value="البحث عن حساب بالاسم", inline=False)
    embed.add_field(name="**!نيترو <ID>**", value="عرض Nitro لحساب (بدون ID: أول حساب)", inline=False)
    embed.add_field(
        name="🔒 **أوامر المالك**",
        value="`!حالة` – عرض جميع الحسابات\n`!قائمة` – قائمة مختصرة\n`!إشعار <ID>` – إرسال إشعار",
        inline=False
    )
    embed.set_footer(text="جميع الأوامر مفتوحة للجميع ما عدا المذكورة 🔒")
    await ctx.send(embed=embed)

@bot.command(name="فحص")
async def check_cmd(ctx, user_id: str):
    loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري فحص الحساب** `{user_id}` **...**")
    try:
        from supabase_client import get_tokens
        for token in get_tokens():
            result = check_account(token)
            if result.get("user_id") == user_id:
                embed = build_boost_embed(result)
                await loading_msg.edit(content=None, embed=embed)
                log_info(f"✅ فحص عام للحساب {user_id} بواسطة {ctx.author}")
                return
        await loading_msg.edit(content=f"❌ **لم أجد حساباً بـ ID:** `{user_id}`", embed=None)
    except Exception as e:
        await loading_msg.edit(content=f"❌ **حدث خطأ:** {str(e)[:100]}", embed=None)

@bot.command(name="بحث")
async def search_cmd(ctx, username: str):
    loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري البحث عن** `{username}` **...**")
    result = search_account_by_username(username)
    if result:
        embed = build_boost_embed(result)
        await loading_msg.edit(content=None, embed=embed)
        log_info(f"🔍 بحث عن {username} بواسطة {ctx.author}")
    else:
        await loading_msg.edit(content=f"❌ **لم أجد حساباً باسم:** `{username}`", embed=None)

@bot.command(name="نيترو")
async def nitro_cmd(ctx, user_id: str = None):
    from supabase_client import get_tokens
    tokens = get_tokens()
    if user_id is None:
        token = tokens[0]
        loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري جلب بيانات Nitro للحساب الأول...**")
        result = check_nitro(token)
        if "error" in result:
            await loading_msg.edit(content=f"❌ **{result['error']}**", embed=None)
        else:
            embed = build_nitro_embed(result)
            await loading_msg.edit(content=None, embed=embed)
        log_info(f"✅ Nitro عام (أول حساب) بواسطة {ctx.author}")
    else:
        loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري جلب بيانات Nitro للحساب** `{user_id}` **...**")
        for token in tokens:
            result = check_nitro(token)
            if result.get("user_id") == user_id:
                embed = build_nitro_embed(result)
                await loading_msg.edit(content=None, embed=embed)
                log_info(f"✅ Nitro عام للحساب {user_id} بواسطة {ctx.author}")
                return
        await loading_msg.edit(content=f"❌ **لم أجد حساباً بـ ID:** `{user_id}`", embed=None)

# ========== الأوامر الخاصة بالمالك ==========

@bot.command(name="حالة")
async def status_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ **غير مصرح لك.**")
    loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري فحص جميع الحسابات...**")
    results = check_all_accounts()
    await loading_msg.delete()
    for r in results:
        if "error" in r:
            await ctx.send(f"❌ **خطأ:** {r['error']}")
        else:
            embed = build_boost_embed(r)
            await ctx.send(embed=embed)
    log_info(f"📊 حالة الحسابات بواسطة {ctx.author}")

@bot.command(name="قائمة")
async def list_cmd(ctx):
    if not is_owner(ctx):
        return await ctx.send("❌ **غير مصرح لك.**")
    loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري تحضير القائمة...**")
    results = check_all_accounts()
    await loading_msg.delete()
    lines = []
    for r in results:
        if "error" in r:
            lines.append(f"❌ **{r['error']}**")
        else:
            emoji = "✅" if r["status"] == "ready" else "⏳"
            lines.append(f"{emoji} **`{r['username']}`** — {r['message']}")
    embed = discord.Embed(
        title="📋 **قائمة الحسابات**",
        description="\n".join(lines) or "**لا توجد بيانات**",
        color=0x00bfff
    )
    embed.set_footer(text=f"عدد الحسابات: {len(results)}")
    await ctx.send(embed=embed)
    log_info(f"📋 قائمة الحسابات بواسطة {ctx.author}")

@bot.command(name="إشعار")
async def notify_cmd(ctx, user_id: str):
    if not is_owner(ctx):
        return await ctx.send("❌ **غير مصرح لك.**")
    loading_msg = await ctx.send(f"{LOADING_EMOJI} **جاري البحث عن الحساب** `{user_id}` **...**")
    from supabase_client import get_tokens
    for token in get_tokens():
        result = check_account(token)
        if result.get("user_id") == user_id:
            if result["status"] == "ready":
                send_ready_notification(result["username"], result["user_id"], result.get("cooldown_timestamp"))
                await loading_msg.edit(content="✅ **تم إرسال إشعار الجاهزية.**", embed=None)
            else:
                send_waiting_notification(
                    result["username"],
                    result["user_id"],
                    result["cooldown_timestamp"],
                    result["message"]
                )
                await loading_msg.edit(content="✅ **تم إرسال إشعار الانتظار.**", embed=None)
            log_info(f"📨 إشعار للحساب {user_id} بواسطة {ctx.author}")
            return
    await loading_msg.edit(content=f"❌ **لم أجد حساباً بـ ID:** `{user_id}`", embed=None)

def run_bot():
    bot.run(config.BOT_TOKEN)
