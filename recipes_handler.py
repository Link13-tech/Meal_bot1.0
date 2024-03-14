import asyncio
import aiohttp
import random
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types
from googletrans import Translator
from aiogram.enums import ParseMode


router = Router()
translator = Translator()


class OrderCategory(StatesGroup):
    waiting_for_category = State()
    waiting_for_recipe_selection = State()


@router.message(Command("category_search_random"))
async def category_search_random(message: Message, command: CommandObject, state: FSMContext):
    if command.args is None:
        await message.answer(
            "Ошибка: не переданы аргументы"
            )
        return
    try:
        num_recipes = int(command.args)
    except ValueError:
        await message.answer("Ошибка: аргумент должен быть числом.")
        return

    await state.update_data({'num_recipes': num_recipes})

    url = "https://www.themealdb.com/api/json/v1/1/list.php?c=list"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await message.answer("Ошибка при получении списка категорий.")
                return
            data = await resp.json()
            categories = [meal['strCategory'] for meal in data['meals']]
            builder = ReplyKeyboardBuilder()
            for category in categories:
                builder.add(types.KeyboardButton(text=category))
            builder.adjust(5)
            await message.answer(
                "*Выберите категорию рецептов:*", parse_mode=ParseMode.MARKDOWN,
                reply_markup=builder.as_markup(resize_keyboard=True),
            )
            await state.set_state(OrderCategory.waiting_for_category.state)


@router.message(OrderCategory.waiting_for_category)
async def get_recipes_by_category(message: types.Message, state: FSMContext):
    data = await state.get_data()
    num_recipes = data.get('num_recipes')
    chosen_category = message.text

    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={chosen_category}"
    print(url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    meals = data.get("meals", [])
    if not meals:
        await message.answer("Извините, но для этой категории нет рецептов.")
        return

    if num_recipes > len(meals):
        await message.answer(f"Извините, но в этой категории доступно только {len(meals)} рецепта.")
        num_recipes = len(meals)
    print(num_recipes)
    selected_meals = random.sample(meals, k=num_recipes)
    await state.set_data({'selected_meals': selected_meals})
    recipe_names = [meal.get('strMeal') for meal in selected_meals]

    rus_recipe_names = [translator.translate(recipe_name, dest='ru').text.capitalize() for recipe_name in recipe_names]

    message_text = "*Могу предложить такие варианты:*\n" + "\n".join(rus_recipe_names)

    reply_markup = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Выбрать рецепт(ы)")]],
        resize_keyboard=True
    )
    await message.answer(message_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    await state.set_state(OrderCategory.waiting_for_recipe_selection.state)


@router.message(OrderCategory.waiting_for_recipe_selection)
async def send_recipe_details(message: types.Message, state: FSMContext):
    data = await state.get_data()
    recipe_ids = [ids['idMeal'] for ids in data['selected_meals']]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_recipe(session, ids) for ids in recipe_ids]
        responses = await asyncio.gather(*tasks)

    for response in responses:
        recipe_details = response.get('meals', [])
        if recipe_details:
            recipe = recipe_details[0]
            recipe_name = recipe.get('strMeal', 'Нет информации')
            ingredients = ', '.join(
                filter(None, [recipe.get(f'strIngredient{i}', '') for i in range(1, 21)])) or 'Нет информации'
            instructions = recipe.get('strInstructions', 'Нет информации')
            recipe_text = f"Имя рецепта:\n{recipe_name}\n\nРецепт:\n{instructions}\n\nИнгредиенты:\n{ingredients}\n"

            translated_recipe_text = translator.translate(recipe_text, dest='ru').text
            translated_recipe_text_bold = (translated_recipe_text.replace('Рецепт:', '*Рецепт:*')
                                           .replace('Имя рецепта:', '*Имя рецепта:*')
                                           .replace('Ингредиенты:', '*Ингредиенты:*'))
            await message.answer(translated_recipe_text_bold, parse_mode=ParseMode.MARKDOWN)

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
    await message.answer("Выберите дальнейшее действие:", reply_markup=keyboard)


async def fetch_recipe(session, recipe_id):
    url = f"http://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}"
    print(url)
    async with session.get(url) as resp:
        return await resp.json()
