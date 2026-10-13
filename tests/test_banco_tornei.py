"""
Test del banco dei tornei della tappa 12, strumenti/banco_tornei.py, punto 4.15 del progetto: 300
tornei a caso con un seme fisso, senza nessuna violazione, con tutti gli esiti, e la serpentina che
separa davvero i compagni di club. E le formule a caso del banco sono tutte formule che l'editor accetta.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import banco_tornei as bt

import formule


def test_trecento_tornei_senza_violazioni():
    righe = []
    misure = bt.banco(300, 2026, righe.append)
    assert misure["errori"] == []
    assert misure["tornei"] == 300 and misure["incontri"] > 10_000
    assert all(misure["esiti"][esito] > 0 for esito in ("regolare", "ritiro", "tavolino", "tavolino_doppio", "riposo"))
    assert misure["finali"] > 0 and misure["compagni"] < misure["compagni_senza"]
    assert any("Nessuna violazione" in riga for riga in righe)


def test_le_formule_a_caso_sono_valide():
    rng = random.Random(9)
    for numero in range(200):
        formula = bt.formula_a_caso(rng, numero)
        assert formule.valida_formula(formula) is None
        assert 4 <= formule.tetto(formula) <= bt.TETTO_MASSIMO
