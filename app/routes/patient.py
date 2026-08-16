import re
import secrets
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")


def bornes_date_naissance():
    """Retourne (min, max) autorisés pour la date de naissance : pas aujourd'hui ni le futur, pas plus de 120 ans."""
    date_max = date.today() - timedelta(days=1)
    date_min = date_max.replace(year=date_max.year - 120)
    return date_min.isoformat(), date_max.isoformat()
from app.database import db
from app.models import Service, Patient, Consultation
from app.scoring import BAREME_SYMPTOMS, evaluer_score_et_priorite
from app.planning import attribuer_creneau, service_est_ouvert
from app.notifications import envoyer_notification_simulee
from app import limiter

patient_bp = Blueprint('patient', __name__)

GENRES_AUTORISES = {'M', 'F', 'Autre'}

@patient_bp.route('/', methods=['GET'])
def index():
    return render_template('landing.html', service_ouvert=service_est_ouvert())

@patient_bp.route('/inscription', methods=['GET', 'POST'])
def inscription():
    services = Service.query.all()
    date_min_naissance, date_max_naissance = bornes_date_naissance()

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        telephone = request.form.get('telephone', '').strip()
        date_naissance = request.form.get('date_naissance', '')
        genre = request.form.get('genre', 'Autre')
        service_id = request.form.get('service_id', type=int)

        selected_symptoms = request.form.getlist('symptomes')

        if not nom or not prenom or not telephone or not service_id or not date_naissance:
            flash("Veuillez remplir tous les champs obligatoires du formulaire.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

        if not NAME_PATTERN.match(nom) or not NAME_PATTERN.match(prenom):
            flash("Le Nom et le Prénom ne doivent contenir que des lettres.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

        if date_naissance and not (date_min_naissance <= date_naissance <= date_max_naissance):
            flash("Date de naissance invalide.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

        if not selected_symptoms:
            flash("Veuillez cocher au moins un symptôme avant de valider votre demande.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

        service = db.session.get(Service, service_id) if service_id is not None else None
        if not service:
            flash("Le service sélectionné est invalide. Veuillez réessayer.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

        if genre not in GENRES_AUTORISES:
            genre = 'Autre'

        # Créer ou retrouver le patient : un même numéro peut être partagé par
        # plusieurs personnes (téléphone familial), donc on ne considère qu'il
        # s'agit du même patient que si le nom ET le prénom correspondent aussi
        # — sinon on créerait un dossier fusionné entre deux personnes distinctes.
        patient = Patient.query.filter_by(telephone=telephone, nom=nom, prenom=prenom).first()
        if not patient:
            patient = Patient(
                nom=nom,
                prenom=prenom,
                telephone=telephone,
                date_naissance=date_naissance,
                genre=genre
            )
            db.session.add(patient)
            db.session.commit()
        else:
            patient.date_naissance = date_naissance
            patient.genre = genre
            db.session.commit()

        # Évaluation clinique du score
        eval_result = evaluer_score_et_priorite(selected_symptoms)
        score = eval_result['score']
        priorite = eval_result['priorite']
        symptomes_details_str = ", ".join(eval_result['symptomes_details']) if eval_result['symptomes_details'] else "Aucun symptôme spécifique déclaré"
        
        # Attribution du créneau (et de la date, reportée au lendemain si la
        # journée est pleine ou déjà terminée)
        date_aujourdhui = date.today()
        resultat_creneau = attribuer_creneau(service_id, date_aujourdhui, priorite)
        if resultat_creneau is None:
            date_consultation, heure_prevue = date_aujourdhui, None
        else:
            date_consultation, heure_prevue = resultat_creneau

        # Code de consultation unique (ex: PS-A9F32)
        code_unique = f"PS-{secrets.token_hex(3).upper()}"

        statut_initial = 'redirection_urgence' if priorite == 'Urgence' else 'en_attente'

        consultation = Consultation(
            code_consultation=code_unique,
            patient_id=patient.id,
            service_id=service_id,
            score=score,
            priorite=priorite,
            symptomes_declares=symptomes_details_str,
            date_consultation=date_consultation,
            heure_prevue=heure_prevue,
            statut=statut_initial
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        # Envoi de la notification SMS simulée
        envoyer_notification_simulee(consultation, type_msg='CONFIRMATION')
        
        if priorite == 'Urgence':
            return redirect(url_for('patient.urgence', code=code_unique))
        else:
            return redirect(url_for('patient.confirmation', code=code_unique))

    return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                            date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                            service_ouvert=service_est_ouvert())

@patient_bp.route('/confirmation/<code>')
def confirmation(code):
    consultation = Consultation.query.filter_by(code_consultation=code).first_or_404()
    return render_template('patient/confirmation.html', consultation=consultation)

@patient_bp.route('/urgence/<code>')
def urgence(code):
    consultation = Consultation.query.filter_by(code_consultation=code).first_or_404()
    return render_template('patient/urgence.html', consultation=consultation)

@patient_bp.route('/mon-rdv', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=['POST'])
def mon_rdv():
    consultation = None
    recherche_effectuee = False
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        recherche_effectuee = True
        if query:
            # Chercher par code consultation ou par numéro de téléphone
            consultation = Consultation.query.join(Patient).filter(
                (Consultation.code_consultation == query.upper()) | 
                (Patient.telephone == query)
            ).order_by(Consultation.id.desc()).first()

    return render_template('patient/mon_rdv.html', consultation=consultation, recherche_effectuee=recherche_effectuee)
