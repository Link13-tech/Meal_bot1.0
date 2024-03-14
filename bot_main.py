import asyncio
from aiogram.enums import ParseMode
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import F
from aiogram.utils.formatting import (Bold, as_list, as_marked_section)
from recipes_handler import router
from token_data import TOKEN

dp = Dispatcher()
dp.include_router(router)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    kb = [
        [
            types.KeyboardButton(text="Команды"),
            types.KeyboardButton(text="Описание бота"),
        ],
    ]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
    )
    await message.answer(f"Привет *{message.from_user.full_name}!* С чего начнем?",
                         parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


@dp.message(F.text.lower() == "описание бота")
async def description(message: types.Message):
    await message.answer("Этот бот предоставляет информацию о рецептах, ингредиентах и категориях блюд."
                         "C его помощью вы можете найти оригинальные рецепты в интересующих вас категориях. "
                         "Каждый рецепт отображает иструкцию приготовления и ингредиенты, что значительно "
                         "облегчит вашу готовку. Вперед!!!")


@dp.message(F.text.lower() == "команды")
async def commands(message: types.Message):
    response = as_list(
        as_marked_section(
            Bold("Команды:"),
            "/category_search_random - поиск категорий (через пробел необходимо указать колличество рецептов)",
            marker="✅ ",
        ),
    )
    await message.answer(
        **response.as_kwargs()
    )


choises = {'Выбрать рецепт(ы)'}
cats = {'Beef', 'Breakfast', 'Chicken', 'Dessert', 'Goat', 'Lamb', 'Miscellaneous', 'Pasta', 'Pork', 'Seafood', 'Side',
        'Starter', 'Vegan', 'Vegetarian'}


@dp.message(~F.text.lower().startswith("/"), ~F.text.in_(cats), ~F.text.in_(choises))
async def handle_invalid_message(message: types.Message):
    await message.answer("Простите, я не понимаю вашего сообщения. Пожалуйста, используйте доступные команды.")


async def main() -> None:
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
