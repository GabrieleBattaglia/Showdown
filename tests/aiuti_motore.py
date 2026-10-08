"""
Strumenti comuni alle prove del motore di partita della tappa 9: giocatori costruiti a mano, una
taratura senza effetti di carattere e d'esperienza, e un dado scritto che guida la catena degli
esiti ramo per ramo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import dataclasses
import datetime
import random

from costanti import ATTRIBUTI_ALLENABILI, ATTRIBUTI_BASE_CON_ALLENABILI, CARATTERISTICHE_FISICHE_BASE, giorni_da_anni
from modelli import Giocatore
from motore.dado import DadoTruccato
from motore.eventi import ErroreMotore
from motore.taratura import TARATURA

NASCITA = datetime.datetime(2026, 1, 1)
# Una taratura in cui la paura degli errori vale sempre 1: temperamento, esperienza, stanchezza e
# qualità non piegano più le probabilità dei falli, così le prove le conoscono.
TARATURA_NEUTRA = dataclasses.replace(TARATURA, K_TEMP_FALLI=0.0, K_ESP_FALLI=0.0, K_FATICA_FALLI=0.0, K_SKILL_FALLI=0.0)


def giocatore(gid, valore=12.0, fisico=3.0, anni=30, sesso="m", **altro):
    """
    Un giocatore costruito a mano, con tutte le caratteristiche di gioco al valore indicato e le
    fisiche a fisico, senza tratti speciali, con il temperamento a 50 e l'esperienza a zero. Gli
    altri argomenti sovrascrivono gli attributi, per esempio mancino=True o chiusurasx_base=2.
    """
    stato = random.getstate()
    random.seed(gid)
    try:
        g = Giocatore(gid, NASCITA)
    finally:
        random.setstate(stato)
    for nome in ATTRIBUTI_BASE_CON_ALLENABILI:
        setattr(g, nome, fisico if nome in CARATTERISTICHE_FISICHE_BASE else valore)
    for nome in ATTRIBUTI_ALLENABILI:
        setattr(g, nome, 0.0)
    g.mancino = g.ambidestro = g.giocorapido = g.cambiovelocita = g.ipovedente = False
    g.infortunato = False
    g.infortunio_sede = None
    g.ritirato = False
    g.sesso = sesso
    g.eta = giorni_da_anni(anni)
    g.temperamento = 50.0 + 0.25 * max(0.0, anni - 25.0)
    g.esperienza = 0.0
    for nome, valore_altro in altro.items():
        setattr(g, nome, valore_altro)
    g.aggiorna_icv()
    return g


class DadoScritto(DadoTruccato):
    """
    Un dado per guidare la catena: ogni voce del copione è un numero, per un tiro, oppure una
    coppia di fascia e residuo, per una chiamata di fascia; le pesate e gli interi tirano un
    numero. Una voce del tipo sbagliato è ErroreMotore, così il copione si legge nell'ordine giusto.
    """

    __slots__ = ()

    def __init__(self, copione):
        super().__init__(copione)
        self.tiro = self._tiro

    def _tiro(self):
        voce = self._prossimo()
        if isinstance(voce, tuple):
            raise ErroreMotore(f"Il copione aspettava un tiro, trova la fascia {voce!r}.")
        return voce

    def fascia(self, probabilita):
        voce = self._prossimo()
        if not isinstance(voce, tuple):
            raise ErroreMotore(f"Il copione aspettava una fascia, trova {voce!r}.")
        indice, residuo = voce
        if not 0 <= indice < len(probabilita) or probabilita[indice] <= 0:
            raise ErroreMotore(f"Fascia {indice} impossibile con le probabilità {probabilita}.")
        return indice, residuo
