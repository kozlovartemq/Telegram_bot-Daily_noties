from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import json


with open('data/bot_data.json', encoding='utf-8') as datafile:
    data = json.load(datafile)

bot = Bot(token=data['Token'])
dp = Dispatcher(bot, storage=MemoryStorage())
