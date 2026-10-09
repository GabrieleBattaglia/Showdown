"""
L'economia di MESS: i conti di giocatori e polisportive.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 8 del piano, secondo la decisione D22, sul modello di Hattrick.
Qui stanno i calcoli, che non cambiano niente: lo stipendio che un giocatore chiede, secondo
valore, tratti rari ed esperienza; il premio d'ingaggio che chiede a una polisportiva, secondo la
reputazione di lei; il suo valore di mercato; lo sponsor di una polisportiva, secondo la gloria;
la pazienza di chi non viene pagato, che dura secondo la fedeltà, e l'umore che ne viene fuori.
Le operazioni che muovono i soldi sono regole del mondo, e stanno in mondo.py.
Dalla tappa 11, il 2026-10-09, decisione D31, c'è il contratto: lo stipendio che il giocatore
chiede resta la formula di prima, ma quello che una polisportiva paga è fisso fino alla scadenza,
quindi chi migliora allenandosi non costa di più finché il contratto dura; il valore di mercato
scende negli ultimi tre mesi di contratto, fino al 40 per cento alla scadenza, per chi non ha
rinnovato.
"""

import math

import contratti
from costanti import (
    AUMENTO_STIPENDIO_PER_ESPERIENZA,
    FATTORE_GLORIA_RICHIESTA_AMBIDESTRO,
    FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL,
    FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO,
    FEDELTA_BANDIERA,
    FEDELTA_PER_MESE_DI_PAZIENZA,
    MESI_DI_INGAGGIO,
    MESI_DI_VALORE,
    MESI_VALORE_PIENO,
    REPUTAZIONE_MASSIMA,
    REPUTAZIONE_MINIMA,
    SCALA_STIPENDIO,
    SPONSOR_PER_GLORIA,
    STIPENDIO_DI_RIFERIMENTO,
    STIPENDIO_MINIMO,
    VALORE_A_SCADENZA,
    VALORE_DI_RIFERIMENTO,
)


def arrotonda(euro, passo=10):
    """Una cifra in euro arrotondata a un passo, per default alla decina."""
    return round(euro / passo) * passo


def scritta_in_euro(importo):
    """Una cifra in euro a parole, con il punto delle migliaia: 2.400 euro."""
    return f"{int(importo):,} euro".replace(",", ".")


def stipendio(g):
    """
    Lo stipendio mensile che il giocatore chiede, in euro. Come in Hattrick lo decide lui, non si
    contratta: cresce di un fattore e ogni SCALA_STIPENDIO punti di valore, sale per i tratti rari,
    ambidestro, gioco rapido e cambio di velocità, e per l'esperienza di carriera.
    """
    euro = STIPENDIO_DI_RIFERIMENTO * math.exp((g.indice_collettivo_valore - VALORE_DI_RIFERIMENTO) / SCALA_STIPENDIO)
    if g.ambidestro:
        euro *= FATTORE_GLORIA_RICHIESTA_AMBIDESTRO
    if g.giocorapido:
        euro *= FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO
    if g.cambiovelocita:
        euro *= FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL
    euro *= 1 + AUMENTO_STIPENDIO_PER_ESPERIENZA * g.esperienza
    return max(STIPENDIO_MINIMO, arrotonda(euro))


def stipendio_pagato(g):
    """
    Lo stipendio che la polisportiva paga ogni mese: quello del contratto, fisso fino alla scadenza,
    oppure, per chi non ha contratto, quello che chiede oggi.
    """
    return g.contratto_stipendio if getattr(g, "contratto_stipendio", 0) > 0 else stipendio(g)


def fattore_reputazione(g, poli):
    """
    Quanto la reputazione della polisportiva sposta l'ingaggio chiesto: sotto uno con una
    polisportiva più gloriosa di quanto il giocatore pretende, sopra uno con una meno gloriosa.
    """
    rapporto = g.gloria_richiesta / max(1, poli.gloria)
    return min(REPUTAZIONE_MASSIMA, max(REPUTAZIONE_MINIMA, math.sqrt(rapporto)))


def ingaggio_richiesto(g, poli):
    """Il premio d'ingaggio, una tantum, che il giocatore chiede alla polisportiva per firmare."""
    return arrotonda(stipendio(g) * MESI_DI_INGAGGIO * fattore_reputazione(g, poli))


def valore_di_mercato_pieno(g):
    """Quanto vale il giocatore sul mercato a contratto lungo: lo stipendio che chiede per sei mesi, arrotondato al centinaio."""
    return arrotonda(stipendio(g) * MESI_DI_VALORE, 100)


def fattore_scadenza(g, oggi=None):
    """
    Quanto scende il valore di mercato verso la scadenza: 1 per i liberi, per chi ha già un rinnovo
    concordato e per chi ha almeno tre mesi di contratto; sotto, in linea retta fino al 40 per cento
    alla scadenza. Senza la data di oggi, 1.
    """
    if oggi is None or not contratti.ha_contratto(g) or contratti.ha_rinnovo(g):
        return 1.0
    mesi = contratti.mesi_al_termine(g, oggi)
    if mesi >= MESI_VALORE_PIENO:
        return 1.0
    return VALORE_A_SCADENZA + (1.0 - VALORE_A_SCADENZA) * mesi / MESI_VALORE_PIENO


def valore_di_mercato(g, oggi=None):
    """
    Quanto vale il giocatore sul mercato delle vendite, il giorno dato: il prezzo di partenza, e il
    metro del computer. È il valore pieno per il fattore della scadenza, arrotondato al centinaio.
    """
    pieno = valore_di_mercato_pieno(g)
    fattore = fattore_scadenza(g, oggi)
    return pieno if fattore >= 1.0 else arrotonda(pieno * fattore, 100)


def sponsor_mensile(poli):
    """Quanto lo sponsor paga ogni mese alla polisportiva, in proporzione alla sua gloria."""
    return arrotonda(poli.gloria * SPONSOR_PER_GLORIA)


def mesi_di_pazienza(g):
    """Per quanti mesi senza stipendio il giocatore aspetta, secondo la fedeltà: da uno a cinque."""
    return 1 + g.fedelta / FEDELTA_PER_MESE_DI_PAZIENZA


def bandiera_attiva(g):
    """Vero per una bandiera che ha già dato abbastanza al suo club: gioca anche senza stipendio."""
    return g.bandiera and g.fedelta >= FEDELTA_BANDIERA


def pazienza_per_euro(g):
    """Quanta pazienza rende o toglie un euro di stipendio: un mese intero vale un mese di pazienza."""
    return 100 / mesi_di_pazienza(g) / max(1, stipendio(g))


def mesi_rimasti(g):
    """Per quanti mesi ancora il giocatore aspetterebbe senza stipendio, con la pazienza di adesso."""
    return g.pazienza / (100 / mesi_di_pazienza(g))
