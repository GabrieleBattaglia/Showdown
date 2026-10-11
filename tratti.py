"""
I tratti rari dell'allenamento e l'ambizione dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11, decisione D31. Tre tratti rari legati all'allenamento: il
talento, che impara più in fretta; l'apprendista rapido, che impara e dimentica in fretta; la
maturazione precoce o tardiva, che sposta gli anni migliori e l'inizio del declino. In più
l'ambizione, da 0 a 100, che decide la durata dei contratti e conta nel rinnovo.
Come il temperamento, i tratti e l'ambizione nascono dal numero del giocatore, con un generatore
tutto loro: il caso del mondo non si tocca, la nascita resta quella di prima, e la migrazione dà ai
giocatori di oggi gli stessi tratti che avrebbero avuto nascendo.
Il modulo dipende soltanto dalle costanti: serve a modelli.py, per il declino, e ad allenamento.py,
per l'efficacia, e così i due non si importano a vicenda.
"""

import random

from costanti import (
    AGING_START_AGE_ANNI,
    AMBIZIONE_DEVIAZIONE,
    AMBIZIONE_MEDIA,
    ANNI_RAMPA_MATURAZIONE,
    ANNO_SIMULAZIONE_GIORNI,
    CURVA_ETA_NUMERATORE,
    CURVA_ETA_SPOSTAMENTO,
    ETA_PERNO_MATURAZIONE,
    SPOSTAMENTO_DECLINO,
    TRATTI_ALLENAMENTO,
)

# L'inizio del declino in giorni d'età, secondo la maturazione: si calcola una volta, perché il
# declino lo chiede ogni giorno per ogni giocatore.
_INIZIO_DECLINO_GIORNI = {None: int(AGING_START_AGE_ANNI * ANNO_SIMULAZIONE_GIORNI),
                          **{chiave: int((AGING_START_AGE_ANNI + anni) * ANNO_SIMULAZIONE_GIORNI) for chiave, anni in SPOSTAMENTO_DECLINO.items()}}


def tratti_innati(id_giocatore):
    """
    I tratti rari con cui nasce un giocatore, da un generatore nato dal suo numero: talento e
    apprendista rapido, vero o falso, e la maturazione, precoce, tardiva o None, che si escludono.
    """
    rng = random.Random(f"MESS-tratti-{id_giocatore}")
    talento = rng.random() * 100.0 < TRATTI_ALLENAMENTO["talento"]["probabilita"]
    apprendista = rng.random() * 100.0 < TRATTI_ALLENAMENTO["apprendista_rapido"]["probabilita"]
    tiro = rng.random() * 100.0
    precoce = TRATTI_ALLENAMENTO["precoce"]["probabilita"]
    if tiro < precoce:
        maturazione = "precoce"
    elif tiro < precoce + TRATTI_ALLENAMENTO["tardiva"]["probabilita"]:
        maturazione = "tardiva"
    else:
        maturazione = None
    return {"talento": talento, "apprendista_rapido": apprendista, "maturazione": maturazione}


def ambizione_innata(id_giocatore):
    """
    L'ambizione con cui nasce un giocatore, da 0, il più modesto, a 100, con un decimale: una
    gaussiana attorno a 50, da un generatore nato dal suo numero, come il temperamento.
    """
    tiro = random.Random(f"MESS-ambizione-{id_giocatore}").gauss(AMBIZIONE_MEDIA, AMBIZIONE_DEVIAZIONE)
    return round(max(0.0, min(100.0, tiro)), 1)


def curva_eta(anni):
    """La curva d'età di Hattrick, 54 diviso gli anni più 37: i ragazzi imparano un po' più in fretta, gli anziani un po' più piano."""
    return CURVA_ETA_NUMERATORE / (anni + CURVA_ETA_SPOSTAMENTO)


def fattore_maturazione(g):
    """
    Quanto la maturazione sposta l'efficacia: 1 per chi non ha il tratto; per il precoce 1,3 da
    ragazzo e 0,7 da anziano, per il tardivo 0,75 da ragazzo e 1,25 da anziano, in linea retta
    fra i 20 e i 40 anni, con il perno ai 30.
    """
    maturazione = getattr(g, "maturazione", None)
    if maturazione is None:
        return 1.0
    anni = g.eta / ANNO_SIMULAZIONE_GIORNI
    rampa = max(-1.0, min(1.0, (ETA_PERNO_MATURAZIONE - anni) / ANNI_RAMPA_MATURAZIONE))
    return 1.0 + TRATTI_ALLENAMENTO[maturazione]["maturazione"] * rampa


def efficacia_dei_tratti(g):
    """Il moltiplicatore dell'efficacia dato dal talento e dall'apprendista rapido, 1 per chi non li ha."""
    fattore = 1.0
    if getattr(g, "talento", False):
        fattore *= TRATTI_ALLENAMENTO["talento"]["efficacia"]
    if getattr(g, "apprendista_rapido", False):
        fattore *= TRATTI_ALLENAMENTO["apprendista_rapido"]["efficacia"]
    return fattore


def oblio_mensile(g):
    """Per quanto si moltiplica ogni mese l'allenata dell'apprendista rapido; 1 per gli altri."""
    if getattr(g, "apprendista_rapido", False):
        return TRATTI_ALLENAMENTO["apprendista_rapido"]["oblio_mensile"]
    return 1.0


def eta_inizio_declino(g):
    """L'età, in anni, da cui comincia il declino: 50, 44 per la maturazione precoce, 56 per la tardiva."""
    return AGING_START_AGE_ANNI + SPOSTAMENTO_DECLINO.get(getattr(g, "maturazione", None), 0.0)


def giorni_inizio_declino(g):
    """L'inizio del declino in giorni d'età, il numero che il declino quotidiano confronta con l'età."""
    return _INIZIO_DECLINO_GIORNI[getattr(g, "maturazione", None)]
