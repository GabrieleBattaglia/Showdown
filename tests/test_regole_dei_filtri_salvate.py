"""
Le prove dei preset di regole e del formato 10 nella forma del costruttore di regole, D36 della sera del 24 ottobre
2026: i preset di serie e lo stato di ogni porta che fanno il giro del salvataggio, la costante storica di archivio.py,
la scrittura severa, la lettura che ripara un pezzo alla volta e riconosce i filtri a schede di prima, il mondo che non
ricorda quello che non si rileggerebbe; e le parole delle regole in testi.py, le righe dell'elenco, il valore, il
perché di una regola in preparazione che non conta, l'etichetta dei trovati, l'annuncio e il campo Trovati.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nascono il 24 ottobre 2026 sera col passo 1 del costruttore di regole. Lo stesso giorno, col cambio della finestra, i
nomi perdono il loro _a_regole, e il mondo salvato dalla finestra a schede si scrive dalle costanti storiche di archivio.py.
"""

import copy
import dataclasses
import json
import random
import re

import pytest
from aiuti_mercato import mondo_del_mercato

import archivio
import mercato
import registro
import regole
import staff
import testi

G = mercato.GIOCATORI
A = mercato.ALLENATORI


@pytest.fixture
def mondo():
    return mondo_del_mercato()


@pytest.fixture
def scritti(monkeypatch):
    righe = []
    monkeypatch.setattr(registro, "scrivi", righe.append)
    return righe


def _regola(bersaglio, chiave, operatore, valore, collegamento=mercato.E):
    return mercato.Regola(collegamento, bersaglio, chiave, operatore, valore)


def _accessibile(testo):
    assert testo and "\n\n" not in testo
    for riga in testo.splitlines():
        assert riga.strip(), "riga vuota"
        assert not re.search(r"(-{3,}|={3,}|_{3,})", riga), riga


def _con_i_preset(m):
    """Il mondo con due preset di regole, il 2 e il 3 dopo che l'1 è stato eliminato, e ogni porta con la sua preparazione."""
    fdr = mercato.filtri_di_ricerca_del_mondo(m)
    mercato.salva_preset(fdr, "Da togliere", mercato.Filtri((_regola(G, "stato", "uguale", mercato.LIBERO),)))
    mercato.salva_preset(fdr, "Giovani mancine", mercato.Filtri((_regola(G, "sesso", "uguale", "f"), _regola(G, "mancino", "uguale", True),
                                                                                 _regola(G, "eta", "minore_uguale", 20)), "valore_alto"))
    mercato.salva_preset(fdr, "Capi o vedenti", mercato.Filtri((_regola(A, "stato", "uguale", mercato.CAPO),
                                                                                _regola(A, "visus", "uguale", staff.VEDENTE, mercato.O)), "eta_anziano"))
    mercato.elimina_preset(fdr, 1)
    mercato.ricorda_i_preset(m, fdr)
    costo = mercato.Filtri((_regola(G, "stato", "uguale", mercato.SUL_MERCATO), _regola(G, "costo", "minore_uguale", 5000),
                                   _regola(G, "stato", "uguale", mercato.SUL_MERCATO, mercato.O), _regola(G, "costo", "manca", None)), "costo_basso")
    mercato.ricorda_la_porta(m, "mercato", mercato.StatoDellaPorta(2, costo, mercato.Preparazione(mercato.E, G, "nome", "contiene", "ros")))
    mercato.ricorda_la_porta(m, "allenatori", mercato.StatoDellaPorta(3, mercato.Filtri((_regola(A, "stato", "uguale", mercato.TUO),), "classe"),
                                                                                 mercato.Preparazione(mercato.O, A, "visus", "uguale", None)))
    a_mano = mercato.Filtri((_regola(G, "stato", "uguale", mercato.IN_ATTIVITA), _regola(G, "valore", "maggiore", 150.5),
                                    _regola(G, "classe", "migliore_uguale", 50), _regola(G, "indole", "uguale", m.giocatori[3].indole),
                                    _regola(G, "regione", "uguale", "Lombardia"), _regola(G, "nome", "contiene", "Forlì")), "numero")
    mercato.ricorda_la_porta(m, "ricerca", mercato.StatoDellaPorta(None, a_mano, mercato.Preparazione(mercato.E, G, "eta", "minore", "2.5")))
    mercato.ricorda_la_porta(m, "amichevole", mercato.StatoDellaPorta("piu_forti", mercato.Filtri((_regola(G, "disponibile", "uguale", True),), "classe"),
                                                                                 mercato.Preparazione(mercato.E, G, "mancino", "uguale", True)))
    return m


