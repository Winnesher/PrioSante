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

    return app
