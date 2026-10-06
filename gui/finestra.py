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
"""

import contextlib

import wx
from GBUtils import Donazione
from GBwx import dentro_area_utile

import archivio
import impostazioni as modulo_impostazioni
import percorsi
import ricerca
import testi
from gui import aspetto
from gui.dialoghi import Aspetto, Caffe, Conservazione, Lettura, Ricerca, SceltaGiocatore
from utilita import adesso, adesso_utc

TITOLO = "MESS, Manageriale e Simulatore Showdown"
RIGHE_BARRA = 4


class FinestraPrincipale(wx.Frame):
    def __init__(self, mondo, origine, messaggi, rapporto, ultimo_prima):
        super().__init__(None, title=TITOLO)
        self.mondo = mondo
        self.rapporto = rapporto
        self.rapporto_sessione = rapporto
        self._modali = 0
        self.impostazioni = modulo_impostazioni.carica()
        self.inizio = adesso()
        self.comandi = 0
        self.ultimo_evento = "mondo pronto"
        self.ultima_ricerca = None
        self._testo_barra = None
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
                ("&Elenco dei giocatori", "Ctrl+E", lambda: self.mostra(testi.elenco_giocatori(self.mondo), "elenco dei giocatori")),
                ("&Classifica per valore", "Ctrl+L", lambda: self.mostra(testi.classifica(self.mondo), "classifica per valore")),
                ("&TOP 10", "Ctrl+T", lambda: self.mostra(testi.top_10(self.mondo), "TOP 10")),
                ("St&atistiche del mondo", "Ctrl+I", lambda: self.mostra(testi.statistiche(self.mondo), "statistiche del mondo")),
                None,
                ("Ce&rca giocatori...", "Ctrl+F", self.cerca),
                ("R&isultati della ricerca", "Ctrl+R", self.risultati),
                None,
                ("&Nuovi arrivati della sessione", "Ctrl+Shift+N", lambda: self.mostra(testi.lista_nuovi(self.mondo), "nuovi arrivati")),
                ("Ritirati della sessi&one", "Ctrl+Shift+R", lambda: self.mostra(testi.lista_ritirati(self.mondo), "ritirati della sessione")),
                ("&Usciti di scena nella sessione", "Ctrl+Shift+U", lambda: self.mostra(testi.lista_usciti(self.mondo), "usciti di scena")),
            )),
            ("&Polisportive", (
                ("&Scheda della polisportiva attiva", "Ctrl+M", self.scheda_polisportiva),
                ("&Tesserati della polisportiva attiva", "Ctrl+Shift+T", lambda: self.mostra(testi.tesserati_attiva(self.mondo), "tesserati")),
                ("&Elenco delle polisportive", "Ctrl+Shift+E", lambda: self.mostra(testi.elenco_polisportive(self.mondo), "elenco delle polisportive")),
                ("&Diario della polisportiva attiva", "Ctrl+Shift+M", self.diario_polisportiva),
            )),
            ("&Mondo", (
                ("&Data e prossimo avanzamento", "Ctrl+D", lambda: self.mostra(testi.data_e_avanzamento(self.mondo, adesso_utc()), "data simulata")),
                ("&Riepilogo dell'ultimo avanzamento", "Ctrl+Shift+A", lambda: self.mostra(testi.riepilogo_avanzamento(self.rapporto), "ultimo avanzamento")),
                ("&Vecchie glorie", "Ctrl+Shift+V", lambda: self.mostra(testi.vecchie_glorie(self.mondo), "vecchie glorie")),
            )),
            ("&Visualizza", (("Vista &principale", "F5", self.vai_alla_vista), ("&Barra di stato", "F7", self.vai_alla_barra))),
            ("&Impostazioni", (("&Aspetto, colori e caratteri...", "Ctrl+P", self.cambia_aspetto), ("&Conservazione dei diari...", None, self.cambia_conservazione))),
            ("&Aiuto", (
                ("&Guida ai comandi", "F1", lambda: self.mostra(testi.guida(self.voci_guida()), "guida ai comandi")),
                ("&Novità", "F2", self.novita),
                ("&Informazioni", "F3", lambda: self.mostra(testi.informazioni(), "informazioni")),
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

    # Mostrare.

    def _esegui(self, comando):
        self.comandi += 1
        comando()

    def mostra(self, testo, evento=None):
        """Mette il testo nella vista principale, al posto di quello di prima, con il cursore all'inizio."""
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

    def avanza(self):
        """Fa avanzare il mondo dei giorni maturati, salva e lo annuncia nella barra di stato."""
        rapporto = self.mondo.processa_tempo_trascorso()
        if not rapporto["ticks"]:
            return
        self.rapporto = rapporto
        self.rapporto_sessione = testi.somma_rapporti(self.rapporto_sessione, rapporto) if self.rapporto_sessione else rapporto
        salvato, _messaggi = self._salva_raccogliendo()
        giorni = "di un giorno" if rapporto["giorni"] == 1 else f"di {rapporto['giorni']} giorni"
        self.ultimo_evento = f"mondo avanzato {giorni}" + ("" if salvato else ", non salvato")

    def _modale(self, dialogo):
        """Mostra un dialogo modale; finché resta aperto, il mondo non avanza."""
        self._modali += 1
        try:
            return dialogo.ShowModal()
        finally:
            self._modali -= 1

    def vai_alla_vista(self):
        self.vista.SetFocus()

    def vai_alla_barra(self):
        if self.barra.HasFocus():
            self.aggiorna_barra()
        self.barra.SetFocus()

    # Comandi.

    def _salva_raccogliendo(self):
        """Salva il mondo e restituisce l'esito e i messaggi dell'archivio."""
        messaggi = []
        notifica = self.mondo.notifica
        self.mondo.notifica = messaggi.append
        try:
            riuscito = archivio.salva(self.mondo)
        finally:
            self.mondo.notifica = notifica
        return riuscito, messaggi

    def salva(self):
        riuscito, messaggi = self._salva_raccogliendo()
        self.mostra("\n".join(messaggi), f"salvato alle {adesso():%H:%M}" if riuscito else "salvataggio non riuscito")

    def esci(self):
        self.Close()

    def _scegli_giocatore(self, titolo, pulsante):
        """Il giocatore scelto nel dialogo, oppure None se il dialogo è stato annullato."""
        dialogo = SceltaGiocatore(self, self.mondo, titolo, pulsante)
        try:
            if self._modale(dialogo) == wx.ID_OK:
                return dialogo.scelto
            return None
        finally:
            dialogo.Destroy()

    def scheda_giocatore(self):
        g = self._scegli_giocatore("Scheda del giocatore", "&Mostra la scheda")
        if g is not None:
            self.mostra(testi.scheda_giocatore(g, self.mondo), f"scheda di {testi.nome_completo(g)}")

    def diario_giocatore(self):
        g = self._scegli_giocatore("Diario del giocatore", "&Mostra il diario")
        if g is not None:
            self.mostra(testi.diario_giocatore(g), f"diario di {testi.nome_completo(g)}")

    def diario_polisportiva(self):
        p = self.mondo.miapolisportiva_attiva
        if p is None:
            self.mostra("Non hai una polisportiva attiva.", "nessuna polisportiva")
            return
        self.mostra(testi.diario_polisportiva(p), f"diario di {p.nome}")

    def cambia_conservazione(self):
        dialogo = Conservazione(self, self.mondo.conservazione_diari)
        try:
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.mondo.conservazione_diari = dialogo.risultato
                self.mostra(testi.conservazione(self.mondo) + " Le voci più vecchie si tolgono a ogni salvataggio.", "conservazione dei diari")
        finally:
            dialogo.Destroy()

    def cerca(self):
        dialogo = Ricerca(self)
        try:
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                ambito, criterio, condizione, valore, descrizione = dialogo.risultato
                ids = ricerca.cerca(self.mondo, ambito, criterio, condizione, valore)
                self.mondo.risultati_ultima_ricerca = ids
                self.ultima_ricerca = descrizione
                self.mostra(testi.risultati_ricerca(self.mondo, descrizione, ids), f"trovati {len(ids)}")
        finally:
            dialogo.Destroy()

    def risultati(self):
        if self.ultima_ricerca is None:
            self.mostra("In questa sessione non hai ancora fatto ricerche: si cercano con Ctrl+F.", "nessuna ricerca")
            return
        self.mostra(testi.risultati_ricerca(self.mondo, self.ultima_ricerca, self.mondo.risultati_ultima_ricerca), "risultati della ricerca")

    def scheda_polisportiva(self):
        p = self.mondo.miapolisportiva_attiva
        if p is None:
            self.mostra("Non hai una polisportiva attiva.", "nessuna polisportiva")
            return
        self.mostra(testi.scheda_polisportiva(p, self.mondo), f"scheda di {p.nome}")

    def cambia_aspetto(self):
        dialogo = Aspetto(self, self.impostazioni)
        try:
            if self._modale(dialogo) == wx.ID_OK and dialogo.risultato is not None:
                self.impostazioni = dialogo.risultato
                salvate = modulo_impostazioni.salva(self.impostazioni)
                self.applica_aspetto()
                self.ultimo_evento = "aspetto aggiornato" if salvate else "aspetto non salvato"
                self._testo_barra = None
                self.aggiorna_barra()
        finally:
            dialogo.Destroy()

    def novita(self):
        try:
            with open(percorsi.risorsa("CHANGELOG.md"), encoding="utf-8") as f:
                testo = testi.novita(f.read())
        except OSError as e:
            testo = f"Il file delle novità non si può leggere: {e}."
        self.mostra(testo, "novità")

    def caffe(self):
        invito = Donazione(lang="it", probabilita=100, stampa=False) or "Grazie se vorrai offrire un caffè all'autore."
        dialogo = Caffe(self, invito, self.impostazioni)
        try:
            self._modale(dialogo)
        finally:
            dialogo.Destroy()

    # Chiusura.

    def _alla_chiusura(self, event):
        """Alla chiusura il mondo si salva, e una finestra riassume la sessione; poi la finestra se ne va."""
        self.timer.Stop()
        riuscito, messaggi = self._salva_raccogliendo()
        riepilogo = testi.chiusura(adesso() - self.inizio, self.comandi, messaggi, self.rapporto_sessione)
        if not riuscito:
            riepilogo += "\nIl mondo non è stato salvato: alla prossima partenza ritroverai quello dell'ultimo salvataggio riuscito."
        dialogo = Lettura(self, "Fine sessione", riepilogo, self.impostazioni)
        with contextlib.suppress(RuntimeError):
            dialogo.ShowModal()
        dialogo.Destroy()
        self.Destroy()
