import disnake
from disnake.ext import commands, tasks
import json
import os
from datetime import datetime, timedelta, time
import random

intents = disnake.Intents.all()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents)

# ==== ملفات قواعد البيانات الأصلية لتجنب تصفير الحسابات ====
CONFIG_FILE = "config.json"

# ==== إعدادات الرومات الثابتة لسيرفرك ====
IDENTITY_SETUP_CHANNEL = 1484406368524828672   # روم بنل تقديم الهوية
IDENTITY_ADMIN_CHANNEL = 1484405475805233202   # روم قبول ورفض الهوية للإدارة

# ==== رتب التفعيل التلقائي ====
AUTO_ROLES = [1491881927005835407, 1492523810937897132, 1491881746151510158]

# النص الأصلي للحلف المعتمد في سيرفركم
OATH_TEXT_ORIGINAL = "اقـسـم بـالله الـعـظـيـم انـا ( اسـمك ) انـي لـن اخـرب بـ رولات بـلاك لايـن و لـن اسـرب اي رابـط مـن روابـط الـسـيـرفـر وانـي لـن اهـكـر الـسـيـرفـر والله عـلـى مـا اقـولـه شـهـي\nد"


# ================= 🛡️ دالة فحص رتب الإدارة وطاقم العمل (المصلحة بالكامل) =================
def check_admin_permission(member):
    # إذا كان يملك صلاحيات المسؤول العامة في السيرفر
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild or member.guild_permissions.kick_members or member.guild_permissions.manage_roles:
        return True
    
    # الفحص بالكلمات الدلالية لجميع الرتب لضمان عدم رفضهم عند ضغط الأزرار
    admin_keywords = ["اداره", "إدارة", "طاقم", "مسؤول", "مسئول", "اداري", "إداري", "امن", "أمن", "دعم", "شرف", "مراقب", "مشرف"]
    for role in member.roles:
        role_name_lower = role.name.lower()
        if any(keyword in role_name_lower for keyword in admin_keywords):
            return True
            
    return False


