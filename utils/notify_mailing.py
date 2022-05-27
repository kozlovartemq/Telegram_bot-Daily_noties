import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pathlib
from pathlib import Path


pathes = {
    'weather': f"{str(Path(pathlib.Path.cwd() / 'data' / 'weather_data.json'))}",
    'previous_rates': f"{str(Path(pathlib.Path.cwd() / 'data' / 'previous_rates.json'))}",
    'bot_data': f"{str(Path(pathlib.Path.cwd() / 'data' / 'bot_data.json'))}"
}


class DailyMailing:
    RUB_URL = 'https://www.cbr-xml-daily.ru/latest.js'
    ALTERNATIVE_EXCHANGE_RATES_API = 'https://api.exchangerate-api.com/v4/latest/'
    BASE_URL_WEATHER_API = 'http://api.openweathermap.org/data/2.5/'
    BASE_URL_BTC_PARSE = 'https://www.google.com/'
    TELEGRAM_BOT_API = 'https://api.telegram.org/bot'
    RANDOM_JOKES_QUOTES = 'http://rzhunemogu.ru/RandJSON.aspx'

    def __init__(self, userid):
        self.__userid = userid

    def get_rates(self, exchange_rates: set):
        try:
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
            }
            response = requests.get(url=f'{self.RUB_URL}', headers=headers).json()

            date = f"{response['date'][8:]}.{response['date'][5:7]}.{response['date'][0:4]}"
            rub_usd_rate = round(1 / response['rates']['USD'], 2)
            rub_eur_rate = round(1 / response['rates']['EUR'], 2)
            kzt_rub_rate = round(response['rates']['KZT'], 2)
            kzt_usd_rate = round(rub_usd_rate * kzt_rub_rate, 2)
        except Exception:
            return 'Не удалось получить курс валют.\n'
        result_dict = dict(date=date, rates=dict())
        if 'USD-RUB' in exchange_rates:
            result_dict['rates']['USD-RUB'] = rub_usd_rate
        if 'EUR-RUB' in exchange_rates:
            result_dict['rates']['EUR-RUB'] = rub_eur_rate
        if 'RUB-KZT' in exchange_rates:
            result_dict['rates']['RUB-KZT'] = kzt_rub_rate
        if 'USD-KZT' in exchange_rates:
            result_dict['rates']['USD-KZT'] = kzt_usd_rate

        return result_dict

    def get_rates_from_exchangerate(self, exchange_rates: set):
        response_usd = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}USD').json()
        response_eur = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}EUR').json()
        response_rub = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}RUB').json()
        date = f"{response_usd['date'][8:]}.{response_usd['date'][5:7]}.{response_usd['date'][0:4]}"
        rub_usd_rate = response_usd['rates']['RUB']
        rub_eur_rate = response_eur['rates']['RUB']
        kzt_rub_rate = response_rub['rates']['KZT']
        kzt_usd_rate = response_usd['rates']['KZT']
        result_dict = dict(date=date, rates=dict())
        if 'USD-RUB' in exchange_rates:
            result_dict['rates']['USD-RUB'] = rub_usd_rate
        if 'EUR-RUB' in exchange_rates:
            result_dict['rates']['EUR-RUB'] = rub_eur_rate
        if 'RUB-KZT' in exchange_rates:
            result_dict['rates']['RUB-KZT'] = kzt_rub_rate
        if 'USD-KZT' in exchange_rates:
            result_dict['rates']['USD-KZT'] = kzt_usd_rate

        return result_dict

    def parse_btc_rate(self):
        try:
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
            }
            response = requests.get(url=f'{self.BASE_URL_BTC_PARSE}finance/quote/BTC-USD', headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            btc_rate_div = soup.find('div', class_='YMlKec fxKbKc')
            btc_rate = btc_rate_div.text
            float_btc = float(btc_rate.replace(',', ''))
        except Exception:
            return 'Не удалось получить курс BTC.\n'
        return float_btc

    def save_history_of_rates(self, rub_rates, btc_rate):
        with open(pathes['previous_rates'], 'r+', encoding='utf-8') as file:
            rates: dict = json.loads(file.read())
            rates[self.__userid] = {}
            if isinstance(rub_rates, dict):
                rates[self.__userid]['rub_rates'] = rub_rates
            if isinstance(btc_rate, float):
                rates[self.__userid]['btc_rate'] = {}
                rates[self.__userid]['btc_rate']['USD-BTC'] = btc_rate

            '''Запись в файл:'''
            file.seek(0)
            json.dump(rates, file, ensure_ascii=False, indent=4)
            file.truncate()

    def get_api_weather(self, cities: list):
        current_weather = {}
        forecast_weather = {}
        alerts = {}
        with open(pathes['weather'], encoding='utf-8') as f:
            weather_json = json.load(f)
        with open(pathes['bot_data'], encoding='utf-8') as f:
            bot_data = json.load(f)
        for city in cities:
            try:
                onecall = requests.get(
                    url=f"{self.BASE_URL_WEATHER_API}onecall?lat={weather_json[city]['lat']}&lon={weather_json[city]['lon']}&exclude=minutely,hourly&appid={bot_data['API_Key_weather']}&lang=ru").json()
                current_weather[city] = {}
                current_weather[city].update({'current_desc': onecall['current']['weather'][0]['description']})
                current_weather[city].update({'current_temp': f"{round(onecall['current']['temp'] - 273, 1)} C"})
                current_weather[city].update({'current_wind': f"{onecall['current']['wind_speed']} м/с"})
                current_weather[city].update({'humidity': f"{onecall['current']['humidity']} %"})  # Влажность %

                forecast_weather[f"{city}"] = {}
                timestamp = onecall['daily'][0]['dt']
                dt = str(datetime.fromtimestamp(timestamp))
                day = f"{dt[8:10]}.{dt[5:7]}.{dt[0:4]}"

                forecast_weather[city].update({'day': day})  # timestamp
                forecast_weather[city].update({'temp': onecall['daily'][0]['temp']})
                forecast_weather[city].update({'desc': onecall['daily'][0]['weather'][0]['description']})
                forecast_weather[city].update({'pop': f"{onecall['daily'][0]['pop'] * 100} %"})  # Вероятность осадков %
                forecast_weather[city].update({'humidity': f"{onecall['daily'][0]['humidity']} %"})  # Влажность %

                alerts[f"{city}"] = {}
                try:
                    alerts[f"{city}"].update({'alerts': onecall['alerts']})
                except:
                    alerts[f"{city}"].update({'alerts': [None]})
            except Exception:
                return 'Не удалось получить прогноз погоды.\n'
        return current_weather, forecast_weather, alerts

    def get_differance_in_rates(self, rub_rates, btc):
        with open(pathes['previous_rates'], encoding='utf-8') as f:
            previous_rates = json.load(f)
        dif = {'USD-BTC': 0}  # Заполняем нулями для случая, если предыдущие величины не найдены
        for rate in rub_rates['rates'].keys():
            dif[rate] = 0

        if self.__userid in previous_rates.keys():
            old_rub_rates: dict = previous_rates[self.__userid]['rub_rates']['rates']
            for rate in rub_rates['rates'].keys():
                dif[rate] = round(rub_rates['rates'][rate] - old_rub_rates[rate], 2)
            btc_rate: dict = previous_rates[self.__userid]['btc_rate']
            dif["USD-BTC"] = round(btc - btc_rate["USD-BTC"], 2)

        emoji = {rate: '\U00002934' if value >= 0.0 else '\U00002935' for rate, value in dif.items()}
        return dif, emoji

    def get_random_quote(self):
        try:
            response = requests.get(url=f'{self.RANDOM_JOKES_QUOTES}?CType=4').json(strict=False)
            return response['content']
        except Exception:
            return "Не удалось получить цитату :("

    @staticmethod
    def create_msg(rub_rates, btc, differance, weather, quote):
        # emoji_up_down = ['\U00002934' if differance[1][i] == '+' else '\U00002935' for i in range(len(differance[1]))]
        msg = ''
        if isinstance(rub_rates, dict):
            msg += f"Курс валют на {rub_rates['date']} \U0001f4c8:\n"
            for rate in rub_rates['rates'].keys():
                # msg += various_dict.get(rate,'')
                if rate == 'USD-RUB':
                    msg += f"1 доллар  = {rub_rates['rates'][rate]} рублей ({differance[1][rate]} {differance[0][rate]});\n"
                elif rate == 'EUR-RUB':
                    msg += f"1 евро      = {rub_rates['rates'][rate]} рублей ({differance[1][rate]} {differance[0][rate]});\n"
                elif rate == 'RUB-KZT':
                    msg += f"1 рубль    = {rub_rates['rates'][rate]} тенге ({differance[1][rate]} {differance[0][rate]});\n"
                elif rate == "USD-KZT":
                    msg += f"1 доллар  = {rub_rates['rates'][rate]} тенге ({differance[1][rate]} {differance[0][rate]});\n"

        elif isinstance(rub_rates, str):
            msg += rub_rates  # 'Не удалось получить курс валют.\n'
        if isinstance(btc, float):
            msg += f"1 Bitcoin   = ${btc} ({differance[1]['USD-BTC']} {differance[0]['USD-BTC']}).\n"
        elif isinstance(btc, str):
            msg += btc  # 'Не удалось получить курс BTC.\n'

        if isinstance(weather, tuple):
            msg += "\nПогода:"

            cities = []
            for city in weather[0].keys():
                cities.append(city)

            for city in cities:

                msg += f"\n\n\U0001f3e2Cейчас в {city} {weather[0][city]['current_desc']} {weather[0][f'{city}']['current_temp']}," \
                       f"\nветер {weather[0][city]['current_wind']}, влажность {weather[0][f'{city}']['humidity']}" \
                       f"\nПрогноз на {weather[1][city]['day'][0:5]}: {weather[1][city]['desc']} -" \
                       f"\nутром: {weather[1][city]['temp']['morn'] - 273:.1f} C " \
                       f"/ в обед: {weather[1][city]['temp']['day'] - 273:.1f} C" \
                       f"\nвечером: {weather[1][city]['temp']['eve'] - 273:.1f} C " \
                       f"/ ночью: {weather[1][city]['temp']['night'] - 273:.1f} C " \
                       f"\nВлажн.: {weather[1][city]['humidity']}, вер-ть осадков {weather[1][city]['pop']}"

                if weather[2][city]['alerts'] != [None]:
                    alerts = []
                    for i in range(len(weather[2][city]['alerts'])):
                        if weather[2][f'{city}']['alerts'][i]['event'][1] in 'абвгдеёжзийклмнопрстуфхцшщъыьэюя':
                            alerts.append(i)
                    if alerts:
                        msg += '\n\U0000203CПредупреждения\U0000203C'
                        for alert_indx in alerts:
                            start_timestamp = weather[2][city]['alerts'][alert_indx]['start']
                            start_dt = datetime.fromtimestamp(start_timestamp)
                            end_timestamp = weather[2][city]['alerts'][alert_indx]['end']
                            end_dt = datetime.fromtimestamp(end_timestamp)

                            msg += f"\n\U00002757 C {str(start_dt)[8:10]}.{str(start_dt)[5:7]} {str(start_dt)[11:-3]} до {str(end_dt)[8:10]}.{str(end_dt)[5:7]} {str(end_dt)[11:-3]}" \
                                   f"\n{weather[2][city]['alerts'][alert_indx]['event']}: {weather[2][city]['alerts'][alert_indx]['description']}" # TODO: format datetime via f''
        elif isinstance(weather, str):
            msg += weather

        if quote is not None:
            msg += f'\n\nСегодняшняя цитата для Вас:' \
                   f'\n{quote}'
        return msg

    def send_msg(self, msg, silent=True):
        with open(pathes['bot_data'], encoding='utf-8') as f:
            data = json.load(f)
        requests.post(url=f'{self.TELEGRAM_BOT_API}{data["Token"]}/sendMessage?chat_id={data["GroupID"]}&disable_notification={silent}&text={msg}')
        print("Cообщение успешно отправилось!")

    def get_updates(self):
        with open(pathes['bot_data'], encoding='utf-8') as f:
            data = json.load(f)
        response = requests.get(url=f'{self.TELEGRAM_BOT_API}{data["Token"]}/getUpdates').json()
        return response
