import sqlite3

conn = sqlite3.connect('tax_app.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print("✅ Database tables created:")
print("=" * 40)
for table in tables:
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"\n📋 {table[0]}")
    print("-" * 40)
    for col in columns:
        col_id, col_name, col_type, notnull, dflt, pk = col
        null_str = "NOT NULL" if notnull else "nullable"
        print(f"  - {col_name:<25} {col_type:<10} {null_str}")

print("\n" + "=" * 40)
print(f"Total tables: {len(tables)}")
conn.close()