# I preset e le porte nel salvataggio.

def test_ogni_preset_di_serie_va_e_torna_dal_dizionario():
    for chiave, _nome in mercato.PRESET_DI_SERIE:
        filtri = mercato.filtri_di_serie(chiave)
        assert mercato.filtri_da_dizionario(json.loads(json.dumps(mercato.filtri_a_dizionario(filtri)))) == filtri
    serie = mercato.filtri_di_ricerca_di_serie()
    assert mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(mercato.filtri_di_ricerca_a_dizionario(serie)))) == (serie, [])


def test_la_costante_storica_del_formato_10_nella_forma_delle_regole():
    """La migrazione dal 9, col cambio della finestra, darà esattamente lo stato di serie delle porte; ogni volta un documento nuovo."""
    serie = mercato.filtri_di_ricerca_di_serie()
    assert archivio.filtri_di_ricerca_del_formato_10() == mercato.filtri_di_ricerca_a_dizionario(serie)
    assert mercato.filtri_di_ricerca_da_dizionario(archivio.filtri_di_ricerca_del_formato_10()) == (serie, [])
    primo = archivio.filtri_di_ricerca_del_formato_10()
    primo["porte"]["mercato"]["attuali"]["regole"].append({"numero": 1})
    primo["porte"]["mercato"]["preparazione"]["valore"] = "x"
    secondo = archivio.filtri_di_ricerca_del_formato_10()
    assert len(secondo["porte"]["mercato"]["attuali"]["regole"]) == 1 and secondo["porte"]["mercato"]["preparazione"]["valore"] == ""
    assert set(archivio.PORTE_DEL_FORMATO_10) == set(mercato.PORTE)


def test_preset_e_porte_fanno_il_giro_del_salvataggio(mondo, scritti):
    _con_i_preset(mondo)
    blocco = mercato.filtri_di_ricerca_da_salvare(mondo)
    assert [(p["numero"], p["nome"]) for p in blocco["preset"]] == [(2, "Giovani mancine"), (3, "Capi o vedenti")] and blocco["prossimo_preset"] == 4
    assert blocco["preset"][0]["filtri"] == {"regole": [
        {"collegamento": "e", "bersaglio": "giocatori", "caratteristica": "sesso", "operatore": "uguale", "valore": "f"},
        {"collegamento": "e", "bersaglio": "giocatori", "caratteristica": "mancino", "operatore": "uguale", "valore": True},
        {"collegamento": "e", "bersaglio": "giocatori", "caratteristica": "eta", "operatore": "minore_uguale", "valore": 20}], "ordine": "valore_alto"}
    assert {porta: stato["scelta"] for porta, stato in blocco["porte"].items()} == {"mercato": 2, "allenatori": 3, "ricerca": None, "amichevole": "piu_forti"}
    assert blocco["porte"]["ricerca"]["preparazione"] == {"collegamento": "e", "bersaglio": "giocatori", "caratteristica": "eta", "operatore": "minore",
                                                          "valore": "2.5"}
    letti, avvisi = mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(blocco)))
    assert letti == mondo.filtri_di_ricerca and avvisi == [] and scritti == []
    assert mercato.stato_della_porta(mondo, "allenatori").preparazione == mercato.Preparazione(mercato.O, A, "visus", "uguale", None)
    assert mercato.filtri_della_voce(letti, 3, None).ordine == "eta_anziano"
    assert mercato.filtri_della_voce(letti, "mercato", None) == mercato.filtri_di_serie("mercato")
    with pytest.raises(KeyError):
        mercato.filtri_della_voce(letti, 1, None)
    with pytest.raises(KeyError):
        mercato.stato_della_porta(mondo, "altrove")


