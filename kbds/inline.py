from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

class Menucallback(CallbackData, prefix ="menu"):
    level: int
    menu_name: str
    page: int = 1

class BUYcallback(CallbackData, prefix = 'cart'):
    menu_name: str


##################Создание инлайн клавиатуры  ################################################################
def  get_callback_btns(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
            
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()

def  get_callback_btns_url(
    *,
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, url in btns.items():
            
        keyboard.add(InlineKeyboardButton(text=text, url=url))

    return keyboard.adjust(*sizes).as_markup()
##################Создание  клавиатуры  ################################################################
def get_keyboard(
    *,
    btns: str,
    placeholder: str = None,
    request_contact: int = None,
    request_location: int = None,
    sizes: tuple[int] = (2,),
):

    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):
        
        if request_contact and request_contact == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))

        elif request_location and request_location == index:
            keyboard.add(KeyboardButton(text=text, request_location=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
            resize_keyboard=True, input_field_placeholder=placeholder)
############################################################Главная клавиатура############################################################
def get_user_main_btns(*, level:int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Каталог": "catalog",
        "Варианы оплаты": "payment",
        }
    for text, menu_name  in btns.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text, callback_data=Menucallback(level=1, menu_name=menu_name).pack()))   
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data =Menucallback(level=level, menu_name=menu_name).pack()))   
            
    return keyboard.adjust(*sizes).as_markup()



############################################################Клавиатура возвращения на перыдущий лвл############################################################
def back_kbds(
    *,
    level: int,
    sizes: tuple[int] = (1)
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Назад',
                callback_data=Menucallback(level=level -1, menu_name='catalog').pack()))

    keyboard.adjust(*sizes)
    return keyboard.as_markup()


############################################################Клавиатура покупки############################################################
