import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    file TEXT,
    action TEXT,
    timestamp INTEGER
)
""")

conn.commit()
conn.close()

print("✅ Logs table ready")