"""
I percorsi di MESS: dove il programma scrive e dove trova le risorse che legge soltanto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 2 del piano, per il problema P10: il vecchio sd.py apriva
salvataggi e registri relativi alla cartella corrente, e lanciato da un'altra cartella non li
trovava. Segue lo schema del parco software: sta nella radice del progetto, chiama le utilità di
GBUtils senza parametri e ricalcola la cartella a ogni chiamata, mai una volta sola
all'importazione, così vale sia da sorgente sia da eseguibile compilato.
Dal 2026-10-23, richiesta di Gabriele per portare il mondo fra le macchine con una penna o con un
cloud come Dropbox, le cartelle sono due. La cartella del mondo, cartella(), tiene tutto quello che
riguarda il mondo, lo stato di gioco e le impostazioni: di serie è la sottocartella Mondo della
cartella del programma, e si sceglie dal menu Impostazioni. Dove sta lo dice un file accanto al
programma, uno per macchina, FILE_DELLA_CARTELLA, che si rilegge a ogni chiamata come il resto: senza
il file vale la cartella predefinita; un file che c'è ma non si legge solleva CartellaIllegibile,
un OSError, così chi scrive fallisce col suo messaggio invece di scrivere altrove. La cartella del
programma, cartella_del_programma(), tiene soltanto quel file e i registri degli errori e dei crash.
Le parti del 23 ottobre sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import contextlib
import json
import os

from GBUtils import cartella_applicazione, percorso_risorsa

# Il file accanto al programma che dice dove sta la cartella del mondo, e la cartella di serie.
FILE_DELLA_CARTELLA = "mess_cartella_del_mondo.json"
CARTELLA_PREDEFINITA = "Mondo"


class CartellaIllegibile(OSError):
    """Il file che dice dove sta la cartella del mondo c'è, ma non si legge o non dice una cartella."""


def cartella_del_programma():
    """La cartella del programma: accanto all'eseguibile compilato, o la radice dei sorgenti."""
    return cartella_applicazione()


def nel_programma(nome_file):
    """Il percorso di un file accanto al programma, come i registri e il file della cartella del mondo."""
    return os.path.join(cartella_del_programma(), nome_file)


def file_della_cartella():
    """Il file, accanto al programma, che dice dove sta la cartella del mondo."""
    return nel_programma(FILE_DELLA_CARTELLA)


def cartella_predefinita():
    """La cartella del mondo di serie: Mondo, dentro la cartella del programma."""
    return nel_programma(CARTELLA_PREDEFINITA)


def normale(cartella):
    """Una cartella in forma confrontabile: assoluta, senza punti e barre di troppo, con le maiuscole come le vede Windows."""
    return os.path.normcase(os.path.normpath(os.path.abspath(cartella)))


def stessa(prima, seconda):
    """Vero se le due cartelle sono la stessa."""
    return normale(prima) == normale(seconda)


def dentro(cartella, contenitore):
    """Vero se cartella è contenitore o sta dentro di lei, a qualunque profondità."""
    a, b = normale(cartella), normale(contenitore)
    try:
        return os.path.commonpath([a, b]) == b
    except ValueError:
        # Due dischi diversi.
        return False


def cartella_scelta():
    """
    La cartella del mondo scritta nel file accanto al programma, assoluta; None se il file non c'è, e
    allora vale la predefinita. CartellaIllegibile se il file c'è ma non si legge o non dice una cartella.
    """
    nome = file_della_cartella()
    try:
        with open(nome, encoding="utf-8") as f:
            dati = json.load(f)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        raise CartellaIllegibile(f"il file {FILE_DELLA_CARTELLA}, accanto al programma, non si legge: {e}") from e
    scelta = dati.get("cartella") if isinstance(dati, dict) else None
    if not isinstance(scelta, str) or not scelta.strip():
        raise CartellaIllegibile(f"il file {FILE_DELLA_CARTELLA}, accanto al programma, non dice quale sia la cartella del mondo")
    # Una cartella relativa, come quelle dentro la cartella del programma, parte da lì.
    return os.path.normpath(os.path.join(cartella_del_programma(), scelta))


def cartella():
    """La cartella del mondo, in cui il programma scrive il mondo, le impostazioni, i tornei e le cronache."""
    return cartella_scelta() or cartella_predefinita()


def percorso(nome_file):
    """Il percorso di un file che il programma scrive, nella cartella del mondo."""
    return os.path.join(cartella(), nome_file)


def imposta_cartella(nuova):
    """
    Scrive nel file accanto al programma che la cartella del mondo è nuova, con la scrittura sicura di
    un file temporaneo; la predefinita toglie il file. Una cartella dentro quella del programma si
    scrive relativa, così il programma si può spostare con lei. OSError se il file non si scrive.
    """
    nome = file_della_cartella()
    if stessa(nuova, cartella_predefinita()):
        with contextlib.suppress(FileNotFoundError):
            os.remove(nome)
        return
    programma = cartella_del_programma()
    scritta = os.path.relpath(nuova, programma) if dentro(nuova, programma) else os.path.abspath(nuova)
    temporaneo = nome + ".tmp"
    try:
        with open(temporaneo, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"cartella": scritta}, f, ensure_ascii=False, indent=1)
        os.replace(temporaneo, nome)
    finally:
        with contextlib.suppress(OSError):
            os.remove(temporaneo)


def risorsa(nome_file):
    """Il percorso di un file che il programma legge soltanto e che viaggia con lui, come le collezioni."""
    return percorso_risorsa(nome_file)
