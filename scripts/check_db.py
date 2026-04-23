import sqlite3
import os

db_path = r'C:\Users\kuzme\Tax\backend\tax_app.db'

if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"Database: {db_path}")
    print(f"Tables found: {[t[0] for t in tables]}")
    
    # Check for users table
    if 'users' in [t[0] for t in tables]:
        cursor.execute("SELECT id, email, created_at FROM users")
        rows = cursor.fetchall()
        print(f"\nUsers in database ({len(rows)} total):")
        for r in rows:
            print(f"  ID: {r[0]}, Email: {r[1]}, Created: {r[2]}")
    else:
        print("\nUsers table does not exist!")
    
    conn.close()