def load(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ================= 🪪 نظام الهوية المستقل تماماً =================

class IdentityAdminButtons(disnake.ui.View):
    def __init__(self, applicant_id=None, roblox_name=""):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.roblox_name = roblox_name

    @disnake.ui.button(label="قبول", style=disnake.ButtonStyle.green, custom_id="id_approve_global")
    async def id_approve(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not check_admin_permission(inter.author):
            return await inter.response.send_message("❌ الصلاحية لطاقم الإدارة والمسؤولين فقط بمختلف رتبهم!", ephemeral=True)
        
        await inter.response.defer()
        member = inter.guild.get_member(self.applicant_id)
        if not member:
            return await inter.followup.send("❌ تعذر العثور على العضو داخل السيرفر.")
        
        # --- 🛡️ نظام الحماية الذكي لمنع تصفير الأرقام (يبدأ من 1120) ---
        config = load(CONFIG_FILE)
        
        # 1. جلب الرقم المخزن في الملف، وإذا لم يوجد يبدأ من 1120
        identity_id = config.get("next_id", 1120)
        
        # 2. فحص السيرفر للتأكد من عدم وجود رقم أعلى (لحمايتك إذا انمسح الملف أو تحدث)
        highest_in_guild = 1119
        for m in inter.guild.members:
            if m.display_name and "|" in m.display_name:
                try:
                    parts = m.display_name.split("|")
                    num_part = int(parts[1].strip())
                    if num_part > highest_in_guild:
                        highest_in_guild = num_part
                except:
                    continue
        
        # إذا كان أعلى رقم في السيرفر أكبر أو يساوي الرقم الحالي، نحدث الرقم ليكون التالي مباشرة
        if highest_in_guild >= identity_id:
            identity_id = highest_in_guild + 1

        # حفظ الرقم التالي للمرة القادمة في الملف
        config["next_id"] = identity_id + 1
        save(CONFIG_FILE, config)
        # --------------------------------------------------
        
        new_nick = f"{self.roblox_name} | {identity_id}"
        
        try: await member.edit(nick=new_nick)
        except Exception as e: print(f"⚠️ تعذر تغيير الاسم: {e}")

        for role_id in AUTO_ROLES:
            role = inter.guild.get_role(role_id)
            if role:
                try: await member.add_roles(role)
                except Exception as e: print(f"⚠️ تعذر إعطاء رتبة {role_id}: {e}")

        embed = inter.message.embeds[0]
        embed.title = "✅ تم قبول طلب الهوية وتفعيل الحساب"
        embed.color = 0x00ff00
        embed.add_field(name="⚖️ المسؤول", value=inter.author.mention, inline=True)
        embed.add_field(name="🪪 الهوية الممنوحة", value=f"`{identity_id}`", inline=True)
        await inter.message.edit(embed=embed, view=None)
        
        try:
            reply_embed = disnake.Embed(
                title="🎉 تهانينا تفعيل هويتك!",
                description=f"تم قبول طلب الهوية الخاص بك بنجاح!\n\n**🪪 رقم الهوية:** {identity_id}\n**👤 الاسم الجديد:** {new_nick}",
                color=0x00ff00
            )
            await member.send(embed=reply_embed)
        except: pass

    @disnake.ui.button(label="رفض", style=disnake.ButtonStyle.red, custom_id="id_deny_global")
    async def id_deny(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if not check_admin_permission(inter.author):
            return await inter.response.send_message("❌ الصلاحية لطاقم الإدارة والمسؤولين فقط بمختلف رتبهم!", ephemeral=True)
            
        embed = inter.message.embeds[0]
        embed.title = "❌ تم رفض طلب الهوية"
        embed.color = 0xff0000
        embed.add_field(name="⚖️ المسؤول", value=inter.author.mention, inline=False)
        await inter.message.edit(embed=embed, view=None)
        
        try:
            member = inter.guild.get_member(self.applicant_id)
            if member:
                reply_embed = disnake.Embed(title="👎 تعذر قبول الهوية", description="للأسف، تم رفض طلب الهوية الخاص بك بعد مراجعته من قبل الإدارة.", color=0xff0000)
                await member.send(embed=reply_embed)
        except: pass


class IdentityConfirmView(disnake.ui.View):
    def __init__(self, answers, bot_instance, guild_id):
        super().__init__(timeout=120)
        self.answers = answers
        self.bot = bot_instance
        self.guild_id = guild_id

    @disnake.ui.button(label="قبول التقديم وإرساله", style=disnake.ButtonStyle.green)
    async def confirm_send(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.defer()
        guild = self.bot.get_guild(self.guild_id)
        if not guild: return await inter.followup.send("❌ حدث خطأ في تحديد السيرفر الرئيسي.")
            
        admin_channel = guild.get_channel(IDENTITY_ADMIN_CHANNEL)
        if not admin_channel: return await inter.followup.send("❌ حدث خطأ: روم الإدارة مفقود.")

        embed = disnake.Embed(title="🪪 طلب هوية جديد للتحقق ومراجعته", color=0x3498db)
        embed.add_field(name="👤 صاحب الطلب", value=f"<@{inter.author.id}>", inline=False)
        embed.add_field(name="📝 اسمك:", value=self.answers["name"], inline=True)
        embed.add_field(name="📝 عمرك:", value=self.answers["age"], inline=True)
        embed.add_field(name="📝 حسابك روبلوكس:", value=self.answers["roblox"], inline=True)
        embed.add_field(name="📝 قانون السيرفر:", value=self.answers["rule1"], inline=False)
        embed.add_field(name="📝 قانون الرول:", value=self.answers["rule2"], inline=False)
        embed.add_field(name="📜 الحلف المطلوب:", value=f"```\n{OATH_TEXT_ORIGINAL}\n```", inline=False)
        embed.add_field(name="✍️ كتابة العضو:", value=f"```\n{self.answers['oath']}\n```", inline=False)
        
        if self.answers["image_url"]:
            embed.set_image(url=self.answers["image_url"])

        await admin_channel.send(embed=embed, view=IdentityAdminButtons(inter.author.id, self.answers["roblox"]))
        await inter.followup.send(embed=disnake.Embed(title="✅ تم التقديم", description="تم إرسال طلب هويتك بنجاح.", color=0x00ff00))
        self.stop()

    @disnake.ui.button(label="إلغاء التقديم", style=disnake.ButtonStyle.red)
    async def cancel_send(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message(embed=disnake.Embed(description="❌ تم إلغاء تقديم الطلب.", color=0xff0000), ephemeral=True)
        self.stop()


class IdentityStartConfirmation(disnake.ui.View):
    def __init__(self, bot_instance, guild_id):
        super().__init__(timeout=60)
        self.bot = bot_instance
        self.guild_id = guild_id

    @disnake.ui.button(label="موافق وبدء الأسئلة", style=disnake.ButtonStyle.green)
    async def accept_start(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(view=None)
        try:
            dm = inter.author
            questions = [
                {"title": "1/7 طلب هوية", "desc": "اسمك الكامل الثنائي:"},
                {"title": "2/7 طلب هوية", "desc": "عمرك الحقيقي:"},
                {"title": "3/7 طلب هوية", "desc": "اسم حسابك في روبلوكس (Roblox Username):"},
                {"title": "4/7 طلب هوية", "desc": "اذكر قانوناً أساسياً واحداً من قوانين السيرفر:"},
                {"title": "5/7 طلب هوية", "desc": "اذكر قانوناً واحداً خاصاً بنظام الرولبلاي:"},
                {"title": "6/7 طلب هوية", "desc": f"اكتب الحلف التالي نصاً بيدك وممنوع النسخ واللصق 👈 : ( {OATH_TEXT_ORIGINAL} )"},
                {"title": "📸 إثبات الصورة الشخصية", "desc": "قم برفع لقطة شاشة لحسابك في روبلوكس الآن أو أرسل رابط الصورة الشخصية المباشر:"}
            ]
            
            answers = {}
            keys = ["name", "age", "roblox", "rule1", "rule2", "oath", "image_url"]
            
            def check(m): return m.author.id == inter.author.id and isinstance(m.channel, disnake.DMChannel)

            for i, q in enumerate(questions):
                await dm.send(embed=disnake.Embed(title=q["title"], description=q["desc"], color=0x2b2d31))
                msg = await self.bot.wait_for("message", check=check, timeout=180)
                if i == 6:  
                    answers[keys[i]] = msg.attachments[0].url if msg.attachments else msg.content
                else:
                    answers[keys[i]] = msg.content

            await dm.send(embed=disnake.Embed(title="❓ تأكيد التقديم النهائي", description="هل أنت متأكد من مراجعة إجاباتك وإرسالها للإدارة؟", color=0xe74c3c), view=IdentityConfirmView(answers, self.bot, self.guild_id))
        except Exception as e:
            try: await inter.author.send(embed=disnake.Embed(title="❌ إلغاء التقديم تلقائياً", description="انتهى الوقت المتاح أو تم إغلاق الخاص لديك.", color=0xff0000))
            except: pass
        self.stop()

    @disnake.ui.button(label="إلغاء التقديم", style=disnake.ButtonStyle.red)
    async def deny_start(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=disnake.Embed(description="❌ تم إلغاء التقديم بنجاح.", color=0xff0000), view=None)
        self.stop()


class IdentityPanelButton(disnake.ui.View):
    def __init__(self, bot_instance):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @disnake.ui.button(label="🪪 ابدأ تقديم الهوية الآن", style=disnake.ButtonStyle.blurple, custom_id="start_identity_btn_global")
    async def start_app(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_message("📥 تم بدء العملية بنجاح! تفقد رسائلك الخاصة الآن لتعبئة الهوية الخاصة بك.", ephemeral=True)
        try:
            await inter.author.send(embed=disnake.Embed(title="❓ تأكيد الرغبة في التقديم", description="هل أنت متأكد من رغبتك بالبدء بتقديم طلب هوية جديد في السيرفر؟", color=0x2b2d31), view=IdentityStartConfirmation(self.bot, inter.guild.id))
        except:
            await inter.followup.send("❌ تعذر إرسال الأسئلة إليك، يرجى فتح رسائل الخاص بالسيرفر أولاً (Allow DMs).", ephemeral=True)


# ================= ⚡ تشغيل البوت والـ Views الحية =================

@bot.event
async def on_ready():
    print(f"✅ تم تسجيل الدخول بنجاح باسم البوت: {bot.user}")
    
    try:
        bot.add_view(IdentityPanelButton(bot))
        bot.add_view(IdentityAdminButtons(None, ""))
    except Exception as e:
        print(f"⚠️ خطأ في تحميل الأزرار الدائمة: {e}")
        
    await bot.wait_until_ready()
    
    channel_id_setup = bot.get_channel(IDENTITY_SETUP_CHANNEL)
    if channel_id_setup:
        try:
            embed_id = disnake.Embed(
                title="🪪 نظام الهويات والتصاريح الرسمي لسيرفر Black Line",
                description="مرحباً بك في مركز استخراج الهويات والتصاريح الموحد.\nتقديم الهوية إلزامي لتستطيع بدء اللعب والحصول على الرتب والتفاعل داخل السيرفر ورول بلاي المدينة.",
                color=0x2b2d31
            )
            embed_id.set_footer(text="الأحوال المدنية | BlackLine Roleplay")
            await channel_id_setup.send(embed=embed_id, view=IdentityPanelButton(bot))
            print("📬 تم تحديث بنل تقديم الهويات التلقائي بنجاح!")
        except Exception as e:
            print(f"❌ تعذر إرسال بنل البوت: {e}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# ضع هنا التوكين الخاص بالبوت الجديد ليعمل بشكل سليم
bot.run("MTUxMTk0MjE0OTk1NDk5ODQzNA.G-vZ2s.RUCoTZ7vUTJAHOtF9mSh_qGHROBodHfHPqqYGE")
