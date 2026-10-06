"""Test del calendario del simulatore, del tiro del caso, dei percorsi e della coerenza delle tabelle."""

import os
import random

import percorsi
from costanti import ANNO_SIMULAZIONE_GIORNI, discrepanze_raggruppamenti, giorni_da_anni
from utilita import caso, converti_giorni_sim, converti_in_tempo, formatta_eta_sim


def test_gruppi_di_caratteristiche_coerenti():
    mancanti, in_piu = discrepanze_raggruppamenti()
    assert mancanti == set()
    assert in_piu == set()


def test_giorni_da_anni():
    assert giorni_da_anni(1) == ANNO_SIMULAZIONE_GIORNI
    assert giorni_da_anni(9.5) == 1026


def test_eta_per_esteso_e_breve():
    assert formatta_eta_sim(0) == "0 anni (compiuti)"
    assert formatta_eta_sim(108) == "1 anno (compiuti)"
    assert formatta_eta_sim(109) == "1 anno, 0 mesi e 1 giorno"
    assert formatta_eta_sim(108 * 20 + 9 + 2) == "20 anni, 1 mese e 2 giorni"
    assert formatta_eta_sim(108 * 20 + 9 + 2, formato_breve=True) == "20/1/2"


def test_eta_non_valida():
    assert formatta_eta_sim(None) == "Età N/D"


def test_giorni_come_data_partono_da_uno():
    assert converti_giorni_sim(0) == (0, 1, 1)
    assert converti_giorni_sim(0, per_eta=True) == (0, 0, 0)
    assert converti_giorni_sim(-5) == (0, 1, 1)


def test_durata_in_ore_minuti_secondi():
    assert converti_in_tempo(3725) == (1, 2, 5)
    assert converti_in_tempo("niente") == (0, 0, 0)


def test_caso_rispetta_i_bordi():
    random.seed(3)
    assert not any(caso(0) for _ in range(1000))
    assert not any(caso(-20) for _ in range(1000))
    uscite = sum(caso(25) for _ in range(20000))
    assert 4500 < uscite < 5500


def test_percorsi_dei_file_scritti(cartella_di_prova):
    assert percorsi.percorso("prova.txt") == os.path.join(str(cartella_di_prova), "prova.txt")


def test_risorse_nella_cartella_dati():
    assert os.path.exists(percorsi.risorsa(os.path.join("dati", "cognomi.txt")))
