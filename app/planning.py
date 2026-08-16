from datetime import datetime, timedelta, time, date
from app.database import db
from app.models import Consultation, LogRetard

HEURE_DEBUT_CONSULTATION = "08:00"
HEURE_FIN_CONSULTATION = "17:00"
DUREE_CRENEAU_MINUTES = 15

def generer_tous_les_creneaux():
    """Génère la liste de tous les créneaux de la journée au format HH:MM."""
    creneaux = []
    current = datetime.strptime(HEURE_DEBUT_CONSULTATION, "%H:%M")
    end = datetime.strptime(HEURE_FIN_CONSULTATION, "%H:%M")
    
    while current < end:
        creneaux.append(current.strftime("%H:%M"))
        current += timedelta(minutes=DUREE_CRENEAU_MINUTES)
    return creneaux

def service_est_ouvert(instant=None):
    """Le service accueille du public entre HEURE_DEBUT_CONSULTATION et
    HEURE_FIN_CONSULTATION. En dehors de cette plage, l'inscription en ligne
    reste possible mais programme le patient au jour ouvré suivant."""
    instant = instant or datetime.now()
    debut = datetime.strptime(HEURE_DEBUT_CONSULTATION, "%H:%M").time()
    fin = datetime.strptime(HEURE_FIN_CONSULTATION, "%H:%M").time()
    return debut <= instant.time() < fin


def attribuer_creneau(service_id, date_cible, priorite):
    """
    Détermine (date, heure) du premier créneau libre à partir de date_cible.
    - Si date_cible est aujourd'hui, ignore les créneaux déjà passés.
    - Si plus aucun créneau n'est disponible ce jour-là (journée pleine ou
      déjà terminée), reporte automatiquement au jour suivant à l'ouverture.
    - Si priorite == 'Urgence', renvoie None (aucun créneau, redirection immédiate).
    """
    if priorite == 'Urgence':
        return None

    creneaux_possibles = generer_tous_les_creneaux()

    if date_cible == date.today():
        maintenant = datetime.now().time()
        creneaux_possibles = [
            c for c in creneaux_possibles
            if datetime.strptime(c, "%H:%M").time() > maintenant
        ]

    if not creneaux_possibles:
        return attribuer_creneau(service_id, date_cible + timedelta(days=1), priorite)

    # Récupérer les consultations déjà réservées non annulées/non libérées
    consultations_existantes = Consultation.query.filter(
        Consultation.service_id == service_id,
        Consultation.date_consultation == date_cible,
        Consultation.statut.in_(['en_attente', 'arrive', 'en_consultation', 'en_retard'])
    ).all()

    creneaux_occupes = {c.heure_prevue for c in consultations_existantes if c.heure_prevue}

    if priorite in ['Élevée', 'Moyenne']:
        # Trouver le tout premier créneau non occupé
        for c in creneaux_possibles:
            if c not in creneaux_occupes:
                return (date_cible, c)
    else:
        # Priorité Faible : attribuer le premier créneau disponible à partir du début
        for c in creneaux_possibles:
            if c not in creneaux_occupes:
                return (date_cible, c)

    # Journée pleine : reporter au jour suivant plutôt que déborder après 17:00
    return attribuer_creneau(service_id, date_cible + timedelta(days=1), priorite)

def gerer_retard_patient(consultation, minutes_retard):
    """
    Applique la règle métier pour les retards :
    - Retard <= 10 minutes : Maintien de la consultation (léger décalage)
    - Retard > 10 minutes : Replacement en fin de file du jour
    """
    if minutes_retard <= 10:
        action = f"Consultation maintenue malgré un retard de {minutes_retard} minutes."
        consultation.statut = 'en_retard'
    else:
        # Replacement en fin de file
        creneaux_possibles = generer_tous_les_creneaux()
        consultations_jour = Consultation.query.filter(
            Consultation.service_id == consultation.service_id,
            Consultation.date_consultation == consultation.date_consultation,
            Consultation.statut.in_(['en_attente', 'arrive', 'en_consultation', 'en_retard'])
        ).all()
        
        heures_occupees = [c.heure_prevue for c in consultations_jour if c.heure_prevue]
        
        # Trouver la dernière heure
        nouvelle_heure = None
        for c in reversed(creneaux_possibles):
            if c not in heures_occupees:
                nouvelle_heure = c
                break
        
        if not nouvelle_heure and heures_occupees:
            derniere = max(heures_occupees)
            dt_dern = datetime.strptime(derniere, "%H:%M")
            nouvelle_heure = (dt_dern + timedelta(minutes=15)).strftime("%H:%M")
        elif not nouvelle_heure:
            nouvelle_heure = "16:45"
            
        consultation.heure_prevue = nouvelle_heure
        consultation.statut = 'en_retard'
        action = f"Retard de {minutes_retard} min (>10 min) : Replacé en fin de file à {nouvelle_heure}."

    log = LogRetard(
        consultation_id=consultation.id,
        minutes_retard=minutes_retard,
        action_prise=action
    )
    db.session.add(log)
    db.session.commit()
    
    return action
