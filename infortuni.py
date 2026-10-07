"""
Gli infortuni dei giocatori di MESS, con la loro sede.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25. L'infortunio resta a fine partita, come prima, ma
ora ha una sede: un braccio, la schiena, un ginocchio o una caviglia. Quello al braccio ferma tutti
tranne l'ambidestro, che continua a giocare con l'altro braccio, ed è questo il suo vantaggio,
insieme a una probabilità un po' più bassa: regola di Gabriele, al posto del vecchio quinto della
probabilità e della durata. La probabilità cresce con l'età, come prima, e con il carico della
partita, cioè con la radice delle azioni giocate; la durata cresce con l'età e con la poca
resistenza, come prima, e con un fattore della sede.
Il caso viene da un generatore che la facciata del motore fa nascere dal seme della partita, così
gli infortuni non toccano il caso del mondo e una partita rigiocata dà gli stessi.
"""

import datetime
import math

from costanti import (
    AGING_PEAK_AGE_GIORNI,
    ANNO_SIMULAZIONE_GIORNI,
    AZIONI_RIFERIMENTO_INFORTUNIO,
    CARICO_INFORTUNIO_MASSIMO,
    CARICO_INFORTUNIO_MINIMO,
    ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI,
    ETA_MAX_PROB_INFORTUNIO_ANNI,
    FATTORE_INFORTUNIO_AMBIDESTRO,
    INFORTUNIO_DURATA_MAX_GIORNI_ETA,
    INFORTUNIO_DURATA_MIN_GIORNI,
    INFORTUNIO_MALUS_MAX_RESISTENZA,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    PROB_INFORTUNIO_AUMENTO_MAX_PERC,
    PROB_INFORTUNIO_BASE_PER_PARTITA,
    SEDE_NON_PRECISATA,
    SEDI_INFORTUNIO,
)
from utilita import accorda, data_breve

_SEDI = {codice: (frase, braccio, peso, fattore) for codice, frase, braccio, peso, fattore in SEDI_INFORTUNIO}
SEDI_VALIDE = frozenset((*_SEDI, SEDE_NON_PRECISATA))


def fattore_carico(azioni):
    """Il carico della partita: la radice delle azioni sul riferimento, fra il minimo e il massimo."""
    if AZIONI_RIFERIMENTO_INFORTUNIO <= 0:
        return 1.0
    return max(CARICO_INFORTUNIO_MINIMO, min(CARICO_INFORTUNIO_MASSIMO, math.sqrt(max(0, azioni) / AZIONI_RIFERIMENTO_INFORTUNIO)))


def probabilita(g, azioni):
    """La probabilità di infortunio dopo una partita, in percentuale: cresce dai 30 anni e col carico; l'ambidestro ne ha un po' meno."""
    aumento = 0.0
    anni = g.eta_anni
    if anni > ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI:
        intervallo = max(1.0, ETA_MAX_PROB_INFORTUNIO_ANNI - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI)
        aumento = (min(anni, ETA_MAX_PROB_INFORTUNIO_ANNI) - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI) / intervallo * PROB_INFORTUNIO_AUMENTO_MAX_PERC
    risultato = (PROB_INFORTUNIO_BASE_PER_PARTITA + aumento) * fattore_carico(azioni)
    if getattr(g, "ambidestro", False):
        risultato *= FATTORE_INFORTUNIO_AMBIDESTRO
    return max(0.0, min(risultato, 95.0))


def pesi_sedi(g):
    """I pesi delle sedi per la mano del giocatore: per il mancino le braccia si scambiano, per l'ambidestro se ne fa la media."""
    pesi = {codice: peso for codice, (_frase, _braccio, peso, _fattore) in _SEDI.items()}
    if getattr(g, "mancino", False) or getattr(g, "ambidestro", False):
        scambiati = dict(pesi)
        for codice in pesi:
            if codice.endswith("_dx"):
                gemella = codice[:-3] + "_sx"
                scambiati[codice], scambiati[gemella] = pesi[gemella], pesi[codice]
        if getattr(g, "ambidestro", False):
            scambiati = {codice: (pesi[codice] + scambiati[codice]) / 2.0 for codice in pesi}
        pesi = scambiati
    return tuple((codice, pesi[codice]) for codice, *_resto in SEDI_INFORTUNIO)


