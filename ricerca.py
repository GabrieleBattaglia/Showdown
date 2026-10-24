"""
La ricerca dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, per la ricerca della finestra: si sceglie dove
cercare, una caratteristica e una condizione. Rispetto al vecchio programma, "minore di" vuol
dire davvero minore, e non minore o uguale: problema P11 del piano.
Dalla tappa 7 serve anche il mercato, che mette insieme più filtri: si aggiungono il sesso, la
gloria richiesta e i tratti speciali, e cerca_con_filtri vuole che un giocatore li soddisfi tutti.
Dalla tappa 11, il 2026-10-09, i criteri dell'allenamento e dei contratti: esperienza, classe, punti
allenamento, indole, ambizione, mesi di contratto rimasti, che si contano dalla data simulata, e i
tratti rari dell'allenamento. Per questo ogni criterio legge il giocatore insieme alla data
simulata del giorno. La classe si scrive come si legge nella scheda, per esempio G4, oppure con il
numero del livello, 64, e si cerca migliore o peggiore di quella: la scala scende, e migliore
vuol dire un livello più piccolo.
Dal 24 ottobre 2026, con la issue 8 e la decisione D36, la prova di un filtro e la lettura di un criterio
sono pubbliche, prova e leggi_criterio, perché il motore della finestra unica Mercato e ricerca, in
mercato.py, le usa per le condizioni e per i tratti. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude
Opus 5.5, UltraCode).
Lo stesso giorno, coi collegamenti della finestra, escono la ricerca che stampava nella vista e il filtro del mercato di
prima, coi loro resti: gli ambiti, compreso quello dei risultati della ricerca precedente, cerca e cerca_con_filtri.
Restano i criteri, le condizioni e la prova di un filtro, per le condizioni e i tratti della finestra. È di Gabriele
Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
La sera dello stesso giorno, col motore del costruttore di regole, leggi_classe passa in regole.py, da cui questo modulo
la riprende: il modulo intero se ne andrà col cambio della finestra. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude
Opus 5.5, UltraCode).
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
from regole import leggi_classe

# La lettura della classe scritta, leggi_classe, sta in regole.py dal costruttore di regole: qui resta per le condizioni di oggi.

NUMERO = "numero"
TESTO = "testo"
SI_NO = "si_no"
SESSO = "sesso"
CLASSE = "classe"
CONDIZIONI = {NUMERO: (("maggiore", "maggiore di"), ("minore", "minore di")), TESTO: (("contiene", "contiene"),), SI_NO: (("si", "sì"), ("no", "no")),
              SESSO: (("m", "uomo"), ("f", "donna")), CLASSE: (("migliore", "migliore di"), ("peggiore", "peggiore di"))}


def _nome_caratteristica(nome_base):
    return NOME_ATTR_TO_DISPLAY_MAP[nome_base].capitalize()


# Le caratteristiche su cui si può cercare: chiave, nome da mostrare, tipo e come leggerla dal
# giocatore, con la data simulata del giorno, che serve soltanto ai mesi di contratto.
CRITERI = (
    ("valore", "Valore", NUMERO, lambda g, _oggi: g.indice_collettivo_valore),
    ("classe", "Classe", CLASSE, lambda g, _oggi: classe.classe(g).livello),
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


def nome_condizione(criterio, condizione):
    return dict(CONDIZIONI[tipo_criterio(criterio)])[condizione]


def leggi_numero(testo):
    """Un numero scritto con la virgola o con il punto; ValueError se non è un numero."""
    return float(str(testo).strip().replace(",", "."))


def leggi_criterio(criterio, g, oggi=None):
    """Il valore del criterio per il giocatore, il giorno dato: un numero, un testo, il sesso, oppure vero o falso."""
    return _CRITERI[criterio][2](g, oggi)


def prova(criterio, condizione, valore, oggi=None):
    """La prova di un filtro, da fare su un giocatore il giorno dato: vera se il giocatore lo soddisfa."""
    _nome, tipo, leggi = _CRITERI[criterio]
    if condizione not in dict(CONDIZIONI[tipo]):
        raise ValueError(f"Condizione {condizione!r} non valida per {criterio}")
    if tipo == NUMERO:
        if condizione == "maggiore":
            return lambda g: leggi(g, oggi) > valore
        return lambda g: leggi(g, oggi) < valore
    if tipo == CLASSE:
        # La scala scende: migliore vuol dire un livello più piccolo, cioè più vicino ad A1.
        valore = leggi_classe(valore) if isinstance(valore, str) else valore
        if condizione == "migliore":
            return lambda g: leggi(g, oggi) < valore
        return lambda g: leggi(g, oggi) > valore
    if tipo == TESTO:
        cercato = str(valore).casefold()
        return lambda g: cercato in leggi(g, oggi).casefold()
    if tipo == SESSO:
        return lambda g: leggi(g, oggi) == condizione
    return lambda g: bool(leggi(g, oggi)) == (condizione == "si")
