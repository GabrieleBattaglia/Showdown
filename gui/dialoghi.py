"""
I dialoghi della finestra di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano. Ogni dialogo segue lo schema di GBwx: stile
adattabile, controlli in un pannello che scorre, misura presa dal contenuto, così i caratteri
grandi non lasciano niente fuori dallo schermo. Solo controlli nativi a selezione singola, e
ogni campo ha davanti la sua etichetta, da cui lo screen reader prende il nome.
Dalla tappa 7 ci sono i dialoghi delle polisportive: fondazione, cambio, password, e il mercato
della decisione D20, che usa la ricerca come filtro e chiede conferma prima di ogni offerta,
perché un'offerta costa una mossa e non si ritira.
Dalla tappa 8 c'è l'economia della decisione D22: al mercato si offre un ingaggio ai liberi, si
compra chi è in vendita e si fa un'offerta d'acquisto per i tesserati del computer, scegliendo la
cifra in un dialogo che, per l'ingaggio, dice anche la probabilità che il giocatore accetti; poi
ci sono i dialoghi per pagare gli arretrati, a chi e quanto, e per mettere in vendita i tesserati.
Dal 2026-10-07, con la decisione D24, i dialoghi suonano: ogni esito ha il suo effetto, gli avvisi
che lasciano aperto il dialogo dicono a orecchio di che errore si tratta, e un elenco che si svuota
o torna pieno mentre si scrive lo fa sentire, perché lo screen reader non lo legge. Il suono
sostituisce il campanello di Windows, che diceva soltanto che qualcosa non andava. C'è anche il
dialogo del volume degli effetti, che fa sentire il suono di prova a ogni ritocco.
Dal 2026-10-08, con l'amichevole della tappa 9, c'è il dialogo delle sue opzioni, scelte di
Gabriele: al meglio di 3 o di 5 set, come seguire l'incontro e il livello della cronaca, che è
anche quello del file della cronaca. La scelta dei due giocatori usa la scelta del giocatore di
sempre, con l'elenco ristretto a chi oggi può giocare. Con la decisione D29 i modi diventano
Assisti e Vai alla fine, e arriva il dialogo della velocità di gioco; la finestra dal vivo sta in
gui/dal_vivo.py.
Dal 2026-10-09, con la tappa 11 e la decisione D31, ci sono la sala allenamento e i contratti. Nella
sala si spendono i punti allenamento dei tesserati, a mano su una caratteristica o tutti secondo il
programma, e si scelgono programma e intensità; nei contratti si propongono i rinnovi, con il tic
della probabilità come al mercato. La spiegazione dell'ingaggio comincia con il contratto che il
giocatore propone. Le domande sì o no dei dialoghi nascono tutte da _conferma, con il no già scelto.
Le parti della tappa 11 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dalla tappa 12, il 2026-10-14, decisione D32 e punto 12.4 del progetto, la sala allenamento ha la
casella dell'iscrizione automatica ai tornei dell'allenando scelto, che vale subito e si conta fra i
cambi della chiusura, e l'allenando dice anche l'acciacco. I dialoghi dei tornei stanno in
gui/tornei.py e gui/editor_tornei.py, quelli delle sfide in gui/sfide.py. Le parti della tappa 12 sono
di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Dalla tappa 13, il 2026-10-21, decisione D33 e capitolo 4 del progetto, ci sono lo staff della
polisportiva, coi tre posti, il rinnovo, il licenziamento e l'assunzione, e il mercato degli allenatori,
coi filtri e l'offerta d'ingaggio. Le parti della tappa 13 sono di Gabriele Battaglia (IZ4APU) &
ClaudIA (Claude Opus 5.5, UltraCode).
Dalla tappa 14, il 2026-10-23, la fondazione chiede anche la sede, un comune cercato per nome in un elenco
che si restringe mentre si scrive. Le parti della tappa 14 sono di Gabriele Battaglia (IZ4APU) & ClaudIA
(Claude Opus 5.5, modalità auto). Con la decisione D34 arriva la proposta dell'aggiornamento automatico,
con le note della release, che allo scadere dell'attesa si chiude da sola come Non adesso; questa parte
è di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode). Dal collaudo di Gabriele del 23
ottobre 2026 tutti i dialoghi si aprono massimizzati, come la finestra principale, ed Esc preme il loro
pulsante Chiudi, se ce l'hanno: le due regole stanno in _Dialogo.completa, da cui passano tutti, così
valgono anche per i dialoghi che verranno. Anche questa parte è di Gabriele Battaglia (IZ4APU) & ClaudIA
(Claude Opus 5.5, UltraCode). Con la cartella del mondo, chiesta da Gabriele lo stesso giorno, arrivano
la finestra di Windows che sceglie una cartella, wx.DirDialog nativa e accessibile, la domanda quando la
cartella scelta ha già un mondo e l'avviso dell'avvio quando la cartella non c'è, con le scelte di
Riprova, di un'altra cartella e di Esci; anche questa parte è di Gabriele Battaglia (IZ4APU) & ClaudIA
(Claude Opus 5.5, UltraCode). Dalla revisione dello stesso giorno le stesse tre scelte valgono anche per
il salvataggio che all'avvio non si legge, MondoIllegibile; la domanda col mondo già presente non offre di
usarlo quando non si legge; e in questi dialoghi Invio nel testo vale il predefinito, ma tenuto giù no.
Dal collaudo di gioco di Gabriele, il 24 ottobre 2026, per la regola di un suono per ogni evento: nella
fondazione la sede che non corrisponde a nessun comune è un campo da correggere, e ne ha il suono, non più
quello di un pulsante premuto senza niente di scelto; nella sala allenamento Allena tutti con i tesserati
tutti infortunati lo dice, col suo suono, allenandi_tutti_infortunati, e quando a chi si allena non sale
niente dice che ha tutto al massimo, invece di dire per tutti e due che nessuno ha un punto da spendere.
Con le verifiche dello stesso collaudo quell'avviso parla soltanto di chi si allena e ha almeno un punto da
spendere, al femminile e al singolare come quello degli infortunati.
È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, con la finestra Mercato e ricerca della decisione D36, due regole passano nella base di tutti i
dialoghi. Un dialogo che conferma con Invio, la scelta del giocatore, la cifra e le opzioni dell'amichevole, conta
la sua apertura come un Invio, e ignora gli Invio che arrivano entro la grazia: NVDA rimanda Invio come pressioni
nuove, e un Invio tenuto giù sulla voce di menu sceglieva il primo giocatore e giocava un'amichevole che nessuno
aveva scelto. E la pressione di un pulsante che si ripete entro mezzo secondo, un tasto tenuto giù, si ignora con
_ripetuta, che arriva dal calendario dei tornei. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, coi collegamenti della finestra, escono il dialogo del mercato dei giocatori, quello del mercato degli
allenatori e quello della ricerca, che vivono nella finestra Mercato e ricerca, in gui/mercato_e_ricerca.py: Assumi dello
staff apre lei, sugli allenatori liberi col posto già scelto, e lo staff tiene le offerte agli allenatori fra i suoi esiti
e il resto fra quelli della finestra. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import contextlib
import os
import time
import webbrowser

import wx
from GBwx import STILE_ADATTABILE, adatta_finestra, pannello_scorrevole

import allenamento
import contratti
import economia
import impostazioni as modulo_impostazioni
import luoghi
import partita_sonora
import staff
import suoni
import testi
from costanti import (
    INDOLI,
    INTENSITA,
    MESI_CONTRATTO_MAX,
    MESI_CONTRATTO_MIN,
    NOME_POLISPORTIVA_MAX,
    NOME_POLISPORTIVA_MIN,
    SET_AMMESSI,
    STIPENDIO_MINIMO,
)
from gui import aspetto
from modelli import normalizza_nome
from motore import cronaca

PAYPAL_URL = "https://paypal.me/GabrieleBattaglia780"
# Quanto aspettano, dopo l'ultima cifra scritta o l'ultima freccia, il suono di prova del volume e il
# tic della probabilità d'ingaggio: così non suonano a ogni cifra.
RITARDO_DEL_SUONO_AL_VOLO = 350
# I due modi di seguire un'amichevole della decisione D29, con le parole del dialogo delle opzioni; il
# primo è il predefinito. Assisti apre la finestra dal vivo, Vai alla fine mostra il risultato e la cronaca.
ASSISTI = "assisti"
VAI_ALLA_FINE = "fine"
MODI_DI_SEGUIRE = ((ASSISTI, "Assisti"), (VAI_ALLA_FINE, "Vai alla fine"))
# I livelli della cronaca, con la normale come predefinita.
LIVELLI_DI_CRONACA = ((cronaca.SINTETICA, "Sintetica"), (cronaca.NORMALE, "Normale"), (cronaca.TECNICA, "Tecnica"))
# Il testo del pulsante che Esc preme, senza la lettera sottolineata: &Chiudi e C&hiudi valgono uguale.
ETICHETTA_CHIUDI = "Chiudi"
# Due pressioni dello stesso pulsante più vicine di così sono un tasto tenuto giù: la seconda si ignora. Viene dal
# calendario dei tornei, dove NVDA manda le ripetizioni come pressioni nuove.
RIPETIZIONE_IGNORATA = 0.5


def controllo_col_fuoco():
    """Il controllo che ha il fuoco: una funzione a sé, perché le prove sul desktop nascosto la sostituiscono."""
    return wx.Window.FindFocus()


def pulsante_chiudi(finestra):
    """Il primo pulsante Chiudi fra i controlli della finestra, a qualunque profondità, o None; i dialoghi che ci stanno dentro non contano."""
    for figlio in finestra.GetChildren():
        if figlio.IsTopLevel():
            continue
        if isinstance(figlio, wx.Button) and figlio.GetLabelText() == ETICHETTA_CHIUDI:
            return figlio
        trovato = pulsante_chiudi(figlio)
        if trovato is not None:
            return trovato
    return None


class _Dialogo(wx.Dialog):
    """
    La base dei dialoghi: pannello che scorre, sizer verticale, apertura massimizzata, chiusura con Esc. Un dialogo
    con GRAZIA_ALL_APERTURA vera conta l'apertura come un Invio, e ignora gli Invio che arrivano entro la grazia
    dall'apertura o dall'Invio di prima, ovunque sia il fuoco: è per i dialoghi in cui Invio conferma, dalla
    finestra Mercato e ricerca.
    """

    GRAZIA_ALL_APERTURA = False

    def __init__(self, genitore, titolo):
        super().__init__(genitore, title=titolo, style=STILE_ADATTABILE)
        self.pannello = pannello_scorrevole(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self._timer_del_suono = None

    def etichetta(self, testo):
        controllo = wx.StaticText(self.pannello, label=testo)
        self.sizer.Add(controllo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        return controllo

    def aggiungi(self, controllo, proporzione=0):
        self.sizer.Add(controllo, proporzione, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        return controllo

    def pulsanti(self, *voci, predefinito=True):
        """
        Una riga di pulsanti: coppie di identificativo e testo; il primo è quello predefinito, salvo
        con predefinito falso, per una seconda riga che non deve rubarlo alla prima.
        """
        riga = wx.BoxSizer(wx.HORIZONTAL)
        creati = []
        for identificativo, testo in voci:
            pulsante = wx.Button(self.pannello, identificativo, testo)
            riga.Add(pulsante, 0, wx.ALL, 4)
            creati.append(pulsante)
        if predefinito:
            creati[0].SetDefault()
        self.sizer.Add(riga, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
        return creati

    def completa(self, misura):
        """
        Dà il sizer al pannello e al dialogo la misura del contenuto, poi le due regole di tutte le finestre
        interne, dal collaudo di Gabriele del 23 ottobre 2026. Il dialogo si apre massimizzato, come la
        finestra principale, perché con lo screen reader e il display braille il testo largo va meno a capo;
        la misura di adatta_finestra resta quella a cui torna se lo si ripristina. E se ha un pulsante
        Chiudi, Esc lo preme: wx lo fa da sé soltanto quando Chiudi è wx.ID_CANCEL, o wx.ID_OK senza un
        annullamento, e non con wx.ID_CLOSE o con un pulsante qualunque. Un dialogo che sceglie da sé il
        pulsante di Esc, come l'aggiornamento col suo Non adesso, tiene il suo.
        """
        self.pannello.SetSizer(self.sizer)
        adatta_finestra(self, self.pannello, misura)
        self.Maximize()
        chiudi = pulsante_chiudi(self)
        if chiudi is not None and self.GetEscapeId() == wx.ID_ANY:
            self.SetEscapeId(chiudi.GetId())
        if self.GRAZIA_ALL_APERTURA:
            # L'ultimo legame del gancio dei tasti, quindi wx lo chiama per primo, prima di ogni altro e prima del pulsante predefinito.
            self.ultimo_invio = _adesso()
            self.Bind(wx.EVT_CHAR_HOOK, self._grazia_dell_invio)

    def _grazia_dell_invio(self, event):
        """Un Invio entro la grazia dall'apertura o dall'Invio di prima si mangia; ogni altro tasto prosegue. Una prova sola per tasto."""
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers() and invio_da_ignorare(self, event):
            return
        event.Skip()

    def _ripetuta(self, nome):
        """Vero se il pulsante del nome dato è stato premuto meno di mezzo secondo fa: è un tasto tenuto giù, e la pressione si ignora."""
        adesso_monotono = time.monotonic()
        pressioni = self.__dict__.setdefault("_pressioni", {})
        prima = pressioni.get(nome)
        pressioni[nome] = adesso_monotono
        return prima is not None and adesso_monotono - prima < RIPETIZIONE_IGNORATA

    def invio_su(self, controllo, azione):
        """
        Invio su quel controllo fa l'azione, e su nessun altro, per i dialoghi senza pulsante
        predefinito: nel pannello dei tornei Invio su un incontro lo ascolta, negli editor Invio su un
        modello o su una fase lo modifica. Con un pulsante predefinito, invece, Invio su qualunque
        elenco lo premeva, e un'azione pensata per un elenco partiva da un altro; lo ha visto la
        revisione della tappa 12, il 14 ottobre 2026. Il tasto si prende prima di Windows, con
        EVT_CHAR_HOOK, perché in un dialogo Invio su un elenco non arriva all'elenco.
        """
        if not hasattr(self, "_azioni_dell_invio"):
            self._azioni_dell_invio = []
            self.Bind(wx.EVT_CHAR_HOOK, self._tasto_invio)
        self._azioni_dell_invio.append((controllo, azione))

    def invio(self, fuoco):
        """L'azione di Invio sul controllo che ha il fuoco, se ce n'è una: vero se è partita."""
        if fuoco is None:
            return False
        for controllo, azione in getattr(self, "_azioni_dell_invio", ()):
            if fuoco is controllo or fuoco.GetId() == controllo.GetId():
                azione()
                return True
        return False

    def _tasto_invio(self, event):
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers() and self.invio(controllo_col_fuoco()):
            return
        event.Skip()

    def chiudi(self, codice):
        """Chiude il dialogo con il codice dato; fuori da ShowModal, come nei collaudi, lo annota soltanto."""
        if self.IsModal():
            self.EndModal(codice)
        else:
            self.SetReturnCode(codice)

    def avvisa(self, testo, controllo, suono="campo_da_correggere"):
        """Un avviso che lascia il dialogo aperto, con il cursore sul campo da correggere; il suono dice di che errore si tratta."""
        suoni.suona(suono)
        wx.MessageBox(testo, self.GetTitle(), wx.OK | wx.ICON_WARNING, self)
        controllo.SetFocus()

    def _conferma(self, domanda):
        """
        Una domanda sì o no con il suono della domanda e il no già scelto, come in tutta la finestra:
        un Invio di troppo non deve confermare un'operazione che non si ritira (Gabriele, 1.39.6). Il
        messaggio nasce dal dialogo, così alla risposta il fuoco torna lì. Al no suona l'annullamento.
        """
        suoni.suona("domanda")
        if wx.MessageBox(domanda, self.GetTitle(), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self) == wx.YES:
            return True
        suoni.suona("annullato")
        return False

    @staticmethod
    def _riscrivi(elenco, righe, posto):
        """
        Mette le righe nell'elenco cambiando soltanto quelle diverse, così lo screen reader non sente
        un elenco nuovo, e tiene la scelta al posto dato, o alla prima riga.
        """
        if elenco.GetCount() != len(righe):
            elenco.Set(righe)
        else:
            for i, riga in enumerate(righe):
                if elenco.GetString(i) != riga:
                    elenco.SetString(i, riga)
        if righe:
            elenco.SetSelection(min(max(posto, 0), len(righe) - 1))

    def _scheda_del_giocatore(self, g, impostazioni=None):
        """La scheda del giocatore scelto in un dialogo, da leggere e chiudere con Esc, con il suono della scheda dei dialoghi."""
        dialogo = Lettura(self, f"Scheda di {testi.nome_completo(g)}", testi.scheda_giocatore(g, self.mondo), impostazioni)
        try:
            suoni.suona("mercato_scheda_giocatore")
            dialogo.ShowModal()
        finally:
            dialogo.Destroy()

    @staticmethod
    def _torna(controllo):
        """Rimette il fuoco sul controllo che l'aveva prima di un'operazione, se c'è ancora."""
        if controllo is not None:
            with contextlib.suppress(RuntimeError):
                controllo.SetFocus()

    def suona_fra_poco(self, funzione):
        """
        Chiama funzione poco dopo l'ultima richiesta: è per i suoni che seguono un campo mentre lo si
        cambia, che così suonano una volta sola quando ci si ferma, e non a ogni cifra o freccia. Se
        nel frattempo si è passati a un altro campo, con un'altra funzione, vale l'ultima.
        """
        if self._timer_del_suono is not None and self._timer_del_suono.IsRunning():
            self._timer_del_suono.Restart(RITARDO_DEL_SUONO_AL_VOLO, funzione)
        else:
            self._timer_del_suono = wx.CallLater(RITARDO_DEL_SUONO_AL_VOLO, self._suono_rimandato, funzione)

    @staticmethod
    def _suono_rimandato(funzione):
        # Se nel frattempo il dialogo si è chiuso, i suoi controlli non ci sono più: niente suono.
        with contextlib.suppress(RuntimeError):
            funzione()


