import telebot
import time
import os

from config import TOKEN, OWNER_ID, DOWNLOAD_DIR, COOLDOWN
from database import get_user, add_user, update_user, get_price, set_price, create_promo, use_promo
from keyboards import main_menu, download_menu, admin_panel
from downloader import download_media
from keep_alive import keep_alive
from scheduler import start_scheduler
from ai_engine import get_ai_reply, generate_ai_image

bot = telebot.TeleBot(TOKEN)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
start_scheduler(bot)
ai_users = set()

def is_owner(user_id): return user_id == OWNER_ID

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    ai_users.discard(uid)
    user = get_user(uid)
    if not user:
        add_user(uid, message.from_user.first_name, 'owner' if is_owner(uid) else 'user')
        text = "<b>🌟 أهلاً بك في بوت تركي!</b>\n\n🎁 حصلت على 30 كوينز هدية.\n🚀 أرسل أي رابط وسأنزله لك."
    else:
        text = f"<b>👋 أهلاً بعودتك!</b>\n\n💰 رصيدك: <code>{user[2]}</code> كوينز.\n👇 اختر من القائمة:"
    bot.send_message(uid, text, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, "<b>👑 لوحة المالك:</b>\n\n/setprice 10 - تغيير السعر\n/addpromo CODE 100 50 - صنع كود", reply_markup=admin_panel(), parse_mode='HTML')

@bot.message_handler(commands=['setprice'])
def change_price(message):
    if not is_owner(message.from_user.id): return
    try:
        set_price(int(message.text.split()[1]))
        bot.reply_to(message, "✅ تم تغيير سعر التنزيل.")
    except: bot.reply_to(message, "⚠️ استخدم: /setprice 10")

@bot.message_handler(commands=['addpromo'])
def add_promo(message):
    if not is_owner(message.from_user.id): return
    try:
        args = message.text.split()
        if create_promo(args[1], int(args[2]), int(args[3])):
            bot.reply_to(message, f"✅ تم صنع الكود: {args[1]}")
        else: bot.reply_to(message, "❌ الكود موجود مسبقاً.")
    except: bot.reply_to(message, "⚠️ استخدم: /addpromo CODE 100 50")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    if call.data == "back_home":
        ai_users.discard(uid)
        bot.edit_message_text("<b>🏠 القائمة الرئيسية:</b>", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')
    elif call.data == "menu_ai":
        ai_users.add(uid)
        bot.edit_message_text("<b>🤖 المحادثة الذكية:</b>\nاكتب أي سؤال.\n<i>(اكتب /start للخروج)</i>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    elif call.data == "menu_image":
        msg = bot.send_message(call.message.chat.id, "🎨 أرسل وصف الصورة:")
        bot.register_next_step_handler(msg, process_image)
    elif call.data == "menu_promo":
        msg = bot.send_message(call.message.chat.id, "🎟️ أرسل كود الشحن:")
        bot.register_next_step_handler(msg, process_promo)

def process_image(message):
    msg = bot.reply_to(message, "🎨 <b>جاري الرسم...</b>", parse_mode='HTML')
    url = generate_ai_image(message.text)
    if url:
        bot.send_photo(message.chat.id, url, caption=f"✅ {message.text}")
        bot.delete_message(message.chat.id, msg.message_id)
    else: bot.edit_message_text("❌ فشل الرسم.", message.chat.id, msg.message_id)

def process_promo(message):
    amount = use_promo(message.from_user.id, message.text)
    if amount: bot.reply_to(message, f"🎉 مبروك! تم شحن {amount} كوينز.")
    else: bot.reply_to(message, "❌ الكود غير صحيح أو منتهي.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    if uid in ai_users:
        msg = bot.reply_to(message, "🤔 <i>جاري التفكير...</i>", parse_mode='HTML')
        bot.edit_message_text(get_ai_reply(message.text), message.chat.id, msg.message_id, parse_mode='HTML')
    elif message.text.startswith('http'):
        user = get_user(uid)
        if not user: return
        current_price = get_price()
        if user[2] < current_price: 
            return bot.reply_to(message, f"❌ رصيدك لا يكفي. تحتاج {current_price} كوينز.")
        
        update_user(uid, 'coins', user[2] - current_price)
        bot.reply_to(message, "✅ <b>تم استلام الرابط.</b>\nاختر الصيغة:", reply_markup=download_menu(message.text), parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def process_download(call):
    action, url = call.data.split('|', 1)
    bot.edit_message_text("⏳ <b>جاري التنزيل...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    file_path = download_media(url, action)
    if file_path:
        if os.path.getsize(file_path) > 50*1024*1024:
            bot.edit_message_text("❌ الملف أكبر من 50 ميجا.", call.message.chat.id, call.message.message_id)
        else:
            with open(file_path, 'rb') as f:
                if action == 'dl_vid': bot.send_video(call.message.chat.id, f, caption="✅ تم التنزيل")
                else: bot.send_audio(call.message.chat.id, f, caption="✅ تم التنزيل")
            bot.delete_message(call.message.chat.id, call.message.message_id)
        os.remove(file_path)
    else: bot.edit_message_text("❌ خطأ في التنزيل.", call.message.chat.id, call.message.message_id, parse_mode='HTML')

keep_alive()
print("Bot V15 is Running...")
bot.infinity_polling()
