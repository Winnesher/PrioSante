# PrioSante

PrioSante est une application web légère développée en Python avec Flask pour la gestion et la priorisation des rendez‑vous médicaux. Elle fournit :
- une interface patient pour inscription, demande et consultation de RDV ;
- un tableau de bord pour le personnel (réception, médecin) pour gérer la file, marquer les arrivées, retards et consultations ;
- un moteur de scoring pour prioriser les consultations selon les symptômes ;
- un module de planning générant et attribuant des créneaux ;
- un système simple de notifications (persistées en base).

Cette documentation explique l'installation, la configuration, l'exécution et les points importants du projet.

## Badges recommandés
- Build: (GitHub Actions)
- Tests: (pytest)
- Licence: MIT

## Table des matières
- Installation
- Configuration
- Base de données & Seed
- Exécution
- Tests
- Structure du projet
- Sécurité & bonnes pratiques
- Licence

## Installation

Pré-requis
- Python 3.10+ recommandé
- Git

Étapes

```bash
# depuis la racine du projet
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

L'application utilise par défaut une base SQLite locale située dans `instance/priosante.sqlite` et une `SECRET_KEY` de développement. Pour la production, définissez les variables d'environnement suivantes :

- `PRIOSANTE_SECRET_KEY` — clé secrète Flask (remplace la valeur par défaut)
- `DATABASE_URL` — (optionnel) URI SQLAlchemy (ex. `sqlite:///instance/priosante.sqlite` ou `postgresql://user:pass@host/db`)

Exemple (macOS / Linux) :

```bash
export PRIOSANTE_SECRET_KEY="change_me_to_a_secure_value"
export DATABASE_URL="sqlite:///instance/priosante.sqlite"
```

Notes :
- Le dossier `instance/` est ignoré par Git et contient la base locale et fichiers runtime.
- Ne commitez jamais de secrets (fichiers `.env`, clés privées, DB réelles).

## Base de données & Seed

Pour initialiser et peupler la base de données de test :

```bash
python seed.py
```

`seed.py` crée des services, questionnaires, personnel, médecins et patients de démonstration (identifiants de démonstration visibles dans `seed.py`). Utilisez-les uniquement en environnement de développement.

## Exécution

Mode développement :

```bash
python run.py
# puis ouvrir http://127.0.0.1:5000
```

Pour un déploiement production, exécutez derrière un serveur WSGI (gunicorn) et fournissez `PRIOSANTE_SECRET_KEY` et `DATABASE_URL` :

```bash
gunicorn -w 4 "run:create_app()" -b 0.0.0.0:8000
```

## Tests

Les tests utilisent `pytest` :

```bash
pytest -q
```

Si nécessaire, activez un environnement propre et installez les dépendances avant d'exécuter les tests.

## Structure du projet (résumé)

- `run.py` : point d'entrée pour lancer l'application en dev.
- `requirements.txt` : dépendances Python.
- `seed.py` : script d'initialisation et de seed DB.
- `instance/` : DB runtime et fichiers locaux (IGNORÉ par Git).
- `app/` : package principal
  - `app/__init__.py` : factory `create_app()`
  - `app/database.py` : instance SQLAlchemy
  - `app/models.py` : définitions des modèles (Patient, Consultation, Personnel, etc.)
  - `app/planning.py` : génération et attribution des créneaux
  - `app/scoring.py` : barème et évaluation de priorité
  - `app/notifications.py` : écriture des notifications en base
  - `app/routes/` : blueprints `patient`, `staff`, `api`
- `tests/` : tests unitaires (planning, scoring, rôles staff)

## Sécurité & bonnes pratiques

- Ne pas exposer `instance/priosante.sqlite` ou tout fichier contenant des données sensibles.
- Remplacer la `SECRET_KEY` de développement par une valeur sûre en production.
- Si vous utilisez HTTPS, terminez TLS au niveau du load‑balancer / reverse proxy.
- Remplacer SQLite par Postgres/MySQL pour la production.

## Points d'attention (pour les contributeurs)

- `seed.py` contient des identifiants de démonstration — changez/retirez-les avant publication publique.
- Vérifiez les endpoints d'API dans `app/routes/api.py` avant d'exposer des données sensibles.
- Ajouter des tests supplémentaires pour la logique métier avant changement majeur (scoring / planning).

## Contribuer

1. Fork du dépôt
2. Créer une branche `feature/ma-fonctionnalite`
3. Ouvrir une Pull Request décrivant les changements

## Licence

Ce projet est sous licence MIT — voir le fichier `LICENSE`.

---

Si tu veux, je peux :
- ajouter des badges CI/tests au README,
- créer un fichier `.env.example`,
- ou créer le dépôt distant GitHub et pousser (si tu confirmes le nom et la visibilité).
