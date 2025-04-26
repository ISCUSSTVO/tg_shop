from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class Menucallback(CallbackData, prefix ="menu"):
    level: int
    menu_name: str
    game_cat: Optional[str] = None 
    tovar: int|None = None
    page: int = 1


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
############################################################Главная клавиатура############################################################
def get_user_main_btns(*, level:int, sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Каталог": "catalog",
        "Варианы оплаты": "payment",
        "Корзина":"cart"
        }
    for text, menu_name  in btns.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text, callback_data=Menucallback(level=1, menu_name=menu_name).pack())) 
        elif menu_name == 'cart':
            keyboard.add(InlineKeyboardButton(text=text, callback_data=Menucallback(level=4, menu_name=menu_name).pack())) 
        else:
            keyboard.add(InlineKeyboardButton(text=text, callback_data =Menucallback(level=level, menu_name=menu_name).pack()))   
            
            
    return keyboard.adjust(*sizes).as_markup()

############################################################Клавиатура возвращения на перыдущий лвл############################################################
def back_kbds(
    *,
    level: int,
    sizes: tuple[int] = (1,)
):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Назад',
                callback_data=Menucallback(level=0, menu_name='main').pack()))

    keyboard.adjust(*sizes)
    return keyboard.as_markup()


############################################################Клавиатура покупки############################################################
def get_user_cart(
    *,
    level: int,
    page: int | None,
    pagination_btns: dict | None,
    tovar: int | None,
    sizes: tuple[int] = (3,2,2)
):
    keyboard = InlineKeyboardBuilder()
    if page:
        keyboard.add(InlineKeyboardButton(text='Удалить',
                    callback_data=Menucallback(level=level, menu_name='delete', tovar=tovar, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='-1',
                    callback_data=Menucallback(level=level, menu_name='decrement', tovar=tovar, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='+1',
                    callback_data=Menucallback(level=level, menu_name='increment', tovar=tovar, page=page).pack()))

        keyboard.adjust(*sizes)

        row = []
        for text, menu_name in pagination_btns.items():
            if menu_name == "next":
                row.append(InlineKeyboardButton(text=text,
                        callback_data=Menucallback(level=level, menu_name=menu_name, page=page + 1).pack()))
            elif menu_name == "previous":
                row.append(InlineKeyboardButton(text=text,
                        callback_data=Menucallback(level=level, menu_name=menu_name, page=page - 1).pack()))
        keyboard.add(InlineKeyboardButton(text = "Оформить заказ",
                                          callback_data= f'select_{tovar}'))
        keyboard.add(InlineKeyboardButton(text='Назад',
                                          callback_data= Menucallback(level=0, menu_name='main').pack()))
                
    else:
        keyboard.add(InlineKeyboardButton(text='Назад',
                                          callback_data= Menucallback(level=0, menu_name='main').pack()))

    keyboard.row(*row)
    return keyboard.adjust(*sizes).as_markup()
    
