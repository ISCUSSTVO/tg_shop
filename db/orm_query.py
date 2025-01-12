from sqlalchemy import delete, distinct, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Catalog, Admins, Banner, Promokodes, Spam, Users

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


############### Работа с каталогами ##############


async def orm_add_Promocode(session: AsyncSession, data: dict):
    obj = Catalog(
        name=data["name"],
        category=data["category"],
        promocode=data["promocode"],
        price=data["price"],
        discount=data["discount"],
    )
    session.add(obj)
    name = data["name"]
    promocode = data["promocode"]
    price = data["price"]
    await session.commit()
    return name, promocode,price


async def orm_get_catalog(session: AsyncSession):
    query = select(Catalog)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_category_catalog(session: AsyncSession):
    query = select(distinct(Catalog.category))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_promocode_by_category(session: AsyncSession, game_cat: str):
    query = select(Catalog).where(Catalog.category == game_cat)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_promocode_by_name(session: AsyncSession, promocode: str):
    query = select(Catalog).where(Catalog.name == promocode)
    result = await session.execute(query)
    account = result.scalars().first()
    print(f"DEBUG: orm_get_promocode_by_name - account: {account}")  # Отладочное сообщение
    return account


async def orm_delete_promocode(session: AsyncSession, desc_name: str):
    query = delete(Catalog).where(Catalog.name == desc_name)
    result = await session.execute(query)
    await session.commit()
    print(f"DEBUG: orm_delete_promocode - rowcount: {result.rowcount}")  # Отладочное сообщение
    return result.rowcount


async def orm_update_catalog(
    session: AsyncSession, promocode: str, field_name: str, new_value: str
):
    query = (
        update(Catalog).where(Catalog.name == promocode).values({field_name: new_value})
    )
    result = await session.execute(query)
    return result


################################ Работа с пользователями ##################################


async def orm_add_user(session: AsyncSession, user_id: str):
    add_in_Users = Users(user_id=user_id)
    session.add(add_in_Users)
    await session.commit()


async def orm_get_user_by_userid(session: AsyncSession, useid: str):
    query = select(Users).where(Users.user_id == useid)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_users(session: AsyncSession):
    query = select(Users.user_id)
    result = await session.execute(query)
    return result.scalars().all()


################################ Работа с промокодами ###########################


async def orm_chek_promo(session: AsyncSession, promo: str):
    query = select(Promokodes).where(Promokodes.promocode == promo)
    result = await session.execute(query)
    return result.scalars().all()


################################### Работа с админами ####################################


async def orm_get_admins(session: AsyncSession):
    query = select(Admins)
    result = await session.execute(query)
    return [admin.username for admin in result.scalars().all()]


async def orm_get_admin(session: AsyncSession, username: str):
    query = select(Admins).where(Admins.username == username)
    result = await session.execute(query)
    return result.scalar()


async def orm_add_admin(session: AsyncSession, username: str):
    obj = Admins(username=username)
    session.add(obj)


async def orm_del_admin(session: AsyncSession, username_to_delete: str):
    query = delete(Admins).where(Admins.username == username_to_delete)
    result = await session.execute(query)
    return result


#################################### Работа со спамом ####################################


async def orm_get_spam(session: AsyncSession):
    query = select(Spam.smska)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_del_spam(session: AsyncSession, sms: str):
    query = delete(Spam).where(Spam.smska == sms)
    result = await session.execute(query)
    return result


async def orm_add_message_spam(session: AsyncSession, message: str):
    result = Spam(smska=message)
    session.add(result)
    await session.commit()
