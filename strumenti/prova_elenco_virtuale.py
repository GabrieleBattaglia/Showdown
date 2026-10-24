"""
Il prototipo dell'elenco virtuale della finestra unica Mercato e ricerca, da provare con NVDA e il display braille.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 con la decisione D36, passo 1 della proposta definitiva della issue 8: prima di scrivere
la finestra, Gabriele prova lui l'elenco che la reggerà. È un wx.ListCtrl virtuale nativo di Windows, a una
colonna e senza intestazione, che chiede a MESS il testo soltanto delle righe che mostra: riempirlo con
ventimila righe costa pochi millesimi, contro quasi due secondi del ListBox di oggi. Se la prova con NVDA non va, D36
ripiega sull'elenco di oggi, un wx.ListBox nativo, con un tetto di righe: è la variante --listbox, con le
prime 500 righe e l'etichetta che dice il numero vero dei trovati.
Il mondo è un mondo di prova a regime, fatto in memoria con mondo_a_regime di strumenti/mondi_sintetici.py:
circa ventimila giocatori in attività, tutti nell'elenco, dal valore più alto, con la riga del mercato
della issue 7: nome e cognome, classe, età completa, valore, stipendio, costo e contratto, tratti e numero.
Le cartelle del programma e del mondo sono temporanee, come nelle prove, quindi il mondo vero non si tocca
e alla chiusura non resta niente; nessun suono parte.
La finestra si apre massimizzata e Esc la chiude. In cima le istruzioni brevi, in un campo in sola lettura,
una per riga; poi il campo Nome, cognome o numero, Alt+N, che filtra l'elenco 350 millesimi dopo l'ultimo
tasto, come il resto dei dialoghi di MESS; la casella Righe lunghe, Alt+R, che allunga ogni riga oltre i
300 caratteri e la chiude col numero dei suoi caratteri; l'elenco, Alt+T, che si chiama "Trovati: 20.000"
e cambia nome col numero; Scheda, Alt+H, che mostra la riga col fuoco in un messaggio, come fa anche Invio
sull'elenco; e Chiudi. Il fuoco parte sull'elenco, come partirà nella finestra vera; le istruzioni sono
sopra, con Maiusc+Tab.
Quando il filtro si ferma, il numero dei trovati arriva alla voce e al display con annunci.py, come decide
D36, secondo gli annunci della cronaca di serie: alla sintesi automatica e al braille, display da 40 celle.
Le lettere iniziali nell'elenco le cerca il prototipo sui nomi preparati a ogni ricalcolo, come fa Windows:
le lettere battute entro un secondo l'una dall'altra si sommano, e la stessa lettera ripetuta passa al nome
seguente che comincia così. La ricerca di wx, nell'elenco virtuale, chiede a Python il testo di tutte le
righe, e sulle righe vere si arrende dopo mezzo secondo senza muovere la scelta: la misura del critico. La
stessa ricerca vale anche nella variante --listbox, sulle righe che mostra.
A ogni freccia l'elenco virtuale manda tre eventi, la deselezione con indice -1, il fuoco e la selezione: il
prototipo ignora il -1, e Scheda lavora sulla riga col fuoco e la riseleziona, così anche dopo Ctrl+Spazio,
che toglie la selezione e lascia il fuoco, non lavora sul nulla. Dopo un ricalcolo resta scelta la stessa
persona, se c'è ancora; altrimenti la prima riga.
Come si lancia, dalla cartella dei sorgenti:
python strumenti\\prova_elenco_virtuale.py
python strumenti\\prova_elenco_virtuale.py --listbox
Il mondo di prova si prepara prima che la finestra si apra: sul PC Gigante ci vogliono circa 40 secondi.
Con --attivi si sceglie quanti giocatori in attività, per esempio --attivi 5000 per partire prima; con
--attesa i millesimi entro cui le lettere iniziali si sommano, 1000 di serie. Alla chiusura la console dice
i tempi dell'apertura e dei ricalcoli.
Con --misura il prototipo non mostra niente: apre le due varianti su un desktop di Windows nascosto, le
pilota con una tastiera simulata dentro il processo, scrive i tempi dell'apertura, dei ricalcoli, delle
frecce e delle lettere iniziali, gli eventi di wx e quelli di accessibilità che seguono gli screen reader, e
quanti caratteri di una riga lunga arrivano a chi la chiede all'elenco con buffer di misure diverse; con
--uscita le scrive anche in un file. Serve a confrontare il Gigante, il GPD e l'ufficio: quelle del PC
Gigante del 24 ottobre 2026 stanno in strumenti/prova_elenco_virtuale_gigante.txt.
Le cose da provare con NVDA e il display:
1. Le frecce: su e giù, Pagina su e giù, Inizio e Fine; che cosa leggono la voce e il display a ogni tasto.
2. Le lettere iniziali: una lettera porta al primo nome che comincia così; due o tre lettere di seguito, come r e o, portano a Ro; la stessa lettera ripetuta passa al nome seguente.
3. Il numero della riga: se NVDA dice "x di y", per esempio 1 di 20.000, sull'elenco e dopo le frecce.
4. Ctrl+Spazio: toglie la selezione dalla riga; che cosa dice NVDA, e se Scheda poi mostra ancora quella riga.
5. Una riga lunga: con Righe lunghe spuntata, se la riga arriva intera alla voce e al display, fino a "fine della riga di N caratteri"; Scheda la mostra intera in un messaggio, per confronto.
6. Il nome dell'elenco: dopo un filtro, tornando sull'elenco con Alt+T o col Tab, se NVDA dice il numero nuovo dei trovati.
"""

import argparse
import contextlib
import ctypes
import os
import random
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import mondi_sintetici  # noqa: E402
import wx  # noqa: E402

import annunci as modulo_annunci  # noqa: E402
import impostazioni as modulo_impostazioni  # noqa: E402
import mercato  # noqa: E402
import percorsi  # noqa: E402
import suoni  # noqa: E402
import testi  # noqa: E402
from costanti import ATTRIBUTI_BASE_CON_ALLENABILI, NOME_ATTR_TO_DISPLAY_MAP  # noqa: E402
from economia import valore_di_mercato  # noqa: E402
from gui import dialoghi  # noqa: E402
from modelli import Polisportiva  # noqa: E402

