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
Dalla revisione dello stesso giorno:
- la stessa cartella raggiunta per un'altra strada, una giunzione o un'unità di subst, è la stessa, e il
  trasloco la rifiuta invece di mettere i dati in una riserva dentro sé stessi;
- la data di un mondo viene dal salvataggio o, se lui non si legge, dalla sua copia, come al caricamento;
  se non si legge nessuno dei due, salvato() dice anche il perché, e quel mondo non si può usare;
- una cartella scelta che c'è ma non ha un mondo, come quella di un cloud non ancora pronto, all'avvio è
  un problema anche lei, SenzaMondo, salvo quella per cui si è appena detto sì a un mondo nuovo;
- la vecchia disposizione non conta le cartelle vuote né il dato che contiene la cartella del mondo stessa,
  e se il mondo accanto al programma è stato salvato dopo quello della cartella, il più recente resta in uso;
- dopo un cambio di cartella si rileggono anche i modelli dei tornei, non soltanto le formule; e un mondo la
  cui cartella non si raggiunge più, per esempio una penna staccata a MESS aperto, si salva nella nuova.
"""

import contextlib
import datetime
import errno
import os
import shutil
from typing import NamedTuple

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


class Salvato(NamedTuple):
    """
    Quando è stato salvato il mondo di una cartella. data, in ora locale, o None se nella cartella non c'è
    un mondo; dal_salvataggio, vero se la data viene dal salvataggio stesso, falso se dalla data del suo
    file, perché non la dice o non si legge; errore, il perché quando né il salvataggio né la sua copia si
    leggono, e allora quel mondo non si può usare, altrimenti None.
    """

    data: datetime.datetime | None
    dal_salvataggio: bool = False
    errore: str | None = None


def _data_del_file(file):
    with contextlib.suppress(OSError, ValueError, OverflowError):
        return datetime.datetime.fromtimestamp(os.path.getmtime(file))  # noqa: DTZ006 - solo per mostrarla, come adesso()
    return None


def salvato(cartella):
    """
    Quando è stato salvato il mondo della cartella, Salvato. I file sono quelli che il caricamento cerca,
    nello stesso ordine, come archivio._carica: il salvataggio e la sua copia, compressi, o quelli di
    prima della tappa 7 se dei compressi non c'è nessuno. Vale il primo che si legge, perché è quello che
    MESS caricherebbe: se il salvataggio è rovinato e la copia no, la data è quella della copia. Se non si
    legge nessuno dei due, la data del file del primo e il perché, con le parole del caricamento.
    """
    principale, copia = (os.path.join(cartella, nome) for nome in (FILE_MONDO, FILE_MONDO_COPIA))
    if not os.path.exists(principale) and not os.path.exists(copia):
        principale, copia = (os.path.join(cartella, nome) for nome in (FILE_MONDO_VECCHIO, FILE_MONDO_COPIA_VECCHIO))
    esistenti = [file for file in (principale, copia) if os.path.exists(file)]
    if not esistenti:
        return Salvato(None)
    motivo = f"il file {os.path.basename(principale)} non c'è"
    for file in esistenti:
        try:
            documento = archivio.leggi(file)
        except archivio.ErroreSalvataggio as errore:
            motivo = f"{motivo}; e la copia di sicurezza nemmeno, perché {errore}" if file == copia else str(errore)
            continue
        with contextlib.suppress(KeyError, TypeError, ValueError, AttributeError):
            return Salvato(in_ora_locale(datetime.datetime.fromisoformat(documento["salvato"])), True)
        return Salvato(_data_del_file(file))
    return Salvato(_data_del_file(esistenti[0]), False, motivo)


class SenzaMondo(str):
    """Il problema dell'avvio quando la cartella scelta c'è ma non ha un mondo: una frase come le altre, che si riconosce dal tipo."""


def problema_della_cartella(accettata=None):
    """
    All'avvio: None se la cartella del mondo c'è, e la predefinita si crea senza domande se manca;
    altrimenti il perché, in una frase da mettere dopo i due punti. Non nasce mai un mondo altrove: anche
    una cartella scelta che c'è ma non ha un mondo è un problema, SenzaMondo, perché può essere quella di
    un cloud non ancora pronto, e un mondo nuovo ci entrerebbe in conflitto col vero. Non lo è la cartella
    accettata, quella per cui all'avvio si è appena detto sì a un mondo nuovo, né la predefinita, dove
    nasce il primo mondo di chi comincia.
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
    if not os.path.isdir(scelta):
        return f"la cartella {scelta} non c'è"
    if ha_un_mondo(scelta) or (accettata is not None and percorsi.stessa(scelta, accettata)):
        return None
    return SenzaMondo(f"nella cartella {scelta} non c'è un mondo di MESS")


