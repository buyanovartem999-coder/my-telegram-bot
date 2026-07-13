import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, sex TEXT, 
                   roblox TEXT, discord TEXT, games TEXT, bio TEXT, photo_id TEXT, username TEXT)''')
conn.commit()

temp_data = {}

def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
    u = cursor.fetchone()
    username = bot.get_chat(chat_id).username or "Нет"
    if not u:
        cursor.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)', (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе", None, username))
    else:
        cursor.execute('UPDATE users SET username = ? WHERE id = ?', (username, chat_id))
    conn.commit()
    return cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,)).fetchone()

@bot.message_handler(commands=['start'])
def start(message):
    u = get_user(message.chat.id)
    if not u[8]:
        msg = bot.send_message(message.chat.id, "⚠️ Пришли фото для профиля:")
        bot.register_next_step_handler(msg, save_photo)
        return
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("✨ Найти", callback_data="find"),
               types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
               types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
               types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
               types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly"))
    bot.send_message(message.chat.id, "👑 Главное меню:", reply_markup=markup)

def save_photo(message):
    if message.photo:
        cursor.execute('UPDATE users SET photo_id = ? WHERE id = ?', (message.photo[-1].file_id, message.chat.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Сохранено! Напиши /start")
    else:
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ Пришли фото:"), save_photo)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? AND photo_id IS NOT NULL ORDER BY RANDOM() LIMIT 1', (chat_id,))
        u = cursor.fetchone()
        if u:
            temp_data[chat_id] = u[0]
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❤️ Лайк", callback_data="like"),
                       types.InlineKeyboardButton("👎 Диз", callback_data="find"))
            bot.send_photo(chat_id, u[8], caption=f"🎯 Напарник: {u[1]}\n🎮 Roblox: {u[4]}\n📝 О себе: {u[7]}", reply_markup=markup)
        else:
            bot.send_message(chat_id, "⏳ Никого нет.")

    elif call.data == "like":
        target_id = temp_data.get(chat_id)
        if target_id:
            t_user = cursor.execute('SELECT username FROM users WHERE id = ?', (target_id,)).fetchone()[0]
            bot.send_message(chat_id, f"✅ Ник напарника: @{t_user}. Можешь отправить ему сообщение ниже:")
            bot.register_next_step_handler(call.message, lambda m: bot.send_message(target_id, f"📩 От напарника: {m.text}"))

    elif call.data == "profile":
        u = get_user(chat_id)
        text = f"👤 {u[1]}\n💎 {u[2]}\n🛡 {u[3]}\n🎮 {u[4]}\n💬 {u[5]}\n🕹 {u[6]}\n📝 {u[7]}"
        if u[8]: bot.send_photo(chat_id, u[8], caption=text)
        else: bot.send_message(chat_id, text)

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        fields = [("Имя", "name"), ("Возраст", "age"), ("Пол", "sex"), ("Roblox", "roblox"), ("Discord", "discord"), ("Фото", "photo")]
        for t, k in fields: markup.add(types.InlineKeyboardButton(f"✏️ {t}", callback_data=f"edit_{k}"))
        bot.edit_message_text("⚙️ Что изменить?", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        if field == "photo":
            bot.register_next_step_handler(bot.send_message(chat_id, "🖼 Пришли фото:"), save_photo)
        elif field == "sex":
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("Man", callback_data="set_sex_Man"), types.InlineKeyboardButton("Woman", callback_data="set_sex_Woman"))
            bot.send_message(chat_id, "🛡 Пол:", reply_markup=m)
        else:
            msg = bot.send_message(chat_id, f"Введите {field}:")
            bot.register_next_step_handler(msg, lambda m: (cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (m.text, chat_id)), conn.commit(), bot.send_message(chat_id, "✅ Успешно.")))

    elif call.data.startswith("set_sex_"):
        cursor.execute('UPDATE users SET sex = ? WHERE id = ?', (call.data.split("_")[2], chat_id))
        conn.commit()
        bot.send_message(chat_id, "✅ Пол изменен.")

bot.polling(none_stop=True)
