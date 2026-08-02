from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database
import keyboards
import config

maintenance_router = Router()


class MaintState(StatesGroup):
    message = State()


@maintenance_router.message(F.text == "🔄 Botni yangilash")
async def maint_start(message: types.Message, state: FSMContext):
    if not database.is_admin(message.from_user.id): return

    status = database.get_maintenance()
    if status == '1':
        # Agar yoniq bo'lsa, o'chiramiz
        database.set_maintenance('0')
        await message.answer("✅ Bot oddiy rejimga qaytdi. Endi mijozlar bemalol kirib xarid qilishi mumkin.",
                             reply_markup=keyboards.admin_kb)
    else:
        # Agar o'chiq bo'lsa, yoqish uchun xabar so'raymiz
        await message.answer(
            "⚠️ Botni yangilash rejimiga o'tkazmoqchisiz.\n\nMijozlarga nima deb xabar yuboramiz? (Masalan: 'Botda yangilash ishlari ketyapti, 1 soatda yonadi')\n\nXabarni yozing:",
            reply_markup=keyboards.cancel_kb)
        await state.set_state(MaintState.message)


@maintenance_router.message(MaintState.message)
async def maint_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    msg_text = message.text
    database.set_maintenance('1')
    users = database.get_all_users()

    count = 0
    for u in users:
        # Adminga xabar bormasligi uchun
        if str(u[0]) == str(config.ADMIN_ID): continue
        try:
            await bot.send_message(u[0], f"🛠 <b>Texnik ishlar!</b>\n\n{msg_text}", parse_mode="HTML")
            count += 1
        except:
            pass

    await state.clear()
    await message.answer(
        f"✅ Bot bloklandi!\nOdamlar kirolmaydi. {count} ta odamga xabar bordi. Endi serverda bemalol kodni almashtiravering.",
        reply_markup=keyboards.admin_kb)