"""
Le regole dei filtri di MESS: la macchina che le legge e le prova, senza il mondo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 sera con il costruttore di regole della finestra unica Mercato e ricerca, issue 8 e decisione
D36, idea di Gabriele: al posto di un controllo per ogni filtro, una regola alla volta, fatta di un bersaglio, di una
caratteristica, di un operatore e di un valore, e dalla seconda regola un collegamento, e oppure o. Qui sta quello che
non dipende dal mondo: i cinque tipi delle caratteristiche, numero, classe, testo, scelta e sì o no; gli operatori di
ogni tipo, con chiavi stabili per il salvataggio; la lettura del valore scritto, all'italiana, col punto soltanto per le
migliaia a gruppi di tre e la virgola per i decimali; la prova di una regola su una riga; e le alternative. La e lega
prima della o, come in logica: le regole si dividono in alternative a ogni o, e una persona è trovata se soddisfa tutte
le regole di almeno un'alternativa. Il non sta negli operatori, e i collegamenti sono soltanto e ed o: diverso, non
contiene, non è e non ha il dato sono i contrari esatti di uguale, contiene, è e ha il dato, così chi non ha il dato di
una caratteristica passa soltanto i negativi. I numeri si confrontano come li scrive la scheda, troncati o arrotondati
come lì, e i testi senza badare a maiuscole, accenti e apostrofi, con la chiave di confronto dei luoghi. Il catalogo
delle caratteristiche, che legge il mondo, sta in mercato.py; leggi_classe arriva qui da ricerca.py, che col cambio della
finestra se ne andrà intera.
"""

import unicodedata
from collections import namedtuple
from dataclasses import dataclass
from typing import Any

import classe
import luoghi

# I cinque tipi delle caratteristiche.
NUMERO = "numero"
CLASSE = "classe"
TESTO = "testo"
SCELTA = "scelta"
SI_NO = "si_no"
TIPI = (NUMERO, CLASSE, TESTO, SCELTA, SI_NO)
# Come la scheda scrive un numero: troncato, come l'età in anni compiuti, o arrotondato ai suoi decimali.
TRONCA = "tronca"
ARROTONDA = "arrotonda"
# I due collegamenti: la e lega prima della o.
E = "e"
O = "o"
COLLEGAMENTI = (E, O)
# Gli operatori di ogni tipo, con la chiave del salvataggio e il nome. La scala della classe scende: migliore vuol
# dire un livello più piccolo, più vicino ad A1.
OPERATORI = {
    NUMERO: (("uguale", "uguale a"), ("diverso", "diverso da"), ("maggiore", "maggiore di"), ("maggiore_uguale", "maggiore o uguale a"),
             ("minore", "minore di"), ("minore_uguale", "minore o uguale a")),
    CLASSE: (("uguale", "uguale a"), ("diverso", "diversa da"), ("migliore", "migliore di"), ("migliore_uguale", "migliore o uguale a"),
             ("peggiore", "peggiore di"), ("peggiore_uguale", "peggiore o uguale a")),
    TESTO: (("contiene", "contiene"), ("non_contiene", "non contiene"), ("comincia", "comincia con"), ("uguale", "è"), ("diverso", "non è")),
    SCELTA: (("uguale", "è"), ("diverso", "non è")),
    SI_NO: (("uguale", "è"),),
}
# In coda, per le caratteristiche che possono mancare, come il costo di un ritirato: due operatori senza valore.
MANCA = "manca"
PRESENTE = "presente"
DEL_DATO = ((MANCA, "non ha il dato"), (PRESENTE, "ha il dato"))
SENZA_VALORE = (MANCA, PRESENTE)
# Le negazioni: ogni negativo è il contrario esatto del suo positivo, e chi non ha il dato passa soltanto i negativi.
NEGAZIONI = {"diverso": "uguale", "non_contiene": "contiene", MANCA: PRESENTE}
NEGATIVI = frozenset(NEGAZIONI)
# Il testo di una regola: da 1 a 50 caratteri, senza gli spazi in testa e in coda.
LUNGHEZZA_MASSIMA_DEL_TESTO = 50
# I perché di un valore che non si legge, per testi.py: vuoto, cifre che non sono cifre, il punto fuori dalle migliaia,
# troppi decimali, fuori dalla misura, una classe che non esiste, un carattere di controllo.
VUOTO = "vuoto"
CIFRE = "cifre"
PUNTO = "punto"
DECIMALI = "decimali"
MISURA = "misura"
NON_E_UNA_CLASSE = "classe"
CONTROLLO = "controllo"
# La lettura di un valore scritto: il valore, oppure None col perché.
Lettura = namedtuple("Lettura", "valore problema")


