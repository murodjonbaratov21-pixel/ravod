import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import BaseMiddleware
from admin_catalog import admin_catalog_router
import config
import database
import client_kb as keyboards
from admin import admin_router
from maintenance import maintenance_router
# YANGI QO'SHILDI:
from client import client_router

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# ROUTERLARNI ULASH:
dp.include_router(client_router)
dp.include_router(admin_router)
dp.include_router(admin_catalog_router)
dp.include_router(maintenance_router)


# ================= ADMIN TEKSHIRUVI =================
def is_any_admin(user_id):
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return False
    return user_id in database.get_all_admins()


# ================= QOROVUL (MIDDLEWARE) =================
class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        # Admin bo'lsa, eshik doim ochiq
        if is_any_admin(user_id):
            return await handler(event, data)

        # Mijoz bo'lsa va bot qulflangan bo'lsa
        if database.get_maintenance() == "1":
            if isinstance(event, types.Message):
                await event.answer("🛠 <b>Bot hozir yangilanmoqda.</b>\n\nIltimos, biroz kuting...", parse_mode="HTML")
            elif isinstance(event, types.CallbackQuery):
                await event.answer("🛠 Texnik ishlar ketyapti...", show_alert=True)
            return

        return await handler(event, data)


dp.message.middleware(MaintenanceMiddleware())
dp.callback_query.middleware(MaintenanceMiddleware())


# ================= START VA TRIGGER =================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (message.from_user.id,))
    exists = cursor.fetchone()
    conn.close()

    if not exists:
        database.add_user(message.from_user.id)
        # TRIGGER: Yangi odam qo'shilganda hisoblash
        try:
            users_count = len(database.get_all_users())
            target_str = database.get_setting('target_users')
            target = int(target_str) if target_str.isdigit() else 0

            if target > 0 and users_count == target:
                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📣 Yangilashni e'lon qilish", callback_data="announce_update")]])
                await bot.send_message(config.ADMIN_ID,
                                       f"🎉 <b>Boshliq! Do'konda odamlar soni {target} taga yetdi!</b>\n\nVa'da qilingan yangilanishni boshlash vaqti keldi.",
                                       parse_mode="HTML", reply_markup=kb)
        except Exception as e:
            print(f"Trigger error: {e}")

    await message.answer("Ravod platformasiga xush kelibsiz!", reply_markup=keyboards.get_user_kb(message.from_user.id))


# ================= BOT HAQIDA =================
@dp.message(F.text == "ℹ️ Bot haqida")
async def bot_info(message: types.Message):
    curr_v = database.get_setting("current_version")
    last_date = database.get_setting("last_update_date")
    next_v = database.get_setting("next_version")
    features = database.get_setting("next_features")
    target = database.get_setting("target_users")

    users_count = len(database.get_all_users())
    target_int = int(target) if target.isdigit() else 0

    text = f"🛍 <b>RAVOD — Sifatli mahsulotlar onlayn do'koni!</b>\n\n⚙️ <b>Joriy versiya:</b> {curr_v}\n📅 <b>Oxirgi yangilanish:</b> {last_date}\n\n🚀 <b>KEYINGI YANGILANISH:</b>\n"

    if next_v and target_int > 0:
        left = target_int - users_count
        if left < 0: left = 0
        text += f"🔹 <b>Versiya:</b> {next_v}\n🔹 <b>Yangi qulayliklar:</b>\n{features}\n🔹 <b>Qachon chiqadi:</b> Yana {left} ta xaridor qo'shilganda!"
    else:
        text += "🔹 <b>Versiya:</b> Kutilmoqda...\n🔹 <b>Yangi qulayliklar:</b> Kutilmoqda...\n🔹 <b>Qachon chiqadi:</b> Kutilmoqda..."

    await message.answer(text, parse_mode="HTML")


# ================= ASOSIY MENYUGA QAYTISH =================
@dp.message(F.text == "🔙 Bosh menyuga qaytish")
async def back_to_main(message: types.Message):
    await message.answer("Asosiy menyu:", reply_markup=keyboards.get_user_kb(message.from_user.id))


# ================= MAIN =================
async def main():
    database.create_tables()
    print("🚀 Ravod platformasi yengillashgan tizim bilan ishga tushdi!")
    print(f"👑 Hozirgi adminlar: {database.get_all_admins()}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())