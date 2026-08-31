import re
import secrets
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import IntegrityError

NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")
MAX_TENTATIVES_CRENEAU = 3


# Seuil minimum de récence : une date de naissance à moins de 7 jours d'aujourd'hui
# n'est pas réaliste pour une inscription (même pour un nouveau-né en Pédiatrie).
MIN_JOURS_AVANT_AUJOURDHUI = 7


def bornes_date_naissance():
    """Retourne (min, max) autorisés pour la date de naissance : pas aujourd'hui, le futur ni
    une date trop récente (< 7 jours), pas plus de 120 ans."""
    today = date.today()
    date_max = today - timedelta(days=MIN_JOURS_AVANT_AUJOURDHUI)
    try:
        date_min = today.replace(year=today.year - 120)
    except ValueError:
        date_min = today.replace(month=2, day=28, year=today.year - 120)
    return date_min.isoformat(), date_max.isoformat()
from app.database import db
from app.models import Service, Patient, Consultation
from app.scoring import BAREME_SYMPTOMS, evaluer_score_et_priorite
from app.planning import attribuer_creneau, service_est_ouvert
from app.notifications import envoyer_notification_simulee, generer_texte_sms_urgence
from app import limiter, csrf

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
        symptome_libre = request.form.get('symptome_libre', '').strip()

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
            flash("Date de naissance invalide : la date ne peut pas être aujourd'hui, dans le futur, dater de moins de 7 jours, ou dépasser 120 ans.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

        if not selected_symptoms and not symptome_libre:
            flash("Veuillez cocher au moins un symptôme ou décrire vos symptômes dans le champ prévu avant de valider votre demande.", "danger")
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

        # Évaluation clinique du score (combinaison cases cochées + saisie libre)
        eval_result = evaluer_score_et_priorite(selected_symptoms, symptome_libre)
        score = eval_result['score']
        priorite = eval_result['priorite']
        is_red_flag = eval_result.get('is_red_flag', False)
        symptomes_details_str = ", ".join(eval_result['symptomes_details']) if eval_result['symptomes_details'] else "Aucun symptôme spécifique déclaré"
        
        # Code de consultation unique (ex: PS-A9F32)
        code_unique = f"PS-{secrets.token_hex(3).upper()}"
        statut_initial = 'redirection_urgence' if priorite == 'Urgence' else 'en_attente'
        date_aujourdhui = date.today()

        # Attribution du créneau (et de la date, reportée au lendemain si la
        # journée est pleine ou déjà terminée), avec nouvelle tentative en cas
        # de collision : si deux patients obtiennent le même créneau au même
        # instant, la contrainte d'unicité en base rejette le second, qui se
        # voit alors attribuer le créneau libre suivant, de façon transparente.
        consultation = None
        for _tentative in range(MAX_TENTATIVES_CRENEAU):
            resultat_creneau = attribuer_creneau(service_id, date_aujourdhui, priorite)
            if resultat_creneau is None:
                date_consultation, heure_prevue = date_aujourdhui, None
            else:
                date_consultation, heure_prevue = resultat_creneau

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
            try:
                db.session.commit()
                break
            except IntegrityError:
                db.session.rollback()
                consultation = None
        else:
            flash("Le service est actuellement très sollicité, veuillez réessayer dans un instant.", "danger")
            return render_template('patient/inscription.html', services=services, bareme=BAREME_SYMPTOMS,
                                    date_min_naissance=date_min_naissance, date_max_naissance=date_max_naissance,
                                    service_ouvert=service_est_ouvert())

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

@patient_bp.route('/urgence/<code>/localisation', methods=['POST'])
@csrf.exempt
def maj_localisation_urgence(code):
    consultation = Consultation.query.filter_by(code_consultation=code).first_or_404()
    data = request.get_json() or {}
    
    adresse = data.get('adresse')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if adresse is not None:
        consultation.adresse_patient = str(adresse).strip() if str(adresse).strip() else None
        
    if latitude is not None and longitude is not None:
        try:
            consultation.latitude = float(latitude)
            consultation.longitude = float(longitude)
        except (ValueError, TypeError):
            pass
            
    db.session.commit()
    
    # Générer le texte SMS simulé actualisé
    sms_text = generer_texte_sms_urgence(consultation)
    
    return jsonify({
        'success': True,
        'message': 'Localisation enregistrée avec succès.',
        'adresse': consultation.adresse_patient,
        'latitude': consultation.latitude,
        'longitude': consultation.longitude,
        'sms_text': sms_text,
        'google_maps_url': f"https://www.google.com/maps?q={consultation.latitude},{consultation.longitude}" if (consultation.latitude is not None and consultation.longitude is not None) else None
    })

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