def test_salvare_eliminare_e_ricordare_i_preset_di_regole(mondo):
    _con_i_preset(mondo)
    fdr = mercato.filtri_di_ricerca_del_mondo(mondo)
    nuovi = mercato.Filtri((_regola(G, "stato", "uguale", mercato.RITIRATO),), "eta_anziano")
    preset, sostituito = mercato.salva_preset(fdr, "giovani MANCINE", nuovi)
    assert sostituito and preset.numero == 2 and preset.nome == "Giovani mancine" and preset.filtri == nuovi
    with pytest.raises(ValueError, match="voce di serie"):
        mercato.salva_preset(fdr, "filtri attuali, NON salvati", nuovi)
    with pytest.raises(ValueError, match="la regola 1 non va"):
        mercato.salva_preset(fdr, "Strani", mercato.Filtri((_regola(G, "eta", "minore", 20.5),)))
    # Eliminando il preset che riapre, la porta torna al suo preset di serie e tiene filtri attuali e preparazione.
    prima = fdr.porte["allenatori"]
    mercato.elimina_preset(fdr, 3)
    dopo = fdr.porte["allenatori"]
    assert dopo.scelta == "allenatori_liberi" and dopo.attuali == prima.attuali and dopo.preparazione == prima.preparazione
    mercato.ricorda_i_preset(mondo, fdr)
    assert [p.numero for p in mondo.filtri_di_ricerca.preset] == [2] and mondo.filtri_di_ricerca.porte["allenatori"].scelta == "allenatori_liberi"
    assert mondo.filtri_di_ricerca.prossimo_preset == 4


SBAGLI_DEL_MONDO = {
    "una regola con troppi decimali": (mercato.Filtri((_regola(G, "eta", "minore", 20.5),)), mercato.Preparazione()),
    "la prima regola con la o": (mercato.Filtri((_regola(G, "eta", "minore", 20, mercato.O),)), mercato.Preparazione()),
    "cinquantuno regole": (mercato.Filtri(tuple(_regola(G, "eta", "minore", n) for n in range(51))), mercato.Preparazione()),
    "un operatore di un altro tipo": (mercato.Filtri((_regola(G, "eta", "contiene", "2"),)), mercato.Preparazione()),
    "una caratteristica dell'altro bersaglio": (mercato.Filtri((_regola(G, "visus", "uguale", staff.VEDENTE),)), mercato.Preparazione()),
    "un valore per non ha il dato": (mercato.Filtri((_regola(G, "costo", "manca", 3),)), mercato.Preparazione()),
    "un ordine che non c'è": (mercato.Filtri((), "a_caso"), mercato.Preparazione()),
    "un testo con gli spazi": (mercato.Filtri((_regola(G, "nome", "contiene", " ros"),)), mercato.Preparazione()),
    "nessuna preparazione": (mercato.Filtri(), None),
    "una preparazione dell'altro bersaglio": (mercato.Filtri(), mercato.Preparazione(mercato.E, A, "valore", "maggiore", "3")),
    "una preparazione con una voce che non c'è": (mercato.Filtri(), mercato.Preparazione(mercato.E, G, "sesso", "uguale", "x")),
    "una preparazione sì o no scritta": (mercato.Filtri(), mercato.Preparazione(mercato.E, G, "mancino", "uguale", "sì")),
}


@pytest.mark.parametrize("sbaglio", list(SBAGLI_DEL_MONDO))
def test_il_mondo_non_ricorda_quello_che_non_si_rileggerebbe(mondo, sbaglio):
    _con_i_preset(mondo)
    prima = mondo.filtri_di_ricerca.copia()
    attuali, preparazione = SBAGLI_DEL_MONDO[sbaglio]
    with pytest.raises(ValueError):
        mercato.ricorda_la_porta(mondo, "ricerca", mercato.StatoDellaPorta(None, attuali, preparazione))
    assert mondo.filtri_di_ricerca == prima
    with pytest.raises(KeyError):
        mercato.ricorda_la_porta(mondo, "altrove", prima.porte["ricerca"])


def test_la_preparazione_si_ripulisce_prima_di_ricordarla(mondo):
    """L'obiezione 22 della critica: un carattere di controllo incollato nel Valore non fa più perdere lo stato della porta."""
    stato = mercato.StatoDellaPorta(None, mercato.Filtri(), mercato.Preparazione(mercato.E, G, "nome", "contiene", "ro\ts\r\n" + "x" * 60))
    mercato.ricorda_la_porta(mondo, "ricerca", stato)
    assert mondo.filtri_di_ricerca.porte["ricerca"].preparazione.valore == "ros" + "x" * 47


