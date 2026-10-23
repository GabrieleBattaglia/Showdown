# MESS, la ricetta di PyInstaller: il pacchetto a cartella (prontuario, premessa).
# Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
# 23/10/2026: nasce con la tappa 14, decisione D34, sul modello di MeTeOra.spec.
#
# Si compila dalla cartella del progetto con: python -m PyInstaller --noconfirm MESS.spec
# Dentro il pacchetto vanno le sole cose che MESS legge: la cartella dati, con nomi, vocabolario,
# comuni e modelli dei tornei; il manuale; le novità; la collezione dei suoni di GBUtils, che
# Acusticator cerca accanto a GBUtils.py e il codice non nomina mai (prontuario 2.2); le librerie di
# accessible_output2. La licenza va accanto all'eseguibile, dove chi riceve il pacchetto la trova.
# Analysis, PYZ, EXE, COLLECT, SPECPATH e DISTPATH li definisce PyInstaller quando esegue la ricetta:
# per ruff, che la controlla con ruff check --extension spec:python MESS.spec, sono nomi sconosciuti.
# ruff: noqa: F821

import os
import shutil

import GBUtils
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = [
    ("dati", "dati"),
    ("manuale.html", "."),
    ("CHANGELOG.md", "."),
    (os.path.join(os.path.dirname(GBUtils.__file__), "Acu_Collection.json"), "."),
]
# Le DLL dei lettori di schermo, che accessible_output2 cerca nella sua cartella lib.
datas += collect_data_files("accessible_output2", include_py_files=False)

# Fuori dal pacchetto, come in MeTeOra: le DLL proprietarie di accessible_output2, di PC-Talker, ZDSR,
# Dolphin e System Access, che non danno il permesso di ridistribuirle, e quella a 32 bit di NVDA;
# le varianti di PortAudio che sounddevice non carica mai su Windows a 64 bit.
FUORI = {
    "pctkusr.dll", "pctkusr64.dll", "zdsrapi.dll", "zdsrapi_x64.dll", "dolapi.dll", "saapi32.dll", "nvdacontrollerclient32.dll",
    "libportaudio.dylib", "libportaudio32bit.dll", "libportaudio32bit-asio.dll", "libportaudio64bit-asio.dll", "libportaudioarm64.dll",
    "libportaudioarm64-asio.dll",
}


def _dentro(voce):
    return os.path.basename(voce[0]).lower() not in FUORI


datas = [voce for voce in datas if _dentro(voce)]
# Le uscite della sintesi si aprono per nome, in GBsintesi di GBUtils, con importlib.
hiddenimports = collect_submodules("accessible_output2.outputs")

a = Analysis(
    ["Showdown.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pandas", "PyQt5", "PyQt6", "PySide2", "PySide6", "IPython", "jedi", "notebook", "pytest",
              "psutil", "chardet", "cryptography", "setuptools", "tomli", "PIL"],
    noarchive=False,
    optimize=0,
)
a.binaries = [voce for voce in a.binaries if _dentro(voce)]
a.datas = [voce for voce in a.datas if _dentro(voce)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MESS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="MESS",
)

# Accanto all'eseguibile, dove chi riceve il pacchetto la trova; presa accanto alla ricetta, da
# qualunque cartella si lanci PyInstaller.
shutil.copyfile(os.path.join(SPECPATH, "LICENSE"), os.path.join(DISTPATH, "MESS", "LICENSE"))
