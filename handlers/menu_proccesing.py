from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from db.orm_query import orm_get_banner, orm_check_catalog, orm_get_category, orm_select_tovar
from kbds.inline import Menucallback, get_user_main_btns,  get_callback_btns



async def main(session, menu_name, level):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    kbds = get_user_main_btns(level=level)
    return image, kbds


async def categ(session):
    # Получаем баннер (если он нужен)
    banner = await orm_get_banner(session, "catalog")

    # Получаем все аккаунты
    accounts = await orm_check_catalog(session)

    if banner:
        image = InputMediaPhoto(
            media=banner.image,
            caption="Выбирай что хочешь😊:",
        )
    else:
        image = None

    # Создаем кнопки с названиями игр
    game_buttons = []
    game_count = {}

    for account in accounts:
        game_cat = account.category
        if game_cat in game_count:
            game_count[game_cat] += 1
        else:
            game_count[game_cat] = 1

    # Создаем кнопки с учетом количества
    for game_cat in game_count:
        game_buttons.append(
            {
                "text": f"{game_cat}",  # Название игры с количеством
                "callback_data": f"show_cat_{game_cat}",  # Передаем название игры
            }
        )

    kbds = {"inline_keyboard": [game_buttons]}

    return image, kbds


async def game_catalog(session: AsyncSession, game_cat: str, level):
    banner = await orm_get_banner(session, "catalog")
    # Получаем игры по категории из базы данных
    games = await orm_get_category(session, game_cat)
    # Формируем список игр для отображения
    
    game_buttons = {}  # Используем словарь для хранения кнопок
    for game in games:
        game_name = game.name
        game_buttons[game_name] = f'show_{game_name}'


    if banner:
        image = InputMediaPhoto(
            media=banner.image,
            caption="Товары👌:"
        )
    else:
        image = None

    # Создаем клавиатуру один раз, используя все кнопки
    kbds =  get_callback_btns(btns={
        **game_buttons,  # Добавляем кнопки для всех игр
        "назад": Menucallback(level=level - 1, menu_name='catalog').pack()
    },sizes=(1,))

    return image, kbds


async def zaglushka(session:AsyncSession, tovar : str, level):
    banner = await orm_get_banner(session, "catalog")
    products = await orm_select_tovar(session, tovar)
    if products is None:
        # Обработка случая, когда продукт не найден
        return None, None 
    
    caption = f"{products.name}\nЦена: {products.price}₽"
    image = InputMediaPhoto(
        media=banner.image,
        caption=caption,
    )
    
    kbds =  get_callback_btns(btns={
        "купить": f"select_{products.name}",
        "Есть промокод?":   "promo",
        "Назад":    Menucallback(level=level -2, menu_name='game_catalog').pack()
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
        return await categ(session)

    elif level == 2:
        return await game_catalog(session, game_cat, level)
    
    elif level == 3:
        return await zaglushka(session, tovar, level)