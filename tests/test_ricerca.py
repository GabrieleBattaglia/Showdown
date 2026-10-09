"""Test della ricerca dei giocatori: ambiti, condizioni e il minore stretto del problema P11."""

import datetime
import random

import pytest

import classe
import mercato
import ricerca
from costanti import INDOLI
from modelli import Polisportiva
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
    assert len(ricerca.CRITERI) == 45
    with pytest.raises(ValueError):
        ricerca.cerca(mondo, "tutti", "valore", "contiene", 3)


def test_sesso_e_tratti(mondo):
    donne = ricerca.cerca(mondo, "tutti", "sesso", "f")
    assert donne == [gid for gid, g in mondo.giocatori.items() if g.sesso == "f"]
    mancini = ricerca.cerca(mondo, "tutti", "mancino", "si")
    assert mancini == [gid for gid, g in mondo.giocatori.items() if g.mancino]
    economici = ricerca.cerca(mondo, "tutti", "gloria_richiesta", "minore", 100)
    assert all(mondo.giocatori[gid].gloria_richiesta < 100 for gid in economici)


def test_filtri_insieme(mondo):
    filtri = [("sesso", "f", None), ("eta", "minore", 40)]
    trovati = ricerca.cerca_con_filtri(mondo, "liberi", filtri)
    assert trovati == [gid for gid in ricerca.ids_ambito(mondo, "liberi") if mondo.giocatori[gid].sesso == "f" and mondo.giocatori[gid].eta_anni < 40]
    assert ricerca.cerca_con_filtri(mondo, "liberi", []) == ricerca.ids_ambito(mondo, "liberi")


def test_i_candidati_del_mercato(mondo):
    poli = Polisportiva("Club di prova", None, ORA)
    filtri = [("sesso", "m", None)]
    righe = mercato.candidati(mondo, poli, filtri, "liberi", 0, "costo")
    assert {c.giocatore.id for c in righe} == set(ricerca.cerca_con_filtri(mondo, "liberi", filtri))
    costi = [c.costo for c in righe]
    assert costi == sorted(costi)
    assert all(c.tipo == mercato.LIBERO for c in righe)
    eta = [c.giocatore.eta for c in mercato.candidati(mondo, poli, (), "liberi", 0, "eta")]
    assert eta == sorted(eta)
    valori = [c.giocatore.indice_collettivo_valore for c in mercato.candidati(mondo, poli)]
    assert valori == sorted(valori, reverse=True)
    assert all(c.costo <= 500 for c in mercato.candidati(mondo, poli, (), "liberi", 500))



def test_la_classe_si_scrive_come_nella_scheda():
    assert ricerca.leggi_classe("G4") == ricerca.leggi_classe(" g4 ") == ricerca.leggi_classe("64") == 64
    assert ricerca.leggi_classe("A1") == 1 and ricerca.leggi_classe("K0") == 100 and ricerca.leggi_classe("B0") == 10
    for sbagliata in ("A0", "K1", "0", "101", "Z3", "G", "G44", "", "4,5"):
        with pytest.raises(ValueError):
            ricerca.leggi_classe(sbagliata)
    assert ricerca.codice_classe(64) == "G4" and ricerca.nome_criterio("classe") == "Classe"
    assert ricerca.nome_condizione("classe", "migliore") == "migliore di" and ricerca.nome_condizione("classe", "peggiore") == "peggiore di"


def test_i_criteri_della_tappa_11(mondo):
    mondo.datetime_corrente_simulazione = ORA
    mia = mondo.fonda_polisportiva("Club della ricerca")
    mondo._entra(mia, mondo.giocatori[1])
    g = mondo.giocatori[1]
    g.punti_allenamento = 42.0
    assert ricerca.cerca(mondo, "tutti", "punti_allenamento", "maggiore", 41) == [1]
    con_contratto = ricerca.cerca(mondo, "tutti", "mesi_contratto", "maggiore", 3)
    assert con_contratto == [1]
    assert ricerca.cerca(mondo, "tutti", "mesi_contratto", "minore", 0.5) == [gid for gid in mondo.giocatori if gid != 1]
    # La classe si cerca migliore o peggiore di un codice: la scala scende, migliore vuol dire un livello più piccolo.
    livelli = {gid: classe.classe(x).livello for gid, x in mondo.giocatori.items()}
    soglia = sorted(livelli.values())[len(livelli) // 2]
    migliori = ricerca.cerca(mondo, "tutti", "classe", "migliore", soglia)
    assert migliori == sorted(gid for gid, n in livelli.items() if n < soglia) and migliori
    assert ricerca.cerca(mondo, "tutti", "classe", "migliore", classe.codice(soglia)) == migliori
    assert ricerca.cerca(mondo, "tutti", "classe", "peggiore", soglia) == sorted(gid for gid, n in livelli.items() if n > soglia)
    assert 1 in ricerca.cerca(mondo, "tutti", "indole", "contiene", INDOLI[g.indole]["nome"].upper())
    talenti = ricerca.cerca(mondo, "tutti", "talento", "si")
    assert talenti == [gid for gid, x in mondo.giocatori.items() if x.talento]
    precoci = ricerca.cerca(mondo, "tutti", "precoce", "si")
    assert precoci == [gid for gid, x in mondo.giocatori.items() if x.maturazione == "precoce"]
    ambiziosi = ricerca.cerca(mondo, "tutti", "ambizione", "maggiore", 60)
    assert ambiziosi == [gid for gid, x in mondo.giocatori.items() if x.ambizione > 60]
    assert ricerca.cerca(mondo, "tutti", "esperienza", "maggiore", -1) == sorted(mondo.giocatori)
