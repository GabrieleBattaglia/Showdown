"""
Il motore di partita di MESS, nato con la tappa 9 del piano di sviluppo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07, secondo le regole IBSA decise con Gabriele nella decisione D25, al posto del
vecchio motore di partita.py, che è rimasto la facciata verso il mondo. Tre strati che non si
mescolano: la catena degli esiti, in scambio.py, decide che cosa succede; la regia, in regia.py,
trasforma gli esiti in eventi con tempo, posizione, lato e distanza, senza cambiarne nessuno; la
cronaca, in cronaca.py, compone l'italiano dagli eventi. Sopra a tutto l'incontro, in incontro.py,
fa l'arbitro. Il motore riceve oggetti Giocatore e restituisce eventi, esiti e statistiche: non
stampa, non chiede nulla e non scrive nel mondo, cosa che fa soltanto la facciata.
"""

from motore.eventi import ErroreMotore, Evento
from motore.incontro import (
    COMPLETO,
    ESSENZIALE,
    SINGOLARE_3,
    SINGOLARE_5,
    SQUADRE,
    Formato,
    Incontro,
    RisultatoIncontro,
    formato_singolare,
    simula_incontro,
)
from motore.scambio import EsitoPunto
from motore.squadre import Squadra
from motore.taratura import TARATURA, Taratura

__all__ = ("COMPLETO", "ESSENZIALE", "SINGOLARE_3", "SINGOLARE_5", "SQUADRE", "TARATURA", "ErroreMotore", "EsitoPunto", "Evento", "Formato", "Incontro",
           "RisultatoIncontro", "Squadra", "Taratura", "formato_singolare", "simula_incontro")
