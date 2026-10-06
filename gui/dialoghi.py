"""
I dialoghi della finestra di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano. Ogni dialogo segue lo schema di GBwx: stile
adattabile, controlli in un pannello che scorre, misura presa dal contenuto, così i caratteri
grandi non lasciano niente fuori dallo schermo. Solo controlli nativi a selezione singola, e
ogni campo ha davanti la sua etichetta, da cui lo screen reader prende il nome.
"""

import contextlib
import webbrowser

import wx
from GBwx import STILE_ADATTABILE, adatta_finestra, pannello_scorrevole

import impostazioni as modulo_impostazioni
import ricerca
import testi
from gui import aspetto

PAYPAL_URL = "https://paypal.me/GabrieleBattaglia780"


class _Dialogo(wx.Dialog):
    """La base dei dialoghi: pannello che scorre, sizer verticale, chiusura con Esc."""

    def __init__(self, genitore, titolo):
        super().__init__(genitore, title=titolo, style=STILE_ADATTABILE)
        self.pannello = pannello_scorrevole(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

    def etichetta(self, testo):
        self.sizer.Add(wx.StaticText(self.pannello, label=testo), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

    def aggiungi(self, controllo, proporzione=0):
        self.sizer.Add(controllo, proporzione, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        return controllo

    def pulsanti(self, *voci):
        """Una riga di pulsanti: coppie di identificativo e testo; il primo è quello predefinito."""
        riga = wx.BoxSizer(wx.HORIZONTAL)
        creati = []
        for identificativo, testo in voci:
            pulsante = wx.Button(self.pannello, identificativo, testo)
            riga.Add(pulsante, 0, wx.ALL, 4)
            creati.append(pulsante)
        creati[0].SetDefault()
        self.sizer.Add(riga, 0, wx.ALIGN_RIGHT | wx.ALL, 4)
        return creati

    def completa(self, misura):
        self.pannello.SetSizer(self.sizer)
        adatta_finestra(self, self.pannello, misura)

    def chiudi(self, codice):
        """Chiude il dialogo con il codice dato; fuori da ShowModal, come nei collaudi, lo annota soltanto."""
        if self.IsModal():
            self.EndModal(codice)
        else:
            self.SetReturnCode(codice)


class SceltaGiocatore(_Dialogo):
    """La scelta di un giocatore: un campo per il numero o il nome e l'elenco, che si restringe mentre si scrive."""

    def __init__(self, genitore, mondo, titolo="Scheda del giocatore", pulsante="&Mostra la scheda"):
        super().__init__(genitore, titolo)
        self.mondo = mondo
        self.scelto = None
        self.tutti = sorted(mondo.giocatori.values(), key=lambda g: g.id)
        self.visibili = []
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

    def conferma(self, event=None):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.Bell()
            return
        self.scelto = self.visibili[indice]
        self.chiudi(wx.ID_OK)


class Ricerca(_Dialogo):
    """La ricerca dei giocatori: dove cercare, la caratteristica, la condizione e il valore."""

    def __init__(self, genitore):
        super().__init__(genitore, "Cerca giocatori")
        self.risultato = None
        self.etichetta("&Dove cercare")
        self.ambito = self.aggiungi(wx.Choice(self.pannello, choices=[nome.capitalize() for _chiave, nome in ricerca.AMBITI]))
        self.etichetta("&Caratteristica")
        self.criterio = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome, _tipo, _leggi in ricerca.CRITERI]))
        self.etichetta("C&ondizione")
        self.condizione = self.aggiungi(wx.Choice(self.pannello))
        self.etichetta("&Valore")
        self.valore = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PROCESS_ENTER))
        cerca, _annulla = self.pulsanti((wx.ID_OK, "C&erca"), (wx.ID_CANCEL, "Annulla"))
        self.ambito.SetSelection(0)
        self.criterio.SetSelection(0)
        self.criterio.Bind(wx.EVT_CHOICE, self.al_criterio)
        self.valore.Bind(wx.EVT_TEXT_ENTER, self.conferma)
        cerca.Bind(wx.EVT_BUTTON, self.conferma)
        self.al_criterio()
        self.completa((440, 360))
        self.ambito.SetFocus()

    def chiave_criterio(self):
        return ricerca.CRITERI[self.criterio.GetSelection()][0]

    def al_criterio(self, event=None):
        """Le condizioni giuste per la caratteristica scelta; per il sì o no il valore non serve."""
        tipo = ricerca.tipo_criterio(self.chiave_criterio())
        self.condizione.Set([nome for _chiave, nome in ricerca.CONDIZIONI[tipo]])
        self.condizione.SetSelection(0)
        self.valore.Enable(tipo != ricerca.SI_NO)

    def conferma(self, event=None):
        """Controlla il valore e conserva la ricerca in risultato: ambito, criterio, condizione, valore e descrizione."""
        criterio = self.chiave_criterio()
        tipo = ricerca.tipo_criterio(criterio)
        condizione = ricerca.CONDIZIONI[tipo][self.condizione.GetSelection()][0]
        testo = self.valore.GetValue().strip()
        valore = None
        if tipo == ricerca.NUMERO:
            try:
                valore = ricerca.leggi_numero(testo)
            except ValueError:
                wx.MessageBox("Il valore deve essere un numero, per esempio 150 o 12,5.", "Cerca giocatori", wx.OK | wx.ICON_WARNING, self)
                self.valore.SetFocus()
                return
        elif tipo == ricerca.TESTO:
            if not testo:
                wx.MessageBox("Scrivi il testo da cercare.", "Cerca giocatori", wx.OK | wx.ICON_WARNING, self)
                self.valore.SetFocus()
                return
            valore = testo
        ambito = ricerca.AMBITI[self.ambito.GetSelection()][0]
        descrizione = f"{ricerca.nome_ambito(ambito)}, {ricerca.nome_criterio(criterio).lower()} {ricerca.nome_condizione(criterio, condizione)}"
        if valore is not None:
            descrizione += f" {testi.numero(valore) if tipo == ricerca.NUMERO else valore}"
        self.risultato = (ambito, criterio, condizione, valore, descrizione)
        self.chiudi(wx.ID_OK)


