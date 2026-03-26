import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("SELECT file_path FROM files")
rows = cursor.fetchall()

print("Stored file paths:")
for r in rows:
    print(r[0])

conn.close()