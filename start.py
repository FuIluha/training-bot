from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import aiosqlite

start_router = Router()

class QuestionStates(StatesGroup):
    waiting_after_start = State()
    waiting_after_agreement = State()
    start_test = State()
    
@start_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT id FROM users WHERE id = ?", (message.from_user.id,)) as cursor:
            if await cursor.fetchone() is None:
                await cursor.execute("INSERT INTO users (id, name) VALUES(?,?);", (message.from_user.id, message.from_user.first_name))
                await db.commit()

            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='Пройти тестирование')]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            await state.set_state(QuestionStates.waiting_after_start)
            await message.answer('''Привет! Сегодня мы проведём тестирование, которое позволит тренеру-боту правильно высчитать рабочие веса, с которыми мы будем работать в ближайшие недели. В сообщении ниже у тебя будет возможность ознакомиться с техникой выполнения и подготовкой к упражнениям в письменном виде, но а я сейчас покажу тебе всё наглядно.\n\nПосле качественной разминки которая также будет выслана тебе, мы начнём тестирование. В каждом из трёх упражнений, одноповторный максимум которых мы узнаем сегодня, тест будет начинаться с пустого грифа. Далее каждое следующее повторение мы будем добавлять 10-20кг на штангу, чем ближе к отказу - тем меньше прибавляется вес за шаг. Первые 2-4 подхода - разминочные, их мы выполняем на 4-6 повторений. Далее, когда вес становится ощутимым, мы делаем подход исключительно на одно повторение, а также отдыхаем между подходами не менее 3 минут.\n\nПосле достижения максимального веса и окончания тестирования введи свои показатели в программу, и через 2 дня после полного восстановления ты можешь приступать к началу четырёхнедельного тренировочного цикла.''', reply_markup=keyboard)
            
@start_router.message(F.text == 'Пройти тестирование', QuestionStates.waiting_after_start)
async def start_test_action(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='С предупреждением ознакомлен')], 
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
    
    await state.set_state(QuestionStates.waiting_after_agreement)
    await message.answer('''<b>Предупреждение:</b>\n\nПриобретая нашу тренировочную программу, вы подтверждаете, что находитесь в хорошем состоянии здоровья и не имеете противопоказаний к занятиям физической активностью, а также несете полную ответственность за свое здоровье и безопасность во время занятий. Мы настоятельно рекомендуем вам проконсультироваться с врачом перед началом любой новой программы тренировок. Следует помнить, что программа носит лишь рекомендательный характер, составленный на основе многолетней работы с исключительно полностью здоровыми спортсменами не имеющими противопоказаний. В случае дискомфорта, не обусловленного работой мышц, рекомендуем немедленно прекратить упражнение и либо закончить тренировку, либо перейти к следующему блоку упражнений, которые не будут болезненными для вас.''', reply_markup=keyboard)

@start_router.message(QuestionStates.waiting_after_start)
async def repeat_question(message: Message):
    keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='Пройти тестирование')]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )

    await message.answer('Пожалуйста, выберите действие на клавиатуре', reply_markup=keyboard)

@start_router.message(QuestionStates.waiting_after_agreement)
async def repeat_agreement(message: Message):
    keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='С предупреждением ознакомлен')], 
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )

    await message.answer('Ознакомьтесь с предупреждением и выберете действие на клавиатуре', reply_markup=keyboard)