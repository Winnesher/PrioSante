# Importation des modules nécessaires
from datetime import datetime, date  # Pour gérer les dates et heures
from app.database import db  # Instance SQLAlchemy pour la base de données
from werkzeug.security import generate_password_hash, check_password_hash  # Pour hacher et vérifier les mots de passe

# =============================================================================
# MODÈLE PATIENT : Représente un patient qui vient consulter
# =============================================================================
class Patient(db.Model):
    """
    Modèle représentant un patient qui vient consulter.
    """
    __tablename__ = 'patients'  # Nom de la table en base de données

    # Champs d'identification
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique automatique (1, 2, 3...)
    nom = db.Column(db.String(80), nullable=False)  # Nom du patient (obligatoire)
    prenom = db.Column(db.String(80), nullable=False)  # Prénom du patient (obligatoire)
    telephone = db.Column(db.String(20), nullable=False)  # Numéro de téléphone (obligatoire)
    date_naissance = db.Column(db.String(20), nullable=True)  # Date de naissance (optionnel)
    genre = db.Column(db.String(10), nullable=True)  # Genre : M, F ou Autre (optionnel)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création automatique

    # Relation : un patient peut avoir plusieurs consultations
    consultations = db.relationship('Consultation', backref='patient', lazy=True)

    # Méthode pour convertir l'objet Patient en dictionnaire (utile pour l'API JSON)
    def to_dict(self):
        """
        Convertit l'objet Patient en dictionnaire pour une représentation JSON.
        """
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'telephone': self.telephone,
            'date_naissance': self.date_naissance,
            'genre': self.genre
        }

# =============================================================================
# MODÈLE SERVICE : Représente un service médical (ex: Médecine Générale)
# =============================================================================
class Service(db.Model):
    __tablename__ = 'services'  # Nom de la table en base de données

    # Champs du service
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    nom = db.Column(db.String(100), nullable=False, unique=True)  # Nom du service (unique, ex: "Médecine Générale")
    description = db.Column(db.Text, nullable=True)  # Description du service
    duree_moyenne_consultation = db.Column(db.Integer, default=15)  # Durée moyenne en minutes (15 par défaut)

    # Relations : un service a plusieurs questionnaires, médecins et consultations
    questionnaires = db.relationship('Questionnaire', backref='service', lazy=True)
    medecins = db.relationship('Medecin', backref='service', lazy=True)
    consultations = db.relationship('Consultation', backref='service', lazy=True)

# =============================================================================
# MODÈLE QUESTIONNAIRE : Représente un symptôme avec son barème de points
# =============================================================================
class Questionnaire(db.Model):
    __tablename__ = 'questionnaires'  # Nom de la table en base de données

    # Champs du symptôme
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Clé étrangère vers le service
    symptome_code = db.Column(db.String(50), nullable=False)  # Code unique du symptôme (ex: 'toux_rhume')
    symptome_libelle = db.Column(db.String(200), nullable=False)  # Libellé lisible (ex: 'Toux / rhume')
    points = db.Column(db.Integer, nullable=False, default=0)  # Nombre de points pour ce symptôme

# =============================================================================
# MODÈLE MÉDECIN : Représente un médecin de l'hôpital
# =============================================================================
class Medecin(db.Model):
    __tablename__ = 'medecins'  # Nom de la table en base de données

    # Champs du médecin
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    nom = db.Column(db.String(80), nullable=False)  # Nom du médecin
    prenom = db.Column(db.String(80), nullable=False)  # Prénom du médecin
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Service où il travaille
    duree_consultation = db.Column(db.Integer, default=15)  # Durée personnalisée de consultation (15 min par défaut)

    # Relations : un médecin a plusieurs consultations et peut avoir plusieurs comptes personnel
    consultations = db.relationship('Consultation', backref='medecin', lazy=True)
    personnels = db.relationship('Personnel', backref='medecin', lazy=True)

