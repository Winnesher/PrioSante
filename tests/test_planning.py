import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Consultation, Patient
from app.planning import attribuer_creneau, generer_tous_les_creneaux, service_est_ouvert
from datetime import date, datetime, timedelta

def test_generer_tous_les_creneaux():
    creneaux = generer_tous_les_creneaux()
    assert len(creneaux) > 0
    assert creneaux[0] == "08:00"
    assert creneaux[1] == "08:15"

def test_attribuer_creneau_urgence():
    res = attribuer_creneau(service_id=1, date_cible=date.today(), priorite='Urgence')
    assert res is None

def test_attribuer_creneau_ne_donne_jamais_une_heure_passee():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        resultat = attribuer_creneau(service_id=1, date_cible=date.today(), priorite='Faible')
        assert resultat is not None
        jour, heure = resultat
        assert jour >= date.today()
        if jour == date.today():
            assert datetime.strptime(heure, "%H:%M").time() > datetime.now().time()
        else:
            assert jour == date.today() + timedelta(days=1)
            assert heure == "08:00"

def test_service_est_ouvert_selon_l_heure():
    instant_ouvert = datetime.strptime("2024-01-01 10:00", "%Y-%m-%d %H:%M")
    instant_ferme = datetime.strptime("2024-01-01 20:00", "%Y-%m-%d %H:%M")
    assert service_est_ouvert(instant_ouvert) is True
    assert service_est_ouvert(instant_ferme) is False
