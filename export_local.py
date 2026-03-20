import sqlite3, json
conn = sqlite3.connect('instance/construction_crm.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
data = {}
for t in [r[0] for r in c.fetchall()]:
    data[t] = [dict(r) for r in c.execute(f'SELECT * FROM {t}')]
json.dump(data, open('data.json','w'), default=str)
print("Exported to data.json")
conn.close()