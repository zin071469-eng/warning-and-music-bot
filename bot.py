import os
import asyncio
import glob
import threading
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, ContextTypes
import yt_dlp 
ydl_opts = {
    'format': 'bestaudio/best',
    'cookiefile': 'cookies.txt',
}


# ==================== 1. FLASK WEB SERVER (Render Keep-Alive) ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_flask():
    # Render မှ သတ်မှတ်ပေးသော PORT ကို ဖတ်ယူမည် (Default: 8080)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== 2. BOT CONFIGURATION ====================
# Environment Variable မှ ဖတ်မည်၊ မရှိပါက ပေးထားသော Token ကို သုံးမည်
TOKEN = os.environ.get("BOT_TOKEN", "8965629672:AAEQTCrlNGar-6qc3Y5IzycdnmL_GQhIXX4")

# Warning စာရင်းများကို မှတ်သားရန် Dictionary
user_warnings = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 မင်္ဂလာပါ! Warning & Music Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "သီချင်းရှာဖွေရန် /song [သီချင်းနာမည်] ဟု ရိုက်နှိပ်ပါ။\n"
        "အသေးစိတ် Commands များကို ကြည့်ရန် /help ကို နှိပ်ပါ။"
    )
    await update.message.reply_text(welcome_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "👋 မင်္ဂလာပါ! Warning & Music Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "🎵 Music Commands:\n"
        "• /song [သီချင်းနာမည်] - Audio မူရင်းဖိုင် ရှာပြီးပို့ပေးရန်\n\n"
        "⚠️ Admin / Warning Commands:\n"
        "• /warn (Reply လုပ်၍) - အဖွဲ့ဝင်ကို သတိပေးရန်\n"
        "• /resetwarn (Reply လုပ်၍) - Warn အကြိမ် ပြန်ဖျက်ရန်\n"
        "• /warnings - မိမိ သို့မဟုတ် User ၏ Warning စာရင်းကြည့်ရန်\n"
        "• /ban (Reply လုပ်၍) - Group မှ Ban ရန်\n"
        "• /unban (Reply လုပ်၍) - Unban လုပ်ရန်\n"
        "• /mute (Reply လုပ်၍) - Mute လုပ်ရန်\n"
        "• /unmute (Reply လုပ်၍) - Unmute လုပ်ရန်\n"
        "• /all - Group အဖွဲ့ဝင်များကို ခေါ်ရန်\n"
        "• /callone - တစ်ဦးချင်းစီ ခေါ်ရန်"
    )
    await update.message.reply_text(help_text)

async def song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ သီချင်းနာမည် ထည့်ပေးပါ။\nဥပမာ - /song လမင်းသို့")
        return

    msg = await update.message.reply_text(f"🔎 **{query}** ကို ရှာဖွေနေပါသည်။ ခဏစောင့်ပေးပါ...")

        ydl_opts = {  
       'format': 'bestaudio/best',
        'noplaylist': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'retries': 2,
        'fragment_retries': 2,
        'sleep_interval': 3,
        'max_sleep_interval': 6,
        'sleep_requests': 1,
        'cookiefile': 'cookies.txt',
    }

        
    

    }

    file_path = None
    try:
        loop = asyncio.get_event_loop()
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                if 'entries' in info and info['entries']:
                    fp = ydl.prepare_filename(info['entries'][0])
                    fp = os.path.splitext(fp)[0] + ".mp3"
                    return fp, info['entries'][0].get('title', 'Audio')
                return None, None

        file_path, title = await loop.run_in_executor(None, download)

        if file_path and os.path.exists(file_path):
            await msg.edit_text("📤 သီချင်းကို ပို့ပေးနေပါသည်။...")
            with open(file_path, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file, title=title)
            await msg.delete()
        else:
            await msg.edit_text("❌ သီချင်း ရှာမတွေ့ပါခင်ဗျာ။")

    except Exception as e:
        await msg.edit_text("❌ ဒေါင်းလုဒ်ဆွဲစဉ် အမှားအယွင်း ဖြစ်ပေါ်ခဲ့ပါသည်။")
        print(f"Error: {e}")

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"File delete error: {e}")
        
        if os.path.exists("downloads"):
            for temp_file in glob.glob("downloads/*"):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

