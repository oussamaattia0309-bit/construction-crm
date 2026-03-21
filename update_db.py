import sys, os
sys.path.append(os.getcwd())
from app import app, db

with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully (including association table)")
    except Exception as e:
        print(f"Error creating tables: {e}")
