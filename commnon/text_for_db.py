from aiogram.utils.formatting import as_marked_section
description_for_info_pages = {
    "main": "Воспользуйтесь кнопками",
    "catalog": "Список всех аккаунтов",
    "start":    "Вас приветсвует магазин промокодов Robert Poloson",
    "payment": as_marked_section(
        "Варианты оплаты:",
        "Картой в боте после выбора интерисующего вас промокода",
        marker="✅ ",
    ).as_markdown(),
}
