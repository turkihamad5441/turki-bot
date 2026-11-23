import telebot
import time
import os
import sqlite3
import yt_dlp
import uuid
import threading
import random
import requests
import urllib.parse
from datetime import datetime
from telebot import types
from flask import Flask
from threading import Thread

# ==========================================
# ⚙️ [1] الإعدادات الأساسية
# ==========================================
TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('ADMIN_ID', 0)) 
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'turkidownloads_bot')
DOWNLOAD_DIR = 'downloads'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==========================================
# 🗄️ [2] قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('turki_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, coins INTEGER, vip_expiry REAL, 
                 role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price', '5')")
    conn.commit(); conn.close()

def get_user(user_id):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone(); conn.close()
    return user

def add_user(user_id, username, role='user'):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, coins, role) VALUES (?, ?, 30, ?)", (user_id, username, role))
    conn.commit(); conn.close()

def update_user(user_id, field, value):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit(); conn.close()

def get_all_users():
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = c.fetchall(); conn.close()
    return [u[0] for u in users]

def get_price():
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'price'")
    price = c.fetchone()[0]; conn.close()
    return int(price)

def set_price(new_price):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("UPDATE settings SET value = ? WHERE key = 'price'", (new_price,))
    conn.commit(); conn.close()

init_db()

# ==========================================
# 🧠 [3] الذكاء الاصطناعي والتنزيل
# ==========================================
def get_ai_reply(prompt):
    try:
        url = "https://text.pollinations.ai/"
        payload = {"messages": [{"role": "user", "content": prompt}], "model": "openai"}
        res = requests.post(url, json=payload, timeout=20)
        return res.text if res.status_code == 200 else "عذراً، الذكاء الاصطناعي غير متاح حالياً."
    except: return "عذراً، حدث خطأ."

def download_media(url, action):
    file_id = str(uuid.uuid4())
    out = f"{DOWNLOAD_DIR}/{file_id}.%(ext)s"
    ydl_opts = {'outtmpl': out, 'quiet': True, 'nocheckcertificate': True, 'noplaylist': True}
    
    if action == 'dl_vid': ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else: ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if action == 'dl_aud': file_path = os.path.splitext(file_path)[0] + '.mp3'
        return file_path if os.path.exists(file_path) else None
    except: return None

# ==========================================
# 🎛️ [4] الأزرار
# ==========================================
def main_menu(uid, is_owner):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 حسابي", callback_data="menu_profile"),
        types.InlineKeyboardButton("💎 اشتراك VIP", callback_data="menu_vip")
    )
    markup.add(
        types.InlineKeyboardButton("🤖 ذكاء اصطناعي", callback_data="menu_ai"),
        types.InlineKeyboardButton("🎨 رسم بالذكاء", callback_data="menu_image")
    )
    if is_owner:
        markup.add(types.InlineKeyboardButton("👑 لوحة المالك", callback_data="menu_owner"))
    return markup

def download_menu(url):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎬 فيديو", callback_data=f"dl_vid|{url}"),
        types.InlineKeyboardButton("🎵 صوت", callback_data=f"dl_aud|{url}")
    )
    return markup

# ==========================================
# 🚀 [5] الترحيب
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    user = get_user(uid)
    if not user:
        add_user(uid, message.from_user.first_name, 'owner' if uid == OWNER_ID else 'user')
        user = get_user(uid)
    
    text = (
        f"<b>🌟 أهلاً بك يا {message.from_user.first_name} في بوت تركي!</b>\n\n"
        f"<blockquote>🧠 أرسل رابط للتنزيل، أو اكتب أي سؤال وسأجيبك بالذكاء الاصطناعي.\n"
        f"💰 رصيدك: <code>{user[2]}</code> كوينز</blockquote>\n\n"
        f"👇 <i>اختر من القائمة:</i>"
    )
    bot.send_message(uid, text, reply_markup=main_menu(uid, uid == OWNER_ID), parse_mode='HTML')

