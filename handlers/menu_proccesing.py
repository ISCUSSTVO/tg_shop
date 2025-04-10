from aiogram.types import InlineKeyboardButton, InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from db.orm_query import (
    orm_chek_cart,
    orm_chek_user_cart_on_code,
    orm_get_banner,
    orm_get_category_catalog,
    orm_get_promocode_by_category,
    orm_get_promocode_by_name,
    orm_get_promocode_usage,
)
from kbds.inline import (
    Menucallback,
    get_user_main_btns, 
    get_callback_btns, 
    get_user_cart)
from utils.paginator import Paginator



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
    # Получаем баннер (если он нужен)
    banner = await orm_get_banner(session, "catalog")
    promocodes = await orm_get_category_catalog(session)
    image = InputMediaPhoto(
        media=banner.image,
        caption="Выбирай что хочешь😊:",
    )

    btns = {f"{promocodes}": f"show_category_{promocodes}" for promocodes in promocodes}
    btns["назад"] = Menucallback(level=0, menu_name="main").pack()

    kbds = get_callback_btns(
        btns=btns,
        sizes=(2,1))
    return image, kbds





async def promocodes_catalog(session: AsyncSession, game_cat: str, level):
    banner = await orm_get_banner(session, "catalog")
    promocodes = await orm_get_promocode_by_category(session, game_cat)
    image = InputMediaPhoto(media=banner.image, caption="Товары👌:")
    btns = {
        f"{promocode.name}": f"show_promocode_{promocode.name}"
        for promocode in promocodes
    }
    btns["назад"] = Menucallback(level=level - 1, menu_name="catalog").pack()

    kbds = get_callback_btns(btns=btns, sizes=(1,))
    return image, kbds


async def payment(session: AsyncSession, tovar: str, user_id: int, level: int):
    banner = await orm_get_banner(session, "catalog")
    product = await orm_get_promocode_by_name(session, tovar)
    user = await orm_chek_cart(session, user_id)
    list = ''.join([i.product_name for i in user])
    if product is None:
        image = InputMediaPhoto(media=banner.image, caption="Промокод не найден")
        kbds = get_callback_btns(
            btns={
                "Назад": Menucallback(level=level - 2, menu_name="game_catalog").pack()
            }
        )
        return image, kbds

    user_promocode_usage = await orm_get_promocode_usage(session, user_id)
    if user_promocode_usage is not None:
        promocode_discount = await orm_get_promocode_by_name(session, user_promocode_usage.promocode)
    else:
        promocode_discount = None

    # Применяем скидку продукта
    product_price = product.price - (product.price * product.discount // 100)
    
    # Если у пользователя есть активный промокод, применяем дополнительную скидку
    if promocode_discount:
        product_price = product_price - (product_price * promocode_discount.discount // 100)

    # Формируем описание продукта с учетом скидок
    if product.discount != 0 or promocode_discount:
        caption = f"{product.name}\nЦена: ~{product.price}₽~ {product_price}₽"
    else:
        caption = f"{product.name}\nЦена: {product.price}₽"

    image = InputMediaPhoto(media=banner.image, caption=caption, parse_mode="MarkdownV2")
    if  user is None or product.name in list:
        kbds = get_callback_btns(
            btns={
                "купить": f"select_{product.name}",
                "Есть промокод?": "promo",
                "Назад": Menucallback(level=level - 2, menu_name="game_catalog").pack(),
            }
        )
    else:
        kbds = get_callback_btns(
            btns={
                "купить": f"select_{product.name}",
                "Есть промокод?": "promo",
                "Добавить в корзину": f'add_cart_{product.name}_{product_price}',
                "Назад": Menucallback(level=level - 2, menu_name="game_catalog").pack(),
            }
        )

    return image, kbds


async def cart(session: AsyncSession, page: int, user_id: int):
    banner = await orm_get_banner(session, "cart")
    carts = await orm_chek_cart(session, user_id)

    if not carts:
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>Ваша корзина пуста</strong>"
        )

        kbds = get_callback_btns(btns={
            "Назад": Menucallback(level=0, menu_name="main").pack()
        })
        
    else:
        paginator = Paginator(carts, page=page)
        current_page_items = paginator.get_page()

        if not current_page_items:
            page = max(1, paginator.pages)
            current_page_items = paginator.get_page()

        current_cart = current_page_items[0]
        

    
        cart_price = round(current_cart.quantity * current_cart.price, 2)
        full_price = sum([cart.quantity * (await orm_chek_user_cart_on_code(session, user_id, cart.product_name)).price for cart in carts])
        caption = f"<strong>{current_cart.product_name}</strong>\n{current_cart.price}₽ x {current_cart.quantity} = {cart_price}\nСтоимость товаров в корзине {full_price} руб.\nТовар {page} из {paginator.pages} в корзине."

        image = InputMediaPhoto(
            media=banner.image,
            caption=caption,
            parse_mode="HTML",
        )

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            page=page,
            pagination_btns=pagination_btns,
            tovar=current_cart.product_name,
        )
        kbds.inline_keyboard.append([InlineKeyboardButton(text="Назад", callback_data=Menucallback(level=0, menu_name="main").pack())])

    return image, kbds

async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    user_id: int,
    game_cat: str = None,
    tovar: str = None,

):
    if level == 0:
        return await main(session=session, level=level, menu_name=menu_name)

    elif level == 1:
        return await category(session)

    elif level == 2:
        return await promocodes_catalog(session, game_cat, level)

    elif level == 3:
        return await payment(session, tovar, user_id,  level = level)
