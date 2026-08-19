import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Patient


def test_inscription_avec_service_id_invalide_ne_plante_pas():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()

        response = client.post('/inscription', data={
            'nom': 'DUPONT',
            'prenom': 'Jean',
            'telephone': '+228 90 00 00 00',
            'date_naissance': '2000-01-01',
            'service_id': '9999',
            'symptomes': ['toux_rhume'],
        })

        assert response.status_code == 200
        assert 'invalide'.encode() in response.data


def test_inscription_meme_telephone_noms_differents_cree_deux_patients():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            service = Service(nom="Médecine Générale")
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        telephone = '+22890000001'

        # Même personne qui se réinscrit deux fois : ne doit créer qu'un seul Patient
        for _ in range(2):
            client.post('/inscription', data={
                'nom': 'KOUADIO', 'prenom': 'Ama', 'telephone': telephone,
                'date_naissance': '1995-01-01', 'genre': 'F',
                'service_id': str(service_id), 'symptomes': ['toux_rhume'],
            })

        # Même téléphone, nom différent (téléphone familial partagé) : nouveau Patient
        client.post('/inscription', data={
            'nom': 'MENSAH', 'prenom': 'Yao', 'telephone': telephone,
            'date_naissance': '1988-05-05', 'genre': 'M',
            'service_id': str(service_id), 'symptomes': ['toux_rhume'],
        })

        with app.app_context():
            patients = Patient.query.filter_by(telephone=telephone).all()
            noms = sorted((p.nom, p.prenom) for p in patients)
            assert len(patients) == 2
            assert noms == [('KOUADIO', 'Ama'), ('MENSAH', 'Yao')]


def test_inscription_date_naissance_aujourdhui_et_future_refusees():
    from datetime import date, timedelta
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            service = Service(nom="Médecine Générale")
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        today_str = date.today().isoformat()
        future_str = (date.today() + timedelta(days=5)).isoformat()
        too_old_str = (date.today() - timedelta(days=365 * 125)).isoformat()

        # Date d'aujourd'hui
        res1 = client.post('/inscription', data={
            'nom': 'SOSSOU', 'prenom': 'Koffi', 'telephone': '+22890111111',
            'date_naissance': today_str, 'service_id': str(service_id),
            'symptomes': ['toux_rhume']
        })
        assert res1.status_code == 200
        assert "Date de naissance invalide".encode('utf-8') in res1.data

        # Date future
        res2 = client.post('/inscription', data={
            'nom': 'SOSSOU', 'prenom': 'Koffi', 'telephone': '+22890111111',
            'date_naissance': future_str, 'service_id': str(service_id),
            'symptomes': ['toux_rhume']
        })
        assert res2.status_code == 200
        assert "Date de naissance invalide".encode('utf-8') in res2.data

        # Date > 120 ans
        res3 = client.post('/inscription', data={
            'nom': 'SOSSOU', 'prenom': 'Koffi', 'telephone': '+22890111111',
            'date_naissance': too_old_str, 'service_id': str(service_id),
            'symptomes': ['toux_rhume']
        })
        assert res3.status_code == 200
        assert "Date de naissance invalide".encode('utf-8') in res3.data