# La lettura che ripara: ogni guasto tocca un pezzo, che torna di serie con un avviso nel registro, e il resto resta.

def _cammina(dati, *chiavi):
    for chiave in chiavi:
        dati = dati[chiave]
    return dati


def _metti(valore, *chiavi):
    def guasto(d):
        _cammina(d, *chiavi[:-1])[chiavi[-1]] = copy.deepcopy(valore)
    return guasto


def _togli(*chiavi):
    def guasto(d):
        del _cammina(d, *chiavi[:-1])[chiavi[-1]]
    return guasto


def _attuali_di_serie(porta):
    def atteso(f):
        stato = f.porte[porta]
        stato.attuali = mercato.filtri_di_serie(mercato.PRESET_DELLA_PORTA[porta])
        if stato.scelta is None:
            stato.scelta = mercato.PRESET_DELLA_PORTA[porta]
    return atteso


def _preparazione_di_serie(porta):
    def atteso(f):
        f.porte[porta].preparazione = mercato.preparazione_di_serie(porta)
    return atteso


def _filtri_del_preset_di_serie(posto):
    def atteso(f):
        f.preset[posto].filtri = mercato.filtri_di_serie(mercato.SERIE_DEI_FILTRI_ILLEGGIBILI)
    return atteso


def _porta_di_serie(porta):
    def atteso(f):
        f.porte[porta] = mercato.stato_di_serie(porta)
    return atteso


def _scelta_di_serie(porta):
    def atteso(f):
        f.porte[porta].scelta = mercato.PRESET_DELLA_PORTA[porta]
    return atteso


def _niente(_f):
    pass


REGOLA_0 = ("preset", 0, "filtri", "regole", 0)
MERCATO = ("porte", "mercato", "attuali", "regole")
PREPARAZIONE = ("porte", "ricerca", "preparazione")
GUASTI = {
    "una caratteristica che non c'è": (_metti("volante", *REGOLA_0, "caratteristica"), _filtri_del_preset_di_serie(0), None),
    "una caratteristica dell'altro bersaglio": (_metti("visus", *MERCATO, 0, "caratteristica"), _attuali_di_serie("mercato"), None),
    "un bersaglio che non c'è": (_metti("arbitri", *MERCATO, 1, "bersaglio"), _attuali_di_serie("mercato"), None),
    "un operatore di un altro tipo": (_metti("contiene", *REGOLA_0, "operatore"), _filtri_del_preset_di_serie(0), None),
    "un collegamento che non c'è": (_metti("ma", "preset", 1, "filtri", "regole", 1, "collegamento"), _filtri_del_preset_di_serie(1), None),
    "un'età oltre la misura": (_metti(121, "preset", 0, "filtri", "regole", 2, "valore"), _filtri_del_preset_di_serie(0), None),
    "un decimale di troppo": (_metti(150.25, "porte", "ricerca", "attuali", "regole", 1, "valore"), _attuali_di_serie("ricerca"), None),
    "un valore vero o falso al posto di un numero": (_metti(True, "preset", 0, "filtri", "regole", 2, "valore"), _filtri_del_preset_di_serie(0), None),
    "un testo con gli spazi": (_metti(" Forlì", "porte", "ricerca", "attuali", "regole", 5, "valore"), _attuali_di_serie("ricerca"), None),
    "una voce che non c'è": (_metti("volante", *MERCATO, 0, "valore"), _attuali_di_serie("mercato"), None),
    "una regione che non c'è": (_metti("Atlantide", "porte", "ricerca", "attuali", "regole", 4, "valore"), _attuali_di_serie("ricerca"), None),
    "un valore per non ha il dato": (_metti(3, *MERCATO, 3, "valore"), _attuali_di_serie("mercato"), None),
    "la prima regola con la o": (_metti("o", *REGOLA_0, "collegamento"), _filtri_del_preset_di_serie(0), None),
    "cinquantuno regole": (lambda d: _cammina(d, *MERCATO).extend([_cammina(d, *MERCATO)[1]] * 47), _attuali_di_serie("mercato"), None),
    "un campo in più nella regola": (_metti(1, *REGOLA_0, "peso"), _filtri_del_preset_di_serie(0), None),
    "un campo in meno nella regola": (_togli(*REGOLA_0, "valore"), _filtri_del_preset_di_serie(0), None),
    "le regole in un dizionario": (_metti({}, "porte", "amichevole", "attuali", "regole"), _attuali_di_serie("amichevole"), None),
    "un ordine che non c'è": (_metti("a_caso", "porte", "allenatori", "attuali", "ordine"), _attuali_di_serie("allenatori"), None),
    "i filtri senza l'ordine": (_togli("preset", 1, "filtri", "ordine"), _filtri_del_preset_di_serie(1), None),
    "una preparazione con un a capo": (_metti("a\nb", *PREPARAZIONE, "valore"), _preparazione_di_serie("ricerca"), None),
    "una preparazione troppo lunga": (_metti("x" * 51, *PREPARAZIONE, "valore"), _preparazione_di_serie("ricerca"), None),
    "una preparazione senza un campo": (_togli(*PREPARAZIONE, "operatore"), _preparazione_di_serie("ricerca"), None),
    "una preparazione con la caratteristica dell'altro bersaglio": (_metti("visus", *PREPARAZIONE, "caratteristica"), _preparazione_di_serie("ricerca"), None),
    "una preparazione con un bersaglio che non c'è": (_metti("arbitri", *PREPARAZIONE, "bersaglio"), _preparazione_di_serie("ricerca"), None),
    "una preparazione con un sì scritto": (_metti("sì", "porte", "amichevole", "preparazione", "valore"), _preparazione_di_serie("amichevole"), None),
    "una preparazione in un elenco": (_metti([], *PREPARAZIONE), _preparazione_di_serie("ricerca"), None),
    "la preparazione che manca": (_togli(*PREPARAZIONE), _preparazione_di_serie("ricerca"), "manca"),
    "una porta in meno": (_togli("porte", "amichevole"), _porta_di_serie("amichevole"), None),
    "un preset che non c'è più": (_metti(7, "porte", "mercato", "scelta"), _scelta_di_serie("mercato"), None),
    "un preset di serie che non c'è": (_metti("inventata", "porte", "amichevole", "scelta"), _scelta_di_serie("amichevole"), None),
    "un preset nella forma di prima": (_metti(archivio.FILTRI_VUOTI_DEL_FORMATO_10_A_SCHEDE, "preset", 1, "filtri"), _filtri_del_preset_di_serie(1), mercato.FORMA_DI_PRIMA),
    "filtri attuali nella forma di prima": (_metti({**archivio.FILTRI_VUOTI_DEL_FORMATO_10_A_SCHEDE, "liberi": True}, "porte", "ricerca", "attuali"),
                                            _attuali_di_serie("ricerca"), mercato.FORMA_DI_PRIMA),
}


