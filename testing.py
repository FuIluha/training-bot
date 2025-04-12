from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
import aiosqlite
from commands import cmd_menu

testing_router = Router()

class QuestionStates(StatesGroup):
    waiting_after_agreement = State()
    start_test = State()

class TestingStates(StatesGroup):
    testing = State()

@testing_router.callback_query(F.data == 'start_test', StateFilter(None))
async def start_test_action(callback: CallbackQuery, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='С предупреждением ознакомлен')], 
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
    
    await state.set_state(QuestionStates.waiting_after_agreement)
    await callback.message.answer('''<b>Предупреждение:</b>\n\nПриобретая нашу тренировочную программу, вы подтверждаете, что находитесь в хорошем состоянии здоровья и не имеете противопоказаний к занятиям физической активностью, а также несете полную ответственность за свое здоровье и безопасность во время занятий. Мы настоятельно рекомендуем вам проконсультироваться с врачом перед началом любой новой программы тренировок. Следует помнить, что программа носит лишь рекомендательный характер, составленный на основе многолетней работы с исключительно полностью здоровыми спортсменами не имеющими противопоказаний. В случае дискомфорта, не обусловленного работой мышц, рекомендуем немедленно прекратить упражнение и либо закончить тренировку, либо перейти к следующему блоку упражнений, которые не будут болезненными для вас.''', reply_markup=keyboard)

@testing_router.message(QuestionStates.waiting_after_agreement)
async def start_testing(message: Message, state: FSMContext):
    if message.text != 'С предупреждением ознакомлен':
        keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='С предупреждением ознакомлен')], 
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )

        await message.answer('Ознакомьтесь с предупреждением и выберете действие на клавиатуре', reply_markup=keyboard)
        return
    await state.set_state(TestingStates.testing)
    await state.update_data(question_index=0, answers=[])
    await testing(message = message, state = state)

@testing_router.message(TestingStates.testing)
async def testing(message: Message, state: FSMContext):
    data = await state.get_data()
    question_index = data.get('question_index')
    answers = data.get('answers')

    if message.text and message.text in questions_keyboards[question_index - 1]:
        answers.append(message.text)
    elif question_index != 0:
        keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=key)] for key in questions_keyboards[question_index - 1]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        await message.answer('Пожалуйста, пользуйтесь клавиатурой', reply_markup=keyboard)
        return
    
    if question_index == 6:
        async with aiosqlite.connect('users.db') as db:
            await db.execute(
                "DELETE FROM test_results WHERE user_id = ?",
                (message.from_user.id,)
            )
            
            await db.execute(
                "INSERT INTO test_results (user_id, results) VALUES (?, ?)",
                (message.from_user.id, ''.join(answers))
            )
            await db.commit()
        await message.answer('Ваши результаты сохранены', reply_markup=ReplyKeyboardRemove())
        await state.clear()
        await cmd_menu(message, state)
        return
    
    if question_index == 3 and not answers[2] in ['1', '2', '4'] or question_index == 4 and not answers[2] in ['3', '4']:
        question_index += 1
        answers.append('0')

    keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=key)] for key in questions_keyboards[question_index]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
    
    await state.update_data(question_index=question_index + 1, answers=answers)
    
    await message.answer(questions[question_index], reply_markup=keyboard)


questions = [
    'Кем вы являетесь?\n\n1. Спортсмен профессионал (5 и более тренировок с командой в \n2. неделю) Спортсмен полупрофессионал (3-4 тренировки с командой в неделю) \n3. Спортсмен любитель (Менее 3 тренировок с командой в неделю)',
    'Выберите ваш возраст.\n\n1. Младше 14 лет\n2. 14 лет и старше',
    'Какие цели вы ставите перед собой?\n\n1. Увеличить общий уровень атлетизма - этот вариант подойдет для атлетов, которые хотят повысить физический потенциал на игровом поле, увеличить скорость, максимальную силу, координацию, эффективность работы в тренажерном зале и трансформацию силовых показателей на поле/площадку. \n2. Поддерживать развитые в межсезонье силовые и кондиционные способности в игровом сезоне - вариант подходит для атлетов, которые уже провели плодотворную и объёмную работу в межсезонье, прошли качественные сборы и желают поддерживать развитый уровень атлетизма и физическую форму между матчами. \n3. Провести межсезонье - вариант для атлетов, которые хотят в отпуске подготовить себя наилучшим образом к сборам либо сезону, увеличить уровень максимальной силы, выносливости и мощности. \n4. Набрать мышечную массу - вариант для спортсменов, которые хотят увеличить безжировую массу тела, повысить уровень атлетизма и сделать акцент на развитие силовых показателей в тренировочной программе',
    'Выберите количество дополнительных тренировок, которое будете проводить в тренажёрном зале в сезоне.\n\n1. 2 тренировки в неделю\n2. 3 тренировки в неделю',
    'Выберите количество дополнительных тренировок, которое будете проводить в тренажёрном зале в сезоне.\n\n1. 3 тренировки в неделю\n2. 4-5 тренировок в неделю',
    'Выберите вашу игровую позицию на футбольном поле.\n\n1. Нападающий \n2. Полузащитник/крайний защитник\n3. Центральный защитник\n4. Вратарь'
]

questions_keyboards = [
    ['1', '2', '3'],
    ['1', '2'],
    ['1', '2', '3', '4'],
    ['1', '2'],
    ['1', '2'],
    ['1', '2', '3', '4']
]