import telebot
import time
import os
import sqlite3
import yt_dlp
import uuid
import threading
import requests
from datetime import datetime
from telebot import types
from flask import Flask
from threading import Thread

# ==========================================
# ⚙️ [1] الإعدادات الأساسية
# ==========================================
TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('ADMIN_ID', 0)) 
DOWNLOAD_DIR = 'downloads'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==========================================
# 🏆 [2] نظام الرتب والامتيازات (30 رتبة)
# ==========================================
RANKS = {
    "owner": {"name": "المالك والمؤسس 🌟", "reward": 10000},
    "visitor": {"name": "زائر 👤", "reward": 50},
    "newcomer": {"name": "عضو جديد ☕", "reward": 35},
    "ambitious": {"name": "مبتدئ طموح 🌱", "reward": 40},
    "explorer": {"name": "مستكشف البوت 🧭", "reward": 45},
    "citizen": {"name": "مواطن رقمي 🏙️", "reward": 50},
    "special": {"name": "عضو مميز ⭐", "reward": 51},
    "contributor": {"name": "عضو متفاعل 🤝", "reward": 52},
    "active": {"name": "مستخدم نشط 🥈", "reward": 55},
    "super_active": {"name": "مستخدم نشط جداً 🚀", "reward": 60},
    "pro": {"name": "عضو محترف 🥇", "reward": 65},
    "expert": {"name": "خبير متميز 💎", "reward": 70},
    "legend": {"name": "أسطورة البوت 👑", "reward": 80},
    "mod": {"name": "مشرف 🛡️", "reward": 180},
    "admin": {"name": "مدير عام البوت 🛡️", "reward": 2000},
}

# ==========================================
# 🗄️ [3] قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('turki_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, tokens INTEGER, rank TEXT DEFAULT 'visitor')''')
    conn.commit(); conn.close()

def get_user(user_id):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone(); conn.close()
    return user

def add_user(user_id, username, rank='visitor'):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    reward = RANKS.get(rank, {}).get("reward", 50)
    c.execute("INSERT OR IGNORE INTO users (user_id, username, tokens, rank) VALUES (?, ?, ?, ?)", (user_id, username, reward, rank))
    conn.commit(); conn.close()

def update_user(user_id, field, value):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit(); conn.close()

init_db()

# ==========================================
# 🧠 [4] الذكاء الاصطناعي والتنزيل
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
# 🎛️ [5] الأزرار والأقسام (الهيكل الأساسي للـ 500 ميزة)
# ==========================================
def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # الأقسام العشرة
    markup.add(
        types.InlineKeyboardButton("👤 الحساب والأمان", callback_data="sec_account"),
        types.InlineKeyboardButton("🎬 التحميل الشامل", callback_data="sec_download")
    )
    markup.add(
        types.InlineKeyboardButton("🧠 الذكاء الاصطناعي", callback_data="sec_ai"),
        types.InlineKeyboardButton("🎨 استوديو التصميم", callback_data="sec_design")
    )
    markup.add(
        types.InlineKeyboardButton("🕌 القسم الإسلامي", callback_data="sec_islamic"),
        types.InlineKeyboardButton("🎮 الألعاب والتحديات", callback_data="sec_games")
    )
    markup.add(
        types.InlineKeyboardButton("💻 أدوات المطورين", callback_data="sec_dev"),
        types.InlineKeyboardButton("💰 الرصيد والشحن", callback_data="sec_wallet")
    )
    markup.add(
        types.InlineKeyboardButton("⏱️ الإنتاجية واليوميات", callback_data="sec_productivity")
    )
    
    # زر الإدارة للمالك فقط
    if user_id == OWNER_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة الإدارة (المالك)", callback_data="sec_admin"))
        
    return markup

def back_btn():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home"))
    return markup

# ==========================================
# 🚀 [6] الترحيب
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if not user:
        rank = 'owner' if uid == OWNER_ID else 'visitor'
        add_user(uid, message.from_user.first_name, rank)
        user = get_user(uid)
    
    rank_name = RANKS.get(user[3], {}).get("name", "زائر 👤")
    
    text = (
        f"<b>🌟 أهلاً بك يا {message.from_user.first_name}!</b>\n\n"
        f"<blockquote>👑 <b>رتبتك الحالية:</b> {rank_name}\n"
        f"🪙 <b>توكن تركي:</b> <code>{user[2]}</code></blockquote>\n\n"
        f"<i>البوت يحتوي على 10 أقسام رئيسية و 500 ميزة خدمية.</i>\n"
        f"👇 <b>اختر القسم الذي تريد دخوله:</b>"
    )
    bot.send_message(uid, text, reply_markup=main_menu(uid), parse_mode='HTML')

