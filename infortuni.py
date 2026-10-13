"""
Gli infortuni dei giocatori di MESS, con la loro sede, e dalla tappa 12 gli acciacchi.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode); dalla tappa 12
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-07 con la tappa 9, decisione D25. L'infortunio ha una sede: un braccio, la schiena,
un ginocchio o una caviglia. Quello al braccio ferma tutti tranne l'ambidestro, che continua a
giocare con l'altro braccio, ed è questo il suo vantaggio, insieme a una probabilità un po' più
bassa: regola di Gabriele, al posto del vecchio quinto della probabilità e della durata. La
probabilità cresce con l'età, come prima, e con il carico della partita, cioè con la radice delle
azioni giocate; la durata cresce con l'età e con la poca resistenza, come prima, e con un fattore
della sede.
Dalla tappa 11, il 2026-10-09, decisione D31, l'intensità dell'allenamento cambia il rischio: in
partita la probabilità si moltiplica per il fattore della sua intensità, sopra quello del carico; e
soltanto l'intensa porta un piccolo rischio anche in seduta, ogni giorno, che cresce dai 30 anni. Il
caso della seduta viene da un generatore nato dalla data e dal numero del giocatore: il caso del
mondo non si tocca, e siccome l'intensa la sceglie soltanto l'utente per i suoi tesserati, ogni
giorno si tirano pochi numeri.
Dalla tappa 12, il 2026-10-13, decisione D32, risposte 6 e 7 di Gabriele e la sua regola sugli
infortuni: l'infortunio d'incontro non si estrae più qui a fine partita, ma nel motore, a fine set,
e soltanto un quinto di quelli di prima ferma il giocatore; il resto diventa acciacco, cioè a fine
incontro il giocatore risente di un colpo, gioca lo stesso, ma per qualche giorno rende un poco
meno. Qui la probabilità si divide in due: probabilita_base, senza il carico, che il motore riceve
per ogni giocatore, e probabilita, che dà gli stessi numeri di prima ed è la probabilità che
nell'incontro succeda qualcosa. La facciata del motore porta nel mondo quello che il motore ha
estratto: colpisci applica l'infortunio, con la sua durata, acciacca l'acciacco, con la sua durata e
il suo calo; calo_acciacco dice quanto rende di meno oggi chi ne ha uno. Il fattore del carico, i
pesi delle sedi e la loro estrazione stanno nel motore, in motore/campo.py, e si importano da lì.
Un acciacco nuovo su uno in corso tiene il più pesante; un infortunio che ferma cancella l'acciacco,
perché chi guarisce torna fresco. L'acciacco non ferma, non toglie punti né esperienza e non alza il
rischio d'infortunio.
"""

import datetime
import math
import random

from costanti import (
    ACCIACCO_CALO_MASSIMO,
    ACCIACCO_CALO_MINIMO,
    ACCIACCO_GIORNI_MASSIMO,
    ACCIACCO_GIORNI_MINIMO,
    AGING_PEAK_AGE_GIORNI,
    ANNO_SIMULAZIONE_GIORNI,
    AUMENTO_RISCHIO_SEDUTA,
    ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI,
    ETA_MAX_PROB_INFORTUNIO_ANNI,
    FATTORE_INFORTUNIO_AMBIDESTRO,
    INFORTUNIO_DURATA_MAX_GIORNI_ETA,
    INFORTUNIO_DURATA_MIN_GIORNI,
    INFORTUNIO_MALUS_MAX_RESISTENZA,
    INTENSITA,
    INTENSITA_PREDEFINITA,
    MAX_TOTALE_PRECISIONE_RESISTENZA,
    PROB_INFORTUNIO_AUMENTO_MAX_PERC,
    PROB_INFORTUNIO_BASE_PER_PARTITA,
    SEDE_NON_PRECISATA,
    SEDI_INFORTUNIO,
)
from motore.campo import estrai_sede, fattore_carico, pesi_sedi
from utilita import accorda, data_breve

__all__ = ("SEDI_VALIDE", "acciacca", "braccio_della_sede", "calo_acciacco", "colpisci", "durata", "estrai_sede", "fattore_carico", "frase_sede",
           "gioca_con_l_altro_braccio", "guarisci_acciacco", "infortunio_in_seduta", "intensita_di", "pesi_sedi", "probabilita", "probabilita_base",
           "probabilita_in_seduta", "testo_acciacco", "testo_diario")

