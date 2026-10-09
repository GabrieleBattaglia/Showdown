"""
La ricerca dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, per la ricerca della finestra: si sceglie dove
cercare, una caratteristica e una condizione. Rispetto al vecchio programma, "minore di" vuol
dire davvero minore, e non minore o uguale: problema P11 del piano.
Dalla tappa 7 serve anche il mercato, che mette insieme più filtri: si aggiungono il sesso, la
gloria richiesta e i tratti speciali, e cerca_con_filtri vuole che un giocatore li soddisfi tutti.
Dalla tappa 11, il 2026-10-09, i criteri dell'allenamento e dei contratti: esperienza, classe, cioè
il numero del livello, da 1 per A1 a 100 per K0, punti allenamento, indole, ambizione, mesi di
contratto rimasti, che si contano dalla data simulata, e i tratti rari dell'allenamento. Per questo
ogni criterio legge il giocatore insieme alla data simulata del giorno.
"""

import classe
import contratti
from costanti import (
    CARATTERISTICHE_ATTACCO_BASE,
    CARATTERISTICHE_CONTROLLO_BASE,
    CARATTERISTICHE_DIFESA_BASE,
    CARATTERISTICHE_FISICHE_BASE,
    INDOLI,
    NOME_ATTR_TO_DISPLAY_MAP,
)

# Dove si può cercare, con il nome da mostrare.
AMBITI = (
    ("attivi", "i giocatori in attività"),
    ("tutti", "tutti i giocatori"),
    ("liberi", "i giocatori liberi"),
    ("tesserati", "i giocatori tesserati"),
    ("nuovi", "i nuovi arrivati della sessione"),
    ("ritirati", "i giocatori ritirati"),
    ("usciti", "gli usciti di scena nella sessione"),
    ("trovati", "i risultati della ricerca precedente"),
)
NUMERO = "numero"
TESTO = "testo"
SI_NO = "si_no"
SESSO = "sesso"
CONDIZIONI = {NUMERO: (("maggiore", "maggiore di"), ("minore", "minore di")), TESTO: (("contiene", "contiene"),), SI_NO: (("si", "sì"), ("no", "no")),
              SESSO: (("m", "uomo"), ("f", "donna"))}
# I tipi di criterio per cui non serve scrivere un valore: basta la condizione.
SENZA_VALORE = (SI_NO, SESSO)


def _nome_caratteristica(nome_base):
    return NOME_ATTR_TO_DISPLAY_MAP[nome_base].capitalize()


# Le caratteristiche su cui si può cercare: chiave, nome da mostrare, tipo e come leggerla dal
# giocatore, con la data simulata del giorno, che serve soltanto ai mesi di contratto.
CRITERI = (
    ("valore", "Valore", NUMERO, lambda g, _oggi: g.indice_collettivo_valore),
    ("classe", "Classe, il numero del livello, da 1 per A1 a 100 per K0", NUMERO, lambda g, _oggi: classe.classe(g).livello),
    ("eta", "Età in anni", NUMERO, lambda g, _oggi: g.eta_anni),
    ("gloria_richiesta", "Gloria richiesta", NUMERO, lambda g, _oggi: g.gloria_richiesta),
    ("esperienza", "Esperienza di carriera", NUMERO, lambda g, _oggi: g.esperienza),
    ("punti_allenamento", "Punti allenamento", NUMERO, lambda g, _oggi: g.punti_allenamento),
    ("ambizione", "Ambizione, da 0 a 100", NUMERO, lambda g, _oggi: g.ambizione),
    ("mesi_contratto", "Mesi di contratto rimasti", NUMERO, lambda g, oggi: contratti.mesi_al_termine(g, oggi) if oggi is not None else 0.0),
    ("nome", "Nome", TESTO, lambda g, _oggi: g.nome),
    ("cognome", "Cognome", TESTO, lambda g, _oggi: g.cognome),
    ("indole", "Indole", TESTO, lambda g, _oggi: INDOLI[g.indole]["nome"]),
    ("sesso", "Sesso", SESSO, lambda g, _oggi: g.sesso),
    ("ipovedente", "Ipovedente", SI_NO, lambda g, _oggi: g.ipovedente),
    ("mancino", "Mancino", SI_NO, lambda g, _oggi: g.mancino),
    ("ambidestro", "Ambidestro", SI_NO, lambda g, _oggi: g.ambidestro),
    ("giocorapido", "Gioco rapido", SI_NO, lambda g, _oggi: g.giocorapido),
    ("cambiovelocita", "Cambio di velocità", SI_NO, lambda g, _oggi: g.cambiovelocita),
    ("talento", "Talento", SI_NO, lambda g, _oggi: g.talento),
    ("apprendista_rapido", "Apprendista rapido", SI_NO, lambda g, _oggi: g.apprendista_rapido),
    ("precoce", "Maturazione precoce", SI_NO, lambda g, _oggi: g.maturazione == "precoce"),
    ("tardiva", "Maturazione tardiva", SI_NO, lambda g, _oggi: g.maturazione == "tardiva"),
    *((nome_base, _nome_caratteristica(nome_base), NUMERO, lambda g, _oggi, n=nome_base: g._get_valore_totale(n))
      for nome_base in CARATTERISTICHE_FISICHE_BASE + CARATTERISTICHE_DIFESA_BASE + CARATTERISTICHE_ATTACCO_BASE + CARATTERISTICHE_CONTROLLO_BASE),
)
_CRITERI = {chiave: (nome, tipo, leggi) for chiave, nome, tipo, leggi in CRITERI}