class Aspetto(_Dialogo):
    """Le impostazioni d'aspetto, sul modello di quelle di Terminal Beast: anteprima, caratteri e colori."""

    def __init__(self, genitore, impostazioni):
        super().__init__(genitore, "Aspetto")
        self.risultato = None
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
            "dimensione": self.dimensione.GetValue(),
            "colore_testo": [c.GetValue() for c in self.testo],
            "colore_sfondo": [c.GetValue() for c in self.sfondo],
        })

    def aggiorna(self, event=None):
        aspetto.applica(self.anteprima, self.valori())

    def ai_predefiniti(self, event=None):
        predefinite = modulo_impostazioni.valide(None)
        self.dimensione.SetValue(predefinite["dimensione"])
        for controlli, valori in ((self.testo, predefinite["colore_testo"]), (self.sfondo, predefinite["colore_sfondo"])):
            for controllo, valore in zip(controlli, valori, strict=True):
                controllo.SetValue(valore)
        self.aggiorna()

    def conferma(self, event=None):
        self.risultato = self.valori()
        self.chiudi(wx.ID_OK)


class Conservazione(_Dialogo):
    """Per quanti giorni simulati si conservano le voci dei diari, come la pulizia dei diari di Terminal Beast."""

    def __init__(self, genitore, conservazione):
        super().__init__(genitore, "Conservazione dei diari")
        self.risultato = None
        self.sizer.Add(wx.StaticText(self.pannello, label="Per quanti giorni simulati si conservano le voci dei diari. Zero vuol dire per sempre."), 0, wx.ALL, 8)
        self.etichetta("Giorni per i diari dei &giocatori")
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


class Caffe(Lettura):
    """L'invito a offrire un caffè, solo a richiesta dal menu Aiuto, con Dona con PayPal e Chiudi."""

    def __init__(self, genitore, testo, impostazioni=None):
        super().__init__(genitore, "Offrimi un caffè", testo, impostazioni, ((wx.ID_ANY, "Dona con &PayPal"), (wx.ID_OK, "&Chiudi")))
        self.bottoni[0].Bind(wx.EVT_BUTTON, self.dona)
        # Invio chiude: donare deve essere una scelta, non un tasto premuto per abitudine.
        self.bottoni[-1].SetDefault()

    def dona(self, event=None):
        with contextlib.suppress(webbrowser.Error):
            webbrowser.open(PAYPAL_URL)
        self.chiudi(wx.ID_OK)
