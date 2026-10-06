"""
Test della tappa 7 sul motore: le polisportive dell'utente, con fondazione, offerte, svincoli e
chiusura; le regole nuove del computer, decisione D19; ritirati e morti che liberano il posto,
problema P4; un nome solo per ogni polisportiva, problema P16; la vetrina dei liberi, problema
P18; la migrazione dei salvataggi al formato 3.
"""

import datetime
import json
import random
import re

import pytest

import archivio
import mondo as modulo_mondo
from costanti import FILE_MONDO, LIMITE_MOVIMENTI_PER_TICK, MAX_TESSERATI_POLISPORTIVA
from modelli import Giocatore, Polisportiva
from mondo import Mondo, _Vetrina

INIZIO = datetime.datetime(2026, 5, 1, 12, 0)
ANCORA = datetime.datetime(2026, 5, 1, 10, 0, tzinfo=datetime.UTC)


@pytest.fixture
def mondo():
    random.seed(707)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.datetime_ultimo_run_reale = ANCORA
    m.crea_giocatori_casuali(40, INIZIO, annuncia=False)
    return m


def _nome(g):
    return f"{g.nome} {g.cognome}"


def _cpu_con_gloria(mondo, gloria=10_000):
    """Una polisportiva del computer che si può permettere chiunque."""
    poli = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    poli.gloria = gloria
    return poli


def _solo_i_primi_liberi(mondo, quanti):
    """Al mercato restano soltanto i primi giocatori: gli altri si ritirano."""
    for gid, g in mondo.giocatori.items():
        if gid > quanti:
            g.ritirato = True


# La vetrina dei liberi.

def test_la_vetrina_trova_il_primo_alla_portata():
    random.seed(5)
    richieste = [random.randint(1, 100) for _ in range(37)]
    vetrina = _Vetrina(richieste)
    tolti = set()
    for _ in range(300):
        gloria = random.randint(0, 110)
        da = random.randint(0, 40)
        atteso = next((i for i in range(da, len(richieste)) if i not in tolti and richieste[i] <= gloria), None)
        assert vetrina.primo(gloria, da) == atteso
        if atteso is not None and random.random() < .3:
            vetrina.togli(atteso)
            tolti.add(atteso)
    assert _Vetrina([]).primo(1000) is None
    assert _Vetrina([7]).primo(7) == 0


# Nomi e polisportive dell'utente.

def test_un_nome_solo_come_lo_si_scrive(mondo):
    poli = mondo.fonda_polisportiva("  Circolo   dei ciechi ")
    assert poli.nome == "Circolo dei ciechi"
    assert mondo.polisportive["Circolo dei ciechi"] is poli
    assert mondo.miapolisportiva_attiva is poli
    assert not poli.protetta
    assert mondo.trova_polisportiva("CIRCOLO DEI CIECHI") is poli
    assert mondo.problema_nome_polisportiva("circolo DEI ciechi") == "Esiste già una polisportiva che si chiama Circolo dei ciechi."
    assert mondo.problema_nome_polisportiva("Club") == "Il nome deve avere da 5 a 50 caratteri."
    with pytest.raises(ValueError, match="Esiste già"):
        mondo.fonda_polisportiva("Circolo dei Ciechi")
    protetta = mondo.fonda_polisportiva("Club protetto", "segreta", attiva=False)
    assert protetta.protetta and protetta.verifica_password("segreta")
    assert mondo.miapolisportiva_attiva is poli


def test_i_nomi_del_computer(mondo):
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    assert re.fullmatch(r"PoliTeam01 [A-Z][a-z]+-[A-Z][a-z]+", cpu.nome)
    assert mondo.polisportive[cpu.nome] is cpu
    # Una polisportiva nata prima della tappa 7, con le maiuscole ritoccate, tiene comunque il suo numero.
    vecchia = Polisportiva("Politeam02 Abab-Cdcd", None, INIZIO, is_cpu_controlled=True)
    mondo.polisportive[vecchia.nome] = vecchia
    assert mondo.crea_polisportiva_cpu(INIZIO).startswith("PoliTeam03 ")


