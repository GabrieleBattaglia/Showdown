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
"""

import contextlib
import webbrowser

import wx
from GBwx import STILE_ADATTABILE, adatta_finestra, pannello_scorrevole

import impostazioni as modulo_impostazioni
import mercato
import ricerca
import testi
from costanti import NOME_POLISPORTIVA_MAX, NOME_POLISPORTIVA_MIN
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

    def avvisa(self, testo, controllo):
        """Un avviso che lascia il dialogo aperto, con il cursore sul campo da correggere."""
        wx.MessageBox(testo, self.GetTitle(), wx.OK | wx.ICON_WARNING, self)
        controllo.SetFocus()


class SceltaGiocatore(_Dialogo):
    """La scelta di un giocatore: un campo per il numero o il nome e l'elenco, che si restringe mentre si scrive."""

    def __init__(self, genitore, mondo, titolo="Scheda del giocatore", pulsante="&Mostra la scheda", giocatori=None):
        super().__init__(genitore, titolo)
        self.mondo = mondo
        self.scelto = None
        self.tutti = sorted(mondo.giocatori.values() if giocatori is None else giocatori, key=lambda g: g.id)
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
    """
    La ricerca dei giocatori: dove cercare, la caratteristica, la condizione e il valore. Senza la
    scelta di dove cercare è il filtro del mercato, che cerca sempre fra i liberi.
    """

    def __init__(self, genitore, con_ambito=True, titolo="Cerca giocatori", pulsante="C&erca"):
        super().__init__(genitore, titolo)
        self.risultato = None
        self.ambito = None
        if con_ambito:
            self.etichetta("&Dove cercare")
            self.ambito = self.aggiungi(wx.Choice(self.pannello, choices=[nome.capitalize() for _chiave, nome in ricerca.AMBITI]))
            self.ambito.SetSelection(0)
        self.etichetta("&Caratteristica")
        self.criterio = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome, _tipo, _leggi in ricerca.CRITERI]))
        self.etichetta("C&ondizione")
        self.condizione = self.aggiungi(wx.Choice(self.pannello))
        self.etichetta("&Valore")
        self.valore = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PROCESS_ENTER))
        cerca, _annulla = self.pulsanti((wx.ID_OK, pulsante), (wx.ID_CANCEL, "Annulla"))
        self.criterio.SetSelection(0)
        self.criterio.Bind(wx.EVT_CHOICE, self.al_criterio)
        self.valore.Bind(wx.EVT_TEXT_ENTER, self.conferma)
        cerca.Bind(wx.EVT_BUTTON, self.conferma)
        self.al_criterio()
        self.completa((440, 360))
        (self.ambito or self.criterio).SetFocus()

    def chiave_criterio(self):
        return ricerca.CRITERI[self.criterio.GetSelection()][0]

    def al_criterio(self, event=None):
        """Le condizioni giuste per la caratteristica scelta; per il sesso e per il sì o no il valore non serve."""
        tipo = ricerca.tipo_criterio(self.chiave_criterio())
        self.condizione.Set([nome for _chiave, nome in ricerca.CONDIZIONI[tipo]])
        self.condizione.SetSelection(0)
        self.valore.Enable(tipo not in ricerca.SENZA_VALORE)

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
        ambito = ricerca.AMBITI[self.ambito.GetSelection()][0] if self.ambito else None
        descrizione = f"{ricerca.nome_criterio(criterio).lower()} {ricerca.nome_condizione(criterio, condizione)}"
        if valore is not None:
            descrizione += f" {testi.numero(valore) if tipo == ricerca.NUMERO else valore}"
        if ambito is not None:
            descrizione = f"{ricerca.nome_ambito(ambito)}, {descrizione}"
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


