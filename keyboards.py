from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database

remove_kb = ReplyKeyboardRemove()

def get_user_kb(telegram_id):
    kb = [[KeyboardButton(text="🛍 Katalog"), KeyboardButton(text="🛒 Savatcha")]]
    if database.is_admin(telegram_id):
        kb.append([KeyboardButton(text="⚙️ Admin panel")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, input_field_placeholder="Kerakli bo'limni tanlang...")


# Boshqa fayllar xato bermasligi uchun qolgan joylarda ham keyboards.get_admin_kb(message.from_user.id) deb chaqiriladi
def get_admin_kb(telegram_id):
    import config
    kb = [
        [KeyboardButton(text="📂 Kat. qo'shish"), KeyboardButton(text="📦 Mahsulot qo'shish")],
        [KeyboardButton(text="🛠 Kategoriya boshqaruvi"), KeyboardButton(text="⚙️ Mahsulot boshqaruvi")],
        [KeyboardButton(text="🔄 Botni yangilash")]
    ]
    # Yashirin tugma: Faqat sizning ID raqamingiz bo'lsa chiqadi!
    if str(telegram_id) == str(config.ADMIN_ID):
        kb.append([KeyboardButton(text="👤 Admin qo'shish")])

    kb.append([KeyboardButton(text="🔙 Bosh menyuga qaytish")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# Lavozim tanlash tugmalari
def get_admin_roles_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Boshliq", callback_data="role_boss")
    builder.button(text="👔 Menejer", callback_data="role_manager")
    builder.button(text="🗣 Operator", callback_data="role_operator")
    builder.adjust(1)
    return builder.as_markup()

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

def get_product_actions_kb(product_id, is_available):
    builder = InlineKeyboardBuilder()
    if is_available:
        builder.button(text="⚡️ Hoziroq olish", callback_data=f"buy_{product_id}")
        builder.button(text="🛒 Savatchaga", callback_data=f"add_{product_id}")
    else:
        builder.button(text="🔴 TUGAGAN (Sotuvda yo'q)", callback_data="ignore")
    builder.button(text="🔙 Orqaga", callback_data="back_to_cats")
    builder.adjust(2, 1) if is_available else builder.adjust(1, 1)
    return builder.as_markup()

def get_cart_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Rasmiylashtirish", callback_data="checkout_cart")
    builder.button(text="🗑 Savatchani tozalash", callback_data="clear_cart")
    builder.adjust(1)
    return builder.as_markup()

# ================= ADMIN BOSHQARUV TUGMALARI =================

def get_manage_cats_list_kb(categories, prefix):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat[1], callback_data=f"{prefix}{cat[0]}")
    builder.adjust(2)
    return builder.as_markup()

def get_admin_category_actions_kb(cat_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Nomini o'zgartirish", callback_data=f"editcname_{cat_id}")
    builder.button(text="❌ Butunlay O'chirish", callback_data=f"delcat_{cat_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_manage_products_list_kb(products):
    builder = InlineKeyboardBuilder()
    for prod in products:
        status = "🟢" if prod[2] else "🔴"
        builder.button(text=f"{status} {prod[1]}", callback_data=f"mngprod_{prod[0]}")
    builder.adjust(1)
    return builder.as_markup()

def get_admin_product_actions_kb(product_id, is_available):
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Nomini o'zgartirish", callback_data=f"editpname_{product_id}")
    builder.button(text="📋 Tavsifini o'zgartirish", callback_data=f"editpdesc_{product_id}")
    builder.button(text="🖼 Rasmini o'zgartirish", callback_data=f"editpphoto_{product_id}")
    status_text = "🟢 Sotuvda BOR qilish" if not is_available else "🛑 Sotuvda YO'Q qilish"
    builder.button(text=status_text, callback_data=f"toggle_{product_id}")
    builder.button(text="❌ Butunlay o'chirish", callback_data=f"delprod_{product_id}")
    builder.adjust(1)
    return builder.as_markup()


