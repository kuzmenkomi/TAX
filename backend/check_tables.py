import sqlite3

conn = sqlite3.connect('tax.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('\n'.join(sorted(tables)))
conn.close()
