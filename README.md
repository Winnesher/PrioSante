# PrioSante

> Projet réalisé dans le cadre de l'UE PHY330, Université de Lomé.

PrioSante est une application web légère développée en Python avec Flask pour la gestion et la priorisation des rendez‑vous médicaux. Elle fournit :
- une interface patient pour inscription, demande et consultation de RDV, disponible en français et en anglais (bascule de langue en un clic) ;
- un tableau de bord pour le personnel (réception, médecin) pour gérer la file, marquer les arrivées, retards et consultations ;
- un moteur de scoring pour prioriser les consultations selon les symptômes ;
- un module de planning générant et attribuant des créneaux ;
- un système simple de notifications (persistées en base).

Cette documentation explique l'installation, la configuration, l'exécution et les points importants du projet.

**Démo en ligne :** [priosante.onrender.com](https://priosante.onrender.com)

## Badges

[![CI](https://github.com/Winnesher/PrioSante/actions/workflows/ci.yml/badge.svg)](https://github.com/Winnesher/PrioSante/actions/workflows/ci.yml)
[![Licence: MIT](https://img.shields.io/badge/Licence-MIT-blue.svg)](LICENSE)

## Table des matières
- Installation
- Configuration
- Base de données & Seed
- Exécution
- Tests
- Structure du projet
- Déploiement (Render)
- CI/CD
- Sécurité & bonnes pratiques
- Points d'attention (pour les contributeurs)
- Limites connues
- Équipe
- Contribuer
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

L'application utilise par défaut une base SQLite locale située dans `instance/priosante.sqlite` et une `SECRET_KEY` de développement. Copiez `.env.example` en `.env` pour voir la liste commentée des variables. Pour la production, définissez :

- `PRIOSANTE_SECRET_KEY` : clé secrète Flask (remplace la valeur par défaut, utilisée pour signer les sessions et les jetons CSRF)
- `DATABASE_URL` : URI de connexion (ex. `postgresql://user:pass@host/db` ; Render fournit automatiquement une URL `postgres://`, réécrite en interne vers le driver `psycopg`)
- `FLASK_DEBUG` : `1` pour activer le mode debug en local uniquement (jamais en production : le débogueur Werkzeug permet l'exécution de code arbitraire)
- `PORT` : port d'écoute (fourni automatiquement par Render)

Exemple (macOS / Linux) :

```bash
export PRIOSANTE_SECRET_KEY="change_me_to_a_secure_value"
export FLASK_DEBUG=1
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
gunicorn run:app -b 0.0.0.0:8000
```

Un seul worker est utilisé volontairement (pas de `-w`), y compris sur Render : le rate-limiting (`Flask-Limiter`) est stocké en mémoire du processus, pas dans un service partagé. Avec plusieurs workers, chacun aurait son propre compteur et la limite réelle deviendrait `N × la valeur configurée`. Voir la section [Limites connues](#limites-connues).

## Tests

Les tests utilisent `pytest` (16 tests répartis sur 4 fichiers : scoring, planning, rôles/accès staff, routes patient) :

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
- `tests/` : tests unitaires (`test_scoring.py`, `test_planning.py`, `test_staff_roles.py`, `test_patient_routes.py`)
- `render.yaml` : Blueprint Render (service web + base PostgreSQL)
- `.github/workflows/ci.yml` : pipeline CI/CD (tests puis déploiement gaté)
- `.env.example` : variables d'environnement documentées

## Déploiement (Render)

Le projet est prêt pour un déploiement sur [Render](https://render.com) via le Blueprint `render.yaml` à la racine, qui décrit :
- un service web Python (build `pip install -r requirements.txt`, démarrage `gunicorn run:app`) ;
- une base PostgreSQL managée, liée automatiquement via `DATABASE_URL`.

Étapes :
1. Créer un compte Render et connecter le dépôt GitHub.
2. Dans le dashboard Render, choisir "New Blueprint" et sélectionner ce dépôt : `render.yaml` est détecté automatiquement.
3. Une fois le service créé, copier l'URL du **Deploy Hook** (Settings du service web) et l'ajouter comme secret GitHub `RENDER_DEPLOY_HOOK_URL` (voir section CI/CD ci-dessous).
4. Peupler la base de démonstration une seule fois via le Shell Render du service :
   ```bash
   SEED_CONFIRM=yes python seed.py
   ```

## CI/CD

Un pipeline GitHub Actions (`.github/workflows/ci.yml`) s'exécute à chaque push / pull request :
1. **Job `test`** : installe les dépendances et lance `pytest -q`.
2. **Job `deploy`** (uniquement sur push vers `main`, et seulement si `test` réussit) : déclenche un déploiement Render via son Deploy Hook.

Ce découplage garantit qu'aucun code cassé n'est déployé automatiquement : contrairement à l'auto-déploiement par défaut de Render, le déploiement est explicitement gaté par les tests.

## Sécurité & bonnes pratiques

- Ne pas exposer `instance/priosante.sqlite` ou tout fichier contenant des données sensibles.
- Remplacer la `SECRET_KEY` de développement par une valeur sûre en production (`PRIOSANTE_SECRET_KEY`).
- Le mode debug (`FLASK_DEBUG=1`) ne doit jamais être activé en production.
- CSRF protégé sur tous les formulaires (Flask-WTF), rate-limiting sur `/staff/login` et `/mon-rdv` (Flask-Limiter), headers de sécurité (CSP, X-Frame-Options, etc.) posés sur chaque réponse.
- Les endpoints `/api/queue-status` et `/api/notifications-log` exigent une session personnel connectée.
- Si vous utilisez HTTPS, terminez TLS au niveau du load‑balancer / reverse proxy (Render le gère automatiquement).
- PostgreSQL est utilisé en production (SQLite reste réservé au développement local, son fichier ne persiste pas sur le filesystem éphémère de Render).

## Points d'attention (pour les contributeurs)

- `seed.py` contient des identifiants de démonstration : changez/retirez-les avant publication publique. Le script refuse de s'exécuter contre une base non-SQLite sans `SEED_CONFIRM=yes`, pour éviter d'effacer accidentellement des données de production.
- Vérifiez les endpoints d'API dans `app/routes/api.py` avant d'exposer des données sensibles.
- Ajouter des tests supplémentaires pour la logique métier avant changement majeur (scoring / planning).

## Limites connues

Quatre limites sont assumées à ce stade du projet, plutôt que corrigées dans l'immédiat :

- **Pas de système de migration de base de données.** `db.create_all()` crée les tables absentes mais n'altère jamais un schéma déjà existant. Un changement de modèle en production demande une réinitialisation manuelle de la base (`seed.py` avec `SEED_CONFIRM=yes`), pas une migration incrémentale.
- **Rate-limiting en mémoire.** Comme expliqué dans la section [Exécution](#exécution), `Flask-Limiter` stocke ses compteurs dans la mémoire d'un seul processus : le déploiement reste volontairement à un seul worker gunicorn.
- **Données patient non chiffrées.** Téléphones et symptômes sont stockés en clair, sans politique de rétention ni de suppression à la demande. Acceptable pour un prototype académique, à revoir avant tout déploiement clinique réel.
- **Fuseau horaire implicite.** La logique d'ouverture de service et d'attribution de créneaux (`app/planning.py`) repose sur l'heure locale du serveur (`datetime.now()`), sans fuseau explicite. Correct aujourd'hui car le Togo est en UTC+0 et les conteneurs Render tournent par défaut en UTC, mais fragile si le serveur change de région.

## Équipe

Projet réalisé par 4 étudiants en Physique de l'Université de Lomé (UE PHY330) :

- **KOGNON Kokou Romeo**
- **OKOBA Yaou Igor Ben**
- **SAKIE Komlan Elom Winner**
- **SODJA Makou Abraham**

## Contribuer

1. Fork du dépôt
2. Créer une branche `feature/ma-fonctionnalite`
3. Ouvrir une Pull Request décrivant les changements

## Licence

Ce projet est sous licence MIT, voir le fichier `LICENSE`.

