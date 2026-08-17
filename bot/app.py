from __future__ import annotations

import asyncio
import logging
import os
import time
from collections import defaultdict

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

import db

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("ravod-admin-bot")

TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Put it in bot/.env on the server.")

ADMIN_IDS = {int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS is missing.")

bot = Bot(TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Lightweight abuse protection: excessive messages from one user are ignored for a short period.
_last_seen: dict[int, float] = defaultdict(float)
RATE_WINDOW = 0.7


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def guarded(message: types.Message) -> bool:
    now = time.monotonic()
    last = _last_seen[message.from_user.id]
    if now - last < RATE_WINDOW:
        return False
    _last_seen[message.from_user.id] = now
    return True


def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " so'm"


def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Mahsulotlar", callback_data="products")],
        [InlineKeyboardButton(text="⚠️ Kam qolganlar", callback_data="low_stock")],
        [InlineKeyboardButton(text="🛒 Yangi buyurtmalar", callback_data="orders_new")],
        [InlineKeyboardButton(text="📋 Barcha buyurtmalar", callback_data="orders_all")],
    ])


def product_kb(rows) -> InlineKeyboardMarkup:
    buttons = []
    for p in rows:
        icon = "🔴" if p["stock"] <= p["reorder_level"] else "🟢"
        buttons.append([InlineKeyboardButton(text=f"{icon} {p['name'][:40]}", callback_data=f"p:{p['id']}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_actions(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Omborni sozlash", callback_data=f"edit:{product_id}")],
        [InlineKeyboardButton(text="➕ Qoldiq qo'shish", callback_data=f"add:{product_id}")],
        [InlineKeyboardButton(text="⬅️ Mahsulotlar", callback_data="products")],
    ])