class _ElencoCheSiRestringe:
    """
    Ricorda se un elenco era vuoto e dice quale suono fa il suo cambiamento: elenco_svuotato quando
    da pieno resta vuoto, elenco_ripopolato quando da vuoto torna ad avere qualcosa, altrimenti
    niente. Lo screen reader non legge un elenco che cambia mentre si scrive in un altro campo.
    """

    def __init__(self):
        self.pieno = None

    def passaggio(self, pieno):
        prima, self.pieno = self.pieno, pieno
        if prima is None or prima == pieno:
            return None
        return "elenco_ripopolato" if pieno else "elenco_svuotato"


class SceltaGiocatore(_Dialogo):
    """
    La scelta di un giocatore: un campo per il numero o il nome e l'elenco, che si restringe mentre si scrive. Invio
    nel campo sceglie il primo: dal 24 ottobre 2026 l'apertura conta come un Invio, e un Invio tenuto giù non sceglie.
    """

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, mondo, titolo="Scheda del giocatore", pulsante="&Mostra la scheda", giocatori=None):
        super().__init__(genitore, titolo)
        self.mondo = mondo
        self.scelto = None
        self.tutti = sorted(mondo.giocatori.values() if giocatori is None else giocatori, key=lambda g: g.id)
        self.visibili = []
        self.elenco_vuoto = _ElencoCheSiRestringe()
        self.etichetta("&Numero o nome del giocatore")
        self.campo = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PROCESS_ENTER))
        self.etichetta("&Giocatori")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        mostra, _annulla = self.pulsanti((wx.ID_OK, pulsante), (wx.ID_CANCEL, "Annulla"))
        self.campo.Bind(wx.EVT_TEXT, self.filtra)
        self.campo.Bind(wx.EVT_TEXT_ENTER, self.conferma)
        self.elenco.Bind(wx.EVT_LISTBOX_DCLICK, self.conferma)
        mostra.Bind(wx.EVT_BUTTON, self.conferma)
        self.filtra()
        self.completa((480, 420))
        self.campo.SetFocus()

    def filtra(self, event=None):
        """Tiene nell'elenco i giocatori il cui numero comincia con le cifre scritte, o il cui nome contiene il testo."""
        chiave = self.campo.GetValue().strip().casefold()
        if not chiave:
            self.visibili = list(self.tutti)
        elif chiave.isdigit():
            self.visibili = sorted((g for g in self.tutti if str(g.id).startswith(chiave)), key=lambda g: (str(g.id) != chiave, g.id))
        else:
            self.visibili = [g for g in self.tutti if chiave in testi.nome_completo(g).casefold()]
        self.elenco.Set([f"{g.id}, {testi.nome_completo(g)}, {testi.anni(g)} anni, {testi.stato(g, self.mondo)}" for g in self.visibili])
        if self.visibili:
            self.elenco.SetSelection(0)
        passaggio = self.elenco_vuoto.passaggio(bool(self.visibili))
        if passaggio:
            suoni.suona(passaggio)

    def conferma(self, event=None):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return
        self.scelto = self.visibili[indice]
        self.chiudi(wx.ID_OK)


class Aspetto(_Dialogo):
    """Le impostazioni d'aspetto, sul modello di quelle di Terminal Beast: anteprima, caratteri e colori."""

    def __init__(self, genitore, impostazioni):
        super().__init__(genitore, "Aspetto")
        self.risultato = None
        # Le impostazioni che questo dialogo non tocca, come il volume degli effetti, restano com'erano.
        self.altre = dict(impostazioni)
        self.etichetta("Anteprima")
        self.anteprima = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
                                                   value="MESS, Manageriale e Simulatore Showdown.\nCosì appare il testo della finestra."))
        self.etichetta("&Dimensione dei caratteri, in punti")
        self.dimensione = self.aggiungi(wx.SpinCtrl(self.pannello, min=modulo_impostazioni.DIMENSIONE_MINIMA, max=modulo_impostazioni.DIMENSIONE_MASSIMA,
                                                    initial=impostazioni["dimensione"]))
        self.testo = self._terna("del testo", impostazioni["colore_testo"])
        self.sfondo = self._terna("dello sfondo", impostazioni["colore_sfondo"])
        predefiniti, ok, _annulla = self.pulsanti((wx.ID_ANY, "&Predefiniti"), (wx.ID_OK, "OK"), (wx.ID_CANCEL, "Annulla"))
        predefiniti.Bind(wx.EVT_BUTTON, self.ai_predefiniti)
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        ok.SetDefault()
        for controllo in (self.dimensione, *self.testo, *self.sfondo):
            controllo.Bind(wx.EVT_SPINCTRL, self.aggiorna)
            controllo.Bind(wx.EVT_TEXT, self.aggiorna)
        self.aggiorna()
        self.completa((420, 480))
        self.dimensione.SetFocus()

    def _terna(self, di_cosa, valori):
        controlli = []
        for nome, valore in zip(("Rosso", "Verde", "Blu"), valori, strict=True):
            self.etichetta(f"{nome} {di_cosa}, in percentuale")
            controlli.append(self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=100, initial=valore)))
        return controlli

    def valori(self):
        return modulo_impostazioni.valide({
            **self.altre,
            "dimensione": self.dimensione.GetValue(),
            "colore_testo": [c.GetValue() for c in self.testo],
            "colore_sfondo": [c.GetValue() for c in self.sfondo],
        })

    def aggiorna(self, event=None):
        aspetto.applica(self.anteprima, self.valori())

    def ai_predefiniti(self, event=None):
        """Dimensione e colori tornano ai predefiniti, ancora da confermare; lo screen reader resta sul pulsante, e il suono lo dice."""
        predefinite = modulo_impostazioni.valide(None)
        self.dimensione.SetValue(predefinite["dimensione"])
        for controlli, valori in ((self.testo, predefinite["colore_testo"]), (self.sfondo, predefinite["colore_sfondo"])):
            for controllo, valore in zip(controlli, valori, strict=True):
                controllo.SetValue(valore)
        self.aggiorna()
        suoni.suona("aspetto_predefiniti")

    def conferma(self, event=None):
        self.risultato = self.valori()
        self.chiudi(wx.ID_OK)


