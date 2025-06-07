import asyncio
import json
from aiogram import Bot, types, Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from db.orm_query import (
    orm_add_to_cart,
    orm_add_user,
    orm_get_promocode_by_name,
    orm_get_discount_promocode_by_promocode,
    orm_get_user_promocode_usage,
    orm_get_user_by_id,
    orm_get_banner,
    orm_use_promocode,
    orm_get_cart_on_id,
    orm_get_code_on_id,
)

from handlers.menu_proccesing import (
    promocodes_catalog, 
    get_menu_content, 
    payment, 
    cart)

from kbds.inline import Menucallback, get_callback_btns, get_callback_btns_url

from kbds.reply import get_keyboard


user_router = Router()
sent_msg = set()


@user_router.message(F.text.lower().contains("start") | F.text.lower().contains("старт"))
@user_router.message(CommandStart())
async def start(message: types.Message, session: AsyncSession):
    banner = await orm_get_banner(session, "start")
    if not await orm_get_user_by_id(session, message.from_user.id):
        await orm_add_user(session, message.from_user.id)
    await message.answer_photo(
        photo=banner.image,
        caption=banner.description,
        reply_markup=get_keyboard(
            btns={"📜Главное меню", "🤓Отзывы", "📺Тг канал", "🛒Корзина"}, sizes=(2,)
        ),
    )


@user_router.callback_query(F.data == "menu")
@user_router.message(F.text.lower().contains("main") | F.text.lower().contains("меню"))
async def menu(message: types.Message | types.CallbackQuery, session: AsyncSession):
    is_callback = isinstance(message, types.CallbackQuery)

    if is_callback:
        await message.answer("Загрузка главного меню...")
    media, reply_markup = await get_menu_content(
        session, level=0, menu_name="main", user_id=1
    )

    if isinstance(media, InputMediaPhoto):
        if is_callback:
            await message.message.answer_photo(
                media.media, caption=media.caption, reply_markup=reply_markup
            )
        else:
            await message.answer_photo(
                media.media, caption=media.caption, reply_markup=reply_markup
            )


@user_router.callback_query(Menucallback.filter())
async def user_menu(
    callback: CallbackQuery, callback_data: Menucallback, session: AsyncSession
):

    result = await get_menu_content(
        session=session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        user_id=callback.from_user.id,
        tovar=callback_data.tovar,
        page=callback_data.page,
        
    )
    if result is None:
        await callback.answer("Не удалось получить данные.", show_alert=True)
        return

    
    media,reply_markup,= result
    if media == ("qwe"):
        await callback.answer("Товара нет в наличии")
    else:
        await callback.message.edit_media(media=media, reply_markup=reply_markup)
        await callback.answer()


@user_router.callback_query(F.data.startswith("add_cart_"))
async def add_cart(callback_query: types.CallbackQuery, session: AsyncSession):
    data = callback_query.data.split("_")
    prod_id = data[-1]
    tovar = await orm_get_promocode_by_name(session,prod_id)
    await orm_add_to_cart(session, prod_id, callback_query.from_user.id)
    if not tovar:
        await callback_query.answer("Товара закончился", show_alert=True)
    else: 
        await callback_query.answer("Товара добавлен в корзину", show_alert=True)

    media, kbds = await payment(session, prod_id, callback_query.from_user.id)
    await callback_query.message.edit_media(media=media, reply_markup=kbds)
        

        


@user_router.callback_query(F.data.startswith("show_category_"))
async def process_show_cats(callback_query: types.CallbackQuery, session: AsyncSession):
    game_cat = callback_query.data.split("_")[-1]
    media, kbds = await promocodes_catalog(session, level=2,game_cat=game_cat)
    await callback_query.message.edit_media(media=media, reply_markup=kbds)
    await callback_query.answer()


@user_router.callback_query(F.data.startswith("show_code_"))
async def process_show_promocodes(
    callback_query: types.CallbackQuery, session: AsyncSession
):
    tovar = callback_query.data.split("_")[-1]
    print("tovar",tovar)
    media, kbds = await payment(session, tovar, callback_query.from_user.id)
    await callback_query.message.edit_media(media=media, reply_markup=kbds)
    await callback_query.answer()


