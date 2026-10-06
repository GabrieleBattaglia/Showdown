"""Test del motore di partita, che non stampa nulla, e del mondo che avanza col tempo."""

import datetime
import random

import pytest

from costanti import MODALITA_OUTPUT_FILE, NOME_FILE_LOG_PARTITE
from mondo import Mondo
from partita import MotorePartita
from utilita import in_ora_locale

INIZIO = datetime.datetime(2026, 1, 1, 12, 0)
# L'istante reale dell'ultimo avanzamento, che il mondo conta in UTC.
ANCORA = datetime.datetime(2026, 1, 1, 11, 0, tzinfo=datetime.UTC)


@pytest.fixture
def mondo():
    random.seed(4242)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(40, INIZIO)
    return m


def test_mondo_senza_notifica_non_stampa(mondo, capsys):
    assert len(mondo.giocatori) == 40
    assert sorted(mondo.giocatori) == list(range(1, 41))
    assert capsys.readouterr().out == ""


def test_partita_silenziosa_e_coerente(mondo, capsys):
    motore = MotorePartita(mondo)
    g1, g2 = mondo.giocatori[1], mondo.giocatori[2]
    g1.infortunato = g2.infortunato = False
    risultato = motore.gioca_partita(1, 2, 5)
    assert capsys.readouterr().out == ""
    assert risultato["error"] is None
    assert {risultato["vincitore_id"], risultato["perdente_id"]} == {1, 2}
    vinti_dal_primo = sum(1 for a, b in risultato["punteggio_set"] if a > b)
    vinti_dal_secondo = len(risultato["punteggio_set"]) - vinti_dal_primo
    assert max(vinti_dal_primo, vinti_dal_secondo) == 3
    assert (vinti_dal_primo == 3) == (risultato["vincitore_id"] == 1)
    for a, b in risultato["punteggio_set"]:
        assert max(a, b) >= 11
    vincitore = mondo.giocatori[risultato["vincitore_id"]]
    assert vincitore.partitevinte == 1
    assert vincitore.puntiesperienza > 0


def test_partita_con_mostra_e_cronaca_su_file(mondo, cartella_di_prova):
    righe = []
    for g in mondo.giocatori.values():
        g.infortunato = False
    MotorePartita(mondo, mostra=righe.append).gioca_partita(3, 4, 3, MODALITA_OUTPUT_FILE)
    assert righe[0].startswith("\n--- Inizio Partita: ID 3 vs ID 4")
    assert any(r.startswith("Cronaca completa salvata in:") for r in righe)
    assert (cartella_di_prova / NOME_FILE_LOG_PARTITE).read_text(encoding="utf-8").count("PARTITA TERMINATA") == 1


def test_partita_rifiutata(mondo):
    righe = []
    motore = MotorePartita(mondo, mostra=righe.append)
    assert motore.gioca_partita(1, 1, 3)["error"] == "I giocatori devono essere diversi."
    assert motore.gioca_partita(1, 999, 3)["error"] == "ID giocatore non valido."
    assert righe[-1] == "ERRORE: ID giocatore non valido."


def test_resistenza_piena_nel_primo_set(mondo):
    motore = MotorePartita(mondo)
    for g in mondo.giocatori.values():
        assert motore._calcola_resistenza_set(g, 1) == 1.0
        assert 0.01 <= motore._calcola_resistenza_set(g, 5) < 1.0


def test_avanzamento_del_tempo(mondo):
    mondo.datetime_ultimo_run_reale = ANCORA
    eta_prima = {gid: g.eta for gid, g in mondo.giocatori.items()}
    messaggi = []
    mondo.notifica = messaggi.append
    rapporto = mondo.processa_tempo_trascorso(ANCORA + datetime.timedelta(hours=17))
    assert rapporto["ticks"] == rapporto["giorni"] == 2
    assert mondo.datetime_corrente_simulazione == INIZIO + datetime.timedelta(days=2)
    # L'ora che avanza resta per la volta dopo.
    assert mondo.datetime_ultimo_run_reale == ANCORA + datetime.timedelta(hours=16)
    for gid, eta in eta_prima.items():
        if gid not in mondo._ids_morti_processati_sessione:
            assert mondo.giocatori[gid].eta == eta + 2
    # I nuovi della sessione restano, quelli di prima compresi: si contano i nati nei due giorni.
    assert 2 <= len([gid for gid in mondo.nuovi_giocatori_sessione if gid not in eta_prima]) <= 14
    assert any("Processando 2 tick" in m for m in messaggi)


def test_niente_avanzamento_prima_di_otto_ore(mondo):
    mondo.datetime_ultimo_run_reale = ANCORA
    messaggi = []
    mondo.notifica = messaggi.append
    assert mondo.processa_tempo_trascorso(ANCORA + datetime.timedelta(hours=3))["ticks"] == 0
    assert mondo.datetime_corrente_simulazione == INIZIO
    assert mondo.datetime_ultimo_run_reale == ANCORA
    prossimo = in_ora_locale(ANCORA + datetime.timedelta(hours=8))
    assert messaggi == [f"INFO: Prox aggiornamento sim alle {prossimo:%H:%M:%S del %d/%m/%Y} (tra 5h 0m)."]


def test_polisportive_del_computer(mondo):
    nome = mondo.crea_polisportiva_cpu(INIZIO)
    assert nome.startswith("PoliTeam01 ")
    assert mondo.polisportive[nome].is_cpu_controlled
    assert mondo.crea_polisportiva_cpu(INIZIO).startswith("PoliTeam02 ")
    tesserati, svincolati, comprati = mondo._esegui_logica_cpu_polisportive()
    assert svincolati == comprati == 0
    assert tesserati == sum(len(p.tesserati) for p in mondo.polisportive.values())
    for p in mondo.polisportive.values():
        for gid in p.tesserati:
            assert mondo.giocatori[gid].appartenenza == p.nome
