"""
Test delle indoli della tappa 11, al posto degli archetipi: le caratteristiche che nominano
esistono, la nascita è la stessa per lo stesso seme, i nove archetipi di prima hanno la loro indole,
completa vince senza una preferenza netta, e il punteggio standardizzato dà a ogni indole fra il 6
e il 16 per cento dei nati.
"""

import collections
import datetime
import random
import types

import allenamento
import modelli
from costanti import ATTRIBUTI_BASE_CON_ALLENABILI, CARATTERISTICHE_FISICHE_BASE, INDOLE_PREDEFINITA, INDOLI, MAPPA_ARCHETIPI_INDOLI, PROB_INDOLE_CASUALE
from modelli import Giocatore

NASCITA = datetime.datetime(2026, 1, 1)


def test_ogni_caratteristica_delle_indoli_esiste():
    for chiave, indole in INDOLI.items():
        assert indole["nome"]
        for nome in (*indole["principali"], *indole["secondarie"]):
            assert nome in allenamento.CARATTERISTICHE, (chiave, nome)
        assert not set(indole["principali"]) & set(indole["secondarie"]), chiave
    assert INDOLI[INDOLE_PREDEFINITA]["principali"] == ()


def test_la_nascita_e_la_stessa_per_lo_stesso_seme():
    random.seed(31)
    primi = [Giocatore(i, NASCITA) for i in range(1, 30)]
    random.seed(31)
    secondi = [Giocatore(i, NASCITA) for i in range(1, 30)]
    assert [g.indole for g in primi] == [g.indole for g in secondi]
    assert all(g.programma == g.indole for g in primi)


def test_la_mappa_dei_nove_archetipi():
    assert len(MAPPA_ARCHETIPI_INDOLI) == 9
    assert set(MAPPA_ARCHETIPI_INDOLI.values()) == set(INDOLI)
    assert MAPPA_ARCHETIPI_INDOLI["TuttofareBilanciato"] == "completa" and MAPPA_ARCHETIPI_INDOLI["MuroFisico"] == "atletica"


def _innate(rng):
    """Le innate di un nato, come le tira la nascita: fino al 60 per cento del vecchio massimo, cioè al 30 per cento del tetto."""
    return types.SimpleNamespace(**{nome: rng.uniform(0, (5.0 if nome in CARATTERISTICHE_FISICHE_BASE else 20.0) * 0.6) for nome in ATTRIBUTI_BASE_CON_ALLENABILI})


def test_completa_senza_una_preferenza_netta(monkeypatch):
    piatto = types.SimpleNamespace(**{nome: (1.5 if nome in CARATTERISTICHE_FISICHE_BASE else 6.0) for nome in ATTRIBUTI_BASE_CON_ALLENABILI})
    assert all(abs(p) < 1e-9 for p in modelli.punteggi_delle_indoli(piatto).values())
    assert modelli.indole_dalle_innate(piatto) == "completa"
    piatto.bloccosx_base = piatto.bloccodx_base = 12.0
    piatto.difesa_base = 11.0
    assert modelli.indole_dalle_innate(piatto) == "muro"
    monkeypatch.setattr(modelli, "caso", lambda _p: False)
    random.seed(5)
    g = Giocatore(5, NASCITA)
    assert g.indole == modelli.indole_dalle_innate(g)


def test_ogni_indole_fra_il_sei_e_il_sedici_per_cento():
    rng = random.Random(11)
    conta = collections.Counter()
    for _ in range(20_000):
        if rng.random() * 100.0 < PROB_INDOLE_CASUALE:
            conta[rng.choice(list(INDOLI))] += 1
        else:
            conta[modelli.indole_dalle_innate(_innate(rng))] += 1
    for chiave in INDOLI:
        assert 0.06 < conta[chiave] / 20_000 < 0.16, (chiave, conta[chiave])
