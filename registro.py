"""
MESS, il registro degli errori e dei crash: due file accanto al programma, a misura limitata.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-23 con la tappa 14, decisione D34: nel pacchetto compilato la console non c'è, e
un errore imprevisto non lascerebbe traccia da mandare a chi sviluppa. Sul modello di registro.py di
MeTeOra, in piccolo:
- "MESS - Errori.log": il resoconto completo di ogni errore imprevisto, con la pila, e dal programma
  compilato ciò che andrebbe su stderr, che lì non c'è. Gira con una copia, "MESS - Errori.log.1",
  e i due insieme non superano MISURA_MASSIMA, 10 MB, come in MeTeOra per scelta di Gabriele.
- "MESS - Crash.log": quello che scrive faulthandler quando Python muore senza accorgersene, per
  esempio per un errore dentro una DLL di Windows. Si apre a ogni avvio e si toglie a ogni uscita
  pulita. All'avvio dopo, se racconta un crash vero, cioè una riga "Fatal Python error" o
  un'eccezione di Windows che è un errore, diventa "MESS - Crash precedente.log", da allegare quando
  si chiede aiuto; le eccezioni di Windows che chi le solleva poi gestisce, come quelle di COM, non
  contano e il file si riscrive.
Il resoconto di un crash non si perde mai: se non si può spostare, si copia nel file del crash
precedente; se neppure questo si può scrivere, resta in testa al file del crash, che allora si apre
in aggiunta, e l'uscita pulita lo riporta al solo resoconto invece di toglierlo, così il prossimo
avvio riprova a metterlo da parte. È la lezione della 1.104.0 di MeTeOra.
Senza avvia(), per esempio nelle prove, le funzioni non fanno niente.
Dal 2026-10-23, con la cartella del mondo che si sceglie dal menu Impostazioni, i registri restano
accanto al programma, nella cartella che Showdown.py passa ad avvia(), percorsi.cartella_del_programma():
descrivono la macchina, non il mondo, e devono potersi scrivere anche quando la cartella del mondo
non c'è, per esempio su una penna non collegata.
"""

import contextlib
import faulthandler
import logging
import logging.handlers
import os
import re
import sys
import threading
import traceback

FILE_DEGLI_ERRORI = "MESS - Errori.log"
FILE_DEL_CRASH = "MESS - Crash.log"
FILE_DEL_CRASH_PRECEDENTE = "MESS - Crash precedente.log"
MISURA_MASSIMA = 10 * 1024 * 1024
_NOME = "mess.errori"
# Il registro, il file aperto per faulthandler, lo stderr del programma compilato, e quanti byte del
# file del crash sono il resoconto della volta prima, che non si è potuto mettere da parte.
_stato = {"registro": None, "crash": None, "stderr": None, "base": 0}
# Le eccezioni di Windows che faulthandler chiama per nome sono tutte errori; le altre le scrive
# col codice, e un codice NTSTATUS è un errore quando i tre bit alti valgono 110.
_ERRORE_DI_PYTHON = "Fatal Python error"
_ECCEZIONE_DI_WINDOWS = "Windows fatal exception: "
_NOMI_FATALI = frozenset({"access violation", "stack overflow", "int divide by zero", "float divide by zero", "float overflow",
                          "integer overflow", "page error"})
_CODICE = re.compile(r"code 0x([0-9A-Fa-f]{1,8})")


def crash_vero(testo):
    """Se il testo del file del crash racconta un crash vero: un errore fatale di Python o un'eccezione di Windows che è un errore."""
    for riga in testo.splitlines():
        if riga.startswith(_ERRORE_DI_PYTHON):
            return True
        if riga.startswith(_ECCEZIONE_DI_WINDOWS):
            resto = riga[len(_ECCEZIONE_DI_WINDOWS):].strip()
            codice = _CODICE.fullmatch(resto)
            if resto in _NOMI_FATALI or (codice and int(codice.group(1), 16) & 0xE0000000 == 0xC0000000):
                return True
    return False


def _metti_da_parte(cartella, crash, dati):
    """
    Il resoconto di un crash vero, dal file del crash a quello del crash precedente: spostato, o, se
    non si può, copiato. Restituisce il percorso del crash precedente, o None se non si è scritto.
    """
    precedente = os.path.join(cartella, FILE_DEL_CRASH_PRECEDENTE)
    with contextlib.suppress(OSError):
        os.replace(crash, precedente)
        return precedente
    try:
        with open(precedente, "wb") as file:
            file.write(dati)
    except OSError:
        return None
    return precedente


