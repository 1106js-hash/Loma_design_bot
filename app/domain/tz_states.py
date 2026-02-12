from aiogram.fsm.state import StatesGroup, State


class TZState(StatesGroup):
    choosing_section = State()
    answering = State()
