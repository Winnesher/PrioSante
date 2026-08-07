import os
from flask import Flask
from app.database import db

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='priosante-dev-secret-key-phy330-ul',
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'priosante.sqlite')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    # Assurer l'existence du dossier instance
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

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
