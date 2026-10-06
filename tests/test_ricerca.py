"""Test della ricerca dei giocatori: ambiti, condizioni e il minore stretto del problema P11."""

import datetime
import random

import pytest

import ricerca
from mondo import Mondo

ORA = datetime.datetime(2026, 10, 6, 18, 0)


@pytest.fixture
def mondo():
    random.seed(5)
    m = Mondo()
    m.crea_giocatori_casuali(30, ORA)
    return m


def test_numeri_con_virgola_o_punto():
    assert ricerca.leggi_numero("12,5") == 12.5
    assert ricerca.leggi_numero(" 150 ") == 150.0
    with pytest.raises(ValueError):
        ricerca.leggi_numero("tanto")


def test_minore_e_maggiore_stretti(mondo):
    soglia = mondo.giocatori[1].indice_collettivo_valore
    minori = ricerca.cerca(mondo, "tutti", "valore", "minore", soglia)
    maggiori = ricerca.cerca(mondo, "tutti", "valore", "maggiore", soglia)
    assert 1 not in minori and 1 not in maggiori
    assert sorted(minori + maggiori + [1]) == sorted(mondo.giocatori)


def test_testo_senza_badare_alle_maiuscole(mondo):
    cognome = mondo.giocatori[3].cognome
    assert 3 in ricerca.cerca(mondo, "tutti", "cognome", "contiene", cognome.upper())


def test_si_e_no(mondo):
    si = ricerca.cerca(mondo, "tutti", "ipovedente", "si")
    no = ricerca.cerca(mondo, "tutti", "ipovedente", "no")
    assert sorted(si + no) == sorted(mondo.giocatori)
    assert all(mondo.giocatori[g].ipovedente for g in si)


def test_ambiti(mondo):
    mondo.giocatori[2].ritirato = True
    mondo.giocatori[4].appartenenza = "Club"
    mondo._ids_morti_processati_sessione.add(6)
    assert 2 not in ricerca.ids_ambito(mondo, "attivi") and 2 in ricerca.ids_ambito(mondo, "ritirati")
    assert ricerca.ids_ambito(mondo, "tesserati") == [4]
    assert ricerca.ids_ambito(mondo, "usciti") == [6]
    assert 6 not in ricerca.ids_ambito(mondo, "liberi")
    mondo.risultati_ultima_ricerca = [9, 3]
    assert ricerca.ids_ambito(mondo, "trovati") == [3, 9]
    with pytest.raises(ValueError):
        ricerca.ids_ambito(mondo, "altrove")


def test_caratteristiche_di_gioco(mondo):
    trovati = ricerca.cerca(mondo, "attivi", "bomba_base", "maggiore", 5)
    assert all(mondo.giocatori[g]._get_valore_totale("bomba_base") > 5 for g in trovati)
    assert len(ricerca.CRITERI) == 29
    with pytest.raises(ValueError):
        ricerca.cerca(mondo, "tutti", "valore", "contiene", 3)
