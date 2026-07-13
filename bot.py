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

# Хранилище состояний
user_state = {}

def clear_chat(chat_id):
    """Удаляет все сообщения, которые бот успел отправить"""
    if chat_id in user_state and 'msgs' in user_state[chat_id]:
        for msg_id in user_state[chat_id]['msgs']:
            try: bot.delete_message(chat_id, msg_id)
            except: pass
        user_state[chat_id]['msgs'] = []

@bot.message_handler(commands=['start'])
def start(message):
    clear_chat(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    msg = bot.send_message(message.chat.id, "👋 Привет! Выбирай действие:", reply_markup=markup)
    user_state[message.chat.id] = {'msgs': [msg.message_id]}

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (chat_id,))
        user = cursor.fetchone()
        if user:
            text = f"👤 Напарник: {user[1]}\nВозраст: {user[2]}\nНик: {user[3]}\nИгры: {user[4]}\nО себе: {user[5]}"
            if user[6]: bot.send_photo(chat_id, user[6], caption=text)
            else: bot.send_message(chat_id, text)
        else: bot.send_message(chat_id, "😢 Пока никого нет.")
    
    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✏️ Изменить Имя", callback_data="edit_name"),
                   types.InlineKeyboardButton("✏️ Изменить Ник Roblox", callback_data="edit_roblox"),
                   types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.edit_message_text("⚙️ Что меняем?", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        user_state[chat_id]['edit'] = field
        msg = bot.send_message(chat_id, "Введите новое значение:")
        user_state[chat_id]['msgs'].append(msg.message_id)
        bot.register_next_step_handler(msg, save_edit)

    elif call.data == "back":
        start(call.message)

def save_edit(message):
    field = user_state[message.chat.id]['edit']
    val = message.text
    if field == "roblox" and len(val) < 3:
        bot.send_message(message.chat.id, "❌ Ник слишком короткий!")
        return
    cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (val, message.chat.id))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Обновлено! Напиши /start")

# Регистрация (упрощенная, чтобы не ломалась)
@bot.message_handler(commands=['reg'])
def reg_start(message):
    msg = bot.send_message(message.chat.id, "Введите Имя:")
    user_state[message.chat.id] = {'msgs': [msg.message_id], 'data': {}}
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    user_state[message.chat.id]['data']['name'] = message.text
    msg = bot.send_message(message.chat.id, "Введите Возраст (цифрами):")
    user_state[message.chat.id]['msgs'].append(msg.message_id)
    bot.register_next_step_handler(msg, get_age)

def get_age(message):
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "Только цифры!")
        bot.register_next_step_handler(msg, get_age)
        return
    user_state[message.chat.id]['data']['age'] = message.text
    msg = bot.send_message(message.chat.id, "Введите ник Roblox (минимум 3 символа):")
    user_state[message.chat.id]['msgs'].append(msg.message_id)
    bot.register_next_step_handler(msg, get_roblox)

def get_roblox(message):
    if len(message.text) < 3:
        msg = bot.send_message(message.chat.id, "Слишком короткий ник!")
        bot.register_next_step_handler(msg, get_roblox)
        return
    user_state[message.chat.id]['data']['roblox'] = message.text
    cursor.execute('INSERT OR REPLACE INTO users (id, name, age, roblox) VALUES (?,?,?,?)', 
                   (message.chat.id, user_state[message.chat.id]['data']['name'], 
                    user_state[message.chat.id]['data']['age'], message.text))
    conn.commit()
    clear_chat(message.chat.id)
    bot.send_message(message.chat.id, "✅ Успешно! Напиши /start для доступа к меню.")

bot.polling(none_stop=True)
