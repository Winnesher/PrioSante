from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.database import db
from app.models import Personnel, Consultation, LogRetard, Notification
from app.planning import gerer_retard_patient, attribuer_creneau
from app.notifications import envoyer_notification_simulee
from app import limiter

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

def staff_required(role=None):
    """Décorateur d'authentification pour les comptes du personnel."""
    def decorator(f):
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash("Veuillez vous connecter pour accéder au tableau de bord.", "warning")
                return redirect(url_for('staff.login'))
            if role and session.get('role') != role and session.get('role') != 'admin':
                flash("Accès non autorisé pour votre rôle.", "danger")
                return redirect(url_for('staff.dashboard'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@staff_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = Personnel.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f"Bienvenue, {user.username} ({'Réceptionniste' if user.role == 'receptionniste' else 'Médecin'})", "success")
            return redirect(url_for('staff.dashboard'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")

    return render_template('staff/login.html')

@staff_bp.route('/logout')
def logout():
    session.clear()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for('staff.login'))

@staff_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('staff.login'))

    today = date.today()
    # Récupérer toutes les consultations du jour triées par priorité puis par heure
    consultations = Consultation.query.filter_by(date_consultation=today).all()
    
    # Tri personnalisé : Urgence en haut, puis Élevée, Moyenne, Faible, puis par heure
    priority_order = {'Urgence': 0, 'Élevée': 1, 'Moyenne': 2, 'Faible': 3}
    consultations = sorted(
        consultations,
        key=lambda c: (priority_order.get(c.priorite, 4), c.heure_prevue or '99:99')
    )
    
    role = session.get('role')
    # Récupère le nom via la relation Medecin (Personnel n'a pas de champ nom propre)
    user_obj = db.session.get(Personnel, session.get('user_id'))
    if user_obj and user_obj.medecin:
        user_name = user_obj.medecin.nom
    else:
        user_name = session.get('username', 'Inconnu')

    # Compteurs statistiques du jour
    stats = {
        'total': len(consultations),
        'en_attente': len([c for c in consultations if c.statut == 'en_attente']),
        'arrive': len([c for c in consultations if c.statut == 'arrive']),
        'en_consultation': len([c for c in consultations if c.statut == 'en_consultation']),
        'termine': len([c for c in consultations if c.statut == 'termine']),
        'urgences': len([c for c in consultations if c.priorite == 'Urgence'])
    }

    if role == 'receptionniste':
        return render_template('staff/dashboard_reception.html', consultations=consultations, stats=stats, user_name=user_name)
    else:
        return render_template('staff/dashboard_medecin.html', consultations=consultations, stats=stats, user_name=user_name)

@staff_bp.route('/action/<int:consultation_id>/<string:action>', methods=['POST'])
def action_consultation(consultation_id, action):
    if 'user_id' not in session:
        return redirect(url_for('staff.login'))
        
    role = session.get('role')
    consultation = Consultation.query.get_or_404(consultation_id)

    if action == 'arrive':
        consultation.statut = 'arrive'
        flash(f"Patient {consultation.patient.nom} {consultation.patient.prenom} marqué comme ARRIVÉ.", "success")
    elif action == 'en_consultation':
        if role != 'medecin' and role != 'admin':
            flash("Seul un médecin peut démarrer une consultation.", "danger")
            return redirect(url_for('staff.dashboard'))
        consultation.statut = 'en_consultation'
        flash(f"Consultation démarrée pour le patient {consultation.patient.nom}.", "info")
    elif action == 'termine':
        if role != 'medecin' and role != 'admin':
            flash("Seul un médecin peut marquer une consultation comme terminée.", "danger")
            return redirect(url_for('staff.dashboard'))
        consultation.statut = 'termine'
        flash(f"Consultation terminée pour M. / Mme {consultation.patient.nom}.", "success")
    elif action == 'retard_signale':
        minutes = request.form.get('minutes_retard', type=int, default=15)
        res = gerer_retard_patient(consultation, minutes)
        envoyer_notification_simulee(consultation, type_msg='RECALCUL')
        flash(f"Retard géré : {res}", "warning")
    elif action == 'absent':
        consultation.statut = 'absent'
        flash(f"Patient marqué comme ABSENT. Son créneau est libéré.", "secondary")

    db.session.commit()
    return redirect(url_for('staff.dashboard'))
