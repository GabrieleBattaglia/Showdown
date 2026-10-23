"""
Le prove dell'istanza unica, tappa 14, decisione D34, con una pipe e un mutex di prova scelti da
MESS_ISTANZA, che non parlano con il MESS magari aperto: senza ascolto manda è falso; con l'ascolto è
vero e la prima copia riceve la richiesta di mostrarsi, il mutex che cerca l'installatore c'è, e una
seconda copia partita nello stesso istante non prende la pipe; ferma libera la pipe e il mutex.
AllowSetForegroundWindow, che darebbe a ogni processo il permesso di prendersi il primo piano sullo
schermo vero, è sostituito da un registratore.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import ctypes
import os
import threading
import time
import uuid
from ctypes import wintypes

import pytest

import istanza

SYNCHRONIZE = 0x00100000


@pytest.fixture
def pipe_di_prova(monkeypatch):
    """Il nome di prova di pipe e mutex, e l'elenco delle volte che si è chiesto il permesso del primo piano."""
    nome = f"mess_prove_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("MESS_ISTANZA", nome)
    permessi = []
    monkeypatch.setattr(ctypes.windll.user32, "AllowSetForegroundWindow", lambda chi: permessi.append(chi) or 1)
    return permessi


def _mutex_c_e(nome):
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenMutexW.restype = wintypes.HANDLE
    kernel32.OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    maniglia = kernel32.OpenMutexW(SYNCHRONIZE, False, nome)
    if maniglia:
        kernel32.CloseHandle(maniglia)
    return bool(maniglia)


def test_i_nomi_di_prova(pipe_di_prova, monkeypatch):
    proprio = os.environ["MESS_ISTANZA"]
    assert istanza.nome() == rf"\\.\pipe\{proprio}" and istanza.nome_del_mutex() == f"MESS-{proprio}"
    monkeypatch.delenv("MESS_ISTANZA")
    monkeypatch.setenv("USERNAME", "gabriele")
    # Il mutex vero ha lo stesso nome di AppMutex in MESS.iss.
    assert istanza.nome() == r"\\.\pipe\MESS-gabriele" and istanza.nome_del_mutex() == "MESS"


def test_senza_ascolto_manda_e_falso(pipe_di_prova):
    assert not istanza.manda()
    assert pipe_di_prova == []


def test_con_l_ascolto_la_seconda_copia_si_presenta(pipe_di_prova):
    chiamata = threading.Event()
    ascolto = istanza.Ascolto(chiamata.set)
    try:
        assert ascolto.attiva and _mutex_c_e(istanza.nome_del_mutex())
        assert istanza.manda()
        assert chiamata.wait(10)
        assert pipe_di_prova == [-1]
        # Una copia partita nello stesso istante trova la pipe già presa.
        altra = istanza.Ascolto(lambda: None)
        assert not altra.attiva
    finally:
        ascolto.ferma()
    assert not _mutex_c_e(istanza.nome_del_mutex())


def test_ferma_libera_la_pipe(pipe_di_prova):
    istanza.Ascolto(lambda: None).ferma()
    # Il filo dell'ascolto si chiude da sé: entro pochi istanti la pipe è di nuovo libera.
    scadenza = time.monotonic() + 10
    nuovo = istanza.Ascolto(lambda: None)
    while not nuovo.attiva and time.monotonic() < scadenza:
        time.sleep(0.05)
        nuovo = istanza.Ascolto(lambda: None)
    try:
        assert nuovo.attiva
    finally:
        nuovo.ferma()
