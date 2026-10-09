"""
Le popolazioni di prova di MESS, per il banco delle partite e per la taratura del valore.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9. Una popolazione di prova è fatta dai nati del generatore vero,
la classe Giocatore di modelli.py, con un seme; una parte di loro riceve un allenamento sintetico,
distribuito a caso fra le caratteristiche entro le bande dell'allenata, e tutti un'esperienza di
carriera estratta a caso, perché nel mondo vero l'esperienza cresce piano, e le misure sulla
lettura del gioco e sui falli non si vedrebbero. Il caso del mondo si rimette com'era alla fine,
così chi usa una popolazione non si accorge di averla creata.
Dalla tappa 11, il 2026-10-09, l'allenata del gioco non ha più tetti suoi, risposta 6 di Gabriele;
la popolazione tiene le bande di prima, 5 per le fisiche e 20 per le altre, come costanti sue e non
del gioco: la regressione del valore resta sulla stessa popolazione della versione 1.50.0, e non si
sposta verso valori che il mondo vero non vedrà per decenni. In più ognuno riceve una costanza
recente uniforme fra 0 e 2, da un generatore a parte, così il resto della popolazione non cambia.
"""

import datetime
import random
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

from costanti import ATTRIBUTI_ALLENABILI, COSTANZA_PIENA  # noqa: E402
from modelli import Giocatore, e_fisica  # noqa: E402

NASCITA = datetime.datetime(2026, 1, 1)  # noqa: DTZ001 - data segnaposto, come tutte quelle del motore
# Le bande dell'allenata della popolazione di prova: gli stessi numeri dei vecchi tetti dell'allenata,
# 5 per precisione, resistenza e forza e 20 per le altre, che nel gioco non ci sono più.
BANDA_ALLENATA_FISICA = 5.0
BANDA_ALLENATA_GIOCO = 20.0


def allena(g, punti, rng):
    """Distribuisce i punti fra le caratteristiche allenabili con pesi a caso, entro le bande dell'allenata e il tetto del totale."""
    pesi = [rng.random() ** 2 for _ in ATTRIBUTI_ALLENABILI]
    totale = sum(pesi) or 1.0
    for nome, peso in zip(ATTRIBUTI_ALLENABILI, pesi, strict=True):
        banda = BANDA_ALLENATA_FISICA if e_fisica(nome) else BANDA_ALLENATA_GIOCO
        quota = punti * peso / totale
        if e_fisica(nome):
            # Un punto fisico vale un decimo della scala, contro un quarantesimo di quelli di gioco.
            quota /= 4.0
        setattr(g, nome, min(banda, getattr(g, nome) + quota))
    g._rispetta_tetti()


def genera(quanti, seme, quota_allenati=0.6, punti=(0, 220), esperienza=(0, 12), primo_id=1):
    """
    Una popolazione di prova: quanti giocatori nati col seme indicato, una quota allenata con un
    numero di punti estratto nell'intervallo, l'esperienza di carriera estratta nell'altro, e la
    costanza recente fra 0 e la costanza piena, da un generatore suo.
    """
    stato = random.getstate()
    random.seed(seme)
    try:
        giocatori = [Giocatore(primo_id + i, NASCITA) for i in range(quanti)]
    finally:
        random.setstate(stato)
    rng = random.Random(f"popolazione-{seme}")
    rng_costanza = random.Random(f"popolazione-costanza-{seme}")
    for g in giocatori:
        if rng.random() < quota_allenati:
            allena(g, rng.uniform(*punti), rng)
        g.esperienza = round(rng.uniform(*esperienza), 2)
        g.costanza = rng_costanza.uniform(0.0, COSTANZA_PIENA)
        g.aggiorna_icv()
    return giocatori
