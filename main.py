# Author: Aleksei Grigorev
# longwinterday@gmail.com


import telebot
import os
from loguru import logger
from decouple import config
from city_founding import city_founding
from simple_price import simple_price
from typing import List, Dict


bot = telebot.TeleBot(config('TOKEN'))

logger.add(os.sep.join(('log', 'file_{time}.log')))

bd_text_data: tuple = (
    'Сколько отелей ищем?',
    'Введите минимальную стоимость одной ночи в рублях',
    'Введите максимальную стоимость одной ночи в рублях',
    'Введите максимальное расстояние от центра в километрах'
)

# Набор команд бота
my_commands: List[str] = [
    'Мои команды:',
    '/help',
    '/hello_world',
    '/lowprice - самые дешевые отели',
    '/highprice - самые дорогие отели',
    '/bestdeal - оптимальное предложение'
]

# Набор простых ответов бота
commands: Dict = {
    '/hello_world': lambda message: bot.send_message(message.from_user.id, 'Привет мир!'),
    '/help': lambda message: bot.send_message(message.from_user.id, '\n'.join(my_commands)),
    '/start': lambda message: bot.send_message(message.from_user.id,
                                               'Добро пожаловать в чат-бот агентства Too Easy Travel! '
                                               'Для того чтобы узнать, что я умею - наберите /help'),
    'Привет': lambda message: hello(message)
}


@bot.message_handler(content_types=['text'])
def get_text_messages(message) -> None:
    """
    Обработчик начальных команд бота
    :param message: Сообщение от пользователя
    """
    get_text_messages.cid = message.chat.id
    if message.text in commands:
        commands[message.text](message)
    elif message.text == '/lowprice' or message.text == '/highprice' or message.text == '/bestdeal':
        if message.text == '/highprice':
            get_text_messages.sort_order_key = "PRICE_HIGHEST_FIRST"
        elif message.text == '/bestdeal':
            get_text_messages.sort_order_key = "DISTANCE_FROM_LANDMARK"
        else:
            get_text_messages.sort_order_key = "PRICE"
        bot.send_message(message.chat.id, 'Какой город ищем?')
        bot.register_next_step_handler(message, city_list_printing)
    else:
        bot.send_message(message.from_user.id, 'Неизвестная команда. Посмотреть список всех команд: /help')


def city_list_printing(message) -> None:
    """
    Предлагает варианты городов для поиска
    :param message: Сообщение от пользователя
    """
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
    buttons_added = list()
    for i_city in city_founding(message.text):
        buttons_added.append(telebot.types.InlineKeyboardButton(text=i_city.name,
                                                                callback_data='~'.join([i_city.name, i_city.id])))
    if not buttons_added:
        bot.send_message(message.chat.id, 'Не нашёл подходящих вариантов. Попробуйте ещё раз. Какой город ищем?')
        bot.register_next_step_handler(message, city_list_printing)
    else:
        keyboard.add(*buttons_added)
        bot.send_message(message.from_user.id, 'Выберите город из списка:', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def how_many_hotels(call) -> None:
    """
    Запрашивает количество отелей для отображения
    :param call: Сообщение от пользователя
    """
    if call.data:
        city_name, how_many_hotels.city_id = call.data.split('~')
        bot.send_message(call.message.chat.id, city_name)
        bot.send_message(call.message.chat.id, 'Я могу найти до 25ти отелей. Сколько будем искать?')
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=None)
        if get_text_messages.sort_order_key == "DISTANCE_FROM_LANDMARK":
            bot.register_next_step_handler(call.message, best_deal)
        else:
            bot.register_next_step_handler(call.message, hotels_results_printing)


def hotels_results_printing(message, bd_data=None) -> None:
    """
    Выводит список найденных отелей
    :param message: Сообщение от пользователя
    :param bd_data: Данные о количестве отелей, минимальной и максимальной цене
    """
    distance: str = 'inf'
    if get_text_messages.sort_order_key != "DISTANCE_FROM_LANDMARK":
        hotels_results_printing.number_of_hotels = message.text
        if not hotels_results_printing.number_of_hotels.isdigit():
            bot.send_message(message.chat.id, 'Ожидаю положительное число цифрами. Сколько отелей ищем?')
            bot.register_next_step_handler(message, hotels_results_printing)
            return
    else:
        distance = message.text
        if not distance.isdigit():
            bot.send_message(message.chat.id, 'Ожидаю положительное число цифрами. '
                                              'Введите максимальное расстояние от центра в километрах')
            bot.register_next_step_handler(message, hotels_results_printing)
            return
    if bd_data:
        hotels_results_printing.number_of_hotels, low_price, high_price = bd_data
        if float(high_price) < float(low_price):
            high_price, low_price = low_price, high_price
            bot.send_message(message.chat.id, 'Вы перепутали максимум и минимум, но я за вас сам всё поменял')
    else:
        low_price, high_price = None, None
    bot.send_message(message.from_user.id, 'Результат:')
    hotels = simple_price(how_many_hotels.city_id, hotels_results_printing.number_of_hotels,
                          get_text_messages.sort_order_key, low_price, high_price, distance)
    if hotels:
        for i_hotel in hotels:
            bot.send_message(message.from_user.id,
                             f'{i_hotel.name} цена одной ночи '
                             f'{i_hotel.price} рублей, отель находится в '
                             f'{i_hotel.distance}км от центра города')
    else:
        bot.send_message(message.chat.id, 'По вашему запросу я не нашёл ни одного варианта')


def best_deal(message, bd_data=None) -> None:
    """
    Запрашивает минимальную и максимальную цену, максимальное расстояние от центра города
    :param message: Сообщение от пользователя
    :param bd_data: Данные о количестве отелей, минимальной и максимальной цене
    """
    if bd_data is None:
        bd_data = []
    while len(bd_data) < 3:
        if not message.text.isdigit():
            bot.send_message(message.chat.id, f'Ожидаю положительное число цифрами. {bd_text_data[len(bd_data)]}')
            bot.register_next_step_handler(message, best_deal, bd_data)
            return
        else:
            bd_data.append(message.text)
            bot.send_message(message.from_user.id, f'{bd_text_data[len(bd_data)]}')
            if len(bd_data) == 3:
                bot.register_next_step_handler(message, hotels_results_printing, bd_data)
                return
            bot.register_next_step_handler(message, best_deal, bd_data)
            return


def hello(message) -> None:
    """
    Функция уточняет имя пользователя и здоровается в ответ на сообщение "Привет"
    :param message: Сообщение от пользователя
    """
    bot.send_message(message.from_user.id, 'Как тебя зовут?')
    bot.register_next_step_handler(message, lambda t_message:
                                   bot.send_message(t_message.from_user.id, f'Привет, {t_message.text}!'))


if __name__ == '__main__':
    while 1:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            bot.send_message(chat_id=(get_text_messages.cid if get_text_messages.cid else '220541838'),
                             text=f"Произошла какая-то ошибка. Подождите пару секунд, бот перезагружается")
            logger.exception(str(e))
