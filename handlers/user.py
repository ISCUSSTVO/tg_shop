import asyncio
import json
from aiogram import Bot, types, Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from utils.paginator import Paginator
from sqlalchemy.ext.asyncio import AsyncSession
from db.engine import AsyncSessionLocal
from db.orm_query import (
    orm_add_to_cart,
    orm_chek_cart,
    orm_add_user, 
    orm_chek_promo,
    orm_delete_from_cart, 
    orm_get_promocode_by_name,
    orm_get_promocode_usage, 
    orm_get_user_by_userid, 
    orm_get_banner,
    orm_use_promocode,
    orm_minus_quant,
    orm_reduce_service_in_cart,
    orm_delete_promocode
    )

from handlers.menu_proccesing import (
    promocodes_catalog, 
    get_menu_content, 
    payment,
    cart)

from kbds.inline import (Menucallback, 
    get_keyboard,  
    get_callback_btns, 
    get_callback_btns_url)


user_router = Router()
sent_msg = set()



@user_router.message(F.text.lower().contains('start') | F.text.lower().contains('старт'))
@user_router.message(CommandStart())
async def start(message:types.Message):
    async with AsyncSessionLocal as session:
        user_id = message.from_user.id
        banner = await orm_get_banner(session, "start")

        if not await orm_get_user_by_userid(session, user_id):
            await orm_add_user(session, user_id)  

        await message.answer_photo(photo=banner.image, caption=banner.description, reply_markup=get_keyboard(btns={
            "📜Главное меню",
            "🤓Отзывы",
            "📺Тг канал",
            "🛒Корзина"
        },sizes=(2,)) )

@user_router.message(F.text.lower().contains('тг '))
async def tg_chennel(message: types.Message):
    await message.reply("Ссылочка внизу ⬇️", reply_markup= get_callback_btns_url(btns={
        "Тг канал": "https://t.me/promokodiciq"
    }))

@user_router.message(F.text.lower().contains('отзывы'))
async def Otzivi(message: types.Message):
    await message.answer("Ссылочка внизу ⬇️", reply_markup= get_callback_btns_url(btns={
        "Отзывы": "https://t.me/promokodiciq"
    }))

@user_router.message(F.text.lower().contains('корзина') | F.text.lower().contains('cart'))
async def go_to_cart (message:types.Message, session: AsyncSession):
    image, kbds = await cart(session,level=4,page=1, user_id=message.from_user.id,menu_name='cart',tovar=None,price=None) 
    await message.answer_photo(photo=image.media, caption=image.caption, reply_markup=kbds)

#@user_router.callback_query(F.data.startswith('increment_') | F.data.startswith('decrement_') | F.data.startswith('delete_') | F.data.startswith('next_') | F.data.startswith('previous_'))
#async def cart_handly(callback: CallbackQuery, session: AsyncSession):
#    data = callback.data.split('_')
#    menu_name = data[0]
#    page = int(data[-1])
#    tovar = data[-2]
# 
#    current_cart = await orm_chek_cart(session, callback.from_user.id)
#    
#    paginator = Paginator(current_cart, page=page, per_page=1)
#    current_page_items = paginator.get_page()
#    print(f"qewasdy7h67yh6712h471h723h78ashdbny7ny237y7qr: {current_page_items}")
#
#
#
#    if not current_page_items:
#        page = max(1, paginator.page)
#        current_page_items = paginator.get_page()
#
#
#    if menu_name == "delete":
#        await orm_delete_from_cart(session, callback.from_user.id, tovar)
#        page = max(1, page - 1)
#    
#    elif menu_name == "decrement":
#        is_cart = await orm_reduce_service_in_cart(session, callback.from_user.id, tovar)
#        if is_cart == "cart none":
#            await callback.answer("динахуй")
#            
#        if not is_cart:
#            await callback.answer("Товар убран из корзины")
#            page = max(1, page - 1)
#
#    elif menu_name == "increment":
#        a = await orm_add_to_cart(session, tovar, callback.from_user.id, current_cart[0].price)
#        if a == False:
#            await callback.answer("Товар закончился")
#
#    elif menu_name == "next":
#        page = min(page + 1 , paginator.pages)
#
#    elif menu_name == "previous":
#        page = max(1 , page - 1 )
#
#    image, kbds = await cart(session, user_id=callback.from_user.id, page=page)
#    for row in kbds.inline_keyboard:
#        for button in row:
#            if button.callback_data and button.callback_data.startswith(menu_name):
#                button.callback_data = f"{menu_name}_{tovar}_{page}"
#
#    await callback.message.edit_media(media=image,reply_markup=kbds)
#
#
@user_router.callback_query(F.data == 'menu')
@user_router.message(F.text.lower().contains('menu') | F.text.lower().contains('меню'))
async def menu_handler(message: types.Message | types.CallbackQuery, session: AsyncSession):
    is_callback = isinstance(message, types.CallbackQuery)

    if is_callback:
        await message.answer("Загрузка главного меню...") 

    media, reply_markup = await get_menu_content(session, level=0, menu_name="main", user_id=1)

    if isinstance(media, InputMediaPhoto):
        if is_callback:
            await message.message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)
        else:
            await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)