def _dentro_i_dati(cartella, contenitore, nomi):
    """Vero se la cartella è uno dei dati nominati del contenitore, o sta dentro uno di loro."""
    return any(percorsi.dentro(cartella, os.path.join(contenitore, nome)) for nome in nomi)


def intrecciate(prima, seconda):
    """
    Vero se una delle due cartelle sta dentro uno dei dati dell'altra, per esempio dentro la sua cartella
    cronache: spostare i dati dall'una all'altra sposterebbe una cartella dentro sé stessa. Vale anche
    con la cartella del programma, dove le versioni di prova tenevano i dati: una cartella del mondo
    dentro la sua cartella tornei, alla partenza seguente, sarebbe da spostare dentro sé stessa.
    """
    return _dentro_i_dati(seconda, prima, DATI) or _dentro_i_dati(prima, seconda, DATI)


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


def trasloca(origine, destinazione, ora=None, nomi=None):
    """
    Sposta i dati di MESS da origine a destinazione, che si crea se manca: tutti quelli che ci sono, o
    soltanto nomi, se dati. Quelli che la destinazione aveva vanno prima in una sua sottocartella di
    riserva datata. Tutto o niente: se uno spostamento non riesce, quelli già fatti tornano indietro e si
    solleva SpostamentoNonRiuscito. Prima di toccare niente rifiuta due cartelle che sono la stessa, anche
    raggiunta per un'altra strada, perché i dati finirebbero nella riserva di sé stessi, e una cartella che
    sta dentro i dati dell'altra. Restituisce il Trasloco, da concludere, quando tutto il resto è andato, o
    da annullare.
    """
    da_spostare = presenti(origine) if nomi is None else list(nomi)
    if percorsi.stessa(origine, destinazione):
        raise SpostamentoNonRiuscito(f"le cartelle {origine} e {destinazione} sono la stessa")
    if _dentro_i_dati(destinazione, origine, da_spostare) or _dentro_i_dati(origine, destinazione, DATI):
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
        for nome in da_spostare:
            trasloco.sposta(os.path.join(origine, nome), os.path.join(destinazione, nome))
            trasloco.spostati.append(nome)
    except OSError as errore:
        rimasti = trasloco.annulla()
        motivo = errore.strerror or str(errore)
        if errore.filename:
            motivo = f"{motivo}: {errore.filename}"
        raise SpostamentoNonRiuscito(motivo, rimasti) from errore
    return trasloco


def _dimentica_le_letture():
    """I dati letti e tenuti da parte, le formule e i modelli dei tornei, si rileggono dai file nel posto nuovo."""
    formule.azzera_cache()
    modelli_torneo.azzera_cache()


