from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ESKI admin_kb (maintenance uchun qoldirildi)
admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📂 Kat. qo'shish"), KeyboardButton(text="📦 Mahsulot qo'shish")],
    [KeyboardButton(text="🛠 Kategoriya boshqaruvi"), KeyboardButton(text="⚙️ Mahsulot boshqaruvi")],
    [KeyboardButton(text="🔄 Botni yangilash"), KeyboardButton(text="📈 Versiya boshqaruvi")],
    [KeyboardButton(text="📝 Chekni o'zgartirish")],
    [KeyboardButton(text="🔙 Bosh menyuga qaytish")]
], resize_keyboard=True)


# admin_kb.py faylidagi get_admin_kb funksiyasi:
def get_admin_kb(telegram_id):
    import config
    kb = [
        [KeyboardButton(text="📂 Kat. qo'shish"), KeyboardButton(text="📦 Mahsulot qo'shish")],
        [KeyboardButton(text="🛠 Kategoriya boshqaruvi"), KeyboardButton(text="⚙️ Mahsulot boshqaruvi")],
        # MANA SHU YERGA YANGI 2 TA TUGMA QO'SHILDI:
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="✉️ Xabar yuborish")],
        [KeyboardButton(text="🔄 Botni yangilash"), KeyboardButton(text="📈 Versiya boshqaruvi")],
        [KeyboardButton(text="📝 Chekni o'zgartirish")]
    ]

    if str(telegram_id) == str(config.ADMIN_ID):
        kb.append([KeyboardButton(text="👤 Admin qo'shish")])

    kb.append([KeyboardButton(text="🔙 Bosh menyuga qaytish")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_admin_roles_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="👑 Boshliq", callback_data="role_boss")
    builder.button(text="👔 Menejer", callback_data="role_manager")
    builder.button(text="🗣 Operator", callback_data="role_operator")
    builder.adjust(1)
    return builder.as_markup()


cancel_kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Orqaga")]], resize_keyboard=True)


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


def get_admin_product_actions_kb(product_id, is_available, category_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Nomini o'zgartirish", callback_data=f"editpname_{product_id}")
    builder.button(text="📋 Tavsifini o'zgartirish", callback_data=f"editpdesc_{product_id}")
    builder.button(text="🖼 Rasmini o'zgartirish", callback_data=f"editpphoto_{product_id}")
    status_text = "🟢 Sotuvda BOR qilish" if not is_available else "🛑 Sotuvda YO'Q qilish"
    builder.button(text=status_text, callback_data=f"toggle_{product_id}")
    builder.button(text="❌ Butunlay o'chirish", callback_data=f"delprod_{product_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"mngprodcat_{category_id}")
    builder.adjust(1)
    return builder.as_markup()

# admin_kb.py eng pastiga qo'shing:
def get_broadcast_target_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="📢 Barcha foydalanuvchilarga", callback_data="target_all")
    builder.button(text="👤 Aniq bitta foydalanuvchiga", callback_data="target_one")
    builder.adjust(1)
    return builder.as_markup()

def get_broadcast_type_kb():
    builder = InlineKeyboardBuilder()
    builder.button(text="💬 Oddiy xabar", callback_data="msgtype_plain")
    builder.button(text="🔗 Havolali (Tugmali) xabar", callback_data="msgtype_button")
    builder.adjust(1)
    return builder.as_markup()