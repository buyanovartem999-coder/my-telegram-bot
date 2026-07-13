import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, roblox TEXT, games TEXT, description TEXT, photo_id TEXT)')
conn.commit()

user_data = {}

def delete_msg(chat_id, message_id):
    try: bot.delete_message(chat_id, message_id)
    except: pass

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Регистрация", callback_data="reg"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("👥 Группа", url="https://t.me/+GDw01C7KS1xlOTBi"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбирай действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "settings":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✏️ Изменить Имя", callback_data="edit_name"),
            types.InlineKeyboardButton("✏️ Изменить Ник Roblox", callback_data="edit_roblox"),
            types.InlineKeyboardButton("⬅️ Назад", callback_data="start")
        )
        bot.edit_message_text("⚙️ Что хочешь изменить?", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        user_data[chat_id] = {'edit': field}
        msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
        bot.register_next_step_handler(msg, update_db)

    elif call.data == "start":
        start(call.message)
    elif call.data == "find":
        # ... (логика поиска остается прежней)
        pass

def update_db(message):
    field = user_data[message.chat.id]['edit']
    val = message.text
    
    # Проверка для никнейма
    if field == "roblox" and len(val) < 3:
        bot.send_message(message.chat.id, "❌ Слишком короткий ник!")
        return

    cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (val, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Успешно обновлено! Напиши /start.")

bot.polling(none_stop=True)
