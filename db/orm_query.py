from sqlalchemy import delete, distinct, select, update , func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Catalog, Admins, Banner,PromocodeUsage, Promokodes, Spam, Users, Cart

############### Работа с баннерами (информационными страницами) ###############


async def orm_add_banner_description(session: AsyncSession, data: dict):
    # Добавляем новый или изменяем существующий по именам
    # пунктов меню: main, about, cart, shipping, payment, catalog
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all(
        [
            Banner(name=name, description=description)
            for name, description in data.items()
        ]
    )
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()



############### Работа с корзиной ##############
async def orm_add_to_cart(session: AsyncSession, product_name: str, user_id: int, price: int,quantity: int, in_cart: int):
    tovar = await session.scalar(select(Catalog).where(Catalog.name == product_name,Catalog.quantity == quantity, Catalog.in_cart == in_cart))
    if not tovar or tovar.quantity <= 0:
        return

    #cart = await session.scalar(select(Cart).where(Cart.user_id == user_id, Cart.product_name == product_name))
    #if cart:
    #    cart.quantity += 1
    session.add(Cart(user_id=user_id, product_name=product_name, quantity = 1, price=tovar.price, promo = tovar.promocode))
    tovar.quantity -= 1
    tovar.in_cart = 1

    await session.commit()


async def orm_get_cart(session: AsyncSession, user_id: int):
    query = select(Cart).where(Cart.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_cart_on_code(session: AsyncSession, user_id: int, code:str):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_name == code)
    result = await session.execute(query)
    return result.scalar()

async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_name: str, promo: str):
    await session.execute(delete(Cart).where(Cart.user_id == user_id, Cart.product_name == product_name,Cart.promo == promo))
    await session.execute(update(Catalog).where(Catalog.name == product_name, Catalog.promocode ==promo).values(in_cart=0, quantity=1))
    await session.commit()

async def orm_decrement_cart_item(session: AsyncSession, user_id: int, product_name: str, promo: str):
    tovar = await orm_get_promocode_by_name(session, product_name)
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_name == product_name)
    result = await session.execute(query)
    cart = result.scalar()
    if cart is None:
        return "cart none"
    if cart.quantity > 1:
        query = update(Cart).where(Cart.user_id == user_id, Cart.product_name == product_name).values(quantity=cart.quantity - 1)
        tovar.quantity =1
        await session.execute(query)
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_name, promo)
        await session.commit()
        return False
    

############### Работа с каталогами ##############
async def orm_add_promocode_to_catalog(session: AsyncSession, data: dict):
    tovar = await orm_get_promocode_by_name(session, data["name"])
    name = data["name"]
    promo = data["promocode"] 
    if tovar is not None:
        price = tovar.price
        obj = Catalog(
            name=name,
            category=tovar.category,
            promocode= promo,
            price=tovar.price,
            discount=tovar.discount,
            quantity=1
        )
        session.add(obj)
    else:
        price = data["price"]
        obj = Catalog(
            name=data["name"],
            category=data["category"],
            promocode=data["promocode"],
            price=data["price"],
            discount=data["discount"],
            quantity=1
        )
        session.add(obj) 

    await session.commit()
    return name,promo,price


async def orm_get_all_catalog_items(session: AsyncSession):
    query = select(Catalog)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_catalog_categories(session: AsyncSession):
    query = select(distinct(Catalog.category))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_promocode_by_category(session: AsyncSession, game_cat: str):
    query = select(Catalog).where(Catalog.category == game_cat)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_promocode_by_name(session: AsyncSession, promocode: str ):
    query = select(Catalog).where(Catalog.name == promocode)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_available_promocode(session: AsyncSession, promocode: str):
    query = select(Catalog).where(Catalog.name == promocode, Catalog.quantity == 1, Catalog.in_cart == 0)
    result = await session.execute(query)
    return result.scalars().first()
    
