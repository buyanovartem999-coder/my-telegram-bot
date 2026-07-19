import telebot
from telebot import types
import sqlite3
import re
import time
import threading
from datetime import datetime

# Твой токен
TOKEN = '8744699618:AAGN3JQKcOGWmXnhnIu4XHauCBFsN7eHrnk'
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
            age TEXT,
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
            dislikes INTEGER DEFAULT 0,
            join_date TEXT,
            msg_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

last_activity = {}
reg_data = {}
last_message_id = {}
sent_notifications = {} 
who_ami_cooldown = {} 
stats_cooldown = {}

def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

def is_english(text):
    return bool(re.match(r'^[a-zA-Z0-9_\-]+$', text))

def delayed_delete(chat_id, message_id, delay=60):
    def target():
        time.sleep(delay)
        if last_message_id.get(chat_id) == message_id:
            return
        safe_delete(chat_id, message_id)
    threading.Thread(target=target, daemon=True).start()

def step_transition(chat_id, user_msg_id, bot_msg_id, next_text, next_step_func, reply_markup=None):
    if user_msg_id:
        delayed_delete(chat_id, user_msg_id, 5)
    if bot_msg_id:
        safe_delete(chat_id, bot_msg_id)
        
    next_msg = bot.send_message(chat_id, next_text, reply_markup=reply_markup)
    if chat_id in reg_data:
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
    
    if next_step_func:
        bot.register_next_step_handler(next_msg, next_step_func)

def get_days_word(days):
    if days % 10 == 1 and days % 100 != 11:
        return "день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return "дня"
    else:
        return "дней"

# --- ФОНОВЫЙ МОНИТОР ---
def global_monitor():
    while True:
        time.sleep(10)
        current_time = time.time()
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT chat_id, partner_id FROM users WHERE partner_id > 0")
            active_chats = cursor.fetchall()
            for chat_id, partner_id in active_chats:
                last_t = last_activity.get(chat_id, current_time)
                if current_time - last_t > 300:
                    cursor.execute("UPDATE users SET partner_id = 0 WHERE chat_id IN (?, ?)", (chat_id, partner_id))
                    conn.commit()
                    last_activity.pop(chat_id, None)
                    last_activity.pop(partner_id, None)
                    send_rating_menu(chat_id, partner_id)
                    send_rating_menu(partner_id, chat_id)
            
            cursor.execute("SELECT chat_id FROM users WHERE is_searching = 1")
            searching_users = [row[0] for row in cursor.fetchall()]
            
            if searching_users:
                cursor.execute("SELECT chat_id FROM users WHERE notifications = 1 AND is_searching = 0 AND partner_id = 0")
                users_to_notify = [row[0] for row in cursor.fetchall()]
                
                for target_id in users_to_notify:
                    if target_id not in sent_notifications:
                        sent_notifications[target_id] = []
                        
                    for searcher_id in searching_users:
                        if target_id != searcher_id and searcher_id not in sent_notifications[target_id]:
                            markup = types.InlineKeyboardMarkup(row_width=2)
                            markup.add(
                                types.InlineKeyboardButton("Начать общение 🎮", callback_data=f"notif_connect_{searcher_id}"),
                                types.InlineKeyboardButton("Пропустить ⏭️", callback_data="notif_skip")
                            )
                            bot.send_message(
                                target_id, 
                                "🐈‍⬛ Мяу! Кто-то прямо сейчас ищет напарника по Роблоксу! Хочешь подключиться?", 
                                reply_markup=markup
                            )
                            sent_notifications[target_id].append(searcher_id)
            conn.close()
        except Exception as e:
            print(f"Ошибка в мониторе: {e}")

threading.Thread(target=global_monitor, daemon=True).start()

def send_rating_menu(chat_id, partner_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👍 Лайк", callback_data=f"rate_like_{partner_id}"),
        types.InlineKeyboardButton("👎 Дизлайк", callback_data=f"rate_dislike_{partner_id}")
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
    markup.add(types.InlineKeyboardButton("👻 Найти напарника", callback_data="find_teammate"))
    markup.add(types.InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile"),
               types.InlineKeyboardButton("⚙️ Настройки", callback_data="open_settings"))
    markup.add(types.InlineKeyboardButton(f"🔔 Уведомления о поиске: {notif_status}", callback_data="toggle_notif"))
    markup.add(types.InlineKeyboardButton("📣 Канал новостей ↗️", url="https://t.me/TheMeowMeowNews"),
               types.InlineKeyboardButton("👥 Наша группа ↗️", url="https://t.me/MeowMeowNaparniki"))
    markup.add(types.InlineKeyboardButton("💬 Поддержка ↗️", url="https://t.me/wehly"))
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
        types.InlineKeyboardButton("← Назад", callback_data="back_to_main")
    )
    return markup

