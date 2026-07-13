import telebot
import sqlite3

# Сюда в кавычки вставь токен от нового бота из BotFather
bot = telebot.TeleBot("ВСТАВЬ_СЮДА_ТОКЕН")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT, age TEXT, roblox TEXT)')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Напиши /reg для регистрации.")

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
    bot.send_message(message.chat.id, "Твой ник в Roblox?")
    bot.register_next_step_handler(message, save_user, name, age)

def save_user(message, name, age):
    roblox = message.text
    cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (message.chat.id, name, age, roblox))
    conn.commit()
    bot.send_message(message.chat.id, "Отлично! Ты успешно зарегистрирован в базе.")

bot.polling(none_stop=True)
