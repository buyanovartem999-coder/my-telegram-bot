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

# Хранилище того, кого сейчас просматривает юзер
temp_data = {}

def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
    u = cursor.fetchone()
    # Обновляем username при каждом входе
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
               types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"))
    bot.send_message(message.chat.id, "👑 Меню:", reply_markup=markup)

def save_photo(message):
    if message.photo:
        cursor.execute('UPDATE users SET photo_id = ? WHERE id = ?', (message.photo[-1].file_id, message.chat.id))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Сохранено! Напиши /start")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? AND photo_id IS NOT NULL ORDER BY RANDOM() LIMIT 1', (chat_id,))
        u = cursor.fetchone()
        if u:
            temp_data[chat_id] = u[0] # Запоминаем, кого лайкаем
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❤️ Лайк", callback_data="like"),
                       types.InlineKeyboardButton("👎 Диз", callback_data="find"))
            text = f"🎯 Напарник: {u[1]}\n🎮 Roblox: {u[4]}\n📝 О себе: {u[7]}"
            bot.send_photo(chat_id, u[8], caption=text, reply_markup=markup)
        else:
            bot.send_message(chat_id, "⏳ Никого нет.")

    elif call.data == "like":
        target_id = temp_data.get(chat_id)
        if target_id:
            target_user = cursor.execute('SELECT username FROM users WHERE id = ?', (target_id,)).fetchone()[0]
            my_user = cursor.execute('SELECT username FROM users WHERE id = ?', (chat_id,)).fetchone()[0]
            
            bot.send_message(chat_id, f"✅ Взаимность! Его ник: @{target_user}. Пиши ему!")
            bot.send_message(target_id, f"✅ Тебя лайкнули! Ник автора: @{my_user}.")
            bot.send_message(chat_id, "📩 Можешь отправить сообщение (напиши его текстом в следующем ответе):")
            bot.register_next_step_handler(call.message, lambda m: bot.send_message(target_id, f"📩 От напарника: {m.text}"))

    elif call.data == "profile":
        u = get_user(chat_id)
        text = f"👤 {u[1]}\n🎮 {u[4]}\n📝 {u[7]}"
        if u[8]: bot.send_photo(chat_id, u[8], caption=text)
        else: bot.send_message(chat_id, text)

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🖼 Изменить фото", callback_data="edit_photo"))
        bot.edit_message_text("⚙️ Настройки:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "edit_photo":
        msg = bot.send_message(chat_id, "🖼 Пришли фото:")
        bot.register_next_step_handler(msg, save_photo)

bot.polling(none_stop=True)
