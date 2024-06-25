import telebot

# Чтение токена из файла token.txt
with open('token.txt') as f:
    API_TOKEN = f.read().strip()

bot = telebot.TeleBot(API_TOKEN)


@bot.message_handler(commands=['everyone'])
def ping_all(message):
    chat_id = message.chat.id
    all_members = []

    try:
        # Получаем информацию о чате
        chat = bot.get_chat(chat_id)

        # Проверяем, является ли бот администратором
        is_bot_admin = any(admin.user.id == bot.get_me().id for admin in bot.get_chat_administrators(chat_id))
        if not is_bot_admin:
            bot.send_message(chat_id, "Бот должен быть администратором, чтобы упоминать всех участников.")
            return

        # Получаем всех администраторов чата
        administrators = bot.get_chat_administrators(chat_id)

        # Формируем упоминания администраторов
        for admin in administrators:
            user = admin.user
            if user.username:
                mention = f'@{user.username}'
            else:
                mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
            all_members.append(mention)

        # Отправляем сообщение, если есть упоминания
        ping_message = ' '.join(all_members)

        if ping_message:
            bot.send_message(chat_id, ping_message, parse_mode='HTML')
        else:
            bot.send_message(chat_id, "Не удалось получить список участников для упоминания.")
    except Exception as e:
        bot.send_message(chat_id, f"Не удалось получить список участников: {e}")


bot.polling()
