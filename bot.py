import telebot
import sqlite3

# Твой токен
bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

# Подключаем базу данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
# Добавили колонки для игр, описания и фото
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, roblox TEXT, 
                   games TEXT, description TEXT, photo_id TEXT)''')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я с радостью помогу тебе найти отличного напарника для игры в Roblox. Давай начнем регистрацию — напиши /reg")

@bot.message_handler(commands=['reg'])
def reg(message):
    bot.send_message(message.chat.id, "Как тебя зовут?")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text
    bot.send_message(message.chat.id, "Сколько тебе лет?")
    bot.register_next_step_handler(message, get_age, name)

def get_age(message, name):
    age = message.text
    bot.send_message(message.chat.id, "Какой у тебя ник в Roblox?")
    bot.register_next_step_handler(message, get_roblox, name, age)

def get_roblox(message, name, age):
    roblox = message.text
    bot.send_message(message.chat.id, "В какие игры в Roblox ты играешь? (например: Blox Fruits, Adopt Me)")
    bot.register_next_step_handler(message, get_games, name, age, roblox)

def get_games(message, name, age, roblox):
    games = message.text
    bot.send_message(message.chat.id, "Напиши краткое описание о себе:")
    bot.register_next_step_handler(message, get_desc, name, age, roblox, games)

def get_desc(message, name, age, roblox, games):
    desc = message.text
    bot.send_message(message.chat.id, "Пришли фото (или любой стикер/картинку), которое будет в твоей анкете:")
    bot.register_next_step_handler(message, save_user, name, age, roblox, games, desc)

def save_user(message, name, age, roblox, games, desc):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id # Берем самое качественное фото
    
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?)', 
                   (message.chat.id, name, age, roblox, games, desc, photo_id))
    conn.commit()
    bot.send_message(message.chat.id, "Ура! Ты успешно зарегистрирован и готов к поиску напарников!")

bot.polling(none_stop=True)
