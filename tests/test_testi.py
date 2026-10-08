"""Test dei testi della finestra: numeri e date all'italiana, schede, elenchi, barra di stato, apertura e regole di accessibilità."""

import datetime
import random
import re

import pytest

import mercato
import testi
from archivio import CARICATO, NATO
from modelli import Polisportiva
from mondo import Mondo

ORA = datetime.datetime(2026, 10, 6, 18, 0)
# Lo stesso istante nel mondo reale, in UTC come lo conta il mondo.
ADESSO = datetime.datetime(2026, 10, 6, 16, 0, tzinfo=datetime.UTC)


@pytest.fixture
def mondo():
    random.seed(77)
    m = Mondo()
    m.datetime_corrente_simulazione = ORA
    m.datetime_ultimo_run_reale = ADESSO - datetime.timedelta(hours=3)
    m.crea_giocatori_casuali(40, ORA)
    mia = Polisportiva("Club Di Prova", "segreta", ORA - datetime.timedelta(days=150))
    m.polisportive[mia.nome] = mia
    for gid in (2, 5, 9):
        mia.aggiungi_tesserato(gid, m.giocatori[gid].indice_collettivo_valore)
        m.giocatori[gid].appartenenza = mia.nome
    m.miapolisportiva_attiva = mia
    m.crea_polisportiva_cpu(ORA)
    return m


def _accessibile(testo):
    """Nessuna riga vuota e nessun separatore grafico fatto di trattini, uguali o trattini bassi ripetuti."""
    assert testo
    assert "\n\n" not in testo
    for riga in testo.splitlines():
        assert riga.strip(), "riga vuota"
        assert not re.search(r"(-{3,}|={3,}|_{3,})", riga), riga


def test_numeri_e_date_all_italiana():
    assert testi.numero(2034.5) == "2.034,5"
    assert testi.numero(0.55, 2) == "0,55"
    assert testi.intero(12345) == "12.345"
    assert testi.data_lunga(datetime.datetime(2026, 10, 7, 18, 39)) == "7 ottobre 2026 alle 18:39"
    assert testi.durata(datetime.timedelta(days=1, hours=3, minutes=5)) == "1 giorno, 3 ore e 5 minuti"
    assert testi.durata(datetime.timedelta(hours=2)) == "2 ore"
    assert testi.durata(datetime.timedelta(seconds=30)) == "meno di un minuto"
    assert testi.unisci(["a", "", "b", "c"]) == "a, b e c"


def test_scala_degli_aggettivi():
    assert testi.aggettivo(0, 40) == "Inesistente"
    assert testi.aggettivo(14.6, 40) == "Buono"
    assert testi.aggettivo(40, 40) == "Divino"
    assert testi.aggettivo(2.9, 10) == "Insufficiente"
    assert testi.aggettivo(10, 10) == "Divino"
    assert len(testi.AGGETTIVI) == 21


def test_scheda_del_giocatore(mondo):
    g = mondo.giocatori[2]
    scheda = testi.scheda_giocatore(g, mondo)
    _accessibile(scheda)
    righe = scheda.splitlines()
    assert righe[0].startswith("[Club Di Prova] ID: 2 | ")
    for etichetta in ("[CARATTERISTICHE FISICHE]", "[DIFESA]", "[ATTACCO]", "[POLIVALENTI]", "[CARRIERA]"):
        assert etichetta in righe
    assert any(r.startswith("Classifica generale: ") and r.endswith(" su 40") for r in righe)
    assert any(r.startswith("Età: ") for r in righe)
    caratteristiche = [r for r in righe if re.match(r"^[A-Z][a-zà]+( [a-zà]+)*: [A-Z][a-z]+ \(\d+,\d\)", r)]
    assert len(caratteristiche) == 13
    libero = next(x for x in mondo.giocatori.values() if x.appartenenza == "*")
    assert testi.scheda_giocatore(libero, mondo).startswith("[LIBER")


def test_elenchi_e_classifiche(mondo):
    for testo in (testi.elenco_giocatori(mondo), testi.classifica(mondo), testi.top_10(mondo), testi.statistiche(mondo),
                  testi.elenco_polisportive(mondo), testi.tesserati_attiva(mondo), testi.scheda_polisportiva(mondo.miapolisportiva_attiva, mondo)):
        _accessibile(testo)
    assert len(testi.elenco_giocatori(mondo).splitlines()) == 41
    assert len(testi.classifica(mondo).splitlines()) == 41
    assert testi.classifica(mondo).splitlines()[1].startswith("1. ")
    assert "[TESSERATI]" in testi.scheda_polisportiva(mondo.miapolisportiva_attiva, mondo)


def test_liste_della_sessione(mondo):
    assert testi.lista_ritirati(mondo) == "In questa sessione non si è ritirato nessuno."
    mondo.giocatori_ritirati_sessione.append((4, "RITIRO: ..."))
    mondo.giocatori_morti_sessione.append((6, "DECESSO (Età): ..."))
    mondo.giocatori_morti_sessione.append((7, "USCITA PREMATURA: ..."))
    mondo._ids_morti_processati_sessione.update({6, 7})
    for testo in (testi.lista_nuovi(mondo), testi.lista_ritirati(mondo), testi.lista_usciti(mondo)):
        _accessibile(testo)
    usciti = testi.lista_usciti(mondo)
    assert "ha lasciato il mondo dello showdown" in usciti
    assert " è mort" in usciti


