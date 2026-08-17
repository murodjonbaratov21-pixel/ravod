from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.getenv("RAVOD_DB_PATH", "../ravod.db")


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def migrate():
    with connect() as db:
        # Inventory fields are additive, so existing RAVOD data is preserved.
        columns = {r[1] for r in db.execute("PRAGMA table_info(products)")}
        additions = {
            "stock": "INTEGER NOT NULL DEFAULT 0",
            "reorder_level": "INTEGER NOT NULL DEFAULT 0",
            "reorder_quantity": "INTEGER NOT NULL DEFAULT 0",
            "purchase_price": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, definition in additions.items():
            if name not in columns:
                db.execute(f"ALTER TABLE products ADD COLUMN {name} {definition}")

        db.execute(
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                username TEXT,
                phone TEXT NOT NULL,
                order_type TEXT NOT NULL,
                total_price INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'new',
                source_message_id INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        db.execute(
            """CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
            )"""
        )
        db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)")


def get_products():
    with connect() as db:
        return db.execute(
            "SELECT id,name,price,stock,reorder_level,reorder_quantity,purchase_price,is_available "
            "FROM products ORDER BY id DESC"
        ).fetchall()


def get_product(product_id: int):
    with connect() as db:
        return db.execute(
            "SELECT id,name,price,stock,reorder_level,reorder_quantity,purchase_price,is_available "
            "FROM products WHERE id=?", (product_id,)
        ).fetchone()


def set_inventory(product_id: int, stock: int, reorder_level: int, reorder_quantity: int, purchase_price: int):
    with connect() as db:
        db.execute(
            "UPDATE products SET stock=?, reorder_level=?, reorder_quantity=?, purchase_price=? WHERE id=?",
            (stock, reorder_level, reorder_quantity, purchase_price, product_id),
        )


def set_stock(product_id: int, stock: int):
    with connect() as db:
        db.execute("UPDATE products SET stock=? WHERE id=?", (stock, product_id))


def low_stock_products():
    with connect() as db:
        return db.execute(
            "SELECT id,name,stock,reorder_level,reorder_quantity FROM products "
            "WHERE stock <= reorder_level ORDER BY stock ASC, name ASC"
        ).fetchall()


def get_orders(status: str | None = None, limit: int = 30):
    with connect() as db:
        if status:
            return db.execute(
                "SELECT * FROM orders WHERE status=? ORDER BY id DESC LIMIT ?", (status, limit)
            ).fetchall()
        return db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


def get_order_items(order_id: int):
    with connect() as db:
        return db.execute(
            "SELECT product_name,quantity,unit_price FROM order_items WHERE order_id=? ORDER BY id",
            (order_id,),
        ).fetchall()


def set_order_status(order_id: int, status: str):
    allowed = {"new", "processing", "done", "cancelled"}
    if status not in allowed:
        raise ValueError("Invalid order status")
    with connect() as db:
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))


def create_order(user_id: int, customer_name: str, username: str | None, phone: str,
                 order_type: str, source_message_id: int | None, items: list[dict]):
    if not items:
        raise ValueError("Order must contain at least one item")

    total = sum(int(x["quantity"]) * int(x["unit_price"]) for x in items)
    with connect() as db:
        cur = db.execute(
            "INSERT INTO orders(telegram_user_id,customer_name,username,phone,order_type,total_price,source_message_id) "
            "VALUES(?,?,?,?,?,?,?)",
            (user_id, customer_name[:120], username[:120] if username else None, phone[:40],
             order_type[:30], total, source_message_id),
        )
        order_id = cur.lastrowid
        for item in items:
            db.execute(
                "INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price) VALUES(?,?,?,?,?)",
                (order_id, item["product_id"], item["product_name"][:200], int(item["quantity"]), int(item["unit_price"])),
            )
            db.execute(
                "UPDATE products SET stock = MAX(0, stock - ?) WHERE id=?",
                (int(item["quantity"]), item["product_id"]),
            )
        return order_id
