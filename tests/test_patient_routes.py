import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db


def test_inscription_avec_service_id_invalide_ne_plante_pas():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()

        response = client.post('/inscription', data={
            'nom': 'DUPONT',
            'prenom': 'Jean',
            'telephone': '+228 90 00 00 00',
            'service_id': '9999',
            'symptomes': ['toux_rhume'],
        })

        assert response.status_code == 200
        assert 'invalide'.encode() in response.data