# ==========================================
# 🧭 [7] موجّه الأقسام (Routing)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    if call.data == "back_home":
        bot.edit_message_text("<b>🏠 القائمة الرئيسية:</b>\nاختر القسم:", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid), parse_mode='HTML')
    
    # --- الأقسام ---
    elif call.data == "sec_account":
        text = "<b>👤 قسم الحسابات والأمان (50 ميزة):</b>\n\n- عرض الملف الشخصي\n- تغيير الرتبة\n- الأمان (2FA)\n- سجل النشاطات\n\n<i>(يتم برمجة باقي الميزات هنا)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_download":
        text = "<b>🎬 قسم التحميل الشامل (50 ميزة):</b>\n\n- تيك توك بدون علامة مائية\n- يوتيوب (فيديو/صوت)\n- انستقرام وتويتر\n- تحويل الصيغ\n\n<i>(أرسل أي رابط للبدء فوراً)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_ai":
        text = "<b>🧠 قسم الذكاء الاصطناعي (50 ميزة):</b>\n\n- محادثة ذكية\n- تلخيص النصوص\n- كتابة الأكواد\n- ترجمة فورية\n\n<i>(اكتب أي سؤال ليتم الرد فوراً)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_design":
        text = "<b>🎨 قسم التصميم (50 ميزة):</b>\n\n- توليد الصور بالذكاء\n- إزالة الخلفية\n- صناعة الشعارات\n\n<i>(جاري تفعيل باقي الأدوات)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_islamic":
        text = "<b>🕌 القسم الإسلامي (50 ميزة):</b>\n\n- مواقيت الصلاة\n- أذكار الصباح والمساء\n- القرآن الكريم\n- التقويم الهجري"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_games":
        text = "<b>🎮 قسم الألعاب (50 ميزة):</b>\n\n- لوحة المتصدرين\n- الألغاز\n- سحب الكوينز"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_dev":
        text = "<b>💻 أدوات المطورين (50 ميزة):</b>\n\n- اختصار الروابط\n- توليد كلمات مرور\n- توليد QR Code"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_wallet":
        user = get_user(uid)
        text = f"<b>💰 محفظة توكن تركي:</b>\n\nرصيدك: <code>{user[2]}</code> توكن.\n\n- شحن الرصيد\n- تحويل للأصدقاء\n- سجل الحركات"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_productivity":
        text = "<b>⏱️ أدوات الإنتاجية (50 ميزة):</b>\n\n- المنبهات\n- الملاحظات\n- قوائم المهام\n- حاسبة العمر"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_admin":
        if uid != OWNER_ID: return
        text = "<b>👑 لوحة الإدارة الشاملة (50 ميزة):</b>\n\n- الإحصائيات\n- الإذاعة\n- إدارة الكوينز والرتب\n- تفعيل الصيانة"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    # --- التنزيل الفعلي ---
    elif call.data.startswith('dl_'):
        action, url = call.data.split('|', 1)
        bot.edit_message_text("⏳ <b>جاري التحميل...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        file_path = download_media(url, action)
        if file_path:
            if os.path.getsize(file_path) > 50*1024*1024:
                bot.edit_message_text("❌ الملف أكبر من 50 ميجا.", call.message.chat.id, call.message.message_id)
            else:
                with open(file_path, 'rb') as f:
                    if action == 'dl_vid': bot.send_video(call.message.chat.id, f)
                    else: bot.send_audio(call.message.chat.id, f)
                bot.delete_message(call.message.chat.id, call.message.message_id)
            try: os.remove(file_path)
            except: pass
        else:
            bot.edit_message_text("❌ خطأ في التحميل.", call.message.chat.id, call.message.message_id, parse_mode='HTML')

# ==========================================
# 🧠 [8] المعالجة التلقائية (AI و الروابط)
# ==========================================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    
    if message.text.startswith('/'): return 
    
    # الروابط
    if message.text.startswith('http'):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🎬 فيديو", callback_data=f"dl_vid|{message.text}"),
            types.InlineKeyboardButton("🎵 صوت", callback_data=f"dl_aud|{message.text}")
        )
        bot.reply_to(message, "<b>✅ تم استلام الرابط. اختر الصيغة:</b>", reply_markup=markup, parse_mode='HTML')
    
    # الذكاء الاصطناعي
    else:
        msg = bot.reply_to(message, "🤔 <i>جاري التفكير...</i>", parse_mode='HTML')
        bot.edit_message_text(get_ai_reply(message.text), message.chat.id, msg.message_id, parse_mode='HTML')

# ==========================================
# 🌐 [9] التشغيل
# ==========================================
@app.route('/')
def home(): return "Bot V18 - 10 Sections Architecture is Running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

keep_alive()
print("Bot V18 is Running...")
bot.infinity_polling()import telebot
import time
import os
import sqlite3
import yt_dlp
import uuid
import threading
import requests
from datetime import datetime
from telebot import types
from flask import Flask
from threading import Thread

