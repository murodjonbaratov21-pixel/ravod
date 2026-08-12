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

    # YANGI: Foydalanuvchilar va Sozlamalar jadvali
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN is_available INTEGER DEFAULT 1")
    except:
        pass

    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")

    conn.commit()
    conn.close()


def is_admin(user_id):
    import config
    return user_id in config.ADMIN_IDS


# --- Mijozlarni saqlash ---
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


# --- Texnik xizmat ---
def get_maintenance():
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'maintenance'")
    status = cursor.fetchone()[0]
    conn.close()
    return status


def set_maintenance(status):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'maintenance'", (status,))
    conn.commit()
    conn.close()


# --- Qolgan barcha eski kodlar ---
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