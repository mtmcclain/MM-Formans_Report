"""Quick script to check users in database"""
import sqlite3
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

cursor.execute('SELECT username, full_name, role FROM users')
users = cursor.fetchall()

conn.close()

print("Users in database:")
if users:
    for username, full_name, role in users:
        name = full_name or "No name"
        print(f"  - {username} ({name}) - {role}")
else:
    print("  No users found in database")