def test_offerte_mosse_e_diari(mondo, monkeypatch):
    poli = mondo.fonda_polisportiva("Club di prova")
    primo, secondo = mondo.giocatori[1], mondo.giocatori[2]
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: False)
    accetta, probabilita = mondo.offerta(poli, primo)
    assert not accetta and probabilita == pytest.approx(50.)
    assert poli.movimenti_oggi == 1 and primo.appartenenza == "*"
    assert primo.diario[0]["testo"].startswith("Rifiuta l'offerta di Club di prova, con un ingaggio di ")
    assert poli.diario[0]["testo"].startswith(f"{_nome(primo)} rifiuta l'offerta, con un ingaggio di ")
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    assert mondo.offerta(poli, secondo)[0]
    assert secondo.appartenenza == "Club di prova" and poli.tesserati == [2]
    assert secondo.diario[0]["testo"].startswith("Tesserat")
    assert poli.diario[0]["testo"].startswith(f"Tesserato {_nome(secondo)}, con un ingaggio di ")
    assert mondo.problema_offerta(poli, secondo).startswith(f"{_nome(secondo)} è già tesserat")
    mondo.giocatori[3].ritirato = True
    assert mondo.problema_offerta(poli, mondo.giocatori[3]).endswith("dall'attività.")
    poli.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    with pytest.raises(ValueError, match="finito le mosse"):
        mondo.offerta(poli, mondo.giocatori[4])
    poli.movimenti_oggi = 0
    poli.tesserati = list(range(100, 100 + MAX_TESSERATI_POLISPORTIVA))
    assert mondo.problema_offerta(poli, mondo.giocatori[4]) == f"Club di prova ha già {MAX_TESSERATI_POLISPORTIVA} tesserati, il massimo."


def test_svincolo_e_chiusura(mondo, monkeypatch):
    poli = mondo.fonda_polisportiva("Club di prova")
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    for gid in (1, 2, 3):
        mondo.offerta(poli, mondo.giocatori[gid])
    mondo.svincola(poli, mondo.giocatori[2])
    assert poli.tesserati == [1, 3] and mondo.giocatori[2].appartenenza == "*"
    assert poli.movimenti_oggi == 4
    assert poli.diario[0]["testo"] == f"Svincolato {_nome(mondo.giocatori[2])}."
    assert mondo.giocatori[2].diario[0]["testo"].endswith(" da Club di prova.")
    with pytest.raises(ValueError, match="non è"):
        mondo.svincola(poli, mondo.giocatori[2])
    assert mondo.chiudi_polisportiva(poli) == 2
    assert "Club di prova" not in mondo.polisportive
    assert mondo.miapolisportiva_attiva is None
    assert mondo.giocatori[1].appartenenza == "*"
    assert mondo.giocatori[1].diario[0]["testo"].endswith(": Club di prova ha chiuso.")


def test_chi_si_ritira_o_muore_libera_il_posto(mondo, monkeypatch):
    monkeypatch.setattr(modulo_mondo, "PROB_USCITA_PREMATURA_GIORNALIERA", 0)
    poli = mondo.fonda_polisportiva("Club di prova")
    ritirato, morto = mondo.giocatori[1], mondo.giocatori[2]
    for g in (ritirato, morto):
        mondo._tessera(poli, g)
    ritirato.etaritiro = ritirato.eta + 1
    morto.etamorte = morto.eta + 1
    mondo.processa_tempo_trascorso(ANCORA + datetime.timedelta(hours=8))
    assert poli.tesserati == []
    assert ritirato.ritirato and ritirato.appartenenza == "*"
    assert ritirato.diario[0]["testo"] == f"Si ritira dall'attività, a {int(ritirato.eta_anni)} anni, e lascia Club di prova."
    testi_club = [voce["testo"] for voce in poli.diario]
    assert f"{_nome(ritirato)} si ritira dall'attività e lascia la polisportiva." in testi_club
    assert f"{_nome(morto)} muore." in testi_club
    assert morto.id in mondo._ids_morti_processati_sessione


def test_gli_ipovedenti_chiedono_un_decimo_in_meno():
    random.seed(3)
    g = Giocatore(id_giocatore=1, datetime_creazione_sim=INIZIO)
    g.ipovedente = False
    piena = g.gloria_richiesta
    g.ipovedente = True
    assert abs(g.gloria_richiesta - piena * .9) <= 1


# Le regole del computer, decisione D19.

def test_il_computer_prova_ogni_candidato_una_volta_al_giorno(mondo, monkeypatch):
    _solo_i_primi_liberi(mondo, 3)
    poli = _cpu_con_gloria(mondo)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: False)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (0, 0, 0)
    assert poli.movimenti_oggi == 3
    assert poli.tesserati == []


def test_sceglie_prima_chi_ha_piu_gloria(mondo, monkeypatch):
    _solo_i_primi_liberi(mondo, 1)
    piccola = _cpu_con_gloria(mondo, 5_000)
    grande = _cpu_con_gloria(mondo, 10_000)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (1, 0, 0)
    assert grande.tesserati == [1] and piccola.tesserati == []
    assert piccola.movimenti_oggi == 0


