import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scoring import evaluer_score_et_priorite, BAREME_SYMPTOMS

def test_evaluer_score_faible():
    res = evaluer_score_et_priorite(['toux_rhume', 'douleur_legere'])
    assert res['score'] == 2
    assert res['priorite'] == 'Faible'

def test_evaluer_score_moyen():
    res = evaluer_score_et_priorite(['fievre_elevee', 'douleur_moderee'])
    assert res['score'] == 6
    assert res['priorite'] == 'Moyenne'

def test_evaluer_score_eleve():
    res = evaluer_score_et_priorite(['difficulte_respirer', 'douleur_moderee'])
    assert res['score'] == 10
    assert res['priorite'] == 'Élevée'

def test_evaluer_score_urgence():
    res = evaluer_score_et_priorite(['confusion', 'fievre_elevee'])
    assert res['score'] == 14
    assert res['priorite'] == 'Urgence'
    assert 'Redirection immédiate' in res['action']
