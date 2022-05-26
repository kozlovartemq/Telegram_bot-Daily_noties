import asyncio
import requests
import json
import logging

import schedule

from oop_bot import DailyMailing
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import Unauthorized, TelegramAPIError
import aioschedule

logging.basicConfig(filename='error.log', filemode='a', datefmt='%d-%b-%y %H:%M:%S', level=logging.ERROR)


class Dialog(StatesGroup):
    alias = State()
    time = State()
    feedback = State()


with open('bot_data.json') as datafile:
    data = json.load(datafile)

with open('weather_data.json') as w:
    weather_json = json.load(w)

with open('exchange_data.json') as e:
    exchange_json = json.load(e)

bot = Bot(token=data['Token'])
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.message_handler(commands='start')
async def start(message: types.Message):
    start_button = ['Создать оповещение!', 'Удалить оповещение!', 'Обратная связь']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_button)
    msg = 'Привет, я бот. Я могу присылать ежедневыные оповещения с указанными темами в заданное время.' \
          '\n\nЕсли Вы нашли ошибку в работе бота или у Вас есть предложения по его улучшению, запросы на новые города, ' \
          'напишите об этом через форму "Обратной связи".' \
          '\n\nТемы:' \
          '\n- Курс валют' \
          '\n- Прогноз погоды на день' \
          '\n- Случайная цитата'
    await message.answer(msg, reply_markup=keyboard)


@dp.message_handler(Text(equals='Обратная связь'))
async def listen_feedback(message: types.Message):
    msg = 'Я внимательно слушаю \U0001F442'
    await Dialog.feedback.set()
    await message.answer(msg, reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Dialog.feedback)
async def get_feedback(message: types.Message, state):
    with open('feedback.txt', 'r+') as feedbackfile:
        feed = ''
        for line in feedbackfile:
            feed += line
        feed += f'{message.from_user.id} пишет: \n{message.text}\n\n'
        feedbackfile.seek(0)
        feedbackfile.write(feed)
        feedbackfile.truncate()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('/start')
    await message.answer('Спасибо за обратную связь!', reply_markup=keyboard)
    await state.finish()
    print('NEW FEEDBACK!')


@dp.message_handler(Text(equals='Создать оповещение!'))
async def ask_for_alias(message: types.Message):
    with open('users.json', 'r+') as file:
        info: dict = json.loads(file.read())
        if str(message.from_user.id) in info.keys():
            msg = 'На вашем аккаунте уже есть оповещение!'
            buttons = ['Удалить оповещение!', 'Обратная связь']
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add(*buttons)
            reply_markup = keyboard
        else:
            msg = "Как мне Вас называть?"
            reply_markup = types.ReplyKeyboardRemove()
            await Dialog.alias.set()
        await message.answer(msg, reply_markup=reply_markup)


@dp.message_handler(state=Dialog.alias)
async def add_user(message: types.Message, state):
    # async with state.proxy() as userdata:
    user_message = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    with open('users.json', 'r+') as file:
        users = json.loads(file.read())
        users[user_id] = {}
        users[user_id]['time'] = None
        users[user_id]['username'] = username
        users[user_id]['alias'] = user_message
        users[user_id]['silent'] = False
        users[user_id]['topics'] = {}
        users[user_id]['topics']['exchange_rates'] = [False]
        users[user_id]['topics']['weather_forecast'] = [False]
        users[user_id]['topics']['quote'] = [False]

        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

    topic_buttons = ['Курс валют', 'Прогноз погоды', 'Случайная цитата']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*topic_buttons)
    await message.answer(f"Хорошо, {user_message}, выбери темы", reply_markup=keyboard)
    await state.finish()


@dp.message_handler(Text(equals='Принять'))
async def ask_for_time(message: types.Message, again=False):
    await Dialog.time.set()
    if again:
        await message.answer('Формат указан не верно, попробуй снова назначить время по Красноярскому часовому поясу: МСК+4\n'
                             'Принимается формат ЧЧ:ММ (с 00:00 до 23:59)')
    else:
        await message.answer('Принял, на какое время назначить оповещение (по Красноярскому часовому поясу: МСК+4)?\n'
                             'Принимается формат ЧЧ:ММ (с 00:00 до 23:59)',
                             reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Dialog.time)
