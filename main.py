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

# --- رسالة الترحيب الفخمة ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    ai_users.discard(uid)
    user = get_user(uid)
    
    if not user:
        add_user(uid, message.from_user.first_name, 'owner' if is_owner(uid) else 'user')
        text = (
            f"<b>🌟 أهلاً بك يا {message.from_user.first_name} في بوت تركي الأسطوري!</b>\n\n"
            f"<blockquote>🎁 حصلت على <b>30 كوينز</b> هدية ترحيبية.\n"
            f"🚀 أرسل لي أي رابط فيديو (يوتيوب، تيك توك، انستقرام) وسأنزله لك <b>بدون علامة مائية</b>.</blockquote>\n\n"
            f"👇 <i>اختر من القائمة أدناه للبدء:</i>"
        )
    else:
        text = (
            f"<b>👋 أهلاً بعودتك يا {message.from_user.first_name}!</b>\n\n"
            f"💰 <b>رصيدك الحالي:</b> <code>{user[2]}</code> كوينز.\n"
            f"📥 <i>أرسل أي رابط للتنزيل، أو اختر من القائمة:</i>"
        )
    
    bot.send_message(uid, text, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')

# --- أوامر المالك ---
@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_owner(message.from_user.id): return
    text = (
        "<b>👑 لوحة المالك:</b>\n\n"
        "لتغيير سعر التنزيل: <code>/setprice 10</code>\n"
        "لإنشاء كود شحن: <code>/addpromo CODE 100 50</code>"
    )
    bot.reply_to(message, text, reply_markup=admin_panel(), parse_mode='HTML')

@bot.message_handler(commands=['setprice'])
def change_price(message):
    if not is_owner(message.from_user.id): return
    try:
        set_price(int(message.text.split()[1]))
        bot.reply_to(message, "✅ <b>تم تغيير سعر التنزيل بنجاح!</b>", parse_mode='HTML')
    except: bot.reply_to(message, "⚠️ استخدم: <code>/setprice 10</code>", parse_mode='HTML')

@bot.message_handler(commands=['addpromo'])
def add_promo(message):
    if not is_owner(message.from_user.id): return
    try:
        args = message.text.split()
        if create_promo(args[1], int(args[2]), int(args[3])):
            bot.reply_to(message, f"✅ <b>تم صنع الكود:</b> <code>{args[1]}</code>", parse_mode='HTML')
        else: bot.reply_to(message, "❌ الكود موجود مسبقاً.")
    except: bot.reply_to(message, "⚠️ استخدم: <code>/addpromo CODE 100 50</code>", parse_mode='HTML')

# --- الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    if call.data == "back_home":
        ai_users.discard(uid)
        bot.edit_message_text("<b>🏠 القائمة الرئيسية:</b>", call.message.chat.id, call.message.message_id, reply_markup=main_menu(uid, is_owner(uid)), parse_mode='HTML')
    
    elif call.data == "menu_ai":
        ai_users.add(uid)
        bot.edit_message_text("<b>🤖 المحادثة الذكية:</b>\n\nاكتب أي سؤال وسأرد عليك فوراً.\n<i>(اكتب /start للخروج)</i>", call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data == "menu_image":
        msg = bot.send_message(call.message.chat.id, "🎨 <b>أرسل وصف الصورة التي تريد رسمها:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_image)
    
    elif call.data == "menu_promo":
        msg = bot.send_message(call.message.chat.id, "🎟️ <b>أرسل كود الشحن الخاص بك:</b>", parse_mode='HTML')
        bot.register_next_step_handler(msg, process_promo)

    elif call.data == "menu_profile":
        user = get_user(uid)
        vip_stat = f"✅ نشط" if user[3] > time.time() else "❌ غير نشط"
        text = f"<b>👤 ملفك الشخصي:</b>\n\n💰 <b>الرصيد:</b> <code>{user[2]}</code> كوينز\n👑 <b>الاشتراك:</b> {vip_stat}"
        markup = telebot.types.InlineKeyboardMarkup().add(telebot.types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode='HTML')

# --- الدوال المساعدة ---
def process_image(message):
    msg = bot.reply_to(message, "🎨 <b>جاري الرسم... انتظر قليلاً.</b>", parse_mode='HTML')
    url = generate_ai_image(message.text)
    if url:
        try:
            bot.send_photo(message.chat.id, url, caption=f"✅ <b>تم الرسم:</b> {message.text}", parse_mode='HTML')
            bot.delete_message(message.chat.id, msg.message_id)
        except: bot.edit_message_text("❌ فشل إرسال الصورة.", message.chat.id, msg.message_id)
    else: bot.edit_message_text("❌ حدث خطأ أثناء الرسم.", message.chat.id, msg.message_id)

def process_promo(message):
    amount = use_promo(message.from_user.id, message.text)
    if amount: bot.reply_to(message, f"🎉 <b>مبروك! تم شحن {amount} كوينز لرصيدك.</b>", parse_mode='HTML')
    else: bot.reply_to(message, "❌ الكود غير صحيح أو منتهي.")

# --- استقبال الروابط والنصوص ---
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    uid = message.from_user.id
    
    # إذا كان في وضع المحادثة الذكية
    if uid in ai_users:
        msg = bot.reply_to(message, "🤔 <i>جاري التفكير...</i>", parse_mode='HTML')
        bot.edit_message_text(get_ai_reply(message.text), message.chat.id, msg.message_id, parse_mode='HTML')
        return

    # إذا أرسل رابط
    if message.text.startswith('http'):
        user = get_user(uid)
        if not user: return
        
        current_price = get_price()
        if user[2] < current_price: 
            return bot.reply_to(message, f"❌ <b>رصيدك لا يكفي.</b>\nتحتاج {current_price} كوينز، ورصيدك {user[2]}.", parse_mode='HTML')
        
        # خصم الرصيد
        update_user(uid, 'coins', user[2] - current_price)
        
        # إرسال رسالة اختيار الصيغة
        text = "<b>✅ تم استلام الرابط بنجاح.</b>\nاختر صيغة التنزيل (سيتم التنزيل <b>بدون علامة مائية</b>):"
        bot.reply_to(message, text, reply_markup=download_menu(message.text), parse_mode='HTML')
    else:
        bot.reply_to(message, "❓ لم أفهم طلبك. أرسل رابط فيديو، أو اكتب /start.")

# --- التنزيل الفعلي ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def process_download(call):
    action, url = call.data.split('|', 1)
    bot.edit_message_text("⏳ <b>جاري التنزيل... قد يستغرق بضع ثواني.</b>", call.message.chat.id, call.message.message_id, parse_mode='HTML')
    
    file_path = download_media(url, action)
    
    if file_path and os.path.exists(file_path):
        # التحقق من حجم الملف (تيليجرام يسمح بـ 50 ميجا كحد أقصى للبوتات)
        if os.path.getsize(file_path) > 50*1024*1024:
            bot.edit_message_text("❌ <b>عذراً، حجم الملف أكبر من 50 ميجا (حد تيليجرام).</b>\nجرب فيديو أقصر.", call.message.chat.id, call.message.message_id, parse_mode='HTML')
        else:
            with open(file_path, 'rb') as f:
                if action == 'dl_vid': 
                    bot.send_video(call.message.chat.id, f, caption="✅ <b>تم التنزيل (بدون علامة مائية)</b>", parse_mode='HTML')
                else: 
                    bot.send_audio(call.message.chat.id, f, caption="✅ <b>تم التنزيل (صوت)</b>", parse_mode='HTML')
            bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # 🧹 حذف الملف من السيرفر فوراً بعد الإرسال
        try: os.remove(file_path)
        except: pass
    else:
        bot.edit_message_text("❌ <b>حدث خطأ في التنزيل.</b>\nقد يكون الرابط غير مدعوم أو الحساب خاص.", call.message.chat.id, call.message.message_id, parse_mode='HTML')

keep_alive()
print("Bot V15 is Running...")
bot.infinity_polling()