# Il mondo di prova dello studio della issue 8: ventimila attivi, un terzo di ritirati, una polisportiva del
# computer ogni quindici attivi su nove decimi, il seme 31; e l'1% dei tesserati in vendita, come lo ha
# supposto lo studio, perché nell'elenco ci siano anche le righe di chi è in vendita.
ATTIVI = 20_000
SEME = 31
QUOTA_IN_VENDITA = 0.01
NOME_DELLA_PROVA = "Polisportiva della prova"
# Il filtro aspetta 350 millesimi dopo l'ultimo tasto, il ritardo che hanno già i dialoghi di MESS.
RITARDO_DEL_FILTRO = dialoghi.RITARDO_DEL_SUONO_AL_VOLO
# Entro quanti secondi le lettere iniziali battute di seguito si sommano: un secondo lascia il tempo della
# seconda lettera anche mentre NVDA legge la riga trovata con la prima. Si cambia con --attesa.
ATTESA_DELLE_LETTERE = 1.0
# Il tetto delle righe della variante --listbox, quello del ripiego di D36.
TETTO_DEL_LISTBOX = 500
# Le righe lunghe passano questo numero di caratteri.
LUNGHEZZA_DELLE_RIGHE_LUNGHE = 300
TITOLO_VIRTUALE = "Prova dell'elenco virtuale"
TITOLO_NATIVO = "Prova dell'elenco nativo"


def istruzioni(nativo, attivi, tetto=TETTO_DEL_LISTBOX):
    """Le istruzioni brevi della prova, una per riga, per il campo in cima alla finestra."""
    quale = f"nativo di oggi, con le prime {testi.intero(tetto)} righe" if nativo else "virtuale della finestra unica"
    return "\n".join((
        f"Prova dell'elenco {quale}, su un mondo di prova di {testi.intero(attivi)} giocatori in attività: il tuo mondo non si tocca.",
        "Nell'elenco Trovati, Alt+T: frecce, Pagina su e giù, Inizio e Fine.",
        "Le lettere iniziali portano al nome: battute di seguito si sommano, la stessa lettera ripetuta passa al nome seguente.",
        "Ctrl+Spazio toglie la selezione dalla riga; Scheda, Alt+H, o Invio sull'elenco, mostra la riga col fuoco in un messaggio.",
        "Nome, cognome o numero, Alt+N, filtra l'elenco quando smetti di scrivere, e la voce e il display dicono quanti sono i trovati.",
        f"Righe lunghe, Alt+R, allunga ogni riga oltre i {LUNGHEZZA_DELLE_RIGHE_LUNGHE} caratteri, e la riga finisce col numero dei suoi caratteri.",
        "Esc o Chiudi chiudono la prova.",
    ))


# Il mondo di prova e le cartelle temporanee.

@contextlib.contextmanager
def cartelle_temporanee():
    """
    Le cartelle del programma e del mondo temporanee, come la fixture cartella_di_prova delle prove: la
    cartella del programma cambia prima di scrivere il file che dice dove sta quella del mondo, così niente
    arriva alla cartella vera dei sorgenti. Alla fine si torna com'era, e le cartelle si cancellano.
    """
    vera = percorsi.cartella_del_programma
    with tempfile.TemporaryDirectory(prefix="mess_prova_elenco_", ignore_cleanup_errors=True) as radice:
        programma = os.path.join(radice, "programma")
        mondo = os.path.join(radice, "mondo")
        os.makedirs(programma)
        os.makedirs(mondo)
        percorsi.cartella_del_programma = lambda: programma
        try:
            percorsi.imposta_cartella(mondo)
            yield mondo
        finally:
            percorsi.cartella_del_programma = vera


