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


def _allenata_negli_anni(apprendista, punti_al_giorno, tappe=(25, 50)):
    """
    Lo stesso giocatore di 20 anni, con o senza il tratto, si allena mese per mese con le funzioni
    vere: i punti del mese spesi secondo la sua indole, il calo e l'oblio del primo del mese, il
    declino. Restituisce la somma della parte allenata alle età delle tappe.
    """
    g = giocatore(31, valore=10.0, fisico=2.5, anni=20, talento=False, maturazione=None, apprendista_rapido=apprendista)
    somme = {}
    while len(somme) < len(tappe):
        g.punti_allenamento += punti_al_giorno * 30
        allenamento.allena_secondo_programma(g, programma=g.indole)
        allenamento.mantenimento_del_mese(g, 30)
        g.eta += 30
        g._applica_declino_aggregato(30)
        anni = g.eta / ANNO_SIMULAZIONE_GIORNI
        for tappa in tappe:
            if tappa not in somme and anni >= tappa:
                somme[tappa] = sum(getattr(g, c + "_allenata") for c in allenamento.CARATTERISTICHE)
    return somme


@pytest.mark.parametrize("punti_al_giorno", [1.0, 2.55])
def test_l_apprendista_rapido_impara_e_dimentica_in_fretta_ma_resta_un_tratto(punti_al_giorno):
    """
    D31: l'apprendista rapido impara e dimentica in fretta. Da giovane è avanti al gemello senza il
    tratto; con gli anni l'oblio lo raggiunge, ma a 50 anni ha ancora almeno i tre quarti della sua
    allenata, da tesserato del computer, un punto al giorno, e da tesserato dell'utente, 2,55.
    Con l'oblio a 0,98 al mese ne aveva poco più della metà, e il tratto era quasi sempre un difetto.
    """
    gemello = _allenata_negli_anni(False, punti_al_giorno)
    apprendista = _allenata_negli_anni(True, punti_al_giorno)
    assert apprendista[25] > gemello[25]
    assert apprendista[50] >= 0.75 * gemello[50]
