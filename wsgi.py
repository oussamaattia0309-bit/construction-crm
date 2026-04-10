import sys
import os

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app
from app import app

# Create the WSGI application
application = app
