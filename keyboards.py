from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Mahsulotlar", "Hisobotlar")
    kb.row("Agentlar", "Real hisobot")
    kb.row("Ombor")
    return kb


def agent_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Sotish", "Hisobot (kunlik)")
    kb.row("Hisobot (uzoq muddatlik)")
    return kb


def products_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Mahsulot qo'shish", "Mahsulot ro'yxati")
    kb.row("Ortga")
    return kb


def agents_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Agent qo'shish", "Agent ro'yxati")
    kb.row("Ortga")
    return kb


def reports_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Kunlik hisobot", "Haftalik hisobot")
    kb.row("Yillik hisobot")
    kb.row("Ortga")
    return kb


def long_reports_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("Kunlik", "Haftalik")
    kb.row("Yillik")
    kb.row("Ortga")
    return kb


def request_location_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    return kb


def confirm_sale_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Tasdiqlash", callback_data="sale_confirm"),
        InlineKeyboardButton("Bekor qilish", callback_data="sale_cancel")
    )
    kb.add(
        InlineKeyboardButton("Tahrirlash", callback_data="sale_edit")
    )
    return kb


def product_list_kb(products):
    kb = InlineKeyboardMarkup(row_width=1)
    for product in products:
        kb.add(
            InlineKeyboardButton(
                "{0} ({1} ta)".format(product["name"], product["quantity"]),
                callback_data="product_view:{0}".format(product["id"])
            )
        )
    return kb


def product_action_kb(product_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Tahrirlash", callback_data="product_edit:{0}".format(product_id)),
        InlineKeyboardButton("O'chirish", callback_data="product_delete:{0}".format(product_id))
    )
    return kb


def stock_product_kb(products):
    kb = InlineKeyboardMarkup(row_width=1)
    for product in products:
        kb.add(
            InlineKeyboardButton(
                "{0} ({1} ta)".format(product["name"], product["quantity"]),
                callback_data="stock_add:{0}".format(product["id"])
            )
        )
    return kb


def sale_product_kb(products):
    kb = InlineKeyboardMarkup(row_width=1)
    for product in products:
        kb.add(
            InlineKeyboardButton(
                product["name"],
                callback_data="sale_product:{0}".format(product["id"])
            )
        )
    return kb