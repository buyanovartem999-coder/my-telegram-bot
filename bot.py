import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, sex TEXT, 
                   roblox TEXT, discord TEXT, games TEXT, bio TEXT)''')
conn.commit()

# Функция для получения пользователя
def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
    u = cursor.fetchone()
    if not u:
        cursor.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)', (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе"))
        conn.commit()
        return (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе")
    return u

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings")
    )
    # Используем премиум-символы прямо в тексте
    bot.send_message(message.chat.id, "🍃 С возвращением! Что делаем ква? 💚", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (chat_id,))
        u = cursor.fetchone()
        if u:
            text = f"☄️ Кто-то ищет напарника!\n\n👤 Имя: {u[1]}\n💎 Возраст: {u[2]}\n⚧ Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}"
            bot.send_message(chat_id, text)
        else:
            bot.send_message(chat_id, "⏳ В базе пока никого нет.")
            
    elif call.data == "profile":
        u = get_user(chat_id)
        text = f"👤 Твой профиль:\n\n🐸 Имя: {u[1]}\n💀 Возраст: {u[2]}\n⚧ Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}"
        bot.send_message(chat_id, text)

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [("🐸 Имя", "name"), ("💀 Возраст", "age"), ("⚧ Пол", "sex"), ("🎮 Roblox", "roblox"), ("💬 Discord", "discord"), ("🕹 Игры", "games")]
        for t, k in btns: markup.add(types.InlineKeyboardButton(f"✏️ {t}", callback_data=f"edit_{k}"))
        bot.edit_message_text("⚙️ Что хочешь изменить?", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        if field == "sex":
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("👨 Man", callback_data="set_sex_Man"), types.InlineKeyboardButton("👩 Woman", callback_data="set_sex_Woman"))
            bot.send_message(chat_id, "🛡 Выбери пол:", reply_markup=m)
        else:
            msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
            bot.register_next_step_handler(msg, lambda m: (cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (m.text, chat_id)), conn.commit(), bot.send_message(chat_id, "✅ Успешно обновлено!")))

    elif call.data.startswith("set_sex_"):
        cursor.execute('UPDATE users SET sex = ? WHERE id = ?', (call.data.split("_")[2], chat_id))
        conn.commit()
        bot.send_message(chat_id, "✅ Пол изменен!")

bot.polling(none_stop=True)