async def orm_get_promocode_by_name_with_quantity_and_cart_status(session: AsyncSession, promocode: str,quantity: int,in_cart: int):
    query = select(Catalog).where(Catalog.name == promocode, Catalog.quantity == quantity, Catalog.in_cart == in_cart)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_next_available_promocode(session: AsyncSession, name: str):
    query = select(Catalog).where(Catalog.name == name, Catalog.quantity > 0).order_by(Catalog.id.asc())
    result = await session.execute(query)
    return result.scalar()


async def orm_get_all_promocodes_by_name(session: AsyncSession, promocode: str):
    query = select(Catalog).where(Catalog.name == promocode)
    result = await session.execute(query)
    return result.scalars().all()



async def orm_delete_promocode(session: AsyncSession, desc_name: str, id: int ):
    query = delete(Catalog).where(Catalog.name == desc_name,Catalog.id == id)
    result = await session.execute(query)
    await session.commit()
    return result.rowcount


async def orm_update_catalog_item(
    session: AsyncSession, promocode: str, field_name: str, new_value: str
):
    query = (
        update(Catalog).where(Catalog.name == promocode).values({field_name: new_value})
    )
    result = await session.execute(query)
    return result

async def orm_count_promocodes(session: AsyncSession, promocode_name: str):
    query = (
        select(func.count()).select_from(Catalog).where(Catalog.name == promocode_name, Catalog.quantity == 1)
    )
    result = await session.execute(query)
    return result.scalar()


################################ Работа с пользователями ##################################


async def orm_add_user(session: AsyncSession, user_id: str):
    add_in_Users = Users(user_id=user_id)
    session.add(add_in_Users)
    await session.commit()


async def orm_get_user_by_id(session: AsyncSession, useid: str):
    query = select(Users).where(Users.user_id == useid)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_users(session: AsyncSession):
    query = select(Users.user_id)
    result = await session.execute(query)
    return result.scalars().all()


################################ Работа с промокодами на скидки ###########################


async def orm_get_discount_promocode_by_promocode(session: AsyncSession, promo: str):
    query = select(Promokodes).where(Promokodes.promocode == promo)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_add_discount_promocode(session: AsyncSession, promocode: str, discount: int, usage: int):
    session.add(Promokodes(promocode=promocode, discount=discount, usage=usage))
    await session.commit()
    return promocode, discount, usage

async def orm_use_promocode(session: AsyncSession, user_id: int, promo: str):
    session.add(PromocodeUsage(user_id=user_id, promocode=promo))

    query = select(Promokodes).where(Promokodes.promocode == promo)
    result = await session.execute(query)
    promocode = result.scalars().first()

    if promocode.usage > 1:
        update_query = (
            update(Promokodes)
            .where(Promokodes.promocode == promocode)
            .values(usage=Promokodes.usage - 1)
        )
        await session.execute(update_query)
    else:
        delete_query = delete(Promokodes).where(Promokodes.promocode == promo)
        await session.execute(delete_query)

    await session.commit()

async def orm_get_user_promocode_usage(session: AsyncSession, user_id):
    query = select(PromocodeUsage).where(PromocodeUsage.user_id == user_id)
    result = await session.execute(query)
    return  result.scalars().first()
################################### Работа с админами ####################################

async def orm_get_admins(session: AsyncSession):
    query = select(Admins)
    result = await session.execute(query)
    return [admin.username for admin in result.scalars().all()]


async def orm_get_admin_by_username(session: AsyncSession, username: str):
    query = select(Admins).where(Admins.username == username)
    result = await session.execute(query)
    return result.scalar()


async def orm_add_admin(session: AsyncSession, username: str):
    session.add(Admins(username=username))
    


async def orm_del_admin(session: AsyncSession, username_to_delete: str):
    query = delete(Admins).where(Admins.username == username_to_delete)
    result = await session.execute(query)
    return result


#################################### Работа со спамом ####################################


async def orm_get_all_spam_messages(session: AsyncSession):
    query = select(Spam.smska)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_spam_message(session: AsyncSession, sms: str):
    query = delete(Spam).where(Spam.smska == sms)
    result = await session.execute(query)
    return result


async def orm_add_spam_message(session: AsyncSession, message: str):
    session.add(Spam(smska=message))
    await session.commit()
