import telebot
import time
import os

from config import TOKEN, OWNER_ID, DOWNLOAD_DIR
from database import get_user, add_user, update_user, get_price, set_price, create_promo, use_promo, get_all_users
from keyboards import main_menu, download_menu, owner_menu, tools_menu
from downloader import download_media
from keep_alive import keep_alive
from scheduler import start_scheduler
from ai_engine import get_ai_reply, generate_ai_image
from islamic_tools import get_random_adhkar # تأكد إنك رافع هذا الملف

bot = telebot.TeleBot(TOKEN)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
start_scheduler(bot)

def is_owner(user_id): return user_id == OWNER_ID

# --- رسالة الترحيب (الشكل الملكي) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    if not user:
        add_user(uid, message.from_user.first_name, 'owner' if is_owner(uid) else 'user')
        user = get_user(uid)
        
    text = (
        f"<b>🌟 أهلاً بك يا {message.from_user.first_name} في بوت تركي الأسطوري!</b>\n\n"
        f"<blockquote>🧠 <b>البوت الذكي:</b> أرسل أي رابط للتنزيل، أو اكتب أي سؤال وسأجيبك بالذكاء الاصطناعي فوراً!\n"
        f"🎁 <b>رصيدك:</b> <code>{user[2]}</code> كوينز</blockquote>\n\n"
        f"👇 <i>اختر من القائمة أو أرسل رسالتك:</i>"
    )
    
    try:
        bot.send_photo(uid, "https://i.ibb.co/6PZ6X9Q/welcome.jpg", caption=text, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')
    except:
        bot.send_message(uid, text, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')

# --- أوامر سريعة ---
@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = (
        "<b>ℹ️ دليل الاستخدام السريع:</b>\n\n"
        "🔗 <b>الروابط:</b> أرسل رابط (يوتيوب، تيك توك..) مباشرة.\n"
        "🧠 <b>الأسئلة:</b> اكتب أي سؤال (مثلاً: من هو مؤسس جوجل؟) وسأجيبك.\n"
        "🎨 <b>الرسم:</b> روح لقسم الأدوات واختر الرسم بالذكاء الاصطناعي.\n"
        "💰 <b>الرصيد:</b> تكلفة التنزيل <code>5</code> كوينز."
    )
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_owner(message.from_user.id): return
    bot.reply_to(message, "<b>👑 لوحة الإدارة:</b>", reply_markup=owner_menu(), parse_mode='HTML')

# --- لوحة التحكم (الأزرار) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    if call.data == "back_home":
        bot.edit_message_text("<b>🏠 القائمة الرئيسية:</b>", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')
    
    elif call.data == "menu_tools":
        bot.edit_message_text("<b>🛠️ مركز الأدوات:</b>\nاختر الأداة:", call.message.chat.id, call.message.message_id, reply_markup=tools_menu(), parse_mode='HTML')
    
    elif call.data == "menu_adhkar":
        bot.send_message(call.message.chat.id, f"<b>📿 ذكر اليوم:</b>\n<blockquote>{get_random_adhkar()}</blockquote>", parse_mode='HTML')
        
    elif call.data == "menu_image":
        msg = bot.send_message(call.message.chat.id, "🎨 <b>أرسل وصف الصورة التي تريد رسمها:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_image)

    elif call.data == "menu_promo":
        msg = bot.send_message(call.message.chat.id, "🎟️ <b>أرسل كود الشحن الخاص بك:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_promo)

    elif call.data == "menu_profile":
        user = get_user(uid)
        text = f"<b>👤 حسابك:</b>\n💰 الرصيد: <code>{user[2]}</code> كوينز\n🆔 الآيدي: <code>{uid}</code>"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')

    # --- أزرار الأدمن ---
    elif call.data == "menu_owner":
        if not is_owner(uid): return
        bot.edit_message_text("<b>👑 لوحة الإدارة:</b>", call.message.chat.id, call.message.message_id, reply_markup=owner_menu(), parse_mode='HTML')
    
    elif call.data == "owner_stats":
        if not is_owner(uid): return
        bot.answer_callback_query(call.id, f"👥 عدد المستخدمين: {len(get_all_users())}", show_alert=True)

    elif call.data == "owner_addcoins":
        if not is_owner(uid): return
        msg = bot.send_message(call.message.chat.id, "💰 أرسل (الآيدي والمبلغ):\n<code>123456789 100</code>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_addcoins)

# --- الدوال المساعدة ---
def process_image(message):
    msg = bot.reply_to(message, "🎨 <b>جاري الرسم...</b>", parse_mode='HTML')
    url = generate_ai_image(message.text)
    if url:
        bot.send_photo(message.chat.id, url, caption=f"✅ <b>تم الرسم:</b> {message.text}", parse_mode='HTML')
        bot.delete_message(message.chat.id, msg.message_id)
    else: bot.edit_message_text("❌ فشل الرسم.", message.chat.id, msg.message_id)

def process_promo(message):
    amount = use_promo(message.from_user.id, message.text)
    if amount: bot.reply_to(message, f"🎉 <b>مبروك! +{amount} كوينز</b>", parse_mode='HTML')
    else: bot.reply_to(message, "❌ كود غير صحيح.")

def process_addcoins(message):
    try:
        target_id, amount = map(int, message.text.split())
        update_user(target_id, 'coins', get_user(target_id)[2] + amount)
        bot.reply_to(message, "✅ تم شحن الرصيد.")
    except: bot.reply_to(message, "❌ صيغة خاطئة.")

# --- الذكاء التلقائي (الرد على الروابط والنصوص) ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    user = get_user(uid)
    
    # 1. إذا أرسل رابط
    if message.text.startswith('http'):
        current_price = get_price()
        if user[2] < current_price: 
            return bot.reply_to(message, f"❌ رصيدك لا يكفي. تحتاج {current_price} كوينز.")
        
        update_user(uid, 'coins', user[2] - current_price)
        bot.reply_to(message, "<b>✅ تم استلام الرابط. اختر الصيغة:</b>", reply_markup=download_menu(message.text), parse_mode='HTML')
    
    # 2. إذا أرسل أي نص ثاني (الذكاء الاصطناعي يشتغل تلقائياً)
    else:
        msg = bot.reply_to(message, "🤔 <i>جاري التفكير...</i>", parse_mode='HTML')
        ai_response = get_ai_reply(message.text)
        bot.edit_message_text(ai_response, message.chat.id, msg.message_id, parse_mode='HTML')

# --- التنزيل ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def process_download(call):
    action, url = call.data.split('|', 1)
    bot.edit_message_text("⏳ <b>جاري التنزيل بأقصى سرعة...</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    
    file_path = download_media(url, action)
    if file_path:
        if os.path.getsize(file_path) > 50*1024*1024:
            bot.edit_message_text("❌ الملف أكبر من 50 ميجا.", call.message.chat.id, call.message.message_id)
        else:
            with open(file_path, 'rb') as f:
                if action == 'dl_vid': bot.send_video(call.message.chat.id, f, caption="✅ <b>تم التنزيل (بدون علامة مائية)</b>", parse_mode='HTML')
                else: bot.send_audio(call.message.chat.id, f, caption="✅ <b>تم التنزيل</b>", parse_mode='HTML')
            bot.delete_message(call.message.chat.id, call.message.message_id)
        try: os.remove(file_path)
        except: pass
    else:
        bot.edit_message_text("❌ حدث خطأ في التنزيل.", call.message.chat.id, call.message.message_id, parse_mode='HTML')

keep_alive()
bot.infinity_polling()
