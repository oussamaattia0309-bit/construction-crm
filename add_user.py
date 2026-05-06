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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def create_user(username, password):
    with app.app_context():
        # Check if user exists (case-insensitive)
        existing_user = User.query.filter(User.username.ilike(username)).first()
        if existing_user:
            print(f"User '{username}' already exists. Updating password...")
            existing_user.set_password(password)
        else:
            print(f"Creating user '{username}'...")
            new_user = User(username=username.lower())
            new_user.set_password(password)
            db.session.add(new_user)

        db.session.commit()
        print("Success!")

if __name__ == "__main__":
    create_user("oussama", "22488665")
    print("User 'oussama' has been created/updated with password '22488665'")
