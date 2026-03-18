import sqlite3
from datetime import datetime


DB_NAME = "bot.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT NOT NULL,
            username TEXT,
            role TEXT NOT NULL,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            shop_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            before_qty INTEGER NOT NULL,
            after_qty INTEGER NOT NULL,
            comment TEXT,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            agent_id INTEGER NOT NULL,
            latitude TEXT NOT NULL,
            longitude TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =========================
# USERS
# =========================

def get_user_by_login(login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE login = ?", (login,))
    user = cur.fetchone()
    conn.close()
    return user


def get_user_by_telegram_id(telegram_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cur.fetchone()
    conn.close()
    return user


def bind_telegram_to_user(user_id, telegram_id, username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET telegram_id = ?, username = ?
        WHERE id = ?
    """, (telegram_id, username, user_id))
    conn.commit()
    conn.close()


def create_user(full_name, role, login, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (telegram_id, full_name, username, role, login, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        None,
        full_name,
        None,
        role,
        login,
        password_hash,
        1,
        now_str()
    ))
    conn.commit()
    conn.close()


def get_all_agents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE role = 'agent' ORDER BY full_name ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


# =========================
# PRODUCTS
# =========================

def create_product(name, price):
    conn = get_connection()
    cur = conn.cursor()
    current_time = now_str()

    cur.execute("""
        INSERT INTO products (name, price, quantity, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (name, price, 0, current_time, current_time))

    conn.commit()
    conn.close()


def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_product_by_id(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row


def update_product(product_id, name, price):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE products
        SET name = ?, price = ?, updated_at = ?
        WHERE id = ?
    """, (name, price, now_str(), product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def add_stock(product_id, qty, created_by, comment="Omborga qo'shildi"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()

    if not product:
        conn.close()
        return None

    before_qty = int(product["quantity"])
    after_qty = before_qty + int(qty)

    cur.execute("""
        UPDATE products
        SET quantity = ?, updated_at = ?
        WHERE id = ?
    """, (after_qty, now_str(), product_id))

    cur.execute("""
        INSERT INTO stock_movements (
            product_id, type, quantity, before_qty, after_qty, comment, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product_id, "in", qty, before_qty, after_qty,
        comment, created_by, now_str()
    ))

    conn.commit()
    conn.close()
    return after_qty


# =========================
# SALES
# =========================

def create_sale(agent_id, product_id, shop_name, quantity, unit_price):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cur.fetchone()

    if not product:
        conn.close()
        return {"ok": False, "message": "Mahsulot topilmadi"}

    current_qty = int(product["quantity"])
    quantity = int(quantity)

    if current_qty < quantity:
        conn.close()
        return {"ok": False, "message": "Omborda yetarli mahsulot yo'q"}

    after_qty = current_qty - quantity
    total_price = quantity * int(unit_price)

    cur.execute("""
        UPDATE products
        SET quantity = ?, updated_at = ?
        WHERE id = ?
    """, (after_qty, now_str(), product_id))

    cur.execute("""
        INSERT INTO sales (
            agent_id, product_id, shop_name, quantity, unit_price, total_price, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_id,
        product_id,
        shop_name,
        quantity,
        unit_price,
        total_price,
        "confirmed",
        now_str()
    ))

    sale_id = cur.lastrowid

    cur.execute("""
        INSERT INTO stock_movements (
            product_id, type, quantity, before_qty, after_qty, comment, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        product_id,
        "out",
        quantity,
        current_qty,
        after_qty,
        "Sotuv: {0}".format(shop_name),
        agent_id,
        now_str()
    ))

    conn.commit()
    conn.close()

    return {
        "ok": True,
        "sale_id": sale_id,
        "total_price": total_price,
        "after_qty": after_qty
    }


def save_location(sale_id, agent_id, latitude, longitude):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO locations (sale_id, agent_id, latitude, longitude, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        sale_id,
        agent_id,
        str(latitude),
        str(longitude),
        now_str()
    ))

    conn.commit()
    conn.close()


def get_agent_daily_sales(agent_id):
    conn = get_connection()
    cur = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cur.execute("""
        SELECT sales.*, products.name AS product_name
        FROM sales
        INNER JOIN products ON products.id = sales.product_id
        WHERE sales.agent_id = ? AND date(sales.created_at) = ?
        ORDER BY sales.id DESC
    """, (agent_id, today))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_stock_report():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return rows