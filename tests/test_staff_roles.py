import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db

def test_access_roles():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        # Non connecte -> redirection vers login
        response = client.get('/staff/dashboard', follow_redirects=True)
        assert b"Se Connecter" in response.data or b"login" in response.request.path.encode()
