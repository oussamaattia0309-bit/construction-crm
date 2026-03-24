"""
Database migration script to add new fields to the User model.
Run this script to update your database with the new account management features.
"""

from app import app, db, User
from datetime import datetime

def migrate():
    with app.app_context():
        # Create all new tables
        db.create_all()

        # Get all users
        users = User.query.all()

        print(f"Found {len(users)} users to migrate...")

        for user in users:
            # Add default values for new fields if they don't exist
            if not hasattr(user, 'email') or user.email is None:
                user.email = None
                print(f"  - Added email field for user {user.username}")

            if not hasattr(user, 'avatar') or user.avatar is None:
                user.avatar = 'default.png'
                print(f"  - Added avatar field for user {user.username}")

            if not hasattr(user, 'last_login') or user.last_login is None:
                user.last_login = None
                print(f"  - Added last_login field for user {user.username}")

            if not hasattr(user, 'created_at') or user.created_at is None:
                user.created_at = datetime.utcnow()
                print(f"  - Added created_at field for user {user.username}")

            if not hasattr(user, 'role') or user.role is None:
                user.role = 'staff'
                print(f"  - Added role field for user {user.username}")

            if not hasattr(user, 'is_active') or user.is_active is None:
                user.is_active = True
                print(f"  - Added is_active field for user {user.username}")

            if not hasattr(user, 'two_factor_enabled') or user.two_factor_enabled is None:
                user.two_factor_enabled = False
                print(f"  - Added two_factor_enabled field for user {user.username}")

            if not hasattr(user, 'notification_email') or user.notification_email is None:
                user.notification_email = True
                print(f"  - Added notification_email field for user {user.username}")

            if not hasattr(user, 'notification_login_alert') or user.notification_login_alert is None:
                user.notification_login_alert = True
                print(f"  - Added notification_login_alert field for user {user.username}")

            if not hasattr(user, 'last_login_ip') or user.last_login_ip is None:
                user.last_login_ip = None
                print(f"  - Added last_login_ip field for user {user.username}")

        # Commit all changes
        db.session.commit()
        print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate()
