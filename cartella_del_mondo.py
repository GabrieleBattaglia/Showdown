"""
MESS, la cartella del mondo: che cosa ci sta, quando è stato salvato il mondo che contiene, e lo
spostamento dei dati da una cartella all'altra, che riesce tutto o niente.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-23, richiesta di Gabriele: tutti i file del mondo, dello stato di gioco e delle
impostazioni stanno in una cartella sola, che si porta fra le macchine con una penna o con un cloud
come Dropbox, e si sceglie dal menu Impostazioni. Dove sta lo dice percorsi.py; qui ci sono i dati
che la compongono, DATI, e le operazioni senza finestre, che la finestra e l'avvio conducono:
- il controllo all'avvio: la cartella scelta che non c'è, o il file che la nomina e non si legge,
  è un problema da dire, mai un mondo nuovo che nasce altrove; la predefinita si crea se manca;
- la data del salvataggio di un mondo, dal salvataggio stesso o, se non si legge, dalla data del file;
- il trasloco: i dati di una cartella passano in un'altra, e quelli che l'altra aveva vanno prima in
  una sua sottocartella di riserva datata, "Riserva AAAA-MM-GG HH.MM". Ogni dato si rinomina, che sullo
  stesso disco è istantaneo; fra due dischi si copia, e l'originale si toglie soltanto quando tutte le
  copie sono riuscite. Se uno spostamento non riesce, quelli già fatti tornano indietro: il mondo non
  resta mai a metà fra due cartelle, e niente si perde;
- la vecchia disposizione: le versioni di prova scrivevano tutto accanto al programma, e alla prima
  partenza di questa i dati passano nella cartella del mondo; se lei ha già un mondo, vanno in una sua
  riserva, e il mondo della cartella resta quello.
"""

import contextlib
import datetime
import errno
import os
import shutil

import archivio
import formule
import impostazioni
import modelli_torneo
import percorsi
from costanti import CARTELLA_CRONACHE, FILE_MONDO, FILE_MONDO_COPIA, FILE_MONDO_COPIA_VECCHIO, FILE_MONDO_VECCHIO, NOME_FILE_LOG_USCITE
from utilita import adesso, in_ora_locale

# I file che sono un mondo, dal più importante: il salvataggio, la sua copia, e quelli non compressi di prima della tappa 7.
FILE_DEL_MONDO = (FILE_MONDO, FILE_MONDO_COPIA, FILE_MONDO_VECCHIO, FILE_MONDO_COPIA_VECCHIO)
# Tutto ciò che sta nella cartella del mondo: il mondo, il file temporaneo della scrittura sicura, le
# impostazioni, le vecchie glorie, le cronache, i modelli e le formule dei tornei, i salvataggi illeggibili.
DATI = (*FILE_DEL_MONDO, FILE_MONDO + ".tmp", impostazioni.FILE_IMPOSTAZIONI, NOME_FILE_LOG_USCITE, CARTELLA_CRONACHE, modelli_torneo.CARTELLA,
        formule.NOME_FILE, archivio.CARTELLA_QUARANTENA)
PREFISSO_RISERVA = "Riserva "
# Windows, quando un file non si può rinominare su un altro disco.
_ERRORE_ALTRO_DISCO = 17


class SpostamentoNonRiuscito(OSError):
    """
    Uno spostamento dei dati non è riuscito, e quelli già fatti sono tornati indietro. motivo è il
    perché, in una frase; rimasti sono i percorsi che non sono potuti tornare al loro posto, di solito nessuno.
    """

    def __init__(self, motivo, rimasti=()):
        super().__init__(motivo)
        self.motivo = motivo
        self.rimasti = list(rimasti)


def presenti(cartella):
    """I dati di MESS che ci sono nella cartella, nell'ordine di DATI."""
    return [nome for nome in DATI if os.path.lexists(os.path.join(cartella, nome))]


def ha_un_mondo(cartella):
    """Vero se nella cartella c'è un mondo: il salvataggio, la sua copia, o quelli di prima della tappa 7."""
    return any(os.path.isfile(os.path.join(cartella, nome)) for nome in FILE_DEL_MONDO)


