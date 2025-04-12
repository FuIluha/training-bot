from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
import aiosqlite
from commands import cmd_menu
import os

training_router = Router()

@training_router.callback_query(F.data == 'get_trainings', StateFilter(None))
async def start_get_training_action(callback: CallbackQuery, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute(
            "SELECT results FROM test_results WHERE user_id = ?",
            (callback.from_user.id,)
        )
        result = await cursor.fetchone()
        
    if result is None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Пройти тестирование", callback_data="start_test")]
            ]
        )
        await callback.message.answer(
            "Для получения персональных тренировок необходимо сначала пройти тестирование.\n\n"
            "Это поможет определить ваши текущие показатели и подобрать оптимальную нагрузку.",
            reply_markup=keyboard
        )
        return

    test_result = result[0]
    age = "under_14" if test_result[1] == "1" else "over_14"
    option = "option_1"
    position = {
        "1": "striker",
        "2": "midfielder",
        "3": "defender",
        "4": "goalkeeper",
    }[test_result[5]]

    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute(
            "SELECT weeks FROM subscriptions WHERE user_id = ?",
            (callback.from_user.id,)
        )
        subscription = await cursor.fetchone()

    if not subscription:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Купить подписку", callback_data="buy_trainings")]
            ]
        )

        await callback.message.answer("Итак, мы подобрали для тебя оптимальную программу тренировок исходя из твоих ответов. Мы рады, что ты решил сделать первый шаг к своим целям и росту атлетизма. После успешной оплаты подписки всего за 399 рублей в неделю вы получите доступ к самотестированию в тренажерном зале, которое поможет определить ваш одноповторный максимум в силовых упражнениях и составить персонализированную программу тренировок с индивидуально подобранными рабочими весами.", reply_markup=keyboard)
        return

    weeks_available = [f"week_{i}" for i in range(1, subscription[0] + 1)]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f'Неделя {week[-1]}', callback_data=f"select_week:{week}")]
            for week in weeks_available
        ]
    )

    await state.set_data({
        "age": age,
        "option": option,
        "position": position
    })

    await callback.message.answer(
        "Выберите неделю для получения тренировок:",
        reply_markup=keyboard
    )

@training_router.callback_query(F.data.startswith('select_week:'), StateFilter(None))
async def send_selected_week_training(callback: CallbackQuery, state: FSMContext):
    selected_week = callback.data.split(':')[1]
    
    user_data = await state.get_data()
    age = user_data['age']
    option = user_data['option']
    position = user_data['position']
    
    if age == "over_14":
        base_path = os.path.join("contents", "over_14", position, selected_week, option)
    else:
        base_path = os.path.join("contents", "under_14", selected_week, option)
    
    files_to_send = [
        "1_training.pages",
        "2_training.pages",
        "Календарь цикла.pages"
    ]
    
    await state.clear()

    for filename in files_to_send:
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path):
            await callback.message.answer_document(
                document=FSInputFile(file_path)
            )
        else:
            await callback.message.answer(f"Произошла ошибка, попробуйте снова, или обратитесь к администратору")
            await cmd_menu(callback.message, state)
            raise FileNotFoundError(f'{filename}')
    await cmd_menu(callback.message, state)