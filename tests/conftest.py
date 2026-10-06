"""
Mette la radice del progetto nel percorso di importazione, così i test trovano i moduli di MESS,
dirotta in una cartella temporanea tutto ciò che il programma scrive, e fa nascere le finestre
delle prove su un desktop di Windows nascosto.
Il desktop nascosto viene da tests/conftest.py di Tornello, dalla 10.13.37. Windows dà il primo
piano anche a una finestra mai mostrata quando riceve il fuoco, se il processo è partito dal
terminale che aveva il primo piano: il 26 settembre 2026 finestre invisibili delle prove di
Tornello hanno preso il primo piano sullo schermo di Gabriele, e NVDA gli leggeva i loro titoli.
Perciò, prima che wx crei qualunque finestra, il thread principale passa su un desktop tutto suo,
che nessuno vede. Se il passaggio non riesce la suite non parte: meglio nessuna prova che
finestre sul desktop vero. Fuori da Windows non serve.
"""

import os
import sys
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

NOME_DEL_DESKTOP = f"mess_prove_{os.getpid()}"
GENERIC_ALL = 0x10000000
# La maniglia del desktop nascosto resta aperta finché il processo vive: chiusa, il desktop
# sparirebbe sotto le finestre delle prove.
DESKTOP_DELLE_PROVE = {}


def _user32():
    """user32 con le firme delle funzioni dei desktop, in una copia tutta sua."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.CreateDesktopW.restype = wintypes.HANDLE
    user32.CreateDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    user32.SetThreadDesktop.restype = wintypes.BOOL
    user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
    user32.CloseDesktop.restype = wintypes.BOOL
    user32.CloseDesktop.argtypes = [wintypes.HANDLE]
    return user32


def _non_disponibile(azione, funzione, codice):
    import ctypes

    return (f"Le prove non partono: non si è potuto {azione} ({funzione}, errore di Windows {codice}: {ctypes.FormatError(codice).strip()}). "
            "Le finestre delle prove nascono su un desktop di Windows nascosto: senza, una finestra mai mostrata che riceve il fuoco "
            "prenderebbe il primo piano sullo schermo di chi lancia le prove. Il passaggio fallisce se questo thread ha già delle finestre.")


def pytest_configure(config):
    """Il passaggio al desktop nascosto, una volta per processo, prima che le prove creino wx.App."""
    if sys.platform != "win32" or DESKTOP_DELLE_PROVE:
        return
    import ctypes

    user32 = _user32()
    desktop = user32.CreateDesktopW(NOME_DEL_DESKTOP, None, None, 0, GENERIC_ALL, None)
    if not desktop:
        raise pytest.UsageError(_non_disponibile("creare il desktop nascosto", "CreateDesktopW", ctypes.get_last_error()))
    if not user32.SetThreadDesktop(desktop):
        codice = ctypes.get_last_error()
        user32.CloseDesktop(desktop)
        raise pytest.UsageError(_non_disponibile("spostare le prove sul desktop nascosto", "SetThreadDesktop", codice))
    DESKTOP_DELLE_PROVE["nascosto"] = desktop


@pytest.fixture(autouse=True)
def cartella_di_prova(tmp_path, monkeypatch):
    """La cartella in cui il programma scrive, durante i test, è una cartella temporanea."""
    import percorsi
    monkeypatch.setattr(percorsi, "cartella", lambda: str(tmp_path))
    return tmp_path


@pytest.fixture(scope="session")
def app_wx():
    """L'applicazione wx delle prove con le finestre, una per tutta la sessione, sul desktop nascosto."""
    import wx

    app = wx.App(False)
    yield app
    for finestra in wx.GetTopLevelWindows():
        finestra.Destroy()
