import telebot
from telebot import types
import os
import google.generativeai as genai

bot = telebot.TeleBot("8951430631:AAEdtfBzghSDyyQ6vQrwfSJOvPXzD2roBn8")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👤 Кто я?", "🛒 Открыть шоп")
    kb.add("🛡 О клане", "👑 Создатель")
    kb.add("🌐 Сменить язык")
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Выбери действие:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.text in ["👤 Кто я?", "🛒 Открыть шоп", "🛡 О клане", "👑 Создатель", "🌐 Сменить язык"]:
        bot.reply_to(message, f"Ты нажал: {message.text}")
    else:
        try:
            response = model.generate_content(message.text)
            bot.reply_to(message, response.text)
        except Exception:
            bot.reply_to(message, "Ошибка связи с ИИ. Проверь API-ключ.")

print("Бот запущен...")
bot.infinity_polling()
