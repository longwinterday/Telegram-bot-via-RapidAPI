# Author: Aleksei Grigorev
# longwinterday@gmail.com


import requests
import json
import re
from typing import List


class City:
    """
    Базовый класс горда
    :method: name: возвращает название города
    :method id: возвращает id города
    """

    def __init__(self, name, city_id):
        self.__name = name
        self.__id = city_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def id(self) -> str:
        return self.__id


def city_founding(city: str) -> List[City]:
    """
    Возвращает список экземпляров класса City из запроса к api по заданным параметрам пользователя
    :param city: название города для поиска
    :return: список экземпляров класса City
        """
    with open('headers.json', 'r', encoding='utf-8') as file:
        headers = json.loads(file.read())

    locale = 'ru_RU' if re.match(r'[А-Яа-яЁё]+', city) else 'en_US'
    city = ' '.join([i.casefold().capitalize() for i in city.split()])
    url_city_founding = 'https://hotels4.p.rapidapi.com/locations/search'
    querystring = {"query": city, "locale": locale}
    res = requests.request("GET", url_city_founding, headers=headers, params=querystring)

    suggestions = json.loads(res.text)['suggestions']

    cities = list()

    for i_sug in suggestions:
        if i_sug.get('group') == 'CITY_GROUP':
            suggestions = i_sug['entities']
            break

    for i_city in suggestions:
        city_name = i_city.get('caption').replace("<span class='highlighted'>", '').replace("</span>", '').replace(
            'United States of America', 'USA')
        if i_city.get('type') == 'CITY' and city_name.startswith(city):
            cities.append(City(city_name, i_city.get('destinationId')))

    return cities