# ==========================================
# 🧭 [6] موجّه الأوامر (Command Router)
# ==========================================
@bot.message_handler(func=lambda message: message.text and message.text.startswith('/'))
def command_router(message):
    uid = message.from_user.id
    cmd = message.text.split()[0].lower()
    
    # 50 أمر للمستخدم (أمثلة، تقدر تضيف المزيد)
    user_cmds = {
        '/help': "دليل البوت: أرسل رابط، أو اسأل الذكاء الاصطناعي.",
        '/profile': f"الآيدي: {uid}\nالرصيد: {get_user(uid)[2]} كوينز",
        '/ping': "البوت شغال 🟢",
        '/time': f"الوقت: {datetime.now().strftime('%H:%M')}",
        '/date': f"التاريخ: {datetime.now().strftime('%Y-%m-%d')}",
        '/id': f"آيديك: {uid}",
        '/support': "الدعم: @YourSupport",
    }

    # 100 أمر للأدمن (أمثلة)
    admin_cmds = {
        '/admin': "لوحة الإدارة.",
        '/stats': f"المستخدمين: {len(get_all_users())}",
        '/broadcast': "استخدم: /broadcast رسالتك",
        '/setprice': "استخدم: /setprice 10",
    }

    # 20 أمر للقروبات (أمثلة)
    group_cmds = {
        '/rules': "القوانين: ممنوع السبام.",
        '/kick': "طرد العضو.",
    }

    if uid == OWNER_ID and cmd in admin_cmds:
        bot.reply_to(message, f"👑 <b>{admin_cmds[cmd]}</b>", parse_mode='HTML')
    elif cmd in user_cmds:
        bot.reply_to(message, f"👤 <b>{user_cmds[cmd]}</b>", parse_mode='HTML')
    elif message.chat.type in ['group', 'supergroup'] and cmd in group_cmds:
        bot.reply_to(message, f"🛡️ <b>{group_cmds[cmd]}</b>", parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ أمر غير معروف، اكتب /help.")

# ==========================================
# 🔘 [7] الأزرار والذكاء الاصطناعي والتنزيل
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    if call.data == "menu_profile":
        user = get_user(uid)
        text = f"<b>👤 حسابك:</b>\n💰 الرصيد: <code>{user[2]}</code> كوينز"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid, uid == OWNER_ID), parse_mode='HTML')
        
    elif call.data == "menu_ai":
        bot.edit_message_text("<b>🤖 أرسل أي سؤال الآن وسأجيبك:</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data == "menu_owner":
        if uid != OWNER_ID: return
        bot.edit_message_text("<b>👑 لوحة المالك:</b>\n/stats\n/broadcast\n/setprice", call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('dl_'):
        action, url = call.data.split('|', 1)
        bot.edit_message_text("⏳ <b>جاري التنزيل بأقصى سرعة...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        file_path = download_media(url, action)
        if file_path:
            if os.path.getsize(file_path) > 50*1024*1024:
                bot.edit_message_text("❌ الملف أكبر من 50 ميجا.", call.message.chat.id, call.message.message_id)
            else:
                with open(file_path, 'rb') as f:
                    if action == 'dl_vid': bot.send_video(call.message.chat.id, f)
                    else: bot.send_audio(call.message.chat.id, f)
                bot.delete_message(call.message.chat.id, call.message.message_id)
            try: os.remove(file_path) # حذف فوري
            except: pass
        else:
            bot.edit_message_text("❌ خطأ في التنزيل.", call.message.chat.id, call.message.message_id, parse_mode='HTML')

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    if message.text.startswith('/'): return # الراوتر تكفل بالأوامر
    
    # الروابط
    if message.text.startswith('http'):
        user = get_user(uid)
        price = get_price()
        if user[2] < price: return bot.reply_to(message, f"❌ تحتاج {price} كوينز.")
        
        update_user(uid, 'coins', user[2] - price)
        bot.reply_to(message, "<b>✅ اختر الصيغة:</b>", reply_markup=download_menu(message.text), parse_mode='HTML')
    
    # الذكاء الاصطناعي التلقائي
    else:
        msg = bot.reply_to(message, "🤔 <i>جاري التفكير...</i>", parse_mode='HTML')
        bot.edit_message_text(get_ai_reply(message.text), message.chat.id, msg.message_id, parse_mode='HTML')

# ==========================================
# 🌐 [8] التشغيل
# ==========================================
@app.route('/')
def home(): return "Bot is Running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

keep_alive()
print("Bot V17 is Running...")
bot.infinity_polling()
