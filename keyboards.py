from telebot import types

def main_menu(user_id, is_owner):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # الصف الأول
    markup.add(
        types.InlineKeyboardButton("👤 حسابي", callback_data="menu_profile"),
        types.InlineKeyboardButton("💎 اشتراك VIP", callback_data="menu_vip")
    )
    # الصف الثاني (الذكاء الاصطناعي)
    markup.add(
        types.InlineKeyboardButton("🤖 محادثة ذكية", callback_data="menu_ai"),
        types.InlineKeyboardButton("🎨 رسم بالذكاء", callback_data="menu_image")
    )
    # الصف الثالث (الأدوات)
    markup.add(
        types.InlineKeyboardButton("🕌 أذكار وأدعية", callback_data="menu_islamic"),
        types.InlineKeyboardButton("🎟️ تفعيل كود", callback_data="menu_promo")
    )
    # الصف الرابع (روابط)
    markup.add(
        types.InlineKeyboardButton("📢 قناتنا", url="https://t.me/turkibots"),
        types.InlineKeyboardButton("📞 الدعم الفني", url="https://t.me/YourSupport")
    )
    # زر المالك (يظهر فقط لك)
    if is_owner:
        markup.add(types.InlineKeyboardButton("👑 لوحة المالك", callback_data="menu_owner"))
    return markup

def download_menu(url):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎬 فيديو (MP4)", callback_data=f"dl_vid|{url}"),
        types.InlineKeyboardButton("🎵 صوت (MP3)", callback_data=f"dl_aud|{url}")
    )
    return markup

def admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💵 تغيير السعر", callback_data="admin_cost"),
        types.InlineKeyboardButton("🎁 إنشاء كود", callback_data="admin_promo")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    return markup