def order_kb(order_id: int, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status == "new":
        buttons.append([InlineKeyboardButton(text="⚙️ Jarayonda", callback_data=f"status:{order_id}:processing")])
    if status in {"new", "processing"}:
        buttons.append([InlineKeyboardButton(text="✅ Yakunlandi", callback_data=f"status:{order_id}:done")])
        buttons.append([InlineKeyboardButton(text="❌ Bekor qilindi", callback_data=f"status:{order_id}:cancelled")])
    buttons.append([InlineKeyboardButton(text="⬅️ Buyurtmalar", callback_data="orders_new")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


class EditInventory(StatesGroup):
    stock = State()
    reorder_level = State()
    reorder_quantity = State()
    purchase_price = State()


class AddStock(StatesGroup):
    quantity = State()


@router.message(Command("start"))
async def start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Siz admin emassiz. Bu bot faqat RAVOD administratorlari uchun.")
        return
    await message.answer("🛡 <b>RAVOD Admin Bot</b>\n\nBoshqaruv paneli tayyor.", parse_mode="HTML", reply_markup=main_kb())


@router.message()
async def non_admin_or_unknown(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Siz admin emassiz. Bu bot faqat RAVOD administratorlari uchun.")
    elif guarded(message):
        await message.answer("Menyudan kerakli bo'limni tanlang.", reply_markup=main_kb())


@router.callback_query()
async def callbacks(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Ruxsat yo'q", show_alert=True)
        return

    data = call.data or ""
    await call.answer()

    if data == "home":
        await state.clear()
        await call.message.edit_text("🛡 <b>RAVOD Admin Bot</b>\n\nBoshqaruv paneli:", parse_mode="HTML", reply_markup=main_kb())
        return

    if data == "products":
        rows = db.get_products()
        if not rows:
            await call.message.edit_text("Mahsulotlar topilmadi.", reply_markup=main_kb())
            return
        await call.message.edit_text("📦 Mahsulotni tanlang:", reply_markup=product_kb(rows))
        return

    if data == "low_stock":
        rows = db.low_stock_products()
        if not rows:
            await call.message.edit_text("✅ Hozircha qayta olib kelish kerak bo'lgan mahsulot yo'q.", reply_markup=main_kb())
            return
        text = "⚠️ <b>Qayta olib kelish kerak:</b>\n\n"
        for p in rows:
            qty = p["reorder_quantity"] or 0
            text += f"• <b>{p['name']}</b> — qoldiq: {p['stock']} | chegara: {p['reorder_level']} | olish: {qty} dona\n"
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=main_kb())
        return

    if data.startswith("p:"):
        pid = int(data.split(":", 1)[1])
        p = db.get_product(pid)
        if not p:
            await call.message.edit_text("Mahsulot topilmadi.", reply_markup=main_kb())
            return
        alert = "🔴 QAYTA OLISH KERAK" if p["stock"] <= p["reorder_level"] else "🟢 Yetarli"
        text = (
            f"📦 <b>{p['name']}</b>\n\n"
            f"💰 Sotish narxi: {money(p['price'])}\n"
            f"💸 Kelish narxi: {money(p['purchase_price'])}\n"
            f"📊 Qoldiq: <b>{p['stock']}</b> dona\n"
            f"⚠️ Qayta olish chegarasi: <b>{p['reorder_level']}</b> dona\n"
            f"🛒 Keyingi safar olish: <b>{p['reorder_quantity']}</b> dona\n\n"
            f"Holat: <b>{alert}</b>"
        )
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=product_actions(pid))
        return

    if data.startswith("edit:"):
        pid = int(data.split(":", 1)[1])
        if not db.get_product(pid):
            await call.message.edit_text("Mahsulot topilmadi.", reply_markup=main_kb())
            return
        await state.update_data(product_id=pid)
        await call.message.edit_text("1/4 — Hozir nechta bor? Faqat butun son yozing.")
        await state.set_state(EditInventory.stock)
        return

    if data.startswith("add:"):
        pid = int(data.split(":", 1)[1])
        if not db.get_product(pid):
            await call.message.edit_text("Mahsulot topilmadi.", reply_markup=main_kb())
            return
        await state.update_data(product_id=pid)
        await call.message.edit_text("Nechta mahsulot qo'shildi? Faqat butun son yozing.")
        await state.set_state(AddStock.quantity)
        return

    if data in {"orders_new", "orders_all"}:
        status = "new" if data == "orders_new" else None
        rows = db.get_orders(status=status, limit=30)
        if not rows:
            await call.message.edit_text("📭 Buyurtmalar topilmadi.", reply_markup=main_kb())
            return
        text = "🛒 <b>Yangi buyurtmalar:</b>\n\n" if status else "📋 <b>Oxirgi buyurtmalar:</b>\n\n"
        for o in rows:
            text += f"#{o['id']} — {o['customer_name']} — {money(o['total_price'])} — {o['status']}\n"
        # Keep the main list compact; each order gets its own button.
        buttons = [[InlineKeyboardButton(text=f"#{o['id']} • {o['customer_name'][:22]}", callback_data=f"order:{o['id']}")] for o in rows]
        buttons.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")])
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    if data.startswith("order:"):
        oid = int(data.split(":", 1)[1])
        rows = db.get_orders(limit=100)
        order = next((x for x in rows if x["id"] == oid), None)
        if not order:
            await call.message.edit_text("Buyurtma topilmadi.", reply_markup=main_kb())
            return
        items = db.get_order_items(oid)
        text = (
            f"🛒 <b>Buyurtma #{order['id']}</b>\n\n"
            f"👤 {order['customer_name']}\n"
            f"📞 {order['phone']}\n"
            f"🔗 {order['username'] or 'username yo‘q'}\n"
            f"📌 Turi: {order['order_type']}\n"
            f"📊 Holati: <b>{order['status']}</b>\n\n"
            "📦 Mahsulotlar:\n"
        )
        for item in items:
            text += f"• {item['product_name']} × {item['quantity']} — {money(item['unit_price'])}\n"
        text += f"\n💵 Jami: <b>{money(order['total_price'])}</b>"
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=order_kb(oid, order["status"]))
        return

    if data.startswith("status:"):
        _, oid_s, status = data.split(":", 2)
        db.set_order_status(int(oid_s), status)
        await call.message.edit_text(f"✅ Buyurtma #{oid_s} holati: <b>{status}</b>", parse_mode="HTML", reply_markup=main_kb())
        return


@router.message(EditInventory.stock)
async def inv_stock(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    if not message.text.isdigit() or int(message.text) < 0:
        await message.answer("❌ 0 yoki undan katta butun son yozing.")
        return
    await state.update_data(stock=int(message.text))
    await message.answer("2/4 — Nechta qolganda qayta olish kerak?")
    await state.set_state(EditInventory.reorder_level)


@router.message(EditInventory.reorder_level)
async def inv_level(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0:
        await message.answer("❌ 0 yoki undan katta butun son yozing.")
        return
    await state.update_data(reorder_level=int(message.text))
    await message.answer("3/4 — Keyingi safar nechta olamiz?")
    await state.set_state(EditInventory.reorder_quantity)


@router.message(EditInventory.reorder_quantity)
async def inv_qty(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0:
        await message.answer("❌ 0 yoki undan katta butun son yozing.")
        return
    await state.update_data(reorder_quantity=int(message.text))
    await message.answer("4/4 — Donasini nechadan oldingiz? (so'm, 0 bo'lishi mumkin)")
    await state.set_state(EditInventory.purchase_price)


@router.message(EditInventory.purchase_price)
async def inv_purchase(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 0:
        await message.answer("❌ Faqat 0 yoki undan katta son yozing.")
        return
    data = await state.get_data()
    pid = data["product_id"]
    db.set_inventory(pid, data["stock"], data["reorder_level"], data["reorder_quantity"], int(message.text))
    await state.clear()
    p = db.get_product(pid)
    await message.answer(
        f"✅ <b>{p['name']}</b> ombori saqlandi.\n\n"
        f"Qoldiq: {p['stock']}\nChegara: {p['reorder_level']}\nKeyingi olish: {p['reorder_quantity']} dona\nKelish narxi: {money(p['purchase_price'])}",
        parse_mode="HTML", reply_markup=main_kb())


@router.message(AddStock.quantity)
async def add_stock(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ 1 yoki undan katta butun son yozing.")
        return
    data = await state.get_data()
    p = db.get_product(data["product_id"])
    if not p:
        await state.clear()
        await message.answer("Mahsulot topilmadi.", reply_markup=main_kb())
        return
    db.set_stock(p["id"], p["stock"] + int(message.text))
    await state.clear()
    await message.answer(f"✅ {p['name']} qoldig'i yangilandi: {p['stock'] + int(message.text)} dona.", reply_markup=main_kb())


async def main():
    db.migrate()
    log.info("RAVOD admin bot started; admins=%s", sorted(ADMIN_IDS))
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
