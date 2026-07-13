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

# Премиум эмодзи ID
E_SEARCH = "✨" # ID: 5368324170671434786
E_PROFILE = "👤"
E_SETTINGS = "⚙️"
E_MAN = "👨"
E_WOMAN = "👩"

def get_user(chat_id):
    cursor.execute('SELECT * FROM users WHERE id = ?', (chat_id,))
    u = cursor.fetchone()
    if not u:
        cursor.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?,?)', (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе"))
        conn.commit()
        return (chat_id, "Не задано", "0", "Не задано", "Ник", "Discord", "Игры", "О себе")
    return u

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(f"✨ Найти напарника", callback_data="find"),
        types.InlineKeyboardButton(f"👤 Мой профиль", callback_data="profile"),
        types.InlineKeyboardButton(f"⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton(f"📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton(f"🆘 Поддержка", url="https://t.me/wehly")
    )
    bot.send_message(message.chat.id, "👑 Добро пожаловать!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (chat_id,))
        u = cursor.fetchone()
        if u:
            bot.send_message(chat_id, f"🎯 Напарник: {u[1]}\n💎 Возраст: {u[2]}\n🛡 Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}\n📝 О себе: {u[7]}")
        else:
            bot.send_message(chat_id, "⏳ Никого нет.")
            
    elif call.data == "profile":
        u = get_user(chat_id)
        bot.send_message(chat_id, f"👤 Имя: {u[1]}\n💎 Возраст: {u[2]}\n🛡 Пол: {u[3]}\n🎮 Roblox: {u[4]}\n💬 Discord: {u[5]}\n🕹 Игры: {u[6]}\n📝 О себе: {u[7]}")

    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        fields = [("👤 Имя", "name"), ("💎 Возраст", "age"), ("🛡 Пол", "sex"), ("🎮 Roblox", "roblox"), ("💬 Discord", "discord"), ("🕹 Игры", "games"), ("📝 О себе", "bio")]
        for t, k in fields: markup.add(types.InlineKeyboardButton(f"✏️ {t}", callback_data=f"edit_{k}"))
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="start"))
        bot.edit_message_text("⚙️ Выберите параметр для изменения:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        if field == "sex":
            m = types.InlineKeyboardMarkup()
            m.add(types.InlineKeyboardButton("👨 Man", callback_data="set_sex_Man"), types.InlineKeyboardButton("👩 Woman", callback_data="set_sex_Woman"))
            bot.send_message(chat_id, "🛡 Выберите пол:", reply_markup=m)
        else:
            msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
            bot.register_next_step_handler(msg, lambda m: (cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (m.text, chat_id)), conn.commit(), bot.send_message(chat_id, "✅ Обновлено.")))

    elif call.data.startswith("set_sex_"):
        cursor.execute('UPDATE users SET sex = ? WHERE id = ?', (call.data.split("_")[2], chat_id))
        conn.commit()
        bot.send_message(chat_id, "✅ Пол изменен.")
    
    elif call.data == "start":
        start(call.message)

bot.polling(none_stop=True)