def costruisci_mondo(attivi=ATTIVI, seme=SEME):
    """
    Il mondo di prova a regime, con la polisportiva della prova attiva, tua e vuota, e l'1% dei tesserati del
    computer in vendita al loro valore di mercato. Restituisce il mondo e la polisportiva.
    """
    mondo = mondi_sintetici.mondo_a_regime(attivi, attivi // 3, max(1, int(attivi * 0.9 / 15)), seme)
    poli = Polisportiva(NOME_DELLA_PROVA, None, mondo.datetime_corrente_simulazione)
    mondo.polisportive[poli.nome] = poli
    mondo.miapolisportiva_attiva = poli
    tesserati = sorted(gid for p in mondo.polisportive.values() if p.is_cpu_controlled for gid in p.tesserati)
    for gid in random.Random(f"prova-elenco-{seme}").sample(tesserati, round(len(tesserati) * QUOTA_IN_VENDITA)):
        g = mondo.giocatori[gid]
        mondo.polisportive[g.appartenenza].in_vendita[gid] = valore_di_mercato(g, mondo.datetime_corrente_simulazione)
    return mondo, poli


def riga_lunga(c):
    """
    La riga del mercato allungata oltre i 300 caratteri con le caratteristiche del giocatore, prima del suo
    numero, e chiusa dal numero dei suoi caratteri: chi la legge sa se gli è arrivata intera.
    """
    g = c.giocatore
    coda = f", ID {g.id}"
    parti = [testi.riga_mercato(c).removesuffix(coda)]
    lunghezza = len(parti[0])
    for nome in ATTRIBUTI_BASE_CON_ALLENABILI:
        if lunghezza > LUNGHEZZA_DELLE_RIGHE_LUNGHE:
            break
        parti.append(f"{NOME_ATTR_TO_DISPLAY_MAP[nome]} {testi.numero(g._get_valore_totale(nome))}")
        lunghezza += 2 + len(parti[-1])
    corpo = ", ".join(parti) + coda + ", fine della riga di "
    finale = " caratteri"
    cifre = len(str(len(corpo) + len(finale)))
    while len(str(len(corpo) + len(finale) + cifre)) != cifre:
        cifre += 1
    return f"{corpo}{len(corpo) + len(finale) + cifre}{finale}"


# La ricerca per lettere iniziali.

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


# I due elenchi, con gli stessi metodi.

class ElencoVirtuale(wx.ListCtrl):
    """
    L'elenco virtuale nativo: a una colonna larga quanto l'elenco, senza intestazione, a selezione singola.
    Windows chiede il testo di una riga quando la mostra o quando qualcuno lo legge; la riga si scrive
    allora, con riga(indice), e si tiene fino al ricalcolo. In richieste il numero delle domande di Windows,
    in scritte quello delle righe scritte davvero.
    """

    def __init__(self, genitore, riga):
        super().__init__(genitore, style=wx.LC_REPORT | wx.LC_VIRTUAL | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER)
        self._riga = riga
        self._righe = []
        self.richieste = 0
        self.scritte = 0
        self._larghezza_data = None
        self.InsertColumn(0, "")
        self.Bind(wx.EVT_SIZE, self._misura_cambiata)

    def OnGetItemText(self, item, col):
        self.richieste += 1
        if not 0 <= item < len(self._righe):
            return ""
        testo = self._righe[item]
        if testo is None:
            testo = self._righe[item] = self._riga(item)
            self.scritte += 1
        return testo

    @property
    def mostrate(self):
        return len(self._righe)

    def mostra(self, quante, posto):
        """quante righe, dimenticando quelle scritte, con la scelta su posto, o sulla prima riga se posto non c'è."""
        self._righe = [None] * quante
        self.SetItemCount(quante)
        if quante:
            self.scegli(posto if 0 <= posto < quante else 0)
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
        da parte le larghezze e alla prima apparizione le rifà una per una, ridisegnando ogni volta, e dopo
        ridisegna due volte ogni larghezza nuova: sul PC Gigante, con 2.000 righe, l'apertura costava da 310 a
        480 millesimi in 15 ridisegni, contro i 55 col messaggio. Quando l'elenco cambia misura, la larghezza
        arriva dopo, con _misura_cambiata, e all'apertura costa un ridisegno della pagina in più: sul Gigante,
        il 24 ottobre 2026, una trentina di millesimi, e 116 domande di Windows invece di 78.
        """
        larghezza = self.GetClientSize().width
        if larghezza > 0 and larghezza != self._larghezza_data:
            self._larghezza_data = larghezza
            user32.SendMessageW(self.GetHandle(), LVM_SETCOLUMNWIDTH, 0, larghezza)

    def _misura_cambiata(self, event):
        event.Skip()
        # La nuova misura arriva anche mentre l'elenco aggiorna ancora le sue barre, quando compare o sparisce
        # quella verticale, per un filtro o per la finestra che cambia misura: la larghezza data lì dentro la
        # supera il calcolo di prima, che lascia la barra orizzontale con la colonna larga quanto l'elenco, e
        # le frecce sinistra e destra farebbero scorrere l'elenco di lato. La stessa larghezza ridata dopo,
        # Windows la ignora; e da wx non si distingue quando l'elenco è a metà. Si dà quando ha finito.
        wx.CallAfter(self._adatta_dopo)

    def _adatta_dopo(self):
        # Se nel frattempo l'elenco si è chiuso, non c'è più niente da adattare.
        with contextlib.suppress(RuntimeError):
            self.adatta_colonna()


class ElencoNativo(wx.ListBox):
    """L'elenco nativo di oggi, il ripiego di D36: le prime tetto righe, scritte tutte a ogni ricalcolo."""

    def __init__(self, genitore, riga, tetto=TETTO_DEL_LISTBOX):
        super().__init__(genitore, style=wx.LB_SINGLE)
        self._riga = riga
        self.tetto = tetto
        self._quante = 0
        self.scritte = 0

    @property
    def mostrate(self):
        return min(self._quante, self.tetto)

    def mostra(self, quante, posto):
        self._quante = quante
        righe = [self._riga(i) for i in range(self.mostrate)]
        self.scritte += len(righe)
        self.Set(righe)
        if righe:
            self.SetSelection(posto if 0 <= posto < len(righe) else 0)

    def riscrivi(self):
        posto = self.GetSelection()
        self.mostra(self._quante, posto)

    def col_fuoco(self):
        return self.GetSelection()

    def scegli(self, indice):
        # La riga già scelta non si riseleziona: il ListBox manderebbe di nuovo il fuoco, e NVDA la rileggerebbe.
        if self.GetSelection() != indice:
            self.SetSelection(indice)
        self.EnsureVisible(indice)

    def testo(self, indice):
        return self.GetString(indice)


# La finestra della prova.

class ProvaElenco(dialoghi._Dialogo):
    """
    La finestra della prova: istruzioni, filtro per nome, cognome o numero, righe lunghe, l'elenco dei trovati,
    Scheda e Chiudi. nativo sceglie il ListBox col tetto di righe al posto dell'elenco virtuale. annunci sono
    quelli che dicono i trovati quando il filtro si ferma, di serie quelli di annunci.py alla voce e al display.
    In eventi gli eventi dell'elenco, in misure i tempi dell'apertura e dei ricalcoli, in millesimi.
    """

    def __init__(self, genitore, mondo, poli, nativo=False, annunci=None, attesa_lettere=ATTESA_DELLE_LETTERE, tetto=TETTO_DEL_LISTBOX):
        inizio = time.perf_counter()
        super().__init__(genitore, TITOLO_NATIVO if nativo else TITOLO_VIRTUALE)
        self.mondo = mondo
        self.poli = poli
        self.nativo = nativo
        self.impostazioni = modulo_impostazioni.valide(None)
        self.annunci = annunci if annunci is not None else modulo_annunci.Annunci(lambda secondi, funzione: wx.CallLater(max(1, round(secondi * 1000)), funzione))
        self.lettere = RicercaPerIniziali(attesa_lettere)
        self.eventi = []
        self.ultima_riga = -1
        self.righe_lunghe = False
        self._timer_del_filtro = None
        self.misure = {"candidati": 0.0, "apertura": 0.0, "ricalcoli": []}
        self.tutti = mercato.candidati(mondo, poli, mostra="tutti")
        self.nomi_di_tutti = [testi.nome_completo(c.giocatore).casefold() for c in self.tutti]
        self.numeri_di_tutti = [str(c.giocatore.id) for c in self.tutti]
        self.misure["candidati"] = (time.perf_counter() - inizio) * 1000
        self.visibili = []
        self.nomi = []
        self.posti = {}
        self.etichetta("Istruzioni della prova")
        self.istruzioni = self.aggiungi(wx.TextCtrl(self.pannello, value=istruzioni(nativo, len(self.tutti), tetto), style=wx.TE_MULTILINE | wx.TE_READONLY))
        self.istruzioni.SetMinSize((-1, self.istruzioni.GetCharHeight() * 8))
        self.etichetta("&Nome, cognome o numero")
        self.campo = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PROCESS_ENTER))
        self.lunghe = self.aggiungi(wx.CheckBox(self.pannello, label=f"&Righe lunghe, oltre i {LUNGHEZZA_DELLE_RIGHE_LUNGHE} caratteri"))
        self.etichetta_trovati = self.etichetta("&Trovati")
        if nativo:
            self.elenco = self.aggiungi(ElencoNativo(self.pannello, self.testo_della_riga, tetto), 1)
            self.elenco.Bind(wx.EVT_LISTBOX, lambda event: self._evento("selezionata", event.GetSelection(), event))
            self.elenco.Bind(wx.EVT_LISTBOX_DCLICK, self.scheda)
        else:
            self.elenco = self.aggiungi(ElencoVirtuale(self.pannello, self.testo_della_riga), 1)
            for tipo, nome in ((wx.EVT_LIST_ITEM_DESELECTED, "deselezionata"), (wx.EVT_LIST_ITEM_FOCUSED, "fuoco"), (wx.EVT_LIST_ITEM_SELECTED, "selezionata")):
                self.elenco.Bind(tipo, lambda event, nome=nome: self._evento(nome, event.GetIndex(), event))
            self.elenco.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.scheda)
        # Senza una misura minima, l'elenco chiederebbe di essere alto quanto tutte le sue righe, e scorrerebbe il pannello invece dell'elenco.
        self.elenco.SetMinSize(self.FromDIP(wx.Size(400, 200)))
        self.pulsante_scheda, self.pulsante_chiudi = self.pulsanti((wx.ID_ANY, "Sc&heda"), (wx.ID_CLOSE, "&Chiudi"), predefinito=False)
        self.pulsante_scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.pulsante_chiudi.Bind(wx.EVT_BUTTON, self._chiudi)
        self.campo.Bind(wx.EVT_TEXT, self.filtra_fra_poco)
        self.campo.Bind(wx.EVT_TEXT_ENTER, self._invio_nel_campo)
        self.lunghe.Bind(wx.EVT_CHECKBOX, self._righe_lunghe_cambiate)
        self.elenco.Bind(wx.EVT_CHAR, self._lettera)
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.ricalcola()
        self.misure["ricalcoli"].clear()
        self.completa((760, 560))
        self.elenco.SetFocus()
        # L'apertura conta come un Invio, come nell'invito al caffè: quello della console, rimandato da NVDA, non apre una scheda.
        self.ultimo_invio = dialoghi._adesso()
        self.misure["apertura"] = (time.perf_counter() - inizio) * 1000

    # Le righe.

    def testo_della_riga(self, indice):
        c = self.visibili[indice]
        return riga_lunga(c) if self.righe_lunghe else testi.riga_mercato(c)

    def testo_dei_trovati(self, con_la_lettera=False):
        """Trovati: 20.000; nella variante col tetto, anche quante righe ci sono nell'elenco."""
        testo = f"{'&' if con_la_lettera else ''}Trovati: {testi.intero(len(self.visibili))}"
        if self.nativo and len(self.visibili) > self.elenco.tetto:
            testo += f", nell'elenco i primi {testi.intero(self.elenco.tetto)}"
        return testo

    # Il filtro e il ricalcolo.

    def _indici(self, chiave):
        """Come la scelta del giocatore: il numero si cerca dall'inizio, con quello uguale per primo; il nome per una parte."""
        if not chiave:
            return range(len(self.tutti))
        if chiave.isdigit():
            trovati = [i for i, numero in enumerate(self.numeri_di_tutti) if numero.startswith(chiave)]
            return [i for i in trovati if self.numeri_di_tutti[i] == chiave] + [i for i in trovati if self.numeri_di_tutti[i] != chiave]
        return [i for i, nome in enumerate(self.nomi_di_tutti) if chiave in nome]

    def ricalcola(self):
        """L'elenco col filtro del momento; resta scelta la stessa persona se c'è ancora, altrimenti la prima riga."""
        inizio = time.perf_counter()
        fuoco = self.riga_scelta()
        scelto = self.visibili[fuoco].giocatore.id if fuoco >= 0 else None
        chiave = self.campo.GetValue().strip().casefold()
        indici = self._indici(chiave)
        self.visibili = [self.tutti[i] for i in indici]
        self.nomi = [self.nomi_di_tutti[i] for i in indici]
        self.posti = {c.giocatore.id: posto for posto, c in enumerate(self.visibili)}
        self.lettere.testo = ""
        self.elenco.mostra(len(self.visibili), self.posti.get(scelto, 0))
        self.ultima_riga = self.elenco.col_fuoco()
        self.etichetta_trovati.SetLabel(self.testo_dei_trovati(con_la_lettera=True))
        self.pannello.Layout()
        self.misure["ricalcoli"].append((chiave, len(self.visibili), (time.perf_counter() - inizio) * 1000))

    def filtra_fra_poco(self, event=None):
        """Il ricalcolo 350 millesimi dopo l'ultimo tasto nel campo."""
        if self._timer_del_filtro is not None and self._timer_del_filtro.IsRunning():
            self._timer_del_filtro.Restart(RITARDO_DEL_FILTRO)
        else:
            self._timer_del_filtro = wx.CallLater(RITARDO_DEL_FILTRO, self._filtro_fermo)

    def _filtro_fermo(self):
        # Se nel frattempo la finestra si è chiusa, i suoi controlli non ci sono più.
        with contextlib.suppress(RuntimeError):
            self.ricalcola()
            self.annuncia_i_trovati()

    def annuncia_i_trovati(self):
        """Il numero dei trovati alla voce e al display, al posto di quello di prima se il display lo mostra ancora."""
        self.annunci.svuota()
        self.annunci.annuncia([self.testo_dei_trovati()], self.impostazioni)

    def _invio_nel_campo(self, event=None):
        """Invio nel campo fa subito il ricalcolo in attesa e porta il fuoco sull'elenco."""
        if self._timer_del_filtro is not None and self._timer_del_filtro.IsRunning():
            self._timer_del_filtro.Stop()
            self.ricalcola()
        self.ultimo_invio = dialoghi._adesso()
        self.elenco.SetFocus()

    def _righe_lunghe_cambiate(self, event=None):
        self.righe_lunghe = self.lunghe.GetValue()
        self.elenco.riscrivi()

    # L'elenco: eventi, lettere iniziali, Invio.

    def _evento(self, nome, indice, event):
        """Gli eventi dell'elenco, in ordine; la riga col fuoco si aggiorna, e la deselezione con indice -1 non conta."""
        self.eventi.append((nome, indice))
        if indice >= 0 and nome != "deselezionata":
            self.ultima_riga = indice
        event.Skip()

    def _lettera(self, event):
        """
        Le lettere iniziali le cerca il prototipo, e il tasto non arriva all'elenco, così Windows non fa la sua
        ricerca. Lo Spazio è una lettera soltanto dentro una ricerca aperta; altrimenti, come Ctrl+Spazio e
        gli altri tasti, va all'elenco.
        """
        codice = event.GetUnicodeKey()
        if codice == wx.WXK_NONE or codice < 32 or codice == 127 or event.ControlDown() or event.AltDown():
            event.Skip()
            return
        carattere = chr(codice)
        adesso = time.monotonic()
        if carattere == " " and not self.lettere.in_corso(adesso):
            event.Skip()
            return
        indice = self.lettere.cerca(carattere, self.nomi, self.elenco.mostrate, self.elenco.col_fuoco(), adesso)
        if indice is not None:
            self.elenco.scegli(indice)

    def _tasto(self, event):
        """Invio sull'elenco mostra la scheda della riga, salvo che sia un Invio tenuto giù, anche con NVDA."""
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers() and event.GetEventObject() is self.elenco:
            if not dialoghi.invio_da_ignorare(self, event):
                self.scheda()
            return
        event.Skip()

    def riga_scelta(self):
        """La riga su cui lavorano le azioni: quella col fuoco, o l'ultima che lo ha avuto; -1 se l'elenco è vuoto."""
        indice = self.elenco.col_fuoco()
        if indice < 0:
            indice = self.ultima_riga
        return indice if 0 <= indice < self.elenco.mostrate else -1

    def scheda(self, event=None):
        """La riga col fuoco in un messaggio; la riga torna scelta, così dopo Ctrl+Spazio non si lavora sul nulla."""
        indice = self.riga_scelta()
        if indice < 0:
            wx.MessageBox("L'elenco è vuoto: non c'è nessuna riga da mostrare.", self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        else:
            self.elenco.scegli(indice)
            titolo = f"Riga {testi.intero(indice + 1)} di {testi.intero(self.elenco.mostrate)}"
            wx.MessageBox(self.elenco.testo(indice), titolo, wx.OK | wx.ICON_INFORMATION, self)
        self.ultimo_invio = dialoghi._adesso()

    def _chiudi(self, event=None):
        if self._timer_del_filtro is not None:
            self._timer_del_filtro.Stop()
        self.annunci.svuota()
        self.chiudi(wx.ID_CLOSE)

    def riepilogo(self):
        """I tempi della prova in una frase, per la console alla chiusura."""
        ricalcoli = [ms for _chiave, _trovati, ms in self.misure["ricalcoli"]]
        frase = f"Finestra pronta in {testi.numero(self.misure['apertura'], 0)} ms, di cui {testi.numero(self.misure['candidati'], 0)} per i candidati"
        if ricalcoli:
            frase += (f"; {testi.conta(len(ricalcoli), 'ricalcolo', 'ricalcoli')}, in media {testi.numero(sum(ricalcoli) / len(ricalcoli), 1)} ms, "
                      f"al massimo {testi.numero(max(ricalcoli), 1)} ms")
        return frase + f"; righe scritte {testi.intero(self.elenco.scritte)}."


# La tastiera simulata e le misure sul desktop nascosto.

# user32 in una copia tutta sua, con le firme che servono qui: il prototipo è soltanto per Windows.
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.SendMessageW.restype = ctypes.c_ssize_t
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.GetKeyboardState.restype = wintypes.BOOL
user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
user32.SetKeyboardState.restype = wintypes.BOOL
user32.SetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
user32.MapVirtualKeyW.restype = wintypes.UINT
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x0100, 0x0101, 0x0102
VK_SPACE, VK_PRIOR, VK_NEXT, VK_END, VK_HOME, VK_UP, VK_DOWN = 0x20, 0x21, 0x22, 0x23, 0x24, 0x26, 0x28
VK_ESCAPE, VK_CONTROL, VK_LCONTROL = 0x1B, 0x11, 0xA2
# I tasti estesi, che senza il bit 24 di lParam wx leggerebbe come quelli del tastierino.
ESTESI = frozenset({VK_PRIOR, VK_NEXT, VK_END, VK_HOME, VK_UP, VK_DOWN})


def pompa(volte=500):
    """Smista i messaggi e gli eventi in attesa, anche fuori da un ciclo di wx."""
    ciclo = wx.EventLoopBase.GetActive()
    attivatore = None
    if ciclo is None:
        ciclo = wx.GUIEventLoop()
        attivatore = wx.EventLoopActivator(ciclo)
    applicazione = wx.GetApp()
    try:
        for _ in range(volte):
            if ciclo.Pending():
                ciclo.Dispatch()
            elif applicazione.HasPendingEvents():
                applicazione.ProcessPendingEvents()
            else:
                break
    finally:
        del attivatore


def aspetta(condizione, secondi=2.0):
    """Smista i messaggi finché condizione() è vera, al più per tanti secondi; restituisce l'ultimo valore."""
    fine = time.monotonic() + secondi
    while not condizione() and time.monotonic() < fine:
        pompa()
        time.sleep(0.01)
    return condizione()


def _lparam(vk, su=False):
    lparam = 1 | ((user32.MapVirtualKeyW(vk, 0) & 0xFF) << 16)
    if vk in ESTESI:
        lparam |= 1 << 24
    if su:
        lparam |= (1 << 30) | (1 << 31)
    return lparam


def premi(controllo, vk, ctrl=False):
    """
    Un tasto al controllo, come dalla tastiera ma dentro il processo: lo stato dei tasti del filo dice Ctrl
    se serve, e i messaggi vanno al controllo con SendMessage. Niente arriva allo schermo vero.
    """
    hwnd = controllo.GetHandle()
    prima = (ctypes.c_ubyte * 256)()
    user32.GetKeyboardState(prima)
    stato = (ctypes.c_ubyte * 256)(*prima)
    if ctrl:
        stato[VK_CONTROL] = stato[VK_LCONTROL] = 0x80
    stato[vk] = 0x80
    try:
        user32.SetKeyboardState(stato)
        user32.SendMessageW(hwnd, WM_KEYDOWN, vk, _lparam(vk))
        if vk == VK_SPACE:
            user32.SendMessageW(hwnd, WM_CHAR, 0x20, _lparam(vk))
        pompa()
        stato[vk] = 0
        user32.SetKeyboardState(stato)
        user32.SendMessageW(hwnd, WM_KEYUP, vk, _lparam(vk, su=True))
        pompa()
    finally:
        user32.SetKeyboardState(prima)


def batti(controllo, carattere):
    """Un carattere al controllo, come un tasto battuto: la lettera arriva con WM_CHAR."""
    user32.SendMessageW(controllo.GetHandle(), WM_CHAR, ord(carattere), 1)
    pompa()


def posta_esc(controllo):
    """Esc nella coda dei messaggi del controllo, come dalla tastiera: lo prende il ciclo che gira, anche quello di ShowModal."""
    hwnd = controllo.GetHandle()
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_ESCAPE, _lparam(VK_ESCAPE))
    user32.PostMessageW(hwnd, WM_KEYUP, VK_ESCAPE, _lparam(VK_ESCAPE, su=True))


