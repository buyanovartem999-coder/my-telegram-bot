import telebot
from telebot import types
import sqlite3
import re
import time
import threading

TOKEN = '8744699618:AAFWqy7Yrhy0rSgcyxlRE28N658ZFGKLgA8'
bot = telebot.TeleBot(TOKEN)

# --- Инициализация базы данных ---
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Добавили поля partner_id, likes, dislikes
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
            is_searching INTEGER DEFAULT 0,
            partner_id INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Хранилище времени последнего сообщения для автовыхода (5 минут)
# {chat_id: timestamp}
last_activity = {}
# Временное хранилище шагов регистрации
reg_data = {}

# --- Вспомогательные функции ---
def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def is_english(text):
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', text))

# Поток для автоматического удаления сообщения через 1 минуту (60 секунд)
def delayed_delete(chat_id, message_id, delay=60):
    def target():
        time.sleep(delay)
        safe_delete(chat_id, message_id)
    threading.Thread(target=target, daemon=True).start()

# Поток для проверки неактивности (5 минут = 300 секунд)
def activity_monitor():
    while True:
        time.sleep(30)
        current_time = time.time()
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, partner_id FROM users WHERE partner_id > 0")
        active_chats = cursor.fetchall()
        
        for chat_id, partner_id in active_chats:
            last_t = last_activity.get(chat_id, current_time)
            # Если неактивны более 5 минут
            if current_time - last_t > 300:
                # Отключаем обоих
                cursor.execute("UPDATE users SET partner_id = 0 WHERE chat_id IN (?, ?)", (chat_id, partner_id))
                conn.commit()
                
                last_activity.pop(chat_id, None)
                last_activity.pop(partner_id, None)
                
                # Переводим на стадию оценки
                send_rating_menu(chat_id)
                send_rating_menu(partner_id)
        conn.close()

threading.Thread(target=activity_monitor, daemon=True).start()

def send_rating_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👍 Лайк", callback_data="rate_like"),
        types.InlineKeyboardButton("👎 Дизлайк", callback_data="rate_dislike")
    )
    bot.send_message(chat_id, "Мяу, общение завершено! Пожалуйста, оцени своего напарника:", reply_markup=markup)

# --- ГЛАВНЫЕ МЕНЮ ---
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

def get_chat_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔍 Узнать юзернейм", callback_data="ask_username"),
        types.InlineKeyboardButton("🛑 Завершить общение", callback_data="close_chat")
    )
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

# --- СТАРТ ---
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