def cambia_cartella(nuova, ora=None, salva=None):
    """
    Dal menu Impostazioni: i dati della cartella del mondo di adesso passano nella nuova, e il file
    accanto al programma la nomina. Prima gli spostamenti, poi il file: se il file non si scrive, gli
    spostamenti tornano indietro, perché alla prossima partenza MESS cercherebbe il mondo nella
    cartella vecchia, ormai vuota. Il mondo va salvato prima; ma se la sua cartella non si raggiunge più,
    per esempio una penna staccata a MESS aperto, non si può, e allora salva, una funzione che salva il
    mondo e torna vero se è riuscito, lo salva nella nuova, quando il file la nomina già: se non riesce,
    tutto torna com'era, file compreso. Restituisce il Trasloco concluso; SpostamentoNonRiuscito se non
    riesce, e niente è cambiato.
    """
    attuale = percorsi.cartella()
    trasloco = trasloca(attuale, nuova, ora)
    try:
        percorsi.imposta_cartella(nuova)
    except OSError as errore:
        rimasti = trasloco.annulla()
        raise SpostamentoNonRiuscito(f"il file {percorsi.FILE_DELLA_CARTELLA}, accanto al programma, non si scrive: {errore.strerror or errore}",
                                     rimasti) from errore
    if salva is not None and not salva():
        rimasti = trasloco.annulla()
        try:
            percorsi.imposta_cartella(attuale)
        except OSError:
            rimasti.append(percorsi.file_della_cartella())
        raise SpostamentoNonRiuscito("il mondo non si è potuto salvare nella cartella nuova", rimasti)
    trasloco.concludi()
    _dimentica_le_letture()
    return trasloco


def _vuota(percorso):
    """Vero per una cartella vuota, come quelle che un installatore può lasciare accanto al programma."""
    if not os.path.isdir(percorso) or os.path.islink(percorso):
        return False
    try:
        with os.scandir(percorso) as voci:
            return next(voci, None) is None
    except OSError:
        return False


def vecchia_disposizione():
    """
    I dati della vecchia disposizione, accanto al programma, quando la cartella del mondo è un'altra; una
    lista vuota se non ce ne sono. Non contano le cartelle vuote, né il dato che contiene la cartella del
    mondo stessa, come la cartella tornei del programma scelta per cartella del mondo: spostarlo vorrebbe
    dire spostare il mondo dentro sé stesso, e MESS si fermerebbe a ogni avvio.
    """
    programma = percorsi.cartella_del_programma()
    mondo = percorsi.cartella()
    if percorsi.stessa(programma, mondo):
        return []
    return [nome for nome in presenti(programma)
            if not _vuota(os.path.join(programma, nome)) and not percorsi.dentro(mondo, os.path.join(programma, nome))]


def _accanto_piu_recente(programma, mondo):
    """Vero se i mondi accanto al programma e nella cartella del mondo si leggono tutti e due, e il primo è stato salvato dopo."""
    nostro, loro = salvato(programma), salvato(mondo)
    if nostro.errore or loro.errore or nostro.data is None or loro.data is None:
        return False
    return nostro.data > loro.data


def sposta_la_vecchia_disposizione(ora=None):
    """
    All'avvio, dopo il controllo della cartella: i dati accanto al programma passano nella cartella del
    mondo. Se lei ha già un mondo, resta in uso il più recente: di solito il suo, e i dati di accanto al
    programma vanno in una sua riserva; ma se il mondo accanto al programma è stato salvato dopo, per
    esempio da una versione di prima aperta nel frattempo, è quello a restare in uso, e quello che la
    cartella aveva va nella riserva. Se uno dei due non si legge, resta quello della cartella. Restituisce
    il Trasloco concluso, o None se non c'era niente da spostare; SpostamentoNonRiuscito se non riesce, e
    niente è cambiato.
    """
    nomi = vecchia_disposizione()
    if not nomi:
        return None
    programma, mondo = percorsi.cartella_del_programma(), percorsi.cartella()
    if ha_un_mondo(mondo) and not _accanto_piu_recente(programma, mondo):
        destinazione = os.path.join(mondo, nome_della_riserva(mondo, ora))
    else:
        destinazione = mondo
    trasloco = trasloca(programma, destinazione, ora, nomi)
    trasloco.concludi()
    return trasloco