class LVITEMW(ctypes.Structure):
    _fields_ = (("mask", wintypes.UINT), ("iItem", ctypes.c_int), ("iSubItem", ctypes.c_int), ("state", wintypes.UINT), ("stateMask", wintypes.UINT),
                ("pszText", ctypes.c_void_p), ("cchTextMax", ctypes.c_int), ("iImage", ctypes.c_int), ("lParam", wintypes.LPARAM), ("iIndent", ctypes.c_int),
                ("iGroupId", ctypes.c_int), ("cColumns", wintypes.UINT), ("puColumns", ctypes.c_void_p), ("piColFmt", ctypes.c_void_p), ("iGroup", ctypes.c_int))


LVM_SETCOLUMNWIDTH = 0x1000 + 30
LVM_GETITEMTEXTW = 0x1000 + 115
LB_GETTEXTLEN = 0x018A


def testo_letto(elenco, indice, buffer=260):
    """
    Il testo della riga come lo riceve chi lo chiede all'elenco virtuale da fuori, come fanno gli screen
    reader: con LVM_GETITEMTEXT e un buffer di tanti caratteri, compreso quello che chiude il testo.
    """
    testo = ctypes.create_unicode_buffer(buffer)
    voce = LVITEMW(iSubItem=0, pszText=ctypes.addressof(testo), cchTextMax=buffer)
    lunghezza = user32.SendMessageW(elenco.GetHandle(), LVM_GETITEMTEXTW, indice, ctypes.addressof(voce))
    return testo.value[:lunghezza]


