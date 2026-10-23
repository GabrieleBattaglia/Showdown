"""
MESS, utilità: compila l'installatore con Inno Setup.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-23 con la tappa 14, dal modello di MeTeOra, per la richiesta di Gabriele: il
pacchetto ha un installatore, che chiede di accettare la licenza. Compila MESS.iss col compilatore di
Inno Setup 6, passandogli la versione di version.py, e scrive MESS-Setup-<versione>.exe nella
cartella del progetto, accanto a MESS.zip. Si lancia dopo PyInstaller e zip_maker.py, con dist
ripulita (prontuario, fase 7.0 e 7.5). Il compilatore si cerca nella variabile MESS_ISCC, poi sulla
path, poi nelle cartelle dove Inno Setup si installa.
"""

import os
import shutil
import subprocess
import sys

from version import __version__

# La cartella del progetto, dove stanno MESS.iss e dist e dove nasce l'installatore, da qualunque
# cartella si lanci lo script.
RADICE = os.path.dirname(os.path.abspath(__file__))


def compilatore():
    """Il percorso di ISCC.exe, o None."""
    candidati = [os.environ.get("MESS_ISCC"), shutil.which("iscc")]
    if os.environ.get("LOCALAPPDATA"):
        candidati.append(os.path.join(os.environ["LOCALAPPDATA"], "Programs", "Inno Setup 6", "ISCC.exe"))
    for radice in (os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES")):
        if radice:
            candidati.append(os.path.join(radice, "Inno Setup 6", "ISCC.exe"))
    return next((c for c in candidati if c and os.path.isfile(c)), None)


def main():
    iscc = compilatore()
    if iscc is None:
        print("Installatore non creato: non trovo ISCC.exe di Inno Setup 6. Indica il percorso con la variabile MESS_ISCC.")
        return 1
    if not os.path.isfile(os.path.join(RADICE, "dist", "MESS", "MESS.exe")):
        print("Installatore non creato: manca dist\\MESS\\MESS.exe. Compila prima con PyInstaller.")
        return 1
    esito = subprocess.run([iscc, "/Q", f"/DVersione={__version__}", "MESS.iss"], cwd=RADICE, check=False)  # noqa: S603 - il compilatore trovato qui sopra
    if esito.returncode:
        print(f"Installatore non creato: ISCC ha finito con il codice {esito.returncode}.")
        return esito.returncode
    print(f"Installatore creato: MESS-Setup-{__version__}.exe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
