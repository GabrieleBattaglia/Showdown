"""
Test della ricerca dei giocatori: le condizioni e il minore stretto del problema P11.
Dal 24 ottobre 2026, coi collegamenti della finestra Mercato e ricerca, la ricerca che stampava nella vista e i suoi
ambiti non ci sono più: le condizioni si provano con ricerca.prova, che la finestra usa per le condizioni e i tratti,
su tutti i giocatori del mondo. Chi cercare lo provano le prove del motore della finestra, tests/test_mercato_e_ricerca.py.
"""

import datetime
import random

import pytest

import classe
import ricerca
from costanti import INDOLI
from mondo import Mondo

ORA = datetime.datetime(2026, 10, 6, 18, 0)


@pytest.fixture
def mondo():
    random.seed(5)
    m = Mondo()
    m.crea_giocatori_casuali(30, ORA)
    return m


def _trova(mondo, criterio, condizione, valore=None, attivi=False):
    """I numeri dei giocatori che soddisfano la condizione, in ordine di numero; con attivi, soltanto quelli in attività."""
    oggi = getattr(mondo, "datetime_corrente_simulazione", None)
    prova = ricerca.prova(criterio, condizione, valore, oggi)
    return [gid for gid, g in sorted(mondo.giocatori.items()) if (not attivi or not g.ritirato) and prova(g)]


def test_numeri_con_virgola_o_punto():
    assert ricerca.leggi_numero("12,5") == 12.5
    assert ricerca.leggi_numero(" 150 ") == 150.0
    with pytest.raises(ValueError):
        ricerca.leggi_numero("tanto")


def test_minore_e_maggiore_stretti(mondo):
    soglia = mondo.giocatori[1].indice_collettivo_valore
    minori = _trova(mondo, "valore", "minore", soglia)
    maggiori = _trova(mondo, "valore", "maggiore", soglia)
    assert 1 not in minori and 1 not in maggiori
    assert sorted(minori + maggiori + [1]) == sorted(mondo.giocatori)


def test_testo_senza_badare_alle_maiuscole(mondo):
    cognome = mondo.giocatori[3].cognome
    assert 3 in _trova(mondo, "cognome", "contiene", cognome.upper())


def test_si_e_no(mondo):
    si = _trova(mondo, "ipovedente", "si")
    no = _trova(mondo, "ipovedente", "no")
    assert sorted(si + no) == sorted(mondo.giocatori)
    assert all(mondo.giocatori[g].ipovedente for g in si)


def test_caratteristiche_di_gioco(mondo):
    mondo.giocatori[2].ritirato = True
    trovati = _trova(mondo, "bomba_base", "maggiore", 5, attivi=True)
    assert 2 not in trovati and all(mondo.giocatori[g]._get_valore_totale("bomba_base") > 5 for g in trovati)
    assert len(ricerca.CRITERI) == 45
    with pytest.raises(ValueError):
        ricerca.prova("valore", "contiene", 3)


def test_sesso_e_tratti(mondo):
    donne = _trova(mondo, "sesso", "f")
    assert donne == [gid for gid, g in mondo.giocatori.items() if g.sesso == "f"]
    mancini = _trova(mondo, "mancino", "si")
    assert mancini == [gid for gid, g in mondo.giocatori.items() if g.mancino]
    economici = _trova(mondo, "gloria_richiesta", "minore", 100)
    assert all(mondo.giocatori[gid].gloria_richiesta < 100 for gid in economici)
    # Le prove di più condizioni si sommano, come le condizioni della finestra.
    prove = [ricerca.prova("sesso", "f", None), ricerca.prova("eta", "minore", 40)]
    insieme = [gid for gid, g in mondo.giocatori.items() if all(p(g) for p in prove)]
    assert insieme == [gid for gid in donne if mondo.giocatori[gid].eta_anni < 40]


def test_la_classe_si_scrive_come_nella_scheda():
    assert ricerca.leggi_classe("G4") == ricerca.leggi_classe(" g4 ") == ricerca.leggi_classe("64") == 64
    assert ricerca.leggi_classe("A1") == 1 and ricerca.leggi_classe("K0") == 100 and ricerca.leggi_classe("B0") == 10
    for sbagliata in ("A0", "K1", "0", "101", "Z3", "G", "G44", "", "4,5"):
        with pytest.raises(ValueError):
            ricerca.leggi_classe(sbagliata)
    assert ricerca.nome_criterio("classe") == "Classe"
    assert ricerca.nome_condizione("classe", "migliore") == "migliore di" and ricerca.nome_condizione("classe", "peggiore") == "peggiore di"


def test_i_criteri_della_tappa_11(mondo):
    mondo.datetime_corrente_simulazione = ORA
    mia = mondo.fonda_polisportiva("Club della ricerca")
    mondo._entra(mia, mondo.giocatori[1])
    g = mondo.giocatori[1]
    g.punti_allenamento = 42.0
    assert _trova(mondo, "punti_allenamento", "maggiore", 41) == [1]
    con_contratto = _trova(mondo, "mesi_contratto", "maggiore", 3)
    assert con_contratto == [1]
    assert _trova(mondo, "mesi_contratto", "minore", 0.5) == [gid for gid in mondo.giocatori if gid != 1]
    # La classe si cerca migliore o peggiore di un codice: la scala scende, migliore vuol dire un livello più piccolo.
    livelli = {gid: classe.classe(x).livello for gid, x in mondo.giocatori.items()}
    soglia = sorted(livelli.values())[len(livelli) // 2]
    migliori = _trova(mondo, "classe", "migliore", soglia)
    assert migliori == sorted(gid for gid, n in livelli.items() if n < soglia) and migliori
    assert _trova(mondo, "classe", "migliore", classe.codice(soglia)) == migliori
    assert _trova(mondo, "classe", "peggiore", soglia) == sorted(gid for gid, n in livelli.items() if n > soglia)
    assert 1 in _trova(mondo, "indole", "contiene", INDOLI[g.indole]["nome"].upper())
    talenti = _trova(mondo, "talento", "si")
    assert talenti == [gid for gid, x in mondo.giocatori.items() if x.talento]
    precoci = _trova(mondo, "precoce", "si")
    assert precoci == [gid for gid, x in mondo.giocatori.items() if x.maturazione == "precoce"]
    ambiziosi = _trova(mondo, "ambizione", "maggiore", 60)
    assert ambiziosi == [gid for gid, x in mondo.giocatori.items() if x.ambizione > 60]
    assert _trova(mondo, "esperienza", "maggiore", -1) == sorted(mondo.giocatori)
