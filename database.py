import sqlite3
import pandas as pd

DB_NAME = "finance_tracker.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL
        )
    """)
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Monthly Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            UNIQUE(user_id, category),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

def create_user(username, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_transaction(user_id, date, trans_type, category, amount, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (user_id, date, type, category, amount, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, str(date), trans_type, category, amount, description))
    conn.commit()
    conn.close()

def get_transactions(user_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT id, date, type, category, amount, description FROM transactions WHERE user_id = ? ORDER BY date DESC",
        conn,
        params=(user_id,)
    )
    conn.close()
    return df

def delete_transaction(transaction_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (transaction_id, user_id))
    conn.commit()
    conn.close()

def set_budget(user_id, category, limit_amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budgets (user_id, category, monthly_limit)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, category) DO UPDATE SET monthly_limit = excluded.monthly_limit
    """, (user_id, category, limit_amount))
    conn.commit()
    conn.close()

def get_budgets(user_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT category, monthly_limit FROM budgets WHERE user_id = ?",
        conn,
        params=(user_id,)
    )
    conn.close()
    return df
