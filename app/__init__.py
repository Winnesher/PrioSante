import os
from datetime import date
from flask import Flask
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.database import db

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri='memory://')


def _resolve_database_uri(app):
    """Lit DATABASE_URL depuis l'environnement (Render fournit un préfixe
    postgres:// que SQLAlchemy 2.x n'accepte plus, il faut le réécrire en
    postgresql+psycopg://). Sans variable d'env, on retombe sur le SQLite
    local historique."""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return f"sqlite:///{os.path.join(app.instance_path, 'priosante.sqlite')}"

    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return database_url


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    is_debug = os.environ.get('FLASK_DEBUG') == '1'

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('PRIOSANTE_SECRET_KEY', 'priosante-dev-secret-key-phy330-ul'),
        SQLALCHEMY_DATABASE_URI=_resolve_database_uri(app),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=not is_debug,
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    if app.config.get('TESTING'):
        app.config['RATELIMIT_ENABLED'] = False
        app.config['WTF_CSRF_ENABLED'] = False

    # Assurer l'existence du dossier instance
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @app.context_processor
    def injecter_annee_courante():
        """Rend l'année courante disponible dans tous les templates, pour que
        la mention de copyright n'ait pas à être mise à jour à la main."""
        return {'annee_courante': date.today().year}

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "font-src 'self' fonts.gstatic.com; "
            "img-src 'self' data: flagcdn.com; "
            "script-src 'self' 'unsafe-inline'"
        )
        return response

    # Enregistrement des Blueprints
    from app.routes.patient import patient_bp
    from app.routes.staff import staff_bp
    from app.routes.api import api_bp

    app.register_blueprint(patient_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()
        _migrer_schema_auto(app)
        if not app.config.get('TESTING'):
            _synchroniser_services_auto(app)

    return app


def _migrer_schema_auto(app):
    """
    Vérifie et ajoute automatiquement les colonnes manquantes (adresse_patient, latitude, longitude)
    sur les bases de données existantes (SQLite/PostgreSQL) pour éviter OperationalError.
    """
    from sqlalchemy import inspect, text
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            if 'consultations' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('consultations')]
                with db.engine.begin() as conn:
                    if 'adresse_patient' not in columns:
                        conn.execute(text("ALTER TABLE consultations ADD COLUMN adresse_patient TEXT"))
                    if 'latitude' not in columns:
                        conn.execute(text("ALTER TABLE consultations ADD COLUMN latitude FLOAT"))
                    if 'longitude' not in columns:
                        conn.execute(text("ALTER TABLE consultations ADD COLUMN longitude FLOAT"))
        except Exception as e:
            app.logger.warning(f"Note de migration automatique de schéma: {e}")


SERVICES_CATALOG = [
    {"nom": "Médecine Générale", "description": "Consultations médicales générales, orientation et suivi des pathologies courantes.", "duree": 20},
    {"nom": "Pédiatrie", "description": "Soins et suivi médical spécialisé des enfants, des nourrissons et des adolescents.", "duree": 15},
    {"nom": "Gynécologie & Obstétrique", "description": "Santé de la femme, suivi de grossesse, accouchement, maternité et contraception.", "duree": 20},
    {"nom": "Cardiologie", "description": "Prévention, diagnostic et traitement des maladies du cœur, hypertension et circulation.", "duree": 20},
    {"nom": "Dermatologie & Vénéréologie", "description": "Diagnostic et soins des affections de la peau, cheveux, ongles et allergies cutanées.", "duree": 15},
    {"nom": "Ophtalmologie", "description": "Examen de la vue, chirurgie réfractive, glaucome et maladies oculaires.", "duree": 15},
    {"nom": "Oto-Rhino-Laryngologie (ORL)", "description": "Prise en charge des troubles des oreilles, du nez, de la gorge, des sinus et de la voix.", "duree": 15},
    {"nom": "Neurologie", "description": "Traitements des maladies du système nerveux central, migraines, vertiges et suivi AVC.", "duree": 25},
    {"nom": "Orthopédie & Traumatologie", "description": "Soins des os, articulations, fractures, entorses, prothèses et colonne vertébrale.", "duree": 20},
    {"nom": "Gastro-Entérologie", "description": "Affections de l'appareil digestif, estomac, foie, pancréas, hépatites et intestins.", "duree": 20},
    {"nom": "Pneumologie", "description": "Maladies des poumons, asthme, bronchite chronique, toux chronique et voies respiratoires.", "duree": 20},
    {"nom": "Endocrinologie & Diabétologie", "description": "Gestion du diabète, des troubles de la thyroïde, de l'obésité et des hormones.", "duree": 20},
    {"nom": "Odontologie & Stomatologie", "description": "Soins dentaires, chirurgie buccale, santé des gencives et prothèses.", "duree": 15},
    {"nom": "Urologie", "description": "Diagnostic et chirurgie de l'appareil urinaire masculin et féminin, reins et prostate.", "duree": 20},
    {"nom": "Rhumatologie", "description": "Traitements des douleurs articulaires, arthrose, ostéoporose, tendinites et rhumatismes.", "duree": 20},
    {"nom": "Néphrologie", "description": "Prévention, diagnostic et suivi des insuffisances rénales et hypertension rénale.", "duree": 20},
    {"nom": "Psychiatrie & Santé Mentale", "description": "Consultations spécialisées en santé mentale, anxieté, dépression et soutien psychologique.", "duree": 30}
]


def _synchroniser_services_auto(app):
    """
    S'assure automatiquement que les 17 services hospitaliers et leurs questionnaires
    existent en base de données (notamment sur Render PostgreSQL).
    """
    from app.models import Service, Questionnaire
    from app.scoring import BAREME_SYMPTOMS
    with app.app_context():
        try:
            services_existants = {s.nom: s for s in Service.query.all()}
            mis_a_jour = False
            for sdata in SERVICES_CATALOG:
                if sdata["nom"] not in services_existants:
                    s = Service(
                        nom=sdata["nom"],
                        description=sdata["description"],
                        duree_moyenne_consultation=sdata["duree"]
                    )
                    db.session.add(s)
                    db.session.flush()
                    services_existants[sdata["nom"]] = s
                    mis_a_jour = True
                    for code, qdata in BAREME_SYMPTOMS.items():
                        q = Questionnaire(
                            service_id=s.id,
                            symptome_code=code,
                            symptome_libelle=qdata['libelle'],
                            points=qdata['points']
                        )
                        db.session.add(q)

            if mis_a_jour:
                db.session.commit()
        except Exception as e:
            app.logger.warning(f"Note de synchronisation des services: {e}")