@pytest.mark.parametrize("guasto", list(GUASTI))
def test_la_lettura_ripara_un_pezzo_alla_volta(mondo, guasto, scritti):
    _con_i_preset(mondo)
    rovina, atteso, nel_testo = GUASTI[guasto]
    dati = mercato.filtri_di_ricerca_da_salvare(mondo)
    rovina(dati)
    letti, avvisi = mercato.filtri_di_ricerca_da_dizionario(dati)
    previsto = mondo.filtri_di_ricerca.copia()
    atteso(previsto)
    assert letti == previsto and avvisi
    righe = [mercato.testo_per_il_registro(avviso) for avviso in avvisi]
    assert all(riga.startswith("Lettura del mondo, filtri di Mercato e ricerca. ") and " Il dato originale, in JSON: " in riga and "\n" not in riga for riga in righe)
    if nel_testo:
        assert any(nel_testo in riga for riga in righe), righe
    # Quello che si è letto si riscrive e si rilegge senza riparazioni.
    assert mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(mercato.filtri_di_ricerca_a_dizionario(letti)))) == (letti, [])


def test_un_mondo_salvato_dalla_finestra_a_schede_si_legge_e_lo_dice(mondo):
    """Il formato 10 di prima del costruttore di regole: i preset restano col loro nome e numero, i filtri tornano di serie, e ogni avviso nomina la forma di prima."""
    # Dal cambio della finestra il motore a schede non c'è più: il mondo salvato da lei si scrive a mano, dalle costanti storiche.
    def a_schede(**campi):
        return {**archivio.FILTRI_VUOTI_DEL_FORMATO_10_A_SCHEDE, "tratti": {}, "condizioni": [], **campi}

    di_prima = archivio.filtri_di_ricerca_del_formato_10_a_schede()
    di_prima["preset"] = [{"numero": 1, "nome": "Donne libere", "filtri": a_schede(liberi=True, sesso="f")}]
    di_prima["prossimo_preset"] = 2
    di_prima["porte"]["mercato"] = {"scelta": 1, "attuali": a_schede(liberi=True)}
    letti, avvisi = mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(di_prima)))
    assert [(p.numero, p.nome) for p in letti.preset] == [(1, "Donne libere")] and letti.prossimo_preset == 2
    assert letti.preset[0].filtri == mercato.filtri_di_serie(mercato.SERIE_DEI_FILTRI_ILLEGGIBILI)
    assert letti.porte["mercato"].scelta == 1 and letti.porte["ricerca"] == mercato.stato_di_serie("ricerca")
    assert all(stato.preparazione == mercato.preparazione_di_serie(porta) for porta, stato in letti.porte.items())
    assert len(avvisi) == 1 + 2 * len(mercato.PORTE)
    assert all("forma di prima del costruttore di regole" in avviso.problema for avviso in avvisi)
    # La costante storica a schede di archivio.py si riconosce allo stesso modo.
    _letti, avvisi = mercato.filtri_di_ricerca_da_dizionario(archivio.filtri_di_ricerca_del_formato_10_a_schede())
    assert len(avvisi) == 2 * len(mercato.PORTE) and _letti == mercato.filtri_di_ricerca_di_serie()


