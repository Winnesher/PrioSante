# PrioSante

> Projet réalisé dans le cadre de l'UE PHY330, Université de Lomé.

PrioSante est une application web légère développée en Python avec Flask pour la gestion et la priorisation des rendez‑vous médicaux.

**Fonctionnalités principales :**
- Interface patient (inscription, demande RDV, consultation) - français/anglais
- Tableau de bord staff (réception, médecin) - gestion file, arrivées, consultations
- Moteur de scoring pour prioriser selon les symptômes
- Module de planning (génération et attribution des créneaux)
- Système de notifications persistées en base

**Démo en ligne :** [priosante.onrender.com](https://priosante.onrender.com)

[![CI](https://github.com/Winnesher/PrioSante/actions/workflows/ci.yml/badge.svg)](https://github.com/Winnesher/PrioSante/actions/workflows/ci.yml)
[![Licence: MIT](https://img.shields.io/badge/Licence-MIT-blue.svg)](LICENSE)

---

## Sommaire

1. [Démarrage rapide](#démarrage-rapide)
2. [Comptes de démonstration](#comptes-de-démonstration)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Initialisation de la base](#initialisation-de-la-base)
6. [Exécution](#exécution)
7. [Tests](#tests)
8. [Structure du projet](#structure-du-projet)
9. [Déploiement](#déploiement)
10. [Sécurité](#sécurité)
11. [Équipe](#équipe)

## Démarrage rapide

```bash
# Cloner le projet
git clone https://github.com/Winnesher/PrioSante.git
cd PrioSante

# Créer l'environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la base de données
python seed.py

# Lancer l'application
python run.py
```

Ouvrir ensuite http://127.0.0.1:5000

---

## Comptes de démonstration

**Comptes staff (pour tester le tableau de bord) :**

| Rôle | Username | Password |
|------|----------|----------|
| Réceptionniste | `reception1` | `demo123` |
| Médecin | `dr.kognon` | `demo123` |

**Note :** Ces identifiants sont générés par le script `seed.py` et ne doivent être utilisés qu'en environnement de développement.

---

## Installation

**Pré-requis :**
- Python 3.10+
- Git

**Étapes :**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

L'application utilise par défaut une base SQLite locale (`instance/priosante.sqlite`) et une clé secrète de développement.

**Variables d'environnement (optionnelles) :**

- `PRIOSANTE_SECRET_KEY` : clé secrète Flask (à remplacer en production)
- `DATABASE_URL` : URI de connexion PostgreSQL (pour production)
- `FLASK_DEBUG` : `1` pour activer le mode debug (jamais en production)
- `PORT` : port d'écoute (fourni automatiquement par Render)

**Exemple :**

```bash
export PRIOSANTE_SECRET_KEY="change_me_to_a_secure_value"
export FLASK_DEBUG=1
```

**Note :** Le dossier `instance/` contient la base locale et est ignoré par Git.

## Initialisation de la base

Pour initialiser et peupler la base de données :

```bash
python seed.py
```

Ce script crée :
- Un service "Médecine Générale"
- Un questionnaire basé sur le barème de priorité
- Un médecin (Dr. KOGNON Kokou Romeo)
- Les comptes staff (voir section [Comptes de démonstration](#comptes-de-démonstration))
- 4 consultations de test (différents niveaux de priorité)

**⚠️ En production :** Pour une base PostgreSQL, ajoutez `SEED_CONFIRM=yes` pour confirmer la réinitialisation.

## Exécution

**Développement :**

```bash
python run.py
# Ouvrir http://127.0.0.1:5000
```

**Production :**

```bash
gunicorn run:app -b 0.0.0.0:8000
```

**Note :** Un seul worker est utilisé volontairement (rate-limiting stocké en mémoire).

## Tests

```bash
pytest -q
```

16 tests couvrent : scoring, planning, rôles staff, routes patient.

## Structure du projet

```
PrioSante/
├── run.py                    # Point d'entrée
├── requirements.txt          # Dépendances
├── seed.py                   # Initialisation DB
├── instance/                 # DB locale (ignoré par Git)
├── app/
│   ├── __init__.py          # Factory Flask
│   ├── database.py          # SQLAlchemy
│   ├── models.py            # Modèles (Patient, Consultation, Personnel...)
│   ├── planning.py          # Génération créneaux
│   ├── scoring.py           # Barème priorité
│   ├── notifications.py     # Notifications
│   └── routes/              # Blueprints (patient, staff, api)
├── tests/                   # Tests unitaires
├── render.yaml              # Blueprint Render
└── .github/workflows/`      # CI/CD
```

## Déploiement

Le projet utilise [Render](https://render.com) avec le Blueprint `render.yaml`.

**Étapes :**

1. Créer un compte Render et connecter le dépôt GitHub
2. Choisir "New Blueprint" et sélectionner ce dépôt
3. Copier l'URL du **Deploy Hook** et l'ajouter comme secret GitHub `RENDER_DEPLOY_HOOK_URL`
4. Initialiser la base en production via le Shell Render :
   ```bash
   SEED_CONFIRM=yes python seed.py
   ```

## CI/CD

Pipeline GitHub Actions (`.github/workflows/ci.yml`) :
1. **Test** : exécute `pytest -q`
2. **Deploy** (sur `main` uniquement si tests OK) : déclenche le déploiement Render

## Sécurité

- Remplacer `SECRET_KEY` en production
- Jamais de `FLASK_DEBUG=1` en production
- CSRF protégé, rate-limiting sur routes sensibles
- PostgreSQL en production (SQLite en dev uniquement)
- Ne jamais commiter les secrets (`.env`, DB réelle)

## Limites connues

- **Pas de migration DB** : `db.create_all()` crée les tables mais ne migre pas le schéma
- **Rate-limiting en mémoire** : déploiement à 1 worker uniquement
- **Données non chiffrées** : acceptable pour prototype académique
- **Fuseau horaire implicite** : basé sur heure serveur (UTC)

---

## Équipe

Projet réalisé par 4 étudiants en Physique (UE PHY330, Université de Lomé) :

- **KOGNON Kokou Romeo**
- **OKOBA Yaou Igor**
- **SAKIE Komlan Elom Winner**
- **SODJA Makou Abraham**

---

## Licence

MIT - voir le fichier `LICENSE`

