import telebot
from telebot import types

BOT_TOKEN = "8951430631:AAEdfFBzghSDyyQ6vQrwfSJOvPXzD2roBn8"
bot = telebot.TeleBot(BOT_TOKEN)

BOT_USERNAME = "@mentalityZeroAi"
CREATOR_USERNAME = "@wehly"
CLAN_NAME = "Mentality Zero"
SHOP_URL = "https://mentalityzeroshop.tiiny.site/"

user_languages = {}

LOCALES = {
    'ru': {
        'welcome': "Привет! Я {bot_name} — Помощник и любимчик клана {clan_name}! Чем я могу тебе помочь?",
        'who_am_i': "👤 Кто я?",
        'change_lang': "🌐 Сменить язык",
        'open_shop': "🛒 Открыть шоп",
        'about_clan': "🛡️ О клане",
        'about_creator': "👑 Создатель",
        'lang_changed': "Язык успешно изменен на Русский! 🇷🇺",
        'clan_info': "🛡️ Клан *{clan_name}* — это сила, координация и семья. Я всегда готов прийти на помощь каждому бойцу клана!",
        'creator_info': "👑 Мой создатель — {creator}. По всем вопросам пишите ему напрямую!",
        'user_info': "👤 *Ваш профиль:*\n\nИмя: {name}\nID: `{id}`\nЯзык: {lang}\nСтатус: Активный участник ⚡"
    },
    'en': {
        'welcome': "Hello! I am {bot_name} — Assistant and favorite of {clan_name} clan! How can I help you?",
        'who_am_i': "👤 Who am I?",
        'change_lang': "🌐 Change Language",
        'open_shop': "🛒 Open Shop",
        'about_clan': "🛡️ About Clan",
        'about_creator': "👑 Creator",
        'lang_changed': "Language successfully changed to English! 🇺🇸",
        'clan_info': "🛡️ Clan *{clan_name}* is strength, coordination, and family. I am always ready to help every member!",
        'creator_info': "👑 My creator is {creator}. Write to him directly!",
        'user_info': "👤 *Your Profile:*\n\nName: {name}\nID: `{id}`\nLanguage: {lang}\nStatus: Active Member ⚡"
    }
}

def get_main_keyboard(user_id):
    lang = user_languages.get(user_id, 'ru')
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn_who = types.KeyboardButton(LOCALES[lang]['who_am_i'])
    btn_lang = types.KeyboardButton(LOCALES[lang]['change_lang'])
    btn_clan = types.KeyboardButton(LOCALES[lang]['about_clan'])
    btn_creator = types.KeyboardButton(LOCALES[lang]['about_creator'])
    btn_shop = types.KeyboardButton(
        text=LOCALES[lang]['open_shop'],
        web_app=types.WebAppInfo(url=SHOP_URL)
    )
    
    keyboard.add(btn_who, btn_shop)
    keyboard.add(btn_clan, btn_creator)
    keyboard.add(btn_lang)
    return keyboard

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if user_id not in user_languages:
        user_languages[user_id] = 'ru'
    lang = user_languages[user_id]
    welcome_text = LOCALES[lang]['welcome'].format(bot_name=BOT_USERNAME, clan_name=CLAN_NAME)
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(user_id), parse_mode="Markdown")

import openai
import os

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, response.choices[0].message.content)
    except Exception:
        bot.reply_to(message, "Ошибка связи с ИИ. Проверь API-ключ в настройках Railway.")

bot.infinity_polling()