_SEDI = {codice: (frase, braccio, peso, fattore) for codice, frase, braccio, peso, fattore in SEDI_INFORTUNIO}
SEDI_VALIDE = frozenset((*_SEDI, SEDE_NON_PRECISATA))
# Il tetto della probabilità d'infortunio di un incontro, in percentuale.
PROBABILITA_MASSIMA = 95.0


def _quota_eta(anni):
    """Quanto l'età ha alzato il rischio, da 0 a 30 anni a 1 dai 75 in su."""
    intervallo = max(1.0, ETA_MAX_PROB_INFORTUNIO_ANNI - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI)
    return max(0.0, min(anni, ETA_MAX_PROB_INFORTUNIO_ANNI) - ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI) / intervallo


def intensita_di(g):
    """La riga della tabella INTENSITA per il giocatore: la sua intensità, normale se non ne ha."""
    return INTENSITA[getattr(g, "intensita", INTENSITA_PREDEFINITA)]


def probabilita_base(g):
    """
    La probabilità d'infortunio di un incontro senza il carico, in percentuale: cresce dai 30 anni,
    si moltiplica per il fattore dell'intensità, e l'ambidestro ne ha un po' meno. Il motore la
    riceve per ogni giocatore e la moltiplica per il carico delle azioni giocate, tappa 12.
    """
    aumento = _quota_eta(g.eta_anni) * PROB_INFORTUNIO_AUMENTO_MAX_PERC
    risultato = (PROB_INFORTUNIO_BASE_PER_PARTITA + aumento) * intensita_di(g)["infortuni_partita"]
    if getattr(g, "ambidestro", False):
        risultato *= FATTORE_INFORTUNIO_AMBIDESTRO
    return max(0.0, risultato)


def probabilita(g, azioni):
    """
    La probabilità che in un incontro con tante azioni succeda qualcosa al giocatore, in
    percentuale, la stessa d'infortunio di prima della tappa 12: la base per il carico, al massimo 95.
    Dalla tappa 12 un quinto sono infortuni che fermano, a fine set, e il resto acciacchi.
    """
    return max(0.0, min(probabilita_base(g) * fattore_carico(azioni), PROBABILITA_MASSIMA))


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


def testo_diario(g, sede, data_fine, in_allenamento=False):
    """La voce del diario: Si infortuna al polso destro: resterà fermo fino al 3 marzo 2026; con in_allenamento, Si infortuna in allenamento."""
    dove = frase_sede(sede)
    inizio = "Si infortuna in allenamento" if in_allenamento else "Si infortuna"
    if dove:
        inizio += f" {dove}"
    if gioca_con_l_altro_braccio(g, sede):
        altro = "sinistro" if braccio_della_sede(sede) == "dx" else "destro"
        return f"{inizio}: fino al {data_breve(data_fine)} giocherà con il braccio {altro}."
    return f"{inizio}: resterà {accorda(g.sesso, 'fermo')} fino al {data_breve(data_fine)}."


def _in_frase(g, testo):
    return f"{g.nome} {g.cognome}: {testo[0].lower()}{testo[1:]}"


def colpisci(mondo, g, sede, rng, annota=True):
    """
    Un infortunio estratto dal motore entra nel mondo, tappa 12: la durata dal generatore che la
    facciata fa nascere dal seme dell'incontro, l'infortunio con la sua sede e, se annota, la voce nel
    diario. L'infortunio che ferma cancella l'acciacco. Restituisce la frase da mostrare, oppure None
    per chi era già infortunato, che non si infortuna di nuovo.
    """
    if g.infortunato:
        return None
    fine = mondo.datetime_corrente_simulazione + datetime.timedelta(days=durata(g, sede, rng))
    g.infortunato = True
    g.infortunio_fine_datetime = fine
    g.infortunio_sede = sede
    guarisci_acciacco(g)
    testo = testo_diario(g, sede, fine)
    if annota:
        mondo.annota(g, testo)
    return _in_frase(g, testo)


def guarisci_acciacco(g):
    """Toglie l'acciacco: è finito, o un infortunio che ferma l'ha cancellato."""
    g.acciacco_fino = None
    g.acciacco_calo = 0.0
    g.acciacco_giorni = 0
    g.acciacco_sede = None


