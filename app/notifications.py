# =============================================================================
# SYSTÈME DE NOTIFICATIONS : Simulation d'envoi de SMS aux patients
# =============================================================================

# Importation des modules nécessaires
from app.database import db  # Instance SQLAlchemy pour la base de données
from app.models import Notification  # Modèle de données

def envoyer_notification_simulee(consultation, type_msg='CONFIRMATION', details_extra=None):
    """
    Simule l'envoi d'un SMS ou message USSD au patient.
    Enregistre le message dans la table notifications pour la démonstration.
    
    Args:
        consultation (Consultation): Objet consultation concernée
        type_msg (str): Type de message ('CONFIRMATION', 'RAPPEL', 'RECALCUL')
        details_extra (str, optional): Texte supplémentaire pour le message
        
    Returns:
        Notification: Objet notification créé en base de données
    """
    # Récupérer les informations du patient et du service
    patient = consultation.patient
    service = consultation.service
    
    # Générer le message selon le type de notification
    if type_msg == 'CONFIRMATION':
        # Message de confirmation de rendez-vous
        if consultation.priorite == 'Urgence':
            message = (f"PrioSanté ALERTE : M. / Mme {patient.nom}, suite à vos symptômes, "
                       f"veuillez vous présenter IMMÉDIATEMENT aux urgences de l'hôpital.")
        else:
            message = (f"PrioSanté : Votre RDV en {service.nom} est confirmé pour le "
                       f"{consultation.date_consultation.strftime('%d/%m/%Y')} à {consultation.heure_prevue}. "
                       f"Code RDV : {consultation.code_consultation}. Priorité : {consultation.priorite}.")
    elif type_msg == 'RAPPEL':
        # Message de rappel avant le rendez-vous
        message = (f"PrioSanté RAPPEL : Votre consultation est prévue aujourd'hui à {consultation.heure_prevue}. "
                   f"Pensez à arriver 5 min en avance avec votre code {consultation.code_consultation}.")
    elif type_msg == 'RECALCUL':
        # Message de recalcul de créneau (ex: après retard)
        message = (f"PrioSanté INFO : Votre créneau a été ajusté à {consultation.heure_prevue} "
                   f"en raison de la prise en charge d'urgences cliniques.")
    else:
        # Message générique avec texte supplémentaire si fourni
        message = f"PrioSanté Notification : {details_extra or 'Mise à jour de votre rendez-vous.'}"

    # Créer l'objet notification avec toutes les informations
    notif = Notification(
        consultation_id=consultation.id,  # Lien vers la consultation
        type_envoi='SMS_SIMULE',  # Type d'envoi (simulé pour la démo)
        destinataire=patient.telephone,  # Numéro de téléphone du patient
        message=message,  # Contenu du message
        statut='simule_envoye'  # Statut d'envoi (simulé)
    )
    
    # Sauvegarder la notification en base de données
    db.session.add(notif)
    db.session.commit()
    
    return notif
