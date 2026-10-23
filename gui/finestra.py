"""
La finestra principale di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-06 con la tappa 5 del piano, sul modello di Terminal Beast e di Tornello: due
aree di testo, la vista principale grande e in sola lettura, dove ogni comando mostra il suo
risultato al posto del precedente, e la barra di stato di quattro righe a codici; nessun albero
dei comandi, ma i menu, ciascuna voce con il suo tasto rapido. I menu nascono da una tabella sola,
da cui nasce anche la guida ai comandi, così le due cose non possono andare d'accordo a metà.
Dalla tappa 6 il mondo avanza anche a finestra aperta: ogni minuto un timer guarda se è maturato
un giorno simulato, lo fa elaborare, salva il mondo e lo annuncia nella barra di stato, senza
toccare la vista principale, dove chi legge non deve vedersi spostare il testo. Mentre è aperto
un dialogo aspetta che si chiuda.
Dalla tappa 7 il menu Polisportive ha le operazioni: fondazione, cambio della polisportiva
attiva, mercato, svincolo, password e chiusura. Ogni operazione si salva subito, così l'esito di
un'offerta resta quello che è stato.
Dalla tappa 8 ci sono il bilancio, gli arretrati da pagare e le vendite, e quando il mondo avanza
la barra di stato dice prima di tutto se i tuoi tesserati sono rimasti senza stipendio.
Dal 2026-10-07, con la decisione D24, ogni evento della finestra ha il suo effetto sonoro: i
comandi, l'apertura e l'esito dei dialoghi, i salvataggi, l'avvio e l'uscita. Quando il mondo
avanza suona un solo suono, quello della notizia più importante, scelto insieme al testo della
barra di stato perché non dicano cose diverse: è l'invito a premere F7. Se un salvataggio
automatico non riesce, dopo il suono dell'operazione si sente quello del salvataggio fallito, e la
vista dice il perché. Nel menu Impostazioni c'è il volume degli effetti.
Dal 2026-10-08, con la tappa 9, c'è il menu Partite, con le scelte di Gabriele: l'amichevole fra un
tuo tesserato e un giocatore qualunque, ciascuno al massimo una al giorno, si gioca e si registra
subito, il mondo si salva, e la cronaca si salva nel suo file al livello scelto. Con la decisione
D29, tappa 10, i modi di seguirla sono due: Vai alla fine mostra nella vista il risultato, i punti
allenamento e sotto la cronaca intera; Assisti apre la finestra dal vivo di gui/dal_vivo.py, e
quando se ne esce con Vai alla fine o dal risultato la vista mostra lo stesso testo. Il punto per
punto con F8 e Ctrl+F8 non c'è più. L'esito si sente solo quando si mostra, perché la partita dal
vivo non lo sveli prima; e con la decisione D30 chi esce con Esc prima della fine non lo vede
affatto: la vista dice che l'incontro è registrato e dove leggerne il risultato. Nel menu Impostazioni c'è la velocità di
gioco, e il dialogo degli effetti sonori ha anche il volume della partita. Le parti delle tappe 9 e
10 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-09, con la tappa 11 e la decisione D31, il menu Polisportive ha la sala allenamento,
dove si spendono i punti allenamento dei tesserati e se ne scelgono programma e intensità, e i
contratti, dove si propongono i rinnovi; lo svincolo dice la buonuscita, e alla chiusura di ciascun
dialogo la vista mostra che cosa è cambiato e il mondo si salva. Anche queste parti sono di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-14, con la tappa 12 e la decisione D32, il mondo gioca. Il menu Tornei ha il calendario con
le iscrizioni a mano, le iscrizioni dei tuoi atleti, il pannello dei tornei in corso, dove gli incontri
dei tuoi si ascoltano in differita o si leggono, l'albo d'oro, la classifica mondiale, gli editor dei
modelli e delle formule e il ripristino del calendario predefinito; il menu Partite ha le sfide fra
polisportive, da lanciare, in arrivo e nello storico. Salva la cronaca salva l'ultimo incontro mostrato
o ascoltato, amichevole, di torneo o di sfida. All'avvio un calendario che non si legge si dice in
testa alla vista; quando il mondo avanza, la barra dice le notizie dei tornei e delle sfide, con un
suono solo, quello della più importante. Le parti della tappa 12 sono di Gabriele Battaglia (IZ4APU) &
ClaudIA (Claude Opus 5.5, modalità auto).
Dal 2026-10-21, con la tappa 13 e la decisione D33, il menu Polisportive ha lo staff della polisportiva
attiva e il mercato degli allenatori, che alla chiusura riepilogano le operazioni nella vista; all'avvio
col mondo appena aggiornato, la notizia dello staff ha il suo suono. Le parti della tappa 13 sono di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Dal 2026-10-23, con la tappa 14 e la decisione D34, il menu Aiuto ha il manuale, manuale.html, che si
apre nel browser con Maiusc+F1. La finestra conduce la sua parte dell'aggiornamento automatico: la
proposta con le note della release, gli esiti in un messaggio che aspetta l'OK, l'avanzamento dello
scaricamento nella barra di stato e la chiusura per farsi sostituire, che salva il mondo e non aspetta
il riepilogo di fine sessione. Torna in primo piano quando si prova ad aprire MESS una seconda volta;
all'apertura dopo un crash la vista lo dice in testa, col suono staccato come la notizia dello staff; e
il messaggio di un errore imprevisto rimanda al registro degli errori, accanto al programma. Le parti
della tappa 14 sono di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import contextlib
import os
import time

import wx
from GBUtils import Donazione
from GBwx import dentro_area_utile

import aggiornamento
import archivio
import impostazioni as modulo_impostazioni
import modelli_torneo
import percorsi
import registro
import ricerca
import sfide
import suoni
import testi
from gui import aspetto
from gui.dal_vivo import ALLA_FINE, CON_ESC, FinestraDalVivo
from gui.dialoghi import (
    ASSISTI,
    Aggiornamento,
    AnnunciDellaCronaca,
    Aspetto,
    Caffe,
    CambiaPolisportiva,
    ChiediPassword,
    Conservazione,
    Contratti,
    EffettiSonori,
    Lettura,
    Mercato,
    MercatoAllenatori,
    NuovaPolisportiva,
    OpzioniAmichevole,
    PagaArretrati,
    PasswordPolisportiva,
    Ricerca,
    SalaAllenamento,
    SceltaGiocatore,
    Staff,
    VelocitaDiGioco,
    Vendite,
)
from gui.editor_tornei import EditorFormule, EditorModelli
from gui.sfide import LanciaSfida, SfideInArrivo, StoricoSfide
from gui.tornei import AlboDOro, CalendarioTornei, PannelloTornei, UltimoIncontro, tuoi_del_mondo
from partita import MotorePartita
from utilita import adesso, adesso_utc

TITOLO = "MESS, Manageriale e Simulatore Showdown"
# Il silenzio fra il suono dell'avvio e quello della notizia dello staff: con la pausa breve della coda
# il fischietto si confondeva con l'avvio, collaudo di Gabriele del 23 ottobre 2026. Dalla tappa 14
# vale anche per la notizia del crash della volta prima.
PAUSA_NOTIZIA_DELLO_STAFF = 1.0
RIGHE_BARRA = 4
# Ogni quanti millesimi la chiusura per l'aggiornamento riprova, finché un messaggio resta aperto.
RIPROVA_DELLA_CHIUSURA = 200
# Dopo quanti secondi la chiusura per l'aggiornamento smette di riprovare: lo script di sostituzione
# aspetta la chiusura di MESS al massimo 30 secondi, e oltre si chiuderebbe per niente.
LIMITE_DELLA_CHIUSURA = 25
NON_INSTALLATO = ("L'aggiornamento non si è installato: MESS doveva chiudersi entro 30 secondi, ma un messaggio è rimasto aperto. "
                  "Continui con questa versione, e l'aggiornamento te lo ripropongo al prossimo avvio.")
# Il suono degli esiti dell'aggiornamento che non sono quello buono, lo scaricamento finito.
SUONI_DEGLI_ESITI = {aggiornamento.NON_RIUSCITO: "aggiornamento_non_riuscito", aggiornamento.NON_PRONTO: "aggiornamento_non_pronto"}


class FinestraPrincipale(wx.Frame):
    def __init__(self, mondo, origine, messaggi, rapporto, ultimo_prima, avvisi_all_avvio=False, crash_precedente=None):
        super().__init__(None, title=TITOLO)
        self.mondo = mondo
        self.origine = origine
        self.avvisi_all_avvio = avvisi_all_avvio
        # Dalla tappa 14: il resoconto del crash della volta prima, se c'è stato; chiusa diventa vera
        # quando la finestra comincia a chiudersi, e il filo dell'aggiornamento non le chiede più niente.
        self.crash_precedente = crash_precedente
        self.chiusa = False
        self._per_aggiornare = False
        # Da quando, in secondi di time.monotonic, la finestra prova a chiudersi per l'aggiornamento.
        self._chiusura_dal = None
        self.rapporto = rapporto
        self.rapporto_sessione = rapporto
        self._modali = 0
        self.impostazioni = modulo_impostazioni.carica()
        suoni.imposta_volume(self.impostazioni["volume_effetti"])
        self.inizio = adesso()
        self.comandi = 0
        self.ultimo_evento = "mondo pronto"
        # Dalla tappa 12, punto 12.10: un modello o una formula dei tornei che non si leggono si dicono in
        # testa alla vista all'avvio, col loro suono, e nella barra una volta per sessione e a ogni cambio.
        self.problemi_all_avvio = self._problemi_del_calendario()
        self._problemi_detti = tuple(self.problemi_all_avvio) or None
        # Il mondo nato adesso avanza subito di un giorno, che non va annunciato: è appena nato.
        self.avanzamento_all_avvio = None
        if origine != archivio.NATO:
            evento, testo = self._evento_avanzamento(rapporto, True)
            if evento:
                self.avanzamento_all_avvio = evento
                self.ultimo_evento = testo
        self.ultima_ricerca = None
        # L'ultima amichevole giocata nella sessione, di cui si salva la cronaca.
        self.incontro = None
        self._testo_barra = None
        self._errore_aperto = False
        self._crea_controlli()
        self._crea_menu()
        self.applica_aspetto()
        dentro_area_utile(self, (1024, 768))
        self.Bind(wx.EVT_CLOSE, self._alla_chiusura)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._al_minuto, self.timer)
        self.timer.Start(60_000)
        apertura = testi.apertura(mondo, origine, messaggi, rapporto, ultimo_prima, adesso_utc())
        if self.problemi_all_avvio:
            apertura = f"{testi.calendario_illeggibile(self.problemi_all_avvio)}\n{apertura}"
        if crash_precedente:
            apertura = f"{testi.crash_precedente(crash_precedente)}\n{apertura}"
        self.mostra(apertura)

    # Costruzione.

    def _crea_controlli(self):
        self.pannello = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.etichetta_vista = wx.StaticText(self.pannello, label="Vista principale")
        self.vista = wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.vista.SetName("Vista principale")
        self.etichetta_barra = wx.StaticText(self.pannello, label="Barra di stato")
        # Le righe della barra non vanno mai a capo, come in Tornello: restano di quaranta
        # caratteri anche con i caratteri grandi o la finestra stretta.
        self.barra = wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP)
        self.barra.SetName("Barra di stato")
        self.barra.Bind(wx.EVT_SET_FOCUS, self._alla_barra)
        sizer.Add(self.etichetta_vista, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        sizer.Add(self.vista, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.etichetta_barra, 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(self.barra, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        self.pannello.SetSizer(sizer)

    def voci_menu(self):
        """La tabella dei menu: per ogni menu il titolo e le voci, cioè testo, tasto rapido e comando; None separa."""
        return (
            ("&File", (("&Salva il mondo", "Ctrl+S", self.salva), None, ("&Esci", "Ctrl+Q", self.esci))),
            ("&Giocatori", (
                ("&Scheda del giocatore...", "Ctrl+G", self.scheda_giocatore),
                ("&Diario del giocatore...", "Ctrl+Shift+D", self.diario_giocatore),
                ("&Elenco dei giocatori", "Ctrl+E", lambda: self.mostra(testi.elenco_giocatori(self.mondo), "elenco dei giocatori", "elenco_giocatori")),
                ("&Classifica per valore", "Ctrl+L", lambda: self.mostra(testi.classifica(self.mondo), "classifica per valore", "classifica")),
                ("&TOP 10", "Ctrl+T", lambda: self.mostra(testi.top_10(self.mondo), "TOP 10", "top_10")),
                ("St&atistiche nazionali", "Ctrl+I", lambda: self.mostra(testi.statistiche(self.mondo), "statistiche nazionali", "statistiche_mondo")),
                None,
                ("Ce&rca giocatori...", "Ctrl+F", self.cerca),
                ("R&isultati della ricerca", "Ctrl+R", self.risultati),
                None,
                ("&Nuovi arrivati della sessione", "Ctrl+Shift+N", lambda: self.mostra(testi.lista_nuovi(self.mondo), "nuovi arrivati", "nuovi_arrivati")),
                ("Ritirati della sessi&one", "Ctrl+Shift+R", lambda: self.mostra(testi.lista_ritirati(self.mondo), "ritirati della sessione", "ritirati_sessione")),
                ("&Usciti di scena nella sessione", "Ctrl+Shift+U", lambda: self.mostra(testi.lista_usciti(self.mondo), "usciti di scena", "usciti_sessione")),
            )),
            ("&Polisportive", (
                ("&Nuova polisportiva...", "Ctrl+N", self.nuova_polisportiva),
                ("&Cambia polisportiva attiva...", "Ctrl+Shift+C", self.cambia_polisportiva),
                None,
                ("&Mercato...", "Ctrl+K", self.mercato),
                ("&Vendite dei tesserati...", None, self.vendite),
                ("Sv&incola un tesserato...", "Ctrl+Shift+S", self.svincola),
                ("Pa&ga gli arretrati...", "Ctrl+Shift+P", self.paga_arretrati),
                ("Sala &allenamento...", "Ctrl+Shift+L", self.sala_allenamento),
                ("Contratti e &rinnovi...", "Ctrl+Shift+K", self.contratti),
                # Lo staff della tappa 13, progetto 4.1: i tasti sono una proposta da confermare con Gabriele al collaudo.
                ("Staf&f della polisportiva attiva...", "Ctrl+H", self.staff),
                ("Mercato degli a&llenatori...", "Ctrl+Shift+G", self.mercato_allenatori),
                None,
                ("&Scheda della polisportiva attiva", "Ctrl+M", self.scheda_polisportiva),
                ("&Bilancio della polisportiva attiva", "Ctrl+B", self.bilancio),
                ("&Tesserati della polisportiva attiva", "Ctrl+Shift+T", self.tesserati_polisportiva),
                ("&Diario della polisportiva attiva", "Ctrl+Shift+M", self.diario_polisportiva),
                ("&Elenco delle polisportive", "Ctrl+Shift+E", lambda: self.mostra(testi.elenco_polisportive(self.mondo), "elenco delle polisportive", "elenco_polisportive")),
                None,
                ("&Password della polisportiva attiva...", None, self.password_polisportiva),
                ("C&hiudi la polisportiva attiva...", None, self.chiudi_polisportiva),
            )),
            ("Pa&rtite", (
                ("&Amichevole...", "Ctrl+O", self.amichevole),
                None,
                ("&Lancia una sfida...", "Ctrl+W", self.lancia_sfida),
                ("Sfide in a&rrivo...", "Ctrl+Shift+F", self.sfide_in_arrivo),
                ("S&torico delle sfide...", "Ctrl+Shift+H", self.storico_sfide),
                None,
                ("&Salva la cronaca", "Ctrl+Shift+O", self.salva_cronaca),
            )),
            # Il menu dei tornei, tappa 12, punto 12.1 del progetto: i tasti sono una proposta da confermare con Gabriele al collaudo.
            ("&Tornei", (
                ("&Calendario e iscrizioni...", "Ctrl+U", self.calendario_tornei),
                ("&Iscrizioni dei tuoi atleti...", "Ctrl+J", self.iscrizioni_tornei),
                ("&Tornei in corso...", "Ctrl+Y", self.tornei_in_corso),
                None,
                ("&Albo d'oro...", "Ctrl+Shift+B", self.albo_d_oro),
                ("Classifica &nazionale", "Ctrl+Shift+W", self.classifica_mondiale),
                None,
                ("&Editor dei modelli di torneo...", "Ctrl+Shift+J", self.editor_modelli),
                ("Editor delle &formule...", "Ctrl+Shift+Y", self.editor_formule),
                ("&Ripristina il calendario predefinito...", None, self.ripristina_calendario),
            )),
            ("&Mondo", (
                ("&Data e prossimo avanzamento", "Ctrl+D", lambda: self.mostra(testi.data_e_avanzamento(self.mondo, adesso_utc()), "data simulata", "data_e_avanzamento")),
                ("&Riepilogo dell'ultimo avanzamento", "Ctrl+Shift+A", self.riepilogo),
                ("&Vecchie glorie", "Ctrl+Shift+V", lambda: self.mostra(testi.vecchie_glorie(self.mondo), "vecchie glorie", "vecchie_glorie")),
            )),
            ("&Visualizza", (("Vista &principale", "F5", self.vai_alla_vista), ("&Barra di stato", "F7", self.vai_alla_barra))),
            ("&Impostazioni", (
                ("&Aspetto, colori e caratteri...", "Ctrl+P", self.cambia_aspetto),
                ("&Conservazione dei diari...", None, self.cambia_conservazione),
                ("&Effetti sonori...", None, self.cambia_effetti),
                ("&Velocità di gioco...", None, self.cambia_velocita),
                ("A&nnunci della cronaca...", None, self.cambia_annunci),
            )),
            ("&Aiuto", (
                ("&Guida ai comandi", "F1", lambda: self.mostra(testi.guida(self.voci_guida()), "guida ai comandi", "guida")),
                ("&Manuale", "Shift+F1", self.manuale),
                ("&Novità", "F2", self.novita),
                ("&Informazioni", "F3", lambda: self.mostra(testi.informazioni(), "informazioni", "informazioni")),
                ("&Offrimi un caffè...", None, self.caffe),
            )),
        )

    def _crea_menu(self):
        barra_menu = wx.MenuBar()
        for titolo, voci in self.voci_menu():
            menu = wx.Menu()
            for voce in voci:
                if voce is None:
                    menu.AppendSeparator()
                    continue
                testo, tasto, comando = voce
                elemento = menu.Append(wx.ID_ANY, f"{testo}\t{tasto}" if tasto else testo)
                self.Bind(wx.EVT_MENU, lambda event, c=comando: self._esegui(c), elemento)
            barra_menu.Append(menu, titolo)
        self.SetMenuBar(barra_menu)

    def voci_guida(self):
        """Le voci dei menu per la guida: titoli e testi senza le e commerciali, tasti con i nomi italiani."""
        voci = []
        for titolo, elenco in self.voci_menu():
            comandi = [(testo.replace("&", "").rstrip("."), tasto.replace("Shift", "Maiusc") if tasto else None) for testo, tasto, _c in filter(None, elenco)]
            voci.append((titolo.replace("&", ""), comandi))
        return voci

    def applica_aspetto(self):
        for controllo in (self.pannello, self.etichetta_vista, self.vista, self.etichetta_barra, self.barra):
            aspetto.applica(controllo, self.impostazioni)
        # La barra è alta quattro righe del suo carattere, più il bordo, la barra di scorrimento
        # orizzontale e mezza riga di margine, come il pie' di pagina di Tornello.
        riga = self.barra.GetCharHeight()
        fuori = max(self.barra.GetSize().height - self.barra.GetClientSize().height,
                    self.barra.GetWindowBorderSize().height + wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y, self.barra))
        self.barra.SetMinSize(wx.Size(-1, riga * RIGHE_BARRA + riga // 2 + fuori))
        self.pannello.Layout()

    # I suoni dell'avvio e degli errori.

    def suoni_d_avvio(self):
        """
        Il suono dell'avvio, da chiamare quando la finestra è comparsa: prima l'avvio dalla copia di
        sicurezza, poi quello con le collezioni di nomi difettose, poi la nascita di un mondo nuovo,
        e infine l'avvio di sempre. Se il mondo è avanzato mentre il programma era chiuso, segue il
        suono dell'avanzamento, quando il primo è finito. Dopo l'avvio suona una notizia sola, la più
        importante: dalla tappa 14 prima di tutte il crash della volta prima, staccato di un secondo
        come la notizia dello staff.
        """
        if self.origine == archivio.DALLA_COPIA:
            primo = "avvio_dalla_copia"
        elif self.avvisi_all_avvio:
            primo = "avvio_con_avvisi"
        elif self.origine == archivio.NATO:
            primo = "avvio_mondo_nuovo"
        else:
            primo = "avvio"
        suoni.suona(primo)
        if self.crash_precedente:
            suoni.in_coda("crash_precedente", pausa=PAUSA_NOTIZIA_DELLO_STAFF)
        elif self.problemi_all_avvio:
            suoni.in_coda("calendario_illeggibile")
        elif getattr(self.mondo, "staff_appena_nato", False):
            # Dalla tappa 13: il mondo appena aggiornato al formato 8 ha lo staff, e la notizia vale più dell'avanzamento.
            suoni.in_coda("staff_appena_nato", pausa=PAUSA_NOTIZIA_DELLO_STAFF)
        elif self.avanzamento_all_avvio:
            suoni.in_coda(self.avanzamento_all_avvio)

    def errore_imprevisto(self, tipo, valore):
        """
        Un'eccezione sfuggita a un comando: il comando muore in silenzio, e dalla tappa 14 il resoconto
        completo va nel registro degli errori, accanto al programma. Qui la dicono il suono
        dell'allarme e un messaggio, che dice dove sta il resoconto.
        """
        if not self or self.IsBeingDeleted() or self._errore_aperto:
            return
        self._errore_aperto = True
        self._modali += 1
        try:
            suoni.suona("errore_imprevisto")
            wx.MessageBox(f"Il comando si è interrotto per un errore imprevisto: {tipo.__name__}, {valore}. {testi.resoconto_degli_errori(percorsi.cartella())}",
                          "Errore imprevisto", wx.OK | wx.ICON_ERROR, self)
        finally:
            self._modali -= 1
            self._errore_aperto = False

    # Mostrare.

    def _esegui(self, comando):
        self.comandi += 1
        comando()

    def mostra(self, testo, evento=None, suono=None):
        """Mette il testo nella vista principale, al posto di quello di prima, con il cursore all'inizio; suono è l'effetto del comando."""
        if suono:
            suoni.suona(suono)
        self.vista.ChangeValue(testo)
        aspetto.ridai_stile(self.vista, self.impostazioni)
        self.vista.SetInsertionPoint(0)
        self.vista.ShowPosition(0)
        self.vista.SetFocus()
        if evento:
            self.ultimo_evento = evento
        self.aggiorna_barra()

    def aggiorna_barra(self):
        """Riscrive la barra di stato, ma solo se è cambiata: riscriverla riporta il cursore all'inizio."""
        testo = "\n".join(testi.righe_barra(self.mondo, self.ultimo_evento, adesso_utc()))
        if testo == self._testo_barra:
            return
        self._testo_barra = testo
        self.barra.ChangeValue(testo)
        aspetto.ridai_stile(self.barra, self.impostazioni)

    def _alla_barra(self, event):
        """Quando il cursore arriva sulla barra, la ricalcola prima che lo screen reader la legga."""
        self.aggiorna_barra()
        event.Skip()

    def _al_minuto(self, event):
        """
        Ogni minuto, se è maturato un giorno simulato e non c'è un dialogo aperto, fa avanzare il
        mondo; poi rinfresca il tempo che manca all'avanzamento, ma non sotto il cursore di chi legge.
        """
        if not self._modali and self.mondo.ticks_maturati():
            self.avanza()
        if not self.barra.HasFocus():
            self.aggiorna_barra()

    def _ha_polisportive(self):
        return any(not p.is_cpu_controlled for p in self.mondo.polisportive.values())

    @staticmethod
    def _problemi_del_calendario():
        """I problemi del calendario dei tornei, modelli e formule che non si leggono, in frasi; una lista vuota se va tutto bene."""
        try:
            return modelli_torneo.GestoreModelli().problemi()
        except OSError as errore:
            return [f"La cartella dei tornei non si legge: {errore}"]

    def _sfidante(self):
        """Il nome della prima polisportiva che aspetta la risposta di una delle tue a una sfida, per la barra; None se nessuna."""
        for p in self.mondo.polisportive.values():
            if not p.is_cpu_controlled:
                for s in self.mondo.sfide.proposte_per(p.nome):
                    return s.sfidante["nome"]
        return None

    def _evento_avanzamento(self, rapporto, salvato):
        """
        Il suono e la riga della barra di un avanzamento, con suoni.evento_avanzamento: il calendario
        con problemi si dice una volta per sessione e a ogni cambio, e la sfida in attesa col nome di chi sfida.
        """
        if rapporto and rapporto.get("calendario_con_problemi"):
            problemi = tuple(self._problemi_del_calendario())
            if problemi == self._problemi_detti:
                rapporto = {**rapporto, "calendario_con_problemi": 0}
            else:
                self._problemi_detti = problemi or None
        return suoni.evento_avanzamento(rapporto, salvato, self._ha_polisportive(), self._sfidante())

    def avanza(self):
        """
        Fa avanzare il mondo dei giorni maturati, salva e lo annuncia nella barra di stato, con un
        suono solo: quello della notizia più importante, che si mette in coda se sta suonando
        l'effetto di un comando.
        """
        rapporto = self.mondo.processa_tempo_trascorso()
        if not rapporto["ticks"]:
            return
        self.rapporto = rapporto
        self.rapporto_sessione = testi.somma_rapporti(self.rapporto_sessione, rapporto) if self.rapporto_sessione else rapporto
        salvato, _messaggi, _avvisi = self._salva_raccogliendo()
        evento, self.ultimo_evento = self._evento_avanzamento(rapporto, salvato)
        suoni.in_coda(evento)

    def _modale(self, dialogo):
        """Mostra un dialogo modale; finché resta aperto, il mondo non avanza."""
        self._modali += 1
        try:
            return dialogo.ShowModal()
        finally:
            self._modali -= 1

    def _domanda(self, testo, titolo, suono="domanda"):
        """Una domanda sì o no, con il no già scelto; finché è aperta, il mondo non avanza. Al no suona l'annullamento."""
        self._modali += 1
        try:
            suoni.suona(suono)
            risposta = wx.MessageBox(testo, titolo, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION, self)
        finally:
            self._modali -= 1
        if risposta != wx.YES:
            suoni.suona("annullato")
        return risposta

    def vai_alla_vista(self):
        suoni.suona("fuoco_vista")
        self.vista.SetFocus()

    def vai_alla_barra(self):
        suoni.suona("fuoco_barra")
        if self.barra.HasFocus():
            self.aggiorna_barra()
        self.barra.SetFocus()

    # Comandi.

    def _salva_raccogliendo(self):
        """Salva il mondo e restituisce l'esito, i messaggi dell'archivio e, a parte, i suoi avvisi."""
        messaggi = []
        notifica = self.mondo.notifica
        self.mondo.notifica = messaggi.append
        try:
            riuscito, avvisi = archivio.salva_con_avvisi(self.mondo)
        finally:
            self.mondo.notifica = notifica
        return riuscito, messaggi, avvisi

    def _concludi(self, testo, evento, suono, salvare=True, coda=None, salvataggio=None):
        """
        La fine di un'operazione sulle polisportive: si salva subito, poi la vista mostra l'esito con
        il suo suono. Se il salvataggio non riesce, la vista aggiunge il perché, e dopo il suono
        dell'operazione si sente quello del salvataggio fallito. coda, se c'è, è un testo lungo da
        mettere dopo il perché, come la cronaca intera di un'amichevole, perché il perché resti a
        portata di mano e non in fondo a centinaia di righe. salvataggio, se c'è, è la coppia di
        esito e messaggi di un salvataggio già fatto, come quello prima della partita dal vivo.
        """
        riuscito, messaggi = True, []
        if salvataggio is not None:
            riuscito, messaggi = salvataggio
        elif salvare:
            riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        if not riuscito:
            testo = "\n".join([testo, *messaggi])
        if coda:
            testo = f"{testo}\n{coda}"
        self.mostra(testo, evento, suono)
        if not riuscito:
            suoni.in_coda("salvataggio_non_riuscito")

    def salva(self):
        riuscito, messaggi, avvisi = self._salva_raccogliendo()
        if not riuscito:
            suono = "salvataggio_non_riuscito"
        elif avvisi:
            suono = "salvataggio_con_avviso"
        else:
            suono = "salvataggio_riuscito"
        self.mostra("\n".join(messaggi), f"salvato alle {adesso():%H:%M}" if riuscito else "salvataggio non riuscito", suono)

    def esci(self):
        self.Close()

    def _scegli_giocatore(self, titolo, pulsante, suono, giocatori=None):
        """
        Il giocatore scelto nel dialogo, oppure None se il dialogo è stato annullato; suono è quello
        dell'apertura, e giocatori, se dato, restringe l'elenco, che altrimenti ha tutto il mondo.
        """
        dialogo = SceltaGiocatore(self, self.mondo, titolo, pulsante, giocatori)
        try:
            suoni.suona(suono)
            if self._modale(dialogo) == wx.ID_OK:
                return dialogo.scelto
            suoni.suona("annullato")
            return None
        finally:
            dialogo.Destroy()

    def scheda_giocatore(self):
        g = self._scegli_giocatore("Scheda del giocatore", "&Mostra la scheda", "dialogo_scheda_giocatore")
        if g is not None:
            self.mostra(testi.scheda_giocatore(g, self.mondo), f"scheda di {testi.nome_completo(g)}", "scheda_giocatore")

    def diario_giocatore(self):
        g = self._scegli_giocatore("Diario del giocatore", "&Mostra il diario", "dialogo_diario_giocatore")
        if g is not None:
            self.mostra(testi.diario_giocatore(g), f"diario di {testi.nome_completo(g)}", "diario_giocatore")

    def diario_polisportiva(self):
        p = self._attiva()
        if p is not None:
            self.mostra(testi.diario_polisportiva(p), f"diario di {p.nome}", "diario_polisportiva")

    def cambia_conservazione(self):
        dialogo = Conservazione(self, self.mondo.conservazione_diari)
        try:
            suoni.suona("dialogo_conservazione")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.mondo.conservazione_diari = dialogo.risultato
                self.mostra(testi.conservazione(self.mondo) + " Le voci più vecchie si tolgono a ogni salvataggio.", "conservazione dei diari", "conservazione_applicata")
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cerca(self):
        dialogo = Ricerca(self)
        try:
            suoni.suona("dialogo_ricerca")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                ambito, criterio, condizione, valore, descrizione = dialogo.risultato
                ids = ricerca.cerca(self.mondo, ambito, criterio, condizione, valore)
                self.mondo.risultati_ultima_ricerca = ids
                self.ultima_ricerca = descrizione
                self.mostra(testi.risultati_ricerca(self.mondo, descrizione, ids), f"trovati {len(ids)}", "ricerca_con_risultati" if ids else "ricerca_senza_risultati")
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def risultati(self):
        if self.ultima_ricerca is None:
            self.mostra("In questa sessione non hai ancora fatto ricerche: si cercano con Ctrl+F.", "nessuna ricerca", "nessuna_ricerca")
            return
        self.mostra(testi.risultati_ricerca(self.mondo, self.ultima_ricerca, self.mondo.risultati_ultima_ricerca), "risultati della ricerca", "risultati_ricerca")

    def riepilogo(self):
        """Il riepilogo dell'ultimo avanzamento; se nella sessione il mondo non è ancora avanzato, lo dice con il suo suono."""
        avanzato = bool(self.rapporto and self.rapporto["ticks"])
        self.mostra(testi.riepilogo_avanzamento(self.rapporto), "ultimo avanzamento", "riepilogo_avanzamento" if avanzato else "nessun_avanzamento")

    def scheda_polisportiva(self):
        p = self._attiva()
        if p is not None:
            self.mostra(testi.scheda_polisportiva(p, self.mondo), f"scheda di {p.nome}", "scheda_polisportiva")

    def tesserati_polisportiva(self):
        if self._attiva() is not None:
            self.mostra(testi.tesserati_attiva(self.mondo), "tesserati", "tesserati_polisportiva")

    # Le operazioni delle polisportive.

    def _attiva(self):
        """La polisportiva attiva; se non c'è, lo dice nella vista principale e restituisce None."""
        p = self.mondo.miapolisportiva_attiva
        if p is None:
            self.mostra("Non hai una polisportiva attiva: fondane una con Ctrl+N, o sceglila con Ctrl+Maiusc+C.", "nessuna polisportiva", "nessuna_polisportiva_attiva")
        return p

    def nuova_polisportiva(self):
        dialogo = NuovaPolisportiva(self, self.mondo)
        try:
            suoni.suona("dialogo_nuova_polisportiva")
            if self._modale(dialogo) != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return
            nome, password, attiva, luogo = dialogo.risultato
        finally:
            dialogo.Destroy()
        p = self.mondo.fonda_polisportiva(nome, password, attiva, luogo)
        self._concludi(testi.fondata(p, self.mondo), f"fondata {p.nome}", "polisportiva_fondata")

    def cambia_polisportiva(self):
        if all(p.is_cpu_controlled for p in self.mondo.polisportive.values()):
            self.mostra("Non hai ancora nessuna polisportiva: fondane una con Ctrl+N.", "nessuna polisportiva", "nessuna_polisportiva_tua")
            return
        dialogo = CambiaPolisportiva(self, self.mondo)
        try:
            suoni.suona("dialogo_cambia_polisportiva")
            if self._modale(dialogo) != wx.ID_OK or dialogo.scelta is None:
                suoni.suona("annullato")
                return
            p = dialogo.scelta
        finally:
            dialogo.Destroy()
        self.mondo.miapolisportiva_attiva = p
        self._concludi(testi.scheda_polisportiva(p, self.mondo), f"attiva {p.nome}", "polisportiva_attivata")

    def mercato(self):
        p = self._attiva()
        if p is None:
            return
        # Il suono dell'apertura viene prima del dialogo, che se nasce con l'elenco vuoto lo dice subito dopo.
        suoni.suona("dialogo_mercato")
        dialogo = Mercato(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_mercato(p, self.mondo, esiti), f"mercato: {testi.conta(len(esiti), 'offerta', 'offerte')}", "lavoro_concluso", bool(esiti))

    def bilancio(self):
        p = self._attiva()
        if p is not None:
            self.mostra(testi.bilancio(p, self.mondo), f"bilancio di {p.nome}", "bilancio")

    def paga_arretrati(self):
        p = self._attiva()
        if p is None:
            return
        if not any(self.mondo.giocatori[gid].arretrati for gid in p.tesserati if gid in self.mondo.giocatori):
            self.mostra(f"Nessun tesserato di {p.nome} aspetta arretrati. {testi.info_mercato(p, self.mondo)}", "nessun arretrato", "nessun_arretrato")
            return
        dialogo = PagaArretrati(self, self.mondo, p)
        try:
            suoni.suona("dialogo_arretrati")
            self._modale(dialogo)
            pagati = list(dialogo.pagati)
        finally:
            dialogo.Destroy()
        righe = [f"Pagati {testi.euro(importo)} a {testi.nome_completo(g)}." for g, importo in pagati] or ["Nessun pagamento."]
        self._concludi("\n".join([*righe, testi.bilancio(p, self.mondo)]), f"arretrati: {testi.conta(len(pagati), 'pagamento', 'pagamenti')}", "lavoro_concluso", bool(pagati))

    def vendite(self):
        p = self._attiva()
        if p is None:
            return
        if not p.tesserati:
            self.mostra(f"{p.nome} non ha tesserati da vendere.", "nessun tesserato", "rosa_vuota")
            return
        dialogo = Vendite(self, self.mondo, p)
        try:
            suoni.suona("dialogo_vendite")
            self._modale(dialogo)
            fatte = list(dialogo.fatte)
        finally:
            dialogo.Destroy()
        self._concludi("\n".join(fatte or ["Nessuna vendita cambiata."]), f"vendite: {testi.conta(len(fatte), 'modifica', 'modifiche')}", "lavoro_concluso", bool(fatte))

    def _rosa_attiva(self, p):
        return [self.mondo.giocatori[gid] for gid in p.tesserati if gid in self.mondo.giocatori]

    def sala_allenamento(self):
        """
        La sala allenamento della tappa 11: spese a mano, allenamento completo, Allena tutti,
        programma e intensità. Alla chiusura la vista mostra le spese con il dettaglio e i cambi, e il
        mondo si salva soltanto se qualcosa è cambiato.
        """
        p = self._attiva()
        if p is None:
            return
        if not self._rosa_attiva(p):
            self.mostra(f"{p.nome} non ha tesserati da allenare.", "nessun tesserato", "rosa_vuota")
            return
        suoni.suona("dialogo_sala_allenamento")
        dialogo = SalaAllenamento(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti, cambi = list(dialogo.esiti), dialogo.cambi()
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_sala(p, esiti, cambi), testi.evento_sala(esiti, cambi), "lavoro_concluso", bool(esiti or cambi))

    def contratti(self):
        """I contratti e i rinnovi della tappa 11: alla chiusura la vista mostra gli esiti delle proposte, e il mondo si salva se ce ne sono."""
        p = self._attiva()
        if p is None:
            return
        if not self._rosa_attiva(p):
            self.mostra(f"{p.nome} non ha tesserati con un contratto.", "nessun tesserato", "rosa_vuota")
            return
        suoni.suona("dialogo_contratti")
        dialogo = Contratti(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_contratti(p, esiti), testi.evento_contratti(esiti), "lavoro_concluso", bool(esiti))

    def staff(self):
        """Lo staff della tappa 13: alla chiusura la vista mostra le operazioni e lo staff di adesso, e il mondo si salva se ce ne sono."""
        p = self._attiva()
        if p is None:
            return
        suoni.suona("dialogo_staff")
        dialogo = Staff(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_staff(p, esiti, self.mondo), testi.evento_staff(esiti), "lavoro_concluso", bool(esiti))

    def mercato_allenatori(self):
        """Il mercato degli allenatori della tappa 13, con lo stesso riepilogo dello staff alla chiusura."""
        p = self._attiva()
        if p is None:
            return
        # Il suono dell'apertura viene prima del dialogo, che se nasce con l'elenco vuoto lo dice subito dopo.
        suoni.suona("dialogo_mercato_allenatori")
        dialogo = MercatoAllenatori(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_staff(p, esiti, self.mondo), testi.evento_staff(esiti), "lavoro_concluso", bool(esiti))

    def svincola(self):
        p = self._attiva()
        if p is None:
            return
        rosa = [self.mondo.giocatori[gid] for gid in p.tesserati if gid in self.mondo.giocatori]
        if not rosa:
            self.mostra(f"{p.nome} non ha tesserati da svincolare.", "nessun tesserato", "rosa_vuota")
            return
        # Le mosse si guardano prima di far scegliere il tesserato, non dopo.
        if self.mondo.mosse_rimaste(p) <= 0:
            self.mostra(f"Per oggi {p.nome} ha finito le mosse di mercato.", "nessuna mossa", "mosse_finite")
            return
        dialogo = SceltaGiocatore(self, self.mondo, f"Svincola un tesserato di {p.nome}", "S&vincola", rosa)
        try:
            suoni.suona("dialogo_svincolo")
            if self._modale(dialogo) != wx.ID_OK or dialogo.scelto is None:
                suoni.suona("annullato")
                return
            g = dialogo.scelto
        finally:
            dialogo.Destroy()
        # Dalla tappa 11 lo svincolo a contratto in corso costa una buonuscita: se la cassa non basta, si dice prima.
        problema = self.mondo.problema_svincolo(p, g)
        if problema:
            self.mostra(problema, "cassa insufficiente", "cassa_insufficiente")
            return
        if self._domanda(testi.domanda_svincolo(g, p, self.mondo), "Svincolo") != wx.YES:
            return
        buonuscita = self.mondo.svincola(p, g)
        self._concludi(testi.svincolato(g, p, self.mondo, buonuscita), f"svincolato {testi.nome_completo(g)}", "tesserato_svincolato")

    def password_polisportiva(self):
        p = self._attiva()
        if p is None:
            return
        dialogo = PasswordPolisportiva(self, p)
        try:
            suoni.suona("dialogo_password")
            if self._modale(dialogo) != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return
            p.imposta_password(dialogo.risultato)
        finally:
            dialogo.Destroy()
        self._concludi(testi.password_cambiata(p), "password" if p.protetta else "senza password", "password_impostata" if p.protetta else "password_tolta")

    def chiudi_polisportiva(self):
        p = self._attiva()
        if p is None:
            return
        if p.protetta:
            dialogo = ChiediPassword(self, p, f"Per chiudere {p.nome} serve la sua password.")
            try:
                suoni.suona("richiesta_password")
                if self._modale(dialogo) != wx.ID_OK:
                    suoni.suona("annullato")
                    return
            finally:
                dialogo.Destroy()
        if self._domanda(testi.domanda_chiusura(p), "Chiusura", "domanda_chiusura_polisportiva") != wx.YES:
            return
        liberati = self.mondo.chiudi_polisportiva(p)
        self._concludi(testi.chiusa(p.nome, liberati), f"chiusa {p.nome}", "polisportiva_chiusa")

    # L'amichevole, tappa 9.

    def _tuoi(self):
        """I numeri dei tesserati di tutte le tue polisportive."""
        return {gid for p in self.mondo.polisportive.values() if not p.is_cpu_controlled for gid in p.tesserati}

    def amichevole(self):
        """
        Un'amichevole, regole di Gabriele: il primo giocatore è un tesserato della polisportiva
        attiva, il secondo chiunque altro, e nessuno dei due deve aver già giocato un'amichevole
        oggi. Dopo le opzioni l'incontro si gioca e si registra subito e il mondo si salva; con
        Assisti si apre la finestra dal vivo, e quando se ne esce con Alt+V o dal risultato, o
        subito con Vai alla fine, la vista mostra il risultato, i punti allenamento e sotto la
        cronaca intera. L'esito suona quando si vede, non prima. Chi esce con Esc prima della fine
        non lo vede, decisione D30: la vista dice soltanto che l'incontro è registrato e dove
        leggerne il risultato; a incontro finito Esc vale come il pulsante del risultato.
        """
        p = self._attiva()
        if p is None:
            return
        motore = MotorePartita(self.mondo)
        rosa = [self.mondo.giocatori[gid] for gid in p.tesserati if gid in self.mondo.giocatori]
        if not rosa:
            self.mostra(f"{p.nome} non ha tesserati da far giocare.", "nessun tesserato", "rosa_vuota")
            return
        primi = motore.disponibili(rosa)
        if not primi:
            self.mostra(testi.nessuno_per_l_amichevole(self.mondo, adesso_utc(), poli=p), "nessuno gioca oggi", "nessun_giocatore_oggi")
            return
        tuo = self._scegli_giocatore(f"Amichevole, il tuo giocatore di {p.nome}", "&Avanti", "dialogo_amichevole", primi)
        if tuo is None:
            return
        avversari = motore.disponibili(g for g in self.mondo.giocatori.values() if g is not tuo)
        if not avversari:
            self.mostra(testi.nessuno_per_l_amichevole(self.mondo, adesso_utc(), primo=tuo), "nessuno gioca oggi", "nessun_giocatore_oggi")
            return
        avversario = self._scegli_giocatore(f"Amichevole, l'avversario di {testi.nome_completo(tuo)}", "&Avanti", "dialogo_avversario", avversari)
        if avversario is None:
            return
        ultime = (self.impostazioni["amichevole_set"], self.impostazioni["amichevole_modo"], self.impostazioni["amichevole_livello"])
        dialogo = OpzioniAmichevole(self, self.mondo, tuo, avversario, ultime)
        try:
            suoni.suona("dialogo_opzioni_amichevole")
            if self._modale(dialogo) != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return
            set_al_meglio, modo, livello = dialogo.risultato
        finally:
            dialogo.Destroy()
        # Le scelte si ricordano per la prossima amichevole, anche dopo la chiusura (Gabriele, 8 ottobre 2026).
        # Se il file non si scrive, valgono comunque per questa sessione: l'incontro non si ferma per questo.
        if ultime != (set_al_meglio, modo, livello):
            self.impostazioni.update(amichevole_set=set_al_meglio, amichevole_modo=modo, amichevole_livello=livello)
            modulo_impostazioni.salva(self.impostazioni)
        # Il tuo giocatore è tuo per definizione; l'avversario può esserlo anche lui, di una qualunque delle tue polisportive.
        fra_tuoi = avversario.id in self._tuoi()
        istante, data_simulata = adesso(), self.mondo.datetime_corrente_simulazione
        gemello = None
        if modo == ASSISTI:
            risultato, gemello = motore.amichevole_da_assistere(tuo.id, avversario.id, set_al_meglio, velocita=self.impostazioni["velocita_gioco"])
        else:
            risultato = motore.gioca_amichevole(tuo.id, avversario.id, set_al_meglio)
        id_vincitore = risultato.parti[0] if risultato.vincitore == "A" else risultato.parti[1]
        if fra_tuoi:
            esito = "amichevole_fra_tuoi"
        elif id_vincitore == tuo.id:
            esito = "amichevole_vinta"
        else:
            esito = "amichevole_persa"
        self.incontro = v = UltimoIncontro(risultato, motore.nomi(risultato), livello, esito, istante, data_simulata)
        # Il mondo si salva subito, anche prima della partita dal vivo: chi esce a metà la trova già registrata.
        riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        uscita = self._dal_vivo(v, gemello) if gemello is not None else None
        if uscita == CON_ESC:
            # Esc non svela il risultato, decisione D30: la vista dice soltanto che l'incontro è
            # registrato e dove leggerlo, con un suono suo e non quello dell'esito, e la barra non dice chi ha vinto.
            self._concludi(testi.amichevole_senza_risultato(v.nomi), "amichevole registrata", "amichevole_registrata", salvataggio=(riuscito, messaggi))
            return
        # Alt+V nella finestra dal vivo: prima i cinque guizzi del salto alla fine, poi l'esito. Se il
        # salvataggio non è riuscito, dopo l'esito si sente quello, e i guizzi restano fuori: due suoni
        # messi in coda insieme si sovrapporrebbero.
        salto = uscita == ALLA_FINE and riuscito
        # La cronaca intera va in coda, dopo il perché di un salvataggio non riuscito, che così resta in cima.
        self._concludi(testi.amichevole_solo_risultato(risultato, self.mondo), v.evento_esito, "resto_dell_incontro" if salto else esito,
                       coda=testi.cronaca_amichevole(risultato, v.nomi, livello), salvataggio=(riuscito, messaggi))
        if salto:
            suoni.in_coda(esito)

    def _dal_vivo(self, v, gemello):
        """
        La finestra dal vivo dell'amichevole v, con l'incontro gemello da svolgere; restituisce come se
        n'è usciti. La velocità di gioco cambiata con più e meno vale anche per le partite che seguono.
        """
        dialogo = FinestraDalVivo(self, gemello, v.nomi, v.livello, self.impostazioni["velocita_gioco"], self.impostazioni)
        try:
            suoni.suona("amichevole_al_via")
            self._modale(dialogo)
            uscita, velocita = dialogo.uscita, dialogo.velocita
        finally:
            dialogo.Destroy()
        if velocita != self.impostazioni["velocita_gioco"]:
            self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "velocita_gioco": velocita})
            modulo_impostazioni.salva(self.impostazioni)
        return uscita

    def salva_cronaca(self):
        """
        La cronaca dell'ultimo incontro mostrato o ascoltato, dalla tappa 12 anche di torneo o di sfida,
        nel suo file, nella cartella delle cronache, al livello scelto; intestazione e nome del file
        dicono quando si è giocato, non quando si salva.
        """
        v = self.incontro
        if v is None:
            self.mostra(testi.NESSUNA_AMICHEVOLE, "nessun incontro", "nessun_incontro")
            return
        try:
            percorso = MotorePartita(self.mondo).salva_cronaca(v.risultato, v.livello, istante=v.istante, data_simulata=v.data_simulata, nomi=v.nomi)
        except OSError as errore:
            self.mostra(testi.cronaca_non_salvata(errore, v.tipo), "cronaca non salvata", "cronaca_non_salvata")
            return
        self.mostra(testi.cronaca_salvata(percorso, v.livello, v.nomi, v.tipo), "cronaca salvata", "cronaca_salvata")

    def _salva_velocita(self, velocita):
        """La velocità di gioco a cui si è arrivati ascoltando dal vivo o in differita: vale anche per le partite che seguono."""
        if velocita is not None and velocita != self.impostazioni["velocita_gioco"]:
            self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "velocita_gioco": velocita})
            modulo_impostazioni.salva(self.impostazioni)

    # Le sfide, tappa 12, punto 12.6.

    def lancia_sfida(self):
        """Il lancio di una sfida a una polisportiva del computer, che risponde subito; alla chiusura la vista dice gli esiti e il mondo si salva."""
        p = self._attiva()
        if p is None:
            return
        if sfide.disponibili(self.mondo, p) <= 0:
            self.mostra(f"{p.nome} non ha sfide da lanciare: il primo del mese ne arrivano due, fino a quattro.", "nessuna sfida da lanciare",
                        "nessuna_sfida_da_lanciare")
            return
        suoni.suona("dialogo_lancia_sfida")
        dialogo = LanciaSfida(self, self.mondo, p, self.impostazioni)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join([f"Sfide lanciate da {p.nome}: {len(esiti)}.", *esiti]) if esiti else f"{p.nome} non ha lanciato sfide."
        self._concludi(testo, f"sfide: {testi.conta(len(esiti), 'lancio', 'lanci')}", "lavoro_concluso", bool(esiti))

    def sfide_in_arrivo(self):
        """Le sfide che aspettano la risposta della polisportiva attiva, entro oggi, prima dell'avanzamento seguente: accettare con la formazione o rifiutare."""
        p = self._attiva()
        if p is None:
            return
        suoni.suona("dialogo_sfide_in_arrivo")
        dialogo = SfideInArrivo(self, self.mondo, p)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join([f"Risposte di {p.nome} alle sfide: {len(esiti)}.", *esiti]) if esiti else f"{p.nome} non ha risposto a nessuna sfida."
        self._concludi(testo, f"sfide: {testi.conta(len(esiti), 'risposta', 'risposte')}", "lavoro_concluso", bool(esiti))

    def storico_sfide(self):
        """Lo storico delle sfide delle tue polisportive, con l'ascolto in differita e la cronaca delle ultime dieci."""
        if not any(not p.is_cpu_controlled for p in self.mondo.polisportive.values()):
            self.mostra("Non hai ancora nessuna polisportiva: fondane una con Ctrl+N.", "nessuna polisportiva", "nessuna_polisportiva_tua")
            return
        suoni.suona("storico_sfide")
        dialogo = StoricoSfide(self, self.mondo, self.impostazioni)
        try:
            self._modale(dialogo)
            ultimo, velocita = dialogo.ultimo, dialogo.velocita
        finally:
            dialogo.Destroy()
        self._salva_velocita(velocita)
        if ultimo is not None:
            self.incontro = ultimo

    # I tornei, tappa 12, punto 12.1.

    def calendario_tornei(self, iscrizioni_subito=False):
        """
        Il calendario dei tornei e le iscrizioni a mano della polisportiva attiva: alla chiusura la vista
        dice le iscrizioni fatte e tolte, e il mondo si salva; se si è chiesto il pannello di un'edizione
        in corso, si apre subito dopo.
        """
        p = self._attiva()
        if p is None:
            return
        suoni.suona("dialogo_iscrizioni_tornei" if iscrizioni_subito else "dialogo_calendario_tornei")
        dialogo = CalendarioTornei(self, self.mondo, p, self.impostazioni, iscrizioni_subito)
        try:
            self._modale(dialogo)
            fatte, pannello = list(dialogo.fatte), dialogo.pannello_chiesto
        finally:
            dialogo.Destroy()
        self._concludi(testi.riepilogo_calendario(p, fatte), testi.evento_calendario(fatte) if fatte else "calendario", "lavoro_concluso", bool(fatte))
        if pannello is not None:
            self.tornei_in_corso(pannello)

    def iscrizioni_tornei(self):
        self.calendario_tornei(iscrizioni_subito=True)

    def tornei_in_corso(self, torneo_scelto=None):
        """
        Il pannello dei tornei in corso e conclusi di recente: alla chiusura l'ultimo incontro ascoltato o
        letto diventa quello di Salva la cronaca, e se si sono mostrati dei risultati il mondo si salva.
        """
        suoni.suona("dialogo_tornei_in_corso")
        dialogo = PannelloTornei(self, self.mondo, self.impostazioni, torneo_scelto)
        try:
            self._modale(dialogo)
            ultimo, velocita, svelati = dialogo.ultimo, dialogo.velocita, dialogo.svelati
        finally:
            dialogo.Destroy()
        self._salva_velocita(velocita)
        if ultimo is not None:
            self.incontro = ultimo
        righe = [f"Pannello dei tornei: {testi.conta(svelati, 'risultato mostrato', 'risultati mostrati')}."]
        if ultimo is not None:
            righe.append(f"L'ultimo incontro, {ultimo.nomi['A'].testo} contro {ultimo.nomi['B'].testo}, ha la cronaca da salvare con Ctrl+Maiusc+O.")
        self._concludi("\n".join(righe), "pannello dei tornei", "lavoro_concluso", bool(svelati))

    def albo_d_oro(self):
        suoni.suona("albo_d_oro")
        dialogo = AlboDOro(self, self.mondo)
        try:
            self._modale(dialogo)
        finally:
            dialogo.Destroy()

    def classifica_mondiale(self):
        self.mostra(testi.classifica_mondiale(self.mondo, tuoi=tuoi_del_mondo(self.mondo)), "classifica nazionale", "classifica_mondiale")

    def editor_modelli(self):
        """L'editor dei modelli di torneo: alla chiusura la vista dice che cosa è cambiato; il mondo non si tocca, perché i modelli stanno accanto al gioco."""
        suoni.suona("dialogo_editor_modelli")
        dialogo = EditorModelli(self)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join(["Modelli di torneo: le modifiche valgono per le edizioni future.", *esiti]) if esiti else "Nessun modello di torneo cambiato."
        self._problemi_detti = None
        self.mostra(testo, f"modelli: {testi.conta(len(esiti), 'modifica', 'modifiche')}", "lavoro_concluso")

    def editor_formule(self):
        """L'editor delle formule: alla chiusura la vista dice le formule salvate ed eliminate."""
        suoni.suona("dialogo_editor_formule")
        dialogo = EditorFormule(self)
        try:
            self._modale(dialogo)
            esiti = list(dialogo.esiti)
        finally:
            dialogo.Destroy()
        testo = "\n".join(["Formule dei tornei: le modifiche valgono per le edizioni future.", *esiti]) if esiti else "Nessuna formula cambiata."
        self._problemi_detti = None
        self.mostra(testo, f"formule: {testi.conta(len(esiti), 'modifica', 'modifiche')}", "lavoro_concluso")

    def ripristina_calendario(self):
        """Rimette il calendario predefinito, dopo la domanda col no già scelto: quello di prima va da parte, e cambiano soltanto le edizioni future."""
        domanda = ("Rimettere il calendario predefinito dei tornei? I modelli e le formule di adesso vanno in una cartella a parte, dentro la cartella tornei, "
                   "e cambiano soltanto le edizioni future.")
        if self._domanda(domanda, "Ripristina il calendario") != wx.YES:
            return
        try:
            da_parte = modelli_torneo.GestoreModelli().ripristina_predefiniti()
        except OSError as errore:
            self.mostra(f"Il calendario predefinito non si è potuto rimettere: {errore}.", "calendario non ripristinato", "calendario_illeggibile")
            return
        self._problemi_detti = None
        self.mostra(f"Il calendario predefinito è tornato. Quello di prima è nella cartella {da_parte}.", "calendario predefinito", "calendario_ripristinato")

    # Le impostazioni.

    def _salva_impostazioni(self, suono_riuscito):
        """Salva le impostazioni e suona com'è andata; restituisce vero se il file si è scritto."""
        salvate = modulo_impostazioni.salva(self.impostazioni)
        suoni.suona(suono_riuscito if salvate else "impostazioni_non_salvate")
        return salvate

    def cambia_aspetto(self):
        dialogo = Aspetto(self, self.impostazioni)
        try:
            suoni.suona("dialogo_aspetto")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = dialogo.risultato
                salvate = self._salva_impostazioni("aspetto_applicato")
                self.applica_aspetto()
                self.ultimo_evento = "aspetto aggiornato" if salvate else "aspetto non salvato"
                self._testo_barra = None
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_effetti(self):
        """
        Il volume degli effetti sonori e, dalla decisione D30, quello della partita dal vivo: il primo
        vale subito, e l'OK si sente già al volume nuovo; il secondo dalla prossima partita.
        """
        dialogo = EffettiSonori(self, self.impostazioni["volume_effetti"], self.impostazioni["volume_partita"])
        try:
            suoni.suona("dialogo_effetti_sonori")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                effetti, partita = dialogo.risultato
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "volume_effetti": effetti, "volume_partita": partita})
                suoni.imposta_volume(self.impostazioni["volume_effetti"])
                salvate = self._salva_impostazioni("effetti_sonori_applicati")
                volumi = f"effetti {self.impostazioni['volume_effetti']}, partita {self.impostazioni['volume_partita']}"
                self.ultimo_evento = f"volume {volumi}" if salvate else "volumi non salvati"
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_velocita(self):
        """La velocità di gioco della partita dal vivo, decisioni D12 e D29: vale dalla prossima partita, e anche dopo la chiusura."""
        dialogo = VelocitaDiGioco(self, self.impostazioni["velocita_gioco"])
        try:
            suoni.suona("dialogo_velocita_di_gioco")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, "velocita_gioco": dialogo.risultato})
                salvate = self._salva_impostazioni("velocita_di_gioco_salvata")
                self.ultimo_evento = f"velocità di gioco {self.impostazioni['velocita_gioco']}" if salvate else "velocità di gioco non salvata"
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def cambia_annunci(self):
        """Gli annunci della cronaca della partita dal vivo e della differita, 1.79.0: valgono dalla riga seguente, e anche dopo la chiusura."""
        dialogo = AnnunciDellaCronaca(self, self.impostazioni)
        try:
            suoni.suona("dialogo_annunci_cronaca")
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = modulo_impostazioni.valide({**self.impostazioni, **dialogo.risultato})
                salvate = self._salva_impostazioni("annunci_cronaca_salvati")
                stato = "accesi" if self.impostazioni["annunci_cronaca"] else "spenti"
                self.ultimo_evento = f"annunci della cronaca {stato}" if salvate else "annunci della cronaca non salvati"
                self.aggiorna_barra()
            else:
                suoni.suona("annullato")
        finally:
            dialogo.Destroy()

    def novita(self):
        try:
            with open(percorsi.risorsa("CHANGELOG.md"), encoding="utf-8") as f:
                testo = testi.novita(f.read())
            suono = "novita"
        except OSError as e:
            testo = f"Il file delle novità non si può leggere: {e}."
            suono = "novita_illeggibile"
        self.mostra(testo, "novità", suono)

    def manuale(self):
        """
        Il manuale, manuale.html, nel browser predefinito, dalla tappa 14: la vista resta com'era, e la
        barra dice che il manuale è aperto. Se il file manca, o Windows non lo apre, lo dice la vista,
        col suono suo del manuale che manca.
        """
        percorso = percorsi.risorsa("manuale.html")
        if not os.path.isfile(percorso):
            self.mostra(f"Il manuale non c'è: dovrebbe essere il file {percorso}. Reinstallare MESS lo rimette al suo posto.", "manuale mancante",
                        "manuale_mancante")
            return
        try:
            os.startfile(percorso)  # noqa: S606 - il manuale si apre col browser che Windows associa all'HTML
        except OSError as errore:
            self.mostra(f"Il manuale non si apre nel browser: {errore.strerror or errore}. È il file {percorso}.", "manuale non aperto", "manuale_mancante")
            return
        suoni.suona("manuale")
        self.ultimo_evento = "manuale nel browser"
        self.aggiorna_barra()

    def caffe(self):
        invito = Donazione(lang="it", probabilita=100, stampa=False) or "Grazie se vorrai offrire un caffè all'autore."
        dialogo = Caffe(self, invito, self.impostazioni)
        try:
            suoni.suona("caffe")
            self._modale(dialogo)
        finally:
            dialogo.Destroy()

    # L'aggiornamento automatico e l'istanza unica, tappa 14, decisione D34: li conducono
    # aggiornamento.py e istanza.py, dai loro fili; qui la finestra e le frasi.

    def proponi_l_aggiornamento(self, versione_attuale, versione_nuova, note, attesa=None):
        """
        La proposta dell'aggiornamento, con le note della release rese leggibili come le novità: vero
        se si sceglie Aggiorna. Allo scadere dell'attesa il dialogo si chiude come Non adesso. Finché è
        aperto il mondo non avanza.
        """
        dialogo = Aggiornamento(self, versione_attuale, versione_nuova, testi.novita(note or ""), attesa, self.impostazioni)
        try:
            # In coda: all'avvio può suonare ancora il motivo di MESS.
            suoni.in_coda("aggiornamento_disponibile")
            scelta = self._modale(dialogo)
            scaduta = dialogo.scaduta
        finally:
            dialogo.Destroy()
        # Aggiorna, Non adesso e la proposta lasciata scadere hanno ciascuno il suo suono.
        if scelta == wx.ID_YES:
            suoni.suona("aggiornamento_scelto")
            self.ultimo_evento = f"scarico MESS {versione_nuova}"
        elif scaduta:
            suoni.suona("aggiornamento_scaduto")
            self.ultimo_evento = "aggiornamento rimandato: tempo scaduto"
        else:
            suoni.suona("annullato")
            self.ultimo_evento = "aggiornamento rimandato"
        self.aggiorna_barra()
        return scelta == wx.ID_YES

    def avvisa_dell_aggiornamento(self, testo):
        """
        Un esito dell'aggiornamento, in un messaggio che aspetta l'OK: torna soltanto quando lo si è
        chiuso, perché i 30 secondi dello script di sostituzione partano dopo, non mentre lo si legge.
        Il suono lo sceglie la frase: l'aggiornamento scaricato, quello non riuscito e il pacchetto
        non ancora pronto hanno ciascuno il suo, e i due esiti cattivi l'icona dell'errore.
        """
        esito = aggiornamento.esito(testo)
        suono = SUONI_DEGLI_ESITI.get(esito, "aggiornamento_esito")
        icona = wx.ICON_ERROR if esito in (aggiornamento.NON_RIUSCITO, aggiornamento.NON_PRONTO) else wx.ICON_INFORMATION
        self._modali += 1
        try:
            suoni.in_coda(suono)
            wx.MessageBox(testo, "Aggiornamento di MESS", wx.OK | icona, self)
        finally:
            self._modali -= 1

    def avanzamento_dell_aggiornamento(self, presi, totale):
        """A che punto è lo scaricamento, nella quarta riga della barra di stato, entro quaranta caratteri; non sotto il cursore di chi legge."""
        if not self or self.chiusa:
            return
        if totale:
            self.ultimo_evento = f"aggiornamento scaricato {testi.con_articolo('al', testi.percento(presi * 100 // totale))}"
        else:
            self.ultimo_evento = f"aggiornamento: {testi.numero(presi / 1048576, 1)} MB scaricati"
        if not self.barra.HasFocus():
            self.aggiorna_barra()

    def chiudi_per_aggiornare(self):
        """
        GBUtils sta per sostituire MESS: la finestra salva il mondo e si chiude senza il riepilogo di
        fine sessione, che aspetterebbe l'OK mentre lo script di sostituzione aspetta al massimo 30
        secondi. Un dialogo aperto si chiude prima: la partita dal vivo e la differita come con Esc,
        che ferma il suono e la cronaca e non svela il risultato, decisione D30; gli altri come
        annullati. Un messaggio aperto, che non si può chiudere da qui, si aspetta, e la chiusura
        riprova finché non è stato letto, ma per LIMITE_DELLA_CHIUSURA secondi al massimo: dopo, lo
        script ha rinunciato, o sta per farlo, e MESS resta aperto, e lo dice appena il messaggio si chiude.
        """
        if not self or self.chiusa:
            return
        if not self._per_aggiornare:
            self._per_aggiornare = True
            self._chiusura_dal = time.monotonic()
        if self._chiudi_i_dialoghi():
            if time.monotonic() - self._chiusura_dal < LIMITE_DELLA_CHIUSURA:
                wx.CallLater(RIPROVA_DELLA_CHIUSURA, self.chiudi_per_aggiornare)
            else:
                self._per_aggiornare = False
                self._chiusura_dal = None
                self._di_che_non_si_e_installato()
            return
        self.Close(force=True)

    def _chiudi_i_dialoghi(self):
        """Chiude i dialoghi modali aperti; vero se ce n'erano, o se resta aperto un messaggio, e la chiusura deve aspettare."""
        aperti = [d for d in wx.GetTopLevelWindows() if isinstance(d, wx.Dialog) and d.IsModal()]
        for dialogo in aperti:
            if isinstance(dialogo, FinestraDalVivo):
                dialogo.esci(CON_ESC)
            else:
                dialogo.EndModal(wx.ID_CANCEL)
        return bool(aperti or self._modali)

    def _di_che_non_si_e_installato(self):
        """L'aggiornamento non si è installato perché un messaggio è rimasto aperto: la vista lo dice quando nessun messaggio e nessun dialogo è più aperto."""
        if not self or self.chiusa:
            return
        if self._modali or any(isinstance(d, wx.Dialog) and d.IsModal() for d in wx.GetTopLevelWindows()):
            wx.CallLater(RIPROVA_DELLA_CHIUSURA, self._di_che_non_si_e_installato)
            return
        self.mostra(NON_INSTALLATO, "aggiornamento non installato", "aggiornamento_non_riuscito")

    def porta_in_primo_piano(self):
        """Si è provato ad aprire MESS una seconda volta: questa finestra torna in primo piano, col suo suono, e l'altra copia si chiude."""
        if not self or self.chiusa:
            return
        if self.IsIconized():
            self.Iconize(False)
        self.Raise()
        suoni.suona("primo_piano")

    # Chiusura.

    def _alla_chiusura(self, event):
        """
        Alla chiusura il mondo si salva, e una finestra riassume la sessione; poi la finestra se ne va.
        Il suono del congedo aspetta di finire, fino a un massimo, prima del riepilogo: dopo, il
        programma si chiude, e lo troncherebbe. Quando si chiude per l'aggiornamento il riepilogo non
        c'è; un salvataggio non riuscito si scrive nel registro degli errori e si dice in un messaggio.
        """
        self.chiusa = True
        self.timer.Stop()
        riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        suoni.suona("uscita" if riuscito else "uscita_senza_salvataggio", sync=suoni.ATTESA_USCITA)
        if self._per_aggiornare:
            if not riuscito:
                perche = " ".join(["Il mondo non si è salvato prima dell'aggiornamento.", *messaggi])
                registro.scrivi(perche)
                wx.MessageBox(f"{perche}\nAlla riapertura ritroverai il mondo dell'ultimo salvataggio riuscito. Con OK MESS si chiude e installa la versione nuova.",
                              "Aggiornamento di MESS", wx.OK | wx.ICON_ERROR, self)
        else:
            riepilogo = testi.chiusura(adesso() - self.inizio, self.comandi, messaggi, self.rapporto_sessione)
            if not riuscito:
                riepilogo += "\nIl mondo non è stato salvato: alla prossima partenza ritroverai quello dell'ultimo salvataggio riuscito."
            dialogo = Lettura(self, "Fine sessione", riepilogo, self.impostazioni)
            with contextlib.suppress(RuntimeError):
                dialogo.ShowModal()
            dialogo.Destroy()
        self.Destroy()
