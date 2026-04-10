import os
import shutil
import sqlite3
import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'construction_crm.db')
BACKUP_PATH = DB_PATH + f'.backup.{datetime.datetime.now():%Y%m%d%H%M%S}'

print(f'Backing up database to: {BACKUP_PATH}')
shutil.copy2(DB_PATH, BACKUP_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = OFF;')
conn.execute('BEGIN TRANSACTION;')

# Create a new table with ON DELETE CASCADE on project_id and contact_id.
conn.execute('''
CREATE TABLE project_worker_new (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    contact_id INTEGER NOT NULL,
    worker_type VARCHAR(50) NOT NULL,
    role VARCHAR(200),
    start_date DATE,
    contract_amount FLOAT DEFAULT 0.0,
    daily_rate FLOAT DEFAULT 0.0,
    days_worked FLOAT DEFAULT 0.0,
    amount_paid FLOAT DEFAULT 0.0,
    notes TEXT,
    created_at DATETIME,
    FOREIGN KEY(project_id) REFERENCES project(id) ON DELETE CASCADE,
    FOREIGN KEY(contact_id) REFERENCES contact(id) ON DELETE CASCADE
);
''')

conn.execute('''
INSERT INTO project_worker_new (
    id, project_id, contact_id, worker_type, role, start_date,
    contract_amount, daily_rate, days_worked, amount_paid, notes, created_at
)
SELECT
    id, project_id, contact_id, worker_type, role, start_date,
    contract_amount, daily_rate, days_worked, amount_paid, notes, created_at
FROM project_worker;
''')

conn.execute('DROP TABLE project_worker;')
conn.execute('ALTER TABLE project_worker_new RENAME TO project_worker;')

# Recreate foreign keys and enable cascading behavior
conn.execute('PRAGMA foreign_keys = ON;')
conn.commit()
conn.close()

print('Migration complete.')
print('If you are using Flask-SQLAlchemy, restart the web app after running this script.')