"""
I dialoghi delle sfide fra polisportive di MESS: il lancio, le sfide in arrivo, la formazione e lo storico.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con il terzo passo della tappa 12, decisione D32, risposte 15 e 16 di Gabriele e
punti 8 e 12.6 del progetto. Una sfida è una gara a squadre IBSA, un set a 31, con due giocatori di un
sesso e uno dell'altro al tavolo e fino a tre riserve; la tua polisportiva ne lancia due al mese, fino
a quattro, e il computer risponde subito; a quelle che ricevi rispondi entro il giorno in cui
arrivano, perché all'avanzamento seguente decadono.
La sezione della formazione è la stessa nel lancio, nelle sfide in arrivo e nella rosa per la Coppa
delle polisportive: Titolare 1, 2 e 3 nell'ordine della rotazione, e Riserva 1, 2 e 3, ciascuno una
scelta fra i convocabili, già riempite con la convocazione automatica, che è soltanto una proposta,
risposta 16. Ogni convocabile si legge con la classe, il sesso e, se c'è, l'acciacco. Sotto, in un
campo che si raggiunge con Tab, lo stato dice se la formazione è valida o perché no; quando smette di
esserlo, mentre la si cambia, lo dice un suono.
Lo storico tiene le sfide delle tue polisportive, e delle ultime dieci giocate fa riascoltare la gara in
differita o leggerne la cronaca.
Ogni dialogo segue lo schema degli altri: pannello che scorre, etichette con la lettera, controlli
nativi a selezione singola, avvisi che lasciano aperto il dialogo col suono del loro perché.
"""

import wx

import impostazioni as modulo_impostazioni
import sfide
import suoni
import testi
from costanti import CONVOCATI_SFIDA, GIOCATORI_AL_TAVOLO
from gui.dialoghi import Lettura, _Dialogo

# Le etichette dei sei posti della formazione: i titolari nell'ordine della rotazione, poi le riserve.
POSTI_DELLA_FORMAZIONE = ("Titolare &1", "Titolare &2", "Titolare &3", "Riserva 1, posto &4", "Riserva 2, posto &5", "Riserva 3, posto &6")
NESSUNO = "nessuno"


