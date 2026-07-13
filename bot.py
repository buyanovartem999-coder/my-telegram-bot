import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot("8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8")

# Подключение БД
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (id INTEGER PRIMARY KEY, name TEXT, age TEXT, roblox TEXT, 
                   discord TEXT, games TEXT, desc TEXT, photo_id TEXT)''')
conn.commit()

# Хранилище: что сейчас делает юзер {chat_id: {'state': '...', 'msg_to_delete': []}}
user_state = {}

def delete_prev_msgs(chat_id):
    if chat_id in user_state:
        for msg_id in user_state[chat_id].get('msgs', []):
            try: bot.delete_message(chat_id, msg_id)
            except: pass
        user_state[chat_id]['msgs'] = []

@bot.message_handler(commands=['start'])
def start(message):
    delete_prev_msgs(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✨ Найти", callback_data="find"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        types.InlineKeyboardButton("📢 Канал", url="https://t.me/+RrmwMGGlUuUyNTUy"),
        types.InlineKeyboardButton("🆘 Поддержка", url="https://t.me/wehly")
    )
    msg = bot.send_message(message.chat.id, "👋 Привет! Главное меню:", reply_markup=markup)
    user_state[message.chat.id] = {'msgs': [msg.message_id]}

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    if call.data == "find":
        cursor.execute('SELECT * FROM users WHERE id != ? ORDER BY RANDOM() LIMIT 1', (chat_id,))
        user = cursor.fetchone()
        if user:
            text = f"👤 Напарник: {user[1]}\n🎂 Возраст: {user[2]}\n🎮 Roblox: {user[3]}\n💬 Discord: {user[4]}\n🕹 Игры: {user[5]}\n📝 О себе: {user[6]}"
            if user[7]: bot.send_photo(chat_id, user[7], caption=text)
            else: bot.send_message(chat_id, text)
        else: bot.send_message(chat_id, "😢 Пока никого нет.")
    
    elif call.data == "settings":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✏️ Имя", callback_data="edit_name"),
            types.InlineKeyboardButton("✏️ Возраст", callback_data="edit_age"),
            types.InlineKeyboardButton("✏️ Roblox", callback_data="edit_roblox"),
            types.InlineKeyboardButton("✏️ Discord", callback_data="edit_discord"),
            types.InlineKeyboardButton("✏️ Фото", callback_data="edit_photo"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="start")
        )
        bot.edit_message_text("⚙️ Что именно изменить?", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("edit_"):
        field = call.data.split("_")[1]
        user_state[chat_id]['editing_field'] = field
        msg = bot.send_message(chat_id, f"Введите новое значение для {field}:")
        user_state[chat_id]['msgs'].append(msg.message_id)
        bot.register_next_step_handler(msg, process_edit)

    elif call.data == "start":
        start(call.message)

def process_edit(message):
    chat_id = message.chat.id
    field = user_state[chat_id].get('editing_field')
    val = message.text
    
    # Валидация
    if field == "age" and not val.isdigit():
        msg = bot.send_message(chat_id, "❌ Возраст должен быть числом! Попробуй еще раз:")
        return bot.register_next_step_handler(msg, process_edit)
    if field == "roblox" and len(val) < 3:
        msg = bot.send_message(chat_id, "❌ Ник слишком короткий! (минимум 3)")
        return bot.register_next_step_handler(msg, process_edit)

    cursor.execute(f'UPDATE users SET {field} = ? WHERE id = ?', (val, chat_id))
    conn.commit()
    bot.send_message(chat_id, f"✅ {field} успешно обновлено! Напиши /start")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if user_state.get(chat_id, {}).get('editing_field') == 'photo':
        photo_id = message.photo[-1].file_id
        cursor.execute('UPDATE users SET photo_id = ? WHERE id = ?', (photo_id, chat_id))
        conn.commit()
        bot.send_message(chat_id, "✅ Фото обновлено! Напиши /start")
    else:
        bot.send_message(chat_id, "Я сейчас не жду фото. Используй настройки.")

bot.polling(none_stop=True)

