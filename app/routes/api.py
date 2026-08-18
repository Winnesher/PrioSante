from datetime import date
from functools import wraps
from flask import Blueprint, jsonify, session
from app.models import Consultation, Notification

api_bp = Blueprint('api', __name__, url_prefix='/api')


def staff_session_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'unauthorized'}), 401
        return f(*args, **kwargs)
    return wrapped


@api_bp.route('/queue-status')
@staff_session_required
def queue_status():
    today = date.today()
    consultations = Consultation.query.filter_by(date_consultation=today).all()
    
    data = []
    for c in consultations:
        data.append({
            'code': c.code_consultation,
            'heure': c.heure_prevue,
            'priorite': c.priorite,
            'statut': c.statut,
            'service': c.service.nom if c.service else ''
        })
    return jsonify({'total': len(data), 'queue': data})

@api_bp.route('/notifications-log')
@staff_session_required
def notifications_log():
    notifs = Notification.query.order_by(Notification.id.desc()).limit(20).all()
    data = [{
        'id': n.id,
        'destinataire': n.destinataire,
        'message': n.message,
        'statut': n.statut,
        'date_envoi': n.date_envoi.strftime('%H:%M:%S')
    } for n in notifs]
    return jsonify(data)
