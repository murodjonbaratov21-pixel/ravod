import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import BaseMiddleware
import config
import database
import keyboards
from admin import admin_router
from maintenance import maintenance_router

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(maintenance_router)


# ================= QOROVUL (MIDDLEWARE) =================
class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        # Admin bo'lsa, eshik doim ochiq
        if str(user_id) == str(config.ADMIN_ID):
            return await handler(event, data)

        # Mijoz bo'lsa va bot yangilanayotgan bo'lsa, bloklaymiz
        if database.get_maintenance() == '1':
            if isinstance(event, types.Message):
                await event.answer("🛠 <b>Bot hozir yangilanmoqda.</b> Iltimos, kuting...", parse_mode="HTML")
            elif isinstance(event, types.CallbackQuery):
                await event.answer("🛠 Texnik ishlar ketyapti...", show_alert=True)
            return  # Kod pastga o'tib ketmaydi, shu yerda to'xtaydi

        # Hamma narsa joyida bo'lsa, ruxsat beramiz
        return await handler(event, data)


dp.message.middleware(MaintenanceMiddleware())
dp.callback_query.middleware(MaintenanceMiddleware())


# ========================================================

class FastOrder(StatesGroup):
    product_id = State()
    contact = State()


class CartOrder(StatesGroup):
    contact = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    database.add_user(message.from_user.id)  # Mijozni bazaga saqlaymiz
    await message.answer("Ravod platformasiga xush kelibsiz!", reply_markup=keyboards.get_user_kb(message.from_user.id))


@dp.message(F.text == "🔙 Bosh menyuga qaytish")
async def back_to_main(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=keyboards.get_user_kb(message.from_user.id))


@dp.message(F.text == "🔙 Orqaga", FastOrder.contact)
@dp.message(F.text == "🔙 Orqaga", CartOrder.contact)
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Buyurtma bekor qilindi.", reply_markup=keyboards.get_user_kb(message.from_user.id))


@dp.message(F.text == "🛍 Katalog")
async def show_catalog(message: types.Message):
    categories = database.get_all_categories()
    if not categories:
        await message.answer("Hozircha do'konda mahsulotlar yo'q.")
        return
    await message.answer("Bo'limni tanlang:", reply_markup=keyboards.get_categories_kb(categories))


@dp.callback_query(F.data == "back_to_cats")
async def go_back_to_cats(call: types.CallbackQuery):
    categories = database.get_all_categories()
    await call.message.delete()
    await call.message.answer("Bo'limni tanlang:", reply_markup=keyboards.get_categories_kb(categories))


@dp.callback_query(F.data.startswith("cat_"))
async def show_products_list(call: types.CallbackQuery):
    cat_id = int(call.data.split("_")[1])
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products WHERE category_id = ?", (cat_id,))
    products = cursor.fetchall()
    conn.close()
    if not products:
        await call.message.edit_text("Bu bo'limda hozircha mahsulot yo'q.")
        return
    await call.message.edit_text("Kerakli mahsulotni tanlang:", reply_markup=keyboards.get_products_list_kb(products))


