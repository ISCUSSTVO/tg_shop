import os 
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.models import Base
from commnon.text_for_db import description_for_info_pages
from db.orm_query import orm_add_banner_description
##################создание базы данных ################################################################
engine = create_async_engine(os.getenv('DB_LITE'), echo = True)


session_maker = async_sessionmaker(bind = engine, class_=AsyncSession)
AsyncSessionLocal = session_maker(bind=engine, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_maker() as session:
        await orm_add_banner_description(session, description_for_info_pages)