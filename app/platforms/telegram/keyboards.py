from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Заполнить ТЗ",
                    callback_data="start_tz"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📩 Оставить заявку",
                    callback_data="start_form"
                )
            ]
        ]
    )
