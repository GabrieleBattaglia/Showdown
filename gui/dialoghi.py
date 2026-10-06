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
"""

import contextlib
import webbrowser

import wx
from GBwx import STILE_ADATTABILE, adatta_finestra, pannello_scorrevole

import economia
import impostazioni as modulo_impostazioni
import mercato
import ricerca
import testi
from costanti import NOME_POLISPORTIVA_MAX, NOME_POLISPORTIVA_MIN
from gui import aspetto
from modelli import probabilita_accettazione

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


class Cifra(_Dialogo):
    """
    Una cifra in euro da scegliere, fino alla cassa, con una spiegazione davanti; se serve, una
    nota dopo il campo segue la cifra, come la probabilità che un giocatore accetti un ingaggio.
    """

    def __init__(self, genitore, titolo, spiegazione, etichetta, iniziale, massimo, nota=None):
        super().__init__(genitore, titolo)
        self.valore = None
        self.calcola_nota = nota
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

    def conferma(self, event=None):
        if self.cifra.GetValue() <= 0:
            self.avvisa("La cifra deve essere di almeno 1 euro.", self.cifra)
            return
        self.valore = self.cifra.GetValue()
        self.chiudi(wx.ID_OK)


class Mercato(_Dialogo):
    """
    Il mercato delle decisioni D20, D22 e D23, sul modello di Hattrick: filtri, chi mostrare, costo
    massimo e ordine danno l'elenco dei candidati. A un libero si offre un ingaggio, scegliendo la
    cifra e sentendo la probabilità che accetti; chi è in vendita si compra al suo prezzo; per un
    tesserato del computer si offre una cifra alla sua polisportiva. Ogni offerta chiede conferma,
    perché costa una mossa e non si ritira, e l'esito arriva in un messaggio. Il dialogo resta
    aperto, e in esiti tiene i testi degli esiti, che la finestra racconta alla chiusura.
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
        self.etichetta("Mo&stra")
        self.scelta = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome, _tipi in mercato.SCELTE]))
        self.scelta.SetSelection(0)
        self.etichetta("Costo &massimo in euro, zero per nessun limite")
        self.massimo = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=100_000_000, initial=0))
        self.etichetta("O&rdina per")
        self.ordine = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in mercato.ORDINI]))
        self.ordine.SetSelection(0)
        self.etichetta_trovati = wx.StaticText(self.pannello, label="&Giocatori trovati")
        self.sizer.Add(self.etichetta_trovati, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.trovati = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        offri, scheda, _chiudi = self.pulsanti((wx.ID_ANY, "Fai un'&offerta"), (wx.ID_ANY, "Sc&heda del giocatore"), (wx.ID_CANCEL, "&Chiudi"))
        offri.Bind(wx.EVT_BUTTON, self.offri)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.trovati.Bind(wx.EVT_LISTBOX_DCLICK, self.offri)
        self.scelta.Bind(wx.EVT_CHOICE, self.aggiorna)
        self.massimo.Bind(wx.EVT_SPINCTRL, self.aggiorna)
        self.massimo.Bind(wx.EVT_TEXT, self.aggiorna)
        self.ordine.Bind(wx.EVT_CHOICE, self.aggiorna)
        self.mostra_filtri()
        self.aggiorna()
        self.completa((700, 620))
        self.trovati.SetFocus()

    def mostra_filtri(self, posto=0):
        """L'elenco dei filtri; senza filtri dice che compaiono tutti."""
        self.elenco_filtri.Set([descrizione for _c, _k, _v, descrizione in self.filtri] or ["Nessun filtro: compaiono tutti."])
        self.elenco_filtri.SetSelection(min(posto, self.elenco_filtri.GetCount() - 1))

    def aggiorna(self, event=None, posto=0):
        """Ricalcola l'elenco dei candidati con filtri, scelta, costo massimo e ordine del momento."""
        mostra = mercato.SCELTE[self.scelta.GetSelection()][0]
        ordine = mercato.ORDINI[self.ordine.GetSelection()][0]
        filtri = [(criterio, condizione, valore) for criterio, condizione, valore, _d in self.filtri]
        self.righe = mercato.candidati(self.mondo, self.poli, filtri, mostra, self.massimo.GetValue(), ordine)
        self.trovati.Set([testi.riga_mercato(c) for c in self.righe])
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

    def _avviso(self, testo):
        wx.MessageBox(testo, "Mercato", wx.OK | wx.ICON_WARNING, self)

    def _conferma(self, domanda):
        return wx.MessageBox(domanda, "Mercato", wx.YES_NO | wx.ICON_QUESTION, self) == wx.YES

    def _cifra(self, titolo, spiegazione, etichetta, iniziale, nota=None):
        """La cifra scelta dall'utente, oppure None se ha annullato."""
        dialogo = Cifra(self, titolo, spiegazione, etichetta, iniziale, self.poli.cassa, nota)
        try:
            return dialogo.valore if dialogo.ShowModal() == wx.ID_OK else None
        finally:
            dialogo.Destroy()

    def offri(self, event=None):
        """L'offerta al candidato scelto, secondo il tipo: ingaggio, acquisto al prezzo, offerta d'acquisto."""
        c, indice = self._scelto()
        if c is None:
            return
        if self.poli.cassa <= 0:
            self._avviso(f"La cassa di {self.poli.nome} è vuota.")
            return
        if c.tipo == mercato.LIBERO:
            esito = self._ingaggio(c)
        elif c.tipo == mercato.IN_VENDITA:
            esito = self._acquisto(c)
        else:
            esito = self._offerta_d_acquisto(c)
        if esito is not None:
            self.esiti.append(esito)
            wx.MessageBox(esito[0], "Esito", wx.OK | wx.ICON_INFORMATION, self)
            self.aggiorna(posto=indice)
        self.trovati.SetFocus()

    def _ingaggio(self, c):
        g = c.giocatore
        problema = self.mondo.problema_offerta(self.poli, g)
        if problema:
            self._avviso(problema)
            return None
        richiesta = c.costo
        importo = self._cifra("Ingaggio", f"{testi.nome_completo(g)} chiede {testi.euro(richiesta)} d'ingaggio: più offri, più è probabile che accetti.",
                              "&Ingaggio da offrire, in euro", richiesta,
                              lambda cifra: f"Accetterebbe al {testi.numero(probabilita_accettazione(cifra, richiesta), 0)}%.")
        if importo is None:
            return None
        problema = self.mondo.problema_offerta(self.poli, g, importo)
        if problema:
            self._avviso(problema)
            return None
        if not self._conferma(testi.domanda_ingaggio(c, importo, probabilita_accettazione(importo, richiesta), self.poli, self.mondo)):
            return None
        accetta, probabilita = self.mondo.offerta(self.poli, g, importo)
        return testi.esito_ingaggio(g, self.poli, accetta, importo, probabilita), accetta

    def _acquisto(self, c):
        g = c.giocatore
        problema = self.mondo.problema_acquisto(self.poli, g)
        if problema:
            self._avviso(problema)
            return None
        if not self._conferma(testi.domanda_acquisto(c, self.poli, self.mondo)):
            return None
        prezzo = self.mondo.acquista(self.poli, g)
        return testi.esito_acquisto(g, c.polisportiva, self.poli, prezzo), True

    def _offerta_d_acquisto(self, c):
        g = c.giocatore
        problema = self.mondo.problema_offerta_d_acquisto(self.poli, g)
        if problema:
            self._avviso(problema)
            return None
        importo = self._cifra("Offerta d'acquisto", f"{testi.nome_completo(g)} vale {testi.euro(c.costo)} sul mercato: {c.polisportiva.nome} lo cede se l'offerta le basta.",
                              "&Cifra da offrire, in euro", c.costo)
        if importo is None:
            return None
        problema = self.mondo.problema_offerta_d_acquisto(self.poli, g, importo)
        if problema:
            self._avviso(problema)
            return None
        if not self._conferma(testi.domanda_offerta_d_acquisto(c, importo, self.poli, self.mondo)):
            return None
        accettata = self.mondo.offerta_d_acquisto(self.poli, g, importo)
        return testi.esito_offerta_d_acquisto(g, c.polisportiva, self.poli, accettata, importo), accettata

    def scheda(self, event=None):
        c, _indice = self._scelto()
        if c is None:
            return
        g = c.giocatore
        dialogo = Lettura(self, f"Scheda di {testi.nome_completo(g)}", testi.scheda_giocatore(g, self.mondo), self.impostazioni)
        try:
            dialogo.ShowModal()
        finally:
            dialogo.Destroy()


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
        indice = self.elenco.GetSelection()
        if not self.debitori or indice == wx.NOT_FOUND:
            wx.Bell()
            return
        g = self.debitori[indice]
        try:
            self.mondo.paga(self.poli, g, self.cifra.GetValue())
        except ValueError as e:
            wx.MessageBox(str(e), "Arretrati", wx.OK | wx.ICON_WARNING, self)
            return
        self.pagati.append((g, self.cifra.GetValue()))
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
        self.elenco.Set([testi.riga_vendita(g, self.poli) for g in self.rosa])
        if self.rosa:
            self.elenco.SetSelection(min(posto, len(self.rosa) - 1))
        self.al_giocatore()

    def al_giocatore(self, event=None):
        """Il prezzo parte da quello di vendita, se il tesserato è già in vendita, o dal suo valore di mercato."""
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            return
        g = self.rosa[indice]
        self.prezzo.SetValue(self.poli.in_vendita.get(g.id, max(1, economia.valore_di_mercato(g))))

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND:
            wx.Bell()
            return None, indice
        return self.rosa[indice], indice

    def metti(self, event=None):
        g, indice = self._scelto()
        if g is None:
            return
        self.mondo.metti_in_vendita(self.poli, g, self.prezzo.GetValue())
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
            wx.MessageBox(str(e), "Vendite", wx.OK | wx.ICON_WARNING, self)
            return
        testo = f"{testi.nome_completo(g)} non è più in vendita."
        self.fatte.append(testo)
        wx.MessageBox(testo, "Vendite", wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna(indice)
        self.elenco.SetFocus()


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