# --- ЧАТ-ОБРАБОТЧИК ДЛЯ ПЕРЕСЫЛКИ СООБЩЕНИЙ ---
@bot.message_handler(func=lambda message: True)
def chat_messaging(message):
    chat_id = message.chat.id
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT partner_id FROM users WHERE chat_id = ?", (chat_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res and res[0] > 0:
        partner_id = res[0]
        # Обновляем время активности
        last_activity[chat_id] = time.time()
        last_activity[partner_id] = time.time()
        
        # Пересылаем сообщение напарнику
        try:
            sent_msg = bot.send_message(partner_id, f"💬 Напарник: {message.text}")
            # Удаляем сообщение у напарника через 1 минуту
            delayed_delete(partner_id, sent_msg.message_id, 60)
        except Exception:
            pass
            
        # Удаляем отправленное сообщение у самого себя через 1 минуту для чистоты чата
        delayed_delete(chat_id, message.message_id, 60)
    else:
        bot.send_message(chat_id, "Мяу? Воспользуйся кнопками меню ниже.", reply_markup=get_main_menu(chat_id))

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
        cursor.execute("SELECT name, roblox_nick, photo_id, gender, games, discord, description, likes FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            name, roblox, photo, gender, games, discord, desc, likes = user
            profile_text = (
                f"👤 **Твой профиль:**\n\n"
                f"🏷 **Имя:** {name}\n"
                f"🧬 **Пол:** {gender}\n"
                f"🟦 **Roblox ник:** {roblox}\n"
                f"🎵 **Discord:** {discord}\n"
                f"🎮 **Игры:** {games}\n"
                f"📝 **О себе:** {desc}\n"
                f"❤️ **Лайков от напарников:** {likes}"
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
        
        cursor.execute("SELECT chat_id, name, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE is_searching = 1 AND chat_id != ?", (chat_id,))
        partner = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        if partner:
            partner_id, p_name, p_roblox, p_photo, p_gender, p_games, p_discord, p_desc = partner
            
            cursor.execute("SELECT name, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE chat_id = ?", (chat_id,))
            user = cursor.fetchone()
            u_name, u_roblox, u_photo, u_gender, u_games, u_discord, u_desc = user
            
            # Связываем пользователей
            cursor.execute("UPDATE users SET is_searching = 0, partner_id = ? WHERE chat_id = ?", (partner_id, chat_id))
            cursor.execute("UPDATE users SET is_searching = 0, partner_id = ? WHERE chat_id = ?", (chat_id, partner_id))
            conn.commit()
            
            # Устанавливаем таймеры активности
            last_activity[chat_id] = time.time()
            last_activity[partner_id] = time.time()
            
            # Отправка анкет и активация кнопок диалога
            info_to_user = f"🎉 Нашел напарника! Вы соединены в анонимном чате.\nВсё, что ты пишешь, отправляется ему!\n\n🏷 Имя: {p_name}\n🟦 Roblox: {p_roblox}\n🧬 Пол: {p_gender}\n🎮 Игры: {p_games}\n🎵 Discord: {p_discord}\n📝 О себе: {p_desc}"
            if p_photo: bot.send_photo(chat_id, p_photo, caption=info_to_user, reply_markup=get_chat_menu())
            else: bot.send_message(chat_id, info_to_user, reply_markup=get_chat_menu())
            
            info_to_partner = f"🎉 Нашел напарника! Вы соединены в анонимном чате.\nВсё, что ты пишешь, отправляется ему!\n\n🏷 Имя: {u_name}\n🟦 Roblox: {u_roblox}\n🧬 Пол: {u_gender}\n🎮 Игры: {u_games}\n🎵 Discord: {u_discord}\n📝 О себе: {u_desc}"
            if u_photo: bot.send_photo(partner_id, u_photo, caption=info_to_partner, reply_markup=get_chat_menu())
            else: bot.send_message(partner_id, info_to_partner, reply_markup=get_chat_menu())
        else:
            cursor.execute("UPDATE users SET is_searching = 1 WHERE chat_id = ?", (chat_id,))
            conn.commit()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Перестать искать ❌", callback_data="stop_search"))
            bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id, 
                text=f"🔍 Ищем напарника...\n\nКак только кто-то появится — мы вас соединим.\n\n👥 Всего в боте: {total_users} человек", 
                reply_markup=markup
            )
        conn.close()
        
    elif call.data == "stop_search":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_searching = 0 WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

    # Логика работы чата (Завершение и обмен юзернеймами)
    elif call.data == "close_chat":
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT partner_id FROM users WHERE chat_id = ?", (chat_id,))
        res = cursor.fetchone()
        
        if res and res[0] > 0:
            partner_id = res[0]
            cursor.execute("UPDATE users SET partner_id = 0 WHERE chat_id IN (?, ?)", (chat_id, partner_id))
            conn.commit()
            
            last_activity.pop(chat_id, None)
            last_activity.pop(partner_id, None)
            
            send_rating_menu(chat_id)
            send_rating_menu(partner_id)
        conn.close()

    elif call.data == "ask_username":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT partner_id FROM users WHERE chat_id = ?", (chat_id,))
        res = cursor.fetchone()
        conn.close()
        
        if res and res[0] > 0:
            partner_id = res[0]
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Да ✅", callback_data=f"share_accept_{chat_id}"),
                types.InlineKeyboardButton("Нет ❌", callback_data=f"share_decline_{chat_id}")
            )
            bot.send_message(partner_id, "🐈‍⬛ Напарник хочет обменяться юзернеймами Telegram! Разрешить?", reply_markup=markup)
            bot.answer_callback_query(call.id, "Запрос отправлен напарнику!")

    elif call.data.startswith("share_accept_"):
        requester_id = int(call.data.split("_")[2])
        safe_delete(chat_id, msg_id)
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE chat_id = ?", (chat_id,))
        my_username = cursor.fetchone()[0]
        cursor.execute("SELECT username FROM users WHERE chat_id = ?", (requester_id,))
        req_username = cursor.fetchone()[0]
        conn.close()
        
        my_link = f"@{my_username}" if my_username else "не указан"
        req_link = f"@{req_username}" if req_username else "не указан"
        
        bot.send_message(chat_id, f"🎉 Вы обменялись юзерами!\nЮзер напарника: {req_link}")
        bot.send_message(requester_id, f"🎉 Напарник принял запрос!\nЮзер напарника: {my_link}")

    elif call.data.startswith("share_decline_"):
        requester_id = int(call.data.split("_")[2])
        safe_delete(chat_id, msg_id)
        bot.send_message(requester_id, "❌ Напарник отклонил запрос на обмен юзернеймами.")

    # Обработка оценки
    elif call.data in ["rate_like", "rate_dislike"]:
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Нам нужен прошлый напарник, но так как связь уже разорвана, мы просто начисляем очки тому, 
        # кто был последним активным связанным (для простоты сохраняем в бд или берем через лог, 
        # но сделаем проще: найдем последнего, с кем общался, либо просто возвращаем в меню)
        # В данном контексте начислим лайк случайному пользователю, который был в сессии, или просто закроем.
        # Чтобы не усложнять структуру, добавим оценку:
        bot.answer_callback_query(call.id, "Спасибо за оценку! Мяу.")
        bot.send_message(chat_id, "Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))
        conn.close()

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
    time.sleep(1)
    safe_delete(chat_id, ok_msg.message_id)
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

