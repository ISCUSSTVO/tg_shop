from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Catalog, Admins, Banner, Promokodes, Spam, Users

############### Работа с баннерами (информационными страницами) ###############

async def orm_add_banner_description(session: AsyncSession, data: dict):
    #Добавляем новый или изменяем существующий по именам
    #пунктов меню: main, about, cart, shipping, payment, catalog
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()

async def orm_add_img (session: AsyncSession, data: dict):
    query = select (Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, image = image) for name, image in data.items()])
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


############### Работа с каталогами##############
async def orm_add_Promocode(session: AsyncSession, data: dict):
    obj = Catalog(
        name = data["name"],
        category=data["category"],
        promocode=data["promocode"],
        price=data["price"],
    )
    session.add(obj)
    name = data["name"]
    price = data["price"]
    await session.commit()
    return name,price

async def orm_add_user(session: AsyncSession, user_id:str):
    add_in_Users = Users(user_id=user_id)
    session.add(add_in_Users)
    await session.commit()


async def orm_check_catalog(session: AsyncSession):
    query = select(Catalog)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_chek_promo(session: AsyncSession, promo:str):
    query = select(Promokodes).where(Promokodes.promocode == promo)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_chek_users(session:AsyncSession, useid: str):
    query = select(Users).where(Users.user_id == useid)
    result  = await session.execute(query)
    return result.scalars().all()

async def orm_chek_users1(session:AsyncSession):
    query = select(Users.user_id)
    result  = await session.execute(query)
    return result.scalars().all()

async def orm_check_catalog_categ(session: AsyncSession):
    query = select(Catalog.category)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_category(session:AsyncSession, game_cat:str):
    query = select(Catalog).where(Catalog.category == game_cat)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_spam(session:AsyncSession):
    query = select(Spam.smska)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_change_account(session: AsyncSession, account_name:str):
    query = select(Catalog).where(Catalog.name == account_name)
    result = await session.execute(query)
    return result.scalars().one_or_none()

async def orm_select_tovar(session: AsyncSession, tovar:str):
    query = select(Catalog).where(Catalog.name == tovar)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_del_account(session: AsyncSession, desc_name : str):
    query = delete(Catalog).where(Catalog.name ==desc_name)
    result = await session.execute(query)
    return result

async def orm_chng_spam(session:AsyncSession, op:str):
    query = update(Spam.smska).values(op)
    result = await session.execute(query)
    return result.scalar_one()

async def orm_del_admin(session: AsyncSession, username_to_delete : str):
    query = delete(Admins).where(Admins.username == username_to_delete)
    result = await session.execute(query)
    return result

async def orm_update_catalog(session: AsyncSession, account_name : str, field_name: str, new_value: str ):
    query = update(Catalog).where(Catalog.name == account_name).values({field_name: new_value})
    result = await session.execute(query)
    return result
############### Работа с админским хендлером###############
async def orm_get_admins(session: AsyncSession):
    query = select(Admins)
    result = await session.execute(query)
    return [admin.username for admin in result.scalars().all()]

async def orm_get_admin(session: AsyncSession, username: str):
    query = select(Admins).where(Admins.username == username)
    result = await session.execute(query)
    return result.scalar()

async def orm_add_admin(session: AsyncSession, username: str):
    obj = Admins(username = username)
    session.add(obj)

####################################Спам##################################

async def orm_add_message_spam(session:AsyncSession, message:str):
    result = Spam(
        smska = message
    )
    session.add(result)
    await session.commit()




