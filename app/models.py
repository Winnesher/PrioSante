from datetime import datetime, date
from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    telephone = db.Column(db.String(20), nullable=False)
    date_naissance = db.Column(db.String(20), nullable=True)
    genre = db.Column(db.String(10), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    consultations = db.relationship('Consultation', backref='patient', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'telephone': self.telephone,
            'date_naissance': self.date_naissance,
            'genre': self.genre
        }

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    duree_moyenne_consultation = db.Column(db.Integer, default=15)

    questionnaires = db.relationship('Questionnaire', backref='service', lazy=True)
    medecins = db.relationship('Medecin', backref='service', lazy=True)
    consultations = db.relationship('Consultation', backref='service', lazy=True)

class Questionnaire(db.Model):
    __tablename__ = 'questionnaires'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    symptome_code = db.Column(db.String(50), nullable=False)
    symptome_libelle = db.Column(db.String(200), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)

class Medecin(db.Model):
    __tablename__ = 'medecins'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), nullable=False)
    prenom = db.Column(db.String(80), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    duree_consultation = db.Column(db.Integer, default=15)

    consultations = db.relationship('Consultation', backref='medecin', lazy=True)
    personnels = db.relationship('Personnel', backref='medecin', lazy=True)

class Personnel(db.Model):
    __tablename__ = 'personnel'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False) # 'receptionniste' or 'medecin'
    medecin_id = db.Column(db.Integer, db.ForeignKey('medecins.id'), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Consultation(db.Model):
    __tablename__ = 'consultations'

    id = db.Column(db.Integer, primary_key=True)
    code_consultation = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    medecin_id = db.Column(db.Integer, db.ForeignKey('medecins.id'), nullable=True)
    
    score = db.Column(db.Integer, nullable=False, default=0)
    priorite = db.Column(db.String(20), nullable=False) # 'Faible', 'Moyenne', 'Élevée', 'Urgence'
    symptomes_declares = db.Column(db.Text, nullable=True) # JSON list or string of symptoms
    
    date_consultation = db.Column(db.Date, default=date.today, nullable=False)
    heure_prevue = db.Column(db.String(10), nullable=True) # '08:15'
    
    # Statuts : 'en_attente', 'arrive', 'en_consultation', 'termine', 'en_retard', 'absent', 'redirection_urgence'
    statut = db.Column(db.String(30), default='en_attente', nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    notifications = db.relationship('Notification', backref='consultation', lazy=True)
    logs_retard = db.relationship('LogRetard', backref='consultation', lazy=True)

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    type_envoi = db.Column(db.String(20), default='SMS') # SMS / USSD
    destinataire = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    statut = db.Column(db.String(20), default='simule_envoye')
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)

class LogRetard(db.Model):
    __tablename__ = 'logs_retard'

    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    minutes_retard = db.Column(db.Integer, nullable=False)
    action_prise = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
