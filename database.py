import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    city TEXT,
    street TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS resources (
    user_id INTEGER,
    resource TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS channels (
    user_id INTEGER,
    channel TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS sent (
    user_id INTEGER,
    msg_key TEXT,
    PRIMARY KEY (user_id, msg_key)
)
""")

conn.commit()


def save_city(user_id, city):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cur.execute("UPDATE users SET city=? WHERE user_id=?", (city, user_id))
    conn.commit()


def save_street(user_id, street):
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cur.execute("UPDATE users SET street=? WHERE user_id=?", (street, user_id))
    conn.commit()


def get_user(user_id):
    cur.execute(
        "SELECT city, street FROM users WHERE user_id=?",
        (user_id,)
    )
    row = cur.fetchone()
    if row is None:
        return None, None
    return row


def set_resources(user_id, items):
    cur.execute("DELETE FROM resources WHERE user_id=?", (user_id,))
    for r in items:
        cur.execute("INSERT INTO resources VALUES (?, ?)", (user_id, r))
    conn.commit()


def get_resources(user_id):
    cur.execute("SELECT resource FROM resources WHERE user_id=?", (user_id,))
    return [x[0] for x in cur.fetchall()]


def set_channels(user_id, items):
    cur.execute("DELETE FROM channels WHERE user_id=?", (user_id,))
    for c in items:
        cur.execute("INSERT INTO channels VALUES (?, ?)", (user_id, c))
    conn.commit()


def get_channels(user_id):
    cur.execute("SELECT channel FROM channels WHERE user_id=?", (user_id,))
    return [x[0] for x in cur.fetchall()]


def is_sent(user_id, key):
    cur.execute(
        "SELECT 1 FROM sent WHERE user_id=? AND msg_key=?",
        (user_id, key)
    )
    return cur.fetchone() is not None


def mark_sent(user_id, key):
    cur.execute("INSERT OR IGNORE INTO sent VALUES (?, ?)", (user_id, key))
    conn.commit()


def all_users():
    cur.execute("SELECT user_id FROM users")
    return [x[0] for x in cur.fetchall()]
def add_channel(user_id, channel):
    cur.execute(
        "INSERT INTO channels (user_id, channel) VALUES (?, ?)",
        (user_id, channel)
    )
    conn.commit()


def remove_channel(user_id, channel):
    cur.execute(
        "DELETE FROM channels WHERE user_id=? AND channel=?",
        (user_id, channel)
    )
    conn.commit()

