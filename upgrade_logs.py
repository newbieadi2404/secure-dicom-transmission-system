import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# Add hash column if not exists
try:
    cursor.execute("ALTER TABLE logs ADD COLUMN hash TEXT")
except:
    pass  # already exists

conn.commit()
conn.close()

print("✅ Logs table upgraded")