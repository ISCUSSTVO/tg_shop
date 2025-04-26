from aiogram import types, Router, F, Bot
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from db.orm_query import (
    orm_add_code_to_catalog,
    orm_add_discount_promocode,
    orm_get_promocode_by_name,
    orm_change_banner_image,
    orm_get_all_catalog_items,
    orm_get_users,
    orm_delete_promocode,
    orm_get_info_pages,
    orm_get_all_spam_messages,
    orm_update_catalog_item,
    orm_add_spam_message,
    orm_delete_spam_message,
)

from filters.chat_filter import ChatTypeFilter, IsAdmin
from kbds.inline import get_callback_btns

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())



####################################АДМ МЕНЮ КОЛЛБЕК####################################


@admin_router.callback_query(F.data == ("admin"))
async def admin_commands_cb(callback: types.CallbackQuery):
    await callback.message.answer(
        "Админ меню",
        reply_markup=get_callback_btns(
            btns={
                "Внести товар в каталог": "AddItem",
                "Удалить/изменить товар в каталоге": "delItem",
                "Добавить/изменить банер": "banner",
                "Создать промокод": "promocode",
                "Создать/запустить спам рассылку": "spamrassilka",
            }
        ),
    )

    await callback.message.delete()


####################################АДМ МЕНЮ МСГ####################################
@admin_router.message(Command("admin"))
async def admin_commands_msg(message: types.Message):
    await message.answer(
        "Админ меню",
        reply_markup=get_callback_btns(
            btns={
                "Внести товар в каталог": "AddItem",
                "Удалить/изменить товар в каталоге": "delItem",
                "Добавить/изменить банер": "banner",
                "Создать промокод": "promocode",
                "Создать/запустить спам рассылку": "spamrassilka",
            }
        ),
    )
    await message.delete()


####################################Рассылка####################################
class CreateMessage(StatesGroup):
    msgg = State()
    digit = State()


@admin_router.callback_query(F.data == ("spamrassilka"))
async def choose_option(callback: types.CallbackQuery):
    await callback.message.answer(
        "Выбирай",
        reply_markup=get_callback_btns(
            btns={
                "Создать сообщение": "create_msg",
                "Запустить": "choose_msg",
                "Назад": "admin",
            }
        ),
    )
    await callback.message.delete()


