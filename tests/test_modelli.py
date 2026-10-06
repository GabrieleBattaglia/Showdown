"""Test della nascita dei giocatori, della gloria richiesta, della probabilità di accettazione e delle polisportive."""

import datetime
import random

import pytest

from costanti import (
    ARCHETIPI_ALLENAMENTO,
    ATTRIBUTI_ALLENABILI,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    CARATTERISTICHE_FISICHE_BASE,
    ETA_MAX_CREAZIONE_GIORNI,
    ETA_MIN_CREAZIONE_GIORNI,
    GLORIA_RICHIESTA_MINIMA_ASSOLUTA,
    MAX_GLORIA_RICHIESTA,
    MAX_PRECISIONE_RESISTENZA,
    MAX_SKILL_VALUE,
    giorni_da_anni,
)
from modelli import Giocatore, Polisportiva, probabilita_accettazione

NASCITA = datetime.datetime(2026, 1, 1)


@pytest.fixture
def giocatori():
    random.seed(20261006)
    return [Giocatore(i, NASCITA) for i in range(1, 61)]


def test_nascita_dentro_i_limiti(giocatori):
    for g in giocatori:
        assert g.sesso in ("m", "f")
        assert ETA_MIN_CREAZIONE_GIORNI <= g.eta <= ETA_MAX_CREAZIONE_GIORNI
        assert g.eta < g.etaritiro and g.eta < g.etamorte
        assert g.nome and g.cognome and g.nome != "*"
        assert g.archetipo_allenamento in ARCHETIPI_ALLENAMENTO
        assert g.descrizione_fisica
        assert not (g.mancino and g.ambidestro)
        for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
            tetto = MAX_PRECISIONE_RESISTENZA if nome_base in CARATTERISTICHE_FISICHE_BASE else MAX_SKILL_VALUE
            assert 0 <= getattr(g, nome_base) <= tetto * 0.6
        for nome_allenato in ATTRIBUTI_ALLENABILI:
            assert getattr(g, nome_allenato) == 0.0


def test_indice_di_valore(giocatori):
    for g in giocatori:
        bonus = 33 * sum(bool(getattr(g, f)) for f in ("ambidestro", "giocorapido", "cambiovelocita"))
        somma = sum(getattr(g, a) for a in ATTRIBUTI_BASE_CON_ALLENABILI)
        assert g.indice_collettivo_valore == pytest.approx(somma + bonus)


def test_parametri_alla_nascita():
    random.seed(1)
    g = Giocatore(7, NASCITA, ipovedente="s", eta=1500, attacco_allenata=99, precisione_allenata="3.5", puntiesperienza="12")
    assert g.ipovedente is True
    assert g.eta == 1500
    assert g.attacco_allenata == 20.0
    assert g.precisione_allenata == 3.5
    assert g.puntiesperienza == 12


def _giocatore_neutro(eta_anni, icv):
    random.seed(5)
    g = Giocatore(1, NASCITA)
    g.ambidestro = g.giocorapido = g.cambiovelocita = False
    g.eta = giorni_da_anni(eta_anni)
    g.indice_collettivo_valore = icv
    return g


def test_gloria_richiesta_al_picco():
    assert _giocatore_neutro(17, 100).gloria_richiesta == int(100 * 0.9 * 2.7 + 12)


def test_gloria_richiesta_cala_con_l_eta():
    assert _giocatore_neutro(55, 100).gloria_richiesta == int(100 * 0.9 * 0.1 + 12)
    assert _giocatore_neutro(30, 100).gloria_richiesta < _giocatore_neutro(20, 100).gloria_richiesta


def test_gloria_richiesta_ai_bordi():
    assert _giocatore_neutro(60, 0).gloria_richiesta == max(GLORIA_RICHIESTA_MINIMA_ASSOLUTA, 12)
    assert _giocatore_neutro(17, 10000).gloria_richiesta == MAX_GLORIA_RICHIESTA


def test_probabilita_accettazione():
    assert probabilita_accettazione(100, 100) == pytest.approx(50.0)
    assert probabilita_accettazione(70, 100) == 3.0
    assert probabilita_accettazione(130, 100) == 97.0
    assert probabilita_accettazione(115, 100) == pytest.approx(73.5)
    assert probabilita_accettazione(50, 0) == 97.0


def test_polisportiva_tesserati_e_indice():
    p = Polisportiva("prova di club", None, NASCITA)
    assert p.nome == "Prova Di Club"
    p.aggiungi_tesserato(3, 120.0)
    p.aggiungi_tesserato(3, 120.0)
    p.aggiungi_tesserato(4, 80.0)
    assert p.tesserati == [3, 4]
    assert p.indicecollettivotesserati == 200.0
    p.rimuovi_tesserato(3, 120.0)
    p.rimuovi_tesserato(99, 50.0)
    assert p.tesserati == [4]
    assert p.indicecollettivotesserati == 80.0


def test_polisportiva_del_computer_senza_password():
    assert Polisportiva("PoliTeam01 abab-cdcd", "segreta", NASCITA, is_cpu_controlled=True).password is None


def test_eta_della_polisportiva():
    p = Polisportiva("Club", None, NASCITA)
    assert p.eta_sim(NASCITA + datetime.timedelta(days=110)) == "1/0/2 sim"
    assert p.eta_sim(None) == "Età N/D"