@dataclass(frozen=True, eq=False)
class Caratteristica:
    """
    Una caratteristica del catalogo, su cui si fa una regola. leggi(riga, contesto) dà il dato grezzo della riga, None
    quando manca: un numero, il livello della classe, un testo, la chiave di una scelta, o per una scelta a voci che
    valgono insieme l'insieme delle sue voci, oppure vero o falso; dato lo porta alla forma che si confronta, il numero
    come lo scrive la scheda e il testo con la sua chiave di confronto. unita sono il
    singolare e il plurale dell'unità, come anno e anni, per le parole; decimali e modo dicono come la scheda scrive il
    numero, e massimo fin dove arriva; voci sono le coppie di chiave e nome di una scelta, o una funzione che le dà, per
    quelle lunghe come le regioni, che si leggono alla prima richiesta. puo_mancare aggiunge i due operatori del dato;
    insieme dice che la scelta ha voci che valgono insieme, e allora è vuol dire appartenere; peso ordina le prove, dalla
    più leggera; etichetta è la parte dell'etichetta del Valore che dice che cosa scrivere. cifre, soltanto per il nome o
    numero, legge il numero da confrontare quando il valore ha soltanto cifre; memorizza falso salta la memoria del
    contesto, per i dati che si leggono più in fretta di quanto costi ricordarli, e che leggi dà già nella forma che si
    confronta, come lo stato, il sesso o il numero.
    """
    chiave: str
    nome: str
    tipo: str
    leggi: Any
    unita: tuple = ()
    decimali: int = 0
    modo: str = ARROTONDA
    massimo: float | None = None
    voci: Any = ()
    puo_mancare: bool = False
    insieme: bool = False
    peso: int = 1
    etichetta: str = ""
    cifre: Any = None
    memorizza: bool = True


def dato(caratteristica, riga, contesto):
    """Il dato della riga nella forma che si confronta: il numero come lo scrive la scheda, il testo con la sua chiave di confronto; None se manca."""
    valore = caratteristica.leggi(riga, contesto)
    if valore is None:
        return None
    if caratteristica.tipo == NUMERO:
        return come_la_scheda(caratteristica, valore)
    if caratteristica.tipo == TESTO:
        return luoghi.chiave_di_confronto(valore)
    return valore


class Contesto:
    """
    Il contesto in cui si provano le regole: dà il dato di una riga. Questo legge ogni volta; la memoria della finestra,
    in mercato.py, ricorda ogni lettura finché la finestra è aperta.
    """

    def leggi(self, caratteristica, riga):
        return dato(caratteristica, riga, self)


def voci(caratteristica):
    """Le voci di una scelta, coppie di chiave e nome: quelle date, o quelle della funzione che le dà."""
    return tuple(caratteristica.voci()) if callable(caratteristica.voci) else caratteristica.voci


def nome_della_voce(caratteristica, chiave):
    """Il nome di una voce della scelta; KeyError se non c'è."""
    return dict(voci(caratteristica))[chiave]


def operatori(caratteristica):
    """Gli operatori della caratteristica, coppie di chiave e nome: quelli del suo tipo, e in coda quelli del dato se può mancare."""
    return OPERATORI[caratteristica.tipo] + (DEL_DATO if caratteristica.puo_mancare else ())


def nome_dell_operatore(caratteristica, operatore):
    """Il nome dell'operatore per la caratteristica; KeyError se non è dei suoi."""
    return dict(operatori(caratteristica))[operatore]


def con_caratteri_di_controllo(testo):
    """Vero se il testo ha un a capo, una tabulazione o un altro carattere di controllo, che nelle caselle non si leggerebbe."""
    return any(unicodedata.category(c) in ("Cc", "Zl", "Zp") for c in testo)


def senza_caratteri_di_controllo(testo):
    """Il testo senza i caratteri di controllo, come lo tiene il Valore mentre si scrive."""
    return "".join(c for c in testo if unicodedata.category(c) not in ("Cc", "Zl", "Zp"))


def come_la_scheda(caratteristica, numero):
    """
    Un numero come lo scrive la scheda, perché la regola confronti quello che si legge: troncato agli interi, come l'età
    in anni compiuti e la gloria richiesta, o arrotondato ai decimali della caratteristica come testi.numero, con la
    stessa regola del formato di Python, così 57,25 diventa quello che la scheda scrive.
    """
    if caratteristica.modo == TRONCA:
        return int(numero)
    if caratteristica.decimali == 0:
        return int(f"{numero:.0f}")
    return float(f"{numero:.{caratteristica.decimali}f}")


