from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database
import keyboards

admin_router = Router()

# ================= STATELAR =================
class AddCategory(StatesGroup):
    name = State()

class AddProduct(StatesGroup):
    category_id = State()
    name = State()
    description = State()
    price = State()
    photo = State()

class EditCatName(StatesGroup):
    cat_id = State()
    new_name = State()

class EditProdName(StatesGroup):
    prod_id = State()
    new_name = State()

class EditProdDesc(StatesGroup):
    prod_id = State()
    new_desc = State()

class EditProdPhoto(StatesGroup):
    prod_id = State()
    new_photo = State()

class AddAdminState(StatesGroup):
    role = State()
    new_admin_id = State()
    password = State()


# ================= ASOSIY BOSHQARUV =================
@admin_router.message(F.text == "🔙 Orqaga")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Jarayon bekor qilindi. Boshqaruv paneli:", reply_markup=keyboards.get_admin_kb(message.from_user.id))

@admin_router.message(F.text == "⚙️ Admin panel")
async def admin_panel(message: types.Message):
    if database.is_admin(message.from_user.id):
        await message.answer("Boshqaruv paneli", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= QO'SHISH =================
@admin_router.message(F.text == "📂 Kat. qo'shish")
async def add_cat_start(message: types.Message, state: FSMContext):
    if database.is_admin(message.from_user.id):
        await message.answer("Kategoriya nomini kiriting:", reply_markup=keyboards.cancel_kb)
        await state.set_state(AddCategory.name)

@admin_router.message(AddCategory.name)
async def add_cat_name(message: types.Message, state: FSMContext):
    database.add_category(message.text)
    await state.clear()
    await message.answer(f"✅ '{message.text}' qo'shildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

@admin_router.message(F.text == "📦 Mahsulot qo'shish")
async def add_product_start(message: types.Message, state: FSMContext):
    if database.is_admin(message.from_user.id):
        categories = database.get_all_categories()
        if not categories:
            await message.answer("❌ Hali bo'lim yo'q!", reply_markup=keyboards.get_admin_kb(message.from_user.id))
            return
        await message.answer("Qaysi bo'limga qo'shamiz?", reply_markup=keyboards.get_manage_cats_list_kb(categories, "admincat_"))
        await state.set_state(AddProduct.category_id)

@admin_router.callback_query(AddProduct.category_id, F.data.startswith("admincat_"))
async def add_product_category(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split("_")[1])
    await state.update_data(category_id=cat_id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Mahsulot nomini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.name)

@admin_router.message(AddProduct.name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Endi mahsulot haqida to'liq ma'lumot (tavsif) yozing:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.description)

@admin_router.message(AddProduct.description)
async def add_product_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Narxni faqat raqamlarda kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.price)

@admin_router.message(AddProduct.price)
async def add_product_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam yozing:")
        return
    await state.update_data(price=message.text)
    await message.answer("Endi rasmini yuboring:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.photo)

@admin_router.message(AddProduct.photo, F.photo)
async def add_product_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, description, price, photo_id, category_id) VALUES (?, ?, ?, ?, ?)",
                   (data['name'], data['description'], data['price'], photo_id, data['category_id']))
    conn.commit()
    conn.close()
    await state.clear()
    await message.answer("✅ Mahsulot qo'shildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= KATEGORIYA BOSHQARUVI =================
@admin_router.message(F.text == "🛠 Kategoriya boshqaruvi")
async def manage_cat_start(message: types.Message):
    if database.is_admin(message.from_user.id):
        categories = database.get_all_categories()
        if not categories:
            await message.answer("❌ Kategoriya yo'q!")
            return
        await message.answer("Tahrirlash yoki o'chirish uchun kategoriyani tanlang:",
                             reply_markup=keyboards.get_manage_cats_list_kb(categories, "mngcat_"))

@admin_router.callback_query(F.data.startswith("mngcat_"))
async def manage_cat_action(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    await call.message.edit_text("Nima quramiz?", reply_markup=keyboards.get_admin_category_actions_kb(cat_id))

@admin_router.callback_query(F.data.startswith("delcat_"))
async def delete_cat_action(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    database.delete_category(cat_id)
    await call.message.delete()
    await call.answer("Bo'lim o'chirildi!", show_alert=True)

@admin_router.callback_query(F.data.startswith("editcname_"))
async def edit_cat_name_start(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split("_")[1])
    await state.update_data(cat_id=cat_id)
    await call.message.delete()
    await call.message.answer("Kategoriyaning yangi nomini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditCatName.new_name)

@admin_router.message(EditCatName.new_name)
async def edit_cat_name_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.update_category_name(data['cat_id'], message.text)
    await state.clear()
    await message.answer("✅ Kategoriya nomi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= MAHSULOT BOSHQARUVI =================
@admin_router.message(F.text == "⚙️ Mahsulot boshqaruvi")
async def manage_prod_start(message: types.Message):
    if database.is_admin(message.from_user.id):
        categories = database.get_all_categories()
        if not categories:
            await message.answer("❌ Kategoriya yo'q!")
            return
        await message.answer("Qaysi bo'limdagi mahsulotni ko'ramiz?",
                             reply_markup=keyboards.get_manage_cats_list_kb(categories, "mngprodcat_"))

@admin_router.callback_query(F.data.startswith("mngprodcat_"))
async def manage_prod_list(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    products = database.get_products_by_category(cat_id)
    if not products:
        await call.answer("Bu bo'limda mahsulot yo'q!", show_alert=True)
        return
    await call.message.edit_text("Tahrirlash yoki o'chirish uchun mahsulotni tanlang:",
                                 reply_markup=keyboards.get_manage_products_list_kb(products))

@admin_router.callback_query(F.data.startswith("mngprod_"))
async def manage_prod_action(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name, is_available FROM products WHERE id = ?", (prod_id,))
    prod = cursor.fetchone()
    conn.close()

    status_icon = "🟢 Sotuvda bor" if prod[1] else "🔴 Qolmagan"
    await call.message.edit_text(
        f"📦 <b>Mahsulot:</b> {prod[0]}\n📌 <b>Holati:</b> {status_icon}\n\nNimasini o'zgartiramiz?",
        parse_mode="HTML", reply_markup=keyboards.get_admin_product_actions_kb(prod_id, prod[1]))

@admin_router.callback_query(F.data.startswith("toggle_"))
async def toggle_prod_action(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    database.toggle_product_availability(prod_id)
    await call.answer("Holat o'zgardi!", show_alert=True)
    await call.message.delete()

@admin_router.callback_query(F.data.startswith("delprod_"))
async def delete_prod_action(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    database.delete_product(prod_id)
    await call.message.delete()
    await call.answer("Mahsulot o'chirildi!", show_alert=True)

# 📝 Mahsulot nomini o'zgartirish
@admin_router.callback_query(F.data.startswith("editpname_"))
async def edit_prod_name_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(prod_id=prod_id)
    await call.message.delete()
    await call.message.answer("Mahsulotning yangi nomini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditProdName.new_name)

@admin_router.message(EditProdName.new_name)
async def edit_prod_name_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.update_product_name(data['prod_id'], message.text)
    await state.clear()
    await message.answer("✅ Mahsulot nomi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

# 📋 Mahsulot tavsifini o'zgartirish
@admin_router.callback_query(F.data.startswith("editpdesc_"))
async def edit_prod_desc_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(prod_id=prod_id)
    await call.message.delete()
    await call.message.answer("Mahsulotning yangi tavsifini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditProdDesc.new_desc)

@admin_router.message(EditProdDesc.new_desc)
async def edit_prod_desc_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.update_product_desc(data['prod_id'], message.text)
    await state.clear()
    await message.answer("✅ Mahsulot tavsifi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

# 🖼 Mahsulot rasmini o'zgartirish
@admin_router.callback_query(F.data.startswith("editpphoto_"))
async def edit_prod_photo_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(prod_id=prod_id)
    await call.message.delete()
    await call.message.answer("Mahsulotning yangi rasmini yuboring:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditProdPhoto.new_photo)

@admin_router.message(EditProdPhoto.new_photo, F.photo)
async def edit_prod_photo_finish(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    database.update_product_photo(data['prod_id'], photo_id)
    await state.clear()
    await message.answer("✅ Mahsulot rasmi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= SUPER ADMIN BOSHQARUVI =================
@admin_router.message(F.text == "👤 Admin qo'shish")
async def add_admin_btn(message: types.Message, state: FSMContext):
    import config
    # Agar siz bo'lmasangiz, e'tibor bermaydi
    if str(message.from_user.id) != str(config.ADMIN_ID):
        return
    await message.answer("Qanday lavozimga admin qo'shmoqchisiz?", reply_markup=keyboards.get_admin_roles_kb())

@admin_router.callback_query(F.data.startswith("role_"))
async def select_admin_role(call: types.CallbackQuery, state: FSMContext):
    role = call.data.split("_")[1]
    await state.update_data(role=role)
    await call.message.edit_text("Yangi adminning Telegram ID raqamini kiriting:")
    await state.set_state(AddAdminState.new_admin_id)

@admin_router.message(AddAdminState.new_admin_id)
async def enter_new_admin_id(message: types.Message, state: FSMContext):
    await state.update_data(new_admin_id=message.text)
    await message.answer("🔒 <b>Xavfsizlik tizimi:</b>\n\nIltimos, tasdiqlash uchun Maxfiy Parolni kiriting:",
                         parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddAdminState.password)

@admin_router.message(AddAdminState.password)
async def verify_admin_password(message: types.Message, state: FSMContext, bot: Bot):
    import config

    # 1. PAROLNI EKRANDAN O'CHIRIB TASHLAYMIZ!
    try:
        await message.delete()
    except:
        pass

    # 2. Parolni tekshirish
    if message.text != config.MASTER_PASSWORD:
        await message.answer("❌ <b>XAVFSIZLIK XATOSI!</b> Noto'g'ri parol kiritildi. Amaliyot bekor qilindi.",
                             parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))
        await state.clear()
        return

    # 3. Parol to'g'ri bo'lsa
    data = await state.get_data()
    new_id = data['new_admin_id']
    role = data['role']

    database.add_admin(new_id, role)

    role_names = {"boss": "Boshliq", "manager": "Menejer", "operator": "Operator"}
    role_uz = role_names.get(role, "Admin")

    await message.answer(
        f"✅ <b>Xavfsizlik tekshiruvidan muvaffaqiyatli o'tdi!</b>\n\nID: {new_id} endi {role_uz} lavozimida.",
        parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))

    # 4. Adminga boshliq nomidan xabar yuborish
    welcome_text = (
        f"🎉 <b>Tabriklaymiz!</b>\n\n"
        f"Hurmatli hamkasb, sizni <b>Ravod boshlig'i</b> do'konga <b>{role_uz}</b> qilib tayinladi! 🤝\n\n"
        "Tizimga kirish uchun /start tugmasini bosing."
    )
    try:
        await bot.send_message(new_id, welcome_text, parse_mode="HTML")
    except:
        await message.answer("⚠️ Tizimga qo'shildi, lekin adminga xabar borolmadi (u avval botga /start bosmagan bo'lishi mumkin).")

    await state.clear()