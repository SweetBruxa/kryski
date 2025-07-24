
import os
import logging
import pytz
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Получаем токен из переменной окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")

user_data = {}

# Список пользователей
subscribers = set()

# Персонажи и раунды
rounds = {
    1: {"text": "🏝 *Раунд 1: Куда поедем?*\n\nВыбери персонажа:", "choices": ["Олаф", "Кузко", "Джинни"]},
    2: {"text": "✈️ *Раунд 2: Кто тебя сопровождает?*\n\nВыбери персонажа:", "choices": ["Гуфи", "Ванилопа", "Дамбо"]},
    3: {"text": "🍽 *Раунд 3: Где поедим?*\n\nВыбери персонажа:", "choices": ["Луи", "Паскаль", "Немо"]},
    4: {"text": "🏖 *Раунд 4: Кто устроит пляжный хаос?*\n\nВыбери персонажа:", "choices": ["Тритон", "Стич", "Винни-Пух"]},
    5: {"text": "🛬 *Раунд 5: Кто вернётся с тобой домой?*\n\nВыбери персонажа:", "choices": ["Питер Пэн", "Дональд Дак", "Мерида"]}
}

def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    subscribers.add(user_id)
    if user_id not in user_data:
        user_data[user_id] = {"round": 0, "choices": []}
    update.message.reply_text("🎉 Ты подписан на летний челлендж Disney! Следи за раундами и выбирай персонажей 🏖")

def send_round_to_all(context: CallbackContext):
    now = datetime.now(pytz.timezone("Europe/Moscow"))
    round_schedule = {
        1: datetime(2024, 7, 28, 13, 0, tzinfo=pytz.timezone("Europe/Moscow")),
        2: datetime(2024, 7, 31, 13, 0, tzinfo=pytz.timezone("Europe/Moscow")),
        3: datetime(2024, 8, 3, 13, 0, tzinfo=pytz.timezone("Europe/Moscow")),
        4: datetime(2024, 8, 6, 13, 0, tzinfo=pytz.timezone("Europe/Moscow")),
        5: datetime(2024, 8, 9, 13, 0, tzinfo=pytz.timezone("Europe/Moscow")),
    }
    for round_num, scheduled_time in round_schedule.items():
        if abs((now - scheduled_time).total_seconds()) < 60:
            for user_id in subscribers:
                send_round(user_id, context, round_num)

def send_round(user_id: int, context: CallbackContext, round_num: int):
    round_info = rounds[round_num]
    reply_markup = ReplyKeyboardMarkup([[c] for c in round_info["choices"]], one_time_keyboard=True, resize_keyboard=True)
    img_path = f"images/{round_info['choices'][0]}.jpg"
    context.bot.send_message(chat_id=user_id, text=round_info["text"], reply_markup=reply_markup, parse_mode='Markdown')
    for choice in round_info["choices"]:
        with open(f"images/{choice}.jpg", "rb") as img:
            context.bot.send_photo(chat_id=user_id, photo=img, caption=choice)

def handle_choice(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in user_data:
        update.message.reply_text("Напиши /start, чтобы вступить в челлендж!")
        return

    current_round = user_data[user_id]["round"] + 1
    choice = update.message.text.strip()
    if current_round > 5 or choice not in rounds[current_round]["choices"]:
        update.message.reply_text("Пожалуйста, выбери персонажа из предложенных.")
        return

    user_data[user_id]["choices"].append(choice)
    user_data[user_id]["round"] = current_round

    if current_round == 5:
        send_final_story(update, context)

def send_final_story(update: Update, context: CallbackContext):
    choices = user_data[update.message.from_user.id]["choices"]
    story = (
        "🎉 *Твой отпуск завершён!*\n\n"
        f"📍 Начал с {choices[0]}\n"
        f"✈️ В дорогу тебя сопровождал {choices[1]}\n"
        f"🍔 Ты рискнул поесть у {choices[2]}\n"
        f"🏖 Пляж превратил в хаос {choices[3]}\n"
        f"🛬 Домой ты вернулся с {choices[4]}\n\n"
        "📸 Осталось раскрасить все 5 сцен и поделиться в чате!"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=story, parse_mode='Markdown')

def main():
    updater = Updater(8125530642:AAEdhoefboJi9aRWoPUWA1AWQxvMP3vef7Y, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_choice))

    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: send_round_to_all(updater.job_queue._dispatcher), 'interval', minutes=1)
    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