def leggi_classe(testo):
    """
    Il livello di una classe scritta come nella scheda, G4 o g4, oppure col numero del livello, 64:
    da 1 per A1 a 100 per K0. ValueError se non è una classe.
    """
    scritto = str(testo).strip().upper()
    if len(scritto) == 2 and scritto[0] in classe.LETTERE and scritto[1].isdigit():
        livello = classe.LETTERE.index(scritto[0]) * 10 + int(scritto[1])
    elif scritto.isdigit():
        livello = int(scritto)
    else:
        raise ValueError(f"Non è una classe: {testo!r}")
    if not 1 <= livello <= classe.LIVELLI:
        raise ValueError(f"Non è una classe: {testo!r}")
    return livello


def _leggi_numero(caratteristica, testo):
    """Un numero all'italiana: le cifre, il punto soltanto fra le migliaia a gruppi di tre, la virgola per i decimali."""
    if any(c not in "0123456789.," for c in testo):
        return Lettura(None, CIFRE)
    intera, virgola, decimali = testo.partition(",")
    if "." in decimali:
        return Lettura(None, PUNTO)
    if not intera.replace(".", "") or "," in decimali or (virgola and not decimali):
        return Lettura(None, CIFRE)
    if "." in intera:
        gruppi = intera.split(".")
        if not (1 <= len(gruppi[0]) <= 3 and all(len(gruppo) == 3 for gruppo in gruppi[1:])):
            return Lettura(None, PUNTO)
    if len(decimali) > caratteristica.decimali:
        return Lettura(None, DECIMALI)
    cifre = intera.replace(".", "")
    valore = int(cifre) if caratteristica.decimali == 0 else float(f"{cifre}.{decimali or '0'}")
    if caratteristica.massimo is not None and valore > caratteristica.massimo:
        return Lettura(None, MISURA)
    return Lettura(valore, None)


def leggi_valore(caratteristica, scritto):
    """
    Il valore di una regola com'è nel controllo del Valore, letto per la caratteristica: Lettura col valore, oppure None
    e il perché, VUOTO compreso, per il campo vuoto o per nessun valore. Un numero, una classe o un testo arrivano
    scritti; una scelta come la sua chiave, o None; un sì o no come vero o falso, o None. I numeri vanno da zero al
    massimo, con i decimali che la scheda scrive; i testi da 1 a 50 caratteri; mai caratteri di controllo.
    """
    tipo = caratteristica.tipo
    if tipo == SCELTA:
        if scritto is None or scritto == "":
            return Lettura(None, VUOTO)
        if scritto not in dict(voci(caratteristica)):
            raise ValueError(f"{scritto!r} non è una voce di {caratteristica.chiave}")
        return Lettura(scritto, None)
    if tipo == SI_NO:
        if scritto is None:
            return Lettura(None, VUOTO)
        if not isinstance(scritto, bool):
            raise ValueError(f"{scritto!r} non è sì o no")
        return Lettura(scritto, None)
    testo = (scritto or "").strip()
    if not testo:
        return Lettura(None, VUOTO)
    if con_caratteri_di_controllo(testo):
        return Lettura(None, CONTROLLO)
    if tipo == NUMERO:
        return _leggi_numero(caratteristica, testo)
    if tipo == CLASSE:
        try:
            return Lettura(leggi_classe(testo), None)
        except ValueError:
            return Lettura(None, NON_E_UNA_CLASSE)
    if len(testo) > LUNGHEZZA_MASSIMA_DEL_TESTO:
        return Lettura(None, MISURA)
    return Lettura(testo, None)


def _intero(valore):
    return isinstance(valore, int) and not isinstance(valore, bool)


def valore_valido(caratteristica, operatore, valore):
    """
    Vero se il valore va bene per la regola così com'è salvata, severo come la scrittura: quello che leggi_valore darebbe.
    Senza valore per i due operatori del dato; per gli altri un numero intero, o con al più i decimali della scheda, da
    zero al massimo; un livello da 1 a 100; un testo senza spazi in testa e in coda, da 1 a 50 caratteri e senza
    caratteri di controllo; la chiave di una voce; vero o falso.
    """
    if operatore in SENZA_VALORE:
        return valore is None
    tipo = caratteristica.tipo
    if tipo == NUMERO:
        if caratteristica.decimali == 0:
            buono = _intero(valore)
        else:
            buono = (_intero(valore) or isinstance(valore, float)) and valore == valore and round(valore, caratteristica.decimali) == valore
        return buono and 0 <= valore <= (caratteristica.massimo if caratteristica.massimo is not None else valore)
    if tipo == CLASSE:
        return _intero(valore) and 1 <= valore <= classe.LIVELLI
    if tipo == TESTO:
        return (isinstance(valore, str) and valore == valore.strip() and 1 <= len(valore) <= LUNGHEZZA_MASSIMA_DEL_TESTO
                and not con_caratteri_di_controllo(valore))
    if tipo == SCELTA:
        return isinstance(valore, str) and valore in dict(voci(caratteristica))
    return isinstance(valore, bool)