def test_la_lettura_non_solleva_mai_eccezioni_e_quello_che_legge_si_riscrive(mondo):
    _con_i_preset(mondo)
    buono = mercato.filtri_di_ricerca_da_salvare(mondo)
    caso = random.Random(2424)
    valori = (None, 0, -1, 1, 2, 3, 1.5, 150.25, float("nan"), True, False, "", "x", "e", "o", "giocatori", "allenatori", "stato", "uguale", "manca",
              "mercato", [], [1], {}, {"a": 1}, {"regole": [], "ordine": "numero"})

    def nodi(dato, percorso=()):
        yield percorso
        figli = dato.items() if isinstance(dato, dict) else enumerate(dato) if isinstance(dato, list) else ()
        for chiave, figlio in figli:
            yield from nodi(figlio, (*percorso, chiave))

    percorsi = list(nodi(buono))
    for _ in range(500):
        dati = copy.deepcopy(buono)
        for _volta in range(caso.randint(1, 3)):
            percorso = caso.choice(percorsi)
            try:
                if percorso:
                    _cammina(dati, *percorso[:-1])[percorso[-1]] = copy.deepcopy(caso.choice(valori))
                else:
                    dati = copy.deepcopy(caso.choice(valori))
            except (KeyError, IndexError, TypeError):
                continue
        letti, _avvisi = mercato.filtri_di_ricerca_da_dizionario(dati)
        assert mercato.filtri_di_ricerca_da_dizionario(json.loads(json.dumps(mercato.filtri_di_ricerca_a_dizionario(letti)))) == (letti, [])


# Le parole delle regole.

def test_le_righe_dell_elenco_delle_regole():
    regole_dell_elenco = (_regola(G, "stato", "uguale", mercato.SUL_MERCATO), _regola(G, "eta", "minore_uguale", 20),
                          _regola(A, "stato", "uguale", mercato.CAPO, mercato.O), _regola(A, "nome", "contiene", "ros"),
                          _regola(G, "costo", "manca", None), _regola(G, "mancino", "uguale", True, mercato.O), _regola(G, "classe", "migliore_uguale", 50),
                          _regola(G, "valore", "maggiore", 150.5), _regola(G, "costo", "maggiore_uguale", 1000), _regola(G, "numero", "uguale", 12345))
    righe = [testi.regola_a_parole(regola, posto, regole_dell_elenco) for posto, regola in enumerate(regole_dell_elenco)]
    assert righe == [
        "Giocatori, stato: è sul mercato",
        "e età: minore o uguale a 20 anni",
        "Alternativa 2: allenatori, stato: è capo allenatore",
        'e nome o numero: contiene "ros"',
        "e giocatori, costo: non ha il dato",
        "Alternativa 3: giocatori, mancino: sì",
        "e classe: migliore o uguale a F0",
        "e valore: maggiore di 150,5",
        "e costo: maggiore o uguale a 1.000 euro",
        "e numero: uguale a 12345",
    ]
    # La o non compare mai come collegamento: la regola che apre un'alternativa lo dice col suo numero.
    assert not any(riga.startswith(("o ", "O ")) for riga in righe)
    soltanto = (_regola(G, "eta", "uguale", 1),)
    assert testi.regola_a_parole(soltanto[0], 0, soltanto) == "Giocatori, età: uguale a 1 anno"
    car = mercato.caratteristica(G, "punti_allenamento")
    assert testi.valore_a_parole(car, 38.5) == "38,5 punti" and testi.valore_a_parole(car, 1.0) == "1 punto"
    assert testi.valore_a_parole(mercato.caratteristica(A, "tipo"), staff.EX) == "ex giocatore"
    assert testi.valore_a_parole(mercato.caratteristica(G, "mancino"), False) == "no"
    assert testi.NESSUNA_REGOLA.startswith("Nessuna regola: ")
    assert testi.linguetta_dei_filtri(0) == "Filtri, nessuna regola" and testi.linguetta_dei_filtri(1) == "Filtri, 1 regola"
    assert testi.linguetta_dei_filtri(2) == "Filtri, 2 regole"


