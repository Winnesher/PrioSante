import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.database import db
from app.models import Service, Patient, Consultation
from app.notifications import generer_texte_sms_urgence

def test_patient_properties_civilite_et_telephone_formate():
    p_m = Patient(nom="KOFFI", prenom="Jean", telephone="+22890123456", genre="M")
    p_f = Patient(nom="SOSSOU", prenom="Abla", telephone="+22891929394", genre="F")
    p_a = Patient(nom="AGBE", prenom="Tete", telephone="90112233", genre="Autre")

    assert p_m.civilite == 'M.'
    assert p_f.civilite == 'Mme'
    assert p_a.civilite == 'M. / Mme'

    assert p_m.telephone_formate == '+228 90 12 34 56'
    assert p_f.telephone_formate == '+228 91 92 93 94'
    assert p_a.telephone_formate == '90 11 22 33'

def test_route_maj_localisation_urgence_adresse_et_gps():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            service = Service(nom="Médecine Générale")
            db.session.add(service)
            db.session.commit()

            patient = Patient(nom="DOE", prenom="John", telephone="+22898765432", genre="M")
            db.session.add(patient)
            db.session.commit()

            c = Consultation(
                code_consultation="PS-URG01",
                patient_id=patient.id,
                service_id=service.id,
                priorite="Urgence",
                score=15
            )
            db.session.add(c)
            db.session.commit()

        # Envoi de l'adresse seule
        res1 = client.post('/urgence/PS-URG01/localisation', json={
            'adresse': 'Quartier Bè, près de la pharmacie Saint-Michel'
        })
        assert res1.status_code == 200
        data1 = res1.get_json()
        assert data1['success'] is True
        assert 'Quartier Bè' in data1['adresse']
        assert 'Localisation : Quartier Bè' in data1['sms_text']
        assert 'M. John DOE' in data1['sms_text']

        # Envoi de la position GPS
        res2 = client.post('/urgence/PS-URG01/localisation', json={
            'latitude': 6.1372,
            'longitude': 1.2125
        })
        assert res2.status_code == 200
        data2 = res2.get_json()
        assert data2['success'] is True
        assert data2['latitude'] == 6.1372
        assert data2['longitude'] == 1.2125
        assert 'https://www.google.com/maps?q=6.1372,1.2125' in data2['google_maps_url']
        assert 'Position GPS : https://www.google.com/maps?q=6.1372,1.2125' in data2['sms_text']

        # Vérification en base de données
        with app.app_context():
            c_db = Consultation.query.filter_by(code_consultation="PS-URG01").first()
            assert c_db.adresse_patient == 'Quartier Bè, près de la pharmacie Saint-Michel'
            assert c_db.latitude == 6.1372
            assert c_db.longitude == 1.2125
