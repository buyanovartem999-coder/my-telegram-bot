import telebot
from telebot import types
import sqlite3
import re
import time

# Твой токен вставлен
TOKEN = '8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8'
bot = telebot.TeleBot(TOKEN)

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            roblox_nick TEXT,
            photo_id TEXT,
            gender TEXT,
            games TEXT,
            discord TEXT,
            description TEXT,
            notifications INTEGER DEFAULT 1,
            is_searching INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Вспомогательные функции ---
def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def is_english(text):
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', text))

# Временное хранилище шагов регистрации
reg_data = {}

# --- ГЛАВНЫЕ МЕНЮ (Генераторы кнопок) ---
def get_main_menu(chat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT notifications FROM users WHERE chat_id = ?", (chat_id,))
    res = cursor.fetchone()
    conn.close()
    
    notif_status = "вкл" if res and res[0] == 1 else "выкл"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_search = types.InlineKeyboardButton("👻 Найти напарника", callback_data="find_teammate")
    btn_profile = types.InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile")
    btn_settings = types.InlineKeyboardButton("⚙️ Настройки", callback_data="open_settings")
    btn_notif = types.InlineKeyboardButton(f"🔔 Уведомления о поиске: {notif_status}", callback_data="toggle_notif")
    btn_news = types.InlineKeyboardButton("📣 Канал новостей ↗️", url="https://t.me/TheMeowMeowNews")
    btn_group = types.InlineKeyboardButton("👥 Наша группа ↗️", url="https://t.me/MeowMeowNaparniki")
    btn_support = types.InlineKeyboardButton("💬 Поддержка ↗️", url="https://t.me/MeowMeowNaparniki")
    
    markup.add(btn_search)
    markup.add(btn_profile, btn_settings)
    markup.add(btn_notif)
    markup.add(btn_news, btn_group)
    markup.add(btn_support)
    return markup

def get_settings_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Редактировать профиль", callback_data="edit_profile"),
        types.InlineKeyboardButton("🛑 Заблокированные", callback_data="blocked_users"),
        types.InlineKeyboardButton("← Назад", callback_data="back_to_main")
    )
    return markup

def get_edit_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(" Pepe Имя", callback_data="change_name"),
        types.InlineKeyboardButton("⏳ Возраст", callback_data="change_age_stub"),
        types.InlineKeyboardButton("🧬 Пол", callback_data="change_gender"),
        types.InlineKeyboardButton("📸 Изменить фото", callback_data="change_photo"),
        types.InlineKeyboardButton("🟦 Roblox", callback_data="change_roblox"),
        types.InlineKeyboardButton("🎵 Discord", callback_data="change_discord"),
        types.InlineKeyboardButton("🎮 Игры", callback_data="change_games")
    )
    markup.add(types.InlineKeyboardButton("📝 О себе", callback_data="change_desc"))
    markup.add(types.InlineKeyboardButton("← Назад", callback_data="open_settings"))
    return markup