class Conservazione(_Dialogo):
    """Per quanti giorni simulati si conservano le voci dei diari, come la pulizia dei diari di Terminal Beast."""

    def __init__(self, genitore, conservazione):
        super().__init__(genitore, "Conservazione dei diari")
        self.risultato = None
        self.sizer.Add(wx.StaticText(self.pannello, label="Per quanti giorni simulati si conservano le voci dei diari. Zero vuol dire per sempre."), 0, wx.ALL, 8)
        self.etichetta("Giorni per i diari dei &giocatori e degli allenatori")
        self.giocatori = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=3650, initial=conservazione["giocatori"]))
        self.etichetta("Giorni per i diari delle &polisportive")
        self.polisportive = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=3650, initial=conservazione["polisportive"]))
        ok, _annulla = self.pulsanti((wx.ID_OK, "OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((400, 260))
        self.giocatori.SetFocus()

    def conferma(self, event=None):
        self.risultato = {"giocatori": self.giocatori.GetValue(), "polisportive": self.polisportive.GetValue()}
        self.chiudi(wx.ID_OK)


class EffettiSonori(_Dialogo):
    """
    Il volume degli effetti sonori, da 0 a 100, decisione D24, e quello della partita dal vivo, da 0
    a 100, decisione D30: a ogni ritocco di un campo, quando ci si ferma, suona il suo campione al
    volume scritto, così si sente subito il livello; a zero tace. Il campione della partita suona al
    fattore con cui suonerebbe la partita, non a quello degli effetti. In risultato restano i due
    volumi, effetti e partita.
    """

    def __init__(self, genitore, volume, volume_partita=modulo_impostazioni.VOLUME_PARTITA_PREDEFINITO):
        super().__init__(genitore, "Effetti sonori")
        self.risultato = None
        self.sizer.Add(wx.StaticText(self.pannello, label=testi.SPIEGAZIONE_VOLUMI), 0, wx.ALL, 8)
        self.etichetta("&Volume degli effetti")
        self.volume = self.aggiungi(wx.SpinCtrl(self.pannello, min=modulo_impostazioni.VOLUME_MINIMO, max=modulo_impostazioni.VOLUME_MASSIMO, initial=volume))
        self.etichetta("Volume della &partita dal vivo")
        self.volume_partita = self.aggiungi(wx.SpinCtrl(self.pannello, min=modulo_impostazioni.VOLUME_MINIMO, max=modulo_impostazioni.VOLUME_MASSIMO,
                                                        initial=volume_partita))
        ok, _annulla = self.pulsanti((wx.ID_OK, "OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        for campo, gestore in ((self.volume, self.al_volume), (self.volume_partita, self.al_volume_partita)):
            campo.Bind(wx.EVT_SPINCTRL, gestore)
            campo.Bind(wx.EVT_TEXT, gestore)
        self.completa((440, 280))
        self.volume.SetFocus()

    def al_volume(self, event=None):
        self.suona_fra_poco(self.prova)

    def al_volume_partita(self, event=None):
        self.suona_fra_poco(self.prova_partita)

    def prova(self):
        """Il suono di prova al volume scritto nel campo, non a quello salvato."""
        suoni.suona("prova_volume_effetti", volume=self.volume.GetValue())

    def prova_partita(self):
        """Il suono di prova della partita al volume della partita scritto nel campo, con il fattore della partita."""
        suoni.suona("prova_volume_partita", fattore=partita_sonora.fattore_del_volume(self.volume_partita.GetValue()))

    def conferma(self, event=None):
        self.risultato = (self.volume.GetValue(), self.volume_partita.GetValue())
        self.chiudi(wx.ID_OK)


class NuovaPolisportiva(_Dialogo):
    """
    La fondazione di una polisportiva: il nome, la sede, la password facoltativa della decisione D3 e se
    renderla attiva. Dalla tappa 14, richiesta di Gabriele del 23 ottobre 2026, la sede è un comune: il
    campo Sede ne propone uno estratto coi pesi della popolazione, che basta confermare, e mentre si
    scrive restringe l'elenco dei comuni, ciascuno con la sua popolazione in percentuale su quella del
    più popoloso, la provincia e la regione; quando l'elenco si svuota o torna pieno lo fa sentire, come
    gli altri filtri. Fonda prende il comune scelto nell'elenco. Invio sul campo Sede o sull'elenco, e
    il doppio clic sull'elenco, non fondano subito, perché lì sembra scegliere il comune: chiedono
    conferma, con il no già scelto. Dalla revisione della tappa 14 fanno la stessa domanda anche Fonda e
    Invio sul nome o sulle password, quando il campo Sede è vuoto o non dice proprio il comune scelto
    nell'elenco: prima fondavano in silenzio a Roma, il primo dell'elenco pieno, o nel primo comune di
    un nome scritto a metà. In risultato restano nome, password, se renderla attiva e comune; il comune
    è vuoto soltanto se la collezione dei comuni non si legge.
    """

    def __init__(self, genitore, mondo, proposta=None):
        super().__init__(genitore, "Nuova polisportiva")
        self.mondo = mondo
        self.risultato = None
        self.comuni = []
        self.elenco_vuoto = _ElencoCheSiRestringe()
        self.ci_sono_comuni = bool(luoghi.candidati(""))
        self.etichetta(f"&Nome, da {NOME_POLISPORTIVA_MIN} a {NOME_POLISPORTIVA_MAX} caratteri")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello))
        self.etichetta("&Sede: scrivi il nome del comune per cercarlo")
        self.sede = self.aggiungi(wx.TextCtrl(self.pannello))
        self.etichetta_comuni = self.etichetta("&Comuni trovati")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Password, facoltativa")
        self.password = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        self.etichetta("C&onferma della password")
        self.conferma_password = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        self.attiva = self.aggiungi(wx.CheckBox(self.pannello, label="&Rendila la polisportiva attiva"))
        self.attiva.SetValue(True)
        fonda, _annulla = self.pulsanti((wx.ID_OK, "&Fonda"), (wx.ID_CANCEL, "Annulla"))
        fonda.Bind(wx.EVT_BUTTON, self.conferma)
        self.sede.Bind(wx.EVT_TEXT, self.filtra)
        self.invio_su(self.sede, self.conferma_con_domanda)
        self.invio_su(self.elenco, self.conferma_con_domanda)
        self.elenco.Bind(wx.EVT_LISTBOX_DCLICK, self.conferma_con_domanda)
        self.sede.ChangeValue(luoghi.comune_a_caso() if proposta is None else proposta)
        self.filtra()
        self.completa((520, 560))
        self.nome.SetFocus()

    def filtra(self, event=None):
        """
        L'elenco dei comuni per il testo del campo Sede, col primo già scelto, e il loro numero
        nell'etichetta; il suono quando si svuota o torna pieno, e all'apertura se è vuoto.
        """
        self.comuni = luoghi.candidati(self.sede.GetValue())
        self._riscrivi(self.elenco, [testi.riga_del_comune(comune) for comune in self.comuni], 0)
        self.etichetta_comuni.SetLabel(f"&Comuni trovati: {testi.intero(len(self.comuni))}")
        self.pannello.Layout()
        apertura = self.elenco_vuoto.pieno is None
        passaggio = self.elenco_vuoto.passaggio(bool(self.comuni))
        if apertura and not self.comuni:
            suoni.in_coda("elenco_svuotato")
        elif passaggio:
            suoni.suona(passaggio)

    def comune_scelto(self):
        """Il comune scelto nell'elenco, oppure None se l'elenco è vuoto."""
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.comuni):
            return None
        return self.comuni[indice]

    def _controlla(self):
        """Nome, sede e password: il risultato se vanno, altrimenti None, dopo l'avviso col cursore sul campo da correggere."""
        problema = self.mondo.problema_nome_polisportiva(self.nome.GetValue())
        if problema:
            self.avvisa(problema, self.nome)
            return None
        comune = self.comune_scelto()
        if comune is None and self.ci_sono_comuni:
            # Un campo da correggere, dal collaudo di gioco: prima suonava come un pulsante premuto senza niente di scelto.
            self.avvisa("Nessun comune corrisponde a quello che hai scritto nella sede: correggilo, o cancellalo per vederli tutti.", self.sede)
            return None
        if self.password.GetValue() != self.conferma_password.GetValue():
            self.avvisa("La password e la conferma non coincidono.", self.password, "password_non_coincidono")
            return None
        return (self.nome.GetValue(), self.password.GetValue() or None, self.attiva.GetValue(), comune or "")

    def conferma(self, event=None):
        """
        Fonda, o Invio sul nome e sulle password: si fonda senza domande, se tutto va e il campo Sede
        dice proprio il comune scelto; se è vuoto o dice altro, la domanda di Invio sulla sede.
        """
        self._fonda(chiedi=False)

    def conferma_con_domanda(self, event=None):
        """Invio sul campo Sede o sull'elenco e il doppio clic sull'elenco: la domanda col nome e la sede, sempre."""
        self._fonda(chiedi=True)

    def _fonda(self, chiedi):
        """Gli stessi controlli per tutti, poi la domanda se serve: al no il fuoco torna dov'era."""
        fuoco = controllo_col_fuoco()
        risultato = self._controlla()
        if risultato is None:
            return
        comune = risultato[3]
        if chiedi or (comune and not luoghi.coincide(self.sede.GetValue(), comune)):
            if not self._conferma(testi.domanda_fondazione(normalizza_nome(risultato[0]), comune)):
                self._torna(fuoco)
                return
        self.risultato = risultato
        self.chiudi(wx.ID_OK)


class CambiaPolisportiva(_Dialogo):
    """La scelta della polisportiva attiva fra quelle dell'utente, con la password se è protetta."""

    def __init__(self, genitore, mondo):
        super().__init__(genitore, "Cambia polisportiva attiva")
        self.mondo = mondo
        self.scelta = None
        self.mie = sorted((p for p in mondo.polisportive.values() if not p.is_cpu_controlled), key=lambda p: p.nome.casefold())
        self.etichetta("&Le tue polisportive")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE, choices=[testi.riga_mia_polisportiva(p, mondo) for p in self.mie]), 1)
        self.etichetta("&Password, se la polisportiva è protetta")
        self.password = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        attiva, _annulla = self.pulsanti((wx.ID_OK, "&Attiva"), (wx.ID_CANCEL, "Annulla"))
        attiva.Bind(wx.EVT_BUTTON, self.conferma)
        self.elenco.Bind(wx.EVT_LISTBOX_DCLICK, self.conferma)
        if self.mie:
            self.elenco.SetSelection(self.mie.index(mondo.miapolisportiva_attiva) if mondo.miapolisportiva_attiva in self.mie else 0)
        self.completa((440, 360))
        self.elenco.SetFocus()

    def conferma(self, event=None):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return
        poli = self.mie[indice]
        if poli.protetta and not poli.verifica_password(self.password.GetValue()):
            self.avvisa(f"La password di {poli.nome} non è giusta.", self.password, "password_sbagliata")
            return
        self.scelta = poli
        self.chiudi(wx.ID_OK)