async def add_time(message: types.Message, state):
    try:
        hours = int(message.text[0:2])
        mins = int(message.text[3:5])
        if len(message.text) == 5 and 0 <= hours <= 23 and 0 <= mins <= 59:
            with open('users.json', 'r+') as file:
                users = json.loads(file.read())
                users[str(message.from_user.id)]['time'] = message.text
                file.seek(0)
                json.dump(users, file, ensure_ascii=False, indent=4)
                file.truncate()

                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add('Настроить темы.')
                await message.answer(f'Время {message.text} установлено.', reply_markup=keyboard)
                await state.finish()
        else:
            raise Exception
    except Exception:
        await ask_for_time(message, again=True)


@dp.message_handler(Text(equals=['Настроить темы.', 'Закончить выбор']))
async def setting_topics(message: types.Message):
    with open('users.json', 'r+') as file:
        users = json.loads(file.read())
        topic_setting_buttons = []
        list_of_topic_weather = users[str(message.from_user.id)]['topics']['weather_forecast']
        list_of_topic_exchange = users[str(message.from_user.id)]['topics']['exchange_rates']
        if list_of_topic_weather[0] and len(list_of_topic_weather) == 1:
            topic_setting_buttons.append('Настроить тему "Прогноз погоды"!')
        if list_of_topic_exchange[0] and len(list_of_topic_exchange) == 1:
            topic_setting_buttons.append('Настроить тему "Курс валют"!')

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if topic_setting_buttons:
            keyboard.add(*topic_setting_buttons)
            await message.answer(f'Выбери тему для настройки', reply_markup=keyboard)
        else:
            buttons = ['Со звуком', 'Без звука']
            keyboard.add(*buttons)
            await message.answer(f'Оповещения присылать со звуком или в беззвучном режиме?', reply_markup=keyboard)


@dp.message_handler(Text(equals=['Со звуком', 'Без звука']))
async def select_silent(message: types.Message):
    with open('users.json', 'r+') as file:
        users = json.loads(file.read())
        userid = str(message.from_user.id)
        users[userid]['silent'] = True if message.text == 'Без звука' else False

        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

    with open('users.json') as file:
        users = json.loads(file.read())
        userid = str(message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('/start')
        await message.answer(f'Нечего настраивать. Увидемся в указанное время!', reply_markup=keyboard)
        aioschedule.every().day.at(users[userid]['time']).do(job, userid=message.from_user.id, dictvalue=users[userid]).tag(userid)


async def ask_for_topics(message: types.Message, users):
    topic_buttons = ['Принять']
    if not users[str(message.from_user.id)]['topics']['exchange_rates'][0]:
        topic_buttons.append('Курс валют')
    if not users[str(message.from_user.id)]['topics']['weather_forecast'][0]:
        topic_buttons.append('Прогноз погоды')
    if not users[str(message.from_user.id)]['topics']['quote'][0]:
        topic_buttons.append('Случайная цитата')
    if topic_buttons != ['Принять']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*topic_buttons)
        await message.answer(f'"{message.text}" добавлено. Еще что-нибудь?', reply_markup=keyboard)
    else:
        await ask_for_time(message)


@dp.message_handler(Text(equals=['Прогноз погоды', 'Курс валют', 'Случайная цитата']))
async def select_topics(message: types.Message):
    with open('users.json', 'r+') as file:  # TODO: Попробовать определить контекстный менеджер в глобал скоупе для users.json, а не переопределять его везде
        users = json.loads(file.read())
        various_dict = {
            'Прогноз погоды': users[str(message.from_user.id)]['topics']['weather_forecast'],
            'Курс валют': users[str(message.from_user.id)]['topics']['exchange_rates'],
            'Случайная цитата': users[str(message.from_user.id)]['topics']['quote']
        }
        various_dict.get(message.text).insert(0, True)  # Рефакторинг (убрал elif)
        various_dict.get(message.text).pop()

        '''Запись в файл:'''
        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

        await ask_for_topics(message, users)


@dp.message_handler(Text(equals='Настроить тему "Прогноз погоды"!'))
async def select_weather(message: types.Message):
    weather_cities = weather_json['Cities']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*weather_cities)
    await message.answer(f'Выбери из доступных городов', reply_markup=keyboard)


async def ask_for_cities(message: types.Message, users):
    cities_buttons = ['Закончить выбор']
    for city in weather_json['Cities']:
        if city not in users[str(message.from_user.id)]['topics']['weather_forecast'][1:]:
            cities_buttons.append(city)
    if len(cities_buttons) != 1:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*cities_buttons)
        await message.answer(f'Выбран город {message.text}. Добавить еще?', reply_markup=keyboard)
    else:
        await setting_topics(message)


