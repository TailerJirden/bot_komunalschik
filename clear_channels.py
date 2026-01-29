import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DELETE FROM users")
cur.execute("DELETE FROM resources")
cur.execute("DELETE FROM channels")
cur.execute("DELETE FROM sent_messages")

conn.commit()
conn.close()

print("✅ Все пользователи и их данные удалены")
