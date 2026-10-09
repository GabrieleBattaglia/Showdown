"""
Test dei tratti rari dell'allenamento e dell'ambizione, tappa 11: nascono dal numero del giocatore
senza toccare il caso del mondo, con le frequenze di D31, e la maturazione sposta l'efficacia e
l'inizio del declino.
"""

import random
import statistics

import pytest
from aiuti_motore import giocatore

import allenamento
import tratti
from costanti import ANNO_SIMULAZIONE_GIORNI


def test_lo_stesso_numero_da_sempre_gli_stessi_tratti_e_la_stessa_ambizione():
    random.seed(1)
    primi = tratti.tratti_innati(4321), tratti.ambizione_innata(4321)
    random.seed(2)
    tiro = random.random()
    random.seed(2)
    assert (tratti.tratti_innati(4321), tratti.ambizione_innata(4321)) == primi
    # Il caso del mondo non si tocca.
    assert random.random() == tiro


def test_le_frequenze_su_ventimila_numeri():
    insieme = [tratti.tratti_innati(i) for i in range(1, 20_001)]
    quota = {chiave: sum(1 for t in insieme if t[chiave]) / len(insieme) for chiave in ("talento", "apprendista_rapido")}
    assert 0.04 < quota["talento"] < 0.06
    assert 0.032 < quota["apprendista_rapido"] < 0.048
    for maturazione in ("precoce", "tardiva"):
        assert 0.032 < sum(1 for t in insieme if t["maturazione"] == maturazione) / len(insieme) < 0.048
    ambizioni = [tratti.ambizione_innata(i) for i in range(1, 20_001)]
    assert statistics.fmean(ambizioni) == pytest.approx(50.0, abs=0.6)
    assert 16.0 < statistics.pstdev(ambizioni) < 18.5
    assert min(ambizioni) >= 0.0 and max(ambizioni) <= 100.0


@pytest.mark.parametrize(("maturazione", "anni", "atteso"), [(None, 15, 1.0), (None, 45, 1.0), ("precoce", 15, 1.3), ("precoce", 30, 1.0), ("precoce", 45, 0.7),
                                                            ("tardiva", 15, 0.75), ("tardiva", 35, 1.125), ("tardiva", 50, 1.25)])
def test_la_maturazione_nell_efficacia(maturazione, anni, atteso):
    g = giocatore(7, anni=anni, maturazione=maturazione, talento=False, apprendista_rapido=False)
    assert tratti.fattore_maturazione(g) == pytest.approx(atteso)
    assert allenamento.efficacia(g) == pytest.approx(tratti.curva_eta(anni) * atteso)


def test_il_talento_impara_piu_in_fretta():
    normale = giocatore(8, anni=25, talento=False, apprendista_rapido=False, maturazione=None)
    talento = giocatore(8, anni=25, talento=True, apprendista_rapido=False, maturazione=None)
    assert allenamento.efficacia(talento) == pytest.approx(1.3 * allenamento.efficacia(normale))


def test_la_maturazione_sposta_l_inizio_del_declino():
    normale = giocatore(9, valore=20.0, anni=47, maturazione=None)
    precoce = giocatore(9, valore=20.0, anni=47, maturazione="precoce")
    tardivo = giocatore(9, valore=20.0, anni=53, maturazione="tardiva")
    assert (tratti.eta_inizio_declino(normale), tratti.eta_inizio_declino(precoce), tratti.eta_inizio_declino(tardivo)) == (50.0, 44.0, 56.0)
    normale._applica_declino_aggregato(1)
    precoce._applica_declino_aggregato(1)
    tardivo._applica_declino_aggregato(1)
    assert normale.difesa_base == 20.0 and tardivo.difesa_base == 20.0
    assert precoce.difesa_base < 20.0
    assert tratti.giorni_inizio_declino(precoce) == int(44 * ANNO_SIMULAZIONE_GIORNI)
