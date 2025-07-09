import os
import json
from datetime import datetime
import pytz
from telegram import Bot

DATA_FILE = "birthdays.json"
TIMEZONE = pytz.timezone("Europe/Kiev")

def load_data():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def format_msg(e):
    bday = datetime.strptime(e['birthday'], "%Y-%m-%d")
    return f"🎉 День рождения у {e['name']}! 🎂\\nВозраст: {e['age']}\\nДата рождения: {bday.strftime('%d %B')}\\nID: {e['id']}"

def main():
    token = os.getenv("TOKEN")
    chat_id = os.getenv("CHAT_ID")
    topic_id = os.getenv("TOPIC_ID")

    if not token or not chat_id:
        print("Не хватает переменных окружения.")
        return

    bot = Bot(token=token)
    today = datetime.now(TIMEZONE).strftime("%m-%d")
    data = load_data()

    for e in data:
        bd = datetime.strptime(e['birthday'], "%Y-%m-%d")
        if bd.strftime("%m-%d") == today:
            kwargs = {"chat_id": chat_id, "text": format_msg(e)}
            if topic_id:
                kwargs["message_thread_id"] = int(topic_id)
            bot.send_message(**kwargs)

if __name__ == "__main__":
    main()