class PasswordPolisportiva(_Dialogo):
    """La password della polisportiva: si mette, si cambia o, lasciando vuota la nuova, si toglie."""

    def __init__(self, genitore, poli):
        super().__init__(genitore, f"Password di {poli.nome}")
        self.poli = poli
        self.risultato = None
        self.attuale = None
        if poli.protetta:
            self.etichetta("Password &attuale")
            self.attuale = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        self.etichetta("&Nuova password, vuota per togliere la protezione")
        self.nuova = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        self.etichetta("&Conferma della nuova password")
        self.conferma_nuova = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        ok, _annulla = self.pulsanti((wx.ID_OK, "OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((420, 300))
        (self.attuale or self.nuova).SetFocus()

    def conferma(self, event=None):
        if self.attuale is not None and not self.poli.verifica_password(self.attuale.GetValue()):
            self.avvisa("La password attuale non è giusta.", self.attuale, "password_sbagliata")
            return
        if self.nuova.GetValue() != self.conferma_nuova.GetValue():
            self.avvisa("La nuova password e la conferma non coincidono.", self.nuova, "password_non_coincidono")
            return
        self.risultato = self.nuova.GetValue()
        self.chiudi(wx.ID_OK)


class ChiediPassword(_Dialogo):
    """La password di una polisportiva protetta, prima di un'operazione che non si può annullare."""

    def __init__(self, genitore, poli, perche):
        super().__init__(genitore, f"Password di {poli.nome}")
        self.poli = poli
        self.sizer.Add(wx.StaticText(self.pannello, label=perche), 0, wx.ALL, 8)
        self.etichetta("&Password")
        self.password = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        ok, _annulla = self.pulsanti((wx.ID_OK, "OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((380, 220))
        self.password.SetFocus()

    def conferma(self, event=None):
        if not self.poli.verifica_password(self.password.GetValue()):
            self.avvisa(f"La password di {self.poli.nome} non è giusta.", self.password, "password_sbagliata")
            return
        self.chiudi(wx.ID_OK)


class Cifra(_Dialogo):
    """
    Una cifra in euro da scegliere, fino alla cassa, con una spiegazione davanti; se serve, una
    nota dopo il campo segue la cifra, come la probabilità che un giocatore accetti un ingaggio.
    La nota è un testo che lo screen reader non legge quando cambia: se il dialogo riceve anche la
    probabilità, a ogni ritocco della cifra, quando ci si ferma, un tic la fa sentire con la sua
    altezza, più acuto quanto più è probabile che il giocatore accetti. Dal 24 ottobre 2026 l'apertura conta come un
    Invio, e un Invio tenuto giù non conferma la cifra.
    """

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, titolo, spiegazione, etichetta, iniziale, massimo, nota=None, probabilita=None):
        super().__init__(genitore, titolo)
        self.valore = None
        self.calcola_nota = nota
        self.calcola_probabilita = probabilita
        self.sizer.Add(wx.StaticText(self.pannello, label=spiegazione), 0, wx.ALL, 8)
        self.etichetta(etichetta)
        self.cifra = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=max(0, massimo), initial=max(0, min(iniziale, massimo))))
        self.nota = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.nota, 0, wx.ALL, 8)
        ok, _annulla = self.pulsanti((wx.ID_OK, "OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        self.cifra.Bind(wx.EVT_SPINCTRL, self.aggiorna)
        self.cifra.Bind(wx.EVT_TEXT, self.aggiorna)
        self.aggiorna()
        self.completa((440, 280))
        self.cifra.SetFocus()

    def aggiorna(self, event=None):
        if self.calcola_nota:
            self.nota.SetLabel(self.calcola_nota(self.cifra.GetValue()))
            self.pannello.Layout()
        if event is not None and self.calcola_probabilita:
            self.suona_fra_poco(self.tic_della_probabilita)

    def tic_della_probabilita(self):
        """Il tic della probabilità d'ingaggio, all'altezza della cifra scritta nel campo."""
        percentuale = self.calcola_probabilita(self.cifra.GetValue())
        suoni.suona("probabilita_ingaggio", semitoni=suoni.probabilita_in_semitoni(percentuale))

    def conferma(self, event=None):
        if self.cifra.GetValue() <= 0:
            self.avvisa("La cifra deve essere di almeno 1 euro.", self.cifra)
            return
        self.valore = self.cifra.GetValue()
        self.chiudi(wx.ID_OK)


class PagaArretrati(_Dialogo):
    """
    Gli arretrati della polisportiva, decisione D22: chi aspetta, dal meno paziente, con il suo
    umore, e quanto dare a ciascuno, perché quando la cassa non basta decide l'utente. In pagati
    restano i pagamenti fatti, che la finestra racconta alla chiusura.
    """

    def __init__(self, genitore, mondo, poli):
        super().__init__(genitore, f"Arretrati di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.pagati = []
        self.debitori = []
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Chi aspetta")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("C&ifra da pagare, in euro")
        self.cifra = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=0, initial=0))
        paga, _chiudi = self.pulsanti((wx.ID_ANY, "&Paga"), (wx.ID_CANCEL, "C&hiudi"))
        paga.Bind(wx.EVT_BUTTON, self.paga)
        self.elenco.Bind(wx.EVT_LISTBOX, self.al_giocatore)
        self.aggiorna()
        self.completa((600, 460))
        self.elenco.SetFocus()

    def aggiorna(self, posto=0):
        rosa = [self.mondo.giocatori[gid] for gid in self.poli.tesserati if gid in self.mondo.giocatori]
        self.debitori = sorted((g for g in rosa if g.arretrati), key=lambda g: g.pazienza)
        self.elenco.Set([testi.riga_arretrati(g) for g in self.debitori] or ["Nessuno aspetta arretrati."])
        self.elenco.SetSelection(min(posto, self.elenco.GetCount() - 1))
        self.info.SetLabel(f"In cassa {testi.euro(self.poli.cassa)}; arretrati da pagare {testi.euro(sum(g.arretrati for g in self.debitori))}.")
        self.al_giocatore()
        self.pannello.Layout()

    def al_giocatore(self, event=None):
        """Per il tesserato scelto, la cifra parte da tutto quello che aspetta, fin dove arriva la cassa."""
        indice = self.elenco.GetSelection()
        if not self.debitori or indice == wx.NOT_FOUND:
            self.cifra.SetRange(0, 0)
            self.cifra.SetValue(0)
            return
        massimo = min(self.debitori[indice].arretrati, self.poli.cassa)
        self.cifra.SetRange(0, max(0, massimo))
        self.cifra.SetValue(max(0, massimo))

    def paga(self, event=None):
        """
        Paga al tesserato scelto la cifra del campo. Il suono dice com'è andata: pagato in parte,
        saldato mentre altri aspettano ancora, o saldato l'ultimo debito.
        """
        indice = self.elenco.GetSelection()
        if not self.debitori or indice == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return
        if self.poli.cassa <= 0:
            self.avvisa(f"La cassa di {self.poli.nome} è vuota.", self.elenco, "cassa_insufficiente")
            return
        g = self.debitori[indice]
        try:
            self.mondo.paga(self.poli, g, self.cifra.GetValue())
        except ValueError as e:
            self.avvisa(str(e), self.cifra)
            return
        self.pagati.append((g, self.cifra.GetValue()))
        if g.arretrati:
            suoni.suona("arretrati_pagati_in_parte")
        elif any(altro.arretrati for altro in self.debitori):
            suoni.suona("arretrati_saldati")
        else:
            suoni.suona("arretrati_tutti_saldati")
        wx.MessageBox(f"Pagati {testi.euro(self.cifra.GetValue())} a {testi.nome_completo(g)}: ora è {testi.umore(g)}.", "Arretrati", wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna(indice)
        self.elenco.SetFocus()


class Vendite(_Dialogo):
    """
    Le vendite della polisportiva, decisione D22: i tesserati con il loro valore di mercato, il
    prezzo a cui metterne uno in vendita, o cambiarlo, e il ritiro dalla vendita. In fatte restano
    i testi delle operazioni, che la finestra racconta alla chiusura.
    """

    def __init__(self, genitore, mondo, poli):
        super().__init__(genitore, f"Vendite di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.fatte = []
        self.rosa = sorted((mondo.giocatori[gid] for gid in poli.tesserati if gid in mondo.giocatori), key=lambda g: -g.indice_collettivo_valore)
        self.etichetta("&Tesserati")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Prezzo, in euro")
        self.prezzo = self.aggiungi(wx.SpinCtrl(self.pannello, min=1, max=100_000_000, initial=1))
        metti, togli, _chiudi = self.pulsanti((wx.ID_ANY, "&Metti in vendita"), (wx.ID_ANY, "To&gli dalla vendita"), (wx.ID_CANCEL, "C&hiudi"))
        metti.Bind(wx.EVT_BUTTON, self.metti)
        togli.Bind(wx.EVT_BUTTON, self.togli)
        self.elenco.Bind(wx.EVT_LISTBOX, self.al_giocatore)
        self.aggiorna()
        self.completa((600, 460))
        self.elenco.SetFocus()

    def aggiorna(self, posto=0):
        self.elenco.Set([testi.riga_vendita(g, self.poli, self.mondo.datetime_corrente_simulazione) for g in self.rosa])
        if self.rosa:
            self.elenco.SetSelection(min(posto, len(self.rosa) - 1))
        self.al_giocatore()

    def al_giocatore(self, event=None):
        """Il prezzo parte da quello di vendita, se il tesserato è già in vendita, o dal suo valore di mercato."""
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            return
        g = self.rosa[indice]
        self.prezzo.SetValue(self.poli.in_vendita.get(g.id, max(1, economia.valore_di_mercato(g, self.mondo.datetime_corrente_simulazione))))

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return None, indice
        return self.rosa[indice], indice

    def metti(self, event=None):
        """
        Mette in vendita il tesserato scelto, o gli cambia il prezzo: il messaggio è lo stesso, e
        solo il suono dice se era già in vendita.
        """
        g, indice = self._scelto()
        if g is None:
            return
        suono = "prezzo_di_vendita_cambiato" if g.id in self.poli.in_vendita else "messo_in_vendita"
        self.mondo.metti_in_vendita(self.poli, g, self.prezzo.GetValue())
        suoni.suona(suono)
        testo = f"{testi.nome_completo(g)} è in vendita a {testi.euro(self.prezzo.GetValue())}."
        self.fatte.append(testo)
        wx.MessageBox(testo, "Vendite", wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna(indice)
        self.elenco.SetFocus()

    def togli(self, event=None):
        g, indice = self._scelto()
        if g is None:
            return
        try:
            self.mondo.togli_dalla_vendita(self.poli, g)
        except ValueError as e:
            suoni.suona("vendita_non_attiva")
            wx.MessageBox(str(e), "Vendite", wx.OK | wx.ICON_WARNING, self)
            return
        testo = f"{testi.nome_completo(g)} non è più in vendita."
        self.fatte.append(testo)
        suoni.suona("tolto_dalla_vendita")
        wx.MessageBox(testo, "Vendite", wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna(indice)
        self.elenco.SetFocus()


class SalaAllenamento(_Dialogo):
    """
    La sala allenamento della decisione D31, tappa 11: gli allenandi della polisportiva, uno alla
    volta, con le loro 24 caratteristiche e il costo del prossimo punto di ciascuna, e il portafoglio
    dei punti allenamento. Si spende a mano su una caratteristica, con l'anteprima in un campo che si
    raggiunge con Tab e che la conferma ripete; oppure si spende tutto secondo il programma, per
    l'allenando scelto o per tutti insieme. Programma e intensità si scelgono qui e valgono subito.
    Ogni esito arriva in un messaggio breve, una riga per allenando, con il suo suono, e quello della
    classe guadagnata in coda; il dettaglio caratteristica per caratteristica resta in esiti, che la
    finestra mostra alla chiusura insieme ai cambi di programma e d'intensità. Gli avvisi lasciano
    aperta la sala, ciascuno col suo suono. Dopo ogni operazione elenchi e controlli si aggiornano
    tenendo il posto, e il fuoco torna dov'era. L'ordine degli allenandi è quello del nome, fermo
    finché la sala resta aperta, così la lettera iniziale li ritrova.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None):
        super().__init__(genitore, f"Sala allenamento di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.esiti = []
        self.allenandi = sorted((mondo.giocatori[gid] for gid in poli.tesserati if gid in mondo.giocatori), key=lambda g: testi.nome_completo(g).casefold())
        # Programma, intensità e, dalla tappa 12, iscrizione automatica ai tornei di ciascuno all'apertura:
        # alla chiusura dicono che cosa è cambiato.
        self.di_partenza = {g.id: (g.programma, g.intensita, g.iscrizione_automatica) for g in self.allenandi}
        self.indoli = list(INDOLI)
        self.livelli = list(INTENSITA)
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("A&llenandi")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Caratteristiche")
        self.caratteristiche = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Punti da spendere")
        self.punti = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=0, initial=0))
        self.etichetta("A&nteprima")
        self.anteprima = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
        spendi, completo, tutti = self.pulsanti((wx.ID_ANY, "&Spendi"), (wx.ID_ANY, "&Esegui allenamento completo"), (wx.ID_ANY, "Allena &tutti"))
        self.etichetta("Pro&gramma")
        self.programma = self.aggiungi(wx.Choice(self.pannello, choices=[testi.nome_programma(k).capitalize() for k in self.indoli]))
        self.etichetta("&Intensità")
        self.intensita = self.aggiungi(wx.Choice(self.pannello, choices=[k.capitalize() for k in self.livelli]))
        # Dalla tappa 12, decisione D32 e punto 12.4: l'iscrizione automatica ai tornei dell'allenando scelto.
        self.automatica = self.aggiungi(wx.CheckBox(self.pannello, label="Iscrizione a&utomatica ai tornei"))
        scheda, _chiudi = self.pulsanti((wx.ID_ANY, "Sche&da"), (wx.ID_CANCEL, "C&hiudi"), predefinito=False)
        spendi.Bind(wx.EVT_BUTTON, self.spendi)
        completo.Bind(wx.EVT_BUTTON, self.completo)
        tutti.Bind(wx.EVT_BUTTON, self.tutti)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.elenco.Bind(wx.EVT_LISTBOX, self.al_allenando)
        self.caratteristiche.Bind(wx.EVT_LISTBOX, self.aggiorna_anteprima)
        self.punti.Bind(wx.EVT_SPINCTRL, self.aggiorna_anteprima)
        self.punti.Bind(wx.EVT_TEXT, self.aggiorna_anteprima)
        self.programma.Bind(wx.EVT_CHOICE, self.al_programma)
        self.intensita.Bind(wx.EVT_CHOICE, self.all_intensita)
        self.automatica.Bind(wx.EVT_CHECKBOX, self.all_automatica)
        self.aggiorna(0, nuovo=True)
        self.completa((640, 600))
        self.elenco.SetFocus()

    # Lo stato dei controlli.

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.allenandi):
            return None
        return self.allenandi[indice]

    def _caratteristica(self):
        indice = self.caratteristiche.GetSelection()
        return None if indice == wx.NOT_FOUND else allenamento.CARATTERISTICHE[indice]

    def aggiorna(self, posto=None, nuovo=False):
        """
        Riscrive la testata e l'elenco degli allenandi, tenendo il posto, e i controlli dell'allenando
        scelto; con nuovo, l'allenando è appena stato scelto e i punti ripartono da tutto il suo portafoglio.
        """
        posto = self.elenco.GetSelection() if posto is None else posto
        self.info.SetLabel(testi.intestazione_sala(self.poli, self.allenandi, self.mondo))
        self._riscrivi(self.elenco, [testi.riga_allenando(g, self.mondo) for g in self.allenandi], posto)
        self._controlli_dell_allenando(nuovo)
        self.pannello.Layout()

    def _controlli_dell_allenando(self, nuovo=False):
        g = self._scelto()
        if g is None:
            return
        posto = self.caratteristiche.GetSelection()
        self._riscrivi(self.caratteristiche, [testi.riga_caratteristica_allenamento(g, c) for c in allenamento.CARATTERISTICHE], 0 if posto == wx.NOT_FOUND else posto)
        massimo = int(g.punti_allenamento + 1e-9)
        valore = massimo if nuovo else min(self.punti.GetValue(), massimo)
        self.punti.SetRange(0, massimo)
        self.punti.SetValue(valore)
        # La voce dell'indole dell'allenando lo dice, così si sa dove riportarlo.
        for indice, chiave in enumerate(self.indoli):
            voce = testi.voce_programma(chiave, g)
            if self.programma.GetString(indice) != voce:
                self.programma.SetString(indice, voce)
        self.programma.SetSelection(self.indoli.index(g.programma) if g.programma in self.indoli else 0)
        self.intensita.SetSelection(self.livelli.index(g.intensita) if g.intensita in self.livelli else 0)
        self.automatica.SetValue(bool(g.iscrizione_automatica))
        self.aggiorna_anteprima()

    def al_allenando(self, event=None):
        self._controlli_dell_allenando(nuovo=True)

    def aggiorna_anteprima(self, event=None):
        """
        L'anteprima della spesa a mano con i punti e la caratteristica del momento; per chi non si
        allena, il perché, e per chi non ha un punto intero da spendere a mano, quello che gli
        dirà Spendi, invece di un campo fermo a zero senza spiegazione.
        """
        g, c = self._scelto(), self._caratteristica()
        if g is None or c is None:
            testo = ""
        elif not allenamento.puo_allenarsi(g):
            testo = testi.allenando_fermo(g)
        elif g.punti_allenamento < 1:
            testo = testi.senza_punti(g)
        else:
            testo = testi.anteprima_allenamento(g, c, self.punti.GetValue())
        if self.anteprima.GetValue() != testo:
            self.anteprima.ChangeValue(testo)

    # Le spese.

    def _data(self):
        return self.mondo.datetime_corrente_simulazione

    def _puo_allenarsi(self, g):
        """Vero se l'allenando si allena oggi; altrimenti lo dice con il suo avviso."""
        if allenamento.puo_allenarsi(g):
            return True
        self.avvisa(testi.allenando_fermo(g), self.elenco, "allenando_infortunato")
        return False

    def spendi(self, event=None):
        """
        La spesa a mano: i punti del campo sulla caratteristica scelta, dopo la conferma, che è
        l'anteprima stessa. Gli avvisi, nell'ordine: allenando infortunato, caratteristica al
        massimo, portafoglio sotto un punto, cifra zero.
        """
        fuoco = wx.Window.FindFocus()
        g, c = self._scelto(), self._caratteristica()
        if g is None or c is None:
            suoni.suona("nessuna_selezione")
            return
        if not self._puo_allenarsi(g):
            return
        if allenamento.totale(g, c) >= allenamento.tetto(c) - 1e-9:
            self.avvisa(testi.caratteristica_al_massimo(g, c), self.caratteristiche, "caratteristica_al_massimo")
            return
        quanti = self.punti.GetValue()
        if g.punti_allenamento < 1:
            self.avvisa(testi.senza_punti(g), self.elenco, "punti_insufficienti")
            return
        if quanti <= 0:
            self.avvisa("Scegli quanti punti spendere: almeno uno.", self.punti, "punti_insufficienti")
            return
        if not self._conferma(testi.domanda_spesa(g, c, quanti)):
            self._torna(fuoco)
            return
        valore_prima, classe_prima = g.indice_collettivo_valore, testi.codice_classe(g)
        try:
            spesa = allenamento.spendi(g, c, quanti, self._data())
        except ValueError as errore:
            self.avvisa(str(errore), self.punti)
            return
        self._racconta([(g, [spesa], spesa.punti, valore_prima, classe_prima)], "allenamento_fatto", fuoco)

    def completo(self, event=None):
        """L'allenamento completo dell'allenando scelto: tutto il portafoglio, frazioni comprese, secondo il suo programma."""
        fuoco = wx.Window.FindFocus()
        g = self._scelto()
        if g is None:
            suoni.suona("nessuna_selezione")
            return
        if not self._puo_allenarsi(g):
            return
        if g.punti_allenamento <= 0:
            self.avvisa(testi.senza_punti(g), self.elenco, "punti_insufficienti")
            return
        spesa = self._secondo_il_programma(g)
        if spesa is None:
            self.avvisa(testi.tutto_al_massimo(g), self.elenco, "caratteristica_al_massimo")
            return
        self._racconta([spesa], "allenamento_completo", fuoco)

    def tutti(self, event=None):
        """
        Allena tutti: dopo la conferma, ciascuno di chi oggi si allena e ha almeno un punto spende tutto secondo
        il suo programma. Dal collaudo di gioco ogni rifiuto dice il suo perché, col suo suono: i tesserati
        tutti infortunati, nessuno di chi si allena con un punto da spendere, e tutto già al massimo.
        """
        fuoco = wx.Window.FindFocus()
        if self.allenandi and not any(allenamento.puo_allenarsi(g) for g in self.allenandi):
            self.avvisa(testi.tutti_infortunati(self.poli, self.allenandi), self.elenco, "allenandi_tutti_infortunati")
            return
        candidati = [g for g in self.allenandi if allenamento.puo_allenarsi(g) and g.punti_allenamento >= 1]
        if not candidati:
            self.avvisa(testi.nessuno_da_allenare(self.poli), self.elenco, "punti_insufficienti")
            return
        if not self._conferma(testi.domanda_allena_tutti(candidati)):
            self._torna(fuoco)
            return
        spese = [spesa for spesa in (self._secondo_il_programma(g) for g in candidati) if spesa is not None]
        if not spese:
            self.avvisa(testi.tutti_al_massimo(self.poli, candidati), self.elenco, "caratteristica_al_massimo")
            return
        self._racconta(spese, "allenati_tutti", fuoco)

    def _secondo_il_programma(self, g):
        """Spende il portafoglio di g secondo il suo programma; la quintupla dell'esito, o None se niente è salito."""
        valore_prima, classe_prima, prima = g.indice_collettivo_valore, testi.codice_classe(g), g.punti_allenamento
        spese = allenamento.allena_secondo_programma(g, self._data())
        if not spese:
            return None
        return g, spese, prima - g.punti_allenamento, valore_prima, classe_prima

    def _racconta(self, fatte, suono, fuoco):
        """
        Dopo le spese: il valore collettivo della polisportiva si ricalcola, ogni spesa va in esiti
        per il riepilogo, la classe guadagnata nel diario, e il messaggio breve dice una riga per
        allenando, con il suono dell'operazione e quello della classe in coda. Poi la sala si
        aggiorna e il fuoco torna dov'era.
        """
        self.poli.aggiorna_ict(self.mondo.giocatori, self.mondo._ids_morti_processati_sessione)
        righe = []
        salita = False
        for g, spese, spesi, valore_prima, classe_prima in fatte:
            riga = testi.esito_allenamento(g, spesi, valore_prima, classe_prima)
            righe.append(riga + ".")
            self.esiti.append(testi.voce_della_sala(riga, spese))
            if testi.sale_di_classe(g, classe_prima):
                salita = True
                self.mondo.annota(g, testi.voce_classe_salita(g))
        suoni.suona(suono)
        if salita:
            suoni.in_coda("classe_salita")
        wx.MessageBox("\n".join(righe), self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna()
        self._torna(fuoco)

    # Programma e intensità, che valgono subito.

    def al_programma(self, event=None):
        g = self._scelto()
        if g is None:
            return
        nuovo = self.indoli[self.programma.GetSelection()]
        if nuovo == g.programma:
            return
        g.programma = nuovo
        suoni.suona("programma_cambiato")
        self.aggiorna()

    def all_intensita(self, event=None):
        g = self._scelto()
        if g is None:
            return
        nuova = self.livelli[self.intensita.GetSelection()]
        if nuova == g.intensita:
            return
        g.intensita = nuova
        suoni.suona("intensita_cambiata")
        self.aggiorna()

    def all_automatica(self, event=None):
        """La casella dell'iscrizione automatica ai tornei, punto 12.4: vale subito, col suo suono, acceso o spento."""
        g = self._scelto()
        if g is None:
            return
        nuova = bool(self.automatica.GetValue())
        if nuova == bool(g.iscrizione_automatica):
            return
        g.iscrizione_automatica = nuova
        suoni.suona("iscrizione_automatica_accesa" if nuova else "iscrizione_automatica_spenta")
        self.aggiorna()

    def cambi(self):
        """Le righe dei tesserati a cui sono cambiati programma, intensità o iscrizione automatica rispetto all'apertura."""
        return [testi.cambio_in_sala(g) for g in self.allenandi if (g.programma, g.intensita, g.iscrizione_automatica) != self.di_partenza[g.id]]

    def scheda(self, event=None):
        g = self._scelto()
        if g is None:
            suoni.suona("nessuna_selezione")
            return
        self._scheda_del_giocatore(g, self.impostazioni)


class Contratti(_Dialogo):
    """
    I contratti e i rinnovi della decisione D31, tappa 11: i tesserati della polisportiva, dal
    contratto che scade prima, con lo stipendio fisso, la scadenza e lo stato del rinnovo. Per il
    tesserato scelto lo stipendio offerto parte dalla sua richiesta e la durata da quella che
    propone; l'esito previsto, in un campo che si raggiunge con Tab, dice la probabilità che accetti,
    e a ogni ritocco, quando ci si ferma, un tic la fa sentire con la sua altezza, come al mercato.
    Proponi il rinnovo chiede conferma; se la proposta non si può fare, l'avviso dice il perché con
    il suo suono. In esiti restano le coppie di testo ed esito delle proposte, accettato, rifiutato o
    chiuso, che la finestra riepiloga alla chiusura.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None):
        super().__init__(genitore, f"Contratti di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.esiti = []
        # Dal contratto che scade prima; chi per qualche ragione non ha contratto, in fondo.
        oggi = mondo.datetime_corrente_simulazione
        self.rosa = sorted((mondo.giocatori[gid] for gid in poli.tesserati if gid in mondo.giocatori),
                           key=lambda g: (g.contratto_scadenza is None, g.contratto_scadenza or oggi, testi.nome_completo(g).casefold()))
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Tesserati")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Stipendio offerto, in euro al mese")
        self.stipendio = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=10_000_000, initial=STIPENDIO_MINIMO))
        self.etichetta("&Durata, in mesi")
        self.durata = self.aggiungi(wx.SpinCtrl(self.pannello, min=MESI_CONTRATTO_MIN, max=MESI_CONTRATTO_MAX, initial=MESI_CONTRATTO_MIN))
        self.etichetta("Es&ito previsto")
        self.previsto = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
        proponi, scheda, _chiudi = self.pulsanti((wx.ID_ANY, "Pro&poni il rinnovo"), (wx.ID_ANY, "S&cheda"), (wx.ID_CANCEL, "C&hiudi"))
        proponi.Bind(wx.EVT_BUTTON, self.proponi)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.elenco.Bind(wx.EVT_LISTBOX, self.al_tesserato)
        for campo in (self.stipendio, self.durata):
            campo.Bind(wx.EVT_SPINCTRL, self.al_ritocco)
            campo.Bind(wx.EVT_TEXT, self.al_ritocco)
        self.aggiorna(0)
        self.al_tesserato()
        self.completa((640, 520))
        self.elenco.SetFocus()

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.rosa):
            return None
        return self.rosa[indice]

    def aggiorna(self, posto=None):
        """La testata con cassa, sponsor e stipendi, e l'elenco dei tesserati, tenendo il posto; poi l'esito previsto."""
        posto = self.elenco.GetSelection() if posto is None else posto
        self.info.SetLabel(testi.testata_contratti(self.poli, self.mondo))
        self._riscrivi(self.elenco, [testi.riga_contratto(g, self.poli, self.mondo) for g in self.rosa], posto)
        self.aggiorna_previsto()
        self.pannello.Layout()

    def al_tesserato(self, event=None):
        """Per il tesserato scelto la durata parte da quella che propone, lo stipendio dalla sua richiesta per quella durata."""
        g = self._scelto()
        if g is None:
            return
        mesi = contratti.durata_proposta(g)
        self.durata.SetValue(mesi)
        self.stipendio.SetValue(contratti.richiesta_rinnovo(g, self.poli, mesi))
        self.aggiorna_previsto()

    def _si_puo_proporre(self, g):
        """Vero se oggi al tesserato si può proporre il rinnovo, stipendio e durata a parte."""
        return self.mondo.problema_rinnovo(self.poli, g) is None

    def aggiorna_previsto(self):
        """L'esito previsto con stipendio e durata del momento; se oggi la proposta non si può fare, il perché."""
        g = self._scelto()
        if g is None:
            testo = ""
        else:
            testo = self.mondo.problema_rinnovo(self.poli, g) or testi.esito_previsto_rinnovo(g, self.poli, self.stipendio.GetValue(), self.durata.GetValue())
        if self.previsto.GetValue() != testo:
            self.previsto.ChangeValue(testo)

    def al_ritocco(self, event=None):
        self.aggiorna_previsto()
        g = self._scelto()
        if g is not None and self._si_puo_proporre(g):
            self.suona_fra_poco(self.tic_della_probabilita)

    def tic_della_probabilita(self):
        """Il tic della probabilità del rinnovo, all'altezza di stipendio e durata scritti nei campi."""
        g = self._scelto()
        if g is None:
            return
        percentuale = contratti.probabilita_rinnovo(g, self.poli, self.stipendio.GetValue(), self.durata.GetValue())
        suoni.suona("probabilita_rinnovo", semitoni=suoni.probabilita_in_semitoni(percentuale))

    def _suono_del_problema(self, g):
        """
        Il suono di una proposta che non si può fare, nell'ordine in cui il mondo controlla: già
        rinnovato, fuori dalla finestra, proposte finite, già proposto oggi, e i campi da correggere.
        """
        oggi = self.mondo.datetime_corrente_simulazione
        if g.id not in self.poli.tesserati or not contratti.ha_contratto(g):
            return "nessuna_selezione"
        if contratti.ha_rinnovo(g):
            return "rinnovo_gia_concordato"
        if not contratti.in_finestra(g, oggi):
            return "rinnovo_fuori_finestra"
        if not contratti.puo_trattare(g):
            return "rinnovo_senza_proposte"
        if g.ultima_trattativa is not None and g.ultima_trattativa.date() == oggi.date():
            return "rinnovo_gia_proposto_oggi"
        return "campo_da_correggere"

    def proponi(self, event=None):
        """La proposta di rinnovo al tesserato scelto, con stipendio e durata dei campi, dopo la conferma."""
        fuoco = wx.Window.FindFocus()
        g = self._scelto()
        if g is None:
            suoni.suona("nessuna_selezione")
            return
        stipendio, mesi = self.stipendio.GetValue(), self.durata.GetValue()
        problema = self.mondo.problema_rinnovo(self.poli, g, stipendio, mesi)
        if problema:
            suono = self._suono_del_problema(g)
            if suono != "campo_da_correggere":
                campo = self.elenco
            elif stipendio < STIPENDIO_MINIMO:
                campo = self.stipendio
            else:
                campo = self.durata
            self.avvisa(problema, campo, suono)
            return
        if not self._conferma(testi.domanda_rinnovo(g, self.poli, stipendio, mesi)):
            self._torna(fuoco)
            return
        accettato, _probabilita, richiesta = self.mondo.rinnova(self.poli, g, stipendio, mesi)
        if accettato:
            esito, suono = "accettato", "rinnovo_accettato"
        elif not contratti.puo_trattare(g):
            esito, suono = "chiuso", "rinnovo_chiuso"
        else:
            esito, suono = "rifiutato", "rinnovo_rifiutato"
        testo = testi.esito_rinnovo(g, self.poli, accettato, richiesta, mesi)
        self.esiti.append((testo, esito))
        suoni.suona(suono)
        wx.MessageBox(testo, self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna()
        self._torna(fuoco)

    def scheda(self, event=None):
        g = self._scelto()
        if g is None:
            suoni.suona("nessuna_selezione")
            return
        self._scheda_del_giocatore(g, self.impostazioni)


def _finestra_mercato_e_ricerca():
    """Il modulo della finestra Mercato e ricerca, che importa questo: lo si prende quando serve, come i tornei in gui/sfide.py."""
    from gui import mercato_e_ricerca

    return mercato_e_ricerca


class Staff(_Dialogo):
    """
    Lo staff della polisportiva attiva, tappa 13, progetto 4.2: i tre posti, il capo e i due assistenti,
    ciascuno con l'allenatore, lo stipendio, la scadenza e il rinnovo, o vuoto; in testa la cassa, gli
    stipendi dello staff, le mosse e la qualità dello staff con i suoi effetti. Per il posto scelto, come
    nei contratti dei tesserati, lo stipendio offerto parte dalla richiesta e la durata da quella che
    l'allenatore propone, e l'esito previsto, con il tic della probabilità a ogni ritocco, dice come
    andrebbe il rinnovo. Assumi, per un posto vuoto, apre la finestra Mercato e ricerca sugli allenatori
    liberi, col posto già scelto; Rinnova propone il rinnovo, Licenzia chiede conferma con la buonuscita.
    Non c'è un pulsante predefinito: Invio sull'elenco non fa niente, come nei dialoghi della tappa 12. In
    esiti restano le coppie di testo ed esito delle operazioni, anche delle offerte agli allenatori fatte
    nella finestra, che la finestra principale riepiloga alla chiusura; in esiti_della_finestra il resto
    di quello che si è fatto nella finestra, e l'amichevole scelta lì, che chiude lo staff.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None):
        super().__init__(genitore, f"Staff di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.esiti = []
        self.esiti_della_finestra = _finestra_mercato_e_ricerca().EsitiDellaFinestra()
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Posti dello staff")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Stipendio offerto per il rinnovo, in euro al mese")
        self.stipendio = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=10_000_000, initial=0))
        self.etichetta("&Durata, in mesi")
        self.durata = self.aggiungi(wx.SpinCtrl(self.pannello, min=MESI_CONTRATTO_MIN, max=MESI_CONTRATTO_MAX, initial=MESI_CONTRATTO_MIN))
        self.etichetta("Es&ito previsto")
        self.previsto = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
        assumi, rinnova, licenzia = self.pulsanti((wx.ID_ANY, "&Assumi..."), (wx.ID_ANY, "&Rinnova"), (wx.ID_ANY, "&Licenzia"), predefinito=False)
        scheda, diario, _chiudi = self.pulsanti((wx.ID_ANY, "S&cheda"), (wx.ID_ANY, "Diari&o"), (wx.ID_CANCEL, "C&hiudi"), predefinito=False)
        assumi.Bind(wx.EVT_BUTTON, self.assumi)
        rinnova.Bind(wx.EVT_BUTTON, self.rinnova)
        licenzia.Bind(wx.EVT_BUTTON, self.licenzia)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        diario.Bind(wx.EVT_BUTTON, self.diario)
        self.elenco.Bind(wx.EVT_LISTBOX, self.al_posto)
        for campo in (self.stipendio, self.durata):
            campo.Bind(wx.EVT_SPINCTRL, self.al_ritocco)
            campo.Bind(wx.EVT_TEXT, self.al_ritocco)
        self.aggiorna(0, campi=True)
        self.completa((660, 540))
        self.elenco.SetFocus()

    def _scelto(self):
        """L'allenatore del posto scelto, o None per un posto vuoto o senza scelta."""
        posto = self.elenco.GetSelection()
        if posto == wx.NOT_FOUND:
            return None
        return testi.allenatore_del_posto(self.poli, posto, self.mondo)

    def aggiorna(self, posto=None, campi=False):
        """
        La testata e i tre posti, tenendo la scelta, e l'esito previsto. Con campi, quando l'allenatore del
        posto cambia, anche stipendio e durata ripartono dalla sua richiesta; dopo una proposta restano
        quelli scritti, come nei contratti dei tesserati.
        """
        posto = self.elenco.GetSelection() if posto is None else posto
        self.info.SetLabel(testi.testata_staff(self.poli, self.mondo))
        self._riscrivi(self.elenco, [testi.riga_posto_staff(self.poli, i, self.mondo) for i in range(staff.POSTI)], posto)
        if campi:
            self.al_posto()
        else:
            self.aggiorna_previsto()
        self.pannello.Layout()

    def al_posto(self, event=None):
        """Per l'allenatore scelto la durata parte da quella che propone, lo stipendio dalla sua richiesta per quella durata."""
        a = self._scelto()
        if a is not None:
            oggi = self.mondo.datetime_corrente_simulazione
            mesi = staff.durata_proposta(a, oggi)
            self.durata.SetValue(mesi)
            self.stipendio.SetValue(staff.richiesta_rinnovo(a, self.poli, mesi, oggi))
        self.aggiorna_previsto()

    def aggiorna_previsto(self):
        """L'esito previsto del rinnovo con stipendio e durata del momento; se oggi non si può proporre, il perché; per un posto vuoto, come riempirlo."""
        a = self._scelto()
        if a is None:
            testo = "Posto vuoto: Assumi apre il mercato degli allenatori per questo posto." if self.elenco.GetSelection() != wx.NOT_FOUND else ""
        else:
            oggi = self.mondo.datetime_corrente_simulazione
            testo = (self.mondo.problema_rinnovo_allenatore(self.poli, a)
                     or testi.esito_previsto_rinnovo_staff(a, self.poli, self.stipendio.GetValue(), self.durata.GetValue(), oggi))
        if self.previsto.GetValue() != testo:
            self.previsto.ChangeValue(testo)

    def al_ritocco(self, event=None):
        self.aggiorna_previsto()
        a = self._scelto()
        if a is not None and self.mondo.problema_rinnovo_allenatore(self.poli, a) is None:
            self.suona_fra_poco(self.tic_della_probabilita)

    def tic_della_probabilita(self):
        """Il tic della probabilità del rinnovo, lo stesso dei tesserati, all'altezza di stipendio e durata dei campi."""
        a = self._scelto()
        if a is None:
            return
        percentuale = staff.probabilita_rinnovo(a, self.poli, self.stipendio.GetValue(), self.durata.GetValue(), self.mondo.datetime_corrente_simulazione)
        suoni.suona("probabilita_rinnovo", semitoni=suoni.probabilita_in_semitoni(percentuale))

    def _suono_del_problema(self, a):
        """Il suono di un rinnovo che non si può proporre, coi perché dei tesserati, nell'ordine in cui il mondo controlla."""
        oggi = self.mondo.datetime_corrente_simulazione
        if contratti.ha_rinnovo(a):
            return "rinnovo_gia_concordato"
        if not contratti.in_finestra(a, oggi):
            return "rinnovo_fuori_finestra"
        if not contratti.puo_trattare(a):
            return "rinnovo_senza_proposte"
        if a.ultima_trattativa is not None and a.ultima_trattativa.date() == oggi.date():
            return "rinnovo_gia_proposto_oggi"
        return "campo_da_correggere"

    def apri_il_mercato(self, posto):
        """
        La finestra Mercato e ricerca sugli allenatori liberi, col posto da offrire già scelto, che suona da sé la sua
        apertura e alla chiusura non ricorda niente: un metodo a sé, perché le prove lo sostituiscono. Restituisce gli
        esiti della finestra.
        """
        finestra = _finestra_mercato_e_ricerca().MercatoERicerca(self, self.mondo, self.impostazioni, None, posto=posto)
        try:
            finestra.ShowModal()
            return finestra.esiti_alla_fine()
        finally:
            finestra.Destroy()

    def assumi(self, event=None):
        """
        La finestra Mercato e ricerca per il posto scelto, se è vuoto. Al ritorno le offerte agli allenatori vanno fra
        gli esiti dello staff, il resto fra quelli della finestra, e lo staff si aggiorna; un'amichevole scelta nella
        finestra chiude lo staff, perché la partita la gioca la finestra principale.
        """
        posto = self.elenco.GetSelection()
        if posto == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return
        a = self._scelto()
        if a is not None:
            self.avvisa(f"Il posto è di {testi.nome_completo(a)}: per cambiarlo, prima licenzia.", self.elenco, "staff_posto_occupato")
            return
        esiti = self.apri_il_mercato(posto)
        self.esiti.extend(esiti.allenatori)
        finestra = self.esiti_della_finestra
        finestra.giocatori.extend(esiti.giocatori)
        finestra.sfide.extend(esiti.sfide)
        finestra.preset.extend(esiti.preset)
        if esiti.amichevole is not None:
            finestra.amichevole = esiti.amichevole
            self.chiudi(wx.ID_CANCEL)
            return
        self.aggiorna(campi=True)
        self._torna(self.elenco)

    def rinnova(self, event=None):
        """La proposta di rinnovo all'allenatore scelto, con stipendio e durata dei campi, dopo la conferma."""
        fuoco = wx.Window.FindFocus()
        a = self._scelto()
        if a is None:
            suoni.suona("nessuna_selezione")
            return
        stipendio, mesi = self.stipendio.GetValue(), self.durata.GetValue()
        problema = self.mondo.problema_rinnovo_allenatore(self.poli, a, stipendio, mesi)
        if problema:
            suono = self._suono_del_problema(a)
            campo = self.elenco if suono != "campo_da_correggere" else (self.stipendio if stipendio < 1 else self.durata)
            self.avvisa(problema, campo, suono)
            return
        oggi = self.mondo.datetime_corrente_simulazione
        if not self._conferma(testi.domanda_rinnovo_staff(a, self.poli, stipendio, mesi, oggi)):
            self._torna(fuoco)
            return
        accettato, _probabilita, richiesta = self.mondo.rinnova_allenatore(self.poli, a, stipendio, mesi)
        if accettato:
            esito, suono = "rinnovato", "staff_rinnovo_concordato"
        elif not contratti.puo_trattare(a):
            esito, suono = "chiuso", "staff_rinnovo_chiuso"
        else:
            esito, suono = "rifiutato", "staff_rinnovo_rifiutato"
        testo = testi.esito_rinnovo_staff(a, self.poli, accettato, richiesta, mesi)
        self.esiti.append((testo, esito))
        suoni.suona(suono)
        wx.MessageBox(testo, self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna()
        self._torna(fuoco)

    def licenzia(self, event=None):
        """Il licenziamento dell'allenatore scelto, con la buonuscita nella domanda e il no già scelto."""
        a = self._scelto()
        if a is None:
            suoni.suona("nessuna_selezione")
            return
        problema = self.mondo.problema_licenziamento(self.poli, a)
        if problema:
            self.avvisa(problema, self.elenco, "mosse_finite" if self.mondo.mosse_rimaste(self.poli) <= 0 else "cassa_insufficiente")
            return
        if not self._conferma(testi.domanda_licenziamento(a, self.poli, self.mondo)):
            self._torna(self.elenco)
            return
        buonuscita = self.mondo.licenzia_allenatore(self.poli, a)
        testo = testi.esito_licenziamento(a, self.poli, buonuscita)
        self.esiti.append((testo, "licenziato"))
        suoni.suona("allenatore_licenziato")
        wx.MessageBox(testo, self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna(campi=True)
        self._torna(self.elenco)

    def _leggi(self, titolo, testo, suono):
        """La scheda o il diario di un allenatore, da leggere e chiudere con Esc."""
        dialogo = Lettura(self, titolo, testo, self.impostazioni)
        try:
            suoni.suona(suono)
            dialogo.ShowModal()
        finally:
            dialogo.Destroy()

    def scheda(self, event=None):
        a = self._scelto()
        if a is None:
            suoni.suona("nessuna_selezione")
            return
        self._leggi(f"Scheda di {testi.nome_completo(a)}", testi.scheda_allenatore(a, self.mondo), "scheda_allenatore")

    def diario(self, event=None):
        a = self._scelto()
        if a is None:
            suoni.suona("nessuna_selezione")
            return
        self._leggi(f"Diario di {testi.nome_completo(a)}", testi.diario_allenatore(a), "diario_allenatore")


class OpzioniAmichevole(_Dialogo):
    """
    Le opzioni dell'amichevole fra due giocatori già scelti: al meglio di 3 o di 5 set, come
    seguirla, e il livello della cronaca, sintetica, normale o tecnica, che vale anche per il file.
    Con la decisione D29 i modi di seguirla sono due: Assisti, la partita dal vivo, e Vai alla fine,
    il risultato con la cronaca intera sotto. I predefiniti sono quelli scelti da Gabriele: 3 set,
    Assisti, normale; dall'8 ottobre 2026 il dialogo riparte dalle ultime scelte, che riceve in
    iniziali come terna di set, modo e livello. In risultato restano le tre scelte. Dal 24 ottobre 2026 l'apertura
    conta come un Invio, e un Invio tenuto giù non fa partire l'incontro.
    """

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, mondo, primo, secondo, iniziali=None):
        super().__init__(genitore, "Opzioni dell'amichevole")
        self.risultato = None
        chi = f"Amichevole fra {testi.nome_completo(primo)}, {testi.stato(primo, mondo)}, e {testi.nome_completo(secondo)}, {testi.stato(secondo, mondo)}."
        self.sizer.Add(wx.StaticText(self.pannello, label=chi), 0, wx.ALL, 8)
        self.etichetta("&Set dell'incontro")
        self.set = self.aggiungi(wx.Choice(self.pannello, choices=[f"Al meglio di {n} set" for n in SET_AMMESSI]))
        self.etichetta("&Come seguire l'incontro")
        self.modo = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in MODI_DI_SEGUIRE]))
        self.etichetta("&Livello della cronaca, anche per il file")
        self.livello = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in LIVELLI_DI_CRONACA]))
        set_al_meglio, modo, livello = iniziali or (SET_AMMESSI[0], ASSISTI, cronaca.NORMALE)
        modi = [chiave for chiave, _nome in MODI_DI_SEGUIRE]
        livelli = [chiave for chiave, _nome in LIVELLI_DI_CRONACA]
        self.set.SetSelection(SET_AMMESSI.index(set_al_meglio) if set_al_meglio in SET_AMMESSI else 0)
        self.modo.SetSelection(modi.index(modo) if modo in modi else 0)
        self.livello.SetSelection(livelli.index(livello) if livello in livelli else livelli.index(cronaca.NORMALE))
        gioca, _annulla = self.pulsanti((wx.ID_OK, "&Gioca"), (wx.ID_CANCEL, "Annulla"))
        gioca.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((460, 340))
        self.set.SetFocus()

    def conferma(self, event=None):
        self.risultato = (SET_AMMESSI[self.set.GetSelection()], MODI_DI_SEGUIRE[self.modo.GetSelection()][0], LIVELLI_DI_CRONACA[self.livello.GetSelection()][0])
        self.chiudi(wx.ID_OK)


class VelocitaDiGioco(_Dialogo):
    """
    La velocità di gioco della partita dal vivo, decisioni D12 e D29, sul modello della velocità di
    combattimento di Terminal Beast, adattato: là un numero di millesimi fra un'azione e l'altra, qui
    un numero da 1 a 8 che divide le pause e la procedura dell'arbitro, mai l'azione. In risultato
    resta la velocità scelta.
    """

    def __init__(self, genitore, velocita):
        super().__init__(genitore, "Velocità di gioco")
        self.risultato = None
        self.sizer.Add(wx.StaticText(self.pannello, label=testi.SPIEGAZIONE_VELOCITA), 0, wx.ALL, 8)
        self.etichetta(f"&Velocità di gioco, da {modulo_impostazioni.VELOCITA_MINIMA} a {modulo_impostazioni.VELOCITA_MASSIMA}")
        self.velocita = self.aggiungi(wx.SpinCtrl(self.pannello, min=modulo_impostazioni.VELOCITA_MINIMA, max=modulo_impostazioni.VELOCITA_MASSIMA, initial=velocita))
        salva, _annulla = self.pulsanti((wx.ID_OK, "&Salva"), (wx.ID_CANCEL, "Annulla"))
        salva.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((440, 240))
        self.velocita.SetFocus()

    def conferma(self, event=None):
        self.risultato = self.velocita.GetValue()
        self.chiudi(wx.ID_OK)


class AnnunciDellaCronaca(_Dialogo):
    """
    Gli annunci della cronaca, 1.79.0, chiesti da Gabriele: se la cronaca della partita dal vivo e della
    differita si legge in automatico, dove va, con quale sintesi, quante celle ha il display braille, 0
    se non importa, e il tempo minimo di lettura di ogni blocco. In risultato restano le scelte, con le
    chiavi delle impostazioni.
    """

    def __init__(self, genitore, impostazioni):
        super().__init__(genitore, "Annunci della cronaca")
        valide = modulo_impostazioni.valide(impostazioni)
        self.risultato = None
        self.sizer.Add(wx.StaticText(self.pannello, label=testi.SPIEGAZIONE_ANNUNCI), 0, wx.ALL, 8)
        self.leggi = self.aggiungi(wx.CheckBox(self.pannello, label="&Leggi la cronaca in automatico"))
        self.leggi.SetValue(valide["annunci_cronaca"])
        self.etichetta("&Dove vanno le righe")
        self._dove = list(testi.DESTINAZIONI_DEGLI_ANNUNCI)
        self.dove = self.aggiungi(wx.Choice(self.pannello, choices=list(testi.DESTINAZIONI_DEGLI_ANNUNCI.values())))
        self.dove.SetSelection(self._dove.index(valide["annunci_dove"]))
        self.etichetta("S&intesi")
        self._sintesi = list(testi.SINTESI_DEGLI_ANNUNCI)
        self.sintesi = self.aggiungi(wx.Choice(self.pannello, choices=list(testi.SINTESI_DEGLI_ANNUNCI.values())))
        self.sintesi.SetSelection(self._sintesi.index(valide["annunci_sintesi"]))
        self.etichetta(f"&Celle del display braille, da 0, che vuol dire non importa, a {modulo_impostazioni.CELLE_MASSIME}")
        self.celle = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=modulo_impostazioni.CELLE_MASSIME, initial=valide["annunci_celle"]))
        self.etichetta(f"&Tempo minimo di lettura di ogni blocco in braille, in millesimi, da {modulo_impostazioni.LETTURA_MINIMA} "
                       f"a {modulo_impostazioni.LETTURA_MASSIMA}")
        self.lettura = self.aggiungi(wx.SpinCtrl(self.pannello, min=modulo_impostazioni.LETTURA_MINIMA, max=modulo_impostazioni.LETTURA_MASSIMA,
                                                 initial=valide["annunci_lettura_minima"]))
        salva, _annulla = self.pulsanti((wx.ID_OK, "&Salva"), (wx.ID_CANCEL, "Annulla"))
        salva.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((520, 440))
        self.leggi.SetFocus()

    def conferma(self, event=None):
        self.risultato = {"annunci_cronaca": self.leggi.GetValue(), "annunci_dove": self._dove[self.dove.GetSelection()],
                          "annunci_sintesi": self._sintesi[self.sintesi.GetSelection()], "annunci_celle": self.celle.GetValue(),
                          "annunci_lettura_minima": self.lettura.GetValue()}
        self.chiudi(wx.ID_OK)


