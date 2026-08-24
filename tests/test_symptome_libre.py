import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Consultation
from app.scoring import evaluer_score_et_priorite

def test_symptome_libre_seul_score_base():
    # Saisie libre simple sans mot clé critique -> +4 points (Priorité Moyenne)
    res = evaluer_score_et_priorite([], "Ma cheville me fait mal suite à une petite chute")
    assert res['score'] == 4
    assert res['priorite'] == 'Moyenne'
    assert res['is_red_flag'] is False
    assert len(res['symptomes_details']) == 1

def test_symptome_libre_cumul_avec_cases():
    # Case Fièvre légère (+1 pt) + texte libre mal de ventre (+8 pts) -> Total = 9 pts (Élevée)
    res = evaluer_score_et_priorite(['fievre_legere'], "Crampes intenses au bas du ventre")
    assert res['score'] == 1 + 8  # 9 points
    assert res['priorite'] == 'Élevée'
    assert len(res['symptomes_details']) == 2

def test_symptome_libre_red_flag_declenche_urgence():
    # Saisie libre contenant 'morsure serpent' -> Red Flag (+15 pts -> Urgence)
    res = evaluer_score_et_priorite([], "Victime d'une morsure de serpent dans les champs")
    assert res['score'] == 15
    assert res['priorite'] == 'Urgence'
    assert res['is_red_flag'] is True

def test_inscription_avec_symptome_libre_seulement():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            service = Service(nom="Médecine Générale")
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        res = client.post('/inscription', data={
            'nom': 'Symptome',
            'prenom': 'Libre',
            'telephone': '+22891234567',
            'date_naissance': '1995-05-15',
            'genre': 'M',
            'service_id': str(service_id),
            'symptomes': [],
            'symptome_libre': 'Douleur aiguë au genou droit'
        })

        assert res.status_code == 302
        assert '/confirmation/' in res.headers['Location']

        with app.app_context():
            c = Consultation.query.first()
            assert c is not None
            assert c.score == 4
            assert '[Saisie libre patient]' in c.symptomes_declares
