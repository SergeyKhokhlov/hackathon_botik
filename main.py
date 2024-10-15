import telebot
import json
from datetime import datetime
import requests

bot = telebot.TeleBot("7541524341:AAG8__2mnA2fG66GGx3_qUEpQ6iJ3gyIlIw")
with open('data.json', encoding='utf-8') as file:
    data = json.load(file)

# Для api подключения и получения данных в json:
# response = requests.get("сюда ссылку на запрос")
# data = response.json()


user_indices = {}


def send_data(call, index):
    """Отправляем данные по указанному индексу"""
    index = max(0, min(int(index), len(data) - 1))  # проверяем, что индекс в пределах данных
    keyboard = telebot.types.InlineKeyboardMarkup()

    # Кнопки навигации
    left_index = max(0, index - 1)
    right_index = min(len(data) - 1, index + 1)

    button_left = telebot.types.InlineKeyboardButton(text="<", callback_data=f"left_{left_index}")
    button_rent = telebot.types.InlineKeyboardButton(text="Забронировать", url="https://discord.ru/")
    button_right = telebot.types.InlineKeyboardButton(text=">", callback_data=f"right_{right_index}")

    keyboard.add(button_rent)
    keyboard.add(button_left, button_right)

    # Данные для отправки
    name = data[str(index)]["name"]
    description = data[str(index)]["description"]
    image = data[str(index)]["image"]
    max_persons = data[str(index)]["max_persons"]

    caption = f"*Название:* {name}\n*Описание:* {description}\n*Максимальное количество персон:* {max_persons}"
    try:
        if call.content_type == 'photo':
            bot.edit_message_media(
                chat_id=call.from_user.id,
                message_id=call.message.message_id,
                media=telebot.types.InputMediaPhoto(image, caption=caption, parse_mode="markdown"),
                reply_markup=keyboard
            )
        else:
            bot.send_photo(call.from_user.id, image, caption=caption, parse_mode="markdown", reply_markup=keyboard)
    except Exception:
        if call.message.content_type == 'photo':
            bot.edit_message_media(
                chat_id=call.from_user.id,
                message_id=call.message.message_id,
                media=telebot.types.InputMediaPhoto(image, caption=caption, parse_mode="markdown"),
                reply_markup=keyboard
            )
        else:
            bot.send_photo(call.from_user.id, image, caption=caption, parse_mode="markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: "left" in call.data or "right" in call.data)
def navigate(call):
    index = call.data.split("_")[1]
    send_data(call, int(index))


@bot.callback_query_handler(func=lambda call: "left" in call.data or "right" in call.data)
def navigate(call):
    index = call.data.split("_")[1]
    send_data(call, int(index))  # Отправляем данные для текущего индекса


@bot.callback_query_handler(func=lambda call: call.data == 'view_all_data')
def view_data(call):
    send_data(call, 0)  # Отображаем первый элемент данных


@bot.callback_query_handler(func=lambda call: call.data == 'rent')
def rent(call):
    bot.send_message(call.from_user.id,
                     "Укажите даты, на которые Вы хотите забронировать помещение\nФормат: (17.10.2024 - 22.10.2024):")
    bot.register_next_step_handler(call.message, rent_step_dates)

def rent_step_dates(message):
    try:
        # Получаем даты от пользователя
        user_input = message.text.strip()
        start_user, end_user = user_input.split(' - ')
        start_user = datetime.strptime(start_user, '%d.%m.%Y')
        end_user = datetime.strptime(end_user, '%d.%m.%Y')

        available_places = []
        for i in range(len(data)):
            start_date = data[str(i)]["start_date"]
            end_date = data[str(i)]["end_date"]

            # Если даты не указаны (пустые), то помещение всегда свободно
            if start_date == '' or end_date == '':
                available_places.append(i)
            else:
                start_date = datetime.strptime(start_date, '%d.%m.%Y')
                end_date = datetime.strptime(end_date, '%d.%m.%Y')

                # Проверяем, свободно ли помещение в указанный пользователем период
                if end_user < start_date or start_user > end_date:
                    available_places.append(i)

        if available_places:
            # Сохраняем индексы доступных помещений для пользователя
            user_indices[message.chat.id] = 0  # Инициализация индекса
            send_data(message, available_places[0])  # Отправляем первое доступное помещение
        else:
            bot.send_message(message.chat.id, "Извините, все помещения заняты в указанные даты.")

    except ValueError:
        bot.send_message(message.chat.id,
                         "Пожалуйста, укажите даты в правильном формате: (дд.мм.гггг - дд.мм.гггг)")
        bot.register_next_step_handler(message, rent_step_dates)  # Повторный запрос при ошибке


@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    button_view = telebot.types.InlineKeyboardButton(text="Отобразить все помещения", callback_data="view_all_data")
    button_rent = telebot.types.InlineKeyboardButton(text="Забронировать помещение", callback_data="rent")
    keyboard.add(button_view)
    keyboard.add(button_rent)

    bot.send_message(message.chat.id, f"Здравствуйте, *{message.from_user.first_name}!*\n\n"
                                      f"С помощью нашего сервиса, Вы можете арендовать помещения для мероприятий",
                     parse_mode="markdown", reply_markup=keyboard)


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=123)
