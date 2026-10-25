"""
Gli annunci della cronaca di MESS: le righe della partita dal vivo e della differita lette in automatico,
alla sintesi, al braille o a tutti e due, con GBsintesi di GBUtils.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-21 con la 1.79.0, chiesto da Gabriele prima del collaudo della 1.78.13: il campo della
cronaca cresce riga per riga mentre l'azione suona, ma il fuoco resta sul pulsante, e NVDA non se ne
accorge; con gli annunci ogni riga nuova arriva da sé alla voce e al display. Le scelte stanno nelle
impostazioni, con la chiave annunci_: se leggere, dove, quale sintesi, quante celle ha il display e il
tempo minimo di lettura di ogni blocco.
Alla sintesi le righe si accodano, scelta di Gabriele: ogni riga si legge intera dopo la precedente,
con l'uscita scelta. Al display ogni riga va in blocchi grandi quanto le celle, spezzati fra le parole,
e i blocchi si mostrano in fila, ognuno almeno per il tempo minimo di lettura: è la coda di GBsintesi,
nata in MeTeOra. Il braille ce l'hanno soltanto NVDA e JAWS: con la voce di Windows scelta per la
sintesi, il display riceve le righe dallo screen reader che risponde, con la scelta automatica.
Non conosce wx: chi lo crea gli dà la funzione che pianifica le attese, wx.CallLater nella finestra.
Dal 2026-10-25, richiesta di Gabriele per la barra di stato su misura di D38, c'è anche il testo breve, che va subito alla
sintesi e al display insieme, senza la coda dei blocchi: il nome di un dato quando il cursore ci entra. È di Gabriele
Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

from GBsintesi import AUTOMATICA, CON_IL_BRAILLE, Coda, Sintesi


class Annunci:
    """
    Gli annunci della cronaca. pianifica(secondi, funzione) chiama funzione più tardi, nello stesso
    filo, e restituisce un oggetto con Stop(), come wx.CallLater; sintesi e orologio si possono
    sostituire, e le prove lo fanno.
    """

    def __init__(self, pianifica, sintesi=None, orologio=None):
        self.sintesi = sintesi if sintesi is not None else Sintesi()
        self._impostazioni = None
        if orologio is None:
            self._coda = Coda(self._al_display, pianifica)
        else:
            self._coda = Coda(self._al_display, pianifica, orologio)

    def _uscita_del_braille(self):
        """La sintesi scelta se ha il braille, NVDA o JAWS; altrimenti lo screen reader che risponde."""
        scelta = self._impostazioni["annunci_sintesi"] if self._impostazioni else AUTOMATICA
        return scelta if scelta in CON_IL_BRAILLE else AUTOMATICA

    def _al_display(self, blocco):
        self.sintesi.dici(blocco, self._uscita_del_braille(), "braille")

    def annuncia(self, righe, impostazioni):
        """Le righe nuove della cronaca, secondo le impostazioni valide: niente se la lettura automatica è spenta."""
        if not impostazioni["annunci_cronaca"]:
            return
        self._impostazioni = impostazioni
        dove = impostazioni["annunci_dove"]
        for riga in righe:
            if dove in ("entrambi", "sintesi"):
                self.sintesi.dici(riga, impostazioni["annunci_sintesi"], "sintesi")
            if dove in ("entrambi", "braille"):
                self._coda.aggiungi(riga, impostazioni["annunci_celle"], impostazioni["annunci_lettura_minima"] / 1000)

    def breve(self, testo, impostazioni):
        """
        Un testo breve alla sintesi e al display braille, subito e senza interrompere quello che la sintesi sta dicendo:
        la sintesi è quella scelta per gli annunci, il braille va come quello della cronaca. Non dipende dalla lettura
        automatica della cronaca, che vale soltanto per le partite.
        """
        self._impostazioni = impostazioni
        self.sintesi.dici(testo, impostazioni["annunci_sintesi"], "sintesi")
        self.sintesi.dici(testo, self._uscita_del_braille(), "braille")

    def svuota(self):
        """Toglie dal display le righe ancora in fila: la finestra si è chiusa, e non servono più."""
        self._coda.svuota()

    @property
    def in_fila(self):
        return self._coda.in_fila
