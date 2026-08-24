# =============================================================================
# CONFIGURATION DE LA BASE DE DONNÉES
# =============================================================================

# Importation de Flask-SQLAlchemy
# Flask-SQLAlchemy est une extension qui intègre SQLAlchemy avec Flask
from flask_sqlalchemy import SQLAlchemy

# Création de l'instance SQLAlchemy
# Cette instance 'db' sera utilisée dans tout le projet pour :
# - Définir les modèles (classes Python qui deviennent des tables)
# - Faire des requêtes à la base de données
# - Gérer les transactions (commit, rollback)
db = SQLAlchemy()