def caratteri_letti(elenco, indice, buffer=260):
    """Quanti caratteri della riga arrivano a chi la chiede all'elenco: col buffer dato per l'elenco virtuale, con LB_GETTEXTLEN per il ListBox."""
    if isinstance(elenco, wx.ListBox):
        return user32.SendMessageW(elenco.GetHandle(), LB_GETTEXTLEN, indice, 0)
    return len(testo_letto(elenco, indice, buffer))


WINEVENTPROC = ctypes.WINFUNCTYPE(None, wintypes.HANDLE, wintypes.DWORD, wintypes.HWND, wintypes.LONG, wintypes.LONG, wintypes.DWORD, wintypes.DWORD)
NOMI_DEGLI_EVENTI = {0x8000: "creazione", 0x8001: "distruzione", 0x8002: "mostra", 0x8003: "nasconde", 0x8004: "riordino", 0x8005: "fuoco",
                     0x8006: "selezione", 0x8007: "selezione aggiunta", 0x8008: "selezione tolta", 0x8009: "selezione interna", 0x800A: "stato",
                     0x800C: "nome", 0x800D: "descrizione", 0x800E: "valore"}


class EventiDiAccessibilita:
    """
    Gli eventi di accessibilità che un controllo manda agli screen reader, presi con SetWinEventHook fuori
    contesto sul processo: arrivano quando il filo smista i suoi messaggi. Il cambio di posto non si annota.
    """

    def __init__(self, controllo):
        self.hwnd = controllo.GetHandle()
        self.eventi = []
        self._richiamo = WINEVENTPROC(self._arrivato)
        user32.SetWinEventHook.restype = wintypes.HANDLE
        user32.SetWinEventHook.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HMODULE, WINEVENTPROC, wintypes.DWORD, wintypes.DWORD, wintypes.UINT]
        user32.UnhookWinEvent.argtypes = [wintypes.HANDLE]
        self._gancio = user32.SetWinEventHook(0x8000, 0x800E, None, self._richiamo, os.getpid(), 0, 0)

    def _arrivato(self, _gancio, evento, hwnd, oggetto, figlio, _filo, _quando):
        if hwnd == self.hwnd and evento in NOMI_DEGLI_EVENTI:
            self.eventi.append((NOMI_DEGLI_EVENTI[evento], figlio if oggetto == 0 or oggetto == -4 else f"{oggetto}/{figlio}"))

    def chiudi(self):
        if self._gancio:
            user32.UnhookWinEvent(self._gancio)
            self._gancio = None


