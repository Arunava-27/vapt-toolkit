import sqlite3

conn = sqlite3.connect('vapt.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT id, target, scan_type, status, created_at FROM scans ORDER BY created_at DESC LIMIT 5')
scans = cursor.fetchall()

print('Recent Scans:')
print('─' * 80)
for scan in scans:
    print(f"ID: {scan['id']}")
    print(f"Target: {scan['target']}")
    print(f"Type: {scan['scan_type']}")
    print(f"Status: {scan['status']}")
    print(f"Created: {scan['created_at']}")
    print()

conn.close()