# ==========================================
# ⚙️ [1] الإعدادات الأساسية
# ==========================================
TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('ADMIN_ID', 0)) 
DOWNLOAD_DIR = 'downloads'

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==========================================
# 🏆 [2] نظام الرتب والامتيازات (30 رتبة)
# ==========================================
RANKS = {
    "owner": {"name": "المالك والمؤسس 🌟", "reward": 10000},
    "visitor": {"name": "زائر 👤", "reward": 50},
    "newcomer": {"name": "عضو جديد ☕", "reward": 35},
    "ambitious": {"name": "مبتدئ طموح 🌱", "reward": 40},
    "explorer": {"name": "مستكشف البوت 🧭", "reward": 45},
    "citizen": {"name": "مواطن رقمي 🏙️", "reward": 50},
    "special": {"name": "عضو مميز ⭐", "reward": 51},
    "contributor": {"name": "عضو متفاعل 🤝", "reward": 52},
    "active": {"name": "مستخدم نشط 🥈", "reward": 55},
    "super_active": {"name": "مستخدم نشط جداً 🚀", "reward": 60},
    "pro": {"name": "عضو محترف 🥇", "reward": 65},
    "expert": {"name": "خبير متميز 💎", "reward": 70},
    "legend": {"name": "أسطورة البوت 👑", "reward": 80},
    "mod": {"name": "مشرف 🛡️", "reward": 180},
    "admin": {"name": "مدير عام البوت 🛡️", "reward": 2000},
}

# ==========================================
# 🗄️ [3] قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect('turki_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, tokens INTEGER, rank TEXT DEFAULT 'visitor')''')
    conn.commit(); conn.close()

def get_user(user_id):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone(); conn.close()
    return user

def add_user(user_id, username, rank='visitor'):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    reward = RANKS.get(rank, {}).get("reward", 50)
    c.execute("INSERT OR IGNORE INTO users (user_id, username, tokens, rank) VALUES (?, ?, ?, ?)", (user_id, username, reward, rank))
    conn.commit(); conn.close()

def update_user(user_id, field, value):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit(); conn.close()

init_db()

# ==========================================
# 🧠 [4] الذكاء الاصطناعي والتنزيل
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
# 🎛️ [5] الأزرار والأقسام (الهيكل الأساسي للـ 500 ميزة)
# ==========================================
def main_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # الأقسام العشرة
    markup.add(
        types.InlineKeyboardButton("👤 الحساب والأمان", callback_data="sec_account"),
        types.InlineKeyboardButton("🎬 التحميل الشامل", callback_data="sec_download")
    )
    markup.add(
        types.InlineKeyboardButton("🧠 الذكاء الاصطناعي", callback_data="sec_ai"),
        types.InlineKeyboardButton("🎨 استوديو التصميم", callback_data="sec_design")
    )
    markup.add(
        types.InlineKeyboardButton("🕌 القسم الإسلامي", callback_data="sec_islamic"),
        types.InlineKeyboardButton("🎮 الألعاب والتحديات", callback_data="sec_games")
    )
    markup.add(
        types.InlineKeyboardButton("💻 أدوات المطورين", callback_data="sec_dev"),
        types.InlineKeyboardButton("💰 الرصيد والشحن", callback_data="sec_wallet")
    )
    markup.add(
        types.InlineKeyboardButton("⏱️ الإنتاجية واليوميات", callback_data="sec_productivity")
    )
    
    # زر الإدارة للمالك فقط
    if user_id == OWNER_ID:
        markup.add(types.InlineKeyboardButton("👑 لوحة الإدارة (المالك)", callback_data="sec_admin"))
        
    return markup

def back_btn():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home"))
    return markup

# ==========================================
# 🚀 [6] الترحيب
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if not user:
        rank = 'owner' if uid == OWNER_ID else 'visitor'
        add_user(uid, message.from_user.first_name, rank)
        user = get_user(uid)
    
    rank_name = RANKS.get(user[3], {}).get("name", "زائر 👤")
    
    text = (
        f"<b>🌟 أهلاً بك يا {message.from_user.first_name}!</b>\n\n"
        f"<blockquote>👑 <b>رتبتك الحالية:</b> {rank_name}\n"
        f"🪙 <b>توكن تركي:</b> <code>{user[2]}</code></blockquote>\n\n"
        f"<i>البوت يحتوي على 10 أقسام رئيسية و 500 ميزة خدمية.</i>\n"
        f"👇 <b>اختر القسم الذي تريد دخوله:</b>"
    )
    bot.send_message(uid, text, reply_markup=main_menu(uid), parse_mode='HTML')