def get_edit_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("⚙️ Имя", callback_data="change_name"),
        types.InlineKeyboardButton("⏳ Возраст", callback_data="change_age"),
        types.InlineKeyboardButton("🧬 Пол", callback_data="change_gender"),
        types.InlineKeyboardButton("📸 Изменить фото", callback_data="change_photo"),
        types.InlineKeyboardButton("🟦 Roblox", callback_data="change_roblox"),
        types.InlineKeyboardButton("🎵 Discord", callback_data="change_discord"),
        types.InlineKeyboardButton("🎮 Игры", callback_data="change_games")
    )
    markup.add(types.InlineKeyboardButton("📝 О себе", callback_data="change_desc"))
    markup.add(types.InlineKeyboardButton("← Назад", callback_data="open_settings"))
    return markup

# --- ОБРАБОТЧИКИ КОМАНД ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type != 'private':
        return

    chat_id = message.chat.id
    delayed_delete(chat_id, message.message_id, 5)
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, age FROM users WHERE chat_id = ?", (chat_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[1]: 
        bot.send_message(chat_id, f"С возвращением, {user[0]}!\nЧто делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))
    else:
        if chat_id in reg_data:
            del reg_data[chat_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Начать регистрацию 👾", callback_data="start_reg"))
        bot.send_message(chat_id, "🐈‍⬛ Мяу, приветики это Roblox meow поиск напарников!!\n\nПеред началом создай профиль.", reply_markup=markup)

# --- РЕАКЦИИ И КОМАНДЫ В ГРУППАХ ---
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_group_messages(message):
    if not message.text:
        return
        
    text_lower = message.text.lower()
    user_id = message.from_user.id
    current_time = time.time()

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (user_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE users SET msg_count = msg_count + 1 WHERE chat_id = ?", (user_id,))
    else:
        today_str = datetime.now().strftime("%d.%m.%Y")
        cursor.execute("INSERT INTO users (chat_id, username, name, join_date, msg_count) VALUES (?, ?, ?, ?, 1)",
                       (user_id, message.from_user.username, message.from_user.first_name, today_str))
    conn.commit()
    conn.close()
    
    if text_lower == "кто я":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, roblox_nick, photo_id, gender, games, discord, description, likes FROM users WHERE chat_id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user and user[1]: 
            if user_id in who_ami_cooldown and current_time - who_ami_cooldown[user_id] < 180:
                left = int(180 - (current_time - who_ami_cooldown[user_id]))
                bot.reply_to(message, f"🐈‍⬛ Мяу! Не спамь. Команду можно вызывать раз в 3 минуты (осталось {left} сек).")
                return
            
            who_ami_cooldown[user_id] = current_time
            name, age, roblox, photo, gender, games, discord, desc, likes = user
            current_likes = int(likes) if likes else 0
            profile_text = f"👤 **Профиль пользователя {message.from_user.first_name}:**\n\n🏷 **Имя:** {name}\n⏳ **Возраст:** {age}\n🧬 **Пол:** {gender}\n🟦 **Roblox ник:** {roblox}\n🎵 **Discord:** {discord}\n🎮 **Игры:** {games}\n📝 **О себе:** {desc}\n\n❤️ **Лайков от напарников:** {current_likes}"
            
            if photo: bot.send_photo(message.chat.id, photo, caption=profile_text, parse_mode="Markdown")
            else: bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")
        else:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Пройти регистрацию 🚀", url="https://t.me/Roblox_finder_zero_bot?start=reg"))
            bot.reply_to(message, "🐈‍⬛ Мяу! Твой профиль еще не заполнен. Нажми на кнопку ниже, чтобы пройти регистрацию в лс:", reply_markup=markup)
        return

    if text_lower == "моя стата":
        if user_id in stats_cooldown and current_time - stats_cooldown[user_id] < 180:
            left = int(180 - (current_time - stats_cooldown[user_id]))
            bot.reply_to(message, f"🐈‍⬛ Мяу! Не спамь. Команду можно вызывать раз в 3 минуты (осталось {left} сек).")
            return

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, name, msg_count, join_date FROM users ORDER BY msg_count DESC")
        leaderboard = cursor.fetchall()
        total_users = len(leaderboard)
        
        my_rank = 0
        my_data = None
        for index, row in enumerate(leaderboard):
            if row[0] == user_id:
                my_rank = index + 1
                my_data = row
                break
        conn.close()

        if my_data:
            stats_cooldown[user_id] = current_time
            _, u_name, m_count, j_date = my_data
            try:
                date_obj = datetime.strptime(j_date, "%d.%m.%Y")
                days_delta = (datetime.now() - date_obj).days
            except:
                j_date = datetime.now().strftime("%d.%m.%Y")
                days_delta = 0
                
            days_word = get_days_word(days_delta)
            
            if m_count < 100: title = "🤫 Молчун"
            elif m_count < 500: title = "💬 Общительный"
            elif m_count < 1000: title = "🔥 Активный"
            else: title = "👑 Легенда Мяу"

            stats_msg = (
                f"👤 **Статистика — {message.from_user.first_name}**\n"
                f"———————————————\n\n"
                f"🏆 **Место в рейтинге:** {my_rank} место из {total_users}\n"
                f"🐱 **Мяуканий (сообщений):** {m_count}\n"
                f"———————————————\n\n"
                f"⭐️ **Звание:** {title}\n"
                f"📅 **В боте с:** {j_date} • с нами {days_delta} {days_word}\n"
            )
            bot.reply_to(message, stats_msg, parse_mode="Markdown")
        else:
            bot.reply_to(message, "🐈‍⬛ Напиши сначала что-нибудь в чат, чтобы я тебя посчитал!")
        return

    if "мяу" in text_lower:
        try:
            bot.set_message_reaction(chat_id=message.chat.id, message_id=message.message_id, reaction=[types.ReactionTypeEmoji(emoji="❤️")])
        except Exception:
            pass

# --- ЛИЧНЫЕ СООБЩЕНИЯ (ЧАТ) ---
@bot.message_handler(func=lambda message: True)
def chat_messaging(message):
    if message.chat.type != 'private':
        return

    # ЖЕЛЕЗНАЯ ЗАЩИТА: Если это команда /start, этот обработчик ПОЛНОСТЬЮ её игнорирует
    if message.text and message.text.startswith('/start'):
        return

    chat_id = message.chat.id
    if chat_id in reg_data:
        return

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, partner_id, age FROM users WHERE chat_id = ?", (chat_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    # Если пользователя нет в базе или у него нет возраста (не пройдена рега), игнорируем, чтобы не слать дубли
    if not user_data or not user_data[2]: 
        return

    name, partner_id, _ = user_data
    
    if partner_id > 0:
        last_activity[chat_id] = time.time()
        last_activity[partner_id] = time.time()
        try:
            sent_msg = bot.send_message(partner_id, f"💬 Напарник: {message.text}")
            last_message_id[partner_id] = sent_msg.message_id
            delayed_delete(partner_id, sent_msg.message_id, 60)
        except Exception:
            pass
        last_message_id[chat_id] = message.message_id
        delayed_delete(chat_id, message.message_id, 60)
    else:
        bot.send_message(chat_id, "Мяу? Воспользуйся кнопками меню ниже.", reply_markup=get_main_menu(chat_id))

# --- ОБРАБОТКА CALLBACK КНОПОК ---
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
        if chat_id in reg_data:
            gender = "Мужской 🧎‍♂️🐈‍⬛" if call.data == "reg_male" else "Женский 🧎‍♀️🐈‍⬛"
            reg_data[chat_id]['gender'] = gender
            bot.clear_step_handler_by_chat_id(chat_id)
            safe_delete(chat_id, msg_id)
            step_transition(chat_id, None, None, "В какие игры ты играешь? (Например: Blade ball, brookhaven итд...)", reg_step_games)

    elif call.data == "my_profile":
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, age, roblox_nick, photo_id, gender, games, discord, description, likes FROM users WHERE chat_id = ?", (chat_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            name, age, roblox, photo, gender, games, discord, desc, likes = user
            current_likes = int(likes) if likes else 0
            profile_text = f"👤 **Твой профиль:**\n\n🏷 **Имя:** {name}\n⏳ **Возраст:** {age}\n🧬 **Пол:** {gender}\n🟦 **Roblox ник:** {roblox}\n🎵 **Discord:** {discord}\n🎮 **Игры:** {games}\n📝 **О себе:** {desc}\n\n❤️ **Лайков от напарников:** {current_likes}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("← В главное меню", callback_data="delete_and_main"))
            
            if photo: bot.send_photo(chat_id, photo, caption=profile_text, parse_mode="Markdown", reply_markup=markup)
            else: bot.send_message(chat_id, profile_text, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "delete_and_main":
        safe_delete(chat_id, msg_id)
        bot.send_message(chat_id, "Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

    elif call.data == "notif_skip":
        safe_delete(chat_id, msg_id)

    elif call.data.startswith("notif_connect_"):
        partner_id = int(call.data.split("_")[2])
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT is_searching, name, age, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE chat_id = ?", (partner_id,))
        partner = cursor.fetchone()
        cursor.execute("SELECT partner_id FROM users WHERE chat_id = ?", (chat_id,))
        my_status = cursor.fetchone()
        
        if partner and partner[0] == 1 and my_status and my_status[0] == 0:
            cursor.execute("UPDATE users SET is_searching = 0, partner_id = ? WHERE chat_id = ?", (partner_id, chat_id))
            cursor.execute("UPDATE users SET is_searching = 0, partner_id = ? WHERE chat_id = ?", (chat_id, partner_id))
            conn.commit()
            
            p_name, p_age, p_roblox, p_photo, p_gender, p_games, p_discord, p_desc = partner[1:]
            cursor.execute("SELECT name, age, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE chat_id = ?", (chat_id,))
            user = cursor.fetchone()
            u_name, u_age, u_roblox, u_photo, u_gender, u_games, u_discord, u_desc = user
            
            last_activity[chat_id] = time.time()
            last_activity[partner_id] = time.time()
            
            info_to_user = f"🎉 Нашел напарника через уведомление! Вы в анонимном чате.\n\n🏷 Имя: {p_name}\n⏳ Возраст: {p_age}\n🟦 Roblox: {p_roblox}\n🧬 Пол: {p_gender}\n🎮 Игры: {p_games}\n🎵 Discord: {p_discord}\n📝 О себе: {p_desc}"
            if p_photo: bot.send_photo(chat_id, p_photo, caption=info_to_user, reply_markup=get_chat_menu())
            else: bot.send_message(chat_id, info_to_user, reply_markup=get_chat_menu())
            
            info_to_partner = f"🎉 Напарник откликнулся на твой поиск! Вы в анонимном чате.\n\n🏷 Имя: {u_name}\n⏳ Возраст: {u_age}\n🟦 Roblox: {u_roblox}\n🧬 Пол: {u_gender}\n🎮 Игры: {u_games}\n🎵 Discord: {u_discord}\n📝 О себе: {u_desc}"
            if u_photo: bot.send_photo(partner_id, u_photo, caption=info_to_partner, reply_markup=get_chat_menu())
            else: bot.send_message(partner_id, info_to_partner, reply_markup=get_chat_menu())
        else:
            bot.send_message(chat_id, "Мяу, к сожалению, этот напарник уже кого-то нашел или отменил поиск.", reply_markup=get_main_menu(chat_id))
        conn.close()

    elif call.data == "find_teammate":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, name, age, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE is_searching = 1 AND chat_id != ?", (chat_id,))
        partner = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        if partner:
            partner_id, p_name, p_age, p_roblox, p_photo, p_gender, p_games, p_discord, p_desc = partner
            cursor.execute("SELECT name, age, roblox_nick, photo_id, gender, games, discord, description FROM users WHERE chat_id = ?", (chat_id,))
            user = cursor.fetchone()
            u_name, u_age, u_roblox, u_photo, u_gender, u_games, u_discord, u_desc = user
            
            cursor.execute("UPDATE users SET is_searching = 0, partner_id = ? WHERE chat_id = ?", (partner_id, chat_id))
            cursor.execute("UPDATE users SET is_searching = 0, partner_id = ? WHERE chat_id = ?", (chat_id, partner_id))
            conn.commit()
            
            last_activity[chat_id] = time.time()
            last_activity[partner_id] = time.time()
            
            info_to_user = f"🎉 Нашел напарника! Вы соединены в анонимном чате.\n\n🏷 Имя: {p_name}\n⏳ Возраст: {p_age}\n🟦 Roblox: {p_roblox}\n🧬 Пол: {p_gender}\n🎮 Игры: {p_games}\n🎵 Discord: {p_discord}\n📝 О себе: {p_desc}"
            if p_photo: bot.send_photo(chat_id, p_photo, caption=info_to_user, reply_markup=get_chat_menu())
            else: bot.send_message(chat_id, info_to_user, reply_markup=get_chat_menu())
            
            info_to_partner = f"🎉 Нашел напарника! Вы соединены в анонимном чате.\n\n🏷 Имя: {u_name}\n⏳ Возраст: {u_age}\n🟦 Roblox: {u_roblox}\n🧬 Пол: {u_gender}\n🎮 Игры: {u_games}\n🎵 Discord: {u_discord}\n📝 О себе: {u_desc}"
            if u_photo: bot.send_photo(partner_id, u_photo, caption=info_to_partner, reply_markup=get_chat_menu())
            else: bot.send_message(partner_id, info_to_partner, reply_markup=get_chat_menu())
            safe_delete(chat_id, msg_id)
        else:
            cursor.execute("UPDATE users SET is_searching = 1 WHERE chat_id = ?", (chat_id,))
            conn.commit()
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Перестать искать ❌", callback_data="stop_search"))
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"🔍 Ищем напарника...\n\nКак только кто-то появится — мы вас соединим.\n\n👥 Всего в боте: {total_users} человек", reply_markup=markup)
        conn.close()
        
    elif call.data == "stop_search":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_searching = 0 WHERE chat_id = ?", (chat_id,))
        conn.commit()
        conn.close()
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

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
            send_rating_menu(chat_id, partner_id)
            send_rating_menu(partner_id, chat_id)
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
            markup.add(types.InlineKeyboardButton("Да ✅", callback_data=f"share_accept_{chat_id}"),
                       types.InlineKeyboardButton("Нет ❌", callback_data=f"share_decline_{chat_id}"))
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

    elif call.data.startswith("rate_like_"):
        target_partner_id = int(call.data.split("_")[2])
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET likes = likes + 1 WHERE chat_id = ?", (target_partner_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Спасибо за оценку!")
        bot.send_message(chat_id, "Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

    elif call.data.startswith("rate_dislike_"):
        target_partner_id = int(call.data.split("_")[2])
        safe_delete(chat_id, msg_id)
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET dislikes = dislikes + 1 WHERE chat_id = ?", (target_partner_id,))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Спасибо за оценку!")
        bot.send_message(chat_id, "Что делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))

    elif call.data == "change_name":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Введи новое имя:")
        bot.register_next_step_handler(m, lambda msg: update_field(msg, "name", m.message_id))
    elif call.data == "change_age":
        safe_delete(chat_id, msg_id)
        m = bot.send_message(chat_id, "Введи свой новый возраст:")
        bot.register_next_step_handler(m, update_age_field, m.message_id)
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
    if chat_id not in reg_data: return
    reg_data[chat_id]['name'] = message.text
    step_transition(chat_id, message.message_id, reg_data[chat_id]['last_bot_msg'], "Сколько тебе лет? ⏳", reg_step_age)

def reg_step_age(message):
    chat_id = message.chat.id
    if chat_id not in reg_data: return
    age_text = message.text
    
    if not age_text.isdigit() or not (4 <= int(age_text) <= 100):
        next_msg = bot.send_message(chat_id, "Мяу, введи настоящий возраст цифрами (от 4 до 100):")
        delayed_delete(chat_id, message.message_id, 5)
        safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_age)
        return
        
    reg_data[chat_id]['age'] = age_text
    step_transition(chat_id, message.message_id, reg_data[chat_id]['last_bot_msg'], "Какой твой ник в Roblox? 🕹", reg_step_roblox)

def reg_step_roblox(message):
    chat_id = message.chat.id
    if chat_id not in reg_data: return
    nick = message.text
    if len(nick) < 3 or not is_english(nick):
        next_msg = bot.send_message(chat_id, "Ник должен быть на английском и от 3 символов! Попробуй еще раз:")
        delayed_delete(chat_id, message.message_id, 5)
        safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_roblox)
        return
        
    reg_data[chat_id]['roblox_nick'] = nick
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Мужской 🧎‍♂️🐈‍⬛", callback_data="reg_male"),
               types.InlineKeyboardButton("Женский 🧎‍♀️🐈‍⬛", callback_data="reg_female"))
    
    next_msg = bot.send_message(chat_id, "Какой твой пол? Кошка/кот", reply_markup=markup)
    reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
    delayed_delete(chat_id, message.message_id, 5)

def reg_step_games(message):
    chat_id = message.chat.id
    if chat_id not in reg_data: return
    reg_data[chat_id]['games'] = message.text
    step_transition(chat_id, message.message_id, reg_data[chat_id]['last_bot_msg'], "Какой твой дискорд? Напиши 'нет' если неету 🐈‍⬛", reg_step_discord)

def reg_step_discord(message):
    chat_id = message.chat.id
    if chat_id not in reg_data: return
    dc = message.text
    if dc.lower() != "нет" and not is_english(dc):
        next_msg = bot.send_message(chat_id, "Дискорд должен быть на английском или напиши 'нет'!")
        delayed_delete(chat_id, message.message_id, 5)
        safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_discord)
        return
        
    reg_data[chat_id]['discord'] = dc
    step_transition(chat_id, message.message_id, reg_data[chat_id]['last_bot_msg'], "Отправь фото своего скина, или то что связано с тобой!! 👾", reg_step_photo)

