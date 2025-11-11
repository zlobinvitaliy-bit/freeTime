# states/states.py
from aiogram.fsm.state import StatesGroup, State

class EventStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_new_time = State() # Новое состояние для ожидания ввода нового времени
