"""
Test della tappa 6: il tempo del mondo contato in UTC, un giorno simulato alla volta con il resto
che non si perde, i diari di giocatori e polisportive, il registro delle vecchie glorie.
"""

import datetime
import json
import random

import pytest

import mondo as modulo_mondo
import testi
from costanti import CREA_NUOVI_PER_TICK_RANGE, NOME_FILE_LOG_USCITE
from modelli import Giocatore, Polisportiva, annota_allenamento, annota_diario
from mondo import Mondo
from partita import MotorePartita
from utilita import in_ora_locale

INIZIO = datetime.datetime(2026, 3, 20, 12, 0)
# La sera prima del passaggio all'ora legale del 29 marzo 2026: in UTC le otto ore restano otto.
ANCORA = datetime.datetime(2026, 3, 28, 20, 0, tzinfo=datetime.UTC)
ORA = datetime.timedelta(hours=1)
GIORNO = datetime.timedelta(days=1)


@pytest.fixture
def mondo(monkeypatch):
    random.seed(606)
    monkeypatch.setattr(modulo_mondo, "PROB_USCITA_PREMATURA_GIORNALIERA", 0)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.datetime_ultimo_run_reale = ANCORA
    m.crea_giocatori_casuali(30, INIZIO, annuncia=False)
    return m


# Il tempo.

def test_un_giorno_ogni_otto_ore_e_il_resto_non_si_perde(mondo):
    assert mondo.ticks_maturati(ANCORA + 8 * ORA - datetime.timedelta(microseconds=1)) == 0
    assert mondo.ticks_maturati(ANCORA + 8 * ORA) == 1
    rapporto = mondo.processa_tempo_trascorso(ANCORA + 17 * ORA)
    assert rapporto["ticks"] == rapporto["giorni"] == 2
    assert mondo.datetime_ultimo_run_reale == ANCORA + 16 * ORA
    assert mondo.datetime_corrente_simulazione == INIZIO + 2 * GIORNO
    assert mondo.processa_tempo_trascorso(ANCORA + 23 * ORA)["ticks"] == 0
    assert mondo.datetime_ultimo_run_reale == ANCORA + 16 * ORA
    # L'ora avanzata prima si somma alle sette di adesso: fanno otto, un giorno.
    assert mondo.processa_tempo_trascorso(ANCORA + 24 * ORA)["ticks"] == 1
    assert mondo.datetime_ultimo_run_reale == ANCORA + 24 * ORA
    assert mondo.datetime_corrente_simulazione == INIZIO + 3 * GIORNO


def test_l_orologio_che_torna_indietro_non_fa_danni(mondo):
    assert mondo.processa_tempo_trascorso(ANCORA - 5 * ORA)["ticks"] == 0
    assert mondo.datetime_ultimo_run_reale == ANCORA
    assert mondo.datetime_corrente_simulazione == INIZIO
    assert mondo.testo_prossimo_sblocco(ANCORA - 5 * ORA).endswith("(tra 13h 0m).")


def test_ogni_giorno_ha_la_sua_elaborazione(mondo):
    eta_prima = {gid: g.eta for gid, g in mondo.giocatori.items()}
    rapporto = mondo.processa_tempo_trascorso(ANCORA + 24 * ORA)
    assert rapporto["ora"] == in_ora_locale(ANCORA + 24 * ORA)
    for gid, eta in eta_prima.items():
        assert mondo.giocatori[gid].eta == eta + 3
    nuovi = [mondo.giocatori[gid] for gid in mondo.nuovi_giocatori_sessione if gid not in eta_prima]
    assert rapporto["nuovi"] == len(nuovi)
    assert 3 <= len(nuovi) <= 21
    # Ciascuno nasce nel suo giorno, e il diario lo ricorda.
    assert {g.datetime_creazione_sim for g in nuovi} <= {INIZIO + n * GIORNO for n in (1, 2, 3)}
    for g in nuovi:
        assert g.diario[-1]["data"] == g.datetime_creazione_sim


def test_le_nascite_non_dipendono_da_quando_si_apre_il_gioco(mondo):
    """Quaranta giorni elaborati insieme fanno nascere quanto quaranta giorni elaborati uno alla volta."""
    rapporto = mondo.processa_tempo_trascorso(ANCORA + 40 * 8 * ORA)
    assert rapporto["giorni"] == 40
    minimo, massimo = CREA_NUOVI_PER_TICK_RANGE
    assert 40 * minimo <= rapporto["nuovi"] <= 40 * massimo
    assert rapporto["nuovi"] > 50


# I diari.