def salvato(cartella):
    """
    Quando è stato salvato il mondo della cartella, in ora locale: la coppia di data e di dove viene,
    vero se dal salvataggio stesso, falso se dalla data del file, perché il salvataggio non si legge o
    non la dice. Vale il primo file del mondo che c'è, nell'ordine di FILE_DEL_MONDO; (None, False) se
    nella cartella non c'è un mondo.
    """
    for nome in FILE_DEL_MONDO:
        file = os.path.join(cartella, nome)
        if not os.path.isfile(file):
            continue
        with contextlib.suppress(archivio.ErroreSalvataggio, KeyError, TypeError, ValueError):
            return in_ora_locale(datetime.datetime.fromisoformat(archivio.leggi(file)["salvato"])), True
        with contextlib.suppress(OSError, ValueError):
            return datetime.datetime.fromtimestamp(os.path.getmtime(file)), False  # noqa: DTZ006 - solo per mostrarla, come adesso()
    return None, False


def problema_della_cartella():
    """
    All'avvio: None se la cartella del mondo c'è, e la predefinita si crea senza domande se manca;
    altrimenti il perché, in una frase da mettere dopo i due punti. Non nasce mai un mondo altrove.
    """
    try:
        scelta = percorsi.cartella_scelta()
    except percorsi.CartellaIllegibile as errore:
        return str(errore)
    if scelta is None:
        predefinita = percorsi.cartella_predefinita()
        try:
            os.makedirs(predefinita, exist_ok=True)
        except OSError as errore:
            return f"la cartella {predefinita} non si può creare: {errore.strerror or errore}"
        return None
    if os.path.isdir(scelta):
        return None
    return f"la cartella {scelta} non c'è"


def intrecciate(prima, seconda):
    """
    Vero se una delle due cartelle sta dentro uno dei dati dell'altra, per esempio dentro la sua cartella
    cronache: spostare i dati dall'una all'altra sposterebbe una cartella dentro sé stessa.
    """
    return any(percorsi.dentro(seconda, os.path.join(prima, nome)) or percorsi.dentro(prima, os.path.join(seconda, nome)) for nome in DATI)


def nome_della_riserva(cartella, ora=None):
    """Il nome della sottocartella di riserva, Riserva AAAA-MM-GG HH.MM, con un numero fra parentesi se nello stesso minuto ce n'è già una."""
    base = f"{PREFISSO_RISERVA}{ora or adesso():%Y-%m-%d %H.%M}"
    nome, numero = base, 2
    while os.path.lexists(os.path.join(cartella, nome)):
        nome = f"{base} ({numero})"
        numero += 1
    return nome


def _altro_disco(errore):
    return errore.errno == errno.EXDEV or getattr(errore, "winerror", None) == _ERRORE_ALTRO_DISCO


def _togli(percorso):
    """Toglie un file o una cartella intera; OSError se non riesce."""
    if os.path.isdir(percorso) and not os.path.islink(percorso):
        shutil.rmtree(percorso)
    else:
        os.remove(percorso)


class Trasloco:
    """
    Gli spostamenti di un trasloco, da concludere o da annullare. origine e destinazione sono le due
    cartelle; riserva è la sottocartella della destinazione dove sono andati i dati che lei aveva, o
    None; spostati i nomi dei dati arrivati; avanzi, dopo concludi, gli originali copiati da un altro
    disco che non si sono potuti togliere, doppioni innocui.
    """

    def __init__(self, origine, destinazione):
        self.origine = origine
        self.destinazione = destinazione
        self.riserva = None
        self.spostati = []
        self.avanzi = []
        self._fatti = []
        self._create = []

    def crea(self, cartella):
        """Crea la cartella se manca, e la ricorda per toglierla se il trasloco si annulla."""
        if not os.path.isdir(cartella):
            os.makedirs(cartella)
            self._create.append(cartella)

    def sposta(self, da, a):
        """Un dato da un posto all'altro: rinominato, o copiato se sta su un altro disco. OSError se non riesce, e niente resta a metà."""
        if os.path.lexists(a):
            raise FileExistsError(errno.EEXIST, "c'è già", a)
        try:
            os.rename(da, a)
        except OSError as errore:
            if not _altro_disco(errore):
                raise
        else:
            self._fatti.append((False, da, a))
            return
        try:
            if os.path.isdir(da):
                shutil.copytree(da, a)
            else:
                shutil.copy2(da, a)
        except OSError:
            if os.path.lexists(a):
                with contextlib.suppress(OSError):
                    _togli(a)
            raise
        self._fatti.append((True, da, a))

    def annulla(self):
        """Riporta ogni dato al suo posto, dall'ultimo al primo, e toglie le cartelle create se sono vuote. Restituisce i percorsi che non sono tornati."""
        rimasti = []
        for copiato, da, a in reversed(self._fatti):
            try:
                if copiato:
                    _togli(a)
                else:
                    os.rename(a, da)
            except OSError:
                rimasti.append(a)
        self._fatti.clear()
        for cartella in reversed(self._create):
            with contextlib.suppress(OSError):
                os.rmdir(cartella)
        self._create.clear()
        return rimasti

    def concludi(self):
        """Toglie gli originali dei dati copiati da un altro disco: quelli che non si tolgono restano in avanzi."""
        for copiato, da, _a in self._fatti:
            if copiato:
                try:
                    _togli(da)
                except OSError:
                    self.avanzi.append(da)
        self._fatti.clear()
        self._create.clear()
        return self.avanzi


