from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
import aiosqlite
from aiogram.filters import StateFilter

subscribing_router = Router()

@subscribing_router.callback_query(F.data == 'buy_trainings', StateFilter(None))
async def start_subscribing_action(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute('SELECT weeks FROM subscriptions WHERE user_id = ?', (user_id,))
        subscription = await cursor.fetchone()
        
        if not subscription:
            await db.execute('INSERT INTO subscriptions (user_id, weeks) VALUES (?, 0)', (user_id,))
            current_weeks = 0
            await db.commit()
        else:
            current_weeks = subscription[0]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Купить подписку на неделю", callback_data="increase_weeks")
            ]
        ])
        
        if current_weeks > 3:
            await callback.message.answer("Вы купили полную программу тренировок.")
        else:
            await callback.message.answer(
                f"Купленное количество недель тренировок: {current_weeks} недель(и).\n\nСтоймость доступа к тренировкам на неделю 399 рублей.",
                reply_markup=keyboard
            )
    
    await callback.answer()

@subscribing_router.callback_query(F.data == 'increase_weeks', StateFilter(None))
async def change_weeks_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data
    
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute('SELECT weeks FROM subscriptions WHERE user_id = ?', (user_id,))
        subscription = await cursor.fetchone()
        
        current_weeks = subscription[0]
        
        new_weeks = current_weeks
        
        if action == 'increase_weeks' and current_weeks < 4:
            new_weeks = current_weeks + 1
            await db.execute('UPDATE subscriptions SET weeks = ? WHERE user_id = ?', (new_weeks, user_id))
        
        await db.commit()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Пройти тестирование', callback_data='start_test')],
            [InlineKeyboardButton(text='Получить тренировки на неделю', callback_data='get_trainings')],
            [InlineKeyboardButton(text='Купить доступ к тренировкам', callback_data='buy_trainings')]
        ])
        
        await callback.message.answer(
            f"Текущая продолжительность подписки: {new_weeks} недель(и)",
            reply_markup=keyboard
        )
    
    await callback.answer()