def test_barra_di_stato(mondo):
    righe = testi.righe_barra(mondo, "mondo salvato alle 18:41", ADESSO)
    assert len(righe) == 4
    assert all(len(r) <= 40 for r in righe)
    assert righe[0] == "s06/10/2026 18:00 a5h00m"
    assert righe[1] == "Club Di Prova g100 t3/15 m5 c20"
    assert re.fullmatch(r"l\d+ t3 f\d+ n40 p2", righe[2])
    mondo.miapolisportiva_attiva.nome = "Un nome di polisportiva lunghissimo, ben oltre i quaranta caratteri"
    assert len(testi.righe_barra(mondo, "x" * 60, ADESSO)[1]) == 40
    mondo.miapolisportiva_attiva = None
    assert testi.righe_barra(mondo, None, ADESSO)[1] == "nessuna polisportiva attiva"


def test_apertura_e_avanzamento(mondo):
    rapporto = Mondo.rapporto_vuoto(ORA) | {"ticks": 3, "giorni": 3, "nuovi": 7, "ritirati": 1, "tesserati_cpu": 4, "svincolati_cpu": 2, "poli_create": 1}
    testo = testi.apertura(mondo, CARICATO, ["Mondo caricato: prova."], rapporto, ADESSO - datetime.timedelta(days=1), ADESSO)
    _accessibile(testo)
    assert "Bentornato!" in testo and "1 giorno fa" in testo
    assert "7 giocatori sono nati e 1 si è ritirato." in testo
    assert "Le polisportive del computer hanno tesserato 4 giocatori e ne hanno svincolati 2 per fare posto." in testo
    assert "È nata una polisportiva del computer." in testo
    assert "Bentornato" not in testi.apertura(mondo, NATO, [], Mondo.rapporto_vuoto(ORA), ADESSO, ADESSO)
    assert testi.riepilogo_avanzamento(Mondo.rapporto_vuoto(ORA)) == "In questa sessione il mondo non è ancora avanzato."
    avanzamento = testi.data_e_avanzamento(mondo, ADESSO)
    _accessibile(avanzamento)
    assert "fra 5 ore" in avanzamento
    assert "maturato in questo momento" in testi.data_e_avanzamento(mondo, ADESSO + datetime.timedelta(hours=6))


def test_guida_novita_e_informazioni():
    guida = testi.guida([("File", [("Salva il mondo", "Ctrl+S"), ("Esci", "Ctrl+Q")])])
    _accessibile(guida)
    assert "Menu File: Salva il mondo, Ctrl+S; Esci, Ctrl+Q." in guida
    assert testi.LEGENDA_BARRA in guida
    # I tasti della partita dal vivo non stanno in un menu: la guida li dice in una riga sua.
    assert testi.GUIDA_DELLA_PARTITA_DAL_VIVO in guida.splitlines()
    assert all(tasto in testi.GUIDA_DELLA_PARTITA_DAL_VIVO for tasto in ("Prosegui", "Alt+F", "Alt+L", "Alt+V", "Esc", "più e meno", "F1"))
    novita = testi.novita("# Changelog\n\n## [1.3.0] - 2026-10-06\n\n### Un mondo nuovo\n\nIl file `mess_mondo.json` si firma.\n")
    assert novita.splitlines() == ["Changelog.", "Versione 1.3.0 del 2026-10-06.", "Un mondo nuovo.", "Il file mess_mondo.json si firma."]
    _accessibile(testi.informazioni())


def test_testi_del_mercato_e_delle_polisportive(mondo):
    p = mondo.miapolisportiva_attiva
    cpu = next(q for q in mondo.polisportive.values() if q.is_cpu_controlled)
    g = mondo.giocatori[1]
    libero = mercato.Candidato(g, mercato.LIBERO, 450, 210)
    riga = testi.riga_mercato(libero)
    assert riga.startswith(f"{g.nome} {g.cognome}, ") and ", stipendio 210 euro, chiede 450 euro d'ingaggio" in riga and riga.endswith(", ID 1")
    in_vendita = mercato.Candidato(mondo.giocatori[3], mercato.IN_VENDITA, 1200, 300, cpu)
    assert f", in vendita da {cpu.nome} a 1.200 euro" in testi.riga_mercato(in_vendita)
    assert testi.domanda_ingaggio(libero, 450, 50.0, p, mondo).endswith("Accetta al 50%, e poi prende 210 euro al mese. Userai una delle 5 mosse che ti restano oggi.")
    p.movimenti_oggi = 4
    assert testi.domanda_acquisto(in_vendita, p, mondo).endswith("Userai l'ultima mossa che ti resta oggi.")
    assert testi.esito_ingaggio(g, p, False, 450, 12.0) == f"{g.nome} {g.cognome} ha rifiutato l'ingaggio di 450 euro: accettava al 12%."
    riepilogo = testi.riepilogo_mercato(p, mondo, [("Primo esito.", False), ("Secondo esito.", True)])
    _accessibile(riepilogo)
    assert riepilogo.startswith("Mercato di Club Di Prova: 2 offerte, 1 riuscita.\nPrimo esito.\nSecondo esito.")
    assert riepilogo.endswith("Club Di Prova: cassa 20.000 euro, gloria 100, tesserati 3 su 15, mosse rimaste 1 su 5.")
    assert testi.riepilogo_mercato(p, mondo, []).startswith("Mercato di Club Di Prova: nessuna offerta.")
    assert testi.domanda_chiusura(p) == "Chiudere per sempre Club Di Prova? I suoi 3 tesserati torneranno liberi, e non si torna indietro."
    assert testi.chiusa("Club Di Prova", 1).startswith("Club Di Prova ha chiuso per sempre: 1 giocatore torna libero.")
    assert testi.chiusa("Club Di Prova", 0).startswith("Club Di Prova ha chiuso per sempre, senza tesserati.")
    assert testi.password_cambiata(p) == "Club Di Prova ora è protetta da password."
    _accessibile(testi.fondata(p, mondo))
