import sqlite3
import json
import os

# Connect to your database
db_path = 'instance/construction_crm.db'
print(f"Exporting from: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]

print(f"Tables found: {tables}")

# Export each table
data = {}
for table in tables:
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    data[table] = [dict(row) for row in rows]
    print(f"  {table}: {len(data[table])} rows")

# Save to JSON
with open('construction_crm_backup.json', 'w') as f:
    json.dump(data, f, default=str, indent=2)

file_size = os.path.getsize('construction_crm_backup.json')
print(f"\n✓ Exported to construction_crm_backup.json ({file_size} bytes)")

conn.close()
