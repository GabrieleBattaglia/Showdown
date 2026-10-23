"""
MESS, Manageriale e Simulatore Showdown: il punto di avvio.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il porting in Python fino alla versione 25.4.24 è di Gabriele Battaglia con Gemini 2.5.
Data concepimento: 13/04/2015 16:13 by Gabriele Battaglia. Porting a Python dal 31/01/2020.
Dal 2026-10-06, con la tappa 2 del piano, il vecchio sd.py è diviso in moduli: qui si crea il
mondo, lo si carica, lo si fa avanzare col tempo trascorso e si apre l'interfaccia. Con la tappa
3, se il salvataggio c'è ma non si legge, il gioco si ferma senza salvare nulla. Con la tappa 5
si apre la finestra; l'interfaccia testuale restava, con l'opzione --testo, per le operazioni che
nella finestra non erano ancora arrivate.
Dal 2026-10-07, con la decisione D24, la finestra suona: all'avvio, e quando il salvataggio non
si legge; e un errore imprevisto, che finirebbe soltanto su una console che chi non vede non legge,
ha il suo allarme e un messaggio.
Dal 2026-10-23, con la tappa 14 e la decisione D34, MESS diventa un programma da installare, e
l'interfaccia testuale se ne va, con cli.py e l'opzione --testo: la finestra fa ormai tutto quello
che faceva lei. All'avvio, prima di ogni altra cosa, se un MESS è già aperto, questa copia lo porta
in primo piano e si chiude senza toccare niente, perché due copie insieme scriverebbero lo stesso
mondo; altrimenti si mette lei in ascolto delle copie che verranno, istanza.py. Poi si apre il
registro degli errori e dei crash accanto al mondo, registro.py: un errore imprevisto vi lascia il
suo resoconto completo, e il crash della volta prima la vista lo dice all'apertura. Un errore che
ferma il programma si scrive lì e si dice in un messaggio, col suono dell'allarme. A finestra
comparsa, solo dall'eseguibile compilato, aggiornamento.py controlla se su GitHub c'è una versione
nuova. Le parti della tappa 14 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
"""

import contextlib
import sys
import threading
import traceback

import archivio
import nomi
import suoni
import testi
from mondo import Mondo


def avvia_finestra(crash_precedente=None, finestre=None):
    """
    Crea, carica e fa avanzare il mondo, poi apre la finestra fino all'uscita. Falso se il salvataggio
    non si leggeva. crash_precedente è il resoconto del crash della volta prima, che la vista dice
    all'apertura; finestre, se data, riceve la finestra appena nasce, per l'ascolto dell'istanza unica.
    """
    import wx

    import aggiornamento
    from gui.finestra import FinestraPrincipale

    # Una wx.App sola per processo: quella delle prove, se c'è già.
    app = wx.GetApp() or wx.App(False)
    messaggi = []
    mondo = Mondo(notifica=messaggi.append)
    nomi.collezioni()
    messaggi.extend(f"Attenzione: {avviso}" for avviso in nomi.avvisi)
    try:
        origine = archivio.carica(mondo)
    except archivio.SalvataggioIllegibile as errore:
        # Il gioco si ferma qui: il suono aspetta di finire, come all'uscita, prima della spiegazione.
        suoni.suona("salvataggio_illeggibile", sync=suoni.ATTESA_USCITA)
        wx.MessageBox("\n".join(testi.salvataggio_illeggibile(errore)), "MESS", wx.OK | wx.ICON_ERROR)
        return False
    # L'avanzamento lo racconta la finestra, dal suo riepilogo in numeri.
    mondo.notifica = lambda *_args: None
    ultimo_prima = mondo.datetime_ultimo_run_reale
    rapporto = mondo.processa_tempo_trascorso()
    finestra = FinestraPrincipale(mondo, origine, messaggi, rapporto, ultimo_prima, avvisi_all_avvio=bool(nomi.avvisi),
                                  crash_precedente=crash_precedente)
    if finestre is not None:
        finestre.append(finestra)
    _rete_per_gli_errori(finestra)
    # Dal collaudo del 23 ottobre 2026 la finestra si apre massimizzata, come vuole Gabriele.
    finestra.Maximize()
    finestra.Show()
    wx.CallAfter(finestra.suoni_d_avvio)
    # Dalla tappa 14, a finestra comparsa: solo dall'eseguibile compilato, in un filo, e la finestra intanto risponde.
    wx.CallAfter(aggiornamento.controlla, finestra)
    app.MainLoop()
    return True