def test_i_diari_cominciano_alla_nascita():
    random.seed(1)
    g = Giocatore(id_giocatore=1, datetime_creazione_sim=INIZIO)
    assert g.diario == [{"data": INIZIO, "testo": f"Entra nel mondo dello showdown, a {int(g.eta_anni)} anni: comincia a giocare, e la sua esperienza parte da zero."}]
    p = Polisportiva("Club Di Prova", None, INIZIO)
    assert p.diario == [{"data": INIZIO, "testo": "Fondata."}]


def test_gli_allenamenti_della_stessa_caratteristica_si_fondono():
    diario = []
    domani = INIZIO + GIORNO
    annota_allenamento(diario, INIZIO, "attacco_base", 10.0, 10.4)
    annota_allenamento(diario, domani, "attacco_base", 10.4, 10.9)
    assert diario == [{"data": domani, "allenamento": "attacco_base", "da": 10.0, "a": 10.9}]
    annota_allenamento(diario, domani, "difesa_base", 8.0, 8.2)
    annota_diario(diario, domani, "Vince l'amichevole.")
    annota_allenamento(diario, domani, "difesa_base", 8.2, 8.5)
    assert [voce.get("allenamento") for voce in diario] == ["difesa_base", None, "difesa_base", "attacco_base"]
    assert testi.voce_diario(diario[0]) == "21 marzo 2026: Allenamento di difesa, da 8,2 a 8,5."
    assert testi.voce_diario(diario[1]) == "21 marzo 2026: Vince l'amichevole."


def test_il_diario_passa_dal_salvataggio():
    random.seed(2)
    g = Giocatore(id_giocatore=7, datetime_creazione_sim=INIZIO)
    g.annota_allenamento(INIZIO + GIORNO, "bomba_base", 5.0, 5.5)
    assert Giocatore.da_dizionario(json.loads(json.dumps(g.a_dizionario()))).diario == g.diario
    dati = g.a_dizionario()
    dati["diario"][0]["allenamento"] = "volare_base"
    with pytest.raises(ValueError, match="diario"):
        Giocatore.da_dizionario(dati)


def test_morte_ritiro_e_vecchie_glorie(mondo, cartella_di_prova):
    club = Polisportiva("Club Di Prova", None, INIZIO)
    mondo.polisportive[club.nome] = club
    morto, ritirato = mondo.giocatori[3], mondo.giocatori[4]
    club.aggiungi_tesserato(3, morto.indice_collettivo_valore)
    morto.appartenenza = club.nome
    morto.etamorte = morto.eta + 1
    ritirato.etaritiro = ritirato.eta + 1
    rapporto = mondo.processa_tempo_trascorso(ANCORA + 8 * ORA)
    domani = INIZIO + GIORNO
    assert rapporto["morti"] == 1 and rapporto["ritirati"] == 1
    assert 3 in mondo._ids_morti_processati_sessione
    assert morto.diario[0] == {"data": domani, "testo": f"Muore, a {int(morto.eta_anni)} anni."}
    assert club.diario[0] == {"data": domani, "testo": f"{morto.nome} {morto.cognome} muore."}
    assert ritirato.ritirato
    assert ritirato.diario[0] == {"data": domani, "testo": f"Si ritira dall'attività, a {int(ritirato.eta_anni)} anni."}
    gloria = mondo.vecchie_glorie[0]
    assert (gloria["id"], gloria["motivo"], gloria["club"]) == (3, "morte", "Club Di Prova")
    assert datetime.datetime.fromisoformat(gloria["data"]) == domani
    registro = (cartella_di_prova / NOME_FILE_LOG_USCITE).read_text(encoding="utf-8")
    assert registro.count("\n") == 1
    assert registro.startswith(f"21 marzo 2026: {morto.nome} {morto.cognome}, ID 3, muore a {int(morto.eta_anni)} anni, da ")
    testo = testi.vecchie_glorie(mondo)
    assert testo.startswith("Le vecchie glorie: 1 giocatore uscito di scena, dal più recente.")
    assert f"{morto.nome} {morto.cognome}, ID 3, è mort" in testo
    assert "con Club Di Prova" in testo


def test_l_uscita_prematura(mondo, monkeypatch):
    monkeypatch.setattr(modulo_mondo, "PROB_USCITA_PREMATURA_GIORNALIERA", 100)
    rapporto = mondo.processa_tempo_trascorso(ANCORA + 8 * ORA)
    assert rapporto["usciti"] == 30
    assert len(mondo.vecchie_glorie) == 30
    assert {voce["motivo"] for voce in mondo.vecchie_glorie} == {"uscita"}
    g = mondo.giocatori[1]
    assert g.diario[0]["testo"] == f"Lascia il mondo dello showdown, a {int(g.eta_anni)} anni."
    assert "ha lasciato il mondo dello showdown" in testi.vecchie_glorie(mondo)


