import os
import telebot
import yt_dlp
import uuid
import time
import datetime
import sqlite3
import threading
import random
import string
import qrcode
import requests
import io
from PIL import Image
from flask import Flask
from telebot import types
from gtts import gTTS

# ==========================================
# ⚙️ [1] الإعدادات الأساسية
# ==========================================
TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('ADMIN_ID', 0)) 
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'TurkiBot')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==========================================
# 🗄️ [2] قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('turki_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, coins INTEGER, vip_expiry REAL, 
                 daily_downloads INTEGER, last_download_date TEXT, last_action_time REAL, 
                 last_bonus_date TEXT, ref_by INTEGER, streak INTEGER, last_streak_date TEXT,
                 role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0, warnings INTEGER DEFAULT 0, xp INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cost', '5')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('limit', '10')")
    conn.commit(); conn.close()
init_db()

def get_setting(key, default):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = c.fetchone(); conn.close()
    return int(res[0]) if res else default

# ==========================================
# 🛡️ [3] الصلاحيات والحماية
# ==========================================
def is_owner(user_id): return user_id == OWNER_ID
def is_mod(user_id):
    if is_owner(user_id): return True
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone(); conn.close()
    return res and res[0] == 'mod'

def check_ban(user_id):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone(); conn.close()
    return res and res[0] == 1

# ==========================================
# 🧹 [4] التنظيف التلقائي
# ==========================================
def cleanup_system():
    while True:
        time.sleep(3600)
        now = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < now - 600:
                try: os.remove(file_path)
                except: pass

# ==========================================
# 🎛️ [5] القوائم
# ==========================================
def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 حسابي", callback_data="menu_profile"),
        types.InlineKeyboardButton("👑 VIP", callback_data="menu_vip")
    )
    markup.add(
        types.InlineKeyboardButton("🔍 بحث أغنية", callback_data="menu_search"),
        types.InlineKeyboardButton("🗣️ نص لصوت", callback_data="menu_tts")
    )
    markup.add(
        types.InlineKeyboardButton("🛠️ أدوات إضافية", callback_data="menu_tools"),
        types.InlineKeyboardButton("🎁 مكافأة", callback_data="menu_bonus")
    )
    if is_mod(user_id): markup.add(types.InlineKeyboardButton("🛡️ المشرفين", callback_data="menu_mod"))
    if is_owner(user_id): markup.add(types.InlineKeyboardButton("👑 المالك", callback_data="menu_owner"))
    return markup

def tools_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 صناعة ستيكر", callback_data="tool_sticker"),
        types.InlineKeyboardButton("🔗 اختصار رابط", callback_data="tool_short")
    )
    markup.add(
        types.InlineKeyboardButton("📸 باركود", callback_data="tool_qr"),
        types.InlineKeyboardButton("🔑 كلمة مرور", callback_data="tool_pass")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    return markup

# ==========================================
# 🚀 [6] الترحيب
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if check_ban(user_id): return
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user:
        role = 'owner' if user_id == OWNER_ID else 'user'
        c.execute("INSERT INTO users (user_id, username, coins, vip_expiry, daily_downloads, last_download_date, last_action_time, last_bonus_date, streak, last_streak_date, role) VALUES (?, ?, 30, 0, 0, '', 0, '0', 0, '0', ?)",
                  (user_id, message.from_user.first_name, role))
        conn.commit()
        text = f"🌟 <b>أهلاً {message.from_user.first_name}!</b>\n🎁 +30 كوينز هدية."
    else:
        text = f"👋 <b>أهلاً {message.from_user.first_name}!</b>\n💰 رصيدك: <code>{user[2]}</code>"
    conn.close()
    bot.send_message(message.chat.id, text, reply_markup=main_menu(user_id), parse_mode='HTML')

# ==========================================
# 🔘 [7] أزرار المستخدمين
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('menu_') and 'mod' not in call.data and 'owner' not in call.data)
def user_menus(call):
    uid = call.from_user.id
    if call.data == "menu_tools":
        bot.edit_message_text("🛠️ <b>أدوات إضافية:</b>", call.message.chat.id, call.message.message_id, reply_markup=tools_menu(), parse_mode='HTML')
    elif call.data == "menu_profile":
        conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
        c.execute("SELECT coins, vip_expiry, daily_downloads FROM users WHERE user_id = ?", (uid,))
        coins, vip, dl = c.fetchone(); conn.close()
        vip_stat = f"✅ باقي {int((vip - time.time())/86400)} يوم" if vip > time.time() else "❌"
        text = f"👤 <b>ملفي:</b>\n💰 الرصيد: <code>{coins}</code>\n👑 VIP: {vip_stat}\n📥 تنزيلات اليوم: <code>{dl}</code>"
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')
    elif call.data == "menu_search":
        msg = bot.send_message(call.message.chat.id, "🔍 أرسل اسم الأغنية:")
        bot.register_next_step_handler(msg, process_search)
    elif call.data == "menu_tts":
        msg = bot.send_message(call.message.chat.id, "🗣️ أرسل النص:")
        bot.register_next_step_handler(msg, process_tts)
    elif call.data == "menu_bonus":
        today = str(datetime.date.today())
        conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
        c.execute("SELECT last_streak_date, streak FROM users WHERE user_id = ?", (uid,))
        last_streak, streak = c.fetchone()
        if last_streak == today: bot.answer_callback_query(call.id, "⚠️ أخذت مكافأتك اليوم!", show_alert=True)
        else:
            streak = streak + 1 if last_streak == str(datetime.date.today() - datetime.timedelta(days=1)) else 1
            bonus = 15 + (streak * 5)
            c.execute("UPDATE users SET coins = coins + ?, last_streak_date = ?, streak = ? WHERE user_id = ?", (bonus, today, streak, uid))
            conn.commit(); bot.answer_callback_query(call.id, f"🔥 اليوم {streak}!\n+{bonus} كوينز", show_alert=True)
        conn.close()
    elif call.data == "back_home":
        bot.edit_message_text("🏠 القائمة:", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid), parse_mode='HTML')