class Lettura(_Dialogo):
    """Un testo da leggere in un'area in sola lettura, con i pulsanti dati: la fine sessione e l'invito al caffè."""

    def __init__(self, genitore, titolo, testo, impostazioni=None, pulsanti=((wx.ID_OK, "&Chiudi"),)):
        super().__init__(genitore, titolo)
        self.testo = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2, value=testo), 1)
        if impostazioni:
            aspetto.applica(self.testo, impostazioni)
        self.bottoni = self.pulsanti(*pulsanti)
        self.bottoni[-1].Bind(wx.EVT_BUTTON, lambda event: self.chiudi(wx.ID_OK))
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.completa((560, 420))
        wx.CallAfter(self._al_testo)

    def _al_testo(self):
        with contextlib.suppress(RuntimeError):
            self.testo.SetInsertionPoint(0)
            self.testo.SetFocus()

    def _tasto(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.chiudi(wx.ID_OK)
        else:
            event.Skip()


# Il tempo entro cui un Invio dopo l'apertura del dialogo, o dopo un altro Invio, vale come tasto tenuto giù:
# con NVDA, nei campi di testo, ogni ripetizione arriva come una pressione nuova e IsAutoRepeat non la vede
# (la trappola di Tornello del 27 settembre 2026). Gli 0,65 secondi di serie della grazia di GBwx 1.1.1,
# che Gabriele ha provato con NVDA il 23 ottobre 2026 nella finestra della mail.
GRAZIA_INVIO = 0.65


def _adesso():
    return time.monotonic()


def invio_da_ignorare(dialogo, event):
    """Vero se l'Invio arriva entro la grazia dall'apertura del dialogo o dall'Invio precedente: un tasto tenuto giù."""
    adesso = _adesso()
    precedente, dialogo.ultimo_invio = dialogo.ultimo_invio, adesso
    return event.IsAutoRepeat() or adesso - precedente < GRAZIA_INVIO


class Caffe(Lettura):
    """L'invito a offrire un caffè, solo a richiesta dal menu Aiuto, con Dona con PayPal e Chiudi."""

    def __init__(self, genitore, testo, impostazioni=None):
        super().__init__(genitore, "Offrimi un caffè", testo, impostazioni, ((wx.ID_ANY, "Dona con &PayPal"), (wx.ID_OK, "&Chiudi")))
        self.bottoni[0].Bind(wx.EVT_BUTTON, self.dona)
        # Invio chiude: donare deve essere una scelta, non un tasto premuto per abitudine.
        self.bottoni[-1].SetDefault()
        # L'apertura conta come un Invio: quello tenuto giù dalla voce del menu non chiude l'invito appena aperto.
        self.ultimo_invio = _adesso()

    def _tasto(self, event):
        """
        Invio nel testo chiude come Chiudi, come Esc: l'area in sola lettura su più righe, che ha il
        fuoco, si tiene Invio, e il pulsante predefinito da solo non basta, terza revisione della tappa
        14. Sui pulsanti Invio resta loro; un Invio tenuto giù non risponde, anche con NVDA, grazie a
        invio_da_ignorare, come nell'Aggiornamento.
        """
        tasto = event.GetKeyCode()
        if event.GetEventObject() is self.testo and tasto in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not invio_da_ignorare(self, event):
            self.chiudi(wx.ID_OK)
        else:
            super()._tasto(event)

    def dona(self, event=None):
        suoni.suona("caffe_paypal")
        with contextlib.suppress(webbrowser.Error):
            webbrowser.open(PAYPAL_URL)
        self.chiudi(wx.ID_OK)


def durata_dell_attesa(secondi):
    """Quanto aspetta la proposta dell'aggiornamento, a parole: 2 minuti, 1 minuto e 30 secondi, 45 secondi."""
    minuti, resto = divmod(max(0, round(secondi)), 60)
    parti = ([testi.conta(minuti, "minuto", "minuti")] if minuti else []) + ([testi.conta(resto, "secondo", "secondi")] if resto or not minuti else [])
    return " e ".join(parti)


class Aggiornamento(Lettura):
    """
    La proposta dell'aggiornamento automatico, tappa 14: nel testo in sola lettura, che ha il fuoco
    all'apertura, la versione nuova, quella che si ha e le note della release; i pulsanti Aggiorna e
    Non adesso, che è il predefinito. Esc, e Invio nel testo, valgono Non adesso: aggiornare si
    sceglie solo con il suo pulsante. Con attesa, in secondi, il dialogo si chiude da solo come Non
    adesso allo scadere, e l'aggiornamento torna al prossimo avvio. Il codice di ShowModal è wx.ID_YES
    per aggiornare, wx.ID_NO altrimenti; scaduta dice se il no è venuto dallo scadere dell'attesa.
    """

    def __init__(self, genitore, versione_attuale, versione_nuova, note, attesa=None, impostazioni=None):
        righe = [f"È disponibile MESS {versione_nuova}; tu hai la {versione_attuale}.",
                 "Aggiorna scarica la versione nuova; poi MESS salva il mondo, si chiude e si riapre aggiornato, con il tuo mondo e le tue impostazioni."]
        if attesa:
            righe.append(f"Se non rispondi entro {durata_dell_attesa(attesa)}, il dialogo si chiude da solo e te lo ripropongo al prossimo avvio.")
        righe += ["Le note della release:", (note or "").strip() or "Nessuna nota scritta per questa versione."]
        super().__init__(genitore, "Aggiornamento di MESS", "\n".join(righe), impostazioni, ((wx.ID_YES, "&Aggiorna"), (wx.ID_NO, "&Non adesso")))
        self.bottoni[0].Bind(wx.EVT_BUTTON, lambda event: self.chiudi(wx.ID_YES))
        # Lettura lega l'ultimo pulsante alla chiusura con OK: qui vale Non adesso.
        self.bottoni[-1].Unbind(wx.EVT_BUTTON)
        self.bottoni[-1].Bind(wx.EVT_BUTTON, lambda event: self.chiudi(wx.ID_NO))
        self.bottoni[-1].SetDefault()
        self.SetEscapeId(wx.ID_NO)
        # Vero se il dialogo si è chiuso da solo, allo scadere: la finestra le dà un suono diverso da Non adesso.
        self.scaduta = False
        # L'apertura conta come un Invio: il dialogo compare da solo all'avvio, magari mentre si preme Invio altrove.
        self.ultimo_invio = _adesso()
        self._scadenza = wx.CallLater(round(attesa * 1000), self._scaduta) if attesa else None

    def _tasto(self, event):
        """Esc, e Invio nel testo, valgono Non adesso; sui pulsanti Invio resta loro. Un Invio tenuto giù non risponde, anche con NVDA."""
        tasto = event.GetKeyCode()
        nel_testo = (event.GetEventObject() is self.testo and tasto in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER)
                     and not invio_da_ignorare(self, event))
        if tasto == wx.WXK_ESCAPE or nel_testo:
            self.chiudi(wx.ID_NO)
        else:
            event.Skip()

    def chiudi(self, codice):
        if self._scadenza is not None:
            self._scadenza.Stop()
        super().chiudi(codice)

    def _scaduta(self):
        # Il dialogo può essere già chiuso, o distrutto.
        if self and self.IsModal():
            self.scaduta = True
            self.EndModal(wx.ID_NO)