def test_l_etichetta_del_valore_e_il_perche_di_una_regola_che_non_conta():
    assert testi.etichetta_del_valore(mercato.caratteristica(G, "eta")) == "&Valore, anni compiuti, da 0 a 120"
    assert "le cifre del numero" in testi.etichetta_del_valore(mercato.caratteristica(G, "nome"))
    assert "cifre del numero" not in testi.etichetta_del_valore(mercato.caratteristica(G, "comune"))
    assert testi.etichetta_del_valore(mercato.caratteristica(G, "sesso")) == "&Valore"

    def perche(chiave, valore):
        primo_operatore = regole.operatori(mercato.caratteristica(G, chiave))[0][0]
        return testi.perche_la_regola_non_conta(mercato.Preparazione(mercato.E, G, chiave, primo_operatore, valore))
    assert perche("valore", "1.000") is None and perche("eta", "20") is None
    assert perche("valore", "1.5") == "La regola in preparazione non conta: il punto separa le migliaia: i decimali vanno dopo la virgola, come 150,5."
    assert perche("eta", "") == "La regola in preparazione non conta: il Valore è vuoto."
    assert perche("sesso", None) == "La regola in preparazione non conta: il Valore è su nessun valore."
    assert perche("eta", "2,5") == "La regola in preparazione non conta: età si scrive senza decimali."
    assert perche("valore", "2,55") == "La regola in preparazione non conta: valore si scrive al più con 1 decimale, come nella scheda."
    assert perche("eta", "121") == "La regola in preparazione non conta: età va da 0 a 120."
    assert perche("nome", "x" * 51) == "La regola in preparazione non conta: il testo va da 1 a 50 caratteri."
    assert "come nella scheda, per esempio G4" in perche("classe", "Z9") and "con le cifre" in perche("eta", "venti")
    assert "caratteri di controllo" in perche("nome", "a\tb")
    assert testi.regola_non_pronta(mercato.Preparazione(mercato.E, G, "eta", "minore", "")) == "La regola non si aggiunge: il Valore è vuoto."
    assert testi.regola_non_pronta(mercato.Preparazione(mercato.E, G, "eta", "minore", "3")) is None
    assert testi.regola_non_pronta(mercato.Preparazione(mercato.E, G, "costo", "manca", "")) is None
    pronta = mercato.Preparazione(mercato.E, G, "eta", "minore", "3")
    assert testi.regola_non_aggiunta(pronta, mercato.AL_LIMITE).startswith("La regola non si aggiunge: le regole sono già 50")
    assert testi.regola_non_aggiunta(dataclasses.replace(pronta, valore="3,5"), regole.DECIMALI) == "La regola non si aggiunge: età si scrive senza decimali."
    assert testi.preparazione_nel_preset(pronta, mercato.AGGIUNTA) == "La regola in preparazione entra nel preset, come ultima regola."
    assert testi.preparazione_nel_preset(pronta, mercato.FUORI) == "La regola in preparazione resta fuori dal preset: le regole sono già 50."
    assert testi.preparazione_nel_preset(dataclasses.replace(pronta, valore="3,5"), None).endswith("età si scrive senza decimali.")
    assert testi.preparazione_nel_preset(dataclasses.replace(pronta, valore=""), None) is None