@dp.message_handler(Text(equals=weather_json['Cities']))
async def select_weather_city(message: types.Message):
    with open('users.json', 'r+') as file:
        users = json.loads(file.read())
        users[str(message.from_user.id)]['topics']['weather_forecast'].append(message.text)
        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

        await ask_for_cities(message, users)


@dp.message_handler(Text(equals='Настроить тему "Курс валют"!'))
async def select_exchange(message: types.Message):
    exchange_pairs = exchange_json['Pairs']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*exchange_pairs)
    await message.answer(f'Выбери из доступных валютных пар', reply_markup=keyboard)


async def ask_for_rates(message: types.Message, users):
    pairs_buttons = ['Закончить выбор']
    for pair in exchange_json['Pairs']:
        if pair not in users[str(message.from_user.id)]['topics']['exchange_rates'][1:]:
            pairs_buttons.append(pair)

    if len(pairs_buttons) != 1:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*pairs_buttons)
        await message.answer(f'Выбрана пара {message.text}. Добавить еще?', reply_markup=keyboard)
    else:
        await setting_topics(message)


@dp.message_handler(Text(equals=exchange_json['Pairs']))
async def select_exchange_rates(message: types.Message):
    with open('users.json', 'r+') as file:
        users = json.loads(file.read())
        users[str(message.from_user.id)]['topics']['exchange_rates'].append(message.text)
        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

        await ask_for_rates(message, users)


@dp.message_handler(Text(equals='Удалить оповещение!'))
async def delete_notify(message: types.Message):
    with open('previous_rates.json', 'r+') as previous_ratesfile:
        old_rates: dict = json.loads(previous_ratesfile.read())
        if str(message.from_user.id) in old_rates.keys():
            old_rates.pop(str(message.from_user.id))
            '''Запись в файл:'''
            previous_ratesfile.seek(0)
            json.dump(old_rates, previous_ratesfile, ensure_ascii=False, indent=4)
            previous_ratesfile.truncate()

    with open('users.json', 'r+') as file:
        info: dict = json.loads(file.read())
        if str(message.from_user.id) in info.keys():
            info.pop(str(message.from_user.id))
            '''Запись в файл:'''
            file.seek(0)
            json.dump(info, file, ensure_ascii=False, indent=4)
            file.truncate()
            msg = 'Оповещение удалено!'
            aioschedule.clear(str(message.from_user.id))  # Удалить рассылку из планировщика. Проверка: 2 плановых, 1 пересоздать

        else:
            msg = 'На вашем аккаунте нет оповещений!'
        buttons = ['Создать оповещение!', 'Обратная связь']
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer(msg, reply_markup=keyboard)


@dp.errors_handler(exception=Unauthorized)
async def error_bot_blocked(update: types.Update, exception: Unauthorized):
    # update: объект события от telegram.
    print(f"Unauthorized error!\n{update}\n{exception}")


@dp.errors_handler(exception=TelegramAPIError)
async def catch_exception(update: types.Update, exception):
    print(f"error!\n{update}\n{exception}")
    # await start()
    return True

@dp.errors_handler(exception=Exception)
async def catch_exception2(update: types.Update, exception):
    print(f"error!\n{update}\n{exception}")
    # await start(message)
    return True
#TODO: add exceptions


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
        rates_without_btc = set(exchange_rates[1:])
        rates_without_btc.discard("USD-BTC")  # Удалится, если есть

        if len(rates_without_btc):
            try:
                rates = session.get_rates(rates_without_btc)
            except Exception:
                rates = session.get_rates_from_exchangerate(rates_without_btc)

        if rates_without_btc != exchange_rates[1:]:
            btc = session.parse_btc_rate()

        if isinstance(rates, dict) and isinstance(btc, float):
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


# def update_users():
    # with open('users.json') as userfile:
    #     users = json.load(userfile)
    # for user, dictvalue in users.items():
    #     await aioschedule.every().day.at(dictvalue['time']).do(job, userid=user, dictvalue=dictvalue)
    # return users


async def scheduler():
    # users = schedule.every().minute.do(update_users).
    with open('users.json') as userfile:
        users = json.load(userfile)
    for user, dictvalue in users.items():
        aioschedule.every().day.at(dictvalue['time']).do(job, userid=user, dictvalue=dictvalue).tag(user)  # Запланировать старые оповещения

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def on_startup(_):
    asyncio.create_task(scheduler())


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
