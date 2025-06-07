from math import prod
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from utils.paginator import Paginator
from db.orm_query import (
    orm_add_to_cart,
    orm_count_promocodes,
    orm_get_cart,
    orm_get_cart_on_code,
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_catalog_categories,
    orm_get_next_available_promocode,
    orm_get_promocode_by_category,
    orm_get_promocode_by_name,
    orm_get_available_promocode,
    orm_get_user_promocode_usage,
    orm_decrement_cart_item,
)
from kbds.inline import (
    Menucallback,
    back_kbds,
    get_user_main_btns, 
    get_callback_btns, 
    get_user_cart)


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def main(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    kbds = get_user_main_btns(level=level, sizes=(1, 2))
    return image, kbds


async def category(session):
    banner = await orm_get_banner(session, "catalog")
    promocodes = await orm_get_catalog_categories(session)
    image = InputMediaPhoto(
        media=banner.image,
        caption="Выбирай что хочешь😊:",
    )
    btns = {f"{promocodes}": f"show_category_{promocodes}" for promocodes in promocodes}
    btns["назад"] = Menucallback(level=0, menu_name="main").pack()

    kbds = get_callback_btns(
        btns=btns,
        sizes=(2,))
    return image, kbds


async def promocodes_catalog(session, level,game_cat):
    banner = await orm_get_banner(session, "catalog")

    categ = game_cat
    promocodes = await orm_get_promocode_by_category(session, categ)
    
    
    filtered_promocodes = [promocode for promocode in promocodes if promocode.quantity > 1]
    if filtered_promocodes != []:
        image = InputMediaPhoto(media=banner.image, caption="Товары👌:")
        btns = {
            f"{promocode.name}": f"show_code_{promocode.id}"
            for promocode in filtered_promocodes
        }
        btns["назад"] = Menucallback(level=level - 1, menu_name="catalog").pack()
    else:
        image = InputMediaPhoto(media=banner.image, caption="В этой категории товаров нет:")
        btns = {"Назад": Menucallback(level=level - 1, menu_name="catalog").pack()}


    kbds = get_callback_btns(btns=btns, sizes=(1,))
    return image, kbds


async def payment(session: AsyncSession, tovar: str, user_id: int):
    banner = await orm_get_banner(session, "catalog")
    promocodes = await orm_get_promocode_by_name(session, tovar)
    if not promocodes:
        image = InputMediaPhoto(media=banner.image, caption="Товар не найден")
        kbds = get_callback_btns(
            btns =  {"Назад": f"show_category_{promocodes.category}"})
        return image, kbds
    

    # Применяем скидку продукта
    product_price = promocodes.price - (promocodes.price * promocodes.discount // 100)
    # Получаем активный промокод пользователя
    user_promocode_usage = await orm_get_user_promocode_usage(session, user_id)
    if user_promocode_usage is not None:
        promocode_discount = await orm_get_promocode_by_name(session, user_promocode_usage.id)
        if promocode_discount:
            product_price -= product_price * promocode_discount.discount // 100

    # Формируем описание продукта с учетом скидок5
    if promocodes.discount != 0 or (user_promocode_usage and promocode_discount):
        caption = f"{promocodes.name}\nЦена: ~{promocodes.price}₽~ {product_price}₽\nОсталось: {str(promocodes.quantity)}\n"
    else:
        caption = f"{promocodes.name}\nЦена: {promocodes.price}₽\nОсталось: {str(promocodes.quantity)}"

    btns = {
        "купить": f"select_{promocodes.id}",
        "Есть промокод?": "promo",
        "Добавить в корзину": f'add_cart_{promocodes.id}',
        "Назад": f"show_category_{promocodes.category}"
    }


    kbds = get_callback_btns(btns=btns)

    # Формируем изображение и кнопки
    image = InputMediaPhoto(media=banner.image, caption=caption, parse_mode="MarkdownV2")
    return image, kbds


async def cart(session:AsyncSession, level, page: int, user_id: int, menu_name,tovar:str):
    if menu_name == "delete":
        await orm_delete_from_cart(session, user_id, tovar)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_cart = await orm_decrement_cart_item(session, user_id, tovar)
        
        if page > 1 and not is_cart:
            page -= 1
    elif menu_name == "increment":
        q = await orm_add_to_cart(session, tovar, user_id)
        if q ==("qwe"):
            image = ("qwe")
            return image
    
    banner = await orm_get_banner(session, "cart")
    carts = await orm_get_cart(session, user_id)

    if not carts:
        image = InputMediaPhoto(
            media=banner.image, 
            caption=f"<strong>Ваша корзина пуста</strong>"
        )

        kbds = back_kbds(level=level)
        
    else:
        paginator = Paginator(carts, page=page)
        current_page_items = paginator.get_page()
        if not current_page_items:
            page = max(1, paginator.pages)
            current_page_items = paginator.get_page()
        current_cart = current_page_items[0]
    
        
        cart_price = round(current_cart.quantity * current_cart.price, 2)
        full_price = sum([cart.quantity * (await orm_get_cart_on_code(session, user_id, cart.product_name)).price for cart in carts])
        caption = f"<strong>{current_cart.product_name}</strong>\n{current_cart.price}₽ x {current_cart.quantity} = {cart_price}\nСтоимость товаров в корзине {full_price} руб.\nТовар {page} из {paginator.pages} в корзине."

        image = InputMediaPhoto(
            media=banner.image,
            caption=caption,
            parse_mode="HTML",
        )

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            tovar=current_cart.id,

        )
    return image, kbds

async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    user_id: int| None = None,
    tovar: str = None,
    page: int | None = None,
    price: int | None = None, 
    game_cat: str | None = None,
    state: FSMContext | None = None,
    promo: str | None = None,

      

):
    if level == 0:
        return await main(session=session, level=level, menu_name=menu_name)

    elif level == 1:
        return await category(session)

    elif level == 2:
        return await promocodes_catalog(session=session,level=level, game_cat=game_cat)

    elif level == 3:
        return await payment(session, tovar, user_id)
    
    elif level == 4:
        return await cart(session, level=level, page=page, user_id=user_id,menu_name=menu_name,tovar=tovar)
