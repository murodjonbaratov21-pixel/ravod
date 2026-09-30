import datetime
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
import config
import admin_kb as keyboards

admin_router = Router()


# ================= FSM HOLATLARI =================
class AddAdminState(StatesGroup):
    role = State()
    new_admin_id = State()
    password = State()


class VersionManage(StatesGroup):
    custom_version = State()
    features = State()
    target = State()


class PolicyEdit(StatesGroup):
    new_text = State()


class BroadcastState(StatesGroup):
    target = State()  # 'all' yoki 'one'
    user_identity = State()  # @username yoki ID
    target_user_id = State()  # Aniqlangan ID
    msg_type = State()  # 'plain' yoki 'button'
    content = State()  # Xabar matni
    button_count = State()  # Tugmalar soni
    button_links = State()  # Tugmalar ro'yxati


# ================= YORDAMCHI TUGMALAR (INLINE) =================
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
    await state.update_data(new_admin_id=message.text.strip())
    await message.answer("🔒 <b>Xavfsizlik tizimi:</b>\n\nIltimos, tasdiqlash uchun Maxfiy Parolni kiriting:",
                         parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddAdminState.password)


@admin_router.message(AddAdminState.password)
async def verify_admin_password(message: types.Message, state: FSMContext, bot: Bot):
    try:
        await message.delete()
    except Exception:
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
    except Exception:
        await message.answer(
            "⚠️ Tizimga qo'shildi, lekin adminga xabar borolmadi (u avval botga /start bosmagan bo'lishi mumkin).")

    await state.clear()


