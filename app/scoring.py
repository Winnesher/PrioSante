# =============================================================================
# MOTEUR DE SCORING : Calcul automatique de la priorité médicale (Moteur SFMU)
# =============================================================================

import unicodedata

# Barème officiel PrioSanté pour la Médecine Générale (Document de Cadrage - Section 3.4)
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

def _normaliser_texte(texte):
    """Convertit en minuscules et supprime les accents pour une recherche insensible aux variations."""
    if not texte:
        return ""
    nfkd = unicodedata.normalize('NFKD', texte.lower())
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

# Dictionnaire SFMU de mots-clés d'URGENCE CRITIQUE (Niveau 1 Red Flag -> +15 points)
RED_FLAG_KEYWORDS = [
    # Cardiologie
    'poitrine', 'thoracique', 'coeur', 'cardiaque', 'infarctus', 'oppression', 'arret cardiaque', 'palpitation',
    # Neurologie / AVC
    'avc', 'paralysie', 'paralyse', 'visage de travers', 'bouche deformee', 'bras engourdi', 'perte de connaissance',
    'evanouissement', 'syncope', 'coma', 'convulsion', 'epilepsie', 'epileptique', 'confusion', 'aphasie', 'parole difficile',
    # Respiratoire
    'etouffement', 'etouffe', 'asphyxie', 'detresse respiratoire', 'respiration impossible', 'cyanose', 'levres bleues', 'fausse route', 'noyade',
    # Trauma / Chocs / Morsures
    'hemorragie', 'sang abondant', 'fracture ouverte', 'serpent', 'chien', 'accident', 'brulure grave', 'empoisonne', 'empoisonnement', 'intoxication',
    # Infectieux / Pédiatrie
    'raideur nuque', 'purpura', 'taches rouges', 'nourrisson',
    # Vital / Psychiatrie
    'suicide', 'idées noires'
]

# Dictionnaire SFMU de mots-clés de PRIORITÉ ÉLEVÉE (Niveau 2 -> +8 points)
HIGH_PRIORITY_KEYWORDS = [
    'asthme', 'souffle court', 'toux', 'sifflement',
    'douleur abdominale', 'mal au ventre', 'ventre', 'vomissement', 'vomir', 'hematemese', 'occlusion',
    'cephalee', 'migraine', 'vertige', 'vision floue',
    'grossesse', 'enceinte', 'contraction', 'pelvienne',
    'entorse', 'plaie', 'brulure', 'luxation', 'morsure', 'mordu', 'mordue', 'sang', 'saigner', 'saignement'
]

def evaluer_score_et_priorite(selected_symptom_codes, texte_saisie_libre=None):
    """
    Calcule le score total et détermine la priorité médicale du patient en combinant
    les symptômes cochés et la saisie libre éventuelle.
    """
    total_score = 0
    details = []
    has_red_flag = False

    # 1. Évaluation des symptômes cochés
    if selected_symptom_codes:
        for code in selected_symptom_codes:
            if code in BAREME_SYMPTOMS:
                s_info = BAREME_SYMPTOMS[code]
                total_score += s_info['points']
                details.append(s_info['libelle'])
                if s_info.get('is_red_flag'):
                    has_red_flag = True

    # 2. Analyse et cumul de la saisie libre du patient
    if texte_saisie_libre and texte_saisie_libre.strip():
        texte_propre = texte_saisie_libre.strip()
        texte_norm = _normaliser_texte(texte_propre)

        # Détection des Red Flags dans la saisie libre
        found_red_flag_keyword = any(kw in texte_norm for kw in RED_FLAG_KEYWORDS)
        
        if found_red_flag_keyword:
            has_red_flag = True
            total_score += 15
            details.append(f'[Saisie libre patient (Red Flag / Urgence)] : "{texte_propre}"')
        else:
            # Détection des mots-clés de priorité élevée
            found_high_priority = any(kw in texte_norm for kw in HIGH_PRIORITY_KEYWORDS)
            if found_high_priority:
                total_score += 8
                details.append(f'[Saisie libre patient (Priorité Élevée)] : "{texte_propre}"')
            else:
                # Score de base de sécurité pour toute saisie libre non critique (+4 points)
                total_score += 4
                details.append(f'[Saisie libre patient] : "{texte_propre}"')

    # 3. Détermination de la catégorie de priorité finale
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

    return {
        'score': total_score,
        'priorite': priorite,
        'action': action,
        'symptomes_details': details,
        'is_red_flag': has_red_flag
    }
