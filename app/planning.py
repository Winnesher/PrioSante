# =============================================================================
# SYSTÈME DE PLANNING : Gestion des créneaux horaires et des retards
# =============================================================================

# Importation des modules nécessaires
from datetime import datetime, timedelta, time, date  # Pour gérer les dates et heures
from app.database import db  # Instance SQLAlchemy pour la base de données
from app.models import Consultation, LogRetard  # Modèles de données

# Constantes de configuration des horaires
HEURE_DEBUT_CONSULTATION = "08:00"  # Heure d'ouverture des consultations
HEURE_FIN_CONSULTATION = "17:00"  # Heure de fermeture des consultations
DUREE_CRENEAU_MINUTES = 15  # Durée d'un créneau en minutes

def generer_tous_les_creneaux():
    """
    Génère la liste de tous les créneaux de la journée au format HH:MM.
    
    Returns:
        list: Liste des créneaux ['08:00', '08:15', '08:30', ..., '16:45', '17:00']
    """
    creneaux = []  # Liste vide pour stocker les créneaux
    current = datetime.strptime(HEURE_DEBUT_CONSULTATION, "%H:%M")  # Heure de début convertie en datetime
    end = datetime.strptime(HEURE_FIN_CONSULTATION, "%H:%M")  # Heure de fin convertie en datetime
    
    # Boucle pour générer tous les créneaux de 15 en 15 minutes
    while current < end:
        creneaux.append(current.strftime("%H:%M"))  # Ajoute l'heure formatée à la liste
        current += timedelta(minutes=DUREE_CRENEAU_MINUTES)  # Ajoute 15 minutes
    return creneaux

def service_est_ouvert(instant=None):
    """
    Vérifie si le service est actuellement ouvert aux horaires de consultation.
    
    Args:
        instant (datetime, optional): Instant à vérifier. Si None, utilise l'heure actuelle.
        
    Returns:
        bool: True si le service est ouvert, False sinon
    """
    # Le service accueille du public entre HEURE_DEBUT_CONSULTATION et HEURE_FIN_CONSULTATION
    # En dehors de cette plage, l'inscription en ligne reste possible mais programme le patient au jour ouvré suivant
    instant = instant or datetime.now()
    debut = datetime.strptime(HEURE_DEBUT_CONSULTATION, "%H:%M").time()
    fin = datetime.strptime(HEURE_FIN_CONSULTATION, "%H:%M").time()
    return debut <= instant.time() < fin


def attribuer_creneau(service_id, date_cible, priorite):
    """
    Détermine (date, heure) du premier créneau libre à partir de date_cible,
    par ordre chronologique — l'attribution de créneau ne dépend pas de la
    priorité clinique (hors Urgence). La priorisation réelle se fait au
    niveau du tableau de bord du personnel (staff.dashboard()), qui trie la
    file d'attente par priorité avant l'heure : un patient plus prioritaire
    est vu en premier dans la salle, même si son créneau officiel est plus
    tardif que celui d'un patient moins prioritaire.
    - Si date_cible est aujourd'hui, ignore les créneaux déjà passés.
    - Si plus aucun créneau n'est disponible ce jour-là (journée pleine ou
      déjà terminée), reporte automatiquement au jour suivant à l'ouverture.
    - Si priorite == 'Urgence', renvoie None (aucun créneau, redirection immédiate).
    """
    if priorite == 'Urgence':
        return None

    creneaux_possibles = generer_tous_les_creneaux()

    # Si date_cible est aujourd'hui, ignore les créneaux déjà passés
    if date_cible == date.today():
        maintenant = datetime.now().time()
        creneaux_possibles = [
            c for c in creneaux_possibles
            if datetime.strptime(c, "%H:%M").time() > maintenant
        ]

    # Si aucun créneau disponible aujourd'hui, reporte au jour suivant
    if not creneaux_possibles:
        return attribuer_creneau(service_id, date_cible + timedelta(days=1), priorite)

    # Récupérer les consultations déjà réservées (statuts actifs uniquement)
    consultations_existantes = Consultation.query.filter(
        Consultation.service_id == service_id,
        Consultation.date_consultation == date_cible,
        Consultation.statut.in_(['en_attente', 'arrive', 'en_consultation', 'en_retard'])
    ).all()

    # Créer un ensemble des créneaux déjà occupés pour une recherche rapide
    creneaux_occupes = {c.heure_prevue for c in consultations_existantes if c.heure_prevue}

    # Chercher le premier créneau libre
    for c in creneaux_possibles:
        if c not in creneaux_occupes:
            return (date_cible, c)

    # Journée pleine : reporter au jour suivant plutôt que déborder après 17:00
    return attribuer_creneau(service_id, date_cible + timedelta(days=1), priorite)

