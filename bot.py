import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

# Подключение БД
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER, roblox TEXT, games TEXT, description TEXT, photo_id TEXT)')
conn.commit()

# Хранилище временных данных регистрации
user_data = {}

def delete_msg(chat_id, message_id):
    try: bot.delete_message(chat_id, message_id)
    except: pass

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Регистрация", callback_data="reg"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("👥 Группа", url="https://t.me/+GDw01C7KS1xlOTBi"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👋 Привет! Выбирай действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "reg":
        msg = bot.send_message(chat_id, "✍️ Как тебя зовут?")
        user_data[chat_id] = {'msg_ids': [call.message.message_id, msg.message_id]}
        bot.register_next_step_handler(msg, get_name)
    elif call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (chat_id,))
        user = cursor.fetchone()
        if user:
            text = f"👤 Напарник: {user[1]}\nВозраст: {user[2]}\nНик Roblox: {user[3]}\nИгры: {user[4]}\nО себе: {user[5]}"
            if user[6]: bot.send_photo(chat_id, user[6], caption=text)
            else: bot.send_message(chat_id, text)
        else: bot.send_message(chat_id, "😢 Пока никого нет.")

def get_name(message):
    delete_msg(message.chat.id, message.message_id)
    user_data[message.chat.id]['name'] = message.text
    msg = bot.send_message(message.chat.id, "🎂 Сколько тебе лет? (цифрами)")
    user_data[message.chat.id]['msg_ids'].append(msg.message_id)
    bot.register_next_step_handler(msg, get_age)

def get_age(message):
    delete_msg(message.chat.id, message.message_id)
    if not message.text.isdigit() or int(message.text) > 100:
        msg = bot.send_message(message.chat.id, "❌ Введи корректный возраст цифрами:")
        bot.register_next_step_handler(msg, get_age)
        return
    user_data[message.chat.id]['age'] = message.text
    msg = bot.send_message(message.chat.id, "🎮 Твой ник в Roblox? (минимум 3 символа)")
    user_data[message.chat.id]['msg_ids'].append(msg.message_id)
    bot.register_next_step_handler(msg, get_roblox)

def get_roblox(message):
    delete_msg(message.chat.id, message.message_id)
    if len(message.text) < 3:
        msg = bot.send_message(message.chat.id, "❌ Ник слишком короткий. Попробуй еще раз:")
        bot.register_next_step_handler(msg, get_roblox)
        return
    user_data[message.chat.id]['roblox'] = message.text
    msg = bot.send_message(message.chat.id, "🕹 В какие игры играешь?")
    bot.register_next_step_handler(msg, get_games)

def get_games(message):
    delete_msg(message.chat.id, message.message_id)
    user_data[message.chat.id]['games'] = message.text
    msg = bot.send_message(message.chat.id, "📝 Напиши пару слов о себе:")
    bot.register_next_step_handler(msg, get_desc)

def get_desc(message):
    delete_msg(message.chat.id, message.message_id)
    user_data[message.chat.id]['desc'] = message.text
    msg = bot.send_message(message.chat.id, "🖼 Пришли свое фото для анкеты (или напиши 'нет'):")
    bot.register_next_step_handler(msg, save_all)

def save_all(message):
    delete_msg(message.chat.id, message.message_id)
    photo_id = message.photo[-1].file_id if message.photo else None
    u = user_data[message.chat.id]
    cursor.execute('INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?,?)', 
                   (message.chat.id, u['name'], u['age'], u['roblox'], u['games'], u['desc'], photo_id))
    conn.commit()
    for m_id in user_data[message.chat.id]['msg_ids']: delete_msg(message.chat.id, m_id)
    bot.send_message(message.chat.id, "✅ Регистрация завершена! Напиши /start чтобы продолжить.")

bot.polling(none_stop=True)
