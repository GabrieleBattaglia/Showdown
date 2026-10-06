"""
Versione di MESS, Manageriale e Simulatore Showdown, in un punto solo.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il vecchio sd.py conta come serie 1: durante i lavori del piano di sviluppo la versione
avanza come 1.y.z, e la GUI completa uscirà come 2.0.0.
"""

__app_name__ = "MESS"
__version__ = "1.3.0"
__date__ = "2026-10-06"
__author__ = "Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto)"


def get_header():
    """Restituisce l'intestazione standard dell'applicazione."""
    return f"{__app_name__}, Manageriale e Simulatore Showdown, versione {__version__} del {__date__}, di {__author__}"
