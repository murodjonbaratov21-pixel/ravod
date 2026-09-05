from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database
import admin_kb as keyboards
admin_router = Router()


class AddAdminState(StatesGroup):
    role = State()
    new_admin_id = State()
    password = State()


class VersionManage(StatesGroup):
    custom_version = State()
    features = State()
    target = State()


# ================= ASOSIY BOSHQARUV =================
@admin_router.message(F.text == "🔙 Orqaga")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Jarayon bekor qilindi. Boshqaruv paneli:",
                         reply_markup=keyboards.get_admin_kb(message.from_user.id))


@admin_router.message(F.text == "⚙️ Admin panel")
async def admin_panel(message: types.Message):
    if database.is_admin(message.from_user.id):
        await message.answer("Boshqaruv paneli", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= SUPER ADMIN BOSHQARUVI =================
@admin_router.message(F.text == "👤 Admin qo'shish")
async def add_admin_btn(message: types.Message, state: FSMContext):
    import config
    if str(message.from_user.id) != str(config.ADMIN_ID): return
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
    try:
        await message.delete()
    except:
        pass

    if message.text != config.MASTER_PASSWORD:
        await message.answer("❌ <b>XAVFSIZLIK XATOSI!</b> Noto'g'ri parol kiritildi. Amaliyot bekor qilindi.",
                             parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))
        await state.clear()
        return

    data = await state.get_data()
    new_id = data['new_admin_id']
    role = data['role']
    database.add_admin(new_id, role)
    role_names = {"boss": "Boshliq", "manager": "Menejer", "operator": "Operator"}
    role_uz = role_names.get(role, "Admin")

    await message.answer(
        f"✅ <b>Xavfsizlik tekshiruvidan muvaffaqiyatli o'tdi!</b>\n\nID: {new_id} endi {role_uz} lavozimida.",
        parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))

    welcome_text = f"🎉 <b>Tabriklaymiz!</b>\n\nHurmatli hamkasb, sizni <b>Ravod boshlig'i</b> do'konga <b>{role_uz}</b> qilib tayinladi! 🤝\n\nTizimga kirish uchun /start tugmasini bosing."
    try:
        await bot.send_message(new_id, welcome_text, parse_mode="HTML")
    except:
        await message.answer(
            "⚠️ Tizimga qo'shildi, lekin adminga xabar borolmadi (u avval botga /start bosmagan bo'lishi mumkin).")
    await state.clear()


# ================= VERSIYA BOSHQARUVI (PRO) =================
@admin_router.message(F.text == "📈 Versiya boshqaruvi")
async def version_menu(message: types.Message):
    if not database.is_admin(message.from_user.id): return
    maint = database.get_setting("maintenance")
    if maint == '1':
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="✅ Yangilashni yakunlash", callback_data="finish_update")]])
        await message.answer(
            "⚠️ <b>Bot hozir YANGILANISH rejimida (Qulflangan).</b>\n\nKodingizni serverga yuklab bo'lgan bo'lsangiz, yangilashni yakunlang:",
            parse_mode="HTML", reply_markup=kb)
        return

    next_v = database.get_setting("next_version")
    if next_v:
        features = database.get_setting("next_features")
        target = database.get_setting("target_users")
        text = (
            f"⏳ <b>Sizda rejalashtirilgan yangilanish bor:</b>\n\n"
            f"🔹 <b>Versiya:</b> {next_v}\n"
            f"🔹 <b>Matn:</b>\n{features}\n"
            f"🔹 <b>Maqsad:</b> {target} ta foydalanuvchi\n\n"
            f"Shuni o'zgartiramizmi?"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ O'zgartirish (Boshqadan yozish)", callback_data="setver_edit")],
            [InlineKeyboardButton(text="🗑 Rejani bekor qilish", callback_data="setver_cancel")]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=kb)
        return

    curr_v = database.get_setting("current_version")
    try:
        parts = curr_v.split('.')
        next_v_suggest = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
    except:
        next_v_suggest = "1.0.1"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Ha, {next_v_suggest}", callback_data=f"setver_{next_v_suggest}")],
        [InlineKeyboardButton(text="✍️ O'zim kiritaman", callback_data="setver_custom")]
    ])
    await message.answer(
        f"📈 <b>Versiya boshqaruvi</b>\n\nHozirgi versiya: {curr_v}\nKeyingi versiyani {next_v_suggest} qilamizmi?",
        parse_mode="HTML", reply_markup=kb)


@admin_router.callback_query(F.data == "setver_edit")
async def edit_planned_version(call: types.CallbackQuery, state: FSMContext):
    curr_v = database.get_setting("current_version")
    try:
        parts = curr_v.split('.')
        next_v_suggest = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
    except:
        next_v_suggest = "1.0.1"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Ha, {next_v_suggest}", callback_data=f"setver_{next_v_suggest}")],
        [InlineKeyboardButton(text="✍️ O'zim kiritaman", callback_data="setver_custom")]
    ])
    await call.message.edit_text(
        f"📈 <b>Versiyani o'zgartirish</b>\n\nHozirgi versiya: {curr_v}\nKeyingi versiyani {next_v_suggest} qilamizmi?",
        parse_mode="HTML", reply_markup=kb)


