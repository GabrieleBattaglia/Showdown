"""
MESS, l'aggiornamento automatico: all'avvio il controllo con l'auto updater di GBUtils.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-23 con la tappa 14, decisione D34, per il primo rilascio: chi installa la 2.0.0 deve
poter ricevere le versioni seguenti. Lo conduce gestisci_aggiornamento di GBUtils, come in MeTeOra,
Tornello e Terminal Beast: controlla l'ultima release su GitHub e, se è più nuova, la propone con le
note della release; se si accetta la scarica, chiude MESS, che salva il mondo, sostituisce i file e lo
riapre. Solo dall'eseguibile compilato: da sorgente non si fa niente. Il controllo gira in un filo;
la proposta e gli avvisi si portano nel filo della finestra, l'unico che possa aprirli, e il filo
aspetta la risposta. Le poche frasi che GBUtils dice da sé passano da FRASI, che le scrive con gli
accenti veri al posto degli apostrofi e con il nome di MESS.
"""

import sys
import threading

from costanti import VERSIONE

APP = "MESS"
API = "https://api.github.com/repos/GabrieleBattaglia/Showdown/releases/latest"
# Le frasi di gestisci_aggiornamento che con la proposta nella finestra arrivano ancora a chi gioca.
FRASI = {
    "ma il pacchetto non e' ancora pronto.": "ma il pacchetto non è ancora pronto: te la ripropongo a un prossimo avvio.",
    "Aggiornamento pronto, il programma si chiude per applicarlo.": "Aggiornamento scaricato: MESS salva il mondo, si chiude per installarlo e si riapre da solo.",
    "Aggiornamento non riuscito, si prosegue con questa versione.": "Aggiornamento non riuscito: continui con questa versione, e te lo ripropongo al prossimo avvio.",
}


def traduci(testo):
    """Una frase di GBUtils com'è detta in MESS: quelle di FRASI riscritte, le altre con gli accenti al posto degli apostrofi."""
    if testo in FRASI:
        return FRASI[testo]
    for apostrofo, accento in (("e' ", "è "), ("gia'", "già"), ("Novita'", "Novità"), ("perche'", "perché")):
        testo = testo.replace(apostrofo, accento)
    return testo


def controlla(finestra, chiama_dopo=None):
    """
    All'avvio, solo dall'eseguibile compilato, il controllo in un filo. La finestra fa la proposta
    (proponi_l_aggiornamento), dice gli esiti (avvisa_dell_aggiornamento) e l'avanzamento dello
    scaricamento (avanzamento_dell_aggiornamento), e si chiude per farsi sostituire
    (chiudi_per_aggiornare). chiama_dopo porta una funzione nel filo della finestra: wx.CallAfter,
    se non si dice altro. Restituisce il filo, o None se il controllo non parte.
    """
    if not getattr(sys, "frozen", False):
        return None
    try:
        from GBUtils import gestisci_aggiornamento
    except ImportError:
        return None
    if chiama_dopo is None:
        import wx

        chiama_dopo = wx.CallAfter

    def nella_finestra(funzione, *argomenti):
        """Esegue funzione nel filo della finestra e ne aspetta il valore; None se intanto la finestra si è chiusa."""
        esito, fatto = [], threading.Event()

        def lavoro():
            try:
                if finestra and not finestra.chiusa:
                    esito.append(funzione(*argomenti))
            finally:
                fatto.set()

        chiama_dopo(lavoro)
        fatto.wait()
        return esito[0] if esito else None

    def proponi(versione_attuale, versione_nuova, note, attesa=None):
        return bool(nella_finestra(finestra.proponi_l_aggiornamento, versione_attuale, versione_nuova, note, attesa))

    def avvisa(testo):
        nella_finestra(finestra.avvisa_dell_aggiornamento, testo)

    def avanzamento(presi, totale):
        chiama_dopo(finestra.avanzamento_dell_aggiornamento, presi, totale)

    def lavoro():
        if gestisci_aggiornamento(APP, VERSIONE, API, proponi=proponi, avvisa=avvisa, avanzamento=avanzamento, traduci=traduci):
            chiama_dopo(finestra.chiudi_per_aggiornare)

    filo = threading.Thread(target=lavoro, name="MESS, aggiornamento", daemon=True)
    filo.start()
    return filo