def calo_acciacco(g, oggi):
    """
    Quanto rende di meno oggi chi ha un acciacco, da 0 a 1: il calo del primo giorno, che scende in
    linea retta, ogni giorno di una parte uguale, fino a zero il giorno della fine. Zero senza acciacco.
    """
    fino = getattr(g, "acciacco_fino", None)
    giorni = getattr(g, "acciacco_giorni", 0)
    if fino is None or giorni <= 0:
        return 0.0
    oggi = oggi.date() if isinstance(oggi, datetime.datetime) else oggi
    restano = (fino.date() - oggi).days
    if restano <= 0:
        return 0.0
    return g.acciacco_calo * min(1.0, restano / giorni)


def testo_acciacco(g, sede, giorni):
    """La voce del diario dell'acciacco: Risente di un colpo al ginocchio: per 5 giorni renderà un poco meno."""
    dove = frase_sede(sede)
    colpo = f"Risente di un colpo {dove}" if dove else "Risente di un colpo"
    return f"{colpo}: per {giorni} giorni renderà un poco meno."


def acciacca(mondo, g, sede, rng, annota=True):
    """
    Un acciacco estratto dal motore a fine incontro entra nel mondo, tappa 12: la durata, da 3 a 7
    giorni, e il calo del primo giorno, dal generatore della facciata. Se ne aveva già uno resta il più
    pesante, cioè quello col calo di oggi più alto, e a parità il più lungo. Chi è infortunato non ne
    prende. Con annota, la voce nel diario. Restituisce la frase da mostrare, oppure None se l'acciacco
    nuovo non conta.
    """
    giorni = rng.randint(ACCIACCO_GIORNI_MINIMO, ACCIACCO_GIORNI_MASSIMO)
    calo = rng.uniform(ACCIACCO_CALO_MINIMO, ACCIACCO_CALO_MASSIMO)
    if g.infortunato:
        return None
    oggi = mondo.datetime_corrente_simulazione
    fine = oggi + datetime.timedelta(days=giorni)
    attuale = calo_acciacco(g, oggi)
    if attuale > calo or (attuale == calo and g.acciacco_fino is not None and g.acciacco_fino >= fine):
        return None
    g.acciacco_fino = fine
    g.acciacco_calo = calo
    g.acciacco_giorni = giorni
    g.acciacco_sede = sede
    testo = testo_acciacco(g, sede, giorni)
    if annota:
        mondo.annota(g, testo)
    return _in_frase(g, testo)


def probabilita_in_seduta(g):
    """
    La probabilità, in percentuale, di infortunarsi nella seduta di un giorno: soltanto all'intensa,
    lo 0,3 per cento, che cresce dai 30 anni fino al triplo a 75; l'ambidestro ne ha un po' meno.
    """
    base = intensita_di(g)["infortuni_seduta"]
    if base <= 0.0:
        return 0.0
    risultato = base * (1.0 + AUMENTO_RISCHIO_SEDUTA * _quota_eta(g.eta_anni))
    if getattr(g, "ambidestro", False):
        risultato *= FATTORE_INFORTUNIO_AMBIDESTRO
    return risultato


def infortunio_in_seduta(mondo, g, data):
    """
    La seduta del giorno può infortunare chi si allena all'intensa: con un generatore nato dalla data
    e dal numero del giocatore, con la sede e la durata degli infortuni di partita. Restituisce la
    frase da mostrare, oppure None. Chi è già infortunato non si infortuna di nuovo. Dalla tappa 12
    l'infortunio cancella l'acciacco, come quelli in gara.
    """
    probabilita_del_giorno = probabilita_in_seduta(g)
    if g.infortunato or probabilita_del_giorno <= 0.0:
        return None
    rng = random.Random(f"seduta-{data.date().isoformat()}-{g.id}")
    if not rng.random() * 100.0 < probabilita_del_giorno:
        return None
    sede = estrai_sede(g, rng)
    fine = data + datetime.timedelta(days=durata(g, sede, rng))
    g.infortunato = True
    g.infortunio_fine_datetime = fine
    g.infortunio_sede = sede
    guarisci_acciacco(g)
    testo = testo_diario(g, sede, fine, in_allenamento=True)
    mondo.annota(g, testo, data)
    return _in_frase(g, testo)
