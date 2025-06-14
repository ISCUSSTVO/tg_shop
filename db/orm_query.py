from sqlalchemy import delete, distinct, select, update , func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import AllCodes, Catalog, Admins, Banner,PromocodeUsage, Promokodes, Spam, Users, Cart

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
async def orm_add_to_cart(session: AsyncSession, prod_id: str, user_id: int):
    tovar = await session.scalar(select(Catalog).where(Catalog.id == prod_id))
    code = await session.scalar(select(AllCodes).where(AllCodes.catalog_id==prod_id, AllCodes.flag == 1))
    
    if not tovar or tovar.quantity <= 0 or not code:
        return ('qwe')
    id = code.id
    cart = await session.scalar(select(Cart).where(Cart.user_id == user_id, Cart.product_name == tovar.name))
    if cart:
        cart.quantity += 1
        if code.id not in cart.codes:  
            cart.codes.append(id)
            await session.execute(
                update(Cart)
                .where(Cart.id == cart.id)
                .values(codes=cart.codes)
            )
    
    else:
        session.add(Cart(user_id=user_id, product_name=tovar.name, quantity = 1, price=tovar.price, codes = [code.id]))
    tovar.quantity -=1

    code.flag = 0
    await session.commit()





async def orm_get_cart(session: AsyncSession, user_id: int):
    query = select(Cart).where(Cart.user_id == user_id)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_cart_on_code(session: AsyncSession, user_id: int, code:str):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_name == code)
    result = await session.execute(query)
    return result.scalar()

async def orm_get_cart_on_id(session: AsyncSession, user_id: int, cart_id:str):
    query = select(Cart).where(Cart.user_id == user_id, Cart.id == cart_id)
    result = await session.execute(query)
    return result.scalar()

async def orm_delete_from_cart(session: AsyncSession, user_id: int, cart_id: int):
    cart = await session.scalar(select(Cart).where(Cart.user_id == user_id, Cart.id == cart_id))
    for code_id in cart.codes:
        code = await session.scalar(select(AllCodes).where(AllCodes.id == code_id))
        if code:
            code.flag = 1

    await session.execute(update(Catalog).where(Catalog.name == cart.product_name).values(quantity=Catalog.quantity + cart.quantity))

    await session.execute(delete(Cart).where(Cart.id == cart_id))

    await session.commit()

async def orm_decrement_cart_item(session: AsyncSession, user_id: int, catalog_id):
    q = 0
    tovar = await orm_get_promocode_by_name(session, catalog_id)
    cart = await session.scalar(select(Cart).where(Cart.user_id == user_id, Cart.product_name == tovar.name))
    code = await session.scalar(select(AllCodes).where(AllCodes.id.in_(cart.codes)))
    if cart is None or code is None:
        return "cart none"
    
    if cart.quantity > 1:
        q = 1
        cart.codes.remove(code.id)
        print ("qweasdqweasd",code.id)
        code.flag = 1
        cart.quantity-=1

        tovar.quantity +=1
        
         
        await session.execute(
            update(Cart)
            .where(Cart.id == cart.id)
            .values(quantity=cart.quantity, codes=cart.codes)
        )

    else:
        await orm_delete_from_cart(session, user_id, catalog_id)
        code.flag = 1
    await session.commit()
    return True if q == 1 else False


async def orm_get_code_on_id(session: AsyncSession, code_id):
    query = select(AllCodes).where(AllCodes.id == code_id)
    result = await session.execute(query)
    return result.scalar()

############### Работа с каталогами ##############
async def orm_add_code_to_catalog(session: AsyncSession, data: dict):

    name = data["name"]
    code = data["code"]
    tovar = await session.scalar(select(Catalog).where(Catalog.name == name))
    

    if tovar:
        quant = await orm_count_promocodes(session,tovar.id)
        price = tovar.price
        new_code = AllCodes(
            catalog_id=tovar.id,  
            code=code,
            flag=1
        )
        session.add(new_code)
        quant +=1 
        tovar.quantity =quant

    else:
        price = data["price"]
        new_catalog_item = Catalog(
            name=data["name"],
            category=data["category"],
            price=data["price"],
            discount=data["discount"],
            quantity =1
        )
        session.add(new_catalog_item)
        await session.flush()  

        new_code = AllCodes(
            catalog_id=new_catalog_item.id,  
            code=code,
            flag=1
        )
        session.add(new_code)

    await session.commit()
    return price

    

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


async def orm_get_promocode_by_name(session: AsyncSession, catalog_id: str ):
    query = select(Catalog).where(Catalog.id == catalog_id)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_promocode_by_name1(session: AsyncSession, name: str ):
    query = select(Catalog).where(Catalog.name==name)
    result = await session.execute(query)
    return result.scalars().first()

async def orm_get_available_promocode(session: AsyncSession, cat_id: str):
    query = select(Catalog).where(Catalog.id == cat_id)
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
    session.commit()

async def orm_count_promocodes(session: AsyncSession, cat_id: str):
    query = (
        select(func.count()).select_from(AllCodes).where(AllCodes.catalog_id == cat_id, AllCodes.flag ==1)
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
    await session.execute(delete(Spam).where(Spam.smska == sms))
    await session.commit()



async def orm_add_spam_message(session: AsyncSession, message: str):
    session.add(Spam(smska=message))
    await session.commit()
