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


def test_api_queue_status_requires_login():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        response = client.get('/api/queue-status')
        assert response.status_code == 401


def test_api_notifications_log_requires_login():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        response = client.get('/api/notifications-log')
        assert response.status_code == 401
