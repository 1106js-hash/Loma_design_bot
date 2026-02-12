from aiogram.fsm.state import State, StatesGroup

class FormState(StatesGroup):
    name = State()
    phone = State()
    email = State()