@admin_router.callback_query(F.data == "setver_cancel")
async def cancel_planned_version(call: types.CallbackQuery):
    database.set_setting("next_version", "")
    database.set_setting("next_features", "")
    database.set_setting("target_users", "0")
    await call.message.edit_text(
        "🗑 <b>Rejalashtirilgan yangilanish bekor qilindi!</b>\n\nEndi mijozlarga kutilayotgan yangilanish ('Kutilmoqda...') bo'lib ko'rinadi.",
        parse_mode="HTML")


@admin_router.callback_query(F.data.startswith("setver_"))
async def setver_start(call: types.CallbackQuery, state: FSMContext):
    val = call.data.split("_")[1]
    if val == "edit" or val == "cancel": return

    if val == "custom":
        await call.message.edit_text("Yangi versiya raqamini yozing (Masalan: 1.1.0):")
        await state.set_state(VersionManage.custom_version)
    else:
        await state.update_data(next_ver=val)
        await call.message.edit_text(
            f"Keyingi versiya: {val}\n\nQanday yangi funksiyalar qo'shiladi? E'lon matnini kiriting:")
        await state.set_state(VersionManage.features)


@admin_router.message(VersionManage.custom_version)
async def setver_custom_step(message: types.Message, state: FSMContext):
    await state.update_data(next_ver=message.text)
    await message.answer("Qanday yangi funksiyalar qo'shiladi? E'lon matnini kiriting:",
                         reply_markup=keyboards.cancel_kb)
    await state.set_state(VersionManage.features)


@admin_router.message(VersionManage.features)
async def setver_features_step(message: types.Message, state: FSMContext):
    await state.update_data(features=message.text)
    await message.answer(
        "Do'konda foydalanuvchilar soni nechtaga yetganda bu yangilanishni e'lon qilamiz? (Faqat raqam kiriting, masalan: 100):",
        reply_markup=keyboards.cancel_kb)
    await state.set_state(VersionManage.target)


@admin_router.message(VersionManage.target)
async def setver_target_step(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting!")
        return
    data = await state.get_data()
    database.set_setting("next_version", data['next_ver'])
    database.set_setting("next_features", data['features'])
    database.set_setting("target_users", message.text)
    await state.clear()
    await message.answer(
        "✅ <b>Yangi versiya rejasi saqlandi!</b>\n\nEndi oddiy xaridorlar 'ℹ️ Bot haqida' bo'limida buni kutilayotganini ko'rishadi.",
        parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= QULFLASH VA OCHISH =================
@admin_router.callback_query(F.data == "announce_update")
async def do_announce(call: types.CallbackQuery, bot: Bot):
    database.set_setting("maintenance", "1")
    users = database.get_all_users()
    import config
    for u in users:
        if str(u[0]) == str(config.ADMIN_ID): continue
        try:
            await bot.send_message(u[0],
                                   "🔔 <b>Diqqat! Bugun botda yangilanish kuni!</b>\n\nBiz va'da qilingan marraga yetdik. Hozircha bot ishlamay turishi mumkin, tez orada yangi versiya bilan qaytamiz!",
                                   parse_mode="HTML")
        except:
            pass
    await call.message.edit_text(
        "✅ <b>Yangilanish e'lon qilindi va bot qulflandi!</b>\n\nEndi serverda bemalol kodingizni almashtiring. Ish bitgach '📈 Versiya boshqaruvi' ga kirib yakunlaysiz.",
        parse_mode="HTML")


@admin_router.callback_query(F.data == "finish_update")
async def do_finish(call: types.CallbackQuery, bot: Bot):
    next_v = database.get_setting("next_version")
    if next_v: database.set_setting("current_version", next_v)
    import datetime
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    database.set_setting("last_update_date", today)
    database.set_setting("next_version", "")
    database.set_setting("next_features", "")
    database.set_setting("target_users", "0")
    database.set_setting("maintenance", "0")

    curr_v = database.get_setting("current_version")
    users = database.get_all_users()
    import config
    for u in users:
        if str(u[0]) == str(config.ADMIN_ID): continue
        try:
            await bot.send_message(u[0],
                                   f"🚀 <b>Bot yangilandi!</b>\n\nYangi versiya: {curr_v}. Kiring va xaridni davom ettiring!",
                                   parse_mode="HTML")
        except:
            pass
    await call.message.edit_text(
        "✅ <b>Yangilash muvaffaqiyatli yakunlandi!</b>\nBot blokdan yechildi va hammaga xabar ketdi.",
        parse_mode="HTML")