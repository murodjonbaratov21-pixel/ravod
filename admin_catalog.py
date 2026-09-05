from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database
import admin_kb as keyboards
admin_catalog_router = Router()

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

# ================= QO'SHISH =================
@admin_catalog_router.message(F.text == "📂 Kat. qo'shish")
async def add_cat_start(message: types.Message, state: FSMContext):
    if database.is_admin(message.from_user.id):
        await message.answer("Kategoriya nomini kiriting:", reply_markup=keyboards.cancel_kb)
        await state.set_state(AddCategory.name)

@admin_catalog_router.message(AddCategory.name)
async def add_cat_name(message: types.Message, state: FSMContext):
    database.add_category(message.text)
    await state.clear()
    await message.answer(f"✅ '{message.text}' qo'shildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

@admin_catalog_router.message(F.text == "📦 Mahsulot qo'shish")
async def add_product_start(message: types.Message, state: FSMContext):
    if database.is_admin(message.from_user.id):
        categories = database.get_all_categories()
        if not categories:
            await message.answer("❌ Hali bo'lim yo'q!", reply_markup=keyboards.get_admin_kb(message.from_user.id))
            return
        await message.answer("Qaysi bo'limga qo'shamiz?", reply_markup=keyboards.get_manage_cats_list_kb(categories, "admincat_"))
        await state.set_state(AddProduct.category_id)

@admin_catalog_router.callback_query(AddProduct.category_id, F.data.startswith("admincat_"))
async def add_product_category(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split("_")[1])
    await state.update_data(category_id=cat_id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Mahsulot nomini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.name)

@admin_catalog_router.message(AddProduct.name)
async def add_product_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Endi mahsulot haqida to'liq ma'lumot (tavsif) yozing:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.description)

@admin_catalog_router.message(AddProduct.description)
async def add_product_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Narxni faqat raqamlarda kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.price)

@admin_catalog_router.message(AddProduct.price)
async def add_product_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam yozing:")
        return
    await state.update_data(price=message.text)
    await message.answer("Endi rasmini yuboring:", reply_markup=keyboards.cancel_kb)
    await state.set_state(AddProduct.photo)

@admin_catalog_router.message(AddProduct.photo, F.photo)
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
@admin_catalog_router.message(F.text == "🛠 Kategoriya boshqaruvi")
async def manage_cat_start(message: types.Message):
    if database.is_admin(message.from_user.id):
        categories = database.get_all_categories()
        if not categories:
            await message.answer("❌ Kategoriya yo'q!")
            return
        await message.answer("Tahrirlash yoki o'chirish uchun kategoriyani tanlang:", reply_markup=keyboards.get_manage_cats_list_kb(categories, "mngcat_"))