# ==================== ADMIN & WARNING FUNCTIONS ====================

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Warning ပေးလိုသော Message ကို Reply လုပ်၍ သုံးပါ။")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    user_key = (chat_id, user.id)

    user_warnings[user_key] = user_warnings.get(user_key, 0) + 1
    count = user_warnings[user_key]

    await update.message.reply_text(f"⚠️ {user.mention_html()} ကို သတိပေးလိုက်ပါပြီ။\nယခု Warning အကြိမ်အရေအတွက်: {count}/3", parse_mode="HTML")

    if count >= 3:
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
            await update.message.reply_text(f"🚫 {user.mention_html()} သည် Warning ၃ ကြိမ် ပြည့်သွားသဖြင့် Group မှ Ban လိုက်ပါပြီ။", parse_mode="HTML")
            user_warnings[user_key] = 0
        except Exception as e:
            await update.message.reply_text(f"❌ Ban ရန် မအောင်မြင်ပါ: {e}")

async def resetwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Warn ပြန်ဖျက်လိုသော Message ကို Reply လုပ်၍ သုံးပါ။")
        return

    user = update.message.reply_to_message.from_user
    chat_id = update.effective_chat.id
    user_key = (chat_id, user.id)

    user_warnings[user_key] = 0
    await update.message.reply_text(f"✅ {user.mention_html()} ၏ Warning အကြိမ်အရေအတွက်ကို ပြန်လည် ဖျက်ပေးလိုက်ပါပြီ။", parse_mode="HTML")

async def warnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
    else:
        user = update.effective_user

    chat_id = update.effective_chat.id
    count = user_warnings.get((chat_id, user.id), 0)
    await update.message.reply_text(f"📊 {user.mention_html()} ၏ လက်ရှိ Warning အကြိမ်အရေအတွက်: {count}/3", parse_mode="HTML")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Ban လိုသော Message ကို Reply လုပ်၍ သုံးပါ။")
        return

    user = update.message.reply_to_message.from_user
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🚫 {user.mention_html()} ကို Group မှ Ban လိုက်ပါပြီ။", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Ban ရန် မအောင်မြင်ပါ: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Unban လိုသော Message ကို Reply လုပ်၍ သုံးပါ။")
        return

    user = update.message.reply_to_message.from_user
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ {user.mention_html()} ကို Unban လုပ်ပေးလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Unban ရန် မအောင်မြင်ပါ: {e}")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Mute လိုသော Message ကို Reply လုပ်၍ သုံးပါ။")
        return

    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"🔇 {user.mention_html()} ကို Mute လုပ်လိုက်ပါပြီ။", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Mute ရန် မအောင်မြင်ပါ: {e}")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Unmute လိုသော Message ကို Reply လုပ်၍ သုံးပါ။")
        return

    user = update.message.reply_to_message.from_user
    try:
        # 🟢 ပြင်ဆင်ထားသော အပိုင်း: python-telegram-bot v20+ အတွက် သဟဇာတဖြစ်သော ChatPermissions
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 {user.mention_html()} ကို Unmute လုပ်ပေးလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Unmute ရန် မအောင်မြင်ပါ: {e}")

async def call_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 Group အဖွဲ့ဝင်များအားလုံးကို ခေါ်ယူနေပါသည်။")

async def call_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await update.message.reply_text(f"🔔 {user.mention_html()} ခေါ်နေပါတယ်ခင်ဗျာ။", parse_mode="HTML")
    else:
        await update.message.reply_text("❌ ခေါ်လိုသော User ၏ Message ကို Reply လုပ်၍ သုံးပါ။")

# ==================== MAIN EXECUTION ====================

def main():
    # 🟢 1. Flask Web Server ကို Thread သီးသန့်ဖြင့် နောက်ကွယ်တွင် Run မည်
    threading.Thread(target=run_flask, daemon=True).start()

    # 🟢 2. Telegram Bot ကို စတင်မည်
    app = Application.builder().token(TOKEN).build()

    # Commands Handlers များ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("song", song))
    
    # Admin & Warning Command Handlers
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("resetwarn", resetwarn))
    app.add_handler(CommandHandler("warnings", warnings))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("all", call_all))
    app.add_handler(CommandHandler("callone", call_one))

    print("Bot & Web Server are running...")
    app.run_polling()

if __name__ == "__main__":
    main()