def _rete_per_gli_errori(finestra):
    """
    Le eccezioni che sfuggono a un comando della finestra: wx le passa a sys.excepthook, e il comando
    muore in silenzio. Dalla tappa 14 il resoconto completo va nel registro degli errori, e da
    sorgente anche sulla console, come prima; dal programma compilato no, perché lì lo stderr è già il
    registro e lo scriverebbe due volte. Poi la finestra fa sentire l'allarme e mostra un messaggio;
    se la finestra non c'è più, resta l'allarme. Le eccezioni degli altri fili, come quello
    dell'aggiornamento, vanno soltanto nel registro: non sono un comando di chi gioca.
    """
    import wx

    import registro

    compilato = getattr(sys, "frozen", False)
    precedente, precedente_dei_fili = sys.excepthook, threading.excepthook

    def gancio(tipo, valore, traccia):
        registro.problema(tipo, valore, traccia)
        if not compilato:
            precedente(tipo, valore, traccia)
        if finestra:
            wx.CallAfter(finestra.errore_imprevisto, tipo, valore)
        else:
            suoni.suona("errore_imprevisto")

    def negli_altri_fili(argomenti):
        registro.problema(argomenti.exc_type, argomenti.exc_value, argomenti.exc_traceback)
        if not compilato:
            precedente_dei_fili(argomenti)

    sys.excepthook = gancio
    threading.excepthook = negli_altri_fili


def _in_primo_piano(finestre):
    """Nel filo dell'ascolto: un'altra copia di MESS chiede di aprirsi, e la finestra, se c'è già, torna in primo piano nel suo filo."""
    import wx

    if finestre:
        wx.CallAfter(finestre[0].porta_in_primo_piano)


def _errore_fatale(tipo, valore, traccia):
    """
    L'ultima rete del programma: l'errore che ferma MESS si scrive nel registro, e da sorgente anche
    sulla console; poi lo dicono il suono dell'allarme e un messaggio, che nomina il file del registro.
    """
    import percorsi
    import registro

    registro.problema(tipo, valore, traccia)
    registro.scrivi("MESS si ferma per un errore fatale.")
    if not getattr(sys, "frozen", False):
        traceback.print_exception(tipo, valore, traccia)
    suoni.suona("errore_imprevisto")
    testo = f"MESS si è fermato per un errore imprevisto: {tipo.__name__}, {valore}. {testi.resoconto_degli_errori(percorsi.cartella())}"
    # Senza wx, o senza schermo, resta il registro.
    with contextlib.suppress(Exception):
        import wx

        _app = wx.GetApp() or wx.App(False)
        wx.MessageBox(testo, "MESS si è fermato", wx.OK | wx.ICON_ERROR)


def main():
    """
    L'avvio di MESS. Restituisce il codice d'uscita: zero se tutto è andato bene, anche quando questa
    copia lascia il posto a quella già aperta; uno se il salvataggio non si leggeva o MESS si è fermato
    per un errore.
    """
    import istanza

    # Prima di tutto, anche del registro: un MESS già aperto viene in primo piano, e questa copia non tocca niente.
    if istanza.manda():
        return 0
    finestre = []
    ascolto = istanza.Ascolto(lambda: _in_primo_piano(finestre))
    # La pipe è già presa: un'altra copia è partita nello stesso istante, e ascolta lei.
    if not ascolto.attiva and istanza.manda():
        return 0
    import percorsi
    import registro
    from costanti import VERSIONE

    crash_precedente = registro.avvia(percorsi.cartella())
    registro.scrivi(f"MESS {VERSIONE} si avvia.")
    try:
        riuscito = avvia_finestra(crash_precedente, finestre)
        registro.scrivi("MESS si chiude." if riuscito else "MESS si ferma: il salvataggio non si legge.")
    except Exception:  # noqa: BLE001 - ultima rete del programma: lo scrive, lo dice e chiude
        _errore_fatale(*sys.exc_info())
        riuscito = False
    finally:
        ascolto.ferma()
        registro.chiudi()
    return 0 if riuscito else 1


if __name__ == "__main__":
    sys.exit(main())