# --- СТАРТ И РЕГИСТРАЦИЯ ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id) 
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE chat_id = ?", (chat_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        bot.send_message(chat_id, f"С возвращением, {user[0]}!\nЧто делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Начать регистрацию 👾", callback_data="start_reg"))
        bot.send_message(chat_id, "🐈‍⬛ Мяу, приветики это Roblox meow поиск напарников!!\n\nПеред началом создай профиль.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handlers(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    
    if call.data == "start_reg":
        safe_delete(chat_id, msg_id)
        next_msg = bot.send_message(chat_id, "Как к тебе обращаться?")
        reg_data[chat_id] = {'last_bot_msg': next_msg.message_id}
        bot.register_next_step_handler(next_msg, reg_step_name)
        
    elif call.data == "open_settings":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⚙️ Настройки", reply_markup=get_settings_menu())
        
    elif call.data == "back_to_main":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))
        
    elif call.data == "edit_profile":
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="✏️ Что хочешь изменить?", reply_markup=get_edit_menu())
        
    elif call.data == "blocked_users":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("← Назад", callback_data="open_settings"))
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="Мяу, пока что нету заблокированных 🐈‍⬛", reply_markup=markup)
        
    elif call.data == "toggle_notif":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT notifications FROM users WHERE chat_id = ?", (chat_id,))
        current = cursor.fetchone()[0]
        new_status = 0 if current == 1 else 1
        cursor.execute("UPDATE users SET notifications = ? WHERE chat_id = ?", (new_status, chat_id))
        conn.commit()
        conn.close()
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=get_main_menu(chat_id))
        
    elif call.data in ["reg_male", "reg_female"]:
        gender = "Мужской 🧎‍♂️🐈‍⬛" if call.data == "reg_male" else "Женский 🧎‍♀️🐈‍⬛"
        reg_data[chat_id]['gender'] = gender
        safe_delete(chat_id, msg_id)
        next_msg = bot.send_message(chat_id, "В какие игры ты играешь? (Например: Blade ball, brookhaven итд...)")
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_games)

    elif call.data == "my_profile":
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            name, roblox, photo, gender, games, discord, desc = user
            profile_text = (
                f"👤 **Твой профиль:**\n\n"
                f"🏷 **Имя:** {name}\n"
                f"🧬 **Пол:** {gender}\n"
                f"🟦 **Roblox ник:** {roblox}\n"
                f"🎵 **Discord:** {discord}\n"
                f"🎮 **Игры:** {games}\n"
                f"📝 **О себе:** {desc}"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("← В главное меню", callback_data="delete_and_main"))
            
            if photo:
                bot.send_photo(chat_id, photo, caption=profile_text, parse_mode="Markdown", reply_markup=markup)
            else:
                bot.send_message(chat_id, profile_text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, "Анкета не найдена. Напиши /start для регистрации.")

    elif call.data == "delete_and_main":
        safe_delete(chat_id, msg_id)
        bot.send_message(chat_id, "Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

    elif call.data == "find_teammate":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_searching = 1 WHERE chat_id = ?", (chat_id,))
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Перестать искать ❌", callback_data="stop_search"))
        
        bot.edit_message_text(
            chat_id=chat_id, message_id=msg_id, 
            text=f"🔍 Ищем напарника...\n\nКак только кто-то появится — мы вас соединим.\n\n"
                 f"ℹ️ Если в очереди кто-то есть, но матч не происходит — с этим человеком ты общался недавно.\n\n"
                 f"👥 Всего в боте: {total_users} человек", 
            reply_markup=markup
        )
        
    elif call.data == "stop_search":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_searching = 0 WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

    # Кнопки изменения данных профиля
    elif call.data == "change_name":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Мяу, введи новое имя как к тебе обращаться! 🐈‍⬛")
        bot.register_next_step_handler(m, lambda msg: update_field(msg, "name", m.message_id))
    elif call.data == "change_roblox":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Введи новый ник в Roblox:")
        bot.register_next_step_handler(m, lambda msg: update_field(msg, "roblox_nick", m.message_id))
    elif call.data == "change_discord":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Введи новый Discord:")
        bot.register_next_step_handler(m, lambda msg: update_field(msg, "discord", m.message_id))
    elif call.data == "change_games":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Введи новые игры через запятую:")
        bot.register_next_step_handler(m, lambda msg: update_field(msg, "games", m.message_id))
    elif call.data == "change_desc":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Введи новое описание о себе (до 100 символов):")
        bot.register_next_step_handler(m, lambda msg: update_field(msg, "description", m.message_id))
    elif call.data == "change_gender":
        safe_delete(chat_id, msg_id)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Мужской 🧎‍♂️🐈‍⬛", callback_data="set_gender_male"),
                   types.InlineKeyboardButton("Женский 🧎‍♀️🐈‍⬛", callback_data="set_gender_female"))
        bot.send_message(chat_id, "Выбери свой пол:", reply_markup=markup)
    elif call.data in ["set_gender_male", "set_gender_female"]:
        safe_delete(chat_id, msg_id)
        gender = "Мужской 🧎‍♂️🐈‍⬛" if call.data == "set_gender_male" else "Женский 🧎‍♀️🐈‍⬛"
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET gender = ? WHERE chat_id = ?", (gender, chat_id))
        conn.commit()
        conn.close()
        bot.send_message(chat_id, "✏️ Что хочешь изменить?", reply_markup=get_edit_menu())
    elif call.data == "change_photo":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Отправь новое фото для твоего профиля: 📸")
        bot.register_next_step_handler(m, update_photo, m.message_id)

# --- ПОШАГОВАЯ РЕГИСТРАЦИЯ ---
def reg_step_name(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id) 
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg']) 
    reg_data[chat_id]['name'] = message.text
    next_msg = bot.send_message(chat_id, "Какой твой ник в Roblox? 🕹")
    reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
    bot.register_next_step_handler(next_msg, reg_step_roblox)

