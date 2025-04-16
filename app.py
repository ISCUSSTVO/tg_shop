import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv
from db.engine import create_db, session_maker
from sqlalchemy.ext.asyncio import AsyncSession


load_dotenv(find_dotenv())

from db.orm_query import orm_add_admin, orm_get_admins
from midleware.db import DataBaseSession

from handlers.admin import admin_router
from handlers.user import user_router


bot = Bot(token=os.getenv("TOKEN"), parse_mode=ParseMode.HTML)
bot.my_admin_list = ["chivdoto", "ardyn_lucis"]

dp = Dispatcher()


dp.include_routers(admin_router, user_router)


async def add_admins_from_list(session: AsyncSession):
    for username in bot.my_admin_list:
        try:
            await orm_add_admin(session, username)
            print(f"Администратор {username} успешно добавлен.")
        except Exception as e:
            print(f"Ошибка при добавлении {username}: {e}")


async def on_startup():
    await create_db()

    async with session_maker() as session:
        for username in bot.my_admin_list:
            if username not in await orm_get_admins(session):
                await add_admins_from_list(session)
                await session.commit()
                print("добавил")

    print(
        "Бот запущен и готов к работе!"
        )


async def main():
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