def tipo_criterio(criterio):
    return _CRITERI[criterio][1]


def nome_criterio(criterio):
    return _CRITERI[criterio][0]


def nome_ambito(ambito):
    return dict(AMBITI)[ambito]


def nome_condizione(criterio, condizione):
    return dict(CONDIZIONI[tipo_criterio(criterio)])[condizione]


def ids_ambito(mondo, ambito):
    """Gli identificativi dei giocatori fra cui cercare, in ordine di numero."""
    morti = mondo._ids_morti_processati_sessione
    giocatori = mondo.giocatori
    if ambito == "tutti":
        ids = list(giocatori)
    elif ambito == "attivi":
        ids = [gid for gid, g in giocatori.items() if gid not in morti and not g.ritirato]
    elif ambito == "liberi":
        ids = [gid for gid, g in giocatori.items() if gid not in morti and not g.ritirato and g.appartenenza == "*"]
    elif ambito == "tesserati":
        ids = [gid for gid, g in giocatori.items() if gid not in morti and not g.ritirato and g.appartenenza != "*"]
    elif ambito == "nuovi":
        ids = [gid for gid in mondo.nuovi_giocatori_sessione if gid in giocatori]
    elif ambito == "ritirati":
        ids = [gid for gid, g in giocatori.items() if gid not in morti and g.ritirato]
    elif ambito == "usciti":
        ids = [gid for gid in morti if gid in giocatori]
    elif ambito == "trovati":
        ids = [gid for gid in mondo.risultati_ultima_ricerca if gid in giocatori]
    else:
        raise ValueError(f"Ambito di ricerca sconosciuto: {ambito}")
    return sorted(ids)


def leggi_numero(testo):
    """Un numero scritto con la virgola o con il punto; ValueError se non è un numero."""
    return float(str(testo).strip().replace(",", "."))


def _prova(criterio, condizione, valore, oggi=None):
    """La prova di un filtro, da fare su un giocatore il giorno dato: vera se il giocatore lo soddisfa."""
    _nome, tipo, leggi = _CRITERI[criterio]
    if condizione not in dict(CONDIZIONI[tipo]):
        raise ValueError(f"Condizione {condizione!r} non valida per {criterio}")
    if tipo == NUMERO:
        if condizione == "maggiore":
            return lambda g: leggi(g, oggi) > valore
        return lambda g: leggi(g, oggi) < valore
    if tipo == TESTO:
        cercato = str(valore).casefold()
        return lambda g: cercato in leggi(g, oggi).casefold()
    if tipo == SESSO:
        return lambda g: leggi(g, oggi) == condizione
    return lambda g: bool(leggi(g, oggi)) == (condizione == "si")


def cerca_con_filtri(mondo, ambito, filtri):
    """
    Gli identificativi dei giocatori dell'ambito che soddisfano tutti i filtri, ciascuno una terna
    di criterio, condizione e valore, in ordine di numero. Senza filtri, tutto l'ambito.
    """
    oggi = getattr(mondo, "datetime_corrente_simulazione", None)
    prove = [_prova(criterio, condizione, valore, oggi) for criterio, condizione, valore in filtri]
    return [gid for gid in ids_ambito(mondo, ambito) if all(prova(mondo.giocatori[gid]) for prova in prove)]


def cerca(mondo, ambito, criterio, condizione, valore=None):
    """
    Gli identificativi dei giocatori dell'ambito che soddisfano la condizione, in ordine di numero.
    Per le caratteristiche numeriche valore è un numero; per nome e cognome un testo, cercato
    senza badare alle maiuscole; per il sesso e per il sì o no non serve.
    """
    return cerca_con_filtri(mondo, ambito, [(criterio, condizione, valore)])