def reg_step_roblox(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
    nick = message.text
    if len(nick) < 3:
        next_msg = bot.send_message(chat_id, "Ники лишь от 3 букв!! 👾")
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_roblox)
        return
    if not is_english(nick):
        next_msg = bot.send_message(chat_id, "Roblox ники изначально Английские!!")
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_roblox)
        return
    reg_data[chat_id]['roblox_nick'] = nick
    next_msg = bot.send_message(chat_id, "Отправь фото своего скина, или то что связано с тобой!! 👾")
    reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
    bot.register_next_step_handler(next_msg, reg_step_photo)

def reg_step_photo(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
    if not message.photo:
        next_msg = bot.send_message(chat_id, "Принимаются лишь фото!!!")
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_photo)
        return
    reg_data[chat_id]['photo_id'] = message.photo[-1].file_id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Мужской 🧎‍♂️🐈‍⬛", callback_data="reg_male"),
               types.InlineKeyboardButton("Женский 🧎‍♀️🐈‍⬛", callback_data="reg_female"))
    next_msg = bot.send_message(chat_id, "Какой твой пол? Кошка/кот", reply_markup=markup)
    reg_data[chat_id]['last_bot_msg'] = next_msg.message_id

def reg_step_games(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
    reg_data[chat_id]['games'] = message.text
    next_msg = bot.send_message(chat_id, "Какой твой дискорд? Напиши 'нет' если нету 🐈‍⬛")
    reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
    bot.register_next_step_handler(next_msg, reg_step_discord)

def reg_step_discord(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
    dc = message.text
    if dc.lower() != "нет" and not is_english(dc):
        next_msg = bot.send_message(chat_id, "Дискорд должен быть на английском или напиши 'нет'!")
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_discord)
        return
    reg_data[chat_id]['discord'] = dc
    next_msg = bot.send_message(chat_id, "Хочешь ли ты добавить свое описание? Напиши 'нет' если не хочешь (до 100 символов)")
    reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
    bot.register_next_step_handler(next_msg, reg_step_desc)

def reg_step_desc(message):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
    desc = message.text
    if len(desc) > 100:
        next_msg = bot.send_message(chat_id, "Описание слишком длинное! Должно быть до 100 символов.")
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_desc)
        return
    reg_data[chat_id]['description'] = desc
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (chat_id, username, name, roblox_nick, photo_id, gender, games, discord, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, message.from_user.username, reg_data[chat_id]['name'], reg_data[chat_id]['roblox_nick'], 
          reg_data[chat_id]['photo_id'], reg_data[chat_id]['gender'], reg_data[chat_id]['games'], 
          reg_data[chat_id]['discord'], reg_data[chat_id]['description']))
    conn.commit()
    conn.close()
    ok_msg = bot.send_message(chat_id, "Хорошо")
    time.sleep(2)
    safe_delete(chat_id, ok_msg.message_id)
    end_msg = bot.send_message(chat_id, "Анкета закончена. 🐈‍⬛")
    time.sleep(2)
    safe_delete(chat_id, end_msg.message_id)
    bot.send_message(chat_id, f"С возвращением, {reg_data[chat_id]['name']}!\nЧто делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))
    del reg_data[chat_id]

# --- ОБНОВЛЕНИЕ ПОЛЕЙ В НАСТРОЙКАХ ---
def update_field(message, field_name, bot_msg_id):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, bot_msg_id)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {field_name} = ? WHERE chat_id = ?", (message.text, chat_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✏️ Что хочешь изменить?", reply_markup=get_edit_menu())

def update_photo(message, bot_msg_id):
    chat_id = message.chat.id
    safe_delete(chat_id, message.message_id)
    safe_delete(chat_id, bot_msg_id)
    
    if not message.photo:
        m = bot.send_message(chat_id, "Мяу, нужно отправить именно фото!")
        bot.register_next_step_handler(m, update_photo, m.message_id)
        return
        
    photo_id = message.photo[-1].file_id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET photo_id = ? WHERE chat_id = ?", (photo_id, chat_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✏️ Что хочешь изменить?", reply_markup=get_edit_menu())

if __name__ == '__main__':
    print("Бот успешно запущен и готов к работе!")
    bot.polling(none_stop=True)

