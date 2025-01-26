import logging
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import pathlib
from pathlib import Path


pathes = {
    'weather': f"{str(Path(pathlib.Path.cwd() / 'data' / 'weather_data.json'))}",
    'previous_rates': f"{str(Path(pathlib.Path.cwd() / 'data' / 'previous_rates.json'))}",
    'bot_data': f"{str(Path(pathlib.Path.cwd() / 'data' / 'bot_data.json'))}",
    'users': f"{str(Path(pathlib.Path.cwd() / 'data' / 'users.json'))}"
}


class DailyMailing:
    RUB_URL = 'https://www.cbr-xml-daily.ru/latest.js'
    ALTERNATIVE_EXCHANGE_RATES_API = 'https://api.exchangerate-api.com/v4/latest/'
    BASE_URL_WEATHER_API = 'http://api.openweathermap.org/data/3.0/'
    BASE_URL_BTC_PARSE = 'https://www.google.com/'
    BASE_URL_BTC_API = 'https://openapiv1.coinstats.app'
    RANDOM_JOKES_QUOTES = 'http://rzhunemogu.ru/RandJSON.aspx'
    BASE_URL_AIR_POLLUTION = 'https://nebo.live/ru/'
    BASE_URL_NEBO_API = 'https://nebo.live/api/v2/en/'
    BASE_URL_FACT_PARSE = 'https://randstuff.ru/fact/'

    def __init__(self, userid: str):
        self.__userid: str = userid
        self.exchange_rates = []

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
            rub_cad_rate = round(1 / response['rates']['CAD'], 2)
            kzt_rub_rate = round(response['rates']['KZT'], 2)
            kzt_usd_rate = round(rub_usd_rate * kzt_rub_rate, 2)
        except Exception as ex:
            logging.exception(f"[get_rates]:\n{ex}")
            return 'Не удалось получить курс валют.\n'
        result_dict = dict(date=date, rates=dict())
        if 'USD-RUB' in exchange_rates:
            result_dict['rates']['USD-RUB'] = rub_usd_rate
        if 'EUR-RUB' in exchange_rates:
            result_dict['rates']['EUR-RUB'] = rub_eur_rate
        if 'CAD-RUB' in exchange_rates:
            result_dict['rates']['CAD-RUB'] = rub_cad_rate
        if 'RUB-KZT' in exchange_rates:
            result_dict['rates']['RUB-KZT'] = kzt_rub_rate
        if 'USD-KZT' in exchange_rates:
            result_dict['rates']['USD-KZT'] = kzt_usd_rate

        return result_dict

    def get_rates_from_exchangerate(self, exchange_rates: set):
        try:
            response_usd = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}USD').json()
            response_eur = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}EUR').json()
            response_cad = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}CAD').json()
            response_rub = requests.get(url=f'{self.ALTERNATIVE_EXCHANGE_RATES_API}RUB').json()
            date = f"{response_usd['date'][8:]}.{response_usd['date'][5:7]}.{response_usd['date'][0:4]}"
            rub_usd_rate = response_usd['rates']['RUB']
            rub_eur_rate = response_eur['rates']['RUB']
            rub_cad_rate = response_cad['rates']['RUB']
            kzt_rub_rate = response_rub['rates']['KZT']
            kzt_usd_rate = response_usd['rates']['KZT']
            result_dict = dict(date=date, rates=dict())
            if 'USD-RUB' in exchange_rates:
                result_dict['rates']['USD-RUB'] = rub_usd_rate
            if 'EUR-RUB' in exchange_rates:
                result_dict['rates']['EUR-RUB'] = rub_eur_rate
            if 'CAD-RUB' in exchange_rates:
                result_dict['rates']['CAD-RUB'] = rub_cad_rate
            if 'RUB-KZT' in exchange_rates:
                result_dict['rates']['RUB-KZT'] = kzt_rub_rate
            if 'USD-KZT' in exchange_rates:
                result_dict['rates']['USD-KZT'] = kzt_usd_rate

            return result_dict
        except Exception as ex:
            logging.exception(f"[get_rates_from_exchangerate]:\n{ex}")
            return 'Не удалось получить курс валют.\n'

    def parse_btc_rate_google_finance(self):
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
        except Exception as ex:
            logging.exception(f"[parse_btc_rate_google_finance]:\n{ex}")
            return 'Не удалось получить курс BTC.\n'
        return float_btc

    def parse_btc_rate_google(self):
        try:
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
            }
            response = requests.get(url=f'{self.BASE_URL_BTC_PARSE}search?q=btc+usd', headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            btc_rate_span = soup.find('span', class_="pclqee")
            btc_rate = btc_rate_span.text
            float_btc = float(btc_rate.replace(',', '.').replace('\xa0', ''))
        except Exception as ex:
            logging.exception(f"[parse_btc_rate_google]:\n{ex}")
            return 'Не удалось получить курс BTC.\n'
        return float_btc

    def parse_btc_rate(self):
        try:
            with open(pathes['bot_data'], encoding='utf-8') as f:
                bot_data = json.load(f)
            headers = {
                'Accept': 'application/json',
                'X-API-KEY': bot_data['API_Coinstat_key']
            }
            response = requests.get(url=f'{self.BASE_URL_BTC_API}/coins/bitcoin?currency=USD', headers=headers).json()
            btc_rate = round(response["price"], 2)
        except Exception as ex:
            logging.exception(f"[parse_btc_rate]:\n{ex}")
            return 'Не удалось получить курс BTC.\n'
        return btc_rate

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
                ya_pogoda = requests.get(url=f"https://api.weather.yandex.ru/v2/forecast?lat={weather_json[city]['lat']}&lon={weather_json[city]['lon']}&lang=ru_RU&limit=2",
                                         headers={'X-Yandex-Weather-Key': bot_data['API_Yapogoda_key']}).json()
                ya_pogoda_fact = ya_pogoda['fact']
                desc_map = {
                    'clear': 'ясно',
                    'partly-cloudy': 'малооблачно',
                    'cloudy': 'облачно с прояснениями',
                    'overcast': 'пасмурно',
                    'light-rain': 'небольшой дождь',
                    'rain': 'дождь',
                    'heavy-rain': 'сильный дождь',
                    'showers': 'ливень',
                    'wet-snow': 'дождь со снегом',
                    'light-snow': 'небольшой дождь',
                    'snow': 'снег',
                    'snow-showers': 'снегопад',
                    'hail': 'град',
                    'thunderstorm': 'гроза',
                    'thunderstorm-with-rain': 'дождь с грозой',
                    'thunderstorm-with-hail': 'гроза с градом',
                }
                phenom_desc = {
                    'fog': 'туман',
                    'mist': 'дымка',
                    'smoke': 'смог',
                    'dust': 'пыль',
                    'dust-suspension': 'пылевая взвесь',
                    'duststorm': 'пыльная буря',
                    'thunderstorm-with-duststorm': 'пыльная буря с грозой',
                    'drifting-snow': 'слабая метель',
                    'blowing-snow': 'метель',
                    'ice-pellets': 'ледяная крупа',
                    'freezing-rain': 'ледяной дождь',
                    'tornado': 'торнадо',
                    'volcanic-ash': 'вулканический пепел',
                }
                current_weather[city] = {}
                current_weather[city].update({'condition': desc_map.get(ya_pogoda_fact['condition'], ya_pogoda_fact['condition'])})
                current_weather[city].update({'phenom_condition': phenom_desc.get(ya_pogoda_fact.get('phenom_condition'))})
                current_weather[city].update({'temp': ya_pogoda_fact['temp']})
                current_weather[city].update({'wind_speed': ya_pogoda_fact['wind_speed']})
                current_weather[city].update({'wind_gust': ya_pogoda_fact['wind_gust']})

                ya_pogoda_forecast = ya_pogoda['forecasts'][0]
                ya_pogoda_forecast2 = ya_pogoda['forecasts'][1]  # for the next night
                forecast_weather[city] = {}
                forecast_weather[city].update({'date': ya_pogoda_forecast['date']})
                forecast_weather[city].update({'sunrise': ya_pogoda_forecast['sunrise']})
                forecast_weather[city].update({'sunset': ya_pogoda_forecast['sunset']})
                forecast_weather[city].update({'day': ya_pogoda_forecast['parts']['day']})
                day_condition = forecast_weather[city]['day']['condition']
                forecast_weather[city]['day'].update({'condition': desc_map.get(day_condition, day_condition)})

                forecast_weather[city].update({'morning': ya_pogoda_forecast['parts']['morning']})
                morning_condition = forecast_weather[city]['morning']['condition']
                forecast_weather[city]['morning'].update({'condition': desc_map.get(morning_condition, morning_condition)})

                forecast_weather[city].update({'night': ya_pogoda_forecast2['parts']['night']})
                night_condition = forecast_weather[city]['night']['condition']
                forecast_weather[city]['night'].update({'condition': desc_map.get(night_condition, night_condition)})

                alerts[city] = {}
                if city == 'Krasnoyarsk':
                    try:
                        alerts_response = requests.post(url=f"https://meteoinfo.ru/hmc-output/meteoalert/map_fed_data.php", data=dict(id_fed='7', type='0-24', id_lang='1')).json()
                        alerts[city].update({'alerts': list(alerts_response['87'].values())})
                    except Exception:
                        alerts[city].update({'alerts': [None]})
                elif city == 'Novosibirsk':
                    try:
                        alerts_response = requests.post(url=f"https://meteoinfo.ru/hmc-output/meteoalert/map_fed_data.php", data=dict(id_fed='7', type='0-24', id_lang='1')).json()
                        alerts[city].update({'alerts': list(alerts_response['46'].values())})
                    except Exception:
                        alerts[city].update({'alerts': [None]})
                elif city == 'Moscow':
                    try:
                        alerts_response = requests.post(url=f"https://meteoinfo.ru/hmc-output/meteoalert/map_fed_data.php", data=dict(id_fed='1', type='0-24', id_lang='1')).json()
                        alerts[city].update({'alerts': list(alerts_response['102'].values())})
                    except Exception:
                        alerts[city].update({'alerts': [None]})
            except Exception as ex1:
                logging.exception(f"[get_api_weather]:\n{ex1}")
                return 'Не удалось получить прогноз погоды.\n'
        return current_weather, forecast_weather, alerts

    def parse_air_pollution(self, cities: list):
        air_pollution_values = {}
        for city in cities:
            try:
                sensors = {
                    'Krasnoyarsk': 'krs/sensors/ulitsa-petra-lomako-14',
                    'Novosibirsk': 'novosibirsk/sensors/sibrevcom-street-71',
                    'Moscow': 'moscow/sensors/zvyozdnyi-bulvar-4',
                    'Nur-Sultan': ''
                }
                if not sensors[city]:
                    air_pollution_values[city] = ''
                    continue
                headers = {
                    'Accept': '*/*',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
                }
                response = requests.get(url=f'{self.BASE_URL_AIR_POLLUTION}{sensors[city]}', headers=headers)
                soup = BeautifulSoup(response.text, 'lxml')
                pm2_5 = soup.find('table').find('tr').find_all('td')[1]
                pm25_text = pm2_5.text
                float_pm25 = float(pm25_text.rstrip().split()[0])
                air_pollution_values[city] = float_pm25
            except Exception as ex:
                logging.exception(f"[parse_air_pollution]:\n{ex}")
                air_pollution_values[city] = ''
        return air_pollution_values

    def get_air_pollution(self, cities: list):
        import hashlib

        air_pollution_values = {}
        with open(pathes['weather']) as f:
            weather_json = json.load(f)
        with open(pathes['bot_data'], encoding='utf-8') as f:
            bot_data = json.load(f)

        timestamp_str = str(datetime.now().replace(microsecond=0).timestamp())[:-2]
        url_hash = hashlib.sha1((timestamp_str + bot_data["nebo_code"]).encode('utf-8')).hexdigest()[5:16]
        for city in cities:
            avg_instant_pm25 = ''
            try:
                response = requests.get(f'{self.BASE_URL_NEBO_API}cities/{weather_json[city]["nebo_url"]}?time={timestamp_str}&hash={url_hash}',
                                        headers={'X-Auth-Nebo': bot_data["nebo_token"]}).json()
                pm25 = [item['instant']['pm25'] for item in response if item['instant']['pm25'] is not None]

                if len(pm25):
                    avg_instant_pm25 = round(sum(pm25) / len(pm25), 1)
            except Exception as ex:
                logging.exception(f"[get_api_weather]:\n{ex}")
            air_pollution_values.update({city: avg_instant_pm25})
        return air_pollution_values

    def get_differance_in_rates(self, rub_rates, btc):
        with open(pathes['previous_rates'], encoding='utf-8') as f_pr:
            previous_rates = json.load(f_pr)

        rates_without_btc = set(self.exchange_rates)
        rates_without_btc.discard("USD-BTC")  # Удалится, если есть

        """Заполняем нулями для случая, если предыдущие величины не найдены"""
        dif = dict()    #
        if 'USD-BTC' in self.exchange_rates:
            dif['USD-BTC'] = 0
        for rate in tuple(rates_without_btc):
            dif[rate] = 0

        """Заполняем предыдущими величинами, если есть"""
        user_id = str(self.__userid)
        if user_id in previous_rates.keys():
            if 'rub_rates' in previous_rates[user_id].keys() and isinstance(rub_rates, dict):
                old_rub_rates: dict = previous_rates[user_id]['rub_rates']['rates']
                for rate in rub_rates['rates'].keys():
                    dif[rate] = round(rub_rates['rates'][rate] - old_rub_rates[rate], 2)
            if "btc_rate" in previous_rates[user_id].keys() and isinstance(btc, float):
                btc_rate: dict = previous_rates[user_id]['btc_rate']
                dif["USD-BTC"] = round(btc - btc_rate["USD-BTC"], 2)

        emoji = {rate: '\U00002934' if value >= 0.0 else '\U00002935' for rate, value in dif.items()}
        return dif, emoji

    def get_random_quote(self):
        try:
            response = requests.get(url=f'{self.RANDOM_JOKES_QUOTES}?CType=4').json(strict=False)
            return response['content']
        except Exception as ex:
            logging.exception(f"[get_random_quote]:\n{ex}")
            return "Не удалось получить цитату :("

    def parse_random_fact(self):
        try:
            headers = {
                'Accept': '*/*',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36'
            }
            response = requests.get(url=self.BASE_URL_FACT_PARSE, headers=headers)
            soup = BeautifulSoup(response.text, 'lxml')
            table = soup.find('table', class_='text')
            fact = table.text
        except Exception as ex:
            logging.exception(f"[parse_random_fact]:\n{ex}")
            return 'Не удалось получить факт.\n'
        return fact

    @staticmethod
    def create_msg(rub_rates, btc, differance, weather, air_pollution, quote):
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
                elif rate == 'CAD-RUB':
                    msg += f"1 кан. доллар = {rub_rates['rates'][rate]} рублей ({differance[1][rate]} {differance[0][rate]});\n"
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
            reaction_emojes = {
                'innocent': '\U0001f607',  # <= 10
                'neutral_face': '\U0001f610',  # 10 < x <= 35
                'grimacing': '\U0001f62c',  # 35 < x <= 60
                'face_with_symbols': '\U0001f92c',  # 60 < x <= 150
                'skull_bones': '\U00002620'  # > 150
            }
            msg += "\nПогода:"

            for city in weather[0].keys():

                ru_cities_map = {
                    "Krasnoyarsk": 'Красноярске',
                    "Novosibirsk": 'Новосибирске',
                    "Moscow": 'Москве',
                    "Nur-Sultan": 'Астане',
                }

                msg += f"\n\n\U0001f3e2Cейчас в {ru_cities_map[city]} {weather[0][city]['condition']}{' ('+weather[0][city]['phenom_condition']+')' if weather[0][city]['phenom_condition'] else ''} {weather[0][f'{city}']['temp']}° C," \
                       f"\nветер {weather[0][city]['wind_speed']} м/с с порывами до {weather[0][city]['wind_gust']} м/с." \
                       f"\nПрогноз на {datetime.fromisoformat(weather[1][city]['date']).strftime('%d.%m.%Y')}:" \
                       f"\nВосход-закат {weather[1][city]['sunrise']}-{weather[1][city]['sunset']}" \
                       f"\nутром: {weather[1][city]['morning']['condition']} {weather[1][city]['morning']['temp_min']}° C, ветер {weather[1][city]['morning']['wind_speed']}({weather[1][city]['morning']['wind_gust']}) м/с" \
                       f"\nв обед: {weather[1][city]['day']['condition']} {weather[1][city]['day']['temp_min']}° C, ветер {weather[1][city]['day']['wind_speed']}({weather[1][city]['day']['wind_gust']}) м/с" \
                       f"\nночью: {weather[1][city]['night']['condition']} {weather[1][city]['night']['temp_min']}° C, ветер {weather[1][city]['night']['wind_speed']}({weather[1][city]['night']['wind_gust']}) м/с"

                if weather[2][city]['alerts'] != [None]:
                    alerts = []
                    for alert in weather[2][city]['alerts']:
                        if alert['3'] != 'Оповещения о погоде не требуется':
                            alerts.append(alert)
                    if alerts:
                        msg += '\n\U0000203CПредупреждения\U0000203C'
                        for alert in alerts:
                            start_timestamp = float(alert['0'])
                            start_dt = datetime.fromtimestamp(start_timestamp)
                            end_timestamp = float(alert['1'])
                            end_dt = datetime.fromtimestamp(end_timestamp)

                            msg += f"\n\U00002757 C {start_dt:%d.%m %H:%M} до {end_dt:%d.%m %H:%M}" \
                                   f"\n{alert['3']}: {alert['4']}"

                pollution_value = air_pollution[city]
                if isinstance(pollution_value, float):
                    if pollution_value <= 10:
                        emoji = reaction_emojes['innocent']
                    elif 10 < pollution_value <= 35:
                        emoji = reaction_emojes['neutral_face']
                    elif 35 < pollution_value <= 60:
                        emoji = reaction_emojes['grimacing']
                    elif 60 < pollution_value <= 150:
                        emoji = reaction_emojes['face_with_symbols']
                    else:
                        emoji = reaction_emojes['skull_bones']
                    msg += f'\n\U00002757 Уровень загрязнения воздуха (PM2.5)' \
                           f'\nв данный момент: {pollution_value} µg/m3 {emoji}'

        elif isinstance(weather, str):
            msg += weather

        if quote is not None:
            msg += f'\n\nСегодняшний факт для Вас:' \
                   f'\n{quote}'
        return msg


TELEGRAM_BOT_API = 'https://api.telegram.org/bot'
with open(pathes['bot_data'], encoding='utf-8') as f:
    data = json.load(f)


def send_msg(msg, chat_id: str, silent=True):
    requests.post(url=f'{TELEGRAM_BOT_API}{data["Token"]}/sendMessage?chat_id={chat_id}&disable_notification={silent}&text={msg}')
    print(f"Cообщение успешно отправилось! ({msg})")


def send_to_admin(msg, silent=True):
    send_msg(msg=msg, chat_id=data['admin'], silent=silent)


def get_updates():
    response = requests.get(url=f'{TELEGRAM_BOT_API}{data["Token"]}/getUpdates').json()
    return response


if __name__ == "__main__":
    ses = DailyMailing("23")
    # a = ses.get_rates_from_exchangerate({'USD-RUB', 'EUR-RUB', 'CAD-RUB', 'RUB-KZT', 'USD-KZT'})
    # b = ses.get_air_pollution(["Krasnoyarsk", "Novosibirsk", "Moscow", "Nur-Sultan"])
    # c = ses.get_api_weather(["Krasnoyarsk", "Novosibirsk", "Moscow", "Nur-Sultan"])
    c = ses.get_api_weather(["Krasnoyarsk"])
    # d = ses.parse_random_fact()
    # ses.parse_btc_rate()
    # print(c)