class NuovaPolisportiva(_Dialogo):
    """La fondazione di una polisportiva: il nome, la password facoltativa della decisione D3 e se renderla attiva."""

    def __init__(self, genitore, mondo):
        super().__init__(genitore, "Nuova polisportiva")
        self.mondo = mondo
        self.risultato = None
        self.etichetta(f"&Nome, da {NOME_POLISPORTIVA_MIN} a {NOME_POLISPORTIVA_MAX} caratteri")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello))
        self.etichetta("&Password, facoltativa")
        self.password = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        self.etichetta("C&onferma della password")
        self.conferma_password = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_PASSWORD))
        self.attiva = self.aggiungi(wx.CheckBox(self.pannello, label="&Rendila la polisportiva attiva"))
        self.attiva.SetValue(True)
        fonda, _annulla = self.pulsanti((wx.ID_OK, "&Fonda"), (wx.ID_CANCEL, "Annulla"))
        fonda.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((420, 320))
        self.nome.SetFocus()

    def conferma(self, event=None):
        problema = self.mondo.problema_nome_polisportiva(self.nome.GetValue())
        if problema:
            self.avvisa(problema, self.nome)
            return
        if self.password.GetValue() != self.conferma_password.GetValue():
            self.avvisa("La password e la conferma non coincidono.", self.password)
            return
        self.risultato = (self.nome.GetValue(), self.password.GetValue() or None, self.attiva.GetValue())
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
            wx.Bell()
            return
        poli = self.mie[indice]
        if poli.protetta and not poli.verifica_password(self.password.GetValue()):
            self.avvisa(f"La password di {poli.nome} non è giusta.", self.password)
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
            self.avvisa("La password attuale non è giusta.", self.attuale)
            return
        if self.nuova.GetValue() != self.conferma_nuova.GetValue():
            self.avvisa("La nuova password e la conferma non coincidono.", self.nuova)
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
            self.avvisa(f"La password di {self.poli.nome} non è giusta.", self.password)
            return
        self.chiudi(wx.ID_OK)


