"""
L'elenco virtuale della finestra Mercato e ricerca, con la sua ricerca per lettere iniziali.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 con la decisione D36, dal prototipo strumenti/prova_elenco_virtuale.py, che Gabriele ha
provato lo stesso giorno con NVDA e il display braille: funziona tutto, e la finestra unica usa questo elenco.
È un wx.ListCtrl virtuale nativo di Windows, a una colonna larga quanto l'elenco e senza intestazione, a
selezione singola, che chiede il testo soltanto delle righe che mostra o che qualcuno legge: riempirlo con
ventimila righe costa pochi millesimi, contro quasi due secondi di un ListBox. Le righe si scrivono quando
Windows le chiede e si tengono fino al ricalcolo, salvo per chi le vuole riscritte sempre, come gli
allenatori, la cui riga dice fino a che ora sono riservati a te, che segue l'ora vera.
A ogni freccia l'elenco manda tre eventi, la deselezione con indice -1, il fuoco e la selezione: chi lo usa
ignora il -1. La larghezza della colonna si dà col messaggio di Windows e, quando l'elenco cambia misura, dopo
che l'elenco ha finito di aggiornare le sue barre: altrimenti, quando la barra verticale compare o sparisce,
la colonna resterebbe più larga e comparirebbe quella orizzontale.
Le lettere iniziali le cerca l'elenco stesso, sui nomi che chi lo usa gli dà a ogni ricalcolo, come fa
Windows: le lettere battute entro un secondo l'una dall'altra si sommano, e la stessa lettera ripetuta passa
al nome seguente che comincia così. La ricerca di wx chiederebbe a Python il testo di tutte le righe, e
sulle righe vere si arrende dopo mezzo secondo senza muovere la scelta: la misura del critico della issue 8.
La sera dello stesso giorno, col costruttore di regole, le righe da riscrivere sempre si scelgono una per una, perché
giocatori e allenatori possono stare nello stesso elenco. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
"""

import contextlib
import ctypes
import time
from ctypes import wintypes

import wx

# Entro quanti secondi le lettere iniziali battute di seguito si sommano: un secondo lascia il tempo della
# seconda lettera anche mentre NVDA legge la riga trovata con la prima.
ATTESA_DELLE_LETTERE = 1.0
LVM_SETCOLUMNWIDTH = 0x1000 + 30

# user32 in una copia tutta sua, con la firma che serve qui: l'elenco virtuale è soltanto per Windows.
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendMessageW.restype = ctypes.c_ssize_t
_user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]


class RicercaPerIniziali:
    """
    La ricerca per lettere iniziali di un elenco, come la fa Windows, sui nomi già preparati, in minuscolo. Le
    lettere battute entro attesa secondi l'una dall'altra si sommano e si cerca il nome che comincia così, a
    partire dalla riga col fuoco; la stessa lettera ripetuta cerca invece il nome seguente che comincia con
    quella lettera, a giro. Il primo carattere parte sempre dalla riga dopo quella col fuoco.
    """

    def __init__(self, attesa=ATTESA_DELLE_LETTERE):
        self.attesa = attesa
        self.testo = ""
        self._ultima = float("-inf")

    def in_corso(self, adesso):
        """Vero se una ricerca è aperta: c'è del testo, e l'ultima lettera è arrivata entro l'attesa."""
        return bool(self.testo) and adesso - self._ultima < self.attesa

    def cerca(self, carattere, nomi, quante, da, adesso):
        """L'indice della riga da scegliere fra le prime quante di nomi, partendo da da, la riga col fuoco o -1; None se nessun nome comincia così."""
        if not self.in_corso(adesso):
            self.testo = ""
        self._ultima = adesso
        self.testo += carattere.casefold()
        if not quante:
            return None
        if len(set(self.testo)) == 1:
            cercato, partenza = self.testo[0], da + 1
        else:
            cercato, partenza = self.testo, max(da, 0)
        for passo in range(quante):
            indice = (partenza + passo) % quante
            if nomi[indice].startswith(cercato):
                return indice
        return None


def carattere_della_ricerca(event):
    """Il carattere che il tasto dà alla ricerca per iniziali, o None per i tasti che vanno all'elenco: quelli con Ctrl o Alt, e quelli che non si scrivono."""
    codice = event.GetUnicodeKey()
    if codice == wx.WXK_NONE or codice < 32 or codice == 127 or event.ControlDown() or event.AltDown():
        return None
    return chr(codice)