# ==========================================
# 🧭 [7] موجّه الأقسام (Routing)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    if call.data == "back_home":
        bot.edit_message_text("<b>🏠 القائمة الرئيسية:</b>\nاختر القسم:", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid), parse_mode='HTML')
    
    # --- الأقسام ---
    elif call.data == "sec_account":
        text = "<b>👤 قسم الحسابات والأمان (50 ميزة):</b>\n\n- عرض الملف الشخصي\n- تغيير الرتبة\n- الأمان (2FA)\n- سجل النشاطات\n\n<i>(يتم برمجة باقي الميزات هنا)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_download":
        text = "<b>🎬 قسم التحميل الشامل (50 ميزة):</b>\n\n- تيك توك بدون علامة مائية\n- يوتيوب (فيديو/صوت)\n- انستقرام وتويتر\n- تحويل الصيغ\n\n<i>(أرسل أي رابط للبدء فوراً)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_ai":
        text = "<b>🧠 قسم الذكاء الاصطناعي (50 ميزة):</b>\n\n- محادثة ذكية\n- تلخيص النصوص\n- كتابة الأكواد\n- ترجمة فورية\n\n<i>(اكتب أي سؤال ليتم الرد فوراً)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_design":
        text = "<b>🎨 قسم التصميم (50 ميزة):</b>\n\n- توليد الصور بالذكاء\n- إزالة الخلفية\n- صناعة الشعارات\n\n<i>(جاري تفعيل باقي الأدوات)</i>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_islamic":
        text = "<b>🕌 القسم الإسلامي (50 ميزة):</b>\n\n- مواقيت الصلاة\n- أذكار الصباح والمساء\n- القرآن الكريم\n- التقويم الهجري"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_games":
        text = "<b>🎮 قسم الألعاب (50 ميزة):</b>\n\n- لوحة المتصدرين\n- الألغاز\n- سحب الكوينز"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_dev":
        text = "<b>💻 أدوات المطورين (50 ميزة):</b>\n\n- اختصار الروابط\n- توليد كلمات مرور\n- توليد QR Code"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_wallet":
        user = get_user(uid)
        text = f"<b>💰 محفظة توكن تركي:</b>\n\nرصيدك: <code>{user[2]}</code> توكن.\n\n- شحن الرصيد\n- تحويل للأصدقاء\n- سجل الحركات"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_productivity":
        text = "<b>⏱️ أدوات الإنتاجية (50 ميزة):</b>\n\n- المنبهات\n- الملاحظات\n- قوائم المهام\n- حاسبة العمر"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    elif call.data == "sec_admin":
        if uid != OWNER_ID: return
        text = "<b>👑 لوحة الإدارة الشاملة (50 ميزة):</b>\n\n- الإحصائيات\n- الإذاعة\n- إدارة الكوينز والرتب\n- تفعيل الصيانة"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=back_btn(), parse_mode='HTML')

    # --- التنزيل الفعلي ---
    elif call.data.startswith('dl_'):
        action, url = call.data.split('|', 1)
        bot.edit_message_text("⏳ <b>جاري التحميل...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
        
        file_path = download_media(url, action)
        if file_path:
            if os.path.getsize(file_path) > 50*1024*1024:
                bot.edit_message_text("❌ الملف أكبر من 50 ميجا.", call.message.chat.id, call.message.message_id)
            else:
                with open(file_path, 'rb') as f:
                    if action == 'dl_vid': bot.send_video(call.message.chat.id, f)
                    else: bot.send_audio(call.message.chat.id, f)
                bot.delete_message(call.message.chat.id, call.message.message_id)
            try: os.remove(file_path)
            except: pass
        else:
            bot.edit_message_text("❌ خطأ في التحميل.", call.message.chat.id, call.message.message_id, parse_mode='HTML')

# ==========================================
# 🧠 [8] المعالجة التلقائية (AI و الروابط)
# ==========================================
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    
    if message.text.startswith('/'): return 
    
    # الروابط
    if message.text.startswith('http'):
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🎬 فيديو", callback_data=f"dl_vid|{message.text}"),
            types.InlineKeyboardButton("🎵 صوت", callback_data=f"dl_aud|{message.text}")
        )
        bot.reply_to(message, "<b>✅ تم استلام الرابط. اختر الصيغة:</b>", reply_markup=markup, parse_mode='HTML')
    
    # الذكاء الاصطناعي
    else:
        msg = bot.reply_to(message, "🤔 <i>جاري التفكير...</i>", parse_mode='HTML')
        bot.edit_message_text(get_ai_reply(message.text), message.chat.id, msg.message_id, parse_mode='HTML')

# ==========================================
# 🌐 [9] التشغيل
# ==========================================
@app.route('/')
def home(): return "Bot V18 - 10 Sections Architecture is Running!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
def keep_alive(): Thread(target=run).start()

keep_alive()
print("Bot V18 is Running...")
bot.infinity_polling()