class SezioneFormazione:
    """
    La formazione dentro un dialogo: sei scelte, i tre titolari e le tre riserve, fra i convocabili, e
    il campo dello stato. convocabili sono i giocatori fra cui scegliere, proposta gli identificativi già
    scelti, controlla la funzione che dagli identificativi dà il problema della formazione, o None.
    """

    def __init__(self, dialogo, mondo, convocabili, proposta, controlla):
        self.dialogo = dialogo
        self.mondo = mondo
        self.controlla = controlla
        self.convocabili = []
        self.scelte = []
        self._valida = None
        dialogo.etichetta("Formazione: i titolari nell'ordine della rotazione, poi le riserve")
        for etichetta in POSTI_DELLA_FORMAZIONE:
            dialogo.etichetta(etichetta)
            scelta = dialogo.aggiungi(wx.Choice(dialogo.pannello))
            scelta.Bind(wx.EVT_CHOICE, self.al_cambio)
            self.scelte.append(scelta)
        dialogo.etichetta("Stato della formazio&ne")
        self.stato = dialogo.aggiungi(wx.TextCtrl(dialogo.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
        self.riempi(convocabili, proposta)

    def riempi(self, convocabili, proposta):
        """I convocabili nelle sei scelte, con la proposta già scelta; le riserve possono restare vuote."""
        self.convocabili = list(convocabili)
        righe = [testi.riga_convocabile(g, self.mondo) for g in self.convocabili]
        per_id = {g.id: indice for indice, g in enumerate(self.convocabili)}
        proposta = list(proposta)[:CONVOCATI_SFIDA]
        for posto, scelta in enumerate(self.scelte):
            titolare = posto < GIOCATORI_AL_TAVOLO
            scelta.Set(righe if titolare else [NESSUNO, *righe])
            gid = proposta[posto] if posto < len(proposta) else None
            if gid in per_id:
                scelta.SetSelection(per_id[gid] + (0 if titolare else 1))
            elif titolare:
                # Senza proposta i titolari sono i primi convocabili, e il posto resta vuoto se non ce n'è uno per lui.
                scelta.SetSelection(posto if posto < len(righe) else wx.NOT_FOUND)
            else:
                scelta.SetSelection(0)
        self._valida = None
        self.aggiorna_stato(suono=False)

    def ids(self):
        """Gli identificativi scelti, nell'ordine dei posti: i tre titolari, poi le riserve scelte."""
        scelti = []
        for posto, scelta in enumerate(self.scelte):
            indice = scelta.GetSelection()
            if indice == wx.NOT_FOUND:
                continue
            if posto >= GIOCATORI_AL_TAVOLO:
                if indice == 0:
                    continue
                indice -= 1
            if 0 <= indice < len(self.convocabili):
                scelti.append(self.convocabili[indice].id)
        return scelti

    def problema(self):
        """Il perché la formazione non va, o None; con meno di tre convocabili lo dice subito, invece di un doppione o di un posto vuoto."""
        if len(self.convocabili) < GIOCATORI_AL_TAVOLO:
            return testi.convocabili_insufficienti(len(self.convocabili))
        return self.controlla(self.ids())

    def aggiorna_stato(self, suono=True):
        """Riscrive lo stato; quando la formazione smette di essere valida, mentre la si cambia, il suono lo dice."""
        problema = self.problema()
        titolari = [self.mondo.giocatori[gid] for gid in self.ids()[:GIOCATORI_AL_TAVOLO] if gid in self.mondo.giocatori]
        testo = testi.stato_della_formazione(problema, titolari)
        if self.stato.GetValue() != testo:
            self.stato.ChangeValue(testo)
        valida = problema is None
        if suono and self._valida and not valida:
            suoni.suona("formazione_non_valida")
        self._valida = valida

    def al_cambio(self, event=None):
        self.aggiorna_stato()


class FormazioneDialogo(_Dialogo):
    """
    La formazione in un dialogo a sé, con OK e Annulla: la rosa della tua polisportiva per la Coppa
    delle polisportive, fino a sei. In risultato restano gli identificativi scelti.
    """

    def __init__(self, genitore, mondo, titolo, spiegazione, convocabili, proposta, controlla):
        super().__init__(genitore, titolo)
        self.risultato = None
        self.sizer.Add(wx.StaticText(self.pannello, label=spiegazione), 0, wx.ALL, 8)
        self.formazione = SezioneFormazione(self, mondo, convocabili, proposta, controlla)
        ok, _annulla = self.pulsanti((wx.ID_OK, "&OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((560, 560))
        self.formazione.scelte[0].SetFocus()

    def conferma(self, event=None):
        problema = self.formazione.problema()
        if problema:
            self.avvisa(problema, self.formazione.scelte[0], "formazione_non_valida")
            return
        self.risultato = self.formazione.ids()
        self.chiudi(wx.ID_OK)


class LanciaSfida(_Dialogo):
    """
    Il lancio di una sfida dal menu Partite, punto 12.6: la testata con le sfide da lanciare, le
    polisportive del computer con la forza della loro squadra di domani, la gloria e l'ultima sfida, la
    formazione e i pulsanti Lancia, Scheda della polisportiva e Chiudi. Il computer risponde subito,
    e l'esito arriva in un messaggio col suo suono; in esiti restano i messaggi, per la vista.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None):
        super().__init__(genitore, f"Lancia una sfida, {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.esiti = []
        self.memoria = {}
        self.bersagli = []
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Polisportive da sfidare")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        giorno = sfide.giorno_del_gioco(mondo)
        self.formazione = SezioneFormazione(self, mondo, sfide.convocabili(mondo, poli, giorno), sfide.proposta(mondo, poli),
                                            lambda ids: sfide.problema_formazione(mondo, poli, ids, giorno))
        lancia, scheda, _chiudi = self.pulsanti((wx.ID_ANY, "&Lancia"), (wx.ID_ANY, "Sc&heda della polisportiva"), (wx.ID_CANCEL, "&Chiudi"))
        lancia.Bind(wx.EVT_BUTTON, self.lancia)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.aggiorna(0)
        self.completa((640, 640))
        self.elenco.SetFocus()

    def aggiorna(self, posto=None):
        posto = self.elenco.GetSelection() if posto is None else posto
        self.info.SetLabel(testi.testata_del_lancio(self.poli, sfide.disponibili(self.mondo, self.poli)))
        self.bersagli = sfide.bersagli(self.mondo, self.poli, self.memoria)
        self._riscrivi(self.elenco, [testi.riga_bersaglio(b) for b in self.bersagli] or ["Non ci sono polisportive del computer da sfidare."], posto)
        self.pannello.Layout()

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.bersagli):
            return None
        return self.bersagli[indice]

    def _suono_del_problema(self, nome):
        """Il suono di un lancio che non si può fare, nell'ordine in cui lo controlla il mondo."""
        if sfide.disponibili(self.mondo, self.poli) <= 0:
            return "nessuna_sfida_da_lanciare"
        if self.mondo.sfide.rifiutata_oggi(self.poli.nome, nome, self.mondo.datetime_corrente_simulazione.date()):
            return "sfida_rifiutata_dall_avversario"
        return "formazione_non_valida"

    def lancia(self, event=None):
        bersaglio = self._scelto()
        if bersaglio is None:
            suoni.suona("nessuna_selezione")
            return
        ids = self.formazione.ids()
        problema = sfide.problema_lancio(self.mondo, self.poli, bersaglio["nome"], ids)
        if problema:
            perche = self._suono_del_problema(bersaglio["nome"])
            if perche == "formazione_non_valida":
                problema = self.formazione.problema() or problema
            self.avvisa(problema, self.elenco if perche != "formazione_non_valida" else self.formazione.scelte[0], perche)
            return
        cognomi = testi.unisci([self.mondo.giocatori[gid].cognome for gid in ids[:GIOCATORI_AL_TAVOLO]])
        if not self._conferma(f"Lanciare la sfida a {bersaglio['nome']}, con {cognomi}? Se accetta, si gioca domani."):
            self.elenco.SetFocus()
            return
        s, messaggio = sfide.lancia(self.mondo, self.poli, bersaglio["nome"], ids)
        self.esiti.append(messaggio)
        suoni.suona("sfida_accettata_dall_avversario" if s.stato == sfide.ACCETTATA else "sfida_rifiutata_dall_avversario")
        wx.MessageBox(messaggio, self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna()
        self.formazione.riempi(sfide.convocabili(self.mondo, self.poli, sfide.giorno_del_gioco(self.mondo)), sfide.proposta(self.mondo, self.poli))
        self.elenco.SetFocus()

    def scheda(self, event=None):
        bersaglio = self._scelto()
        p = self.mondo.polisportive.get(bersaglio["nome"]) if bersaglio else None
        if p is None:
            suoni.suona("nessuna_selezione")
            return
        dialogo = Lettura(self, f"Scheda di {p.nome}", testi.scheda_polisportiva(p, self.mondo), self.impostazioni)
        try:
            suoni.suona("scheda_polisportiva")
            dialogo.ShowModal()
        finally:
            dialogo.Destroy()


class SfideInArrivo(_Dialogo):
    """
    Le sfide che aspettano la risposta della polisportiva attiva, punto 12.6: chi sfida, la forza della
    sua squadra e la scadenza; la formazione, proposta per il giorno del gioco e da cambiare se vuoi; i
    pulsanti Accetta, Rifiuta e Chiudi. In esiti restano i messaggi, per la vista.
    """

    def __init__(self, genitore, mondo, poli):
        super().__init__(genitore, f"Sfide in arrivo, {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.esiti = []
        self.proposte = []
        self.memoria = {}
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Sfide in arrivo")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        giorno = sfide.giorno_del_gioco(mondo)
        self.formazione = SezioneFormazione(self, mondo, sfide.convocabili(mondo, poli, giorno), sfide.proposta(mondo, poli), self._problema_della_formazione)
        accetta, rifiuta, _chiudi = self.pulsanti((wx.ID_ANY, "&Accetta"), (wx.ID_ANY, "&Rifiuta"), (wx.ID_CANCEL, "&Chiudi"))
        accetta.Bind(wx.EVT_BUTTON, self.accetta)
        rifiuta.Bind(wx.EVT_BUTTON, self.rifiuta)
        self.aggiorna(0)
        self.completa((640, 620))
        self.elenco.SetFocus()

    def _forza(self, s):
        giocatori = [self.mondo.giocatori[gid] for gid in s.convocati["sfidante"] if gid in self.mondo.giocatori]
        return sfide.forza_squadra(giocatori, self.memoria) if len(giocatori) >= GIOCATORI_AL_TAVOLO else None

    def aggiorna(self, posto=None):
        posto = self.elenco.GetSelection() if posto is None else posto
        self.proposte = sfide.in_arrivo(self.mondo, self.poli)
        self.info.SetLabel(f"{self.poli.nome}: {testi.conta(len(self.proposte), 'sfida aspetta', 'sfide aspettano')} la tua risposta. "
                           "Accettata, si gioca domani; senza risposta decade all'avanzamento di domani.")
        self._riscrivi(self.elenco, [testi.riga_sfida_in_arrivo(s, self._forza(s)) for s in self.proposte] or ["Nessuna sfida aspetta la tua risposta."], posto)
        self.pannello.Layout()

    def _scelta(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.proposte):
            return None
        return self.proposte[indice]

    def _problema_della_formazione(self, ids):
        s = self._scelta() if hasattr(self, "proposte") and hasattr(self, "elenco") else None
        if s is None:
            return sfide.problema_formazione(self.mondo, self.poli, ids, sfide.giorno_del_gioco(self.mondo))
        return sfide.problema_risposta(self.mondo, s.id, self.poli, ids)

    def accetta(self, event=None):
        s = self._scelta()
        if s is None:
            suoni.suona("nessuna_selezione")
            return
        ids = self.formazione.ids()
        problema = sfide.problema_risposta(self.mondo, s.id, self.poli, ids)
        if problema:
            self.avvisa(self.formazione.problema() or problema, self.formazione.scelte[0], "formazione_non_valida")
            return
        cognomi = testi.unisci([self.mondo.giocatori[gid].cognome for gid in ids[:GIOCATORI_AL_TAVOLO]])
        if not self._conferma(f"Accettare la sfida di {s.sfidante['nome']}, con {cognomi}? Si gioca domani."):
            self.elenco.SetFocus()
            return
        messaggio = sfide.accetta(self.mondo, s.id, self.poli, ids)
        self._dopo(messaggio, "sfida_accettata")

    def rifiuta(self, event=None):
        s = self._scelta()
        if s is None:
            suoni.suona("nessuna_selezione")
            return
        problema = sfide.problema_risposta(self.mondo, s.id, self.poli)
        if problema:
            self.avvisa(problema, self.elenco)
            return
        if not self._conferma(f"Rifiutare la sfida di {s.sfidante['nome']}? Non costa niente a nessuno."):
            self.elenco.SetFocus()
            return
        self._dopo(sfide.rifiuta(self.mondo, s.id, self.poli), "sfida_rifiutata")

    def _dopo(self, messaggio, suono):
        self.esiti.append(messaggio)
        suoni.suona(suono)
        wx.MessageBox(messaggio, self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.aggiorna()
        self.formazione.riempi(sfide.convocabili(self.mondo, self.poli, sfide.giorno_del_gioco(self.mondo)), sfide.proposta(self.mondo, self.poli))
        self.elenco.SetFocus()


class StoricoSfide(_Dialogo):
    """
    Lo storico delle sfide delle tue polisportive, dalla più recente, punto 12.1: per le ultime dieci
    giocate, Ascolta in differita e Leggi la cronaca, che la finestra dal vivo e la lettura condividono
    col pannello dei tornei. In ultimo resta l'ultimo incontro ascoltato o letto, per Salva la cronaca, e
    in velocita la velocità di gioco a cui si è arrivati ascoltando.
    """

    def __init__(self, genitore, mondo, impostazioni=None):
        super().__init__(genitore, "Storico delle sfide")
        self.mondo = mondo
        self.impostazioni = modulo_impostazioni.valide(impostazioni)
        self.ultimo = None
        self.velocita = self.impostazioni.get("velocita_gioco")
        self.voci = list(reversed(mondo.sfide.storico))
        self.etichetta("&Sfide delle tue polisportive, dalla più recente")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE, choices=[testi.riga_dello_storico(s, mondo) for s in self.voci]
                                               or ["Le tue polisportive non hanno ancora sfide nello storico."]), 1)
        ascolta, leggi, _chiudi = self.pulsanti((wx.ID_ANY, "&Ascolta in differita"), (wx.ID_ANY, "&Leggi la cronaca"), (wx.ID_CANCEL, "&Chiudi"))
        ascolta.Bind(wx.EVT_BUTTON, self.ascolta)
        leggi.Bind(wx.EVT_BUTTON, self.leggi)
        self.elenco.Bind(wx.EVT_LISTBOX_DCLICK, self.ascolta)
        if self.voci:
            self.elenco.SetSelection(0)
        self.completa((640, 460))
        self.elenco.SetFocus()

    def _con_differita(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.voci):
            suoni.suona("nessuna_selezione")
            return None
        s = self.voci[indice]
        if not s.differita:
            self.avvisa("Questa sfida non si può riascoltare: si riascoltano soltanto le ultime dieci giocate.", self.elenco, "nessuna_differita")
            return None
        return s

    def _tuoi(self):
        return {p.nome for p in self.mondo.polisportive.values() if not p.is_cpu_controlled}

    def ascolta(self, event=None):
        from gui import tornei as gui_tornei

        s = self._con_differita()
        if s is None:
            return
        self.ultimo, self.velocita = gui_tornei.ascolta_e_ricorda(self, self.mondo, s.differita, s.seme, self.impostazioni, self._tuoi(),
                                                                 s.data_gioco, "sfida", self.velocita)
        self.elenco.SetFocus()

    def leggi(self, event=None):
        from gui import tornei as gui_tornei

        s = self._con_differita()
        if s is None:
            return
        self.ultimo = gui_tornei.leggi_e_ricorda(self, self.mondo, s.differita, s.seme, self.impostazioni, s.data_gioco, "sfida")
        self.elenco.SetFocus()
