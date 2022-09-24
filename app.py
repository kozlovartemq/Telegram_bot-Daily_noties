from loader import dp
import requests
from utils.notify_mailing import DailyMailing
import middlewares, handlers
import json
import aioschedule
import asyncio
from aiogram import executor
import logging

logging.basicConfig(filename='data/error.log', filemode='a', datefmt='%d-%b-%y %H:%M:%S', level=logging.ERROR)

with open('data/bot_data.json', encoding='utf-8') as datafile:
    data = json.load(datafile)


async def job(userid: str, dictvalue: dict):
    alias = dictvalue['alias']
    silent = dictvalue['silent']
    exchange_rates = dictvalue['topics']['exchange_rates']
    weather_forecast = dictvalue['topics']['weather_forecast']
    quote = dictvalue['topics']['quote']
    session = DailyMailing(userid)
    msg = f'Здравствуйте, {alias}!\n'
    rates, btc, rate_differance, weather, rnd_quote = (None,)*5

    if exchange_rates[0]:
        session.exchange_rates = exchange_rates[1:]
        rates_without_btc = set(session.exchange_rates)
        rates_without_btc.discard("USD-BTC")  # Удалится, если есть

        if len(rates_without_btc):
            try:
                rates = session.get_rates(rates_without_btc)
            except Exception:
                rates = session.get_rates_from_exchangerate(rates_without_btc)

        if rates_without_btc != set(exchange_rates[1:]):
            btc = session.parse_btc_rate()

        if isinstance(rates, dict) or isinstance(btc, float):
            rate_differance = session.get_differance_in_rates(rates, btc)
            session.save_history_of_rates(rates, btc)
    if weather_forecast[0]:
        weather = session.get_api_weather(weather_forecast[1:])
    if quote[0]:
        rnd_quote = session.get_random_quote()
    try:
        msg += session.create_msg(rates, btc, rate_differance, weather, rnd_quote)
        requests.post(
            url=f'https://api.telegram.org/bot{data["Token"]}/sendMessage?chat_id={userid}&disable_notification={silent}&text={msg}')
        print(f'Оповещение {userid} отправлено в {dictvalue["time"]}')
    except Exception as ex:
        try:
            silent = dictvalue['silent']
            msg = 'Извините, сегодня не удалось подготовить оповещение, что-то сломалось :(\n'
            requests.post(
                     url=f'https://api.telegram.org/bot{data["Token"]}/sendMessage?chat_id={userid}&disable_notification={silent}&text={msg}')

            logging.exception(msg)
            print(msg, 'user: ', userid)
        except Exception as ex2:
            logging.exception('\nДаже сообщение об ошибке не отправилось...\n')
            print('Даже сообщение об ошибке не отправилось... Смотри логи.')


async def scheduler():
    with open('data/users.json', encoding='utf-8') as userfile:
        users = json.load(userfile)
    for user, dictvalue in users.items():
        aioschedule.every().day.at(dictvalue['time']).do(job, userid=user, dictvalue=dictvalue).tag(user)  # Запланировать старые оповещения
    for running_job in aioschedule.jobs:
        print(running_job)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
