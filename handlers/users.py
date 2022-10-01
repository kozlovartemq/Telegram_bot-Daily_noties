import json
import pathlib
from pathlib import Path
from datetime import datetime
from aiogram import types
from aiogram.dispatcher.filters import Text
import aioschedule
from loader import dp
from app import job
from states.dialog import Dialog
from utils.check_input_format import is_string_allowed, is_time_allowed
from utils.notify_mailing import send_to_admin

pathes = {
    'weather': f"{str(Path(pathlib.Path.cwd() / 'data' / 'weather_data.json'))}",
    'exchange_data': f"{str(Path(pathlib.Path.cwd() / 'data' / 'exchange_data.json'))}",
    'users': f"{str(Path(pathlib.Path.cwd() / 'data' / 'users.json'))}",
    'feedback': f"{str(Path(pathlib.Path.cwd() / 'data' / 'feedback.txt'))}",
    'previous_rates': f"{str(Path(pathlib.Path.cwd() / 'data' / 'previous_rates.json'))}"
}

with open(pathes['weather'], encoding='utf-8') as w:
    weather_json = json.load(w)

with open(pathes['exchange_data'], encoding='utf-8') as e:
    exchange_json = json.load(e)


@dp.message_handler(commands='start')
async def start(message: types.Message):
    start_button = ['Создать оповещение!', 'Удалить оповещение!', 'Обратная связь']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_button)
    msg = 'Привет, я бот. Я могу присылать ежедневные оповещения с указанными темами в заданное время.' \
          '\n\nЕсли Вы нашли ошибку в работе бота или у Вас есть предложения по его улучшению, запросы на новые темы,' \
          ' новые города, напишите об этом через форму "Обратной связи".' \
          '\n\nТемы:' \
          '\n- Курс валют' \
          '\n- Прогноз погоды на день' \
          '\n- Случайная цитата'
    await message.answer(msg, reply_markup=keyboard)


@dp.message_handler(Text(equals='Обратная связь'))
async def listen_feedback(message: types.Message, again=False):
    await Dialog.feedback.set()
    if again:
        await message.answer('Вы отправли запрещенный символ, попробуйте еще раз \U0001F442')
    else:
        await message.answer('Я внимательно слушаю \U0001F442',
                             reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Dialog.feedback)
async def get_feedback(message: types.Message, state):
    if not is_string_allowed(message.text):
        await listen_feedback(message, again=True)
    else:
        with open(pathes['feedback'], 'r+', encoding='utf-8') as feedbackfile:
            feed = ''
            for line in feedbackfile:
                feed += line
            feed += f'{message.from_user.id} пишет в {datetime.now()}: \n{message.text}\n\n'
            feedbackfile.seek(0)
            feedbackfile.write(feed)
            feedbackfile.truncate()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('/start')
        await message.answer('Спасибо за обратную связь!', reply_markup=keyboard)
        await state.finish()
        print_msg = f'New feedback from user {message.from_user.id}'
        print(print_msg)
        send_to_admin(print_msg)


@dp.message_handler(Text(equals='Создать оповещение!'))
async def ask_for_alias(message: types.Message, again=False):
    if again:
        await Dialog.alias.set()
        await message.answer('Вы отправли запрещенный символ, попробуйте еще раз.\nКак мне Вас называть?')

    else:
        with open(pathes['users'], 'r+', encoding='utf-8') as file:
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
    if not is_string_allowed(message.text):
        await ask_for_alias(message, again=True)
    else:
        user_message = message.text
        user_id = message.from_user.id
        username = message.from_user.username
        with open(pathes['users'], 'r+', encoding='utf-8') as file:
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
        await message.answer('Формат указан не верно, попробуй снова назначить время по часовому поясу UTC (МСК-3).\n'
                             'Принимается формат ЧЧ:ММ (с 00:00 до 23:59)')
    else:
        await message.answer('Принял, на какое время назначить оповещение по часовому поясу UTC (МСК-3)?\n'
                             'Принимается формат ЧЧ:ММ (с 00:00 до 23:59)',
                             reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Dialog.time)
async def add_time(message: types.Message, state):
    if not is_time_allowed(message.text):
        await ask_for_time(message, again=True)
    else:

        with open(pathes['users'], 'r+', encoding='utf-8') as file:
            users = json.loads(file.read())
            if not str(message.from_user.id) in users.keys():  # Вдруг кто-то прожмет "Принять" до создания оповещения
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add('/start')
                await message.answer("Так делать нельзя! Следуй инструкции, пожалуйста", reply_markup=keyboard)
            else:
                users[str(message.from_user.id)]['time'] = message.text
                file.seek(0)
                json.dump(users, file, ensure_ascii=False, indent=4)
                file.truncate()

                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                keyboard.add('Настроить темы.')
                await message.answer(f'Время {message.text} установлено.', reply_markup=keyboard)
            await state.finish()


@dp.message_handler(Text(equals=['Настроить темы.', 'Закончить выбор']))
async def setting_topics(message: types.Message):
    with open(pathes['users'], 'r+', encoding='utf-8') as file:
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
    with open(pathes['users'], 'r+', encoding='utf-8') as file:
        users = json.loads(file.read())
        userid = str(message.from_user.id)
        users[userid]['silent'] = True if message.text == 'Без звука' else False

        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

    with open(pathes['users'], encoding='utf-8') as file:
        users = json.loads(file.read())
        userid = str(message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('/start')
        await message.answer(f'Нечего настраивать. Увидимся в указанное время!', reply_markup=keyboard)
        aioschedule.every().day.at(users[userid]['time']).do(job, userid=message.from_user.id, dictvalue=users[userid]).tag(userid)
        print_msg = f"Джоб для {userid} запланирован"
        print(print_msg)
        send_to_admin(print_msg)


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
    with open(pathes['users'], 'r+', encoding='utf-8') as file:
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
    with open(pathes['users'], 'r+', encoding='utf-8') as file:
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
    with open(pathes['users'], 'r+', encoding='utf-8') as file:
        users = json.loads(file.read())
        users[str(message.from_user.id)]['topics']['exchange_rates'].append(message.text)
        file.seek(0)
        json.dump(users, file, ensure_ascii=False, indent=4)
        file.truncate()

        await ask_for_rates(message, users)


@dp.message_handler(Text(equals='Удалить оповещение!'))
async def delete_notify(message: types.Message):
    with open(pathes['previous_rates'], 'r+', encoding='utf-8') as previous_ratesfile:
        old_rates: dict = json.loads(previous_ratesfile.read())
        if str(message.from_user.id) in old_rates.keys():
            old_rates.pop(str(message.from_user.id))
            '''Запись в файл:'''
            previous_ratesfile.seek(0)
            json.dump(old_rates, previous_ratesfile, ensure_ascii=False, indent=4)
            previous_ratesfile.truncate()

    with open(pathes['users'], 'r+', encoding='utf-8') as file:
        info: dict = json.loads(file.read())
        if str(message.from_user.id) in info.keys():
            info.pop(str(message.from_user.id))
            '''Запись в файл:'''
            file.seek(0)
            json.dump(info, file, ensure_ascii=False, indent=4)
            file.truncate()
            msg = 'Оповещение удалено!'
            userid = str(message.from_user.id)
            aioschedule.clear(userid)  # Удалить имеющуюся рассылку для юзера из планировщика
            print_msg = f"Запланированный джоб для {userid} удален"
            print(print_msg)
            send_to_admin(print_msg)


        else:
            msg = 'На вашем аккаунте нет оповещений!'
        buttons = ['Создать оповещение!', 'Обратная связь']
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*buttons)
        await message.answer(msg, reply_markup=keyboard)