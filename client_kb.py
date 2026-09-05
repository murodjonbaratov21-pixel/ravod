from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database

remove_kb = ReplyKeyboardRemove()

def get_user_kb(telegram_id):
    kb = [
        [KeyboardButton(text="🛍 Katalog"), KeyboardButton(text="🛒 Savatcha")],
        [KeyboardButton(text="ℹ️ Bot haqida")]
    ]
    if database.is_admin(telegram_id):
        kb.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Kerakli bo'limni tanlang...")

cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Orqaga")]], resize_keyboard=True)
contact_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)], [KeyboardButton(text="🔙 Orqaga")]], resize_keyboard=True)

def get_categories_kb(categories):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat[1], callback_data=f"cat_{cat[0]}")
    builder.adjust(2)
    return builder.as_markup()

def get_products_list_kb(products):
    builder = InlineKeyboardBuilder()
    for prod in products:
        builder.button(text=prod[1], callback_data=f"prod_{prod[0]}")
    builder.button(text="🔙 Bo'limlarga qaytish", callback_data="back_to_cats")
    builder.adjust(1)
    return builder.as_markup()

def get_product_actions_kb(product_id, is_available, category_id):
    builder = InlineKeyboardBuilder()
    if is_available:
        builder.button(text="⚡️ Hoziroq olish", callback_data=f"buy_{product_id}")
        builder.button(text="🛒 Savatchaga", callback_data=f"add_{product_id}")
    else:
        builder.button(text="🔴 TUGAGAN (Sotuvda yo'q)", callback_data="ignore")
    builder.button(text="🔙 Orqaga", callback_data=f"backtoprods_{category_id}")
    builder.adjust(2, 1) if is_available else builder.adjust(1, 1)
    return builder.as_markup()

def get_cart_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Rasmiylashtirish", callback_data="checkout_cart")
    builder.button(text="🗑 Savatchani tozalash", callback_data="clear_cart")
    builder.adjust(1)
    return builder.as_markup()