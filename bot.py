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

# Инициализация пользователя, если его нет (чтобы профиль всегда работал)
def ensure_user(chat_id):
    cursor.execute('INSERT OR IGNORE INTO users (id, name, age, sex, roblox, discord, games, bio) VALUES (?,?,?,?,?,?,?,?)', 
                   (chat_id, "Не задано", "0", "Не задано", "Не задано", "Не задано", "Не задано", "Не задано"))
    conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    ensure_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👋 **Привет! Я твой помощник.** Выбирай действие:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "profile":
        cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
        u = cursor.fetchone()
        text = f"👤 **Твой профиль**:\n\n🐸 Имя: {u[1]}\n💀 Возраст: {u[2]}\n⚧ Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}\n📝 О себе: {u[7]}"
        bot.send_message(chat_id, text, parse_mode="Markdown")
    
    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            ("🐸 Имя", "name"), ("💀 Возраст", "age"), ("⚧ Пол", "sex"),
            ("🎮 Roblox", "roblox"), ("💬 Discord", "discord"), ("🕹 Игры", "games")
        ]
        for text, key in buttons:
            markup.add(types.InlineKeyboardButton(f"✏️ {text}", callback_data=f"edit_{key}"))
        bot.edit_message_text("⚙️ **Настройки профиля**:", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        if field == "sex":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👨 Man", callback_data="set_sex_Man"),
                       types.InlineKeyboardButton("👩 Woman", callback_data="set_sex_Woman"))
            bot.send_message(chat_id, "Выбери свой пол:", reply_markup=markup)
        else:
            msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
            bot.register_next_step_handler(msg, lambda m: update_db(m, field))

    elif call.data.startswith("set_sex_"):
        sex = call.data.split("_")[2]
        cursor.execute('UPDATE users SET sex = ? WHERE id = ?', (sex, chat_id))
        conn.commit()
        bot.send_message(chat_id, "✅ Пол обновлен! Напиши /start")

def update_db(message, field):
    cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (message.text, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Успешно! Напиши /start")

bot.polling(none_stop=True)