@admin_catalog_router.callback_query(F.data.startswith("mngcat_"))
async def manage_cat_action(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    await call.message.edit_text("Nima quramiz?", reply_markup=keyboards.get_admin_category_actions_kb(cat_id))

@admin_catalog_router.callback_query(F.data.startswith("delcat_"))
async def delete_cat_action(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    database.delete_category(cat_id)
    await call.message.delete()
    await call.answer("Bo'lim o'chirildi!", show_alert=True)

@admin_catalog_router.callback_query(F.data.startswith("editcname_"))
async def edit_cat_name_start(call: types.CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split("_")[1])
    await state.update_data(cat_id=cat_id)
    await call.message.delete()
    await call.message.answer("Kategoriyaning yangi nomini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditCatName.new_name)

@admin_catalog_router.message(EditCatName.new_name)
async def edit_cat_name_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.update_category_name(data['cat_id'], message.text)
    await state.clear()
    await message.answer("✅ Kategoriya nomi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

# ================= MAHSULOT BOSHQARUVI =================
@admin_catalog_router.message(F.text == "⚙️ Mahsulot boshqaruvi")
async def manage_prod_start(message: types.Message):
    if database.is_admin(message.from_user.id):
        categories = database.get_all_categories()
        if not categories:
            await message.answer("❌ Kategoriya yo'q!")
            return
        await message.answer("Qaysi bo'limdagi mahsulotni ko'ramiz?", reply_markup=keyboards.get_manage_cats_list_kb(categories, "mngprodcat_"))

@admin_catalog_router.callback_query(F.data.startswith("mngprodcat_"))
async def manage_prod_list(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    products = database.get_products_by_category(cat_id)
    if not products:
        await call.answer("Bu bo'limda mahsulot yo'q!", show_alert=True)
        return
    await call.message.edit_text("Tahrirlash yoki o'chirish uchun mahsulotni tanlang:", reply_markup=keyboards.get_manage_products_list_kb(products))

@admin_catalog_router.callback_query(F.data.startswith("mngprod_"))
async def manage_prod_action(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name, is_available, category_id FROM products WHERE id = ?", (prod_id,))
    prod = cursor.fetchone()
    conn.close()
    status_icon = "🟢 Sotuvda bor" if prod[1] else "🔴 Qolmagan"
    await call.message.edit_text(f"📦 <b>Mahsulot:</b> {prod[0]}\n📌 <b>Holati:</b> {status_icon}\n\nNimasini o'zgartiramiz?", parse_mode="HTML", reply_markup=keyboards.get_admin_product_actions_kb(prod_id, prod[1], prod[2]))

@admin_catalog_router.callback_query(F.data.startswith("toggle_"))
async def toggle_prod_action(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    database.toggle_product_availability(prod_id)
    await call.answer("Holat o'zgardi!", show_alert=True)
    await call.message.delete()

@admin_catalog_router.callback_query(F.data.startswith("delprod_"))
async def delete_prod_action(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id FROM products WHERE id = ?", (prod_id,))
    cat_row = cursor.fetchone()
    database.delete_product(prod_id)
    await call.message.delete()
    await call.answer("Mahsulot o'chirildi!", show_alert=True)
    if cat_row:
        cat_id = cat_row[0]
        products = database.get_products_by_category(cat_id)
        if products:
            await call.message.answer("Qolgan mahsulotlarni tahrirlash:", reply_markup=keyboards.get_manage_products_list_kb(products))
        else:
            await call.message.answer("Bu bo'limda boshqa mahsulot qolmadi.")

@admin_catalog_router.callback_query(F.data.startswith("editpname_"))
async def edit_prod_name_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(prod_id=prod_id)
    await call.message.delete()
    await call.message.answer("Mahsulotning yangi nomini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditProdName.new_name)

@admin_catalog_router.message(EditProdName.new_name)
async def edit_prod_name_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.update_product_name(data['prod_id'], message.text)
    await state.clear()
    await message.answer("✅ Mahsulot nomi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

@admin_catalog_router.callback_query(F.data.startswith("editpdesc_"))
async def edit_prod_desc_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(prod_id=prod_id)
    await call.message.delete()
    await call.message.answer("Mahsulotning yangi tavsifini kiriting:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditProdDesc.new_desc)

@admin_catalog_router.message(EditProdDesc.new_desc)
async def edit_prod_desc_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    database.update_product_desc(data['prod_id'], message.text)
    await state.clear()
    await message.answer("✅ Mahsulot tavsifi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))

@admin_catalog_router.callback_query(F.data.startswith("editpphoto_"))
async def edit_prod_photo_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(prod_id=prod_id)
    await call.message.delete()
    await call.message.answer("Mahsulotning yangi rasmini yuboring:", reply_markup=keyboards.cancel_kb)
    await state.set_state(EditProdPhoto.new_photo)

@admin_catalog_router.message(EditProdPhoto.new_photo, F.photo)
async def edit_prod_photo_finish(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()
    database.update_product_photo(data['prod_id'], photo_id)
    await state.clear()
    await message.answer("✅ Mahsulot rasmi o'zgartirildi!", reply_markup=keyboards.get_admin_kb(message.from_user.id))