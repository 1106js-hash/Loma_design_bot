from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_form_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к заполнению", callback_data="start_form")]
        ]
    )
