import sys, os
sys.path.append(os.getcwd())
from app import app, db, User

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
