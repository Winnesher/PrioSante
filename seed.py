import os
import sys
from app import create_app
from app.database import db
from app.models import Service, Questionnaire, Personnel, Medecin, Patient, Consultation
from app.scoring import BAREME_SYMPTOMS, evaluer_score_et_priorite
from app.planning import attribuer_creneau
from datetime import date

def seed_database():
    app = create_app()

    database_url = os.environ.get('DATABASE_URL', '')
    if database_url and not database_url.startswith('sqlite'):
        if os.environ.get('SEED_CONFIRM') != 'yes':
            print("[ERREUR] DATABASE_URL ne pointe pas vers une base SQLite locale.")
            print("         Ce script efface toutes les donnees existantes (db.drop_all()).")
            print("         Si vous etes certain de vouloir reinitialiser cette base,")
            print("         relancez avec la variable d'environnement SEED_CONFIRM=yes.")
            sys.exit(1)

    with app.app_context():
        print("[INFO] Reinitialisation et peuplement de la base de donnees PrioSante...")
        db.drop_all()
        db.create_all()

        # 1. Création du service de Médecine Générale
        service_mg = Service(
            nom="Médecine Générale",
            description="Consultations médicales générales, orientation et suivi des pathologies courantes.",
            duree_moyenne_consultation=15
        )
        db.session.add(service_mg)
        db.session.commit()

        # 2. Création du questionnaire basé sur le barème officiel du document de cadrage
        for code, data in BAREME_SYMPTOMS.items():
            q = Questionnaire(
                service_id=service_mg.id,
                symptome_code=code,
                symptome_libelle=data['libelle'],
                points=data['points']
            )
            db.session.add(q)
        db.session.commit()

        # 3. Création des Médecins
        medecin = Medecin(
            nom="KOGNON",
            prenom="Kokou Romeo",
            service_id=service_mg.id,
            duree_consultation=15
        )
        db.session.add(medecin)
        db.session.commit()

        # 4. Création des comptes du personnel (Réceptionniste & Médecin)
        user_reception = Personnel(
            username="reception1",
            role="receptionniste"
        )
        user_reception.set_password("demo123")

        user_doc = Personnel(
            username="dr.kognon",
            role="medecin",
            medecin_id=medecin.id
        )
        user_doc.set_password("demo123")

        db.session.add(user_reception)
        db.session.add(user_doc)
        db.session.commit()

        # 5. Création de patients et consultations de démonstration (différents cas de figure)
        demo_patients = [
            {
                "nom": "KOUADIO", "prenom": "Ama", "tel": "+228 90 11 22 33",
                "symptomes": ["toux_rhume", "fievre_legere"], # Score 2 (Faible)
                "statut": "en_attente"
            },
            {
                "nom": "MENSAH", "prenom": "Yao", "tel": "+228 91 22 33 44",
                "symptomes": ["fievre_elevee", "douleur_moderee"], # Score 6 (Moyenne)
                "statut": "arrive"
            },
            {
                "nom": "LAWSON", "prenom": "Kodjo", "tel": "+228 92 33 44 55",
                "symptomes": ["difficulte_respirer", "douleur_moderee"], # Score 10 (Élevée)
                "statut": "en_attente"
            },
            {
                "nom": "ADZOH", "prenom": "Afiwa", "tel": "+228 93 44 55 66",
                "symptomes": ["confusion", "fievre_elevee"], # Score 14 (Urgence)
                "statut": "redirection_urgence"
            }
        ]

        idx = 1
        today = date.today()
        for pdata in demo_patients:
            patient = Patient(
                nom=pdata["nom"],
                prenom=pdata["prenom"],
                telephone=pdata["tel"],
                genre="M" if idx % 2 != 0 else "F"
            )
            db.session.add(patient)
            db.session.commit()

            eval_res = evaluer_score_et_priorite(pdata["symptomes"])
            code_unique = f"PS-DEMO0{idx}"
            heure = attribuer_creneau(service_mg.id, today, eval_res["priorite"])

            consultation = Consultation(
                code_consultation=code_unique,
                patient_id=patient.id,
                service_id=service_mg.id,
                medecin_id=medecin.id,
                score=eval_res["score"],
                priorite=eval_res["priorite"],
                symptomes_declares=", ".join(eval_res["symptomes_details"]),
                date_consultation=today,
                heure_prevue=heure,
                statut=pdata["statut"]
            )
            db.session.add(consultation)
            idx += 1

        db.session.commit()
        print("[SUCCESS] Base de donnees PrioSante initialisee avec succes !")
        print("   - Service : Medecine Generale")
        print("   - Compte Reception : reception1 / demo123")
        print("   - Compte Medecin : dr.kognon / demo123")
        print("   - 4 consultations de test generees (Faible, Moyenne, Elevee, Urgence)")

if __name__ == "__main__":
    seed_database()