@user_router.callback_query(Menucallback.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: Menucallback, session: AsyncSession):

    result = await get_menu_content(
        session = session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        user_id=callback.from_user.id,
        game_cat = callback_data.game_cat,
        tovar = callback_data.tovar,
        page = callback_data.page,
        price=callback_data.price,

    )
    if result is None:
        await callback.answer("Не удалось получить данные.", show_alert=True)
        return
    
    media, reply_markup, = result
    await callback.message.edit_media(media=media, reply_markup=reply_markup )
    await callback.answer()

@user_router.callback_query(F.data.startswith('add_cart_'))
async def add_cart(callback_query: types.CallbackQuery, session: AsyncSession):
    data = callback_query.data.split('_')
    car = await orm_chek_cart(session, callback_query.from_user.id)
    promo = await orm_get_promocode_by_name(session, data[-2])
    if promo.quantity == 0:
        await callback_query.answer("Товара нет в наличии")
        await orm_delete_promocode(session, data[-2])
        image, kbds = await payment(session, data[-2], callback_query.from_user.id, level=2)
        await callback_query.message.edit_media(media=image, reply_markup=kbds)
    
        
    else:
        await orm_add_to_cart(session, data[-2], callback_query.from_user.id, price=data[-1])
        await callback_query.answer("Товар добавлен в корзину")
        await orm_minus_quant(session, data[-2])


@user_router.callback_query(F.data.startswith('show_category_'))
async def process_show_cat(callback_query: types.CallbackQuery, session: AsyncSession):
    # Извлекаем категорию из колбек-данных
    game_cat = callback_query.data.split('_')[-1]  # Получаем название категории
    media, kbds = await promocodes_catalog(session, game_cat, level=2)
    # Отправляем сообщение пользователю
    await callback_query.message.edit_media(media=media, reply_markup=kbds)
    await callback_query.answer()

@user_router.callback_query(F.data.startswith('show_promocode_'))
async def process_show_game(callback_query: types.CallbackQuery, session: AsyncSession):
    # Извлекаем категорию из колбек-данных
    tovar = callback_query.data.split('_')[-1]  # Получаем название категории
    media, kbds = await payment(session, tovar,  callback_query.from_user.id, level=3)
    # Отправляем сообщение пользователю
    await callback_query.message.edit_media(media=media, reply_markup=kbds)
    await callback_query.answer()

