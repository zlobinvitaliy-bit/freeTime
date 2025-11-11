# states/states.py
from aiogram.fsm.state import State, StatesGroup

class EventStates(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()