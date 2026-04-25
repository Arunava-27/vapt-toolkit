import sqlite3
try:
    conn = sqlite3.connect('vapt.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(f'Tables: {tables}')
    c.execute('PRAGMA integrity_check')
    result = c.fetchone()[0]
    print(f'DB integrity: {result}')
    conn.close()
except Exception as e:
    print(f'DB Error: {e}')
