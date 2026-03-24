"""
Database migration script to add new fields to the User model using raw SQL.
Run this script to update your database with the new account management features.
"""

from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        # List of columns to add
        columns = [
            ('email', 'VARCHAR(120) UNIQUE'),
            ('avatar', 'VARCHAR(200) DEFAULT "default.png"'),
            ('last_login', 'DATETIME'),
            ('created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('role', 'VARCHAR(20) DEFAULT "staff"'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('two_factor_enabled', 'BOOLEAN DEFAULT 0'),
            ('notification_email', 'BOOLEAN DEFAULT 1'),
            ('notification_login_alert', 'BOOLEAN DEFAULT 1'),
            ('last_login_ip', 'VARCHAR(45)')
        ]

        # Get existing columns
        inspector = db.inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('user')]

        print(f"Existing columns: {existing_columns}")

        # Add each column if it doesn't exist
        for column_name, column_def in columns:
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_def}"
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    print(f"✗ Error adding column {column_name}: {e}")
                    db.session.rollback()
            else:
                print(f"- Column {column_name} already exists, skipping...")

        print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate()
