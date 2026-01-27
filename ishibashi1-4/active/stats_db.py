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

# ---- 互換レイヤー（全部ここで吸収） ----

def increment_toxic(username):
    add_count(username)

def increase(username):
    add_count(username)

def log_toxic(username):
    add_count(username)