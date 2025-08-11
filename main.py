import os
from dotenv import load_dotenv
import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
import random
import string
import datetime

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("توکن ربات در متغیر محیطی BOT_TOKEN تعریف نشده است!")

CHANNEL_ID = -1001657777927  # آیدی عددی کانال شما

bot = telebot.TeleBot(TOKEN)
user_data = {}
group_ids = set()

# تعریف ماه‌های شمسی به فارسی
jalali_months_fa = [
    "فروردین", "اردیبهشت", "خرداد", "تیر",
    "مرداد", "شهریور", "مهر", "آبان",
    "آذر", "دی", "بهمن", "اسفند"
]

# معادل فارسی روزهای هفته
weekdays_fa = {
    "Saturday": "شنبه",
    "Sunday": "یک‌شنبه",
    "Monday": "دوشنبه",
    "Tuesday": "سه‌شنبه",
    "Wednesday": "چهارشنبه",
    "Thursday": "پنج‌شنبه",
    "Friday": "جمعه"
}

# تابع تبدیل تاریخ میلادی به شمسی
def gregorian_to_jalali(g_y, g_m, g_d):
    g_days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    j_days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]

    gy = g_y - 1600
    gm = g_m - 1
    gd = g_d - 1

    g_day_no = 365 * gy + (gy + 3) // 4 - (gy + 99) // 100 + (gy + 399) // 400
    for i in range(gm):
        g_day_no += g_days_in_month[i]
    g_day_no += gd

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)
    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    for i in range(11):
        if j_day_no < j_days_in_month[i]:
            jm = i + 1
            jd = j_day_no + 1
            break
        j_day_no -= j_days_in_month[i]
    else:
        jm = 12
        jd = j_day_no + 1

    return jy, jm, jd

def get_jalali_date_fa():
    now = datetime.datetime.now()
    weekday_en = now.strftime('%A')
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    weekday_fa = weekdays_fa.get(weekday_en, weekday_en)
    return f"{weekday_fa} {jd} {jalali_months_fa[jm - 1]} {jy}"

def send_poll_to_groups():
    for gid in group_ids:
        try:
            bot.send_message(gid, "📢 نظرسنجی هفتگی آغاز شد!\nبرای ثبت نظر، لطفاً به ربات پیام خصوصی بده.")
        except Exception as e:
            print(f"خطا در ارسال پیام به گروه {gid}: {e}")

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
        date_fa = get_jalali_date_fa()

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