@dp.callback_query(F.data.startswith("prod_"))
async def show_one_product(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, price, photo_id, is_available FROM products WHERE id = ?", (prod_id,))
    prod = cursor.fetchone()
    conn.close()

    status_text = "🟢 Sotuvda bor" if prod[4] else "🔴 Qolmagan (Vaqtinchalik yo'q)"
    caption = f"🏷 <b>Mahsulot:</b> {prod[0]}\n\n📋 <b>Tavsif:</b> {prod[1]}\n\n💵 <b>Narxi:</b> {prod[2]} so'm\n\n📌 <b>Holati:</b> {status_text}"

    await call.message.delete()
    await call.message.answer_photo(photo=prod[3], caption=caption, parse_mode="HTML",
                                    reply_markup=keyboards.get_product_actions_kb(prod_id, prod[4]))


@dp.callback_query(F.data == "ignore")
async def ignore_action(call: types.CallbackQuery):
    await call.answer("❌ Bu mahsulot vaqtinchalik sotuvda yo'q, xarid qila olmaysiz!", show_alert=True)


@dp.callback_query(F.data.startswith("add_"))
async def add_cart(call: types.CallbackQuery):
    prod_id = int(call.data.split("_")[1])
    database.add_to_cart(call.from_user.id, prod_id)
    await call.answer("✅ Mahsulot savatchaga qo'shildi!", show_alert=True)


@dp.message(F.text == "🛒 Savatcha")
async def view_cart(message: types.Message):
    items = database.get_cart(message.from_user.id)
    if not items:
        await message.answer("Savatchangiz hozircha bo'm-bo'sh 😔")
        return
    text = "🛒 <b>Sizning savatchangiz:</b>\n\n"
    total_price = 0
    for i, item in enumerate(items, 1):
        text += f"{i}. {item[0]} — {item[1]} so'm\n"
        total_price += item[1]
    text += f"\n💵 <b>Jami to'lov: {total_price} so'm</b>"
    await message.answer(text, parse_mode="HTML", reply_markup=keyboards.get_cart_kb())


@dp.callback_query(F.data == "clear_cart")
async def clear_cart_action(call: types.CallbackQuery):
    database.clear_cart(call.from_user.id)
    await call.message.edit_text("🗑 Savatcha tozalandi.")


@dp.callback_query(F.data == "checkout_cart")
async def checkout_cart_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("📞 Buyurtmani rasmiylashtirish uchun telefon raqamingizni yuboring:",
                              reply_markup=keyboards.contact_kb)
    await state.set_state(CartOrder.contact)


@dp.message(CartOrder.contact)
async def cart_buy_finish(message: types.Message, state: FSMContext):
    contact = message.contact.phone_number if message.contact else message.text
    items = database.get_cart(message.from_user.id)
    if not items:
        await message.answer("Savatchangiz bo'sh.", reply_markup=keyboards.get_user_kb(message.from_user.id))
        await state.clear()
        return
    total_price = 0
    order_list = ""
    for i, item in enumerate(items, 1):
        order_list += f"{i}. {item[0]} — {item[1]} so'm\n"
        total_price += item[1]

    username = f"@{message.from_user.username}" if message.from_user.username else "Yashiringan"
    admin_text = f"🚨 <b>YANGI ZAKAZ (Savatchadan)!</b>\n\n👤 <b>Xaridor:</b> {message.from_user.first_name}\n📞 <b>Raqami:</b> {contact}\n🔗 <b>Profili:</b> {username}\n\n📦 <b>Mahsulotlar:</b>\n{order_list}\n💵 <b>Jami to'lov:</b> {total_price} so'm"

    await bot.send_message(config.ADMIN_ID, admin_text, parse_mode="HTML")
    database.clear_cart(message.from_user.id)
    await state.clear()
    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada adminlarimiz siz bilan bog'lanadi.",
                         reply_markup=keyboards.get_user_kb(message.from_user.id))


@dp.callback_query(F.data.startswith("buy_"))
async def fast_buy_start(call: types.CallbackQuery, state: FSMContext):
    prod_id = int(call.data.split("_")[1])
    await state.update_data(product_id=prod_id)
    await call.message.delete()
    await call.message.answer("📞 Buyurtmani rasmiylashtirish uchun telefon raqamingizni yuboring:",
                              reply_markup=keyboards.contact_kb)
    await state.set_state(FastOrder.contact)


@dp.message(FastOrder.contact)
async def fast_buy_finish(message: types.Message, state: FSMContext):
    contact = message.contact.phone_number if message.contact else message.text
    data = await state.get_data()
    prod_id = data['product_id']

    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM products WHERE id = ?", (prod_id,))
    prod = cursor.fetchone()
    conn.close()

    username = f"@{message.from_user.username}" if message.from_user.username else "Yashiringan"
    admin_text = f"🚨 <b>YANGI ZAKAZ (Tezkor)!</b>\n\n👤 <b>Xaridor:</b> {message.from_user.first_name}\n📞 <b>Raqami:</b> {contact}\n🔗 <b>Profili:</b> {username}\n\n📦 <b>Mahsulot:</b> {prod[0]}\n💵 <b>Narxi:</b> {prod[1]} so'm"

    # Barcha adminlarga xabar jo'natish
    for admin in config.ADMIN_IDS:
        try:
            await bot.send_message(admin, admin_text, parse_mode="HTML")
        except:
            pass
    await state.clear()
    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada adminlarimiz siz bilan bog'lanadi.",
                         reply_markup=keyboards.get_user_kb(message.from_user.id))


async def main():
    database.create_tables()
    print("🚀 Ravod yangilash tizimi bilan ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())