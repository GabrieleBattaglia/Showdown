"""
Il dado del motore di partita di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9. Il motore non chiama mai il modulo random direttamente: tira
un Dado costruito su un generatore suo, così una partita si rigioca identica dal suo seme. Le
fasce sono sempre esaustive, e il residuo, cioè la posizione del tiro dentro la fascia uscita,
torna uniforme fra 0 e 1: il motore lo usa soltanto dove ha un senso di gioco, il tiro critico
dentro la fascia del fallo e la fermata sporca dentro quella della fermata.
Il DadoTruccato restituisce i tiri scritti in una prova, uno dopo l'altro, e quando finiscono
solleva ErroreMotore: serve a costruire scenari esatti, ramo per ramo.
"""

import math

from motore.eventi import ErroreMotore


class Dado:
    """I tiri del caso per il motore, su un generatore random.Random."""

    __slots__ = ("tiro",)

    def __init__(self, rng):
        # Il metodo del generatore legato una volta sola: è il tiro più frequente del motore.
        self.tiro = rng.random

    def fascia(self, probabilita):
        """
        Con un tiro solo, l'indice della fascia uscita e il residuo, di nuovo uniforme. Le
        probabilità si sommano a uno; l'ultima fascia prende comunque il resto, così nessun tiro
        resta fuori per un arrotondamento.
        """
        u = self.tiro()
        inizio = 0.0
        ultima = len(probabilita) - 1
        for indice in range(ultima):
            larghezza = probabilita[indice]
            fine = inizio + larghezza
            if u < fine:
                return indice, (u - inizio) / larghezza if larghezza > 0 else 0.0
            inizio = fine
        resto = 1.0 - inizio
        residuo = (u - inizio) / resto if resto > 0 else 0.0
        return ultima, min(max(residuo, 0.0), 0.9999999999)

    def pesata(self, tabella):
        """Un codice da una tabella di coppie, codice e peso, con un tiro solo."""
        totale = 0.0
        for _codice, peso in tabella:
            totale += peso
        soglia = self.tiro() * totale
        cumulata = 0.0
        for codice, peso in tabella:
            cumulata += peso
            if soglia < cumulata:
                return codice
        return tabella[-1][0]

    def si(self, p):
        """Vero con probabilità p."""
        return self.tiro() < p

    def intero(self, a, b):
        """Un intero fra a e b, estremi compresi."""
        return a + min(b - a, int(self.tiro() * (b - a + 1)))

    def softmax(self, utilita, temperatura):
        """L'indice scelto con probabilità proporzionali a exp(utilità / temperatura)."""
        massimo = max(utilita)
        pesi = [math.exp((u - massimo) / temperatura) for u in utilita]
        soglia = self.tiro() * sum(pesi)
        cumulata = 0.0
        for indice, peso in enumerate(pesi):
            cumulata += peso
            if soglia < cumulata:
                return indice
        return len(pesi) - 1


class DadoTruccato(Dado):
    """Un dado che restituisce i tiri scritti, nell'ordine; finiti quelli, solleva ErroreMotore."""

    __slots__ = ("_tiri", "usati")

    def __init__(self, tiri):
        self._tiri = list(tiri)
        self.usati = 0
        self.tiro = self._prossimo

    def _prossimo(self):
        if self.usati >= len(self._tiri):
            raise ErroreMotore(f"Il dado truccato ha finito i suoi {len(self._tiri)} tiri.")
        valore = self._tiri[self.usati]
        self.usati += 1
        return valore

    @property
    def rimasti(self):
        return len(self._tiri) - self.usati