def passa_al_desktop_nascosto():
    """
    Il filo principale passa su un desktop di Windows tutto suo, che nessuno vede, prima di creare qualunque
    finestra, come fanno le prove in tests/conftest.py: altrimenti una finestra della misura prenderebbe il
    primo piano e NVDA ne leggerebbe il titolo. Se non riesce, la misura non parte.
    """
    user32.CreateDesktopW.restype = wintypes.HANDLE
    user32.CreateDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    user32.SetThreadDesktop.restype = wintypes.BOOL
    user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
    desktop = user32.CreateDesktopW(f"mess_prova_elenco_{os.getpid()}", None, None, 0, 0x10000000, None)
    if not desktop or not user32.SetThreadDesktop(desktop):
        sys.exit(f"Il desktop nascosto non è disponibile, errore di Windows {ctypes.get_last_error()}: la misura non parte.")
    return desktop


class SintesiMuta:
    """La sintesi delle misure: annota ciò che direbbe, alla voce o al display, e non dice niente."""

    def __init__(self):
        self.detti = []

    def dici(self, testo, chiave="automatica", dove="entrambi", interrompi=False):
        self.detti.append((dove, testo))
        return True


def _tempo(funzione):
    inizio = time.perf_counter()
    funzione()
    return (time.perf_counter() - inizio) * 1000


def _serie(tempi):
    ordinati = sorted(tempi)
    return f"media {testi.numero(sum(tempi) / len(tempi), 2)} ms, mediana {testi.numero(ordinati[len(ordinati) // 2], 2)} ms, massimo {testi.numero(ordinati[-1], 2)} ms"