def trasloca(origine, destinazione, ora=None):
    """
    Sposta i dati di MESS da origine a destinazione, che si crea se manca. Quelli che la destinazione
    aveva vanno prima in una sua sottocartella di riserva datata. Tutto o niente: se uno spostamento non
    riesce, quelli già fatti tornano indietro e si solleva SpostamentoNonRiuscito. Restituisce il
    Trasloco, da concludere, quando tutto il resto è andato, o da annullare.
    """
    if intrecciate(origine, destinazione):
        raise SpostamentoNonRiuscito(f"le cartelle {origine} e {destinazione} stanno una dentro i dati dell'altra")
    trasloco = Trasloco(origine, destinazione)
    try:
        trasloco.crea(destinazione)
        loro = presenti(destinazione)
        if loro:
            trasloco.riserva = os.path.join(destinazione, nome_della_riserva(destinazione, ora))
            trasloco.crea(trasloco.riserva)
            for nome in loro:
                trasloco.sposta(os.path.join(destinazione, nome), os.path.join(trasloco.riserva, nome))
        for nome in presenti(origine):
            trasloco.sposta(os.path.join(origine, nome), os.path.join(destinazione, nome))
            trasloco.spostati.append(nome)
    except OSError as errore:
        rimasti = trasloco.annulla()
        motivo = errore.strerror or str(errore)
        if errore.filename:
            motivo = f"{motivo}: {errore.filename}"
        raise SpostamentoNonRiuscito(motivo, rimasti) from errore
    return trasloco


def cambia_cartella(nuova, ora=None):
    """
    Dal menu Impostazioni: i dati della cartella del mondo di adesso passano nella nuova, e il file
    accanto al programma la nomina. Prima gli spostamenti, poi il file: se il file non si scrive, gli
    spostamenti tornano indietro, perché alla prossima partenza MESS cercherebbe il mondo nella
    cartella vecchia, ormai vuota. Il mondo va salvato prima. Restituisce il Trasloco concluso;
    SpostamentoNonRiuscito se non riesce, e niente è cambiato.
    """
    trasloco = trasloca(percorsi.cartella(), nuova, ora)
    try:
        percorsi.imposta_cartella(nuova)
    except OSError as errore:
        rimasti = trasloco.annulla()
        raise SpostamentoNonRiuscito(f"il file {percorsi.FILE_DELLA_CARTELLA}, accanto al programma, non si scrive: {errore.strerror or errore}",
                                     rimasti) from errore
    trasloco.concludi()
    # I dati letti e tenuti da parte si rileggono dai file nel posto nuovo.
    formule.azzera_cache()
    return trasloco


def vecchia_disposizione():
    """I dati della vecchia disposizione, accanto al programma, quando la cartella del mondo è un'altra; una lista vuota se non ce ne sono."""
    programma = percorsi.cartella_del_programma()
    if percorsi.stessa(programma, percorsi.cartella()):
        return []
    return presenti(programma)


def sposta_la_vecchia_disposizione(ora=None):
    """
    All'avvio, dopo il controllo della cartella: i dati accanto al programma passano nella cartella del
    mondo; se lei ha già un mondo vanno in una sua riserva, e il mondo resta quello della cartella.
    Restituisce il Trasloco concluso, o None se non c'era niente da spostare; SpostamentoNonRiuscito
    se non riesce, e niente è cambiato.
    """
    if not vecchia_disposizione():
        return None
    mondo = percorsi.cartella()
    destinazione = os.path.join(mondo, nome_della_riserva(mondo, ora)) if ha_un_mondo(mondo) else mondo
    trasloco = trasloca(percorsi.cartella_del_programma(), destinazione, ora)
    trasloco.concludi()
    return trasloco
