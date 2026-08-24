# =============================================================================
# MOTEUR DE SCORING : Calcul automatique de la priorité médicale
# =============================================================================

# Barème officiel PrioSanté pour la Médecine Générale (Document de Cadrage - Section 3.4)
# Chaque symptôme a un nombre de points selon sa gravité médicale
BAREME_SYMPTOMS = {
    'toux_rhume': {'libelle': 'Toux / rhume', 'points': 1},  # Symptôme bénin
    'fievre_legere': {'libelle': 'Fièvre légère (< 38,5°C)', 'points': 1},  # Symptôme bénin
    'douleur_legere': {'libelle': 'Douleur légère', 'points': 1},  # Symptôme bénin
    'douleur_moderee': {'libelle': 'Douleur modérée', 'points': 2},  # Symptôme modéré
    'vomissements': {'libelle': 'Vomissements répétés', 'points': 3},  # Symptôme modéré
    'enceinte': {'libelle': 'Femme enceinte', 'points': 3},  # Situation particulière
    'fievre_elevee': {'libelle': 'Fièvre élevée (> 39°C)', 'points': 4},  # Symptôme sérieux
    'douleur_abdo': {'libelle': 'Douleur abdominale intense', 'points': 6},  # Symptôme sérieux
    'difficulte_respirer': {'libelle': 'Difficulté à respirer', 'points': 8},  # Symptôme critique
    'confusion': {'libelle': 'Confusion / perte de connaissance', 'points': 10},  # Symptôme critique
    'douleur_thoracique': {'libelle': 'Douleur thoracique constrictive (poitrine / thorax)', 'points': 15, 'is_red_flag': True},  # Red Flag absolu
    'signes_avc': {'libelle': "Signes d'AVC (faiblesse unilatérale, bouche déformée, parole difficile)", 'points': 15, 'is_red_flag': True}  # Red Flag absolu
}

def evaluer_score_et_priorite(selected_symptom_codes):
    """
    Calcule le score total et détermine la priorité médicale du patient.
    
    Args:
        selected_symptom_codes (list): Liste des codes de symptômes cochés par le patient
        
    Returns:
        dict: Dictionnaire contenant :
            - score (int): Total de points calculé
            - priorite (str): 'Faible', 'Moyenne', 'Élevée' ou 'Urgence'
            - action (str): Action préconisée selon la priorité
            - symptomes_details (list): Liste des libellés des symptômes sélectionnés
            - is_red_flag (bool): Vrai si au moins un symptôme à risque critique est présent
    """
    # Initialisation des variables
    total_score = 0  # Score total qui sera additionné
    details = []  # Liste pour stocker les libellés des symptômes
    has_red_flag = False

    if selected_symptom_codes:
        for code in selected_symptom_codes:
            if code in BAREME_SYMPTOMS:
                s_info = BAREME_SYMPTOMS[code]
                total_score += s_info['points']
                details.append(s_info['libelle'])
                if s_info.get('is_red_flag'):
                    has_red_flag = True

    # Détermination de la catégorie de priorité selon le score total ou présence d'un Red Flag
    if has_red_flag or total_score > 12:
        priorite = 'Urgence'
        action = 'Redirection immédiate vers les urgences physiques, aucun créneau attribué'
    elif total_score <= 3:
        priorite = 'Faible'
        action = 'Planification normale'
    elif total_score <= 7:
        priorite = 'Moyenne'
        action = 'Planification normale, créneau prioritaire dans la journée'
    else:
        priorite = 'Élevée'
        action = 'Créneau le plus proche possible, alerte réceptionniste'

    # Retour du résultat sous forme de dictionnaire
    return {
        'score': total_score,
        'priorite': priorite,
        'action': action,
        'symptomes_details': details,
        'is_red_flag': has_red_flag
    }

