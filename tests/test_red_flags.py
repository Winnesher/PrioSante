import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Consultation, Patient
from app.scoring import evaluer_score_et_priorite, BAREME_SYMPTOMS

def test_douleur_thoracique_declenche_red_flag_et_urgence():
    result = evaluer_score_et_priorite(['douleur_thoracique'])
    assert result['score'] == 15
    assert result['priorite'] == 'Urgence'
    assert result['is_red_flag'] is True

def test_signes_avc_declenche_red_flag_et_urgence():
    result = evaluer_score_et_priorite(['signes_avc'])
    assert result['score'] == 15
    assert result['priorite'] == 'Urgence'
    assert result['is_red_flag'] is True

def test_inscription_red_flag_persiste_en_base_et_api():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            service = Service(nom="Médecine Générale")
            db.session.add(service)
            db.session.commit()
            service_id = service.id

        # Inscription patient avec symptôme Red Flag (Douleur thoracique)
        res = client.post('/inscription', data={
            'nom': 'URGENT',
            'prenom': 'Patient',
            'telephone': '+22899999999',
            'date_naissance': '1980-01-01',
            'genre': 'M',
            'service_id': str(service_id),
            'symptomes': ['douleur_thoracique'],
        })

        assert res.status_code == 302
        assert '/urgence/' in res.headers['Location']

        with app.app_context():
            consultation = Consultation.query.first()
            assert consultation is not None
            assert consultation.priorite == 'Urgence'
            assert consultation.is_red_flag is True
            assert consultation.heure_prevue is None  # Aucun créneau attribué pour l'urgence

        # Test de l'API /api/queue-status (avec authentification session staff)
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        api_res = client.get('/api/queue-status')
        assert api_res.status_code == 200
        json_data = api_res.get_json()
        assert json_data['has_urgences'] is True
        assert json_data['urgences_count'] == 1
        assert json_data['queue'][0]['is_red_flag'] is True
