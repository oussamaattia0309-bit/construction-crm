
#!/usr/bin/env python
"""
Migration script to add the project_task table for Gantt chart functionality
"""
from app import app, db
from datetime import datetime

def migrate():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Migration completed successfully!")
        print("The project_task table has been added to the database.")

if __name__ == '__main__':
    migrate()
