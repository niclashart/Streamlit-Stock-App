import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import os  # Add os import

# Path to the directory containing this database.py file
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(APP_DIR, "stock_app.db")  # Use absolute path


def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """
    )

    # Portfolios table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS portfolios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        shares REAL NOT NULL,
        entry_price REAL NOT NULL,
        purchase_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """
    )

    # Orders table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ticker TEXT NOT NULL,
        order_type TEXT NOT NULL, -- 'buy' or 'sell'
        price REAL NOT NULL,
        quantity REAL NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT NOT NULL, -- 'pending', 'executed', 'cancelled'
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """
    )
    conn.commit()
    conn.close()


# --- User Management ---
def hash_password_db(password):
    return hashlib.md5(password.encode()).hexdigest()


def add_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password_db(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:  # Username already exists
        return False
    finally:
        conn.close()


def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def validate_user_login(username, password):
    user = get_user(username)
    if user and user["password_hash"] == hash_password_db(password):
        return user["id"]
    return None


def update_user_password(username, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (hash_password_db(new_password), username),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


# --- Portfolio Management ---
def get_portfolio(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticker, shares, entry_price, purchase_date FROM portfolios WHERE user_id = ?",
        (user_id,),
    )
    portfolio_data = cursor.fetchall()
    conn.close()
    # Convert to DataFrame to maintain compatibility with existing app logic expecting DataFrames
    df = pd.DataFrame(
        portfolio_data, columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"]
    )
    if not portfolio_data:  # Ensure correct columns even if empty
        return pd.DataFrame(
            columns=["Ticker", "Anteile", "Einstiegspreis", "Kaufdatum"]
        )
    df["Kaufdatum"] = pd.to_datetime(df["Kaufdatum"])
    return df


def add_to_portfolio(user_id, ticker, shares, entry_price, purchase_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if position exists to update it, or insert new
    cursor.execute(
        """
        SELECT id, shares FROM portfolios 
        WHERE user_id = ? AND ticker = ? AND entry_price = ? AND purchase_date = ?
    """,
        (user_id, ticker, entry_price, purchase_date.strftime("%Y-%m-%d")),
    )
    existing_position = cursor.fetchone()

    if existing_position:
        new_shares = existing_position["shares"] + shares
        cursor.execute(
            "UPDATE portfolios SET shares = ? WHERE id = ?",
            (new_shares, existing_position["id"]),
        )
    else:
        cursor.execute(
            """
            INSERT INTO portfolios (user_id, ticker, shares, entry_price, purchase_date)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, ticker, shares, entry_price, purchase_date.strftime("%Y-%m-%d")),
        )
    conn.commit()
    conn.close()


def update_portfolio_after_sell(user_id, ticker, quantity_to_sell):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get all positions for this ticker, oldest first, to sell from
    cursor.execute(
        """
        SELECT id, shares FROM portfolios 
        WHERE user_id = ? AND ticker = ? 
        ORDER BY purchase_date ASC
    """,
        (user_id, ticker),
    )
    positions = cursor.fetchall()

    remaining_quantity_to_sell = quantity_to_sell
    for position in positions:
        if remaining_quantity_to_sell <= 0:
            break

        position_id = position["id"]
        position_shares = position["shares"]

        if position_shares > remaining_quantity_to_sell:
            new_shares = position_shares - remaining_quantity_to_sell
            cursor.execute(
                "UPDATE portfolios SET shares = ? WHERE id = ?",
                (new_shares, position_id),
            )
            remaining_quantity_to_sell = 0
        else:  # Sell all shares in this position
            cursor.execute("DELETE FROM portfolios WHERE id = ?", (position_id,))
            remaining_quantity_to_sell -= position_shares

    conn.commit()
    conn.close()
    return remaining_quantity_to_sell == 0  # True if all shares were successfully sold


# --- Order Management ---
def add_order_db(user_id, ticker, order_type, price, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "pending"
    cursor.execute(
        """
        INSERT INTO orders (user_id, ticker, order_type, price, quantity, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (user_id, ticker, order_type, price, quantity, created_at, status),
    )
    conn.commit()
    conn.close()
    return True


def get_orders(user_id=None, status=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT o.id, u.username, o.ticker, o.order_type, o.price, o.quantity, o.created_at, o.status FROM orders o JOIN users u ON o.user_id = u.id"
    params = []
    conditions = []

    if user_id is not None:
        conditions.append("o.user_id = ?")
        params.append(user_id)
    if status is not None:
        conditions.append("o.status = ?")
        params.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY o.created_at DESC"

    cursor.execute(query, tuple(params))
    orders_data = cursor.fetchall()
    conn.close()

    df_columns = [
        "id",
        "username",
        "ticker",
        "order_type",
        "price",
        "quantity",
        "created_at",
        "status",
    ]
    df = pd.DataFrame(orders_data, columns=df_columns)
    if not orders_data:
        return pd.DataFrame(columns=df_columns)
    return df


def update_order_status(order_id, new_status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    conn.commit()
    conn.close()


# Initialize database and tables on first import
init_db()
