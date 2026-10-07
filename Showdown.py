"""
MESS, Manageriale e Simulatore Showdown: il punto di avvio.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il porting in Python fino alla versione 25.4.24 è di Gabriele Battaglia con Gemini 2.5.
Data concepimento: 13/04/2015 16:13 by Gabriele Battaglia. Porting a Python dal 31/01/2020.
Dal 2026-10-06, con la tappa 2 del piano, il vecchio sd.py è diviso in moduli: qui si crea il
mondo, lo si carica, lo si fa avanzare col tempo trascorso e si apre l'interfaccia. Con la tappa
3, se il salvataggio c'è ma non si legge, il gioco si ferma senza salvare nulla. Con la tappa 5
si apre la finestra; l'interfaccia testuale resta, con l'opzione --testo, per le operazioni che
nella finestra non sono ancora arrivate, e se ne andrà quando le avrà tutte.
Dal 2026-10-07, con la decisione D24, la finestra suona: all'avvio, e quando il salvataggio non
si legge; e un errore imprevisto, che finirebbe soltanto su una console che chi non vede non legge,
ha il suo allarme e un messaggio.
"""

import sys
import traceback

import archivio
import nomi
import suoni
import testi
from cli import InterfacciaTestuale
from mondo import Mondo


def avvia(dopo_creazione=None):
    """
    Crea il mondo, lo carica, lo fa avanzare e apre l'interfaccia testuale fino all'uscita.
    dopo_creazione, se data, riceve il mondo appena creato: serve ai collaudi. Restituisce falso
    se il gioco si è fermato perché il salvataggio non si leggeva.
    """
    mondo = Mondo(notifica=print)
    if dopo_creazione:
        dopo_creazione(mondo)
    nomi.collezioni()
    for avviso in nomi.avvisi:
        print(f"ATT: {avviso}")
    try:
        archivio.carica(mondo)
    except archivio.SalvataggioIllegibile as errore:
        for riga in testi.salvataggio_illeggibile(errore):
            print(riga)
        return False
    mondo.processa_tempo_trascorso()
    InterfacciaTestuale(mondo).run()
    return True


def avvia_finestra():
    """Crea, carica e fa avanzare il mondo, poi apre la finestra fino all'uscita. Falso se il salvataggio non si leggeva."""
    import wx

    from gui.finestra import FinestraPrincipale

    app = wx.App(False)
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
    finestra = FinestraPrincipale(mondo, origine, messaggi, rapporto, ultimo_prima, avvisi_all_avvio=bool(nomi.avvisi))
    _rete_per_gli_errori(finestra)
    finestra.Show()
    wx.CallAfter(finestra.suoni_d_avvio)
    app.MainLoop()
    return True


def _rete_per_gli_errori(finestra):
    """
    Le eccezioni che sfuggono a un comando della finestra: wx le passa a sys.excepthook, che stampa
    la traccia sulla console, e il comando muore in silenzio. La traccia resta dov'era, e in più la
    finestra fa sentire l'allarme e mostra un messaggio; se la finestra non c'è più, resta l'allarme.
    """
    import wx

    precedente = sys.excepthook

    def gancio(tipo, valore, traccia):
        precedente(tipo, valore, traccia)
        if finestra:
            wx.CallAfter(finestra.errore_imprevisto, tipo, valore)
        else:
            suoni.suona("errore_imprevisto")

    sys.excepthook = gancio


def main():
    try:
        riuscito = avvia() if "--testo" in sys.argv[1:] else avvia_finestra()
    except Exception as errore:  # noqa: BLE001 - ultima rete del programma: mostra l'errore e chiude
        print("\n--- ERRORE FATALE ESECUZIONE ---")
        print(f"Tipo: {type(errore).__name__}")
        print(f"Msg: {errore}")
        traceback.print_exc()
        print("\nProgramma terminato.")
        suoni.suona("errore_imprevisto", sync=suoni.ATTESA_USCITA)
        sys.exit(1)
    if not riuscito:
        sys.exit(1)


if __name__ == "__main__":
    main()
