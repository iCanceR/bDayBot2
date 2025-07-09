import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from datetime import datetime

DATA_FILE = "birthdays.json"

ADD_NAME, ADD_AGE, ADD_ID, ADD_BIRTHDAY = range(4)
EDIT_CHOICE, EDIT_NEW_VALUE = range(2)

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для напоминаний о днях рождения 👋\n"
        "/add – добавить\n"
        "/edit <id> – изменить\n"
        "/delete <id> – удалить\n"
        "/list – список\n"
        "/cancel – отменить"
    )

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите имя:")
    return ADD_NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['entry'] = {'name': update.message.text}
    await update.message.reply_text("Введите возраст:")
    return ADD_AGE

async def add_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("Возраст должен быть числом.")
        return ADD_AGE
    context.user_data['entry']['age'] = int(update.message.text)
    await update.message.reply_text("Введите ID:")
    return ADD_ID

async def add_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['entry']['id'] = update.message.text
    await update.message.reply_text("Введите дату рождения (ГГГГ-ММ-ДД):")
    return ADD_BIRTHDAY

async def add_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        datetime.strptime(update.message.text, "%Y-%m-%d")
    except:
        await update.message.reply_text("Неверный формат. Пример: 1995-06-27")
        return ADD_BIRTHDAY
    context.user_data['entry']['birthday'] = update.message.text
    data = load_data()
    data.append(context.user_data['entry'])
    save_data(data)
    await update.message.reply_text("✅ Добавлено!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

async def list_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("Список пуст.")
        return
    msg = "\n\n".join([f"{e['name']} ({e['age']} лет)\nID: {e['id']}\nДР: {e['birthday']}" for e in data])
    await update.message.reply_text(msg)

async def delete_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /delete 123456")
        return
    id_ = context.args[0]
    data = load_data()
    new_data = [e for e in data if e['id'] != id_]
    if len(data) == len(new_data):
        await update.message.reply_text("ID не найден.")
    else:
        save_data(new_data)
        await update.message.reply_text("Удалено.")

async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /edit 123456")
        return ConversationHandler.END
    id_ = context.args[0]
    data = load_data()
    entry = next((e for e in data if e['id'] == id_), None)
    if not entry:
        await update.message.reply_text("ID не найден.")
        return ConversationHandler.END
    context.user_data['edit_id'] = id_
    context.user_data['edit_entry'] = entry
    await update.message.reply_text("Что редактировать? (name, age, id, birthday):")
    return EDIT_CHOICE

async def edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text
    if field not in ('name', 'age', 'id', 'birthday'):
        await update.message.reply_text("Выберите: name, age, id, birthday")
        return EDIT_CHOICE
    context.user_data['edit_field'] = field
    await update.message.reply_text("Введите новое значение:")
    return EDIT_NEW_VALUE

async def edit_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    field = context.user_data['edit_field']
    if field == "age" and not val.isdigit():
        await update.message.reply_text("Возраст должен быть числом.")
        return EDIT_NEW_VALUE
    if field == "birthday":
        try:
            datetime.strptime(val, "%Y-%m-%d")
        except:
            await update.message.reply_text("Формат даты: ГГГГ-ММ-ДД")
            return EDIT_NEW_VALUE
    data = load_data()
    for e in data:
        if e['id'] == context.user_data['edit_id']:
            e[field] = int(val) if field == "age" else val
    save_data(data)
    await update.message.reply_text("Изменено.")
    return ConversationHandler.END

async def main():
    from telegram.ext import ApplicationBuilder
    TOKEN = os.getenv("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    conv_add = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            ADD_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_age)],
            ADD_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_id)],
            ADD_BIRTHDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_birthday)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    conv_edit = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_start)],
        states={
            EDIT_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_choice)],
            EDIT_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_add)
    app.add_handler(conv_edit)
    app.add_handler(CommandHandler("delete", delete_entry))
    app.add_handler(CommandHandler("list", list_entries))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