@user_router.callback_query(F.data.startswith('select_'))
async def buy(callback:types.CallbackQuery, session: AsyncSession):
    promo = callback.data.split('_')[-1]
    promocode = await orm_get_promocode_by_name(session, promo)
    if promocode.discount != 0:
        price = promocode.price - promocode.price * promocode.discount // 100
        prices = [LabeledPrice(label=promocode.name, amount=price * 100)] 
        await callback.message.answer(f'Цена: {prices}₽')
    else:
        prices = [LabeledPrice(label=promocode.name, amount=promocode.price * 100)] 
        await callback.message.answer(f'Цена: {prices}₽')
    data = {
        "user_id": callback.from_user.id,
        "service": "offline_activation",
        "game_name": promo
    }
    payload=json.dumps(data)

    banner = await orm_get_banner(session, 'catalog')

    try:
        await callback.message.answer_invoice(
            title='🎮 Покупка промокода',
            description=promocode.name,
            payload=payload,
            provider_token='381764678:TEST:93111',  
            currency='RUB',
            prices=prices,
            photo_url=banner.image if banner else None,
        )
    except Exception as e:
        await callback.answer(f"Ошибка при отправке инвойса: {str(e)}", show_alert=True)
    await callback.message.answer('После оплаты нажмите на кнопку', reply_markup= get_callback_btns(btns={
        'оплатил': f'msg_{promocode.name}'
    }))

@user_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@user_router.callback_query(F.data.startswith('msg_'))
async def send_message_to_adm(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):   
    mssg = callback.data.split('_')[-1]
    tovar = await orm_get_promocode_by_name(session, mssg)
    
    msg_key = (tovar.id, callback.from_user.full_name)
    if msg_key in sent_msg:
        await callback.message.answer('Обратитесь к администратору с чеком об оплате\n\nhttps://t.me/civqw')
        await callback.answer()
        return

    await bot.send_message('-4672084883', f'{tovar.name}\nПромокод: {tovar.promocode}\nЦена: {tovar.price}\n\nhttps://t.me/{callback.from_user.username}')
    sent_msg.add(msg_key)
    await callback.message.answer('Обратитесь к администратору с чеком об оплате\n\nhttps://t.me/civqw')
    await callback.answer()




###########################Получение промокода################
class GetPromo(StatesGroup):
    Promo = State()

@user_router.callback_query(F.data == ('promo'))
async def chek_promocode(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, level=3):
    banner = await orm_get_banner(session, "catalog")
    image = None
    if banner:
        image = InputMediaPhoto(
            media=banner.image,
            caption="\nВведите промокод"
        )
    await callback.message.edit_media(media=image, reply_markup=get_callback_btns(btns={
        'назад': Menucallback(level=level - 2, menu_name='game_catalog').pack()
    }))
    await state.set_state(GetPromo.Promo)
    await state.update_data(level=level, user_id=callback.from_user.id)
    # await callback.message.delete()

@user_router.message(GetPromo.Promo)
async def get_promocode(message: types.Message, session: AsyncSession, state: FSMContext):
    promo = message.text
    result = await orm_chek_promo(session, promo)
    res = await orm_get_promocode_usage(session, message.from_user.id)
    data = await state.get_data()
    level = data.get('level', 3)
    user_id = data.get('user_id', message.from_user.id)

    if res:
        caption = f'Вы уже использовали промокод\nВаш промокод: {res.promocode}'
    elif result:
        await orm_use_promocode(session, message.from_user.id, promo)
        caption = 'Промокод принят'
    else:
        caption = 'Нет такого промокода'

    banner = await orm_get_banner(session, "catalog")
    image = InputMediaPhoto(
        media=banner.image,
        caption=caption
    )
    await message.answer_photo(photo=image.media, caption=image.caption, reply_markup=get_callback_btns(btns={
        'назад': Menucallback(level=level - 2, menu_name='game_catalog').pack()
    }))
    await state.clear()
    await message.delete()
    await asyncio.sleep(5)
    await message.delete()

    if result and not res:
        media, kbds = await payment(session, promo, user_id, level)
        await message.answer_photo(photo=media.media, caption=media.caption, reply_markup=kbds)




@user_router.message()
async def null_message(message: types.Message):
    await message.answer('напиши старт')