def test_i_trovati_l_annuncio_e_il_campo_trovati(mondo):
    serie = mercato.filtri_di_serie("mercato")
    vuota = mercato.Preparazione()
    righe = mercato.cerca(mondo, serie)
    giocatori = len(righe)
    assert testi.trovati(righe, serie) == f"&Trovati: {giocatori} giocatori" and testi.trovati([], mercato.Filtri()) == "&Trovati: nessuno, senza regole"
    assert testi.trovati([], serie) == "&Trovati: nessuno"
    assert testi.annuncio_dei_trovati(righe, serie, vuota) == f"Trovati: {giocatori} giocatori"
    sbagliata = mercato.Preparazione(mercato.E, G, "valore", "maggiore", "1.5")
    assert testi.annuncio_dei_trovati(righe, serie, sbagliata) == (f"Trovati: {giocatori} giocatori. La regola in preparazione non conta: il punto separa le "
                                                                    "migliaia: i decimali vanno dopo la virgola, come 150,5.")
    campo = testi.riepilogo_dei_trovati(righe, serie, vuota, mondo)
    assert campo == f"{giocatori} giocatori.\nLa regola in preparazione non conta: il Valore è vuoto."
    _accessibile(campo)
    ros = dataclasses.replace(vuota, valore="ro")
    contano = mercato.con_la_preparazione(serie, ros)
    con_ros = mercato.cerca(mondo, contano)
    assert testi.riepilogo_dei_trovati(con_ros, serie, ros, mondo).splitlines()[0] == f"{len(con_ros)} giocatori, con la regola in preparazione."
    assert testi.riepilogo_dei_trovati([], mercato.Filtri(), vuota, mondo).splitlines()[0] == "Nessuno, perché non ci sono regole."
    # Le alternative, quelle che mescolano i bersagli, gli allenatori in un ordine che non hanno, il costo senza polisportiva attiva.
    due = mercato.Filtri((_regola(G, "stato", "uguale", mercato.LIBERO), _regola(A, "stato", "uguale", mercato.LIBERO, mercato.O)), "valore_alto")
    o_preparazione = mercato.Preparazione(mercato.O, A, "sesso", "uguale", "f")
    insieme = mercato.cerca(mondo, mercato.con_la_preparazione(due, o_preparazione))
    campo = testi.riepilogo_dei_trovati(insieme, due, o_preparazione, mondo)
    giocatori, allenatori = mercato.conta_le_righe(insieme)
    assert campo.splitlines() == [f"{giocatori} giocatori e {allenatori} allenatori, con la regola in preparazione.",
                                  "Le regole formano 3 alternative; la regola in preparazione va nell'alternativa 3.",
                                  "Gli allenatori non hanno il dato dell'ordine, valore, dal più alto: vanno in fondo, in ordine di classe."]
    assert testi.trovati(insieme, due) == f"&Trovati: {giocatori} giocatori e {allenatori} allenatori"
    misto = mercato.Filtri((_regola(G, "stato", "uguale", mercato.LIBERO), _regola(A, "stato", "uguale", mercato.LIBERO)), "numero")
    assert "Le regole mescolano giocatori e allenatori: non trovano nessuno." in testi.riepilogo_dei_trovati([], misto, vuota, mondo).splitlines()
    solo_allenatori = mercato.Filtri((_regola(A, "stato", "uguale", mercato.LIBERO),), "costo_basso")
    trovati = mercato.cerca(mondo, solo_allenatori)
    assert "Gli allenatori non hanno il dato dell'ordine, costo, dal più basso: sono in ordine di classe." in testi.riepilogo_dei_trovati(trovati, solo_allenatori,
                                                                                                                                     vuota, mondo)
    mondo.miapolisportiva_attiva = None
    assert testi.riepilogo_dei_trovati(trovati, solo_allenatori, vuota, mondo).endswith("perché l'ingaggio dipende dalla gloria di chi offre.")
    costo = mercato.Filtri((_regola(G, "costo", "minore", 30),), "numero")
    assert testi.riepilogo_dei_trovati([], costo, vuota, mondo).splitlines()[-1].startswith("Senza polisportiva attiva i liberi non hanno un costo")
