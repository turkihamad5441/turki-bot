import schedule
import time
import threading
from database import get_all_users
from ai_engine import generate_auto_adhkar
from telebot import types

def start_scheduler(bot):
    def send_auto_adhkar():
        users = get_all_users()
        if not users: return
        
        adhkar_text = generate_auto_adhkar()
        text = f"<b>🕌 تذكير إيماني تلقائي:</b>\n\n<blockquote>{adhkar_text}</blockquote>"
        
        for user_id in users:
            try:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back_home"))
                bot.send_message(user_id, text, reply_markup=markup, parse_mode='HTML')
                time.sleep(0.1)
            except:
                pass

    schedule.every(4).hours.do(send_auto_adhkar) # كل 4 ساعات
    
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    thread = threading.Thread(target=run_schedule)
    thread.daemon = True
    thread.start()
