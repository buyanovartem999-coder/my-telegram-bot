import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, sex TEXT, 
                   roblox TEXT, discord TEXT, games TEXT, bio TEXT, photo_id TEXT)''')
conn.commit()

user_state = {}

def get_profile_text(user):
    return (f"👤 **Твой профиль:**\n\n"
            f"Имя: {user[1]}\nВозраст: {user[2]}\nПол: {user[3]}\n"
            f"Roblox: {user[4]}\nDiscord: {user[5]}\nИгры: {user[6]}\nО себе: {user[7]}")

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбирай действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    
    if call.data == "profile":
        cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
        user = cursor.fetchone()
        if user: bot.send_message(chat_id, get_profile_text(user))
        else: bot.send_message(chat_id, "❌ Профиль не найден. Напиши /reg")

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        fields = {"Имя": "name", "Возраст": "age", "Пол": "sex", "Roblox": "roblox", 
                  "Discord": "discord", "Игры": "games", "О себе": "bio"}
        for name, db_key in fields.items():
            markup.add(types.InlineKeyboardButton(f"✏️ {name}", callback_data=f"edit_{db_key}"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="start"))
        bot.edit_message_text("✏️ Что хочешь изменить?", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        user_state[chat_id] = field
        msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
        bot.register_next_step_handler(msg, save_edit)

    elif call.data == "start":
        start(call.message)

def save_edit(message):
    chat_id = message.chat.id
    field = user_state.get(chat_id)
    cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (message.text, chat_id))
    conn.commit()
    bot.send_message(chat_id, "✅ Успешно обновлено! Напиши /start")

bot.polling(none_stop=True)