def misura_variante(mondo, poli, nativo, scrivi):
    """Apre una variante sul desktop nascosto e scrive i suoi tempi, i suoi eventi e le righe chieste."""
    nome = "ListBox" if nativo else "Elenco virtuale"
    sintesi = SintesiMuta()
    annunci = modulo_annunci.Annunci(lambda secondi, funzione: wx.CallLater(max(1, round(secondi * 1000)), funzione), sintesi=sintesi)
    inizio = time.perf_counter()
    dialogo = ProvaElenco(None, mondo, poli, nativo=nativo, annunci=annunci)
    costruita = (time.perf_counter() - inizio) * 1000
    dialogo.Show()
    pompa()
    mostrata = (time.perf_counter() - inizio) * 1000
    elenco = dialogo.elenco
    richieste = getattr(elenco, "richieste", None)
    scrivi(f"{nome}, apertura con {testi.intero(len(dialogo.visibili))} trovati: finestra pronta in {testi.numero(costruita, 1)} ms, di cui "
           f"{testi.numero(dialogo.misure['candidati'], 1)} per i candidati; mostrata e disegnata in {testi.numero(mostrata, 1)} ms; "
           f"righe scritte {testi.intero(elenco.scritte)}" + (f", domande di Windows {testi.intero(richieste)}" if richieste is not None else "") + ".")
    tempo = _tempo(lambda: (dialogo.Restore(), pompa(), dialogo.Maximize(), pompa()))
    colonna = "" if nativo else f", colonna larga {elenco.GetColumnWidth(0)} pixel su {elenco.GetClientSize().width}"
    scrivi(f"{nome}, finestra ripristinata e di nuovo massimizzata in {testi.numero(tempo, 1)} ms{colonna}.")
    sentinella = EventiDiAccessibilita(elenco)
    try:
        elenco.SetFocus()
        elenco.scegli(0)
        pompa()
        dialogo.eventi.clear()
        sentinella.eventi.clear()
        premi(elenco, VK_DOWN)
        scrivi(f"{nome}, una freccia giù dalla prima riga: riga col fuoco {elenco.col_fuoco()}, eventi di wx {dialogo.eventi}, eventi di accessibilità {sentinella.eventi}.")
        tempi, domande, scritte = [], [], []
        for _ in range(200):
            prima_r, prima_s = getattr(elenco, "richieste", 0), elenco.scritte
            tempi.append(_tempo(lambda: premi(elenco, VK_DOWN)))
            domande.append(getattr(elenco, "richieste", 0) - prima_r)
            scritte.append(elenco.scritte - prima_s)
        scrivi(f"{nome}, 200 frecce giù: {_serie(tempi)}; per freccia in media {testi.numero(sum(domande) / len(domande), 1)} domande di Windows e "
               f"{testi.numero(sum(scritte) / len(scritte), 2)} righe scritte; riga col fuoco {elenco.col_fuoco()}.")
        for tasto, parola in ((VK_NEXT, "Pagina giù"), (VK_END, "Fine"), (VK_PRIOR, "Pagina su"), (VK_HOME, "Inizio")):
            prima_r = getattr(elenco, "richieste", 0)
            sentinella.eventi.clear()
            tempo = _tempo(lambda tasto=tasto: premi(elenco, tasto))
            scrivi(f"{nome}, {parola}: {testi.numero(tempo, 2)} ms, riga col fuoco {elenco.col_fuoco()}, domande di Windows {getattr(elenco, 'richieste', 0) - prima_r}, "
                   f"eventi di accessibilità {len(sentinella.eventi)}.")
        dialogo.eventi.clear()
        premi(elenco, VK_DOWN, ctrl=True)
        premi(elenco, VK_DOWN, ctrl=True)
        scrivi(f"{nome}, due Ctrl+freccia giù dalla prima riga: riga col fuoco {elenco.col_fuoco()}, eventi di wx {dialogo.eventi}.")
        elenco.scegli(1)
        pompa()
        dialogo.eventi.clear()
        sentinella.eventi.clear()
        premi(elenco, VK_SPACE, ctrl=True)
        dopo_lo_spazio = (elenco.col_fuoco(), elenco.GetFirstSelected() if not nativo else elenco.GetSelection())
        scrivi(f"{nome}, Ctrl+Spazio sulla seconda riga: fuoco e selezione {dopo_lo_spazio}, eventi di wx {dialogo.eventi}, eventi di accessibilità {sentinella.eventi}; "
               f"la riga delle azioni resta la {dialogo.riga_scelta()}.")
        misura_lettere(dialogo, nome, scrivi, sentinella)
        misura_ricalcoli(dialogo, nome, scrivi, sintesi)
        misura_righe_lunghe(dialogo, nome, scrivi)
    finally:
        sentinella.chiudi()
        dialogo.Destroy()
        pompa()


def misura_lettere(dialogo, nome, scrivi, sentinella):
    """Le lettere iniziali: la prima, due di seguito, la stessa ripetuta, e una lettera che porta in fondo all'elenco."""
    elenco = dialogo.elenco
    quante = elenco.mostrate
    iniziali = [n[:1] for n in dialogo.nomi[:quante]]
    # La lettera più rara, la cui prima riga sta più in basso: il caso peggiore per chi cerca dall'inizio.
    ultima = max(set(iniziali), key=lambda lettera: iniziali.index(lettera))
    for parola, lettere in ((f"la lettera {ultima}, la cui prima riga sta più in basso", ultima), ("r e o di seguito", "ro"), ("tre volte m", "mmm")):
        elenco.scegli(0)
        pompa()
        dialogo.lettere.testo = ""
        sentinella.eventi.clear()
        prima_r = getattr(elenco, "richieste", 0)
        tempi = []
        for lettera in lettere:
            tempi.append(_tempo(lambda lettera=lettera: batti(elenco, lettera)))
        fuoco = elenco.col_fuoco()
        letto = dialogo.nomi[fuoco] if fuoco >= 0 else None
        scrivi(f"{nome}, {parola} dalla prima riga: riga {fuoco}, {letto!r}; tempo per lettera {', '.join(testi.numero(t, 2) for t in tempi)} ms; "
               f"domande di Windows {getattr(elenco, 'richieste', 0) - prima_r}; eventi di accessibilità {sentinella.eventi}.")