# La cartella del mondo, richiesta di Gabriele del 23 ottobre 2026: la scelta con la finestra di Windows,
# la domanda quando la cartella scelta ha già un mondo, e l'avviso dell'avvio quando la cartella non c'è.
# I codici d'uscita delle scelte. Esci è un annullamento, come vuole la regola di Esc di tutti i dialoghi.
USA_IL_MONDO_DELLA_CARTELLA = wx.ID_YES
PORTA_IL_MIO_MONDO = wx.ID_NO
RIPROVA = wx.ID_RETRY
UN_ALTRA_CARTELLA = wx.ID_OPEN
ESCI = wx.ID_CANCEL


def scegli_cartella(genitore, titolo, partenza=""):
    """
    La finestra di Windows che sceglie una cartella, wx.DirDialog, nativa e accessibile: la cartella
    scelta, o None se la si chiude con Annulla. Parte dalla cartella data, se c'è. Una funzione a sé,
    perché le prove la sostituiscono: una finestra di Windows vera aspetterebbe per sempre.
    """
    dialogo = wx.DirDialog(genitore, titolo, partenza if partenza and os.path.isdir(partenza) else "", wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    try:
        return dialogo.GetPath() if dialogo.ShowModal() == wx.ID_OK else None
    finally:
        dialogo.Destroy()


class _SceltaConTesto(_Dialogo):
    """
    Un testo da leggere, in un'area in sola lettura che ha il fuoco all'apertura, e una riga di
    pulsanti, ciascuno col suo codice d'uscita; predefinita è il codice del pulsante di Invio, ed Esc
    vale l'ultimo. Dalla revisione del 23 ottobre 2026 Invio nel testo vale il predefinito, come nel
    caffè e nell'aggiornamento, perché l'area su più righe si tiene il tasto; e un Invio tenuto giù non
    risponde, anche con NVDA, invio_da_ignorare: l'apertura conta come un Invio, così quello rimasto
    dalla finestra di Windows che sceglie la cartella non annulla la domanda appena aperta, né ripete
    Riprova a raffica nell'avviso dell'avvio.
    """

    def __init__(self, genitore, titolo, testo, scelte, predefinita, impostazioni=None):
        super().__init__(genitore, titolo)
        self.testo = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2, value=testo), 1)
        if impostazioni:
            aspetto.applica(self.testo, impostazioni)
        self.bottoni = self.pulsanti(*scelte, predefinito=False)
        for bottone, (codice, _etichetta) in zip(self.bottoni, scelte, strict=True):
            bottone.Bind(wx.EVT_BUTTON, lambda event, c=codice: self.chiudi(c))
        self.predefinita = predefinita
        self.bottoni[[codice for codice, _etichetta in scelte].index(predefinita)].SetDefault()
        self.SetEscapeId(scelte[-1][0])
        self.ultimo_invio = _adesso()
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.completa((560, 420))
        wx.CallAfter(self._al_testo)

    def _al_testo(self):
        with contextlib.suppress(RuntimeError):
            self.testo.SetInsertionPoint(0)
            self.testo.SetFocus()

    def _tasto(self, event):
        """Invio, ovunque sia il fuoco, non risponde se è tenuto giù; nel testo vale il predefinito, sui pulsanti resta loro."""
        if event.GetKeyCode() not in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) or event.HasAnyModifiers():
            event.Skip()
        elif invio_da_ignorare(self, event):
            return
        elif event.GetEventObject() is self.testo:
            self.chiudi(self.predefinita)
        else:
            event.Skip()


