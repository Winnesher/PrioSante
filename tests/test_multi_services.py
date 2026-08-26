import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Consultation, Patient
from datetime import date

def test_17_services_peuplement_base():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        services_noms = [
            "Médecine Générale", "Pédiatrie", "Gynécologie & Obstétrique", "Cardiologie",
            "Dermatologie & Vénéréologie", "Ophtalmologie", "Oto-Rhino-Laryngologie (ORL)",
            "Neurologie", "Orthopédie & Traumatologie", "Gastro-Entérologie", "Pneumologie",
            "Endocrinologie & Diabétologie", "Odontologie & Stomatologie", "Urologie",
            "Rhumatologie", "Néphrologie", "Psychiatrie & Santé Mentale"
        ]

        for nom in services_noms:
            s = Service(nom=nom, description=f"Description du service {nom}", duree_moyenne_consultation=20)
            db.session.add(s)
        db.session.commit()

        total = Service.query.count()
        assert total == 17

def test_inscription_patient_pediatrie_et_cardiologie():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            service_pediatrie = Service(nom="Pédiatrie", description="Service enfant", duree_moyenne_consultation=15)
            service_cardio = Service(nom="Cardiologie", description="Service cœur", duree_moyenne_consultation=20)
            db.session.add_all([service_pediatrie, service_cardio])
            db.session.commit()
            ped_id = service_pediatrie.id
            card_id = service_cardio.id

        # Inscription en Pédiatrie
        res1 = client.post('/inscription', data={
            'nom': 'ENFANT',
            'prenom': 'Leo',
            'telephone': '+22890000001',
            'date_naissance': '2018-06-12',
            'genre': 'M',
            'service_id': str(ped_id),
            'symptomes': ['fievre_legere'],
            'symptome_libre': ''
        })

        assert res1.status_code == 302
        assert '/confirmation/' in res1.headers['Location']

        # Inscription en Cardiologie
        res2 = client.post('/inscription', data={
            'nom': 'ADULTE',
            'prenom': 'Marc',
            'telephone': '+22890000002',
            'date_naissance': '1970-03-25',
            'genre': 'M',
            'service_id': str(card_id),
            'symptomes': ['douleur_moderee'],
            'symptome_libre': ''
        })

        assert res2.status_code == 302
        assert '/confirmation/' in res2.headers['Location']

        with app.app_context():
            c1 = Consultation.query.filter_by(patient_id=1).first()
            c2 = Consultation.query.filter_by(patient_id=2).first()
            assert c1.service_id == ped_id
            assert c2.service_id == card_id
