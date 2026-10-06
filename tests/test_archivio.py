"""Test dell'archivio: salvataggio e caricamento in una cartella temporanea, e lettore che rifiuta le classi estranee."""

import datetime
import io
import os
import pickle
import random

import pytest

import archivio
from modelli import Polisportiva
from mondo import Mondo

INIZIO = datetime.datetime(2026, 3, 1, 9, 30)


def _mondo_popolato():
    random.seed(99)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.datetime_ultimo_run_reale = INIZIO
    m.crea_giocatori_casuali(12, INIZIO)
    m.crea_polisportiva_cpu(INIZIO)
    mia = Polisportiva("Club Di Prova", None, INIZIO)
    m.polisportive[mia.nome] = mia
    mia.aggiungi_tesserato(3, m.giocatori[3].indice_collettivo_valore)
    m.miapolisportiva_attiva = mia
    return m


def test_salva_e_ricarica(cartella_di_prova):
    originale = _mondo_popolato()
    originale._ids_morti_processati_sessione.add(5)
    messaggi = []
    originale.notifica = messaggi.append
    assert archivio.salva(originale)
    assert "  (Rimuovendo 1 giocatori morti/usciti)" in messaggi
    ricaricato = Mondo(notifica=messaggi.append)
    archivio.carica(ricaricato)
    assert sorted(ricaricato.giocatori) == [g for g in range(1, 13) if g != 5]
    assert ricaricato.giocatori[3].nome == originale.giocatori[3].nome
    assert vars(ricaricato.giocatori[7]) == vars(originale.giocatori[7])
    assert ricaricato.datetime_corrente_simulazione == INIZIO
    assert ricaricato.miapolisportiva_attiva.nome == originale.miapolisportiva_attiva.nome
    assert ricaricato.miapolisportiva_attiva.tesserati == [3]
    assert set(os.listdir(cartella_di_prova)) == {"sd-gamestate.db", "sd-players.db", "sd-polisport.db"}


def test_mondo_nuovo_se_non_ci_sono_salvataggi():
    random.seed(1)
    messaggi = []
    m = Mondo(notifica=messaggi.append)
    archivio.carica(m)
    assert len(m.giocatori) == 50
    assert m.nuovi_giocatori_sessione == []
    assert "File giocatori 'sd-players.db' non trovato." in messaggi


def test_lettore_rifiuta_le_classi_estranee():
    contenuto = pickle.dumps(os.system)
    with pytest.raises(pickle.UnpicklingError):
        archivio.LettoreSalvataggi(io.BytesIO(contenuto)).load()


def test_lettore_riporta_le_classi_di_sd_py_ai_modelli():
    # Un salvataggio del vecchio sd.py registra la classe come __main__.Polisportiva.
    contenuto = pickle.dumps({"chiave": datetime.date(2025, 1, 2)})
    assert archivio.LettoreSalvataggi(io.BytesIO(contenuto)).load() == {"chiave": datetime.date(2025, 1, 2)}
    classe = archivio.LettoreSalvataggi(io.BytesIO(b"")).find_class("__main__", "Polisportiva")
    assert classe is archivio.Polisportiva
