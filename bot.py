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

def generate_ai_response(user_message, user_name):
    prompt = user_message.lower()
    if any(x in prompt for x in ["привет", "hello", "ку", "хай"]):
        return f"Привет, {user_name}! Рад тебя слышать. Я твой верный Mentality Zero ИИ-помощник! 👾"
    elif any(x in prompt for x in ["создатель", "wehly", "вехли", "автор"]):
        return f"Мой создатель — легендарный {CREATOR_USERNAME}! Он создал меня, чтобы я помогал нашему клану и развивал проект Mentality Zero."
    elif any(x in prompt for x in ["клан", "clan", "mentality"]):
        return f"Клан {CLAN_NAME} — это топ-1! Мы лучшие, и я сделаю всё, чтобы помочь ребятам доминировать!"
    elif any(x in prompt for x in ["кто ты", "что за бот"]):
        return f"Я — {BOT_USERNAME}, официальный бот-помощник и любимчик великого клана {CLAN_NAME}! Умею общаться и открывать наш фирменный шоп."
    elif any(x in prompt for x in ["токен", "купить", "infinity"]):
        return f"О! Если ты хочешь приобрести статус Infinity или токены, нажми кнопку 'Открыть шоп' в меню или напиши напрямую {CREATOR_USERNAME}."
    return f"Я, {BOT_USERNAME}, согласен с тобой! Как любимчик клана {CLAN_NAME}, я всегда на связи. Что еще обсудим?"

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ru')
    text = message.text

    if text in [LOCALES['ru']['who_am_i'], LOCALES['en']['who_am_i']]:
        name = message.from_user.first_name
        user_info = LOCALES[lang]['user_info'].format(
            name=name, id=user_id, lang="Русский 🇷🇺" if lang == 'ru' else "English 🇺🇸"
        )
        bot.send_message(message.chat.id, user_info, parse_mode="Markdown")
    elif text in [LOCALES['ru']['about_clan'], LOCALES['en']['about_clan']]:
        clan_info = LOCALES[lang]['clan_info'].format(clan_name=CLAN_NAME)
        bot.send_message(message.chat.id, clan_info, parse_mode="Markdown")
    elif text in [LOCALES['ru']['about_creator'], LOCALES['en']['about_creator']]:
        creator_info = LOCALES[lang]['creator_info'].format(creator=CREATOR_USERNAME)
        bot.send_message(message.chat.id, creator_info, parse_mode="Markdown")
    elif text in [LOCALES['ru']['change_lang'], LOCALES['en']['change_lang']]:
        new_lang = 'en' if lang == 'ru' else 'ru'
        user_languages[user_id] = new_lang
        bot.send_message(message.chat.id, LOCALES[new_lang]['lang_changed'], reply_markup=get_main_keyboard(user_id))
    else:
        ai_reply = generate_ai_response(text, message.from_user.first_name)
        bot.send_message(message.chat.id, ai_reply)

if __name__ == "__main__":
    bot.infinity_polling()
