import os
from dotenv import load_dotenv
import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
import random
import string
import jdatetime

load_dotenv()  # بارگذاری متغیرهای محیطی از فایل .env

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات در فایل .env با کلید BOT_TOKEN تعریف نشده است!")

CHANNEL_ID = -1001657777927  # آیدی عددی کانال

bot = telebot.TeleBot(TOKEN)
user_data = {}
group_ids = set()

def send_poll_to_groups():
    for gid in group_ids:
        try:
            bot.send_message(gid, "📢 نظرسنجی هفتگی آغاز شد!\nبرای ثبت نظر، لطفاً به ربات پیام خصوصی بده.")
            print(f"✅ پیام نظرسنجی به گروه {gid} ارسال شد.")
        except Exception as e:
            print(f"❌ خطا در ارسال پیام به گروه {gid}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(send_poll_to_groups, 'cron', day_of_week='fri', hour=18, minute=0)
scheduler.start()

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    if message.chat.type == 'private':
        user_data[chat_id] = {'step': 'anon_choice'}
        bot.send_message(chat_id, "سلام! 👋\nآیا می‌خوای نظرت با اسم ثبت بشه؟ (بله / نه)")
    else:
        group_ids.add(chat_id)
        print(f"✅ گروه با آی‌دی {chat_id} ثبت شد.")

@bot.message_handler(func=lambda m: m.chat.type == 'private')
def handle_private(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id not in user_data:
        bot.send_message(chat_id, "لطفاً ابتدا /start رو بزن 🙂")
        return

    step = user_data[chat_id]['step']

    if step == 'anon_choice':
        if text.lower() in ['بله', 'بلی', 'بله.', 'yes']:
            user_data[chat_id]['anon'] = False
            user_data[chat_id]['step'] = 'name'
            bot.send_message(chat_id, "🧒 لطفاً *نام و نام خانوادگی* خودتو وارد کن:")
        elif text.lower() in ['نه', 'خیر', 'نه.', 'no']:
            user_data[chat_id]['anon'] = True
            user_data[chat_id]['step'] = 'advisor'
            bot.send_message(chat_id, "🗣 نام مشاورت رو وارد کن:")
        else:
            bot.send_message(chat_id, "فقط 'بله' یا 'نه' پاسخ بده 🙂")

    elif step == 'name':
        user_data[chat_id]['name'] = text
        user_data[chat_id]['step'] = 'province'
        bot.send_message(chat_id, "🏘 استان محل سکونتت رو وارد کن:")

    elif step == 'province':
        user_data[chat_id]['province'] = text
        user_data[chat_id]['step'] = 'advisor'
        bot.send_message(chat_id, "🗣 نام مشاورت رو وارد کن:")

    elif step == 'advisor':
        user_data[chat_id]['advisor'] = text
        user_data[chat_id]['step'] = 'rating'
        bot.send_message(chat_id, "⭐️ از 1 تا 5 به مشاورت نمره بده:\n\n۵ = عالی\n۴ = خوب\n۳ = معمولی\n۲ = ضعیف\n۱ = خیلی ضعیف\n\n🔢 لطفاً عدد را با کیبورد انگلیسی وارد کن (مثلاً: 4)")

    elif step == 'rating':
        if text not in ['1', '2', '3', '4', '5']:
            bot.send_message(chat_id, "❗ لطفاً فقط یک عدد بین 1 تا 5 وارد کن (با کیبورد انگلیسی).")
            return
        user_data[chat_id]['rating'] = text
        user_data[chat_id]['step'] = 'opinion'
        bot.send_message(chat_id, "💬 حالا لطفاً نظرتو درباره عملکرد مشاورت بنویس:")

    elif step == 'opinion':
        user_data[chat_id]['opinion'] = text

        info = user_data[chat_id]
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        now = jdatetime.date.today()
        weekday = now.strftime('%A')
        date_fa = f"{weekday} {now.day} {now.j_months_fa[now.month - 1]} {now.year}"

        name_line = f"🧒 اسم دانش آموز: {info['name']}" if not info['anon'] else "🧒 اسم دانش آموز: (ناشناس)"
        province_line = f"🏘 استان: {info['province']}" if not info['anon'] else "🏘 استان: ---"

        rating_map = {
            '5': '۵ (عالی)',
            '4': '۴ (خوب)',
            '3': '۳ (معمولی)',
            '2': '۲ (ضعیف)',
            '1': '۱ (خیلی ضعیف)'
        }

        final_msg = f"""✅ ثبت نظر

{name_line}
{province_line}
🗣 مشاور: {info['advisor']}

⭐️ امتیاز داده شده: {rating_map[info['rating']]}
💬 نظر هفتگی: {info['opinion']}

🧾 کد نظر: {code}
📅 {date_fa}
"""

        bot.send_message(CHANNEL_ID, final_msg)
        bot.send_message(chat_id, "✅ نظرت با موفقیت ثبت شد. ممنون از همکاری‌ت 🌷")
        user_data.pop(chat_id)

    else:
        bot.send_message(chat_id, "لطفاً ابتدا /start رو بزن.")

@bot.message_handler(func=lambda m: m.chat.type != 'private')
def handle_groups(message):
    group_ids.add(message.chat.id)

if __name__ == "__main__":
    print("✅ ربات با موفقیت اجرا شد...")
    bot.infinity_polling()