class MondoGiaPresente(_SceltaConTesto):
    """
    La cartella scelta dal menu Impostazioni ha già un mondo: il testo dice quando è stato salvato
    l'uno e l'altro e quale è il più recente, e il suo pulsante lo dice anche lui. Le scelte sono Usa
    il mondo della cartella, Porta il mio mondo e Annulla, che è il predefinito e vale anche per Esc:
    un Invio di troppo non deve spostare un mondo. Con usabile falso, quando il mondo della cartella non
    si legge o quello aperto non si potrebbe salvare, Usa il mondo della cartella non c'è.
    """

    def __init__(self, genitore, testo, piu_recente, impostazioni=None, usabile=True):
        usa = "&Usa il mondo della cartella" + (", il più recente" if piu_recente == testi.QUELLO_DELLA_CARTELLA else "")
        porta = "&Porta il mio mondo" + (", il più recente" if piu_recente == testi.IL_TUO else "")
        scelte = ((USA_IL_MONDO_DELLA_CARTELLA, usa),) if usabile else ()
        super().__init__(genitore, "Nella cartella c'è già un mondo", testo,
                         (*scelte, (PORTA_IL_MIO_MONDO, porta), (wx.ID_CANCEL, "Annulla")), wx.ID_CANCEL, impostazioni)


class _AvvisoDellAvvio(_SceltaConTesto):
    """Un avviso dell'avvio che ferma il mondo: Riprova, il predefinito, Scegli un'altra cartella ed Esci, che vale anche per Esc."""

    def __init__(self, genitore, titolo, testo):
        super().__init__(genitore, titolo, testo, ((RIPROVA, "&Riprova"), (UN_ALTRA_CARTELLA, "&Scegli un'altra cartella"), (ESCI, "&Esci")), RIPROVA)


class CartellaAssente(_AvvisoDellAvvio):
    """L'avviso dell'avvio quando la cartella del mondo non c'è, non si sa dove sia, o c'è ma senza un mondo."""

    def __init__(self, genitore, testo):
        super().__init__(genitore, "MESS non trova il mondo", testo)


class MondoIllegibile(_AvvisoDellAvvio):
    """L'avviso dell'avvio quando il salvataggio c'è ma non si legge, e nemmeno la sua copia: dalla revisione del 23 ottobre 2026 non ferma più MESS senza scelte."""

    def __init__(self, genitore, testo):
        super().__init__(genitore, "MESS, il salvataggio non si legge", testo)
