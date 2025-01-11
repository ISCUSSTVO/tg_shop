from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from db.orm_query import (orm_get_banner, 
    orm_get_category_catalog, 
    orm_get_promocode_by_category, 
    orm_get_promocode_by_name)
from kbds.inline import Menucallback, get_user_main_btns,  get_callback_btns
import logging



async def main(session,level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    kbds = get_user_main_btns(level=level, sizes=(1,2))
    return image, kbds


async def category(session):
    # Получаем баннер (если он нужен)
    banner = await orm_get_banner(session, "catalog")
    promocodes = await orm_get_category_catalog(session)
    image = InputMediaPhoto(media=banner.image,caption="Выбирай что хочешь😊:",)

    btns = {
        f"{promocodes}": f"show_category_{promocodes}"for promocodes in promocodes
        }
    
    btns["назад"] = Menucallback(level=0, menu_name='main').pack()
    kbds = get_callback_btns(btns = btns, sizes=(2,2,))
    return image, kbds


async def promocodes_catalog(session: AsyncSession, game_cat: str, level):
    banner = await orm_get_banner(session, "catalog")
    promocodes = await orm_get_promocode_by_category(session, game_cat)
    image = InputMediaPhoto(media=banner.image,caption="Товары👌:")
    btns = {
        f"{promocode.name}": f"show_promocode_{promocode.name}" for promocode in promocodes
    }
    btns["назад"] = Menucallback(level=level - 1, menu_name='catalog').pack()

    kbds = get_callback_btns(btns=btns, sizes=(1,))
    return image, kbds


async def payment(session: AsyncSession, tovar: str, level):
    banner = await orm_get_banner(session, "catalog")
    product = await orm_get_promocode_by_name(session, tovar)
    
    if product is None:
        image = InputMediaPhoto(media=banner.image, caption="Промокод не найден")
        kbds = get_callback_btns(btns={
            "Назад": Menucallback(level=level - 2, menu_name='game_catalog').pack()
        })
        return image, kbds

    image = InputMediaPhoto(media=banner.image, caption=f"{product.name}\nЦена: {product.price}₽")
    
    kbds = get_callback_btns(btns={
        "купить": f"select_{product.name}",
        "Есть промокод?": "promo",
        "Назад": Menucallback(level=level - 2, menu_name='game_catalog').pack()
    })
    
    return image, kbds


async def get_menu_content(
        
    session: AsyncSession,
    level: int,
    menu_name: str,
    game_cat: str = None,
    tovar: str = None
):
    if level == 0:
        return await main(session=session, level=level, menu_name=menu_name)

    elif level == 1:
        return await category(session)

    elif level == 2:
        return await promocodes_catalog(session, game_cat, level)
    
    elif level == 3:
        return await payment(session, tovar, level)