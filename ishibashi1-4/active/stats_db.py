import sqlite3

DB_PATH = "stats.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS toxic_counts (
            username TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            password TEXT,
            first_name TEXT,
            last_name TEXT
        )
    """)
    conn.commit()
    conn.close()

# 正式API（これを基本にする）
def add_count(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO toxic_counts(username, count)
        VALUES(?, 1)
        ON CONFLICT(username)
        DO UPDATE SET count = count + 1
    """, (username,))
    conn.commit()
    conn.close()

def get_count(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT count FROM toxic_counts WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def save_user(username, user_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO users(username, name, email, password, first_name, last_name)
        VALUES(?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            password=excluded.password,
            first_name=excluded.first_name,
            last_name=excluded.last_name
        """,
        (
            username,
            user_data.get("name"),
            user_data.get("email"),
            user_data.get("password"),
            user_data.get("first_name"),
            user_data.get("last_name"),
        ),
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, name, email, password, first_name, last_name FROM users")
    rows = c.fetchall()
    conn.close()
    users = {}
    for username, name, email, password, first_name, last_name in rows:
        users[username] = {
            "name": name,
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
        }
    return users

# ---- 互換レイヤー（全部ここで吸収） ----

def increment_toxic(username):
    add_count(username)

def increase(username):
    add_count(username)

def log_toxic(username):
    add_count(username)