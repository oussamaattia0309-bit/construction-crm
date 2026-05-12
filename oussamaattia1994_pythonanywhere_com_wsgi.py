import sys

# Add the project directory to the Python path
sys.path.append('/home/Oussamaattia1994/mysite')

# Import the Flask app
from app import app

# Create the WSGI application
application = app