def reg_step_photo(message):
    chat_id = message.chat.id
    if chat_id not in reg_data: return
    if not message.photo:
        next_msg = bot.send_message(chat_id, "Принимаются лишь фото! Отправь картинку:")
        delayed_delete(chat_id, message.message_id, 5)
        safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_photo)
        return
        
    reg_data[chat_id]['photo_id'] = message.photo[-1].file_id
    step_transition(chat_id, message.message_id, reg_data[chat_id]['last_bot_msg'], "Хочешь ли ты добавить свое описание? Напиши 'нет' если не хочешь (до 100 символов)", reg_step_desc)

def reg_step_desc(message):
    chat_id = message.chat.id
    if chat_id not in reg_data: return
    desc = message.text
    if len(desc) > 100:
        next_msg = bot.send_message(chat_id, "Описание слишком длинное! Должно быть до 100 символов. Попробуй снова:")
        delayed_delete(chat_id, message.message_id, 5)
        safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
        reg_data[chat_id]['last_bot_msg'] = next_msg.message_id
        bot.register_next_step_handler(next_msg, reg_step_desc)
        return
        
    reg_data[chat_id]['description'] = desc
    today_str = datetime.now().strftime("%d.%m.%Y")
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (chat_id, username, name, age, roblox_nick, photo_id, gender, games, discord, description, join_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, message.from_user.username, reg_data[chat_id]['name'], reg_data[chat_id]['age'], 
          reg_data[chat_id]['roblox_nick'], reg_data[chat_id]['photo_id'], reg_data[chat_id]['gender'], 
          reg_data[chat_id]['games'], reg_data[chat_id]['discord'], reg_data[chat_id]['description'], today_str))
    conn.commit()
    conn.close()
    
    delayed_delete(chat_id, message.message_id, 5)
    safe_delete(chat_id, reg_data[chat_id]['last_bot_msg'])
    
    bot.send_message(chat_id, f"Регистрация успешно завершена! С возвращением, {reg_data[chat_id]['name']}!\nЧто делаем мяу? 🐈‍⬛", reply_markup=get_main_menu(chat_id))
    del reg_data[chat_id]