# ==========================================
# 🛠️ [8] الأدوات الجديدة (ستيكر، رابط، باركود)
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('tool_'))
def tools_handler(call):
    if call.data == "tool_sticker":
        msg = bot.send_message(call.message.chat.id, "🎨 أرسل صورة لتحويلها إلى ستيكر:")
        bot.register_next_step_handler(msg, process_sticker)
    elif call.data == "tool_short":
        msg = bot.send_message(call.message.chat.id, "🔗 أرسل الرابط الطويل لاختصاره:")
        bot.register_next_step_handler(msg, process_short)
    elif call.data == "tool_qr":
        msg = bot.send_message(call.message.chat.id, "📸 أرسل النص أو الرابط لعمل باركود:")
        bot.register_next_step_handler(msg, process_qr)
    elif call.data == "tool_pass":
        pwd = ''.join(random.choices(string.ascii_letters + string.digits + "!@#$%^&*", k=16))
        bot.send_message(call.message.chat.id, f"🔑 كلمة مرور قوية:\n<code>{pwd}</code>", parse_mode='HTML')

def process_sticker(message):
    if not message.photo:
        return bot.reply_to(message, "❌ الرجاء إرسال صورة.")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded_file))
        img.thumbnail((512, 512)) # تصغير الحجم ليناسب الستيكر
        path = os.path.join(DOWNLOAD_DIR, f"sticker_{uuid.uuid4()}.webp")
        img.save(path, format="WEBP")
        with open(path, 'rb') as f:
            bot.send_sticker(message.chat.id, f)
        os.remove(path)
    except Exception as e:
        bot.reply_to(message, "❌ حدث خطأ أثناء صناعة الستيكر.")

def process_short(message):
    try:
        url = message.text
        if not url.startswith('http'):
            return bot.reply_to(message, "❌ أرسل رابط صحيح يبدأ بـ http")
        res = requests.get(f"https://is.gd/create.php?format=simple&url={url}")
        if res.status_code == 200:
            bot.reply_to(message, f"🔗 <b>رابطك المختصر:</b>\n<code>{res.text}</code>", parse_mode='HTML')
        else:
            bot.reply_to(message, "❌ فشل في اختصار الرابط.")
    except:
        bot.reply_to(message, "❌ حدث خطأ.")

def process_qr(message):
    try:
        img = qrcode.make(message.text)
        path = os.path.join(DOWNLOAD_DIR, f"qr_{uuid.uuid4()}.png")
        img.save(path)
        with open(path, 'rb') as f: bot.send_photo(message.chat.id, f)
        os.remove(path)
    except: bot.reply_to(message, "❌ خطأ.")

def process_search(message):
    msg = bot.reply_to(message, "🔍 جاري البحث...")
    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s', 'quiet': True, 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]}) as ydl:
            info = ydl.extract_info(f"ytsearch1:{message.text}", download=True)['entries'][0]
            file = f"{DOWNLOAD_DIR}/{info['id']}.mp3"
        with open(file, 'rb') as f: bot.send_audio(message.chat.id, f, caption=f"🎵 {info['title']}")
        os.remove(file); bot.delete_message(message.chat.id, msg.message_id)
    except: bot.edit_message_text("❌ لم أجد الأغنية.", message.chat.id, msg.message_id)