class Mercato(_Dialogo):
    """
    Il mercato della decisione D20, sul modello di Hattrick: filtri, probabilità minima e ordine
    danno l'elenco dei liberi, ciascuno con la probabilità di accettare; a chi si sceglie si fa
    un'offerta, dopo una domanda di conferma, e l'esito arriva in un messaggio. Il dialogo resta
    aperto, e in esiti tiene le offerte fatte, che la finestra racconta alla chiusura.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None):
        super().__init__(genitore, f"Mercato di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.filtri = []
        self.esiti = []
        self.righe = []
        self.info = wx.StaticText(self.pannello, label=testi.info_mercato(poli, mondo))
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Filtri")
        self.elenco_filtri = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE))
        riga = wx.BoxSizer(wx.HORIZONTAL)
        for testo, azione in (("&Aggiungi un filtro...", self.aggiungi_filtro), ("&Togli il filtro", self.togli_filtro), ("Togli t&utti i filtri", self.togli_tutti)):
            pulsante = wx.Button(self.pannello, label=testo)
            pulsante.Bind(wx.EVT_BUTTON, azione)
            riga.Add(pulsante, 0, wx.ALL, 4)
        self.sizer.Add(riga, 0, wx.LEFT | wx.RIGHT, 4)
        self.etichetta("Probabilità &minima di accettare, in percentuale")
        self.minima = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=100, initial=0))
        self.etichetta("&Ordina per")
        self.ordine = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in mercato.ORDINI]))
        self.ordine.SetSelection(0)
        self.etichetta_trovati = wx.StaticText(self.pannello, label="&Giocatori trovati")
        self.sizer.Add(self.etichetta_trovati, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.trovati = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        offri, scheda, _chiudi = self.pulsanti((wx.ID_ANY, "Fai un'&offerta"), (wx.ID_ANY, "&Scheda del giocatore"), (wx.ID_CANCEL, "&Chiudi"))
        offri.Bind(wx.EVT_BUTTON, self.offri)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.trovati.Bind(wx.EVT_LISTBOX_DCLICK, self.offri)
        self.minima.Bind(wx.EVT_SPINCTRL, self.aggiorna)
        self.minima.Bind(wx.EVT_TEXT, self.aggiorna)
        self.ordine.Bind(wx.EVT_CHOICE, self.aggiorna)
        self.mostra_filtri()
        self.aggiorna()
        self.completa((680, 600))
        self.trovati.SetFocus()

    def mostra_filtri(self, posto=0):
        """L'elenco dei filtri; senza filtri dice che compaiono tutti i liberi."""
        self.elenco_filtri.Set([descrizione for _c, _k, _v, descrizione in self.filtri] or ["Nessun filtro: compaiono tutti i liberi."])
        self.elenco_filtri.SetSelection(min(posto, self.elenco_filtri.GetCount() - 1))

    def aggiorna(self, event=None, posto=0):
        """Ricalcola l'elenco dei candidati con filtri, probabilità minima e ordine del momento."""
        ordine = mercato.ORDINI[self.ordine.GetSelection()][0]
        filtri = [(criterio, condizione, valore) for criterio, condizione, valore, _d in self.filtri]
        self.righe = mercato.candidati(self.mondo, self.poli, filtri, self.minima.GetValue(), ordine)
        self.trovati.Set([testi.riga_mercato(g, probabilita) for g, probabilita in self.righe])
        if self.righe:
            self.trovati.SetSelection(min(posto, len(self.righe) - 1))
        self.etichetta_trovati.SetLabel(f"&Giocatori trovati: {testi.intero(len(self.righe))}")
        self.info.SetLabel(testi.info_mercato(self.poli, self.mondo))
        self.pannello.Layout()

    def aggiungi_filtro(self, event=None):
        dialogo = Ricerca(self, con_ambito=False, titolo="Aggiungi un filtro", pulsante="&Aggiungi")
        try:
            if dialogo.ShowModal() == wx.ID_OK and dialogo.risultato is not None:
                _ambito, criterio, condizione, valore, descrizione = dialogo.risultato
                self.filtri.append((criterio, condizione, valore, descrizione[0].upper() + descrizione[1:]))
                self.mostra_filtri(len(self.filtri) - 1)
                self.aggiorna()
        finally:
            dialogo.Destroy()

    def togli_filtro(self, event=None):
        indice = self.elenco_filtri.GetSelection()
        if not self.filtri or indice == wx.NOT_FOUND:
            wx.Bell()
            return
        del self.filtri[indice]
        self.mostra_filtri(indice)
        self.aggiorna()

    def togli_tutti(self, event=None):
        self.filtri.clear()
        self.mostra_filtri()
        self.aggiorna()

    def _scelto(self):
        indice = self.trovati.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.Bell()
            return None, indice
        return self.righe[indice], indice

    def offri(self, event=None):
        """L'offerta al candidato scelto: prima i controlli e la conferma, poi l'esito in un messaggio."""
        riga, indice = self._scelto()
        if riga is None:
            return
        g, probabilita = riga
        problema = self.mondo.problema_offerta(self.poli, g)
        if problema:
            wx.MessageBox(problema, "Offerta", wx.OK | wx.ICON_WARNING, self)
            return
        if wx.MessageBox(testi.domanda_offerta(g, self.poli, probabilita, self.mondo), "Offerta", wx.YES_NO | wx.ICON_QUESTION, self) != wx.YES:
            return
        accetta, probabilita = self.mondo.offerta(self.poli, g)
        self.esiti.append((g, accetta, probabilita))
        wx.MessageBox(testi.esito_offerta(g, self.poli, accetta, probabilita), "Esito dell'offerta", wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna(posto=indice)
        self.trovati.SetFocus()

    def scheda(self, event=None):
        riga, _indice = self._scelto()
        if riga is None:
            return
        g = riga[0]
        dialogo = Lettura(self, f"Scheda di {testi.nome_completo(g)}", testi.scheda_giocatore(g, self.mondo), self.impostazioni)
        try:
            dialogo.ShowModal()
        finally:
            dialogo.Destroy()


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