@user_router.callback_query(F.data.startswith("select_"))
async def purchase(callback: types.CallbackQuery, session: AsyncSession):
    catalog_id = callback.data.split("_")[-1]
    cart = await orm_get_cart_on_id(session, callback.from_user.id, catalog_id)
    for i in cart.codes:
        w = i 
        print ('aqwjkeoiqwe',w)
    code = await orm_get_code_on_id(session, w)
    promocode = await orm_get_promocode_by_name(session, code.catalog_id)
    if promocode.discount != 0:
        price = promocode.price - promocode.price * promocode.discount // 100
    else:
        price = promocode.price
    prices = [LabeledPrice(label=promocode.name, amount=promocode.price * 100)]
    #await callback.message.answer(f"Товар: <strong>{promo}</strong>\nЦена: {price}₽",parse_mode="HTML")
    data = {
        "user_id": callback.from_user.id,
        "service": "offline_activation",
        "game_name": promocode.name,
    }
    payload = json.dumps(data)

    banner = await orm_get_banner(session, "catalog")

    try:
        await callback.message.answer_invoice(
            title="🎮 Покупка",
            description=promocode.name,
            payload="wqe",
            provider_token="390540012:LIVE:60574",
            currency="RUB",
            prices=prices,
            photo_url=banner.image ,
        )
    except Exception as e:
        await callback.answer(f"Ошибка при отправке инвойса: {str(e)}", show_alert=True)
    await callback.message.answer(
        "После оплаты нажмите на кнопку",
        reply_markup=get_callback_btns(btns={"оплатил": f"msg_{promocode.name}"}),
    )


@user_router.pre_checkout_query()
async def process_pre_checkout_query(
    pre_checkout_query: types.PreCheckoutQuery, bot: Bot
):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@user_router.callback_query(F.data.startswith("msg_"))
async def send_message_to_adm(
    callback: types.CallbackQuery, bot: Bot, session: AsyncSession
):
    mssg = callback.data.split("_")[-1]
    tovar = await orm_get_promocode_by_name(session, mssg)

    msg_key = (tovar.id, callback.from_user.full_name)
    if msg_key in sent_msg:
        await callback.message.answer(
            "Обратитесь к администратору с чеком об оплате\n\nhttps://t.me/civqw"
        )
        await callback.answer()
        return

    await bot.send_message(
        "-4672084883",
        f"{tovar.name}\nПромокод: {tovar.promocode}\nЦена: {tovar.price}\n\nhttps://t.me/{callback.from_user.username}",
    )
    sent_msg.add(msg_key)
    await callback.message.answer(
        "Обратитесь к администратору с чеком об оплате\n\nhttps://t.me/civqw"
    )
    await callback.answer()


###########################Получение промокода на скидку################
class GetPromo(StatesGroup):
    Promo = State()


@user_router.callback_query(F.data == ("promo"))
async def chek_promocode(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession, level=3
):
    banner = await orm_get_banner(session, "catalog")
    image = None
    if banner:
        image = InputMediaPhoto(media=banner.image, caption="\nВведите промокод")
    await callback.message.edit_media(
        media=image,
        reply_markup=get_callback_btns(
            btns={
                "назад": Menucallback(level=level - 2, menu_name="game_catalog").pack()
            }
        ),
    )
    await state.set_state(GetPromo.Promo)
    await state.update_data(level=level, user_id=callback.from_user.id)


@user_router.message(GetPromo.Promo)
async def get_promocode(
    message: types.Message, session: AsyncSession, state: FSMContext
):
    promo = message.text
    result = await orm_get_discount_promocode_by_promocode(session, promo)
    res = await orm_get_user_promocode_usage(session, message.from_user.id)
    data = await state.get_data()
    level = data.get("level", 3)
    user_id = data.get("user_id", message.from_user.id)

    if res:
        caption = f"Вы уже использовали промокод\nВаш промокод: {res.promocode}"
    elif result:
        await orm_use_promocode(session, message.from_user.id, promo)
        caption = "Промокод принят"
    else:
        caption = "Нет такого промокода"

    banner = await orm_get_banner(session, "catalog")
    image = InputMediaPhoto(media=banner.image, caption=caption)
    await message.answer_photo(
        photo=image.media,
        caption=image.caption,
        reply_markup=get_callback_btns(
            btns={
                "назад": Menucallback(level=level - 2, menu_name="game_catalog").pack()
            }
        ),
    )
    await state.clear()
    await message.delete()
    await asyncio.sleep(5)
    await message.delete()

    if result and not res:
        media, kbds = await payment(session, promo, user_id)
        await message.answer_photo(
            photo=media.media, caption=media.caption, reply_markup=kbds
        )

@user_router.message()
async def null_message(message: types.Message, session: AsyncSession):
    text = message.text.strip().lower()
    if "тг" in text:
        await message.reply(
            "Ссылочка внизу ⬇️",
            reply_markup=get_callback_btns_url(
                btns={"Тг канал": "https://t.me/promokodiciq"}
            ),
        )
    elif "отзывы" in text:
        await message.reply(
            "Ссылочка внизу ⬇️",
            reply_markup=get_callback_btns_url(
                btns={"Отзывы": "https://t.me/promokodiciq"}
            ),
        )
    elif "корзина" in text or "cart" in text:
        image, kbds = await cart(
            session,
            level=4,
            page=1,
            user_id=message.from_user.id,
            menu_name="cart",
            tovar=None,
        )
        await message.answer_photo(
            photo=image.media, caption=image.caption, reply_markup=kbds
        )
    else:
        await message.reply("напиши старт")
