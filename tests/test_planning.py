import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Consultation, Patient
from app.planning import attribuer_creneau, generer_tous_les_creneaux
from datetime import date

def test_generer_tous_les_creneaux():
    creneaux = generer_tous_les_creneaux()
    assert len(creneaux) > 0
    assert creneaux[0] == "08:00"
    assert creneaux[1] == "08:15"

def test_attribuer_creneau_urgence():
    res = attribuer_creneau(service_id=1, date_cible=date.today(), priorite='Urgence')
    assert res is None