def test_le_polisportive_del_computer_scrivono_nei_diari(mondo):
    poli = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    poli.gloria = 10_000
    tesserati, _svincolati, _comprati = mondo._esegui_logica_cpu_polisportive(INIZIO)
    assert tesserati == len(poli.tesserati) > 0
    for gid in poli.tesserati:
        g = mondo.giocatori[gid]
        assert g.diario[0]["data"] == INIZIO
        assert g.diario[0]["testo"].startswith(f"{testi.accorda(g, 'Tesserato')} con {poli.nome}, con un ingaggio di ")
    nomi = {f"Tesserato {mondo.giocatori[gid].nome} {mondo.giocatori[gid].cognome}" for gid in poli.tesserati}
    assert {voce["testo"].split(",")[0] for voce in poli.diario[:tesserati]} == nomi


def test_la_partita_finisce_nei_diari(mondo):
    for g in mondo.giocatori.values():
        g.infortunato = False
    risultato = MotorePartita(mondo).gioca_partita(1, 2, 3)
    vincitore, perdente = mondo.giocatori[risultato["vincitore_id"]], mondo.giocatori[risultato["perdente_id"]]
    vinta = next(voce for voce in vincitore.diario if "amichevole" in voce.get("testo", ""))
    persa = next(voce for voce in perdente.diario if "amichevole" in voce.get("testo", ""))
    assert vinta["data"] == persa["data"] == INIZIO
    assert vinta["testo"].startswith(f"Vince l'amichevole contro {perdente.nome} {perdente.cognome}, 2 set a ")
    assert persa["testo"].startswith(f"Perde l'amichevole contro {vincitore.nome} {vincitore.cognome}, ")


def test_sfoltire_i_diari(mondo):
    g = mondo.giocatori[1]
    p = Polisportiva("Club Di Prova", None, INIZIO - 50 * GIORNO)
    mondo.polisportive[p.nome] = p
    g.diario.clear()
    for giorni in (20, 10, 5):
        g.annota(INIZIO - giorni * GIORNO, f"{giorni} giorni fa.")
    assert mondo.sfoltisci_diari() == 0
    mondo.conservazione_diari = {"giocatori": 10, "polisportive": 30}
    assert mondo.sfoltisci_diari() == 2
    assert [voce["testo"] for voce in g.diario] == ["5 giorni fa.", "10 giorni fa."]
    assert p.diario == []
    assert all(len(altro.diario) == 1 for altro in mondo.giocatori.values() if altro is not g)


# I testi.

def test_i_testi_dei_diari_e_della_conservazione(mondo):
    g = mondo.giocatori[1]
    righe = testi.diario_giocatore(g).splitlines()
    assert righe == [f"Diario di {g.nome} {g.cognome}, ID 1: 1 voce, dalla più recente.",
                     f"20 marzo 2026: Entra nel mondo dello showdown, a {int(g.eta_anni)} anni: comincia a giocare, e la sua esperienza parte da zero."]
    g.diario.clear()
    assert testi.diario_giocatore(g) == f"Diario di {g.nome} {g.cognome}, ID 1: nessuna voce."
    assert testi.conservazione(mondo) == "Le voci dei diari dei giocatori si conservano per sempre, quelle delle polisportive per sempre."
    mondo.conservazione_diari = {"giocatori": 1, "polisportive": 90}
    assert testi.conservazione(mondo) == "Le voci dei diari dei giocatori si conservano per 1 giorno simulato, quelle delle polisportive per 90 giorni simulati."
    assert testi.vecchie_glorie(mondo) == "Le vecchie glorie: ancora nessuno è uscito di scena."


def test_il_riepilogo_della_sessione(mondo):
    primo = mondo.processa_tempo_trascorso(ANCORA + 8 * ORA)
    secondo = mondo.processa_tempo_trascorso(ANCORA + 16 * ORA)
    somma = testi.somma_rapporti(primo, secondo)
    assert somma["giorni"] == 2
    assert somma["nuovi"] == primo["nuovi"] + secondo["nuovi"]
    assert somma["ora"] == secondo["ora"]
    testo = testi.chiusura(datetime.timedelta(minutes=5), 3, [], somma)
    assert "Nella sessione il mondo è andato avanti di 2 giorni simulati." in testo
    assert "\n\n" not in testo