def _rosa_piena(mondo, valore_tesserati, valore_liberi):
    """Una polisportiva del computer con i primi quindici giocatori, e valori dati a tesserati e liberi."""
    poli = _cpu_con_gloria(mondo)
    for gid in range(1, MAX_TESSERATI_POLISPORTIVA + 1):
        mondo._tessera(poli, mondo.giocatori[gid])
    for gid, g in mondo.giocatori.items():
        g.indice_collettivo_valore = (valore_tesserati if gid <= MAX_TESSERATI_POLISPORTIVA else valore_liberi) + gid
    poli.movimenti_oggi = 0
    return poli


def test_a_rosa_piena_ogni_tanto_ne_prova_uno_piu_forte(mondo, monkeypatch):
    poli = _rosa_piena(mondo, 100, 100)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (1, 1, 0)
    forte, debole = mondo.giocatori[40], mondo.giocatori[1]
    assert 40 in poli.tesserati and 1 not in poli.tesserati
    assert len(poli.tesserati) == MAX_TESSERATI_POLISPORTIVA
    assert debole.appartenenza == "*" and forte.appartenenza == poli.nome
    assert debole.diario[0]["testo"].endswith(f" da {poli.nome}, che al suo posto ha tesserato {_nome(forte)}.")
    assert poli.diario[0]["testo"].startswith(f"Tesserato {_nome(forte)} al posto di {_nome(debole)}, che torna ")
    assert poli.movimenti_oggi == 1


def test_nessuno_scambio_senza_un_libero_piu_forte(mondo, monkeypatch):
    poli = _rosa_piena(mondo, 200, 100)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (0, 0, 0)
    assert poli.movimenti_oggi == 0


def test_nessuno_scambio_quando_non_tocca(mondo, monkeypatch):
    poli = _rosa_piena(mondo, 100, 100)
    monkeypatch.setattr(modulo_mondo, "PROB_SCAMBIO_CPU_GIORNALIERA", 0)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (0, 0, 0)
    assert poli.movimenti_oggi == 0


# Il salvataggio.

def test_un_salvataggio_del_formato_2_si_aggiorna(mondo, cartella_di_prova):
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    mia = mondo.fonda_polisportiva("Club di prova")
    for gid in (1, 2, 3):
        mondo._tessera(cpu, mondo.giocatori[gid])
    mondo._tessera(mia, mondo.giocatori[4])
    contenuto = archivio.componi(mondo)
    # Com'era il formato 2: la polisportiva del computer registrata sotto il nome generato, con il nome ritoccato
    # dalle maiuscole nella scheda e nei tesserati; un ritirato e un assente ancora fra i tesserati.
    dati = contenuto["mondo"]
    voce = dati["polisportive"].pop(cpu.nome)
    chiave = "PoliTeam01 " + cpu.nome.split(" ", 1)[1].lower()
    ritoccato = chiave.title()
    voce["nome"] = ritoccato
    voce["tesserati"] = [1, 2, 3, 999]
    dati["polisportive"][chiave] = voce
    for g in dati["giocatori"]:
        if g["id"] in (1, 2, 3):
            g["appartenenza"] = ritoccato
        if g["id"] == 3:
            g["ritirato"] = True
    contenuto["formato"] = 2
    percorso = cartella_di_prova / FILE_MONDO
    percorso.write_text(json.dumps({**contenuto, "firma": archivio.firma(contenuto)}), encoding="utf-8")
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert sorted(ricaricato.polisportive) == sorted([ritoccato, "Club di prova"])
    assert ricaricato.polisportive[ritoccato].tesserati == [1, 2]
    assert ricaricato.giocatori[1].appartenenza == ritoccato
    assert ricaricato.giocatori[3].appartenenza == "*"
    assert ricaricato.miapolisportiva_attiva is ricaricato.polisportive["Club di prova"]
    assert ricaricato.polisportive["Club di prova"].tesserati == [4]
    assert archivio.salva(ricaricato)
    assert archivio.leggi(percorso)["formato"] == archivio.FORMATO


def test_una_polisportiva_sotto_un_altro_nome_non_si_accetta(mondo):
    mondo.fonda_polisportiva("Club di prova")
    contenuto = archivio.componi(mondo)
    dati = contenuto["mondo"]
    dati["polisportive"]["Altro nome"] = dati["polisportive"].pop("Club di prova")
    dati["polisportiva_attiva"] = "Altro nome"
    with pytest.raises(archivio.ErroreSalvataggio, match="sotto un altro nome"):
        archivio.costruisci(contenuto, Mondo())
