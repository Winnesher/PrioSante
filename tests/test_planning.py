import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Consultation, Patient
from types import SimpleNamespace

from app.planning import (
    attribuer_creneau,
    generer_tous_les_creneaux,
    service_est_ouvert,
    creneau_est_depasse,
    gerer_retard_patient,
)
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

def test_creneau_est_depasse():
    jour = date(2024, 1, 1)
    consultation = SimpleNamespace(heure_prevue="08:00", date_consultation=jour, statut='en_attente')

    avant_la_marge = datetime.strptime("2024-01-01 08:10", "%Y-%m-%d %H:%M")
    apres_la_marge = datetime.strptime("2024-01-01 08:20", "%Y-%m-%d %H:%M")
    assert creneau_est_depasse(consultation, instant=avant_la_marge) is False
    assert creneau_est_depasse(consultation, instant=apres_la_marge) is True

    # Un patient déjà arrivé ou terminé n'est plus "en défaut"
    consultation_arrivee = SimpleNamespace(heure_prevue="08:00", date_consultation=jour, statut='arrive')
    assert creneau_est_depasse(consultation_arrivee, instant=apres_la_marge) is False

    # Une consultation d'un autre jour n'est jamais dépassée par rapport à "instant"
    consultation_demain = SimpleNamespace(heure_prevue="08:00", date_consultation=jour + timedelta(days=1), statut='en_attente')
    assert creneau_est_depasse(consultation_demain, instant=apres_la_marge) is False

def _consultation_de_test(code, jour):
    return Consultation(
        code_consultation=code,
        patient_id=1,
        service_id=1,
        score=1,
        priorite="Faible",
        date_consultation=jour,
        heure_prevue="08:00",
        statut="en_attente",
    )

def test_gerer_retard_patient_replace_en_fin_de_journee():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        jour = date(2024, 1, 1)
        consultation = _consultation_de_test("PS-TESTRETARD1", jour)
        db.session.add(consultation)
        db.session.commit()

        instant_normal = datetime.strptime("2024-01-01 10:00", "%Y-%m-%d %H:%M")
        gerer_retard_patient(consultation, 15, instant=instant_normal)

        assert consultation.statut == 'en_retard'
        assert consultation.date_consultation == jour
        assert datetime.strptime(consultation.heure_prevue, "%H:%M").time() > instant_normal.time()

def test_gerer_retard_patient_journee_terminee_reporte_au_lendemain():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        jour = date(2024, 1, 1)
        consultation = _consultation_de_test("PS-TESTRETARD2", jour)
        db.session.add(consultation)
        db.session.commit()

        instant_tres_tard = datetime.strptime("2024-01-01 20:00", "%Y-%m-%d %H:%M")
        action = gerer_retard_patient(consultation, 15, instant=instant_tres_tard)

        assert consultation.statut == 'en_retard'
        assert consultation.date_consultation == jour + timedelta(days=1)
        assert consultation.heure_prevue == "08:00"
        assert "reporté" in action