def misura_ricalcoli(dialogo, nome, scrivi, sintesi):
    """I ricalcoli col filtro, chiamati subito, e uno col ritardo vero dopo l'ultimo tasto, con l'annuncio."""
    elenco = dialogo.elenco
    persona = dialogo.visibili[elenco.col_fuoco()].giocatore if elenco.col_fuoco() >= 0 else None
    cognome = persona.cognome.casefold() if persona is not None else "rossi"
    for chiave in ("a", cognome, "", "ro", "ros", "12", "1234", "zzz", ""):
        dialogo.campo.ChangeValue(chiave)
        tempo = _tempo(lambda: (dialogo.ricalcola(), pompa()))
        fuoco = elenco.col_fuoco()
        resta = persona is not None and fuoco >= 0 and dialogo.visibili[fuoco].giocatore is persona
        scrivi(f"{nome}, ricalcolo col filtro {chiave!r}: {testi.intero(len(dialogo.visibili))} trovati, ricalcolati e ridisegnati in {testi.numero(tempo, 1)} ms; "
               f"la stessa persona {'resta scelta' if resta else 'non resta scelta'}; etichetta {dialogo.etichetta_trovati.GetLabel()!r}.")
    sintesi.detti.clear()
    prima = len(dialogo.misure["ricalcoli"])
    inizio = time.perf_counter()
    for lettera in "ross":
        dialogo.campo.AppendText(lettera)
    pronto = aspetta(lambda: len(dialogo.misure["ricalcoli"]) > prima and sintesi.detti)
    attesa = (time.perf_counter() - inizio) * 1000
    scrivi(f"{nome}, quattro lettere nel campo: ricalcolo e annuncio {'arrivati' if pronto else 'non arrivati'} dopo {testi.numero(attesa, 0)} ms; annunci {sintesi.detti}.")
    dialogo.campo.ChangeValue("")
    dialogo.ricalcola()


def misura_righe_lunghe(dialogo, nome, scrivi):
    """Le righe lunghe: il tempo per riscriverle, quanto sono lunghe, e quanti caratteri arrivano a chi le legge."""
    elenco = dialogo.elenco
    dialogo.lunghe.SetValue(True)
    tempo = _tempo(lambda: (dialogo._righe_lunghe_cambiate(), pompa()))
    lunghezze = [len(elenco.testo(i)) for i in range(min(50, elenco.mostrate))]
    letti = ", ".join(f"buffer {b}: {caratteri_letti(elenco, 0, b)}" for b in (260, 1024, 4096)) if not dialogo.nativo else f"LB_GETTEXTLEN {caratteri_letti(elenco, 0)}"
    scrivi(f"{nome}, righe lunghe: riscritte e ridisegnate in {testi.numero(tempo, 1)} ms; le prime 50 da {min(lunghezze)} a {max(lunghezze)} caratteri; "
           f"della prima, di {len(elenco.testo(0))} caratteri, arrivano a chi legge l'elenco: {letti}.")
    dialogo.lunghe.SetValue(False)
    dialogo._righe_lunghe_cambiate()


def misura(mondo, poli, uscita=None):
    """Le misure delle due varianti, sul desktop nascosto già scelto, a console e, se si dà, in un file."""
    righe = []

    def scrivi(testo):
        righe.append(testo)
        print(testo, flush=True)

    scrivi(f"wxPython {wx.version()}, Python {sys.version.split()[0]}, computer {os.environ.get('COMPUTERNAME', '?')}.")
    # La prima finestra del processo paga anche l'avvio dei controlli di Windows: si misura a parte, così le
    # due varianti si confrontano alla pari, come si apriranno nel programma, che ha già la sua finestra.
    inizio = time.perf_counter()
    prima = ProvaElenco(None, mondo, poli, annunci=modulo_annunci.Annunci(lambda secondi, funzione: wx.CallLater(max(1, round(secondi * 1000)), funzione), sintesi=SintesiMuta()))
    prima.Show()
    pompa()
    scrivi(f"La prima finestra del processo, con l'elenco virtuale: pronta, mostrata e disegnata in {testi.numero((time.perf_counter() - inizio) * 1000, 1)} ms.")
    prima.Destroy()
    pompa()
    for nativo in (False, True):
        misura_variante(mondo, poli, nativo, scrivi)
    if uscita:
        Path(uscita).write_text("\n".join(righe) + "\n", encoding="utf-8")


def leggi_opzioni(argomenti=None):
    parser = argparse.ArgumentParser(description="Il prototipo dell'elenco virtuale della finestra unica di MESS, da provare con NVDA.")
    parser.add_argument("--listbox", action="store_true", help="la variante di ripiego: il ListBox nativo di oggi con le prime 500 righe")
    parser.add_argument("--attivi", type=int, default=ATTIVI, help="quanti giocatori in attività ha il mondo di prova, 20000 di serie")
    parser.add_argument("--seme", type=int, default=SEME, help="il seme del mondo di prova, 31 di serie")
    parser.add_argument("--attesa", type=int, default=round(ATTESA_DELLE_LETTERE * 1000), help="entro quanti millesimi le lettere iniziali si sommano, 1000 di serie")
    parser.add_argument("--misura", action="store_true", help="le misure delle due varianti su un desktop nascosto, senza mostrare niente")
    parser.add_argument("--uscita", help="con --misura, il file in cui scrivere anche le misure")
    return parser.parse_args(argomenti)


def main(argomenti=None):
    opzioni = leggi_opzioni(argomenti)
    if opzioni.misura:
        passa_al_desktop_nascosto()
    with cartelle_temporanee():
        suoni.imposta_volume(0)
        print(f"Preparo il mondo di prova con {testi.intero(opzioni.attivi)} giocatori in attività: sul PC Gigante, con ventimila, ci vogliono circa 40 secondi.", flush=True)
        inizio = time.perf_counter()
        mondo, poli = costruisci_mondo(opzioni.attivi, opzioni.seme)
        print(f"Il mondo di prova è pronto in {testi.numero(time.perf_counter() - inizio, 1)} secondi.", flush=True)
        app = wx.App(False)
        try:
            if opzioni.misura:
                misura(mondo, poli, opzioni.uscita)
                return
            dialogo = ProvaElenco(None, mondo, poli, nativo=opzioni.listbox, attesa_lettere=opzioni.attesa / 1000)
            try:
                dialogo.ShowModal()
                print(f"Prova chiusa. {dialogo.riepilogo()}", flush=True)
            finally:
                dialogo.Destroy()
        finally:
            for finestra in wx.GetTopLevelWindows():
                finestra.Destroy()
            del app


if __name__ == "__main__":
    main()
