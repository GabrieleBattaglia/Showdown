"""
I percorsi di MESS: dove il programma scrive e dove trova le risorse che legge soltanto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, per il problema P10: il vecchio sd.py apriva
salvataggi e registri relativi alla cartella corrente, e lanciato da un'altra cartella non li
trovava. Segue lo schema del parco software: sta nella radice del progetto, chiama le utilità di
GBUtils senza parametri e ricalcola la cartella a ogni chiamata, mai una volta sola
all'importazione, così vale sia da sorgente sia da eseguibile compilato.
"""

import os

from GBUtils import cartella_applicazione, percorso_risorsa


def cartella():
    """La cartella in cui il programma scrive salvataggi e registri."""
    return cartella_applicazione()


def percorso(nome_file):
    """Il percorso di un file che il programma scrive, nella cartella del programma."""
    return os.path.join(cartella(), nome_file)


def risorsa(nome_file):
    """Il percorso di un file che il programma legge soltanto e che viaggia con lui, come le collezioni."""
    return percorso_risorsa(nome_file)