# --- ОБНОВЛЕНИЕ ПОЛЕЙ В НАСТРОЙКАХ ---
def update_field(message, field_name, bot_msg_id):
    chat_id = message.chat.id
    delayed_delete(chat_id, message.message_id, 5)
    safe_delete(chat_id, bot_msg_id)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {field_name} = ? WHERE chat_id = ?", (message.text, chat_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✏️ Что хочешь изменить?", reply_markup=get_edit_menu())

def update_age_field(message, bot_msg_id):
    chat_id = message.chat.id
    delayed_delete(chat_id, message.message_id, 5)
    age_text = message.text
    
    if not age_text.isdigit() or not (4 <= int(age_text) <= 100):
        safe_delete(chat_id, bot_msg_id)
        m = bot.send_message(chat_id, "Мяу, возраст должен быть числом от 4 до 100! Попробуй еще раз:")
        bot.register_next_step_handler(m, update_age_field, m.message_id)
        return
        
    safe_delete(chat_id, bot_msg_id)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age = ? WHERE chat_id = ?", (age_text, chat_id))
    conn.commit()
    conn.close()
    bot.send_message(chat_id, "✏️ Что хочешь изменить?", reply_markup=get_edit_menu())

def update_photo(message, bot_msg_id):
    chat_id = message.chat.id
    delayed_delete(chat_id, message.message_id, 5)
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
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка пуллинга: {e}")
        time.sleep(5)

