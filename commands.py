from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

command_router = Router()
    
@command_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (message.from_user.id,)) as cursor:
            if await cursor.fetchone() is None:
                await cursor.execute("INSERT INTO users (id, name) VALUES(?,?);", (message.from_user.id, message.from_user.first_name))
                await db.commit()

            await message.answer('''Привет! Сегодня мы проведём тестирование, которое позволит тренеру-боту правильно высчитать рабочие веса, с которыми мы будем работать в ближайшие недели. В сообщении ниже у тебя будет возможность ознакомиться с техникой выполнения и подготовкой к упражнениям в письменном виде, но а я сейчас покажу тебе всё наглядно.\n\nПосле качественной разминки которая также будет выслана тебе, мы начнём тестирование. В каждом из трёх упражнений, одноповторный максимум которых мы узнаем сегодня, тест будет начинаться с пустого грифа. Далее каждое следующее повторение мы будем добавлять 10-20кг на штангу, чем ближе к отказу - тем меньше прибавляется вес за шаг. Первые 2-4 подхода - разминочные, их мы выполняем на 4-6 повторений. Далее, когда вес становится ощутимым, мы делаем подход исключительно на одно повторение, а также отдыхаем между подходами не менее 3 минут.\n\nПосле достижения максимального веса и окончания тестирования введи свои показатели в программу, и через 2 дня после полного восстановления ты можешь приступать к началу четырёхнедельного тренировочного цикла.''', reply_markup=main_keyboard)

@command_router.message(Command('Menu'))
async def cmd_menu(message: Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (message.from_user.id,)) as cursor:
            if await cursor.fetchone() is None:
                await cursor.execute("INSERT INTO users (id, name) VALUES(?,?);", (message.from_user.id, message.from_user.first_name))
                await db.commit()

            await message.answer('''Доступные действия:''', reply_markup=main_keyboard)


main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Пройти тестирование', callback_data='start_test')],
        [InlineKeyboardButton(text='Получить тренировки на неделю', callback_data='get_trainings')],
        [InlineKeyboardButton(text='Купить доступ к тренировкам', callback_data='buy_trainings')]
    ]
)