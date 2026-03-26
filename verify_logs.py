import sqlite3
import hashlib

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("SELECT user, file, action, timestamp, hash FROM logs")
rows = cursor.fetchall()

tampered = False

for row in rows:
    user, file, action, timestamp, stored_hash = row

    log_string = f"{user}|{file}|{action}|{timestamp}"
    computed_hash = hashlib.sha256(log_string.encode()).hexdigest()

    if computed_hash != stored_hash:
        print("❌ TAMPER DETECTED:", row)
        tampered = True

if not tampered:
    print("✅ Logs are clean")

conn.close()