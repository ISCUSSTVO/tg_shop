from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from utils.paginator import Paginator
from db.orm_query import (
    orm_add_to_cart,
    orm_get_cart,
    orm_get_cart_on_code,
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_category_catalog,
    orm_get_next_promocode_by_name,
    orm_get_promocode_by_category,
    orm_get_promocode_by_name,
    orm_get_promocode_by_name_with_quantity,
    orm_get_promocode_usage,
    orm_reduce_service_in_cart,
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

async def promocodes_catalog(state, session, level,game_cat):
    banner = await orm_get_banner(session, "catalog")
    

    # Получаем категорию из состояния или из переданных данных
    #if state:
    #    state_data = await state.get_data()
    #    categ = data.get("category") or state_data.get("category") or state_data.get("last_category")
    #else:
    #    categ = data.get("category")
    #
    # Логирование для отладки

    categ = game_cat
    promocodes = await orm_get_promocode_by_category(session, categ)

    image = InputMediaPhoto(media=banner.image, caption="Товары👌:")
    btns = {
        f"{promocode.name}": f"show_promocode_{promocode.name}"
        for promocode in promocodes
    }
    btns["назад"] = Menucallback(level=level - 1, menu_name="catalog").pack()

    kbds = get_callback_btns(btns=btns, sizes=(1,))
    return image, kbds


async def payment(session: AsyncSession, tovar: str, user_id: int):
    banner = await orm_get_banner(session, "catalog")

    # Получаем текущий товар
    product = await orm_get_promocode_by_name_with_quantity(session, tovar)
    if product is None:
        # Если товар не найден
        image = InputMediaPhoto(media=banner.image, caption="Товар не найден")
        kbds = get_callback_btns(
            btns={
                "Назад": Menucallback(level=2, menu_name="game_catalog").pack()
            }
        )
        return image, kbds

    # Проверяем, доступен ли товар
    if product.quantity == 0 and product.in_cart == 1:
        # Если текущий товар недоступен, ищем следующий товар с таким же именем
        next_product = await orm_get_next_promocode_by_name(session, tovar)
        if next_product is None or next_product.quantity == 0 or next_product.in_cart == 1:
            image = InputMediaPhoto(media=banner.image, caption="Товар недоступен")
            kbds = get_callback_btns(
                btns={
                    "Назад": Menucallback(level=2, menu_name="game_catalog").pack()
                }
            )
            return image, kbds
        else:
            product = next_product

    # Применяем скидку продукта
    product_price = product.price - (product.price * product.discount // 100)

    # Получаем активный промокод пользователя
    user_promocode_usage = await orm_get_promocode_usage(session, user_id)
    if user_promocode_usage is not None:
        promocode_discount = await orm_get_promocode_by_name(session, user_promocode_usage.promocode)
        if promocode_discount:
            product_price -= product_price * promocode_discount.discount // 100

    # Формируем описание продукта с учетом скидок
    if product.discount != 0 or (user_promocode_usage and promocode_discount):
        caption = f"{product.name}\nЦена: ~{product.price}₽~ {product_price}₽\nОсталось: {product.quantity}\nВ корзине: {product.in_cart}"
    else:
        caption = f"{product.name}\nЦена: {product.price}₽\nОсталось: {product.quantity}\nВ корзине: {product.in_cart}"

    # Формируем кнопки
    btns = {
        "купить": f"select_{product.name}",
        "Есть промокод?": "promo",
        "Добавить в корзину": f'add_cart_{product.name}_{product_price}_{product.quantity}_{product.in_cart}',
        "Назад": Menucallback(level=2, menu_name="game_catalog").pack(),
    }


    kbds = get_callback_btns(btns=btns)

    # Формируем изображение и кнопки
    image = InputMediaPhoto(media=banner.image, caption=caption, parse_mode="MarkdownV2")
    return image, kbds


async def cart(session, level, page: int, user_id: int, menu_name,tovar:str,price):
    if menu_name == "delete":
        await orm_delete_from_cart(session, user_id, tovar)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_cart = await orm_reduce_service_in_cart(session, user_id, tovar)
        if page > 1 and not is_cart:
            page -= 1
    elif menu_name == "increment":
        await orm_add_to_cart(session, tovar, user_id, price)
    
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
            tovar=current_cart.product_name,
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
      

):
    if level == 0:
        return await main(session=session, level=level, menu_name=menu_name)

    elif level == 1:
        return await category(session)

    elif level == 2:
        return await promocodes_catalog(state=state,session=session,level=level, game_cat=game_cat)

    elif level == 3:
        return await payment(session, tovar, user_id)
    
    elif level == 4:
        return await cart(session, level=level, page=page, user_id=user_id,menu_name=menu_name,tovar=tovar,price=price)
