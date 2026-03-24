"""
Final migration script to add email and created_at columns.
"""

from app import app, db
from sqlalchemy import text
from datetime import datetime

def migrate():
    with app.app_context():
        # Get existing columns
        inspector = db.inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('user')]

        print(f"Existing columns: {existing_columns}")

        # Add email column (without UNIQUE constraint first)
        if 'email' not in existing_columns:
            try:
                # Add email column without UNIQUE constraint
                db.session.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(120)"))
                db.session.commit()
                print("✓ Added column: email (without UNIQUE constraint)")

                # Update existing users with NULL email
                db.session.execute(text("UPDATE user SET email = NULL WHERE email IS NULL"))
                db.session.commit()

                # Now create a new table with UNIQUE constraint and copy data
                print("Creating new table with UNIQUE constraint...")
                db.session.execute(text("""
                    CREATE TABLE user_new (
                        id INTEGER PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        password_hash VARCHAR(120) NOT NULL,
                        email VARCHAR(120) UNIQUE,
                        avatar VARCHAR(200) DEFAULT 'default.png',
                        last_login DATETIME,
                        created_at DATETIME,
                        role VARCHAR(20) DEFAULT 'staff',
                        is_active BOOLEAN DEFAULT 1,
                        two_factor_enabled BOOLEAN DEFAULT 0,
                        notification_email BOOLEAN DEFAULT 1,
                        notification_login_alert BOOLEAN DEFAULT 1,
                        last_login_ip VARCHAR(45)
                    )
                """))
                db.session.commit()

                # Copy data from old table to new table
                print("Copying data...")
                db.session.execute(text("""
                    INSERT INTO user_new (id, username, password_hash, email, avatar, last_login, role, is_active, two_factor_enabled, notification_email, notification_login_alert, last_login_ip)
                    SELECT id, username, password_hash, email, avatar, last_login, role, is_active, two_factor_enabled, notification_email, notification_login_alert, last_login_ip
                    FROM user
                """))
                db.session.commit()

                # Drop old table
                print("Dropping old table...")
                db.session.execute(text("DROP TABLE user"))
                db.session.commit()

                # Rename new table
                print("Renaming new table...")
                db.session.execute(text("ALTER TABLE user_new RENAME TO user"))
                db.session.commit()

                print("✓ Email column added with UNIQUE constraint")
            except Exception as e:
                print(f"✗ Error adding email column: {e}")
                db.session.rollback()
        else:
            print("- Column email already exists, skipping...")

        # Add created_at column
        if 'created_at' not in existing_columns:
            try:
                # Add created_at column without default
                db.session.execute(text("ALTER TABLE user ADD COLUMN created_at DATETIME"))
                db.session.commit()

                # Update existing users with current timestamp
                db.session.execute(text("UPDATE user SET created_at = ? WHERE created_at IS NULL"), (datetime.utcnow(),))
                db.session.commit()

                print("✓ Added column: created_at")
            except Exception as e:
                print(f"✗ Error adding created_at column: {e}")
                db.session.rollback()
        else:
            print("- Column created_at already exists, skipping...")

        print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate()