class _VersoIlRegistro:
    """
    Uno stderr che scrive nel registro, riga per riga: per il programma compilato, che uno stderr non
    ce l'ha. Se il file del registro non si scrive, logging racconta l'errore proprio su stderr, cioè
    di nuovo qui: dalla seconda revisione della tappa 14 quello che arriva mentre lo stesso filo sta
    già scrivendo si perde, invece di andare in ricorsione fino al RecursionError. Ha encoding, come
    gli stderr veri, per le librerie che lo leggono.
    """

    encoding = "utf-8"
    errors = "replace"

    def __init__(self, registro):
        self._registro = registro
        self._resto = ""
        self._filo = threading.local()

    def write(self, testo):
        testo = str(testo)
        if getattr(self._filo, "dentro", False):
            return len(testo)
        self._filo.dentro = True
        try:
            self._resto += testo
            *righe, self._resto = self._resto.split("\n")
            for riga in righe:
                if riga.strip():
                    self._registro.error(riga.rstrip())
        finally:
            self._filo.dentro = False
        return len(testo)

    def flush(self):
        pass

    def isatty(self):
        return False


def avvia(cartella, misura=MISURA_MASSIMA):
    """
    All'avvio: apre i due file nella cartella del programma. Restituisce il percorso del resoconto
    del crash della volta prima, se è stato un crash vero, altrimenti None.
    """
    crash = os.path.join(cartella, FILE_DEL_CRASH)
    dati = b""
    with contextlib.suppress(OSError), open(crash, "rb") as file:
        dati = file.read()
    precedente = None
    conserva = False
    if crash_vero(dati.decode("utf-8", errors="replace")):
        precedente = _metti_da_parte(cartella, crash, dati)
        if precedente is None:
            precedente, conserva = crash, True
    registro = logging.getLogger(_NOME)
    registro.setLevel(logging.INFO)
    registro.propagate = False
    for vecchio in list(registro.handlers):
        registro.removeHandler(vecchio)
        vecchio.close()
    with contextlib.suppress(OSError):
        gestore = logging.handlers.RotatingFileHandler(os.path.join(cartella, FILE_DEGLI_ERRORI), maxBytes=misura // 2, backupCount=1,
                                                       encoding="utf-8", delay=True)
        gestore.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        registro.addHandler(gestore)
    _stato["registro"] = registro
    _stato["base"] = 0
    with contextlib.suppress(OSError):
        # In aggiunta, quando il resoconto della volta prima resta qui: faulthandler scrive dopo di lui.
        _stato["crash"] = open(crash, "a" if conserva else "w", encoding="utf-8")  # noqa: SIM115 - resta aperto per faulthandler, fino a chiudi()
        if conserva:
            _stato["base"] = os.fstat(_stato["crash"].fileno()).st_size
        faulthandler.enable(_stato["crash"], all_threads=True)
    if sys.stderr is None:
        _stato["stderr"] = sys.stderr = _VersoIlRegistro(registro)
    if conserva:
        scrivi(f"Il resoconto del crash della volta prima non si è potuto mettere in {FILE_DEL_CRASH_PRECEDENTE}: resta in {FILE_DEL_CRASH}.")
    return precedente


def scrivi(testo):
    """Una riga nel registro, se è avviato."""
    if _stato["registro"] is not None:
        with contextlib.suppress(Exception):
            _stato["registro"].info(testo)


def problema(tipo, valore, traccia):
    """Il resoconto completo di un errore imprevisto, con la pila."""
    if _stato["registro"] is not None:
        with contextlib.suppress(Exception):
            _stato["registro"].error("".join(traceback.format_exception(tipo, valore, traccia)).rstrip())


def chiudi():
    """
    All'uscita pulita: faulthandler si spegne e il file del crash si toglie, perché non c'è stato
    nessun crash; se in testa ha il resoconto della volta prima, torna a quello e resta.
    """
    crash = _stato["crash"]
    if crash is not None:
        with contextlib.suppress(Exception):
            faulthandler.disable()
        base = _stato["base"]
        if base:
            with contextlib.suppress(OSError, ValueError):
                crash.truncate(base)
        with contextlib.suppress(OSError):
            crash.close()
            if not base:
                os.remove(crash.name)
        _stato["crash"] = None
    _stato["base"] = 0
    if _stato["stderr"] is not None and sys.stderr is _stato["stderr"]:
        sys.stderr = None
    _stato["stderr"] = None
    registro = _stato["registro"]
    if registro is not None:
        for gestore in list(registro.handlers):
            registro.removeHandler(gestore)
            gestore.close()
    _stato["registro"] = None
