import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, roblox TEXT, 
                   games TEXT, description TEXT, photo_id TEXT)''')
conn.commit()

# Главное меню с кнопками
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Регистрация / Анкетa", callback_data="reg"))
    markup.add(types.InlineKeyboardButton("🔍 Найти напарника", callback_data="find"))
    bot.send_message(message.chat.id, "Привет! Я помогу найти тебе напарников по Roblox. Выбери действие:", reply_markup=markup)

# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "reg":
        bot.send_message(call.message.chat.id, "Как тебя зовут?")
        bot.register_next_step_handler(call.message, get_name)
    elif call.data == "find":
        bot.send_message(call.message.chat.id, "Функция поиска скоро будет готова!")

def get_name(message):
    name = message.text
    bot.send_message(message.chat.id, "Сколько тебе лет?")
    bot.register_next_step_handler(message, get_age, name)

def get_age(message, name):
    age = message.text
    bot.send_message(message.chat.id, "Твой ник в Roblox?")
    bot.register_next_step_handler(message, get_roblox, name, age)

def get_roblox(message, name, age):
    roblox = message.text
    bot.send_message(message.chat.id, "В какие игры играешь?")
    bot.register_next_step_handler(message, get_games, name, age, roblox)

def get_games(message, name, age, roblox):
    games = message.text
    bot.send_message(message.chat.id, "Краткое описание о себе:")
    bot.register_next_step_handler(message, get_desc, name, age, roblox, games)

def get_desc(message, name, age, roblox, games):
    desc = message.text
    bot.send_message(message.chat.id, "Пришли фото для анкеты:")
    bot.register_next_step_handler(message, save_user, name, age, roblox, games, desc)

def save_user(message, name, age, roblox, games, desc):
    photo_id = message.photo[-1].file_id if message.photo else None
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', 
                   (message.chat.id, name, age, roblox, games, desc, photo_id))
    conn.commit()
    bot.send_message(message.chat.id, "Ты успешно в базе! Теперь можешь нажать /start, чтобы увидеть меню.")

bot.polling(none_stop=True)
