from aiogram.dispatcher.filters.state import StatesGroup, State


class Dialog(StatesGroup):
    alias = State()
    time = State()
    feedback = State()
