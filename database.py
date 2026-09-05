import sqlite3


def db_connect():
    return sqlite3.connect("ravod.db")


def create_tables():
    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, price INTEGER, photo_id TEXT, category_id INTEGER)''')
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS carts (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY, role TEXT)''')

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN is_available INTEGER DEFAULT 1")
    except:
        pass

    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")

    # === YANGI: VERSIYA VA TARGET UCHUN XOTIRA ===
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('current_version', '1.0.0')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('last_update_date', '2026-09-05')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('next_version', '')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('next_features', '')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('target_users', '0')")

    conn.commit()
    conn.close()


# === YANGI FUNKSIYALAR: SOZLAMALARNI O'QISH VA YOZISH ===
def get_setting(key):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else ""


def set_setting(key, value):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


# QOLGAN BARCHA KODLARINGIZ O'Z HOLLICHA QOLDIRILDI:
def add_admin(user_id, role):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO admins (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()
    conn.close()


def is_admin(user_id):
    import config
    if str(user_id) == str(config.ADMIN_ID):
        return True
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return bool(res)


def add_user(user_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    return users


def get_maintenance():
    return get_setting('maintenance')


def set_maintenance(status):
    set_setting('maintenance', status)


def add_category(name):
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except:
        pass
    conn.close()


def get_all_categories():
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    cats = cursor.fetchall()
    conn.close()
    return cats


def add_to_cart(user_id, product_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO carts (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
    conn.commit()
    conn.close()


def get_cart(user_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT products.name, products.price FROM carts JOIN products ON carts.product_id = products.id WHERE carts.user_id = ?''',
        (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items


def clear_cart(user_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_products_by_category(cat_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, is_available FROM products WHERE category_id = ?", (cat_id,))
    prods = cursor.fetchall()
    conn.close()
    return prods


def delete_category(cat_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    cursor.execute("DELETE FROM products WHERE category_id = ?", (cat_id,))
    conn.commit()
    conn.close()


def delete_product(prod_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (prod_id,))
    cursor.execute("DELETE FROM carts WHERE product_id = ?", (prod_id,))
    conn.commit()
    conn.close()


def toggle_product_availability(prod_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT is_available FROM products WHERE id = ?", (prod_id,))
    status = cursor.fetchone()[0]
    new_status = 0 if status == 1 else 1
    cursor.execute("UPDATE products SET is_available = ? WHERE id = ?", (new_status, prod_id))
    conn.commit()
    conn.close()


def update_category_name(cat_id, new_name):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, cat_id))
    conn.commit()
    conn.close()


def update_product_name(prod_id, new_name):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ? WHERE id = ?", (new_name, prod_id))
    conn.commit()
    conn.close()


def update_product_desc(prod_id, new_desc):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET description = ? WHERE id = ?", (new_desc, prod_id))
    conn.commit()
    conn.close()


def update_product_photo(prod_id, photo_id):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET photo_id = ? WHERE id = ?", (photo_id, prod_id))
    conn.commit()
    conn.close()


def get_all_admins():
    import config
    admins = [int(config.ADMIN_ID)]
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM admins")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        admin_id = int(row[0])
        if admin_id not in admins:
            admins.append(admin_id)
    return admins