# =============================================================================
# MODÈLE PERSONNEL : Représente un compte utilisateur (réceptionniste ou médecin)
# =============================================================================
class Personnel(db.Model):
    __tablename__ = 'personnel'  # Nom de la table en base de données

    # Champs du compte utilisateur
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    username = db.Column(db.String(80), unique=True, nullable=False)  # Identifiant de connexion unique
    password_hash = db.Column(db.String(255), nullable=False)  # Mot de passe haché (jamais en clair)
    role = db.Column(db.String(30), nullable=False)  # Rôle : 'receptionniste' ou 'medecin'
    medecin_id = db.Column(db.Integer, db.ForeignKey('medecins.id'), nullable=True)  # Lien vers le médecin (si applicable)

    # Méthodes de gestion sécurisée du mot de passe
    def set_password(self, password):
        """Hache le mot de passe et le stocke dans password_hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie si le mot de passe correspond au hachage stocké"""
        return check_password_hash(self.password_hash, password)

# =============================================================================
# MODÈLE CONSULTATION : Représente un rendez-vous complet
# =============================================================================
class Consultation(db.Model):
    __tablename__ = 'consultations'  # Nom de la table en base de données
    __table_args__ = (
        # Empêche deux consultations distinctes d'occuper le même créneau pour
        # un même service/jour, même en cas d'inscriptions simultanées (les
        # lignes avec heure_prevue=NULL, ex. Urgence, ne sont jamais en conflit
        # entre elles : NULL n'est jamais égal à NULL pour une contrainte SQL).
        db.UniqueConstraint('service_id', 'date_consultation', 'heure_prevue', name='uq_consultation_creneau'),
    )

    # Champs d'identification
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    code_consultation = db.Column(db.String(20), unique=True, nullable=False)  # Code unique pour le patient (ex: 'PS-A9F32')
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)  # Clé étrangère vers le patient
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Clé étrangère vers le service
    medecin_id = db.Column(db.Integer, db.ForeignKey('medecins.id'), nullable=True)  # Clé étrangère vers le médecin (optionnel)
    
    # Champs de scoring médical
    score = db.Column(db.Integer, nullable=False, default=0)  # Score calculé (somme des points des symptômes)
    priorite = db.Column(db.String(20), nullable=False)  # Priorité : 'Faible', 'Moyenne', 'Élevée', 'Urgence'
    symptomes_declares = db.Column(db.Text, nullable=True)  # Liste des symptômes déclarés (texte)

    @property
    def is_red_flag(self):
        """Détermine si la consultation est un Red Flag / Urgence critique."""
        return self.priorite == 'Urgence' or (self.score is not None and self.score > 12)
    
    # Champs de planning
    date_consultation = db.Column(db.Date, default=date.today, nullable=False)  # Date de la consultation
    heure_prevue = db.Column(db.String(10), nullable=True)  # Créneau horaire attribué (ex: '13:40')
    
    # Champs de statut
    # Statuts possibles : 'en_attente', 'arrive', 'en_consultation', 'termine', 'en_retard', 'absent', 'redirection_urgence'
    statut = db.Column(db.String(30), default='en_attente', nullable=False)  # État actuel de la consultation
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)  # Date de création automatique

    # Relations : une consultation a plusieurs notifications et logs de retard
    notifications = db.relationship('Notification', backref='consultation', lazy=True)
    logs_retard = db.relationship('LogRetard', backref='consultation', lazy=True)

# =============================================================================
# MODÈLE NOTIFICATION : Représente un message envoyé au patient (SMS simulé)
# =============================================================================
class Notification(db.Model):
    __tablename__ = 'notifications'  # Nom de la table en base de données

    # Champs de la notification
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)  # Clé étrangère vers la consultation
    type_envoi = db.Column(db.String(20), default='SMS')  # Type d'envoi : 'SMS' ou 'USSD'
    destinataire = db.Column(db.String(20), nullable=False)  # Numéro de téléphone du patient
    message = db.Column(db.Text, nullable=False)  # Contenu du message
    statut = db.Column(db.String(20), default='simule_envoye')  # Statut d'envoi (simulé pour la démo)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow)  # Date d'envoi automatique

# =============================================================================
# MODÈLE LOGRETARD : Historique des retards et actions prises
# =============================================================================
class LogRetard(db.Model):
    __tablename__ = 'logs_retard'  # Nom de la table en base de données

    # Champs du log de retard
    id = db.Column(db.Integer, primary_key=True)  # Identifiant unique
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)  # Clé étrangère vers la consultation
    minutes_retard = db.Column(db.Integer, nullable=False)  # Nombre de minutes de retard
    action_prise = db.Column(db.String(100), nullable=False)  # Description de l'action prise
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Date et heure de l'action