# ================= VERSIYA BOSHQARUVI =================
@admin_router.message(F.text == "📈 Versiya boshqaruvi")
async def version_menu(message: types.Message):
    if not database.is_admin(message.from_user.id):
        return

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
    except Exception:
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
    except Exception:
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
    if val in ["edit", "cancel"]:
        return

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
    await state.update_data(next_ver=message.text.strip())
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
    database.set_setting("target_users", message.text.strip())
    await state.clear()
    await message.answer(
        "✅ <b>Yangi versiya rejasi saqlandi!</b>\n\nEndi oddiy xaridorlar 'ℹ️ Bot haqida' bo'limida buni kutilayotganini ko'rishadi.",
        parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= QULFLASH VA OCHISH =================
@admin_router.callback_query(F.data == "announce_update")
async def do_announce(call: types.CallbackQuery, bot: Bot):
    database.set_setting("maintenance", "1")
    users = database.get_all_users()
    for u in users:
        if str(u[0]) == str(config.ADMIN_ID):
            continue
        try:
            await bot.send_message(u[0],
                                   "🔔 <b>Diqqat! Bugun botda yangilanish kuni!</b>\n\nBiz va'da qilingan marraga yetdik. Hozircha bot ishlamay turishi mumkin, tez orada yangi versiya bilan qaytamiz!",
                                   parse_mode="HTML")
        except Exception:
            pass
    await call.message.edit_text(
        "✅ <b>Yangilanish e'lon qilindi va bot qulflandi!</b>\n\nEndi serverda bemalol kodingizni almashtiring. Ish bitgach '📈 Versiya boshqaruvi' ga kirib yakunlaysiz.",
        parse_mode="HTML")


@admin_router.callback_query(F.data == "finish_update")
async def do_finish(call: types.CallbackQuery, bot: Bot):
    next_v = database.get_setting("next_version")
    if next_v:
        database.set_setting("current_version", next_v)

    today = datetime.datetime.now().strftime("%Y-%m-%d")
    database.set_setting("last_update_date", today)
    database.set_setting("next_version", "")
    database.set_setting("next_features", "")
    database.set_setting("target_users", "0")
    database.set_setting("maintenance", "0")

    curr_v = database.get_setting("current_version")
    users = database.get_all_users()
    for u in users:
        if str(u[0]) == str(config.ADMIN_ID):
            continue
        try:
            await bot.send_message(u[0],
                                   f"🚀 <b>Bot yangilandi!</b>\n\nYangi versiya: {curr_v}. Kiring va xaridni davom ettiring!",
                                   parse_mode="HTML")
        except Exception:
            pass
    await call.message.edit_text(
        "✅ <b>Yangilash muvaffaqiyatli yakunlandi!</b>\nBot blokdan yechildi va hammaga xabar ketdi.",
        parse_mode="HTML")


# ================= CHEK / QOIDA MATNINI TAHRIRLASH =================
@admin_router.message(F.text.startswith("/qoida"))
async def update_policy_cmd(message: types.Message):
    if database.is_admin(message.from_user.id):
        new_policy = message.text.replace("/qoida", "", 1).strip()
        if not new_policy:
            await message.answer("⚠️ Qoida matnini /qoida dan keyin yozing!")
            return
        with open('/root/ravod/policy.txt', 'w', encoding='utf-8') as f:
            f.write(new_policy)
        await message.answer(f"✅ Qoidalar matni muvaffaqiyatli o'zgartirildi!\n\nYangi matn:\n{new_policy}")


@admin_router.message(F.text == "📝 Chekni o'zgartirish")
async def edit_policy_start(message: types.Message, state: FSMContext):
    if not database.is_admin(message.from_user.id):
        return
    try:
        with open('/root/ravod/policy.txt', 'r', encoding='utf-8') as f:
            current_text = f.read()
    except Exception:
        current_text = "Hozircha matn o'rnatilmagan."

    await message.answer(f"📄 <b>ESKI CHEK MATNI:</b>\n\n{current_text}\n\n✍️ <b>Endi yangi chek matnini kiriting:</b>",
                         parse_mode="HTML", reply_markup=keyboards.cancel_kb)
    await state.set_state(PolicyEdit.new_text)


@admin_router.message(PolicyEdit.new_text)
async def edit_policy_finish(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=keyboards.get_admin_kb(message.from_user.id))
        return

    with open('/root/ravod/policy.txt', 'w', encoding='utf-8') as f:
        f.write(message.text)

    await state.clear()
    await message.answer("✅ Chek matni muvaffaqiyatli yangilandi!",
                         reply_markup=keyboards.get_admin_kb(message.from_user.id))


# ================= STATISTIKA =================
@admin_router.message(F.text == "📊 Statistika")
async def show_statistics(message: types.Message):
    if not database.is_admin(message.from_user.id):
        return

    users = database.get_all_users()
    cats = database.get_all_categories()

    conn = database.db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM products")
    products_count = cursor.fetchone()[0]
    conn.close()

    text = (
        f"📊 <b>RAVOD do'koni statistikasi:</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {len(users)} ta\n"
        f"📂 <b>Kategoriyalar soni:</b> {len(cats)} ta\n"
        f"📦 <b>Jami mahsulotlar:</b> {products_count} ta\n"
    )
    await message.answer(text, parse_mode="HTML")


# ================= AQLI VA SHAKLLANTIRILGAN RASSILKA =================
@admin_router.message(F.text == "✉️ Xabar yuborish")
async def start_broadcast(message: types.Message, state: FSMContext):
    if not database.is_admin(message.from_user.id):
        return
    await message.answer("🎯 <b>Xabarni kimga yubormoqchisiz?</b>", parse_mode="HTML",
                         reply_markup=get_broadcast_target_kb())


@admin_router.callback_query(F.data.startswith("target_"))
async def process_target_choice(call: types.CallbackQuery, state: FSMContext):
    choice = call.data.split("_")[1]
    await state.update_data(target=choice)

    if choice == "one":
        await call.message.edit_text("👤 Foydalanuvchining <b>@username</b> manzilini yoki <b>ID raqamini</b> yuboring:",
                                     parse_mode="HTML")
        await state.set_state(BroadcastState.user_identity)
    else:
        await call.message.edit_text("📝 <b>Xabar turini tanlang:</b>", parse_mode="HTML",
                                     reply_markup=get_broadcast_type_kb())
        await state.set_state(BroadcastState.msg_type)


@admin_router.message(BroadcastState.user_identity)
async def process_user_identity(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    target_id = None

    if user_input.startswith("@"):
        uname = user_input.replace("@", "").lower()
        conn = database.db_connect()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM users WHERE LOWER(username) = ?", (uname,))
            row = cursor.fetchone()
            if row:
                target_id = row[0]
        except Exception:
            pass
        conn.close()

        if not target_id:
            await message.answer(
                "❌ Bu username bazadan topilmadi. Qaytadan yozing yoki Telegram ID raqamini kiritib ko'ring:")
            return
    elif user_input.isdigit():
        target_id = int(user_input)
    else:
        await message.answer("❌ Noto'g'ri format! @username yoki faqat ID raqam yuboring:")
        return

    await state.update_data(target_user_id=target_id)
    await message.answer("📝 <b>Xabar turini tanlang:</b>", parse_mode="HTML", reply_markup=get_broadcast_type_kb())
    await state.set_state(BroadcastState.msg_type)


@admin_router.callback_query(F.data.startswith("msgtype_"))
async def process_msg_type(call: types.CallbackQuery, state: FSMContext):
    msg_type = call.data.split("_")[1]
    await state.update_data(msg_type=msg_type)
    await call.message.edit_text("💬 Yuboriladigan <b>xabar matnini</b> kiriting:", parse_mode="HTML")
    await state.set_state(BroadcastState.content)


@admin_router.message(BroadcastState.content)
async def process_broadcast_content(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(content_text=message.text)
    data = await state.get_data()

    if data.get("msg_type") == "button":
        await message.answer(
            "🔗 Xabarga <b>nechta havola (tugma)</b> qo'shmoqchisiz? (Raqam yozing, masalan: 1 yoki 2):",
            parse_mode="HTML")
        await state.set_state(BroadcastState.button_count)
    else:
        await send_final_broadcast(message, state, bot)


@admin_router.message(BroadcastState.button_count)
async def process_button_count(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting (masalan: 1):")
        return
    count = int(message.text)
    await state.update_data(btn_count=count, current_btn=1, links_list=[])
    await message.answer(
        "1-tugma uchun ma'lumotni quyidagi formatda yuboring:\n\n<code>Tugma nomi - https://manzil.com</code>",
        parse_mode="HTML")
    await state.set_state(BroadcastState.button_links)


@admin_router.message(BroadcastState.button_links)
async def process_button_links(message: types.Message, state: FSMContext, bot: Bot):
    if " - " not in message.text:
        await message.answer("❌ Noto'g'ri format! Namuna kabi yuboring:\n<code>Tugma nomi - https://manzil.com</code>",
                             parse_mode="HTML")
        return

    parts = message.text.split(" - ", 1)
    btn_name = parts[0].strip()
    btn_url = parts[1].strip()

    data = await state.get_data()
    links_list = data.get("links_list", [])
    links_list.append((btn_name, btn_url))

    curr = data.get("current_btn", 1)
    total = data.get("btn_count", 1)

    if curr < total:
        curr += 1
        await state.update_data(links_list=links_list, current_btn=curr)
        await message.answer(f"{curr}-tugma uchun ma'lumotni yuboring:\n<code>Tugma nomi - https://manzil.com</code>",
                             parse_mode="HTML")
    else:
        await state.update_data(links_list=links_list)
        await send_final_broadcast(message, state, bot)


async def send_final_broadcast(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = data.get("content_text")
    target = data.get("target")
    links_list = data.get("links_list", [])

    reply_markup = None
    if links_list:
        builder = InlineKeyboardBuilder()
        for name, url in links_list:
            builder.button(text=name, url=url)
        builder.adjust(1)
        reply_markup = builder.as_markup()

    sent_count = 0
    if target == "all":
        users = database.get_all_users()
        await message.answer("⏳ <i>Xabar barcha foydalanuvchilarga yuborilmoqda...</i>", parse_mode="HTML")
        for u in users:
            try:
                await bot.send_message(u[0], text, parse_mode="HTML", reply_markup=reply_markup)
                sent_count += 1
            except Exception:
                pass
        await message.answer(f"✅ Xabar barcha <b>{sent_count} ta</b> foydalanuvchiga muvaffaqiyatli yetkazildi!",
                             parse_mode="HTML", reply_markup=keyboards.get_admin_kb(message.from_user.id))
    else:
        target_user_id = data.get("target_user_id")
        try:
            await bot.send_message(target_user_id, text, parse_mode="HTML", reply_markup=reply_markup)
            await message.answer("✅ Xabar foydalanuvchiga muvaffaqiyatli yetkazildi!", parse_mode="HTML",
                                 reply_markup=keyboards.get_admin_kb(message.from_user.id))
        except Exception as e:
            await message.answer(f"❌ Xabarni yuborib bo'lmadi. Xatolik: {e}",
                                 reply_markup=keyboards.get_admin_kb(message.from_user.id))

    await state.clear()