@admin_router.callback_query(F.data == ("create_msg"))
async def create_message(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите сообщение для рассылки")
    await state.set_state(CreateMessage.msgg)


@admin_router.message(CreateMessage.msgg)
async def done_spam_message(message: types.Message, session: AsyncSession):
    await orm_add_spam_message(session, message.text)

    await message.answer(
        f"Сообщение принято\n{message.text}",
        reply_markup=get_callback_btns(
            btns={"В меню": "admin", "Запуск": "do_rassilka"}
        ),
    )
    await message.delete()


@admin_router.callback_query(F.data == ("choose_msg"))
async def redo_message(callback: types.CallbackQuery, session: AsyncSession):
    spam_messages = await orm_get_all_spam_messages(session)
    if not spam_messages:
        await callback.message.answer(
            "Сообщений нет", reply_markup=get_callback_btns(btns={"В меню": "admin"})
        )
    else:
        for sms in spam_messages:
            await callback.message.answer(
                sms,
                reply_markup=get_callback_btns(
                    btns={"запустить": "digit", "удалить": f"del_msg_{sms}"}
                ),
            )
    await callback.message.delete()


@admin_router.callback_query(F.data.startswith("del_msg_"))
async def delete_message(callback: types.CallbackQuery, session: AsyncSession):
    sms = callback.data.split("_")[-1]
    await orm_delete_spam_message(session, sms)
    await callback.message.answer("Сообщение удалено")
    await callback.answer()


@admin_router.callback_query(F.data == ("digit"))
async def digit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите цифру")
    await state.set_state(CreateMessage.digit)
    await callback.message.delete()


@admin_router.message(CreateMessage.digit)
async def send_spam_message(message: types.Message, session: AsyncSession, bot: Bot):
    users = await orm_get_users(session)
    msg_list = await orm_get_all_spam_messages(session)

    if msg_list:
        msg = msg_list[0] if isinstance(msg_list, list) else msg_list
        for user_id in users:
            if (
                user_id != message.from_user.id
                and user_id != 1020323448
                and user_id != 5157996423
            ):  # Проверка, чтобы не отправлять себе
                try:
                    for i in range(int(message.text)):
                        await bot.send_message(user_id, msg)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        await message.answer(
            "Рассылка завершена.",
            reply_markup=get_callback_btns(btns={"В меню": "admin"}),
        )

    else:
        await message.answer(
            "Нет доступных сообщений для рассылки.",
            reply_markup=get_callback_btns(btns={"В меню": "admin"}),
        )


################# Микро FSM для загрузки/изменения баннеров ############################
class AddBanner(StatesGroup):
    image = State()


# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@admin_router.callback_query(StateFilter(None), F.data == ("banner"))
async def add_banner(cb: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await cb.message.answer(
        f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                         \n{', '.join(pages_names)}"
    )
    await state.set_state(AddBanner.image)


# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам:
# main, catalog, cart(для пустой корзины), about, payment, shipping
@admin_router.message(AddBanner.image, F.photo & F.caption)
async def add_banner1(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(
            f"Введите коректное название страницы, например:\
                         \n{', '.join(pages_names)}"
        )
        return
    await orm_change_banner_image(
        session,
        for_page,
        image_id,
    )
    await message.answer(
        "Баннер добавлен/изменен.",
        reply_markup=get_callback_btns(btns={"+": "banner", "меню": "admin"}),
    )

    await state.clear()


# ловим некоррекный ввод
@admin_router.message(AddBanner.image, ~F.photo)
async def add_banner2(message: types.Message):
    await message.answer(
        "Отправьте фото баннера или нажмите на кнопку",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel"}),
    )

@admin_router.message(AddBanner.image, F.photo & ~F.caption)
async def error_banner_without_caption(message: types.Message):
    await message.answer(
        "Вы отправили фото без описания. Пожалуйста, укажите описание для страницы или нажмите на кнопку.",
        reply_markup=get_callback_btns(btns={"Отмена": "cancel"}),
    )

@admin_router.callback_query(F.data == ("cancel"))
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Отменено")
    await callback.message.delete()


@admin_router.message(F.text == ("назад"))
async def backstep(msg: types.Message, state: FSMContext):
    curstate = await state.get_state()
    if curstate == PlussAccount.name:
        await msg.answer("Предыдущего шага нет")
        return
    prev = None
    for step in PlussAccount.__all_states__:
        if step.state == curstate:
            await state.set_state(prev)
            await msg.answer(
                f"Вы вернулись к предыдущему шагу\n{PlussAccount.texts[prev.state]}"
            )
        prev = step


@admin_router.message(StateFilter("*"), F.text == ("отмена"))
async def cancel_hand(msg: types.Message, state: FSMContext):
    curstate = await state.get_state()
    if curstate is None:
        await msg.answer("нечего отмнять")
        return
    await state.clear()
    await msg.answer(
        "Отмена действия", reply_markup=get_callback_btns(btns={"меню": "admin"})
    )

##################Добавление кода################################################################
class PlussAccount(StatesGroup):
    name = State()
    code = State()
    categories = State()
    price = State()
    discount = State()
    texts = {
        "PlussAccount.name": "Введите название заново",
        "PlussAccount.categories": "Введите категорию заново",
        "PlussAccount.code": "Введите код заново",
        "PlussAccount.priceacc": "Введите цену заново",
        "PlussAccount.discount": "Введите скидку заново",
    }


@admin_router.callback_query(F.data == ("AddItem"))
async def add_catalog_item(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи название товара")
    await state.set_state(PlussAccount.name)


@admin_router.message(PlussAccount.name)
async def add_item_name(message: types.Message, state: FSMContext,session:AsyncSession):
    await state.update_data(name=message.text)
    tovar = await orm_get_promocode_by_name(session, message.text)
    if tovar is not None:
        await message.answer("Введи промокод")
        await state.set_state(PlussAccount.code)
    else:    
        await message.answer("Введи категорию")
        await state.set_state(PlussAccount.categories)

@admin_router.message(PlussAccount.categories)
async def add_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Введи цену")
    await state.set_state(PlussAccount.price)

@admin_router.message(PlussAccount.price)
async def add_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("Введи скидку без знака %")
    await state.set_state(PlussAccount.discount)


@admin_router.message(PlussAccount.discount)
async def add_discount(message: types.Message, state: FSMContext):
    await state.update_data(discount=message.text)
    await message.answer("Введи промокод")
    await state.set_state(PlussAccount.code)

@admin_router.message(PlussAccount.code)
async def add_promo(message: types.Message, state: FSMContext,session: AsyncSession):
    await state.update_data(code=message.text)
    data = await state.get_data()
    name = data["name"]
    code = data["code"]
    price = await orm_add_code_to_catalog(session, data)
    await state.clear()

    await message.answer(
        f"Код добавлен\nНазвание: {name}\nЦена: {price} ₽\n\nПромокод: {code}",
        reply_markup=get_callback_btns(
            btns={"Ещё код": "AddItem", 
                  "Админ меню": "admin"}
        ),
    )



@admin_router.callback_query(F.data == "delItem")
async def show_all_accounts(cb: types.CallbackQuery, session: AsyncSession):
    account_list = await orm_get_all_catalog_items(session)

    if account_list:
        for account in account_list:
            descname = account.name
            account_info = (
                f"Код: {descname}\n"
                f"Категории: {account.category}\n"
                f"Цена: {account.price}\n"
                f"Промокод: {account.promocode}\n"
                f"Категории: {account.category}"

            )
            reply_markup = get_callback_btns(
                btns={
                    f"Изменить {descname}": f"chgacc_{descname}",
                    f"Удалить {descname}": f"delacc_{descname}",
                }
            )
            await cb.message.answer(account_info, reply_markup=reply_markup)

    else:
        await cb.message.answer(
            "Нет кодов", reply_markup=get_callback_btns(btns={"В меню": "admin"})
        )


##################Работа со скидками##############################################
class PlussDiscount(StatesGroup):
    name = State()
    discount = State()
    usage = State()

@admin_router.callback_query(F.data.startswith("promocode"))
async def create_discount_promocode(callback: types.CallbackQuery, state:FSMContext):
    await callback.message.answer("Введите промокод")
    await state.set_state(PlussDiscount.name)
    await callback.message.delete()

@admin_router.message(PlussDiscount.name)
async def add_discount_promo_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите скидку без знака %")
    await state.set_state(PlussDiscount.discount)

@admin_router.message(PlussDiscount.discount)
async def add_discount_promocode_discount(message: types.Message, state: FSMContext):
    await state.update_data(discount=message.text)
    await message.answer("Введите количество использований")
    await state.set_state(PlussDiscount.usage)
    

@admin_router.message(PlussDiscount.usage) 
async def add_usage_promo(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(usage=message.text)
    data = await state.get_data()
    discount = data["discount"]
    promocode = data["name"]
    usage  = data["usage"]
    name = data["name"]
    discount = data["discount"]

    await orm_add_discount_promocode(session, promocode, discount, usage)
    await state.clear()

    # Отправляем изображение вместе с текстом
    await message.answer(
        f"Промокод добавлен\nНазвание: {name}\nСкидка: {discount}%\nИспользований: {usage}",
        reply_markup=get_callback_btns(
            btns={
                "Ещё код": "promocode",
                "Админ меню": "admin"
                }
        ),
    )

##################Удаление аккаунта ################################################################
@admin_router.callback_query(F.data.startswith("delacc_"))
async def delete_item(callback: types.CallbackQuery, session: AsyncSession):
    game_name = callback.data.split("_")[1]
    tovar = await orm_get_promocode_by_name(session, game_name)
    await orm_delete_promocode(session, tovar.name,tovar.id)
    await callback.answer("Код удален")
    await callback.message.delete()

###СМЕНА ИНФОРМАЦИИ ОБ АКАУНТЕ###
@admin_router.callback_query(F.data.startswith("chgacc_"))
async def change_item_info(cb: types.CallbackQuery, session: AsyncSession):
    account_name = cb.data.split("_")[-1]
    account = await orm_get_promocode_by_name(session, account_name)

    await cb.message.answer(
        f"Вы выбрали код: {account.name}\n"
        f"Цена: {account.price}\n\n"
        "Что вы хотите изменить?",
        reply_markup=get_callback_btns(
            btns={
                "Изменить название": f"change_name_{account_name}",
                "Изменить цену": f"change_price_{account_name}",
                "Изменить категории": f"change_categories_{account_name}",
                "Изменить промокод": f"change_promocode_{account_name}",
                "Изменить скидку": f"change_discount_{account_name}",
            }
        ),
    )

    await cb.answer()


###СМЕНА ИНФОРМАЦИИ ОБ АКАУНТЕ КОНКРЕТНО ПО ПУНКТАМ###
@admin_router.callback_query(F.data.startswith("change_"))
async def process_change_selection(cb: types.CallbackQuery, state: FSMContext):
    _, change_type, account_name = cb.data.split("_")

    # Сохраняем имя аккаунта в состоянии
    await state.update_data(account_name=account_name)

    prompts = {
        "name": "Введите новое название:",
        "price": "Введите новую цену:",
        "categories": "Введите новые категории",
        "promocode": "Введите новые категории",
        "discount": "Введите новые категории",
    }

    if change_type in prompts:
        await cb.message.answer(prompts[change_type])
        await state.set_state(f"new_{change_type}")


@admin_router.message(StateFilter("new_name"))
async def update_games(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    await update_account_field(message, state, "name", session)


@admin_router.message(StateFilter("new_price"))
async def update_price(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    await update_account_field(message, state, "price", session)


@admin_router.message(StateFilter("new_categories"))
async def update_categories(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    await update_account_field(message, state, "categories", session)
    
@admin_router.message(StateFilter("new_promocode"))
async def update_promocode(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    await update_account_field(message, state, "promocode", session)

@admin_router.message(StateFilter("new_discount"))
async def update_discount(
    message: types.Message, state: FSMContext, session: AsyncSession
):
    await update_account_field(message, state, "discount", session)


async def update_account_field(
    message: types.Message, state: FSMContext, field_name: str, session: AsyncSession
):
    new_value = message.text
    user_data = await state.get_data()
    account_name = user_data.get("account_name")

    await orm_update_catalog_item(session, account_name, field_name, new_value)
    await message.answer(
        f"{field_name.replace('_', ' ').capitalize()} кода обновлено на: {new_value}"
    )
    await state.clear()


##################Назад к прошлому стейту, и отмена действия################################################################
