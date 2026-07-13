import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

# Подключение базы
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, roblox TEXT, 
                   games TEXT, description TEXT, photo_id TEXT)''')
conn.commit()

# --- МЕНЮ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("👥 Группа", url="https://t.me/+GDw01C7KS1xlOTBi"),
        types.InlineKeyboardButton("💬 Discord", url="https://discord.gg/your_link_here"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👋 Привет! Я твой помощник в поиске напарников. Выбирай действие:", reply_markup=markup)

# --- ЛОГИКА ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data == "find":
        # Система поиска
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (call.message.chat.id,))
        user = cursor.fetchone()
        if user:
            text = f"👤 Напарник найден!\n\nИмя: {user[1]}\nВозраст: {user[2]}\nНик: {user[3]}\nИгры: {user[4]}\nО себе: {user[5]}"
            if user[6]: bot.send_photo(call.message.chat.id, user[6], caption=text)
            else: bot.send_message(call.message.chat.id, text)
        else:
            bot.send_message(call.message.chat.id, "😢 Пока никого нет, попробуй позже!")
    
    elif call.data == "profile":
        cursor.execute('SELECT * FROM users WHERE id = ?', (call.message.chat.id,))
        user = cursor.fetchone()
        if user:
            bot.send_message(call.message.chat.id, f"👤 Твой профиль:\n{user[1]}, {user[2]} лет\nНик: {user[3]}")
        else:
            bot.send_message(call.message.chat.id, "Ты еще не зарегистрирован! Напиши /reg для начала.")

@bot.message_handler(commands=['reg'])
def reg(message):
    bot.send_message(message.chat.id, "Как тебя зовут?")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text
    bot.send_message(message.chat.id, "Сколько лет?")
    bot.register_next_step_handler(message, get_age, name)

def get_age(message, name):
    age = message.text
    bot.send_message(message.chat.id, "Ник в Roblox?")
    bot.register_next_step_handler(message, get_roblox, name, age)

def get_roblox(message, name, age):
    roblox = message.text
    if len(roblox) < 3:
        bot.send_message(message.chat.id, "Увы, ники начинаются от 3 букв. Напиши еще раз:")
        bot.register_next_step_handler(message, get_roblox, name, age)
    else:
        bot.send_message(message.chat.id, "В какие игры играешь?")
        bot.register_next_step_handler(message, get_games, name, age, roblox)

def get_games(message, name, age, roblox):
    games = message.text
    bot.send_message(message.chat.id, "Описание о себе:")
    bot.register_next_step_handler(message, save_user, name, age, roblox, games)

def save_user(message, name, age, roblox, games):
    desc = message.text
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', 
                   (message.chat.id, name, age, roblox, games, desc, None))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Готово! Ты в базе.")

bot.polling(none_stop=True)
