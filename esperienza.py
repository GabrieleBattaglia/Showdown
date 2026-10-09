"""
L'esperienza di carriera dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11. L'esperienza va da 0 a 20, pesa il 30 per cento della classe
e cresce da più fonti, regola di Gabriele dell'8 ottobre 2026, dalla più piccola alla più grande:
un poco con l'età, perché chi guarda e vive lo showdown da tanto ne capisce di più, anche da
libero; le amichevoli; lo stare in una polisportiva, che fa crescere di più, con un piccolo fattore
in più dato dall'esperienza collettiva del gruppo; i tornei e le sfide, con un premio per i buoni
piazzamenti, che arriveranno con la tappa 12 ma che il modello prevede già. Chi nasce parte da
zero, risposta 8 di Gabriele: entra nel mondo quando comincia a giocare.
Fino alla tappa 10 l'esperienza cresceva soltanto in polisportiva, un decimo al mese.
"""

from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    ESPERIENZA_MASSIMA,
    ESPERIENZA_PER_AMICHEVOLE,
    ESPERIENZA_PER_ANNO_DI_VITA,
    ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA,
    ESPERIENZA_PER_PARTITA_TORNEO,
    ESPERIENZA_PER_PIAZZAMENTO,
    ESPERIENZA_PER_SFIDA,
    K_GRUPPO_ESPERIENZA,
)

AMICHEVOLE = "amichevole"
TORNEO = "torneo"
SFIDA = "sfida"
PER_PARTITA = {AMICHEVOLE: ESPERIENZA_PER_AMICHEVOLE, TORNEO: ESPERIENZA_PER_PARTITA_TORNEO, SFIDA: ESPERIENZA_PER_SFIDA}
# L'esperienza di un giorno d'età, la fonte più piccola.
_PER_GIORNO_DI_VITA = ESPERIENZA_PER_ANNO_DI_VITA / ANNO_SIMULAZIONE_GIORNI


def _aggiungi(g, quanto):
    g.esperienza = min(ESPERIENZA_MASSIMA, g.esperienza + quanto)


def fattore_gruppo(rosa):
    """Il fattore del gruppo di una polisportiva: 1 più K per l'esperienza media della rosa su 20; 1,05 con una media di 5."""
    if not rosa:
        return 1.0
    return 1.0 + K_GRUPPO_ESPERIENZA * sum(g.esperienza for g in rosa) / len(rosa) / ESPERIENZA_MASSIMA


def del_giorno(g, in_polisportiva, fattore=1.0):
    """L'esperienza di un giorno simulato: quella dell'età per tutti, e per chi è in polisportiva quella del club per il fattore del gruppo."""
    quanto = _PER_GIORNO_DI_VITA
    if in_polisportiva:
        quanto += ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * fattore
    _aggiungi(g, quanto)


def da_partita(g, tipo=AMICHEVOLE):
    """L'esperienza di un incontro registrato: amichevole, torneo o sfida."""
    _aggiungi(g, PER_PARTITA[tipo])


def da_piazzamento(g, posto):
    """Il premio d'esperienza di un piazzamento in un torneo, dal primo al quarto posto; niente per gli altri."""
    _aggiungi(g, ESPERIENZA_PER_PIAZZAMENTO.get(posto, 0.0))
