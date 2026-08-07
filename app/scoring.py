# Barème officiel PrioSanté pour la Médecine Générale (Document de Cadrage - Section 3.4)

BAREME_SYMPTOMS = {
    'toux_rhume': {'libelle': 'Toux / rhume', 'points': 1},
    'fievre_legere': {'libelle': 'Fièvre légère (< 38,5°C)', 'points': 1},
    'douleur_legere': {'libelle': 'Douleur légère', 'points': 1},
    'douleur_moderee': {'libelle': 'Douleur modérée', 'points': 2},
    'vomissements': {'libelle': 'Vomissements répétés', 'points': 3},
    'enceinte': {'libelle': 'Femme enceinte', 'points': 3},
    'fievre_elevee': {'libelle': 'Fièvre élevée (> 39°C)', 'points': 4},
    'douleur_abdo': {'libelle': 'Douleur abdominale intense', 'points': 6},
    'difficulte_respirer': {'libelle': 'Difficulté à respirer', 'points': 8},
    'confusion': {'libelle': 'Confusion / perte de connaissance', 'points': 10}
}

def evaluer_score_et_priorite(selected_symptom_codes):
    """
    Prend en entrée une liste de codes de symptômes sélectionnés par le patient.
    Retourne un dictionnaire contenant :
    - score : le total de points
    - priorite : 'Faible', 'Moyenne', 'Élevée', ou 'Urgence'
    - action : l'action préconisée
    - symptomes_details : la liste explicite des libellés sélectionnés
    """
    total_score = 0
    details = []

    if selected_symptom_codes:
        for code in selected_symptom_codes:
            if code in BAREME_SYMPTOMS:
                total_score += BAREME_SYMPTOMS[code]['points']
                details.append(BAREME_SYMPTOMS[code]['libelle'])

    # Calcul de la catégorie de priorité
    if total_score <= 3:
        priorite = 'Faible'
        action = 'Planification normale'
    elif total_score <= 7:
        priorite = 'Moyenne'
        action = 'Planification normale, créneau prioritaire dans la journée'
    elif total_score <= 12:
        priorite = 'Élevée'
        action = 'Créneau le plus proche possible, alerte réceptionniste'
    else:
        priorite = 'Urgence'
        action = 'Redirection immédiate vers les urgences physiques, aucun créneau attribué'

    return {
        'score': total_score,
        'priorite': priorite,
        'action': action,
        'symptomes_details': details
    }
