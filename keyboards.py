from telebot import types

def main_menu(user_id, is_owner):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # أزرار سريعة ومرتبة
    markup.add(
        types.InlineKeyboardButton("👤 حسابي", callback_data="menu_profile"),
        types.InlineKeyboardButton("💎 اشتراك VIP", callback_data="menu_vip")
    )
    markup.add(
        types.InlineKeyboardButton("🛠️ الأدوات", callback_data="menu_tools"),
        types.InlineKeyboardButton("ℹ️ المساعدة", callback_data="menu_help")
    )
    markup.add(
        types.InlineKeyboardButton("📢 قناتنا", url="https://t.me/turkibots"),
        types.InlineKeyboardButton("📞 الدعم", url="https://t.me/YourSupport")
    )
    
    if is_owner:
        markup.add(types.InlineKeyboardButton("👑 لوحة الإدارة", callback_data="menu_owner"))
    return markup

def tools_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎨 رسم بالذكاء", callback_data="menu_image"),
        types.InlineKeyboardButton("🎟️ تفعيل كود", callback_data="menu_promo")
    )
    markup.add(
        types.InlineKeyboardButton("📿 أذكار عشوائية", callback_data="menu_adhkar"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
    )
    return markup

def owner_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 إحصائيات", callback_data="owner_stats"),
        types.InlineKeyboardButton("📢 إذاعة", callback_data="owner_broadcast")
    )
    markup.add(
        types.InlineKeyboardButton("💰 شحن رصيد", callback_data="owner_addcoins"),
        types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home")
    )
    return markup

def download_menu(url):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎬 تحميل فيديو", callback_data=f"dl_vid|{url}"),
        types.InlineKeyboardButton("🎵 تحميل صوت", callback_data=f"dl_aud|{url}")
    )
    return markup
