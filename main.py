import telebot
import random
import json
import os

TOKEN = "8148374493:AAGDwlyGPjH03GzeD2dTjxnVwrKNl2QTVOw"
bot = telebot.TeleBot(TOKEN)

# Путь к файлу
EXPLORERS_FILE = 'explorers.json'

# Загрузка данных
def load_explorers():
    try:
        with open(EXPLORERS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Инициализация данных
explorers = load_explorers()
user_states = {}

def send_photo_safe(chat_id, image_path, caption=None, reply_markup=None):
    try:
        with open(image_path, 'rb') as photo:
            bot.send_photo(
                chat_id,
                photo,
                caption=caption,
                reply_markup=reply_markup
            )
        return True
    except Exception as e:
        print(f"Error sending image {image_path}: {e}")
        if caption:
            bot.send_message(chat_id, caption, reply_markup=reply_markup)

# Создание клавиатур
def create_reply_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📚 Список мореплавателей", "❓ Проверь себя")
    keyboard.row("🏠 Главное меню")
    return keyboard

def create_main_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("📚 Список мореплавателей", callback_data="show_list"),
        telebot.types.InlineKeyboardButton("❓ Проверь себя", callback_data="quiz")
    )
    return keyboard

def create_explorer_keyboard(explorer_id):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("🗺 Маршрут", callback_data=f"route_{explorer_id}")
    )
    keyboard.add(
        telebot.types.InlineKeyboardButton("◀️ В главное меню", callback_data="main_menu")
    )
    return keyboard

def create_keyboard():
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("◀️ В главное меню", callback_data="main_menu")
    )
    return keyboard

# Обработчики команд
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user_states[chat_id] = "1"
    welcome_text = """
    🌊 Добро пожаловать в мир великих мореплавателей!
    🚢 Выберите действие:
    📚 Список мореплавателей - изучите великих первооткрывателей
    ❓ Проверь себя - проверьте свои знания
    """
    bot.send_message(
        chat_id,
        welcome_text,
        reply_markup=create_main_keyboard()
    )
    bot.send_message(
        chat_id,
        "Выберите действие:",
        reply_markup=create_reply_keyboard()
    )

# Обработчик текстовых сообщений
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "📚 Список мореплавателей":
        show_explorers_list(message)
    elif message.text == "❓ Проверь себя":
        start_quiz(message)
    elif message.text == "🏠 Главное меню":
        show_main_menu(message)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    current_explorer = user_states.get(chat_id, "1")
    if call.data == "show_list":
        show_explorers_list(call.message)
    elif call.data == "quiz":
        start_quiz(call.message)
    elif call.data.startswith("select_"):
        explorer_id = call.data.split("_")[1]
        user_states[chat_id] = explorer_id
        show_explorer_info(call.message)
    elif call.data.startswith("route_"):
        explorer_id = call.data.split("_")[1]
        user_states[chat_id] = explorer_id
        show_route(call.message)
    elif call.data == "main_menu":
        show_main_menu(call.message)
    elif call.data.startswith("quiz_"):
        handle_quiz_answer(call)
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )
    except:
        pass

def show_main_menu(message):
    welcome_text = """
    🌊 Главное меню
    🚢 Выберите действие:
    📚 Список мореплавателей - изучите великих первооткрывателей
    ❓ Проверь себя - проверьте свои знания
    """
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_keyboard()
    )
    bot.send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=create_reply_keyboard()
    )

def show_explorers_list(message):
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for id, explorer in explorers.items():
        keyboard.add(telebot.types.InlineKeyboardButton(
            f"{explorer['name']} ({explorer['years']})",
            callback_data=f"select_{id}"
        ))
    keyboard.add(telebot.types.InlineKeyboardButton("◀️ В главное меню", callback_data="main_menu"))
    bot.send_message(
        message.chat.id,
        "📚 Выберите мореплавателя:",
        reply_markup=keyboard
    )

def show_explorer_info(message):
    explorer_id = user_states.get(message.chat.id, "1")
    explorer = explorers[explorer_id]
    caption = f"""
    📚 {explorer['name']}
    Годы жизни: {explorer['years']}
    {explorer['bio']}
    """
    send_photo_safe(message.chat.id, explorer['image'], caption, create_explorer_keyboard(explorer_id))

def show_route(message):
    explorer_id = user_states.get(message.chat.id, "1")
    explorer = explorers[explorer_id]
    if explorer['route'] != "нет":
        send_photo_safe(message.chat.id, explorer['route'], "Маршрут", create_keyboard())
    else:
        bot.send_message(message.chat.id, "Маршрут не доступен.", reply_markup=create_keyboard())


def start_quiz(message):
    explorer_id = random.choice(list(explorers.keys()))
    explorer = explorers[explorer_id]
    caption = f"❓ О каком мореплавателе идет речь?\n\n{explorer['bio']}"
    send_photo_safe(message.chat.id, explorer['image'], caption)

    # Создаем список вариантов, включая правильный ответ
    options = [explorer]
    while len(options) < 3:
        option = random.choice(list(explorers.values()))
        if option not in options:
            options.append(option)

    # Перемешиваем варианты
    random.shuffle(options)

    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    for option in options:
        keyboard.add(telebot.types.InlineKeyboardButton(
            option['name'],
            callback_data=f"quiz_{option['name'] == explorer['name']}"
        ))
    keyboard.add(telebot.types.InlineKeyboardButton("◀️ В главное меню", callback_data="main_menu"))
    bot.send_message(
        message.chat.id,
        "Выберите правильный ответ:",
        reply_markup=keyboard
    )
def handle_quiz_answer(call):
    is_correct = call.data.split("_")[1] == "True"
    if is_correct:
        text = "✅ Правильно! Молодец!"
    else:
        text = "❌ Неправильно! Попробуй еще раз!"
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        telebot.types.InlineKeyboardButton("🔄 Ещё вопрос", callback_data="quiz")
    )
    keyboard.add(telebot.types.InlineKeyboardButton("◀️ В главное меню", callback_data="main_menu"))
    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=keyboard
    )

if __name__ == "__main__":
    bot.polling(none_stop=True)
