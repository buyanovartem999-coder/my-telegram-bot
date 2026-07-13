import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
# Добавлено поле photo_id
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, sex TEXT, 
                   roblox TEXT, discord TEXT, games TEXT, bio TEXT, photo_id TEXT)''')
conn.commit()

def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
    u = cursor.fetchone()
    if not u:
        cursor.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)', (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе", None))
        conn.commit()
        return (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе", None)
    return u

@bot.message_handler(commands=['start'])
def start(message):
    u = get_user(message.chat.id)
    # Если нет фото — запрашиваем
    if not u[8]:
        msg = bot.send_message(message.chat.id, "⚠️ Для продолжения отправь свое фото (аватарку):")
        bot.register_next_step_handler(msg, save_photo)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton(f"👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton(f"⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton(f"📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton(f"🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👑 Добро пожаловать!", reply_markup=markup)

def save_photo(message):
    if message.photo:
        photo_id = message.photo[-1].file_id
        cursor.execute('UPDATE users SET photo_id = ? WHERE id = ?', (photo_id, message.chat.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Фото сохранено! Напиши /start")
    else:
        msg = bot.send_message(message.chat.id, "❌ Это не фото. Отправь картинку:")
        bot.register_next_step_handler(msg, save_photo)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? AND photo_id IS NOT NULL ORDER BY RANDOM() LIMIT 1', (chat_id,))
        u = cursor.fetchone()
        if u:
            text = f"🎯 Напарник: {u[1]}\n💎 Возраст: {u[2]}\n🛡 Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}\n📝 О себе: {u[7]}"
            bot.send_photo(chat_id, u[8], caption=text)
        else:
            bot.send_message(chat_id, "⏳ Никого нет.")
            
    elif call.data == "profile":
        u = get_user(chat_id)
        text = f"👤 Имя: {u[1]}\n💎 Возраст: {u[2]}\n🛡 Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}\n📝 О себе: {u[7]}"
        if u[8]: bot.send_photo(chat_id, u[8], caption=text)
        else: bot.send_message(chat_id, text)

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        fields = [("👤 Имя", "name"), ("💎 Возраст", "age"), ("🛡 Пол", "sex"), 
                  ("🎮 Roblox", "roblox"), ("💬 Discord", "discord"), ("🖼 Фото", "photo")]
        for t, k in fields: markup.add(types.InlineKeyboardButton(f"✏️ {t}", callback_data=f"edit_{k}"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="start"))
        bot.edit_message_text("⚙️ Выберите параметр для изменения:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        if field == "photo":
            msg = bot.send_message(chat_id, "🖼 Отправь новое фото:")
            bot.register_next_step_handler(msg, save_photo)
        elif field == "sex":
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("👨 Man", callback_data="set_sex_Man"), types.InlineKeyboardButton("👩 Woman", callback_data="set_sex_Woman"))
            bot.send_message(chat_id, "🛡 Выберите пол:", reply_markup=m)
        else:
            msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
            bot.register_next_step_handler(msg, lambda m: (cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (m.text, chat_id)), conn.commit(), bot.send_message(chat_id, "✅ Обновлено.")))

    elif call.data.startswith("set_sex_"):
        cursor.execute('UPDATE users SET sex = ? WHERE id = ?', (call.data.split("_")[2], chat_id))
        conn.commit()
        bot.send_message(chat_id, "✅ Пол изменен.")
    
    elif call.data == "start":
        start(call.message)

bot.polling(none_stop=True)
