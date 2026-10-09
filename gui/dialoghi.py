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
"""

import contextlib
import webbrowser

import wx
from GBwx import STILE_ADATTABILE, adatta_finestra, pannello_scorrevole

import allenamento
import contratti
import economia
import impostazioni as modulo_impostazioni
import mercato
import partita_sonora
import ricerca
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
from modelli import probabilita_accettazione
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


class _Dialogo(wx.Dialog):
    """La base dei dialoghi: pannello che scorre, sizer verticale, chiusura con Esc."""

    def __init__(self, genitore, titolo):
        super().__init__(genitore, title=titolo, style=STILE_ADATTABILE)
        self.pannello = pannello_scorrevole(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self._timer_del_suono = None

    def etichetta(self, testo):
        self.sizer.Add(wx.StaticText(self.pannello, label=testo), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

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
        self.pannello.SetSizer(self.sizer)
        adatta_finestra(self, self.pannello, misura)

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
    """La scelta di un giocatore: un campo per il numero o il nome e l'elenco, che si restringe mentre si scrive."""

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
                self.avvisa("Il valore deve essere un numero, per esempio 150 o 12,5.", self.valore)
                return
        elif tipo == ricerca.TESTO:
            if not testo:
                self.avvisa("Scrivi il testo da cercare.", self.valore)
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
            self.avvisa("La password e la conferma non coincidono.", self.password, "password_non_coincidono")
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
    altezza, più acuto quanto più è probabile che il giocatore accetti.
    """

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


class Mercato(_Dialogo):
    """
    Il mercato delle decisioni D20, D22 e D23, sul modello di Hattrick: filtri, chi mostrare, costo
    massimo e ordine danno l'elenco dei candidati. A un libero si offre un ingaggio, scegliendo la
    cifra e sentendo la probabilità che accetti; chi è in vendita si compra al suo prezzo; per un
    tesserato del computer si offre una cifra alla sua polisportiva. Ogni offerta chiede conferma,
    perché costa una mossa e non si ritira, e l'esito arriva in un messaggio. Il dialogo resta
    aperto, e in esiti tiene i testi degli esiti, che la finestra racconta alla chiusura.
    Ogni azione ha il suo suono, e ogni esito di un'offerta il suo, così accettata e rifiutata si
    distinguono prima di leggere il messaggio. Quando un'azione svuota l'elenco dei candidati, o lo
    riempie di nuovo, al posto del suo suono si sente quello del passaggio.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None):
        super().__init__(genitore, f"Mercato di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.filtri = []
        self.esiti = []
        self.righe = []
        self.elenco_vuoto = _ElencoCheSiRestringe()
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
        self.scelta.Bind(wx.EVT_CHOICE, lambda event: self.aggiorna(suono="mercato_scelta_cambiata"))
        self.massimo.Bind(wx.EVT_SPINCTRL, self.aggiorna)
        self.massimo.Bind(wx.EVT_TEXT, self.aggiorna)
        self.ordine.Bind(wx.EVT_CHOICE, lambda event: self.aggiorna(suono="mercato_ordine_cambiato"))
        self.mostra_filtri()
        self.aggiorna()
        self.completa((700, 620))
        self.trovati.SetFocus()

    def mostra_filtri(self, posto=0):
        """L'elenco dei filtri; senza filtri dice che compaiono tutti."""
        self.elenco_filtri.Set([descrizione for _c, _k, _v, descrizione in self.filtri] or ["Nessun filtro: compaiono tutti."])
        self.elenco_filtri.SetSelection(min(posto, self.elenco_filtri.GetCount() - 1))

    def aggiorna(self, event=None, posto=0, suono=None):
        """
        Ricalcola l'elenco dei candidati con filtri, scelta, costo massimo e ordine del momento, e
        suona il suono dell'azione, o quello del passaggio dell'elenco da pieno a vuoto o ritorno. Se
        il mercato si apre già vuoto, lo dice dopo il suono dell'apertura.
        """
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
        apertura = self.elenco_vuoto.pieno is None
        passaggio = self.elenco_vuoto.passaggio(bool(self.righe))
        if apertura and not self.righe:
            suoni.in_coda("elenco_svuotato")
        elif passaggio or suono:
            suoni.suona(passaggio or suono)

    def aggiungi_filtro(self, event=None):
        dialogo = Ricerca(self, con_ambito=False, titolo="Aggiungi un filtro", pulsante="&Aggiungi")
        try:
            suoni.suona("dialogo_filtro_mercato")
            if dialogo.ShowModal() == wx.ID_OK and dialogo.risultato is not None:
                _ambito, criterio, condizione, valore, descrizione = dialogo.risultato
                self.filtri.append((criterio, condizione, valore, descrizione[0].upper() + descrizione[1:]))
                self.mostra_filtri(len(self.filtri) - 1)
                self.aggiorna(suono="filtro_aggiunto")
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def togli_filtro(self, event=None):
        indice = self.elenco_filtri.GetSelection()
        if not self.filtri or indice == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return
        del self.filtri[indice]
        self.mostra_filtri(indice)
        self.aggiorna(suono="filtro_tolto")

    def togli_tutti(self, event=None):
        if not self.filtri:
            suoni.suona("nessuna_selezione")
            return
        self.filtri.clear()
        self.mostra_filtri()
        self.aggiorna(suono="filtri_tutti_tolti")

    def _scelto(self):
        indice = self.trovati.GetSelection()
        if indice == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return None, indice
        return self.righe[indice], indice

    def _avviso(self, testo, suono):
        suoni.suona(suono)
        wx.MessageBox(testo, "Mercato", wx.OK | wx.ICON_WARNING, self)

    def _suono_del_problema(self, costo=None):
        """
        Il suono di un'offerta che non si può fare, nell'ordine in cui il mondo controlla: le mosse
        del giorno finite, la rosa piena, la cassa che non basta per il costo. Gli altri problemi,
        come un giocatore che nel frattempo non è più disponibile, sono un tasto premuto a vuoto.
        """
        if self.mondo.mosse_rimaste(self.poli) <= 0:
            return "mosse_finite"
        if len(self.poli.tesserati) >= self.poli.maxtesserati:
            return "rosa_piena"
        if costo is not None and costo > self.poli.cassa:
            return "cassa_insufficiente"
        return "nessuna_selezione"

    def _cifra(self, titolo, spiegazione, etichetta, iniziale, suono, nota=None, probabilita=None):
        """La cifra scelta dall'utente, oppure None se ha annullato; suono è quello dell'apertura."""
        dialogo = Cifra(self, titolo, spiegazione, etichetta, iniziale, self.poli.cassa, nota, probabilita)
        try:
            suoni.suona(suono)
            if dialogo.ShowModal() == wx.ID_OK:
                return dialogo.valore
            suoni.suona("annullato")
            return None
        finally:
            dialogo.Destroy()

    def offri(self, event=None):
        """L'offerta al candidato scelto, secondo il tipo: ingaggio, acquisto al prezzo, offerta d'acquisto."""
        c, indice = self._scelto()
        if c is None:
            return
        if self.poli.cassa <= 0:
            self._avviso(f"La cassa di {self.poli.nome} è vuota.", "cassa_insufficiente")
            return
        if c.tipo == mercato.LIBERO:
            esito = self._ingaggio(c)
            suono = "ingaggio_accettato" if esito and esito[1] else "ingaggio_rifiutato"
        elif c.tipo == mercato.IN_VENDITA:
            esito = self._acquisto(c)
            suono = "acquisto_fatto"
        else:
            esito = self._offerta_d_acquisto(c)
            suono = "offerta_d_acquisto_accettata" if esito and esito[1] else "offerta_d_acquisto_rifiutata"
        if esito is not None:
            self.esiti.append(esito)
            suoni.suona(suono)
            wx.MessageBox(esito[0], "Esito", wx.OK | wx.ICON_INFORMATION, self)
            self.aggiorna(posto=indice)
        self.trovati.SetFocus()

    def _ingaggio(self, c):
        g = c.giocatore
        problema = self.mondo.problema_offerta(self.poli, g)
        if problema:
            self._avviso(problema, self._suono_del_problema())
            return None
        richiesta = c.costo
        # Dalla tappa 11 la spiegazione comincia con il contratto che il giocatore propone, D31:
        # accettare l'offerta vuol dire accettare la proposta, annullare vuol dire rifiutarla.
        spiegazione = (f"{testi.proposta_di_contratto(g, self.mondo)} Per firmare, {testi.nome_completo(g)} chiede {testi.euro(richiesta)} d'ingaggio: "
                       "più offri, più è probabile che accetti.")
        importo = self._cifra(f"Ingaggio di {testi.nome_completo(g)}", spiegazione,
                              "&Ingaggio da offrire, in euro", richiesta, "dialogo_cifra_ingaggio",
                              lambda cifra: f"Accetterebbe al {testi.numero(probabilita_accettazione(cifra, richiesta), 0)}%.",
                              lambda cifra: probabilita_accettazione(cifra, richiesta))
        if importo is None:
            return None
        problema = self.mondo.problema_offerta(self.poli, g, importo)
        if problema:
            self._avviso(problema, self._suono_del_problema(importo))
            return None
        if not self._conferma(testi.domanda_ingaggio(c, importo, probabilita_accettazione(importo, richiesta), self.poli, self.mondo)):
            return None
        accetta, probabilita = self.mondo.offerta(self.poli, g, importo)
        return testi.esito_ingaggio(g, self.poli, accetta, importo, probabilita), accetta

    def _acquisto(self, c):
        g = c.giocatore
        problema = self.mondo.problema_acquisto(self.poli, g)
        if problema:
            self._avviso(problema, self._suono_del_problema(c.costo))
            return None
        if not self._conferma(testi.domanda_acquisto(c, self.poli, self.mondo)):
            return None
        prezzo = self.mondo.acquista(self.poli, g)
        return testi.esito_acquisto(g, c.polisportiva, self.poli, prezzo), True

    def _offerta_d_acquisto(self, c):
        g = c.giocatore
        problema = self.mondo.problema_offerta_d_acquisto(self.poli, g)
        if problema:
            self._avviso(problema, self._suono_del_problema())
            return None
        importo = self._cifra("Offerta d'acquisto", f"{testi.nome_completo(g)} vale {testi.euro(c.costo)} sul mercato: {c.polisportiva.nome} lo cede se l'offerta le basta.",
                              "&Cifra da offrire, in euro", c.costo, "dialogo_cifra_offerta_d_acquisto")
        if importo is None:
            return None
        problema = self.mondo.problema_offerta_d_acquisto(self.poli, g, importo)
        if problema:
            self._avviso(problema, self._suono_del_problema(importo))
            return None
        if not self._conferma(testi.domanda_offerta_d_acquisto(c, importo, self.poli, self.mondo)):
            return None
        accettata = self.mondo.offerta_d_acquisto(self.poli, g, importo)
        return testi.esito_offerta_d_acquisto(g, c.polisportiva, self.poli, accettata, importo), accettata

    def scheda(self, event=None):
        c, _indice = self._scelto()
        if c is None:
            return
        self._scheda_del_giocatore(c.giocatore, self.impostazioni)


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
        # Programma e intensità di ciascuno all'apertura: alla chiusura dicono che cosa è cambiato.
        self.di_partenza = {g.id: (g.programma, g.intensita) for g in self.allenandi}
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
        self.programma = self.aggiungi(wx.Choice(self.pannello, choices=[INDOLI[k]["nome"].capitalize() for k in self.indoli]))
        self.etichetta("&Intensità")
        self.intensita = self.aggiungi(wx.Choice(self.pannello, choices=[k.capitalize() for k in self.livelli]))
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
        self.info.SetLabel(testi.intestazione_sala(self.poli, self.allenandi))
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
        self.programma.SetSelection(self.indoli.index(g.programma) if g.programma in self.indoli else 0)
        self.intensita.SetSelection(self.livelli.index(g.intensita) if g.intensita in self.livelli else 0)
        self.aggiorna_anteprima()

    def al_allenando(self, event=None):
        self._controlli_dell_allenando(nuovo=True)

    def aggiorna_anteprima(self, event=None):
        """L'anteprima della spesa a mano con i punti e la caratteristica del momento; per chi non si allena, il perché."""
        g, c = self._scelto(), self._caratteristica()
        if g is None or c is None:
            testo = ""
        elif not allenamento.puo_allenarsi(g):
            testo = testi.allenando_fermo(g)
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
        """Allena tutti: dopo la conferma, ciascuno di chi oggi si allena e ha almeno un punto spende tutto secondo il suo programma."""
        fuoco = wx.Window.FindFocus()
        candidati = [g for g in self.allenandi if allenamento.puo_allenarsi(g) and g.punti_allenamento >= 1]
        if not candidati:
            self.avvisa(testi.nessuno_da_allenare(self.poli), self.elenco, "punti_insufficienti")
            return
        if not self._conferma(testi.domanda_allena_tutti(candidati)):
            self._torna(fuoco)
            return
        spese = [spesa for spesa in (self._secondo_il_programma(g) for g in candidati) if spesa is not None]
        if not spese:
            self.avvisa(testi.nessuno_da_allenare(self.poli), self.elenco, "caratteristica_al_massimo")
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

    def cambi(self):
        """Le righe dei tesserati a cui sono cambiati programma o intensità rispetto all'apertura."""
        return [testi.cambio_in_sala(g) for g in self.allenandi if (g.programma, g.intensita) != self.di_partenza[g.id]]

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
    il suo suono. In esiti restano i testi degli esiti, che la finestra mostra alla chiusura.
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
            suono = "rinnovo_accettato"
        elif not contratti.puo_trattare(g):
            suono = "rinnovo_chiuso"
        else:
            suono = "rinnovo_rifiutato"
        testo = testi.esito_rinnovo(g, self.poli, accettato, richiesta, mesi)
        self.esiti.append(testo)
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


class OpzioniAmichevole(_Dialogo):
    """
    Le opzioni dell'amichevole fra due giocatori già scelti: al meglio di 3 o di 5 set, come
    seguirla, e il livello della cronaca, sintetica, normale o tecnica, che vale anche per il file.
    Con la decisione D29 i modi di seguirla sono due: Assisti, la partita dal vivo, e Vai alla fine,
    il risultato con la cronaca intera sotto. I predefiniti sono quelli scelti da Gabriele: 3 set,
    Assisti, normale; dall'8 ottobre 2026 il dialogo riparte dalle ultime scelte, che riceve in
    iniziali come terna di set, modo e livello. In risultato restano le tre scelte.
    """

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
        suoni.suona("caffe_paypal")
        with contextlib.suppress(webbrowser.Error):
            webbrowser.open(PAYPAL_URL)
        self.chiudi(wx.ID_OK)
