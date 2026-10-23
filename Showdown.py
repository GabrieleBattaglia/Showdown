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
registro degli errori e dei crash accanto al programma, registro.py: un errore imprevisto vi lascia il
suo resoconto completo, e il crash della volta prima la vista lo dice all'apertura. Un errore che
ferma il programma si scrive lì e si dice in un messaggio, col suono dell'allarme. A finestra
comparsa, solo dall'eseguibile compilato, aggiornamento.py controlla se su GitHub c'è una versione
nuova. Le parti della tappa 14 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
Dal 2026-10-23, richiesta di Gabriele, il mondo, lo stato di gioco e le impostazioni stanno nella
cartella del mondo, che si sceglie dal menu Impostazioni, e accanto al programma restano soltanto il
file che dice dove sta e i registri. Prima di caricare il mondo l'avvio controlla la sua cartella: la
predefinita, Mondo, si crea senza domande; una cartella scelta che non c'è, per esempio su una penna
non collegata, ferma l'avvio con un avviso e tre scelte, Riprova, Scegli un'altra cartella ed Esci,
perché un mondo nuovo non deve mai nascere da solo altrove. Poi i dati che le versioni di prova
scrivevano accanto al programma passano nella cartella del mondo, e la vista lo dice. Quando MESS si
riapre sul mondo di un'altra cartella, la copia nuova parte con --attendi e aspetta che la vecchia
sia uscita prima di presentarsi all'istanza unica. Anche queste parti sono di Gabriele Battaglia
(IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dalla revisione dello stesso giorno: avvia_finestra a finestra chiusa restituisce APERTA, e non più un
vero che fra gli ESITI non c'era, e faceva finire ogni chiusura nell'errore fatale; una cartella scelta
che c'è ma non ha un mondo è un problema dell'avvio come quella che manca, salvo dopo il sì a un mondo
nuovo; il salvataggio che non si legge apre l'avviso con Riprova, Scegli un'altra cartella ed Esci,
invece di fermare MESS e basta; e all'avvio non si accetta una cartella dentro i dati accanto al programma.
Con la verifica finale, le copie del salvataggio illeggibile si fanno una volta sola per cartella e non a
ogni Riprova, la notizia dei dati spostati alla prima partenza va subito anche nel registro, e lo
spostamento che non riesce e la cartella rifiutata hanno ciascuno il suo suono. Con l'ultima verifica lo
ha anche il file accanto al programma che non si riesce a scrivere quando si indica un'altra cartella.
Con la verifica seguente lo hanno anche i dati di accanto al programma messi in una riserva della cartella
del mondo, che la notizia porta alla finestra col suo tipo, e la notizia dice se fra quei dati c'era un mondo.
Dal collaudo di gioco di Gabriele, il 24 ottobre 2026, per la regola di un suono per ogni evento, l'errore
che ferma MESS ha il suo suono, errore_fatale, la sirena che crolla come un motore che si spegne: prima
suonava come l'errore che interrompe un comando e lascia MESS aperto, che resta errore_imprevisto. È di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
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

# Come finisce avvia_finestra: la finestra aperta e poi chiusa, il salvataggio che non si legge, la
# cartella del mondo che non c'è e si sceglie di uscire, i dati accanto al programma che non si spostano.
# Per ciascuno il codice d'uscita del programma e la riga del registro.
APERTA = "aperta"
ILLEGGIBILE = "illeggibile"
SENZA_CARTELLA = "senza cartella"
NON_SPOSTATI = "non spostati"
ESITI = {
    APERTA: (0, "MESS si chiude."),
    ILLEGGIBILE: (1, "MESS si ferma: il salvataggio non si legge."),
    SENZA_CARTELLA: (0, "MESS si chiude: la cartella del mondo non c'è."),
    NON_SPOSTATI: (1, "MESS si ferma: i dati accanto al programma non si sono potuti spostare nella cartella del mondo."),
}


def _scegli_all_avvio():
    """
    Scegli un'altra cartella, negli avvisi dell'avvio: la finestra di Windows, e una cartella senza mondo
    soltanto dopo una domanda, perché lì nascerà un mondo nuovo. Restituisce la cartella, se è cambiata,
    altrimenti None. Dalla revisione del 23 ottobre 2026 non si accetta una cartella dentro i dati che le
    versioni di prova tenevano accanto al programma, come la sua cartella tornei: alla partenza seguente
    MESS avrebbe dovuto spostarla dentro sé stessa, e si sarebbe fermato a ogni avvio.
    """
    import wx

    import cartella_del_mondo
    import percorsi
    from gui.dialoghi import scegli_cartella

    suoni.suona("cartella_mondo")
    nuova = scegli_cartella(None, testi.TITOLO_DELLA_SCELTA)
    if nuova is None:
        suoni.suona("annullato")
        return None
    programma = percorsi.cartella_del_programma()
    if cartella_del_mondo.intrecciate(programma, nuova):
        # Dalla verifica finale del 23 ottobre 2026 la cartella rifiutata ha il suo suono, come dal menu.
        suoni.suona("cartella_rifiutata")
        wx.MessageBox(testi.intrecciata_col_programma(nuova, programma), "MESS", wx.OK | wx.ICON_WARNING)
        return None
    if not cartella_del_mondo.ha_un_mondo(nuova):
        suoni.suona("domanda")
        if wx.MessageBox(testi.nessun_mondo_nella_cartella(nuova), "MESS", wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
            suoni.suona("annullato")
            return None
    try:
        percorsi.imposta_cartella(nuova)
    except OSError as errore:
        # Dall'ultima verifica col suo suono, e non più con quello delle impostazioni non salvate.
        suoni.suona("cartella_non_registrata")
        wx.MessageBox(testi.cartella_non_scritta(errore, nuova), "MESS", wx.OK | wx.ICON_ERROR)
        return None
    return nuova


def prepara_la_cartella(accettata=None):
    """
    Prima del mondo, la sua cartella. Finché non c'è, l'avviso col suo suono e le tre scelte: Riprova,
    dopo aver collegato la penna o atteso il cloud; Scegli un'altra cartella; Esci. Dalla revisione del 23
    ottobre 2026 l'avviso viene anche per una cartella scelta che c'è ma non ha un mondo, come quella di
    un cloud non ancora pronto, salvo accettata, la cartella per cui si è appena detto sì a un mondo
    nuovo. Poi i dati della vecchia disposizione, accanto al programma, passano nella cartella del mondo.
    Restituisce la terna di esito, notizia e cartella accettata: l'esito è None se si va avanti,
    altrimenti SENZA_CARTELLA o NON_SPOSTATI; la notizia è la riga della vista sui dati spostati, o None,
    che dalla verifica finale del 23 ottobre 2026 va subito anche nel registro. Dalla verifica seguente la
    notizia dice se fra quei dati c'era un mondo, ed è testi.DatiInRiserva quando sono andati in una riserva
    della cartella del mondo, perché lei aveva già un mondo: la finestra la suona col suono dei dati in riserva.
    """
    import wx

    import cartella_del_mondo
    import percorsi
    import registro
    from gui.dialoghi import ESCI, UN_ALTRA_CARTELLA, CartellaAssente

    while (problema := cartella_del_mondo.problema_della_cartella(accettata)) is not None:
        dialogo = CartellaAssente(None, testi.cartella_assente(problema, isinstance(problema, cartella_del_mondo.SenzaMondo)))
        try:
            suoni.suona("cartella_assente")
            scelta = dialogo.ShowModal()
        finally:
            dialogo.Destroy()
        if scelta == ESCI:
            return SENZA_CARTELLA, None, accettata
        if scelta == UN_ALTRA_CARTELLA:
            accettata = _scegli_all_avvio() or accettata
    try:
        trasloco = cartella_del_mondo.sposta_la_vecchia_disposizione()
    except cartella_del_mondo.SpostamentoNonRiuscito as errore:
        suoni.suona("cartella_non_spostata", sync=suoni.ATTESA_USCITA)
        testo = testi.vecchia_disposizione_non_spostata(errore, percorsi.cartella_del_programma(), percorsi.cartella())
        wx.MessageBox(testo, "MESS", wx.OK | wx.ICON_ERROR)
        return NON_SPOSTATI, None, accettata
    if trasloco is None:
        return None, None, accettata
    in_riserva = not percorsi.stessa(trasloco.destinazione, percorsi.cartella())
    piu_recente = not in_riserva and trasloco.riserva is not None and cartella_del_mondo.ha_un_mondo(trasloco.riserva)
    # Accanto al programma potevano esserci soltanto impostazioni, tornei o cronache. Nella destinazione, la riserva o
    # la cartella del mondo, adesso ci sono soltanto i dati spostati, perché quelli che la cartella aveva sono andati
    # nella sua riserva: se lì c'è un mondo, è arrivato da accanto al programma.
    con_mondo = cartella_del_mondo.ha_un_mondo(trasloco.destinazione)
    notizia = testi.vecchia_disposizione_spostata(trasloco, in_riserva, piu_recente, con_mondo)
    # Anche nel registro, subito: se poi il mondo non si legge e si esce, la vista non la dice mai, e alla
    # partenza seguente non c'è più niente da spostare.
    registro.scrivi(notizia)
    return None, notizia, accettata


def _carica_o_scegli(mondo, accettata, copie=None):
    """
    Carica il mondo. Se il salvataggio c'è ma non si legge, e nemmeno la sua copia, il suono e l'avviso
    con le tre scelte, dalla revisione del 23 ottobre 2026: prima MESS si fermava e basta, e una cartella
    del mondo scelta con un salvataggio illeggibile, per esempio di una versione più recente sull'altro
    computer, lo fermava a ogni avvio senza una via d'uscita dall'app. Restituisce la terna di origine,
    esito e cartella accettata: l'origine del mondo se si è caricato; altrimenti None, con l'esito
    ILLEGGIBILE se si esce, o None se si riprova, anche con un'altra cartella.
    Dalla verifica finale dello stesso giorno, copie va dalla cartella del mondo, in forma confrontabile,
    alla cartella dove sono le copie dei suoi file illeggibili: si fanno soltanto la prima volta per
    quella cartella, o finché non riescono, e non a ogni Riprova, che col cloud si ripete; alle volte
    seguenti l'avviso nomina la cartella delle copie della prima.
    """
    import percorsi
    from gui.dialoghi import ESCI, UN_ALTRA_CARTELLA, MondoIllegibile

    copie = {} if copie is None else copie
    cartella = percorsi.cartella()
    chiave = percorsi.normale(cartella)
    try:
        return archivio.carica(mondo, metti_da_parte=copie.get(chiave) is None), None, accettata
    except archivio.SalvataggioIllegibile as errore:
        if errore.cartella is None:
            errore.cartella = copie.get(chiave)
        else:
            copie[chiave] = errore.cartella
        # Il suono aspetta di finire, come all'uscita, prima della spiegazione.
        suoni.suona("salvataggio_illeggibile", sync=suoni.ATTESA_USCITA)
        dialogo = MondoIllegibile(None, testi.mondo_illeggibile_all_avvio(errore, cartella))
        try:
            scelta = dialogo.ShowModal()
        finally:
            dialogo.Destroy()
    if scelta == ESCI:
        return None, ILLEGGIBILE, accettata
    if scelta == UN_ALTRA_CARTELLA:
        accettata = _scegli_all_avvio() or accettata
    # Al giro seguente la cartella si controlla di nuovo, e il mondo si ricarica in un Mondo nuovo.
    return None, None, accettata


def avvia_finestra(crash_precedente=None, finestre=None):
    """
    Prepara la cartella del mondo, poi crea, carica e fa avanzare il mondo, e apre la finestra fino
    all'uscita. Restituisce uno degli ESITI: APERTA, ILLEGGIBILE se il salvataggio non si leggeva e si è
    scelto di uscire, SENZA_CARTELLA o NON_SPOSTATI. crash_precedente è il resoconto del crash della
    volta prima, che la vista dice all'apertura; finestre, se data, riceve la finestra appena nasce, per
    l'ascolto dell'istanza unica.
    """
    import wx

    import aggiornamento
    from gui.finestra import FinestraPrincipale

    # Una wx.App sola per processo: quella delle prove, se c'è già.
    app = wx.GetApp() or wx.App(False)
    accettata, origine, cartella_spostata = None, None, None
    # Per ogni cartella del mondo con un salvataggio illeggibile, dove sono le copie dei suoi file: si fanno una volta sola.
    copie = {}
    while origine is None:
        esito, notizia, accettata = prepara_la_cartella(accettata)
        if esito is not None:
            return esito
        # I dati accanto al programma si spostano una volta sola: la notizia resta anche se il giro si ripete,
        # e col suo tipo resta anche il suono che la finestra le dà, quello dei dati in riserva o dei dati spostati.
        cartella_spostata = notizia or cartella_spostata
        nomi.collezioni()
        messaggi = []
        mondo = Mondo(notifica=messaggi.append)
        messaggi.extend(f"Attenzione: {avviso}" for avviso in nomi.avvisi)
        origine, esito, accettata = _carica_o_scegli(mondo, accettata, copie)
        if esito is not None:
            return esito
    # L'avanzamento lo racconta la finestra, dal suo riepilogo in numeri.
    mondo.notifica = lambda *_args: None
    ultimo_prima = mondo.datetime_ultimo_run_reale
    rapporto = mondo.processa_tempo_trascorso()
    finestra = FinestraPrincipale(mondo, origine, messaggi, rapporto, ultimo_prima, avvisi_all_avvio=bool(nomi.avvisi),
                                  crash_precedente=crash_precedente, cartella_spostata=cartella_spostata)
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
    return APERTA


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
    sulla console; poi lo dicono il suono dell'errore fatale e un messaggio, che nomina il file del
    registro. Dal collaudo di gioco il suono è suo, non più quello del comando interrotto.
    """
    import percorsi
    import registro

    registro.problema(tipo, valore, traccia)
    registro.scrivi("MESS si ferma per un errore fatale.")
    if not getattr(sys, "frozen", False):
        traceback.print_exception(tipo, valore, traccia)
    suoni.suona("errore_fatale")
    testo = (f"MESS si è fermato per un errore imprevisto: {tipo.__name__}, {valore}. "
             f"{testi.resoconto_degli_errori(percorsi.cartella_del_programma())}")
    # Senza wx, o senza schermo, resta il registro.
    with contextlib.suppress(Exception):
        import wx

        _app = wx.GetApp() or wx.App(False)
        wx.MessageBox(testo, "MESS si è fermato", wx.OK | wx.ICON_ERROR)


def main(argomenti=None):
    """
    L'avvio di MESS. Restituisce il codice d'uscita: zero se tutto è andato bene, anche quando questa
    copia lascia il posto a quella già aperta o si esce perché la cartella del mondo non c'è; uno se il
    salvataggio non si leggeva, i dati accanto al programma non si spostavano o MESS si è fermato per
    un errore. argomenti sono quelli della riga di comando, senza il nome del programma: con --attendi
    e un numero di processo, la copia che si riapre aspetta prima che quel processo sia uscito.
    """
    import istanza

    argomenti = sys.argv[1:] if argomenti is None else argomenti
    da_attendere = istanza.da_attendere(argomenti)
    if da_attendere is not None:
        istanza.aspetta_l_uscita(da_attendere)
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

    # I registri stanno accanto al programma, non nella cartella del mondo, che potrebbe non esserci.
    crash_precedente = registro.avvia(percorsi.cartella_del_programma())
    registro.scrivi(f"MESS {VERSIONE} si avvia.")
    try:
        codice, riga = ESITI[avvia_finestra(crash_precedente, finestre)]
        registro.scrivi(riga)
    except Exception:  # noqa: BLE001 - ultima rete del programma: lo scrive, lo dice e chiude
        _errore_fatale(*sys.exc_info())
        codice = 1
    finally:
        ascolto.ferma()
        registro.chiudi()
    return codice


if __name__ == "__main__":
    sys.exit(main())
