# Author: Aleksei Grigorev
# longwinterday@gmail.com


import requests
import json
import datetime
from typing import List, Optional
from re import match


class Hotel:
    """
    Базовый класс отеля
    :methods: name: возвращает название отеля
    :method price: возвращает стоимость одной ночи
    :method distance: возвращает удалённость от центра города
    """
    def __init__(self, name: str, city_id: str, distance_from_center: str) -> None:
        self.__name = name
        self.__id = city_id
        self.__distance = distance_from_center

    @property
    def name(self) -> str:
        return self.__name

    @property
    def price(self) -> str:
        return self.__id

    @property
    def distance(self):
        return self.__distance


def simple_price(user_destination: Optional[str], user_page_size: str,
                 sort_order_key: str, min_price: Optional[str] = None,
                 max_price: Optional[str] = None, user_distance: str = "inf") -> List[Hotel]:
    """
    Возвращает список экземпляров класса Hotel из запроса к api по заданным параметрам пользователя на сегодняшнюю дату
    :param user_destination: id города в котором производится поиск отелей
    :param user_page_size: количество отелей
    :param sort_order_key: ключ сортировки
    :param min_price: минимальная стоимость номера
    :param max_price: максимальная стоимость номера
    :param user_distance: максимальная удалённость от центра города
    :return: список экземпляров класса Hotel
    """
    with open('headers.json', 'r', encoding='utf-8') as file:
        headers = json.loads(file.read())
    url_hotels_founding = 'https://hotels4.p.rapidapi.com/properties/list'

    today = datetime.datetime.today().date()
    tomorrow = today + datetime.timedelta(days=1)

    params: dict = {
        "adults1": "1",
        "pageNumber": "1",
        "destinationId": user_destination,
        "pageSize": user_page_size,
        "checkOut": str(tomorrow),
        "checkIn": str(today),
        "sortOrder": sort_order_key,
        "locale": "ru_RU",
        "currency": "RUB",
        "priceMax": max_price,
        "priceMin": min_price,
        "landmarkIds": "City center"
    }

    res = requests.request("GET", url_hotels_founding, headers=headers, params=params)
    data = json.loads(res.text)['data']['body']['searchResults']['results']
    result = list()
    for i_hotel in data:
        name = i_hotel.get('name')
        price = i_hotel.get('ratePlan').get('price').get('exactCurrent')
        distance = ''.join(sym for sym in i_hotel.get('landmarks')[0].get('distance')
                           if match(r'[0-9,.]', sym)).replace(',', '.')

        if float(user_distance) >= float(distance):
            result.append(Hotel(name, price, distance))
    if sort_order_key == "DISTANCE_FROM_LANDMARK":
        result.sort(key=lambda x: x.price)
    return result
