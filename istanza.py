"""
MESS, l'istanza unica: la seconda copia porta la prima in primo piano e si chiude.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-23 con la tappa 14, decisione D34: due copie aperte insieme scriverebbero lo
stesso mess_mondo.json.gz, e una cancellerebbe il lavoro dell'altra. Sul modello di istanza.py di
MeTeOra, senza i file da passare: la prima copia tiene un mutex con nome, che anche l'installatore
di Inno Setup cerca con AppMutex di MESS.iss, e ascolta su una pipe con nome di Windows, per utente
e con una chiave; la seconda copia ci si presenta, le permette di venire in primo piano e si chiude.
Sul filo passano solo byte JSON, mai oggetti di Python. La variabile d'ambiente MESS_ISTANZA cambia
i nomi della pipe e del mutex, per le prove: così non parlano con il MESS che magari è aperto.
"""

import contextlib
import ctypes
import hashlib
import json
import os
import threading
from ctypes import wintypes
from multiprocessing import AuthenticationError
from multiprocessing.connection import Client, Listener

# AllowSetForegroundWindow: qualunque processo, cioè la prima copia.
_ASFW_ANY = -1


def nome():
    """Il nome della pipe, per utente."""
    proprio = os.environ.get("MESS_ISTANZA")
    if proprio:
        return rf"\\.\pipe\{proprio}"
    return rf"\\.\pipe\MESS-{os.environ.get('USERNAME', 'utente')}"


def nome_del_mutex():
    """Il mutex di MESS aperto: lo stesso nome di AppMutex in MESS.iss; con MESS_ISTANZA, uno di prova."""
    proprio = os.environ.get("MESS_ISTANZA")
    return f"MESS-{proprio}" if proprio else "MESS"


def _chiave(nome_della_pipe):
    return hashlib.sha256(f"MESS {nome_della_pipe}".encode()).digest()


def manda(nome_della_pipe=None):
    """Se un MESS è già aperto, gli chiede di venire in primo piano e torna vero; falso se non ce n'è uno."""
    nome_della_pipe = nome_della_pipe or nome()
    try:
        connessione = Client(nome_della_pipe, family="AF_PIPE", authkey=_chiave(nome_della_pipe))
    except (OSError, EOFError, AuthenticationError):
        # Nessuno ascolta, o sulla pipe c'è qualcuno che non conosce la chiave di MESS.
        return False
    with contextlib.suppress(Exception):
        ctypes.windll.user32.AllowSetForegroundWindow(_ASFW_ANY)
    try:
        with connessione:
            connessione.send_bytes(json.dumps({"mostra": True}).encode("utf-8"))
    except (OSError, EOFError):
        return False
    return True


class Ascolto:
    """
    La prima copia ascolta le altre: mostra() è chiamata nel filo dell'ascolto, per ogni copia che si
    presenta, e deve portare il lavoro nel filo della finestra. Se la pipe c'è già, perché un'altra
    copia è partita nello stesso istante, attiva è falso.
    """

    def __init__(self, mostra, nome_della_pipe=None):
        self._mostra = mostra
        self._nome = nome_della_pipe or nome()
        self._fermo = False
        self._mutex = None
        try:
            self._ascoltatore = Listener(self._nome, family="AF_PIPE", authkey=_chiave(self._nome))
        except OSError:
            self._ascoltatore = None
        self.attiva = self._ascoltatore is not None
        if self.attiva:
            if nome_della_pipe is None:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.CreateMutexW.restype = wintypes.HANDLE
                kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
                self._mutex = kernel32.CreateMutexW(None, False, nome_del_mutex()) or None
            threading.Thread(target=self._ascolta, name="MESS, istanza unica", daemon=True).start()

    def _ascolta(self):
        while not self._fermo:
            try:
                connessione = self._ascoltatore.accept()
            except Exception:  # noqa: BLE001 - una copia che si presenta male, o con la chiave sbagliata
                if self._fermo:
                    return
                continue
            with connessione, contextlib.suppress(Exception):
                messaggio = json.loads(connessione.recv_bytes(1 << 16).decode("utf-8"))
                if isinstance(messaggio, dict) and messaggio.get("mostra"):
                    self._mostra()

    def ferma(self):
        """All'uscita: l'ascolto finisce, e il mutex si lascia."""
        self._fermo = True
        if self._mutex is not None:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle(self._mutex)
            self._mutex = None
        if self._ascoltatore is not None:
            with contextlib.suppress(Exception):
                self._ascoltatore.close()
            # Sblocca accept aprendo e chiudendo la pipe senza la stretta di mano di Client, che
            # aspetterebbe per sempre una sfida (la lezione della 1.96.11 di MeTeOra).
            with contextlib.suppress(OSError), open(self._nome, "rb", buffering=0):
                pass
