from telebot import types

def main_menu(user_id, is_owner):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 حسابي", callback_data="menu_profile"),
        types.InlineKeyboardButton("💎 اشتراك VIP", callback_data="menu_vip")
    )
    markup.add(
        types.InlineKeyboardButton("🤖 محادثة ذكية", callback_data="menu_ai"),
        types.InlineKeyboardButton("🎨 رسم بالذكاء", callback_data="menu_image")
    )
    markup.add(
        types.InlineKeyboardButton("🎟️ تفعيل كود", callback_data="menu_promo")
    )
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
        types.InlineKeyboardButton("💵 تغيير سعر التنزيل", callback_data="admin_cost"),
        types.InlineKeyboardButton("🎁 إنشاء كود", callback_data="admin_promo")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
    return markup
