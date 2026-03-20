import sqlite3
import json

# Connect to your local database
conn = sqlite3.connect('instance/construction_crm.db')
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
with open('local_data_export.json', 'w') as f:
    json.dump(data, f, default=str, indent=2)

print(f"\n✓ Exported to local_data_export.json")
conn.close()
