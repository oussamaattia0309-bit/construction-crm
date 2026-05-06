import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Create a minimal Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///construction_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)

# Define the User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    avatar = db.Column(db.String(200), default='default.png')
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='staff')
    is_active = db.Column(db.Boolean, default=True)

def list_users():
    with app.app_context():
        users = User.query.all()
        print("Current users in the system:")
        print("-" * 50)
        for user in users:
            status = "Active" if user.is_active else "Inactive"
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email or 'Not set'}")
            print(f"Role: {user.role}")
            print(f"Status: {status}")
            print(f"Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'Not set'}")
            print(f"Last login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'}")
            print("-" * 50)

if __name__ == "__main__":
    list_users()