def process_tts(message):
    msg = bot.reply_to(message, "🗣️ جاري التحويل...")
    try:
        file = f"{DOWNLOAD_DIR}/{uuid.uuid4()}.mp3"
        gTTS(text=message.text, lang='ar').save(file)
        with open(file, 'rb') as f: bot.send_voice(message.chat.id, f)
        os.remove(file); bot.delete_message(message.chat.id, msg.message_id)
    except: bot.edit_message_text("❌ النص طويل أو خطأ.", message.chat.id, msg.message_id)

# ==========================================
# 📥 [9] التنزيل
# ==========================================
@bot.message_handler(func=lambda message: message.text and message.text.startswith('http') and not message.text.startswith('http://is.gd'))
def handle_link(message):
    uid = message.from_user.id
    if check_ban(uid): return
    
    COST = get_setting('cost', 5)
    LIMIT = get_setting('limit', 10)

    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT coins, vip_expiry, daily_downloads, last_download_date, last_action_time FROM users WHERE user_id = ?", (uid,))
    coins, vip, dl, last_date, last_act = c.fetchone()
    
    if time.time() - last_act < 10: return bot.reply_to(message, "⚠️ انتظر 10 ثواني.")
    if last_date != str(datetime.date.today()): dl = 0
    
    if dl >= (100 if vip > time.time() else LIMIT): return bot.reply_to(message, "🚫 وصلت الحد اليومي.")
    if vip < time.time() and coins < COST: return bot.reply_to(message, "❌ رصيدك لا يكفي.")

    if vip < time.time(): c.execute("UPDATE users SET coins = coins - ?, daily_downloads = ?, last_download_date = ?, last_action_time = ? WHERE user_id = ?", (COST, dl+1, str(datetime.date.today()), time.time(), uid))
    else: c.execute("UPDATE users SET daily_downloads = ?, last_download_date = ?, last_action_time = ? WHERE user_id = ?", (dl+1, str(datetime.date.today()), time.time(), uid))
    conn.commit(); conn.close()

    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🎬 فيديو", callback_data=f"dl_vid|{message.text}"), types.InlineKeyboardButton("🎵 صوت", callback_data=f"dl_aud|{message.text}"))
    bot.reply_to(message, "✅ اختر الصيغة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def process_download(call):
    action, url = call.data.split('|', 1)
    bot.edit_message_text("⏳ جاري التنزيل...", call.message.chat.id, call.message.message_id)
    out = f"{DOWNLOAD_DIR}/{uuid.uuid4()}.%(ext)s"
    ydl_opts = {'outtmpl': out, 'quiet': True, 'nocheckcertificate': True}
    if action == 'dl_vid': ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
    else: ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]})
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True); file = ydl.prepare_filename(info)
            if action == 'dl_aud': file = os.path.splitext(file)[0] + '.mp3'
        if os.path.getsize(file) > 50*1024*1024: bot.edit_message_text("❌ الملف أكبر من 50 ميجا.", call.message.chat.id, call.message.message_id)
        else:
            with open(file, 'rb') as f:
                if action == 'dl_vid': bot.send_video(call.message.chat.id, f)
                else: bot.send_audio(call.message.chat.id, f)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        os.remove(file)
    except: bot.edit_message_text("❌ خطأ في التنزيل.", call.message.chat.id, call.message.message_id)

# ==========================================
# 👑 [10] أوامر الإدارة (للمالك والمشرفين)
# ==========================================
@bot.message_handler(commands=['setcost', 'setlimit'])
def owner_settings(message):
    if not is_owner(message.from_user.id): return
    try:
        val = message.text.split()[1]
        conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
        if message.text.startswith('/setcost'):
            c.execute("UPDATE settings SET value = ? WHERE key = 'cost'", (val,)); bot.reply_to(message, f"✅ سعر التنزيل صار {val} كوينز.")
        else:
            c.execute("UPDATE settings SET value = ? WHERE key = 'limit'", (val,)); bot.reply_to(message, f"✅ الحد اليومي صار {val} فيديو.")
        conn.commit(); conn.close()
    except: bot.reply_to(message, "⚠️ استخدم: /setcost 5 أو /setlimit 10")

# ==========================================
# 🌐 [11] التشغيل
# ==========================================
@app.route('/')
def home(): return "Turki Bot V8 is Running!"

def run_bot(): bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=cleanup_system, daemon=True).start()
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
