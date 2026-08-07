from app.database import db
from app.models import Notification

def envoyer_notification_simulee(consultation, type_msg='CONFIRMATION', details_extra=None):
    """
    Simule l'envoi d'un SMS ou message USSD au patient.
    Enregistre le message dans la table notifications pour la démonstration.
    """
    patient = consultation.patient
    service = consultation.service
    
    if type_msg == 'CONFIRMATION':
        if consultation.priorite == 'Urgence':
            message = (f"PrioSanté ALERTE : M. / Mme {patient.nom}, suite à vos symptômes, "
                       f"veuillez vous présenter IMMÉDIATEMENT aux urgences de l'hôpital.")
        else:
            message = (f"PrioSanté : Votre RDV en {service.nom} est confirmé pour le "
                       f"{consultation.date_consultation.strftime('%d/%m/%Y')} à {consultation.heure_prevue}. "
                       f"Code RDV : {consultation.code_consultation}. Priorité : {consultation.priorite}.")
    elif type_msg == 'RAPPEL':
        message = (f"PrioSanté RAPPEL : Votre consultation est prévue aujourd'hui à {consultation.heure_prevue}. "
                   f"Pensez à arriver 5 min en avance avec votre code {consultation.code_consultation}.")
    elif type_msg == 'RECALCUL':
        message = (f"PrioSanté INFO : Votre créneau a été ajusté à {consultation.heure_prevue} "
                   f"en raison de la prise en charge d'urgences cliniques.")
    else:
        message = f"PrioSanté Notification : {details_extra or 'Mise à jour de votre rendez-vous.'}"

    notif = Notification(
        consultation_id=consultation.id,
        type_envoi='SMS_SIMULE',
        destinataire=patient.telephone,
        message=message,
        statut='simule_envoye'
    )
    
    db.session.add(notif)
    db.session.commit()
    
    return notif
