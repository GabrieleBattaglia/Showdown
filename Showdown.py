"""
MESS, Manageriale e Simulatore Showdown: il punto di avvio.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il porting in Python fino alla versione 25.4.24 è di Gabriele Battaglia con Gemini 2.5.
Data concepimento: 13/04/2015 16:13 by Gabriele Battaglia. Porting a Python dal 31/01/2020.
Dal 2026-10-06, con la tappa 2 del piano, il vecchio sd.py è diviso in moduli: qui si crea il
mondo, lo si carica, lo si fa avanzare col tempo trascorso e si apre l'interfaccia testuale.
"""

import sys
import traceback

import archivio
import nomi
from cli import InterfacciaTestuale
from mondo import Mondo


def avvia(dopo_creazione=None):
    """
    Crea il mondo, lo carica, lo fa avanzare e apre l'interfaccia testuale fino all'uscita.
    dopo_creazione, se data, riceve il mondo appena creato: serve ai collaudi.
    """
    mondo = Mondo(notifica=print)
    if dopo_creazione:
        dopo_creazione(mondo)
    nomi.collezioni()
    for avviso in nomi.avvisi:
        print(f"ATT: {avviso}")
    archivio.carica(mondo)
    mondo.processa_tempo_trascorso()
    InterfacciaTestuale(mondo).run()


def main():
    try:
        avvia()
    except Exception as errore:  # noqa: BLE001 - ultima rete del programma: mostra l'errore e chiude
        print("\n--- ERRORE FATALE ESECUZIONE ---")
        print(f"Tipo: {type(errore).__name__}")
        print(f"Msg: {errore}")
        traceback.print_exc()
        print("\nProgramma terminato.")
        sys.exit(1)


if __name__ == "__main__":
    main()