class ElencoVirtuale(wx.ListCtrl):
    """
    L'elenco virtuale nativo: a una colonna larga quanto l'elenco, senza intestazione, a selezione singola.
    Windows chiede il testo di una riga quando la mostra o quando qualcuno lo legge; la riga si scrive allora,
    con riga(indice), e si tiene fino al ricalcolo, salvo con riscrivi_sempre, che la scrive a ogni domanda. In
    nomi i nomi in minuscolo delle righe, per la ricerca per iniziali, che chi usa l'elenco rifà a ogni
    ricalcolo; in lettere la ricerca. In richieste il numero delle domande di Windows, in scritte quello delle
    righe scritte davvero. Dal costruttore di regole della sera del 24 ottobre 2026 riscrivi_sempre può anche essere
    una funzione dell'indice, vera per le righe da riscrivere a ogni domanda: nella finestra, quelle degli allenatori,
    che nello stesso elenco stanno insieme ai giocatori.
    """

    def __init__(self, genitore, riga, riscrivi_sempre=False, attesa=ATTESA_DELLE_LETTERE):
        super().__init__(genitore, style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        self._riga = riga
        self._righe = []
        self.riscrivi_sempre = riscrivi_sempre
        self.nomi = []
        self.lettere = RicercaPerIniziali(attesa)
        self.richieste = 0
        self.scritte = 0
        self._larghezza_data = None
        self.InsertColumn(0, "")
        self.Bind(wx.EVT_SIZE, self._misura_cambiata)
        self.Bind(wx.EVT_CHAR, self._lettera)

    def OnGetItemText(self, item, col):
        self.richieste += 1
        if not 0 <= item < len(self._righe):
            return ""
        sempre = self.riscrivi_sempre(item) if callable(self.riscrivi_sempre) else self.riscrivi_sempre
        testo = None if sempre else self._righe[item]
        if testo is None:
            testo = self._riga(item)
            self.scritte += 1
            if not sempre:
                self._righe[item] = testo
        return testo

    @property
    def mostrate(self):
        return len(self._righe)

    def mostra(self, quante, posto, nomi=None):
        """quante righe, dimenticando quelle scritte, con la scelta su posto, o sulla prima riga se posto non c'è; con nomi, anche quelli delle iniziali."""
        self._righe = [None] * quante
        if nomi is not None:
            self.nomi = nomi
        self.lettere.testo = ""
        self.SetItemCount(quante)
        if quante:
            self.scegli(posto if posto is not None and 0 <= posto < quante else 0)
        self.Refresh()
        self.adatta_colonna()

    def riscrivi(self):
        """Le righe si riscrivono alla prossima domanda di Windows, con le stesse persone."""
        self._righe = [None] * len(self._righe)
        self.Refresh()

    def col_fuoco(self):
        return self.GetFocusedItem()

    def scegli(self, indice):
        """Fuoco e selezione sulla riga, in un colpo solo, e la riga in vista."""
        stato = wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED
        self.SetItemState(indice, stato, stato)
        self.EnsureVisible(indice)

    def testo(self, indice):
        return self.OnGetItemText(indice, 0)

    def adatta_colonna(self):
        """
        La colonna larga quanto l'elenco, senza misurare le righe, mai due volte la stessa larghezza. Si dà
        col messaggio di Windows e non con SetColumnWidth di wx 3.3, che prima che la finestra si mostri tiene
        da parte le larghezze e alla prima apparizione le rifà una per una, ridisegnando ogni volta: sul PC
        Gigante, con 2.000 righe, l'apertura costava da 310 a 480 millesimi in 15 ridisegni, contro i 55 col
        messaggio. Quando l'elenco cambia misura, la larghezza arriva dopo, con _misura_cambiata.
        """
        larghezza = self.GetClientSize().width
        if larghezza > 0 and larghezza != self._larghezza_data:
            self._larghezza_data = larghezza
            _user32.SendMessageW(self.GetHandle(), LVM_SETCOLUMNWIDTH, 0, larghezza)

    def _misura_cambiata(self, event):
        event.Skip()
        # La nuova misura arriva anche mentre l'elenco aggiorna ancora le sue barre, quando compare o sparisce
        # quella verticale: la larghezza data lì dentro la supera il calcolo di prima, e le frecce sinistra e
        # destra farebbero scorrere l'elenco di lato. Si dà quando ha finito.
        wx.CallAfter(self._adatta_dopo)

    def _adatta_dopo(self):
        # Se nel frattempo l'elenco si è chiuso, non c'è più niente da adattare.
        with contextlib.suppress(RuntimeError):
            self.adatta_colonna()

    def _lettera(self, event):
        """
        Le lettere iniziali le cerca l'elenco, e il tasto non arriva a Windows, che farebbe la sua ricerca. Lo
        Spazio è una lettera soltanto dentro una ricerca aperta; altrimenti, come Ctrl+Spazio e gli altri
        tasti, va all'elenco.
        """
        carattere = carattere_della_ricerca(event)
        adesso = time.monotonic()
        if carattere is None or (carattere == " " and not self.lettere.in_corso(adesso)):
            event.Skip()
            return
        indice = self.lettere.cerca(carattere, self.nomi, self.mostrate, self.col_fuoco(), adesso)
        if indice is not None:
            self.scegli(indice)
