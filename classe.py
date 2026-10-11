"""
La classe dei giocatori di MESS, da K0 ad A1.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11, decisione D31 e scelte di Gabriele dell'8 ottobre 2026. La
scala ha cento livelli, da A1, il più forte, a K0, il livello 100, il più debole: il codice è il
numero del livello con una lettera al posto delle decine, A per lo zero fino a K per il dieci.
La classe riunisce le caratteristiche, con il valore pesato, al 70 per cento, e l'esperienza al
30: il punteggio vale 0 per il minimo di tutto e 1 per la carriera perfetta a 50 anni, e chi la
supera resta A1. Il valore pesato è calcolato direttamente con i pesi della classe, copia
congelata di quelli del valore: non dipende dalla scala A e B, e una nuova taratura del valore
non sposta la classe di nessuno. Le soglie, fissate una volta per sempre, si interpolano in linea
retta fra le ancore di costanti.py, più fitte dove stanno i giocatori veri: i nati fra le classi I
e F, i bravi a metà carriera fra E e D, le classi più alte per le carriere eccellenti. Dalla
revisione della tappa 11 i livelli si allargano dal basso verso l'alto in tre tratti: fra I9 e F0,
fra F0 e D0, fra D0 e A1.
La classe non si salva: si ricava.
"""

import bisect
import itertools
import math
from collections import namedtuple

import valore
from costanti import (
    ANCORE_CLASSE,
    ESPERIENZA_MASSIMA,
    PESI_CLASSE,
    PESI_TRATTI_CLASSE,
    PESO_ESPERIENZA_CLASSE,
    PESO_VALORE_CLASSE,
    SOMMA_CARRIERA_PERFETTA,
)

LIVELLI = 100
LETTERE = "ABCDEFGHIJK"
# La classe di un giocatore: il codice, come G4; il livello, da 1 a 100; la percentuale verso la classe seguente, None per A1.
Classe = namedtuple("Classe", "codice livello percentuale")


def _soglie(ancore):
    """Le soglie dei livelli da 1 a 100, in un elenco che parte dal livello 1: interpolate in linea retta fra le ancore."""
    ordinate = sorted(ancore)
    soglie = []
    for n in range(1, LIVELLI + 1):
        for (n1, p1), (n2, p2) in itertools.pairwise(ordinate):
            if n1 <= n <= n2:
                # Sulle ancore il punteggio è esattamente il loro, senza gli scarti della divisione.
                soglie.append(p1 if n == n1 else p2 if n == n2 else p1 + (p2 - p1) * (n - n1) / (n2 - n1))
                break
    return tuple(soglie)


SOGLIE_CLASSE = _soglie(ANCORE_CLASSE)
# Le soglie cambiate di segno, in ordine crescente, per trovare il livello con una ricerca binaria.
_SOGLIE_CRESCENTI = tuple(-s for s in SOGLIE_CLASSE)


def somma_classe(g):
    """Il valore pesato della classe: la somma pesata dei totali più i tratti, con i pesi congelati della classe."""
    return valore.somma_pesata(g, pesi=PESI_CLASSE) + valore.bonus_tratti(g, PESI_TRATTI_CLASSE)


def punteggio(g):
    """Il punteggio della classe: 0,7 per il valore pesato sulla carriera perfetta, più 0,3 per l'esperienza su 20."""
    esperienza = min(1.0, max(0.0, g.esperienza) / ESPERIENZA_MASSIMA)
    return PESO_VALORE_CLASSE * somma_classe(g) / SOMMA_CARRIERA_PERFETTA + PESO_ESPERIENZA_CLASSE * esperienza


def soglia(n):
    """Il punteggio minimo del livello n: 0 per il 100, K0, e 1 per l'1, A1."""
    return SOGLIE_CLASSE[n - 1]


def livello(valore_del_punteggio):
    """Il livello di un punteggio: il più piccolo n con il punteggio almeno pari alla sua soglia. 0 è K0, 1 o più è A1."""
    return min(LIVELLI, bisect.bisect_left(_SOGLIE_CRESCENTI, -valore_del_punteggio) + 1)


def codice(n):
    """Il codice del livello: la lettera delle decine e le unità. 1 è A1, 10 è B0, 99 è J9, 100 è K0."""
    decine, unita = divmod(n, 10)
    return f"{LETTERE[decine]}{unita}"


def percentuale_verso_la_seguente(g, valore_del_punteggio=None):
    """Quanto manca alla classe di sopra, in percentuale troncata del tratto fra le due soglie; None per A1."""
    p = punteggio(g) if valore_del_punteggio is None else valore_del_punteggio
    n = livello(p)
    if n == 1:
        return None
    basso, alto = soglia(n), soglia(n - 1)
    # Un millesimo di milionesimo in più, perché la metà esatta del tratto non diventi 49 per uno scarto di calcolo.
    return max(0, min(99, math.floor((p - basso) / (alto - basso) * 100 + 1e-9)))


def classe(g):
    """La classe del giocatore: Classe con codice, livello e percentuale verso la seguente."""
    p = punteggio(g)
    n = livello(p)
    return Classe(codice(n), n, percentuale_verso_la_seguente(g, p))
