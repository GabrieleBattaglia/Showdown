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
"""

import contextlib

import wx
from GBUtils import Donazione
from GBwx import dentro_area_utile

import archivio
import impostazioni as modulo_impostazioni
import percorsi
import ricerca
import suoni
import testi
from gui import aspetto
from gui.dal_vivo import ALLA_FINE, CON_ESC, FinestraDalVivo
from gui.dialoghi import (
    ASSISTI,
    Aspetto,
    Caffe,
    CambiaPolisportiva,
    ChiediPassword,
    Conservazione,
    EffettiSonori,
    Lettura,
    Mercato,
    NuovaPolisportiva,
    OpzioniAmichevole,
    PagaArretrati,
    PasswordPolisportiva,
    Ricerca,
    SceltaGiocatore,
    VelocitaDiGioco,
    Vendite,
)
from partita import MotorePartita
from utilita import adesso, adesso_utc

TITOLO = "MESS, Manageriale e Simulatore Showdown"
RIGHE_BARRA = 4


class UltimaAmichevole:
    """
    L'ultima amichevole della sessione, già giocata e registrata: il risultato, i nomi della cronaca,
    il livello scelto, che vale anche per il file, il suono dell'esito e le parole dell'esito per la
    barra di stato. Ricorda anche quando si è giocata, l'istante reale e il giorno simulato: la
    cronaca si salva più tardi, magari dopo un avanzamento del mondo, e il file deve dire il momento
    dell'incontro, lo stesso dei diari dei due giocatori.
    """

    def __init__(self, risultato, nomi, livello, esito, istante, data_simulata):
        self.risultato = risultato
        self.nomi = nomi
        self.livello = livello
        self.esito = esito
        self.istante = istante
        self.data_simulata = data_simulata
        vince = risultato.vincitore
        sa, sb = risultato.set_vinti
        mio, suo = (sa, sb) if vince == "A" else (sb, sa)
        self.evento_esito = f"vince {nomi[vince].testo}, {mio} set a {suo}"


class FinestraPrincipale(wx.Frame):
    def __init__(self, mondo, origine, messaggi, rapporto, ultimo_prima, avvisi_all_avvio=False):
        super().__init__(None, title=TITOLO)
        self.mondo = mondo
        self.origine = origine
        self.avvisi_all_avvio = avvisi_all_avvio
        self.rapporto = rapporto
        self.rapporto_sessione = rapporto
        self._modali = 0
        self.impostazioni = modulo_impostazioni.carica()
        suoni.imposta_volume(self.impostazioni["volume_effetti"])
        self.inizio = adesso()
        self.comandi = 0
        self.ultimo_evento = "mondo pronto"
        # Il mondo nato adesso avanza subito di un giorno, che non va annunciato: è appena nato.
        self.avanzamento_all_avvio = None
        if origine != archivio.NATO:
            evento, testo = suoni.evento_avanzamento(rapporto, True, self._ha_polisportive())
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
        self.mostra(testi.apertura(mondo, origine, messaggi, rapporto, ultimo_prima, adesso_utc()))

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
                ("St&atistiche del mondo", "Ctrl+I", lambda: self.mostra(testi.statistiche(self.mondo), "statistiche del mondo", "statistiche_mondo")),
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
                ("&Salva la cronaca", "Ctrl+Shift+O", self.salva_cronaca),
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
            )),
            ("&Aiuto", (
                ("&Guida ai comandi", "F1", lambda: self.mostra(testi.guida(self.voci_guida()), "guida ai comandi", "guida")),
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
        suono dell'avanzamento, quando il primo è finito.
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
        if self.avanzamento_all_avvio:
            suoni.in_coda(self.avanzamento_all_avvio)

    def errore_imprevisto(self, tipo, valore):
        """
        Un'eccezione sfuggita a un comando: la traccia va sulla console, che chi non vede non legge,
        e il comando muore in silenzio. Qui la dicono il suono dell'allarme e un messaggio.
        """
        if not self or self.IsBeingDeleted() or self._errore_aperto:
            return
        self._errore_aperto = True
        self._modali += 1
        try:
            suoni.suona("errore_imprevisto")
            wx.MessageBox(f"Il comando si è interrotto per un errore imprevisto: {tipo.__name__}, {valore}. La traccia completa è sulla console.",
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
        evento, self.ultimo_evento = suoni.evento_avanzamento(rapporto, salvato, self._ha_polisportive())
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
            nome, password, attiva = dialogo.risultato
        finally:
            dialogo.Destroy()
        p = self.mondo.fonda_polisportiva(nome, password, attiva)
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
        domanda = f"Svincolare {testi.nome_completo(g)}? Tornerà {testi.accorda(g, 'libero')}, e userai una delle {self.mondo.mosse_rimaste(p)} mosse che ti restano oggi."
        if self._domanda(domanda, "Svincolo") != wx.YES:
            return
        self.mondo.svincola(p, g)
        self._concludi(testi.svincolato(g, p, self.mondo), f"svincolato {testi.nome_completo(g)}", "tesserato_svincolato")

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
        self.incontro = v = UltimaAmichevole(risultato, motore.nomi(risultato), livello, esito, istante, data_simulata)
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
        La cronaca dell'ultima amichevole nel suo file, nella cartella delle cronache, al livello
        scelto nelle opzioni; intestazione e nome del file dicono quando si è giocata, non quando si salva.
        """
        v = self.incontro
        if v is None:
            self.mostra(testi.NESSUNA_AMICHEVOLE, "nessuna amichevole", "nessun_incontro")
            return
        try:
            percorso = MotorePartita(self.mondo).salva_cronaca(v.risultato, v.livello, istante=v.istante, data_simulata=v.data_simulata)
        except OSError as errore:
            self.mostra(testi.cronaca_non_salvata(errore), "cronaca non salvata", "cronaca_non_salvata")
            return
        self.mostra(testi.cronaca_salvata(percorso, v.livello, v.nomi), "cronaca salvata", "cronaca_salvata")

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

    def novita(self):
        try:
            with open(percorsi.risorsa("CHANGELOG.md"), encoding="utf-8") as f:
                testo = testi.novita(f.read())
            suono = "novita"
        except OSError as e:
            testo = f"Il file delle novità non si può leggere: {e}."
            suono = "novita_illeggibile"
        self.mostra(testo, "novità", suono)

    def caffe(self):
        invito = Donazione(lang="it", probabilita=100, stampa=False) or "Grazie se vorrai offrire un caffè all'autore."
        dialogo = Caffe(self, invito, self.impostazioni)
        try:
            suoni.suona("caffe")
            self._modale(dialogo)
        finally:
            dialogo.Destroy()

    # Chiusura.

    def _alla_chiusura(self, event):
        """
        Alla chiusura il mondo si salva, e una finestra riassume la sessione; poi la finestra se ne va.
        Il suono del congedo aspetta di finire, fino a un massimo, prima del riepilogo: dopo, il
        programma si chiude, e lo troncherebbe.
        """
        self.timer.Stop()
        riuscito, messaggi, _avvisi = self._salva_raccogliendo()
        riepilogo = testi.chiusura(adesso() - self.inizio, self.comandi, messaggi, self.rapporto_sessione)
        if not riuscito:
            riepilogo += "\nIl mondo non è stato salvato: alla prossima partenza ritroverai quello dell'ultimo salvataggio riuscito."
        suoni.suona("uscita" if riuscito else "uscita_senza_salvataggio", sync=suoni.ATTESA_USCITA)
        dialogo = Lettura(self, "Fine sessione", riepilogo, self.impostazioni)
        with contextlib.suppress(RuntimeError):
            dialogo.ShowModal()
        dialogo.Destroy()
        self.Destroy()
