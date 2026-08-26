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

        # 1. Création de tous les 17 services hospitaliers (Top 5 les plus demandés + catalogue complet)
        SERVICES_DATA = [
            # Top 5 les plus demandés
            {
                "nom": "Médecine Générale",
                "description": "Consultations médicales générales, orientation et suivi des pathologies courantes.",
                "duree": 20
            },
            {
                "nom": "Pédiatrie",
                "description": "Soins et suivi médical spécialisé des enfants, des nourrissons et des adolescents.",
                "duree": 15
            },
            {
                "nom": "Gynécologie & Obstétrique",
                "description": "Santé de la femme, suivi de grossesse, accouchement, maternité et contraception.",
                "duree": 20
            },
            {
                "nom": "Cardiologie",
                "description": "Prévention, diagnostic et traitement des maladies du cœur, hypertension et circulation.",
                "duree": 20
            },
            {
                "nom": "Dermatologie & Vénéréologie",
                "description": "Diagnostic et soins des affections de la peau, cheveux, ongles et allergies cutanées.",
                "duree": 15
            },
            # Catalogue complet des spécialités hospitalières
            {
                "nom": "Ophtalmologie",
                "description": "Examen de la vue, chirurgie réfractive, glaucome et maladies oculaires.",
                "duree": 15
            },
            {
                "nom": "Oto-Rhino-Laryngologie (ORL)",
                "description": "Prise en charge des troubles des oreilles, du nez, de la gorge, des sinus et de la voix.",
                "duree": 15
            },
            {
                "nom": "Neurologie",
                "description": "Traitements des maladies du système nerveux central, migraines, vertiges et suivi AVC.",
                "duree": 25
            },
            {
                "nom": "Orthopédie & Traumatologie",
                "description": "Soins des os, articulations, fractures, entorses, prothèses et colonne vertébrale.",
                "duree": 20
            },
            {
                "nom": "Gastro-Entérologie",
                "description": "Affections de l'appareil digestif, estomac, foie, pancréas, hépatites et intestins.",
                "duree": 20
            },
            {
                "nom": "Pneumologie",
                "description": "Maladies des poumons, asthme, bronchite chronique, toux chronique et voies respiratoires.",
                "duree": 20
            },
            {
                "nom": "Endocrinologie & Diabétologie",
                "description": "Gestion du diabète, des troubles de la thyroïde, de l'obésité et des hormones.",
                "duree": 20
            },
            {
                "nom": "Odontologie & Stomatologie",
                "description": "Soins dentaires, chirurgie buccale, santé des gencives et prothèses.",
                "duree": 15
            },
            {
                "nom": "Urologie",
                "description": "Diagnostic et chirurgie de l'appareil urinaire masculin et féminin, reins et prostate.",
                "duree": 20
            },
            {
                "nom": "Rhumatologie",
                "description": "Traitements des douleurs articulaires, arthrose, ostéoporose, tendinites et rhumatismes.",
                "duree": 20
            },
            {
                "nom": "Néphrologie",
                "description": "Prévention, diagnostic et suivi des insuffisances rénales et hypertension rénale.",
                "duree": 20
            },
            {
                "nom": "Psychiatrie & Santé Mentale",
                "description": "Consultations spécialisées en santé mentale, anxieté, dépression et soutien psychologique.",
                "duree": 30
            }
        ]

        services_crees = {}
        for sdata in SERVICES_DATA:
            service = Service(
                nom=sdata["nom"],
                description=sdata["description"],
                duree_moyenne_consultation=sdata["duree"]
            )
            db.session.add(service)
            db.session.flush()
            services_crees[sdata["nom"]] = service

            # Création du questionnaire clinique pour chaque service
            for code, qdata in BAREME_SYMPTOMS.items():
                q = Questionnaire(
                    service_id=service.id,
                    symptome_code=code,
                    symptome_libelle=qdata['libelle'],
                    points=qdata['points']
                )
                db.session.add(q)

        db.session.commit()
        service_mg = services_crees["Médecine Générale"]

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
                "naissance": "1995-03-14",
                "symptomes": ["toux_rhume", "fievre_legere"], # Score 2 (Faible)
                "statut": "en_attente"
            },
            {
                "nom": "MENSAH", "prenom": "Yao", "tel": "+228 91 22 33 44",
                "naissance": "1988-07-22",
                "symptomes": ["fievre_elevee", "douleur_moderee"], # Score 6 (Moyenne)
                "statut": "arrive"
            },
            {
                "nom": "LAWSON", "prenom": "Kodjo", "tel": "+228 92 33 44 55",
                "naissance": "2001-11-05",
                "symptomes": ["difficulte_respirer", "douleur_moderee"], # Score 10 (Élevée)
                "statut": "en_attente"
            },
            {
                "nom": "ADZOH", "prenom": "Afiwa", "tel": "+228 93 44 55 66",
                "naissance": "1972-01-30",
                "symptomes": ["douleur_thoracique", "fievre_elevee"], # Score 19 (Red Flag Urgence Critiques)
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
                date_naissance=pdata["naissance"],
                genre="M" if idx % 2 != 0 else "F"
            )
            db.session.add(patient)
            db.session.commit()

            eval_res = evaluer_score_et_priorite(pdata["symptomes"])
            code_unique = f"PS-DEMO0{idx}"
            resultat_creneau = attribuer_creneau(service_mg.id, today, eval_res["priorite"])
            date_cons, heure = (resultat_creneau[0], resultat_creneau[1]) if resultat_creneau else (today, None)

            consultation = Consultation(
                code_consultation=code_unique,
                patient_id=patient.id,
                service_id=service_mg.id,
                medecin_id=medecin.id,
                score=eval_res["score"],
                priorite=eval_res["priorite"],
                symptomes_declares=", ".join(eval_res["symptomes_details"]),
                date_consultation=date_cons,
                heure_prevue=heure,
                statut=pdata["statut"]
            )
            db.session.add(consultation)
            db.session.commit()
            idx += 1

        db.session.commit()
        print("[SUCCESS] Base de donnees PrioSante initialisee avec succes !")
        print("   - Service : Medecine Generale")
        print("   - Compte Reception : reception1 / demo123")
        print("   - Compte Medecin : dr.kognon / demo123")
        print("   - 4 consultations de test generees (Faible, Moyenne, Elevee, Urgence)")

if __name__ == "__main__":
    seed_database()