def creneau_est_depasse(consultation, minutes_grace=DUREE_CRENEAU_MINUTES, instant=None):
    """
    Vérifie si un créneau est dépassé (heure passée sans prise en charge).
    
    Args:
        consultation (Consultation): Consultation à vérifier
        minutes_grace (int): Marge de grâce en minutes (défaut: durée d'un créneau)
        instant (datetime, optional): Instant de référence. Si None, utilise l'heure actuelle.
        
    Returns:
        bool: True si le créneau est dépassé, False sinon
    """
    # Un créneau est considéré dépassé quand son heure prévue (+ une marge de grâce)
    # est déjà passée alors que le patient n'a toujours pas été pris en charge
    # Sert uniquement de repère visuel pour le personnel — aucune bascule automatique de statut
    instant = instant or datetime.now()
    if not consultation.heure_prevue or consultation.date_consultation != instant.date():
        return False
    if consultation.statut not in ('en_attente', 'en_retard'):
        return False
    heure_limite = (
        datetime.strptime(consultation.heure_prevue, "%H:%M") + timedelta(minutes=minutes_grace)
    ).time()
    return instant.time() > heure_limite


def gerer_retard_patient(consultation, minutes_retard, instant=None):
    """
    Applique la règle métier pour les retards :
    - Retard <= 10 minutes : Maintien de la consultation (léger décalage)
    - Retard > 10 minutes : Replacement en fin de file du jour, sans jamais
      proposer un créneau déjà passé. Si la journée est pleine ou déjà
      terminée, reporte au lendemain à l'ouverture (même logique que
      attribuer_creneau).
    """
    instant = instant or datetime.now()

    # Règle : retard <= 10 minutes → consultation maintenue
    if minutes_retard <= 10:
        action = f"Consultation maintenue malgré un retard de {minutes_retard} minutes."
        consultation.statut = 'en_retard'
    else:
        # Règle : retard > 10 minutes → replacement en fin de file
        date_originale = consultation.date_consultation
        creneaux_possibles = generer_tous_les_creneaux()

        # Si le retard est aujourd'hui, ignorer les créneaux déjà passés
        if date_originale == instant.date():
            heure_actuelle = instant.time()
            creneaux_possibles = [
                c for c in creneaux_possibles
                if datetime.strptime(c, "%H:%M").time() > heure_actuelle
            ]

        # Chercher un nouveau créneau en fin de file
        nouvelle_heure = None
        if creneaux_possibles:
            consultations_jour = Consultation.query.filter(
                Consultation.service_id == consultation.service_id,
                Consultation.date_consultation == date_originale,
                Consultation.statut.in_(['en_attente', 'arrive', 'en_consultation', 'en_retard'])
            ).all()

            heures_occupees = [c.heure_prevue for c in consultations_jour if c.heure_prevue]

            # Trouver la dernière heure encore libre
            for c in reversed(creneaux_possibles):
                if c not in heures_occupees:
                    nouvelle_heure = c
                    break

            # Si aucun créneau libre, tenter de créer un après la dernière heure occupée
            if not nouvelle_heure and heures_occupees:
                derniere = max(heures_occupees)
                dt_dern = datetime.strptime(derniere, "%H:%M")
                candidat = (dt_dern + timedelta(minutes=DUREE_CRENEAU_MINUTES)).strftime("%H:%M")
                # Ne proposer ce dépassement que s'il reste dans les horaires de service
                if candidat <= HEURE_FIN_CONSULTATION:
                    nouvelle_heure = candidat

        # Si un créneau est trouvé, mettre à jour la consultation
        if nouvelle_heure:
            consultation.heure_prevue = nouvelle_heure
            consultation.statut = 'en_retard'
            action = f"Retard de {minutes_retard} min (>10 min) : Replacé en fin de file à {nouvelle_heure}."
        else:
            # Journée pleine ou déjà terminée : reporter au lendemain à l'ouverture
            consultation.date_consultation = date_originale + timedelta(days=1)
            consultation.heure_prevue = HEURE_DEBUT_CONSULTATION
            consultation.statut = 'en_retard'
            action = (f"Retard de {minutes_retard} min (>10 min) : journée pleine ou terminée, "
                      f"reporté au {consultation.date_consultation.strftime('%d/%m/%Y')} à {HEURE_DEBUT_CONSULTATION}.")

    # Créer un log de retard pour l'historique
    log = LogRetard(
        consultation_id=consultation.id,
        minutes_retard=minutes_retard,
        action_prise=action
    )
    db.session.add(log)
    db.session.commit()
    
    return action