def _vero_se(caratteristica, operatore, valore):
    """La prova di un operatore positivo sul dato che c'è: vera se il dato la soddisfa."""
    tipo = caratteristica.tipo
    if tipo in (NUMERO, CLASSE):
        confronti = {"uguale": lambda d: d == valore, "maggiore": lambda d: d > valore, "maggiore_uguale": lambda d: d >= valore,
                     "minore": lambda d: d < valore, "minore_uguale": lambda d: d <= valore,
                     # La scala della classe scende: migliore è un livello più piccolo.
                     "migliore": lambda d: d < valore, "migliore_uguale": lambda d: d <= valore, "peggiore": lambda d: d > valore,
                     "peggiore_uguale": lambda d: d >= valore}
        return confronti[operatore]
    if tipo == TESTO:
        cercato = luoghi.chiave_di_confronto(valore)
        if operatore == "contiene":
            return lambda d: cercato in d
        if operatore == "comincia":
            return lambda d: d.startswith(cercato)
        return lambda d: d == cercato
    if caratteristica.insieme:
        return lambda d: valore in d
    return lambda d: d == valore


def prova(caratteristica, operatore, valore):
    """
    La prova di una regola, da fare su una riga nel suo contesto: vera se la riga la soddisfa. Il dato si chiede al
    contesto, che lo ricorda, salvo per le caratteristiche che si leggono al volo. Chi non ha il dato non passa nessun
    confronto e passa ogni negativo: un negativo è il contrario esatto del suo positivo, così una regola e il suo
    contrario, uniti dalla o, trovano tutti. Per il nome o numero scritto con le sole cifre contiene e comincia con
    guardano l'inizio del numero, è il numero esatto. ValueError per un operatore che la caratteristica non ha.
    """
    if operatore not in dict(operatori(caratteristica)):
        raise ValueError(f"L'operatore {operatore!r} non vale per {caratteristica.chiave}")
    if caratteristica.memorizza:
        def leggi(riga, contesto):
            return contesto.leggi(caratteristica, riga)
    else:
        leggi = caratteristica.leggi
    if operatore == MANCA:
        return lambda riga, contesto: leggi(riga, contesto) is None
    if operatore == PRESENTE:
        return lambda riga, contesto: leggi(riga, contesto) is not None
    positivo = NEGAZIONI.get(operatore, operatore)
    # Soltanto le cifre da 0 a 9: un apice come ² per Python è una cifra, ma nessun numero comincia così.
    if caratteristica.cifre is not None and valore.isascii() and valore.isdigit():
        leggi = caratteristica.cifre
        vero = (lambda d: d == valore) if positivo == "uguale" else (lambda d: d.startswith(valore))
    else:
        vero = _vero_se(caratteristica, positivo, valore)
    negativo = operatore in NEGATIVI
    if not caratteristica.puo_mancare:
        if negativo:
            return lambda riga, contesto: not vero(leggi(riga, contesto))
        return lambda riga, contesto: vero(leggi(riga, contesto))
    if negativo:
        def prova_negativa(riga, contesto):
            dato = leggi(riga, contesto)
            return dato is None or not vero(dato)
        return prova_negativa

    def prova_positiva(riga, contesto):
        dato = leggi(riga, contesto)
        return dato is not None and vero(dato)
    return prova_positiva


def alternative(regole):
    """
    Le regole divise in alternative a ogni o, nel loro ordine: la e lega prima della o. Ogni regola ha il campo
    collegamento; quello della prima non conta, perché apre sempre la prima alternativa. Senza regole, nessuna.
    """
    gruppi = []
    for regola in regole:
        if not gruppi or regola.collegamento == O:
            gruppi.append([regola])
        else:
            gruppi[-1].append(regola)
    return gruppi


def compila(regole, caratteristica_della_regola):
    """
    Le prove di ogni alternativa, ciascuna nell'ordine del peso, dalla più leggera, così la più costosa si fa soltanto
    su chi passa le altre. caratteristica_della_regola dà la Caratteristica di una regola, che ha operatore e valore.
    """
    compilate = []
    for alternativa in alternative(regole):
        prove = []
        for posto, regola in enumerate(alternativa):
            caratteristica = caratteristica_della_regola(regola)
            prove.append((caratteristica.peso, posto, prova(caratteristica, regola.operatore, regola.valore)))
        compilate.append([prova_della_regola for _peso, _posto, prova_della_regola in sorted(prove, key=lambda voce: voce[:2])])
    return compilate
