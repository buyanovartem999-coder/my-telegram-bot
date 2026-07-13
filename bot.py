import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, sex TEXT, 
                   roblox TEXT, discord TEXT, games TEXT, bio TEXT)''')
conn.commit()

# Премиум Unicode-коды (анимируются в Telegram)
# Если хочешь свои кастомные эмодзи из наборов, их нужно вставлять как объекты документов
P_SEARCH = "\U0001FA84" 
P_PROFILE = "\U0001FA99"
P_SETTINGS = "\U0001FA9D"

def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
    u = cursor.fetchone()
    if not u:
        cursor.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)', (chat_id, "None", "0", "None", "None", "None", "None", "None"))
        conn.commit()
        return (chat_id, "None", "0", "None", "None", "None", "None", "None")
    return u

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"{P_SEARCH} Найти", callback_data="find"),
        types.InlineKeyboardButton(f"{P_PROFILE} Профиль", callback_data="profile"),
        types.InlineKeyboardButton(f"{P_SETTINGS} Настройки", callback_data="settings")
    )
    bot.send_message(message.chat.id, "MENU", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ?', (chat_id,))
        users = cursor.fetchall()
        if users:
            u = users[0]
            bot.send_message(chat_id, f"USER: {u[1]} | AGE: {u[2]} | NICK: {u[4]}")
        else:
            bot.send_message(chat_id, "EMPTY")

    elif call.data == "profile":
        u = get_user(chat_id)
        bot.send_message(chat_id, f"NAME: {u[1]} | AGE: {u[2]} | SEX: {u[3]}")

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("EDIT NAME", callback_data="edit_name"))
        bot.edit_message_text("SETTINGS", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "edit_name":
        msg = bot.send_message(chat_id, "ENTER NAME:")
        bot.register_next_step_handler(msg, lambda m: (cursor.execute('UPDATE users SET name = ? WHERE id = ?', (m.text, chat_id)), conn.commit()))

bot.polling(none_stop=True)
