from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
import asyncio
import logging
import aiosqlite
import os
import nest_asyncio
from commands import command_router
from testing import testing_router
from training import training_router
from subscribe import subscribing_router

token = os.getenv('BOT_TOKEN')
if not token:
    raise ValueError("Не установлен BOT_TOKEN в .env файле")

bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(testing_router)
dp.include_router(training_router)
dp.include_router(subscribing_router)
dp.include_router(command_router)

nest_asyncio.apply()

logging.basicConfig(force=True, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SomeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        message = data.get('event_update').message
        if message:
            text = message.text
            chat_id = message.chat.id

            state = data['state']
            current_state = await state.get_state()
            if text == '/start':
                return await handler(event, data)

            async with aiosqlite.connect('users.db') as db:
                async with db.execute("SELECT id FROM users WHERE id = ?", (chat_id,)) as cursor:
                    if await cursor.fetchone() is None:
                        await bot.send_message(chat_id=chat_id, text='Вы не зарегистрированы! Зарегистрируйтесь, используя команду /start.')
                        return

        return await handler(event, data)


async def start_db():
    async with aiosqlite.connect('users.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name STRING
            )
        ''')
        await db.commit()
        await db.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                user_id INTEGER,
                results TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        await db.commit()
        await db.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER,
                weeks INTEGER CHECK(weeks IN (0, 1, 2, 3, 4)),
                FOREIGN KEY(user_id) REFERENCES users(id),
                PRIMARY KEY (user_id)
            )
        ''')
        await db.commit()

async def main():
    dp.startup.register(start_db)
    try:
        print("Бот запущен...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        print("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())