def estrai_sede(g, rng):
    """La sede di un infortunio, estratta coi pesi della mano del giocatore."""
    pesi = pesi_sedi(g)
    soglia = rng.random() * sum(peso for _codice, peso in pesi)
    cumulata = 0.0
    for codice, peso in pesi:
        cumulata += peso
        if soglia < cumulata:
            return codice
    return pesi[-1][0]


def durata(g, sede, rng):
    """La durata in giorni simulati: più lunga con l'età e con poca resistenza, per il fattore della sede."""
    if ANNO_SIMULAZIONE_GIORNI <= 0:
        return rng.randint(3, 20)
    eta_norm = max(0.0, min(1.0, g.eta / max(1, AGING_PEAK_AGE_GIORNI)))
    minimo, massimo = INFORTUNIO_DURATA_MIN_GIORNI, INFORTUNIO_DURATA_MAX_GIORNI_ETA
    medio = (minimo + massimo) / 2.0
    if rng.random() < eta_norm ** 1.5:
        da = min(math.ceil(medio), massimo)
        base = rng.randint(da, massimo)
    else:
        a = max(math.floor(medio), minimo)
        base = rng.randint(minimo, a)
    resistenza = max(0.0, min(g._get_valore_totale("resistenza_base"), MAX_TOTALE_PRECISIONE_RESISTENZA))
    malus = (1.0 - resistenza / MAX_TOTALE_PRECISIONE_RESISTENZA) * INFORTUNIO_MALUS_MAX_RESISTENZA if MAX_TOTALE_PRECISIONE_RESISTENZA > 0 else 0.0
    fattore = _SEDI[sede][3] if sede in _SEDI else 1.0
    return max(INFORTUNIO_DURATA_MIN_GIORNI, round((base + malus) * fattore))


def braccio_della_sede(sede):
    """Il braccio della sede, dx o sx, oppure None per schiena, gambe e sede non precisata."""
    return _SEDI[sede][1] if sede in _SEDI else None


def frase_sede(sede):
    """La sede a parole, con l'articolo: al polso destro; vuota per la sede non precisata."""
    return _SEDI[sede][0] if sede in _SEDI else ""


def gioca_con_l_altro_braccio(g, sede):
    """Vero se l'infortunio lascia giocare: l'ambidestro con un braccio fermo gioca con l'altro."""
    return bool(getattr(g, "ambidestro", False)) and braccio_della_sede(sede) is not None


def testo_diario(g, sede, data_fine):
    """La voce del diario: Si infortuna al polso destro: resterà fermo fino al 3 marzo 2026."""
    dove = frase_sede(sede)
    inizio = f"Si infortuna {dove}" if dove else "Si infortuna"
    if gioca_con_l_altro_braccio(g, sede):
        altro = "sinistro" if braccio_della_sede(sede) == "dx" else "destro"
        return f"{inizio}: fino al {data_breve(data_fine)} giocherà con il braccio {altro}."
    return f"{inizio}: resterà {accorda(g.sesso, 'fermo')} fino al {data_breve(data_fine)}."


def infortuna(mondo, g, azioni, rng):
    """
    Dopo una partita: se il caso lo vuole, il giocatore si infortuna, con la sede e la durata, e
    lo dice il suo diario. Restituisce la frase da mostrare, oppure None. Chi è già infortunato,
    come l'ambidestro che gioca con l'altro braccio, non si infortuna di nuovo.
    """
    if g.infortunato:
        return None
    if not rng.random() * 100.0 < probabilita(g, azioni):
        return None
    sede = estrai_sede(g, rng)
    giorni = durata(g, sede, rng)
    fine = mondo.datetime_corrente_simulazione + datetime.timedelta(days=giorni)
    g.infortunato = True
    g.infortunio_fine_datetime = fine
    g.infortunio_sede = sede
    testo = testo_diario(g, sede, fine)
    mondo.annota(g, testo)
    return f"{g.nome} {g.cognome}: {testo[0].lower()}{testo[1:]}"
