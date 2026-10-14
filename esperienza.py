"""
L'esperienza di carriera dei giocatori di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11. L'esperienza va da 0 a 20, pesa il 30 per cento della classe
e cresce da più fonti, regola di Gabriele dell'8 ottobre 2026, dalla più piccola alla più grande:
un poco con l'età, perché chi guarda e vive lo showdown da tanto ne capisce di più, anche da
libero; le amichevoli; lo stare in una polisportiva, che fa crescere di più, con un piccolo fattore
in più dato dall'esperienza collettiva del gruppo; i tornei e le sfide. Chi nasce parte da zero,
risposta 8 di Gabriele: entra nel mondo quando comincia a giocare.
Fino alla tappa 10 l'esperienza cresceva soltanto in polisportiva, un decimo al mese.
Dalla tappa 12, il 2026-10-13, decisione D32 e punto 10.3 del progetto, l'ordine delle fonti è età,
amichevoli, sfide, club e tornei, sempre 20 a 50 anni per la carriera perfetta. Ogni incontro ha la
sua esperienza per l'importanza del torneo; dai tornei vengono anche le fasi superate e un premio di
piazzamento a scalare per i primi dodici, regola di Gabriele, sempre per l'importanza; nessuna quota
per la sola partecipazione, risposta 9. Le riserve di una sfida prendono metà dell'esperienza dei
titolari, risposta 15.
"""

from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    ESPERIENZA_MASSIMA,
    ESPERIENZA_PER_AMICHEVOLE,
    ESPERIENZA_PER_ANNO_DI_VITA,
    ESPERIENZA_PER_FASE_SUPERATA,
    ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA,
    ESPERIENZA_PER_PARTITA_TORNEO,
    ESPERIENZA_PER_SFIDA,
    ESPERIENZA_PIAZZAMENTO_BASE,
    ESPERIENZA_RISERVA_QUOTA,
    K_GRUPPO_ESPERIENZA,
    SCALA_PIAZZAMENTI,
)

AMICHEVOLE = "amichevole"
TORNEO = "torneo"
SFIDA = "sfida"
TIPI = (AMICHEVOLE, TORNEO, SFIDA)
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


def quanto_del_giorno(in_polisportiva, fattore=1.0):
    """
    Quanta esperienza dà un giorno simulato: quella dell'età per tutti, e per chi è in polisportiva quella
    del club per il fattore del gruppo. Dalla tappa 12, decisione 4 di Gabriele del 14 ottobre 2026, il
    mondo la calcola una volta per polisportiva al giorno, invece che per ogni giocatore.
    """
    quanto = _PER_GIORNO_DI_VITA
    if in_polisportiva:
        quanto += ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * fattore
    return quanto


def del_giorno(g, in_polisportiva, fattore=1.0):
    """L'esperienza di un giorno simulato, quella di quanto_del_giorno, fino al massimo."""
    _aggiungi(g, quanto_del_giorno(in_polisportiva, fattore))


def da_partita(g, tipo=AMICHEVOLE, importanza=1.0):
    """L'esperienza di un incontro registrato, amichevole, torneo o sfida, per l'importanza del torneo, 1 se non c'è."""
    _aggiungi(g, PER_PARTITA[tipo] * importanza)


def da_riserva(g, importanza=1.0):
    """L'esperienza di una riserva convocata in una sfida o nella coppa: metà di quella dei titolari, risposta 15 di Gabriele."""
    _aggiungi(g, ESPERIENZA_RISERVA_QUOTA * ESPERIENZA_PER_SFIDA * importanza)


def da_fasi(g, fasi, importanza=1.0):
    """L'esperienza delle fasi superate in un torneo: un girone passato o un turno di tabellone vinto, anche col riposo, per l'importanza."""
    _aggiungi(g, ESPERIENZA_PER_FASE_SUPERATA * max(0, fasi) * importanza)


def premio_piazzamento(posto):
    """Il premio di piazzamento, senza l'importanza: a scalare per i primi dodici, niente dal tredicesimo in giù."""
    if not 1 <= posto <= len(SCALA_PIAZZAMENTI):
        return 0.0
    return ESPERIENZA_PIAZZAMENTO_BASE * SCALA_PIAZZAMENTI[posto - 1]


def da_piazzamento(g, posto, importanza=1.0):
    """Il premio d'esperienza di un piazzamento in un torneo, dal primo al dodicesimo posto, per l'importanza; niente per gli altri."""
    _aggiungi(g, premio_piazzamento(posto) * importanza)
