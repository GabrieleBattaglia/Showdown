"""
I dialoghi dei tornei di MESS: il calendario con le iscrizioni, il pannello dei tornei e l'albo d'oro.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con il terzo passo della tappa 12, decisioni D9, D13 e D32, risposte 2, 13 e 18 di
Gabriele e punti 12.1, 12.2 e 12.3 del progetto. Il pannello prende il posto della dashboard dei
tornei di Terminal Beast, TournamentDashboardDialog, ma senza Notebook e senza misure in pixel: soltanto
controlli nativi a selezione singola, ciascuno con la sua etichetta, come la sala allenamento. Il
calendario prende le due liste di TournamentParticipationDialog, gli iscrivibili e gli iscritti.
Il calendario: le edizioni aperte, quelle dei prossimi trenta giorni secondo la ricorrenza dei modelli
e quelle in corso; per l'edizione scelta, i tuoi tesserati della polisportiva attiva da iscrivere e
quelli iscritti, ciascuno con il suo stato e la data dell'iscrizione automatica, perché a mano decidi
tu, risposta 2: la regola dei due mesi a mano non c'è. Si iscrive e si toglie soltanto coi pulsanti,
mai con Invio o spazio sugli elenchi, e una seconda pressione dello stesso pulsante entro mezzo secondo
si ignora: NVDA manda le ripetizioni di un tasto tenuto giù come pressioni nuove, e un tasto tenuto
pagherebbe più iscrizioni. Ogni iscrizione paga e ogni ritiro rimborsa subito, col suo suono; i rifiuti
arrivano con un avviso, ciascuno col suono del suo perché. Per la Coppa delle polisportive, a cui la tua
è qualificata, Iscrivi diventa Rosa per la coppa, che apre la formazione con sei posti.
Il pannello: i tornei in corso e quelli conclusi da meno di due settimane, con i tuoi atleti o tutti;
per il torneo scelto le parti, cioè la classifica generale, i tuoi incontri, i gironi e il tabellone; la
classifica della parte e i suoi incontri. Un incontro dei tuoi non ancora ascoltato, letto o mostrato
dice soltanto che è da ascoltare, risposta 18: Ascolta in differita lo fa sentire nella finestra dal
vivo, Invio sull'incontro fa lo stesso, Leggi la cronaca lo mostra da leggere, Mostra il risultato lo
svela; Mostra tutti i risultati, la regola che Gabriele ha aggiunto, svela in un colpo solo tutti gli
incontri dei tuoi da ascoltare, dopo una domanda col no già scelto, perché non si torna indietro. Esc
prima della fine dell'ascolto non svela niente. Le classifiche dicono comunque chi va avanti.
L'albo d'oro conserva ogni podio per sempre, risposta 13: ci si arriva per modello e per anno, e per
ogni edizione si leggono i podi delle sue sedi, tutte o soltanto quelle con i tuoi.
La revisione del 14 ottobre 2026 ha tolto il pulsante predefinito dai tre dialoghi: nel calendario Invio
su un elenco iscriveva e pagava, nel pannello ascoltava da qualunque elenco l'incontro scelto negli
Incontri, nell'albo chiudeva. Ora Invio ascolta soltanto sull'elenco degli incontri, e altrove non fa
niente. Mostra del pannello ha una voce in più, le ultime edizioni concluse con i tuoi, dalle
differite del calendario: D32 vuole riascoltabile l'ultimo concluso anche dopo le due settimane, e lì
restano i tuoi incontri, col podio della sede preso dall'albo. Esc durante l'ascolto ha il suo suono,
differita_interrotta, come vuole D30.
"""

import datetime
import time

import wx

import impostazioni as modulo_impostazioni
import iscrizioni
import modelli_torneo
import sfide
import suoni
import testi
import tornei
from calendario import SedeInDifferita
from gui import sfide as gui_sfide
from gui.dal_vivo import ALLA_FINE, CON_ESC, ascolta_in_differita
from gui.dialoghi import Lettura, _Dialogo
from partita import risultato_della_differita
from utilita import adesso

# Due pressioni dello stesso pulsante più vicine di così sono un tasto tenuto giù: la seconda si ignora.
RIPETIZIONE_IGNORATA = 0.5
# I giorni del calendario che guarda avanti, oltre alle edizioni aperte.
GIORNI_AVANTI = 30
APERTE, PROSSIME, IN_CORSO = "aperte", "prossime", "in_corso"
SCELTE_DEL_CALENDARIO = ((APERTE, "Edizioni aperte alle iscrizioni"), (PROSSIME, "Edizioni dei prossimi 30 giorni"), (IN_CORSO, "Edizioni in corso"))
CON_I_TUOI, TUTTI_IN_CORSO, CONCLUSI_TUOI, TUTTI_CONCLUSI, DIFFERITE = "tuoi", "in_corso", "conclusi_tuoi", "conclusi", "differite"
# L'ultima voce, dalla revisione del 14 ottobre 2026: D32 vuole da riascoltare l'ultimo concluso anche
# dopo le due settimane in cui le sedi concluse restano nel pannello.
SCELTE_DEL_PANNELLO = ((CON_I_TUOI, "Tornei con i tuoi atleti"), (TUTTI_IN_CORSO, "Tutti i tornei in corso"),
                       (CONCLUSI_TUOI, "Conclusi di recente con i tuoi"), (TUTTI_CONCLUSI, "Tutti i conclusi di recente"),
                       (DIFFERITE, "Ultime edizioni concluse con i tuoi, da riascoltare"))
TUTTE_LE_SEDI, SEDI_CON_I_TUOI = "tutte", "tuoi"
SCELTE_DELL_ALBO = ((TUTTE_LE_SEDI, "Tutte le sedi"), (SEDI_CON_I_TUOI, "Soltanto le sedi con i tuoi sul podio"))


class UltimoIncontro:
    """
    L'ultimo incontro mostrato o ascoltato nella sessione, per Salva la cronaca: un'amichevole, un
    incontro di torneo o una sfida. Il risultato è giocato tutto, coi momenti; nomi, livello, il suono
    dell'esito, quando si è giocato, l'istante reale e il giorno simulato, e il tipo, per le frasi.
    """

    def __init__(self, risultato, nomi, livello, esito, istante, data_simulata, tipo="amichevole"):
        self.risultato = risultato
        self.nomi = nomi
        self.livello = livello
        self.esito = esito
        self.istante = istante
        self.data_simulata = data_simulata
        self.tipo = tipo
        vince = risultato.vincitore
        sa, sb = risultato.set_vinti
        mio, suo = (sa, sb) if vince == "A" else (sb, sa)
        self.evento_esito = f"vince {nomi[vince].testo}, {mio} set a {suo}"


def _data_del_gioco(data):
    """Il giorno simulato di un incontro in differita, come data con l'ora, per la cronaca."""
    if data is None:
        return None
    if isinstance(data, str):
        data = datetime.date.fromisoformat(data[:10])
    if isinstance(data, datetime.datetime):
        return data
    return datetime.datetime.combine(data, datetime.time(9, 0))


def ascolta_e_ricorda(genitore, mondo, differita, seme, impostazioni, tuoi, data, tipo, velocita=None):
    """
    L'ascolto in differita di un incontro dei tuoi, condiviso dal pannello dei tornei e dallo storico
    delle sfide: restituisce l'ultimo incontro per Salva la cronaca, o None se si è usciti con Esc
    prima della fine, e la velocità di gioco a cui si è arrivati.
    """
    valide = dict(impostazioni)
    if velocita is not None:
        valide["velocita_gioco"] = velocita
    uscita, velocita = ascolta_in_differita(genitore, differita, seme, valide, tuoi)
    if uscita == CON_ESC:
        # D30: l'uscita con Esc ha un suono suo, che non svela il risultato, e non quello di ogni Annulla.
        suoni.suona("differita_interrotta")
        return None, velocita
    if uscita == ALLA_FINE:
        suoni.suona("resto_dell_incontro")
        suoni.in_coda("risultato_svelato")
    else:
        suoni.suona("risultato_svelato")
    risultato, nomi = risultato_della_differita(differita, seme)
    return UltimoIncontro(risultato, nomi, valide.get("amichevole_livello", "normale"), None, adesso(), _data_del_gioco(data), tipo), velocita


def leggi_e_ricorda(genitore, mondo, differita, seme, impostazioni, data, tipo):
    """La cronaca di un incontro dei tuoi da leggere, nel dialogo della lettura; restituisce l'ultimo incontro per Salva la cronaca."""
    livello = impostazioni.get("amichevole_livello", "normale")
    risultato, nomi = risultato_della_differita(differita, seme)
    testo = "\n".join([f"Cronaca di {nomi['A'].testo} contro {nomi['B'].testo}.", testi.cronaca_amichevole(risultato, nomi, livello)])
    dialogo = Lettura(genitore, f"Cronaca di {nomi['A'].testo} contro {nomi['B'].testo}", testo, impostazioni)
    try:
        suoni.suona("cronaca_torneo_letta")
        dialogo.ShowModal()
    finally:
        dialogo.Destroy()
    return UltimoIncontro(risultato, nomi, livello, None, adesso(), _data_del_gioco(data), tipo)


def tuoi_del_mondo(mondo):
    """I tuoi: gli identificativi dei tesserati e i nomi delle polisportive dell'utente, per riconoscerli nei tornei e nelle sfide."""
    mie = [p for p in mondo.polisportive.values() if not p.is_cpu_controlled]
    return {gid for p in mie for gid in p.tesserati} | {p.nome for p in mie}


def tuoi_nel_torneo(mondo, torneo, tuoi=None):
    """Gli iscritti di una sede che sono tuoi: tesserati di adesso o iscritti col club di una tua polisportiva; nella coppa, le tue polisportive."""
    tuoi = tuoi_del_mondo(mondo) if tuoi is None else tuoi
    scelti = set()
    for gid in torneo.iscritti:
        poli = iscrizioni.polisportiva_del_club(mondo, torneo.info[gid].get("club"))
        if gid in tuoi or (poli is not None and not poli.is_cpu_controlled):
            scelti.add(gid)
    return scelti


class CalendarioTornei(_Dialogo):
    """
    Il calendario dei tornei e le iscrizioni a mano della polisportiva attiva, punto 12.3. Con
    iscrizioni vero si apre sulle iscrizioni della prima edizione aperta, con Ctrl+J. In fatte restano
    le iscrizioni fatte e tolte, coppie di tipo e testo, che la finestra riassume alla chiusura; in
    pannello, se si è chiesto il pannello di un'edizione in corso, la sua prima sede.
    """

    def __init__(self, genitore, mondo, poli, impostazioni=None, iscrizioni_subito=False):
        super().__init__(genitore, f"Calendario e iscrizioni di {poli.nome}")
        self.mondo = mondo
        self.poli = poli
        self.impostazioni = impostazioni
        self.fatte = []
        self.pannello_chiesto = None
        self.voci = []
        self.iscrivibili = []
        self.iscritti = []
        self._pressioni = {}
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Mostra")
        self.scelta = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in SCELTE_DEL_CALENDARIO]))
        self.scelta.SetSelection(0)
        self.etichetta("&Edizioni")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Iscrivibili, i tuoi tesserati")
        self.elenco_iscrivibili = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("Is&critti dei tuoi")
        self.elenco_iscritti = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        # Nessun pulsante predefinito, punto 12.3: con Iscrivi predefinito, Invio su un elenco o su Mostra
        # iscriveva e pagava la quota per l'atleta scelto nell'altro elenco, revisione del 14 ottobre 2026.
        self.iscrivi_pulsante, togli, pannello, _chiudi = self.pulsanti((wx.ID_ANY, "Iscri&vi"), (wx.ID_ANY, "&Togli"),
                                                                       (wx.ID_ANY, "&Pannello del torneo"), (wx.ID_CANCEL, "C&hiudi"), predefinito=False)
        self.iscrivi_pulsante.Bind(wx.EVT_BUTTON, self.iscrivi)
        togli.Bind(wx.EVT_BUTTON, self.togli)
        pannello.Bind(wx.EVT_BUTTON, self.al_pannello)
        self.scelta.Bind(wx.EVT_CHOICE, lambda event: self.aggiorna(0))
        self.elenco.Bind(wx.EVT_LISTBOX, lambda event: self.aggiorna_atleti())
        self.aggiorna(0)
        self.completa((680, 680))
        (self.elenco_iscrivibili if iscrizioni_subito else self.elenco).SetFocus()

    # Le edizioni.

    def _modo(self):
        return SCELTE_DEL_CALENDARIO[self.scelta.GetSelection()][0]

    def _oggi(self):
        return self.mondo.datetime_corrente_simulazione.date()

    def _tuoi_nell_edizione(self, ed):
        if not ed.individuale:
            return int(ed.iscritto(self.poli.nome) is not None)
        tuoi = tuoi_del_mondo(self.mondo)
        return sum(1 for gid in ed.ids() if gid in tuoi)

    def _voci_aperte(self):
        return [("aperta", ed) for ed in sorted(self.mondo.calendario.edizioni, key=lambda ed: (ed.data_inizio, ed.nome))]

    def _voci_prossime(self):
        """Le edizioni aperte e quelle dei prossimi trenta giorni che la ricorrenza dei modelli farà nascere, dalla più vicina."""
        oggi = self._oggi()
        limite = oggi + datetime.timedelta(days=GIORNI_AVANTI)
        aperte = self._voci_aperte()
        gia = {(ed.modello_id, ed.data_inizio) for _tipo, ed in aperte}
        gia |= {(t.modello["id"], datetime.date.fromisoformat(t.data_inizio)) for t in self.mondo.calendario.tornei}
        previste = []
        modelli, _scartati = modelli_torneo.GestoreModelli().modelli()
        for modello in modelli:
            if not modello.attivo or modelli_torneo.problema(modello) is not None:
                continue
            giorno = oggi + datetime.timedelta(days=1)
            while True:
                inizio = modelli_torneo.prossima_data(modello, giorno)
                if inizio > limite:
                    break
                if (modello.id, inizio) not in gia:
                    previste.append(("prevista", (modello, inizio)))
                giorno = inizio + datetime.timedelta(days=1)
        voci = aperte + previste
        return sorted(voci, key=lambda v: (v[1].data_inizio if v[0] == "aperta" else v[1][1], v[1].nome if v[0] == "aperta" else v[1][0].nome))

    def _voci_in_corso(self):
        """Le edizioni già cominciate, una voce per edizione con le sue sedi in corso."""
        per_edizione = {}
        for torneo in self.mondo.calendario.tornei:
            per_edizione.setdefault(torneo.edizione, []).append(torneo)
        return [("in_corso", sedi) for _ed, sedi in sorted(per_edizione.items(), key=lambda v: (v[1][0].data_inizio, v[1][0].modello["nome"]))]

    def _riga(self, voce):
        tipo, dati = voce
        if tipo == "aperta":
            return testi.riga_edizione(dati, self._tuoi_nell_edizione(dati))
        if tipo == "prevista":
            return testi.riga_edizione_prevista(*dati)
        tuoi = sum(len(tuoi_nel_torneo(self.mondo, t)) for t in dati)
        primo = dati[0]
        return testi.riga_edizione_in_corso(primo.modello["nome"], primo.modello["sesso"], datetime.date.fromisoformat(primo.data_inizio), len(dati), tuoi)

    def aggiorna(self, posto=None):
        """Riscrive la testata, l'elenco delle edizioni tenendo il posto, e gli atleti dell'edizione scelta."""
        posto = self.elenco.GetSelection() if posto is None else posto
        modo = self._modo()
        self.voci = {APERTE: self._voci_aperte, PROSSIME: self._voci_prossime, IN_CORSO: self._voci_in_corso}[modo]()
        self.info.SetLabel(testi.testata_del_calendario(self.poli, len(self.mondo.calendario.edizioni)))
        vuoto = {APERTE: "Nessuna edizione ha le iscrizioni aperte.", PROSSIME: "Nessuna edizione nei prossimi 30 giorni.", IN_CORSO: "Nessuna edizione è in corso."}[modo]
        self._riscrivi(self.elenco, [self._riga(v) for v in self.voci] or [vuoto], posto)
        self.aggiorna_atleti()
        self.pannello.Layout()

    def _voce(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.voci):
            return None
        return self.voci[indice]

    def _edizione_aperta(self):
        voce = self._voce()
        return voce[1] if voce is not None and voce[0] == "aperta" else None

    # Gli atleti dell'edizione scelta.

    def _tesserati(self):
        return sorted((self.mondo.giocatori[gid] for gid in self.poli.tesserati if gid in self.mondo.giocatori), key=lambda g: testi.nome_completo(g).casefold())

    def aggiorna_atleti(self):
        """Gli iscrivibili e gli iscritti dell'edizione scelta, tenendo il posto; Iscrivi diventa Rosa per la coppa quando serve."""
        ed = self._edizione_aperta()
        posti = (self.elenco_iscrivibili.GetSelection(), self.elenco_iscritti.GetSelection())
        tesserati = self._tesserati()
        if ed is None:
            voce = self._voce()
            self.iscrivibili, self.iscritti = [], []
            if voce is not None and voce[0] == "prevista":
                motivo = f"Le iscrizioni di questa edizione si aprono il {testi.data_breve(voce[1][1] - datetime.timedelta(days=voce[1][0].giorni_iscrizione))}."
            elif voce is not None:
                motivo = "L'edizione è già cominciata: si segue dal pannello del torneo."
            else:
                motivo = "Scegli un'edizione aperta alle iscrizioni."
            righe_iscrivibili, righe_iscritti = [motivo], [motivo]
        elif ed.individuale:
            ids = set(ed.ids())
            self.iscrivibili = [g for g in tesserati if g.id not in ids]
            self.iscritti = [(g, ed.iscritto(g.id)["origine"]) for g in tesserati if g.id in ids]
            # Chi è iscritto per il club ma non è più tesserato resta iscritto per chi ha pagato, e si può togliere.
            club = iscrizioni.club_della(self.poli)
            for iscritto in ed.iscritti:
                g = self.mondo.giocatori.get(iscritto["id"])
                if g is not None and iscritto["club"] == club and g.id not in self.poli.tesserati:
                    self.iscritti.append((g, iscritto["origine"]))
            righe_iscrivibili = [testi.riga_atleta_del_calendario(g, self.mondo, ed=ed) for g in self.iscrivibili] or ["Tutti i tuoi tesserati sono già iscritti."]
            righe_iscritti = [testi.riga_atleta_del_calendario(g, self.mondo, origine) for g, origine in self.iscritti] or ["Nessuno dei tuoi è iscritto."]
        else:
            iscritto = ed.iscritto(self.poli.nome)
            rosa = list(iscritto.get("rosa", ())) if iscritto else []
            self.iscrivibili = [g for g in tesserati if g.id not in rosa]
            self.iscritti = [(self.mondo.giocatori[gid], posto) for posto, gid in enumerate(rosa, start=1) if gid in self.mondo.giocatori]
            righe_iscrivibili = [testi.riga_atleta_del_calendario(g, self.mondo) for g in self.iscrivibili] or ["Tutti i tuoi tesserati sono nella rosa."]
            if iscritto is None:
                righe_iscritti = [f"{self.poli.nome} non è qualificata a {ed.nome}: si qualificano le polisportive con più gloria."]
            else:
                righe_iscritti = [testi.riga_della_rosa(g, self.mondo, posto) for g, posto in self.iscritti] or ["La rosa è vuota."]
        self._riscrivi(self.elenco_iscrivibili, righe_iscrivibili, posti[0])
        self._riscrivi(self.elenco_iscritti, righe_iscritti, posti[1])
        etichetta = "&Rosa per la coppa..." if ed is not None and not ed.individuale else "Iscri&vi"
        if self.iscrivi_pulsante.GetLabel() != etichetta:
            self.iscrivi_pulsante.SetLabel(etichetta)
            self.pannello.Layout()

    def _scelto(self, elenco, voci):
        indice = elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(voci):
            return None
        return voci[indice]

    # I pulsanti.

    def _ripetuta(self, nome):
        """Vero se il pulsante è stato premuto meno di mezzo secondo fa: è un tasto tenuto giù, e la pressione si ignora."""
        adesso_monotono = time.monotonic()
        prima = self._pressioni.get(nome)
        self._pressioni[nome] = adesso_monotono
        return prima is not None and adesso_monotono - prima < RIPETIZIONE_IGNORATA

    def _suono_del_rifiuto(self, ed, g):
        """Il suono di un'iscrizione rifiutata, nell'ordine dei controlli di iscrizioni.problema_iscrizione."""
        if ed.data_inizio <= self._oggi() or g.id not in self.poli.tesserati or g.ritirato:
            return "campo_da_correggere"
        if not ed.individuale or ed.qualificazione != modelli_torneo.NESSUNA or (ed.sesso not in ("aperto", g.sesso)) or (
                ed.filtri and not modelli_torneo.idoneo(ed.oggetto_modello, g)):
            return "iscrizione_non_idoneo"
        if g.id in ed.ids():
            return "campo_da_correggere"
        for inizio, fine, _descrizione, _tipo in self.mondo.calendario.impegni_descritti(self.mondo, g.id):
            if inizio <= ed.data_fine and ed.data_inizio <= fine:
                return "iscrizione_sovrapposta"
        if self.poli.cassa < ed.quota:
            return "iscrizione_cassa_insufficiente"
        return "campo_da_correggere"

    def _non_aperta(self, elenco):
        """L'avviso di un pulsante premuto su un'edizione che non ha le iscrizioni aperte."""
        voce = self._voce()
        if voce is None:
            suoni.suona("nessuna_selezione")
        elif voce[0] == "prevista":
            self.avvisa(self.elenco_iscrivibili.GetString(0), self.elenco)
        else:
            self.avvisa("L'edizione è già cominciata: il sorteggio è fatto, e le iscrizioni non si cambiano più.", self.elenco)

    def iscrivi(self, event=None):
        if self._ripetuta("iscrivi"):
            return
        ed = self._edizione_aperta()
        if ed is None:
            self._non_aperta(self.elenco)
            return
        if not ed.individuale:
            self.rosa_per_la_coppa(ed)
            return
        g = self._scelto(self.elenco_iscrivibili, self.iscrivibili)
        if g is None:
            suoni.suona("nessuna_selezione")
            return
        problema = iscrizioni.problema_iscrizione(self.mondo, ed.id, g, self.poli)
        if problema:
            self.avvisa(problema, self.elenco_iscrivibili, self._suono_del_rifiuto(ed, g))
            return
        iscrizioni.iscrivi(self.mondo, ed.id, g, self.poli)
        self.fatte.append(("iscritto", testi.iscrizione_fatta(g, ed, ed.quota)))
        suoni.suona("iscrizione_fatta")
        self.aggiorna()

    def togli(self, event=None):
        if self._ripetuta("togli"):
            return
        ed = self._edizione_aperta()
        if ed is None:
            self._non_aperta(self.elenco)
            return
        if not ed.individuale:
            self.avvisa("La rosa per la coppa si cambia con Rosa per la coppa.", self.elenco_iscritti)
            return
        scelto = self._scelto(self.elenco_iscritti, self.iscritti)
        if scelto is None:
            suoni.suona("nessuna_selezione")
            return
        g, _origine = scelto
        problema = iscrizioni.problema_ritiro(self.mondo, ed.id, g, self.poli)
        if problema:
            self.avvisa(problema, self.elenco_iscritti)
            return
        if ed.qualificazione == modelli_torneo.PUNTI_ANNO:
            # Dal mondiale il posto passa al seguente, e chi hai tolto non torna convocato: si chiede.
            if not self._conferma(f"Togliere {testi.nome_completo(g)} da {ed.nome}? Il posto passa al primo dei non convocati, e non si torna indietro."):
                self.elenco_iscritti.SetFocus()
                return
        rimborso = iscrizioni.togli(self.mondo, ed.id, g, self.poli)
        self.fatte.append(("tolto", testi.iscrizione_tolta(g, ed, rimborso)))
        suoni.suona("iscrizione_tolta")
        self.aggiorna()

    def rosa_per_la_coppa(self, ed):
        """La rosa della tua polisportiva qualificata alla coppa, fino a sei, nel dialogo della formazione."""
        iscritto = ed.iscritto(self.poli.nome)
        if iscritto is None:
            self.avvisa(f"{self.poli.nome} non è qualificata a {ed.nome}: si qualificano le polisportive con più gloria.", self.elenco, "iscrizione_non_idoneo")
            return
        convocabili = [g for g in self._tesserati() if not g.ritirato]
        dialogo = gui_sfide.FormazioneDialogo(self, self.mondo, f"Rosa per {ed.nome}", f"La rosa di {self.poli.nome} per {ed.nome}, dal "
                                              f"{testi.data_breve(ed.data_inizio)}: i primi tre giocano ogni incontro, se sono sani, e le riserve li sostituiscono.",
                                              convocabili, iscritto.get("rosa", []), lambda ids: sfide.problema_rosa(self.mondo, ed.id, self.poli, ids))
        try:
            suoni.suona("dialogo_formazione")
            if dialogo.ShowModal() != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return
            ids = dialogo.risultato
        finally:
            dialogo.Destroy()
        sfide.cambia_rosa(self.mondo, ed.id, self.poli, ids)
        self.fatte.append(("rosa", testi.rosa_iscritta(self.poli, ed, [self.mondo.giocatori[gid] for gid in ids])))
        suoni.suona("iscrizione_fatta")
        self.aggiorna()

    def al_pannello(self, event=None):
        """Il pannello di un'edizione già cominciata: il calendario si chiude, e la finestra apre il pannello sulla sua prima sede."""
        voce = self._voce()
        if voce is None or voce[0] != "in_corso":
            if voce is None:
                suoni.suona("nessuna_selezione")
            else:
                self.avvisa("Il pannello c'è per le edizioni già cominciate: si sceglie Edizioni in corso in Mostra.", self.scelta)
            return
        self.pannello_chiesto = voce[1][0].id
        self.chiudi(wx.ID_OK)


class PannelloTornei(_Dialogo):
    """
    Il pannello dei tornei, punto 12.2: i tornei in corso e conclusi di recente, le loro parti, le
    classifiche e gli incontri, con l'ascolto in differita, la lettura della cronaca e i risultati da
    svelare. In ultimo resta l'ultimo incontro ascoltato o letto, per Salva la cronaca; in velocita la
    velocità di gioco a cui si è arrivati ascoltando; in svelati quanti risultati si sono mostrati.
    """

    def __init__(self, genitore, mondo, impostazioni=None, torneo_scelto=None):
        super().__init__(genitore, "Tornei in corso")
        self.mondo = mondo
        self.impostazioni = modulo_impostazioni.valide(impostazioni)
        self.velocita = self.impostazioni.get("velocita_gioco")
        self.ultimo = None
        self.svelati = 0
        self.tuoi = tuoi_del_mondo(mondo)
        self.mostrati = []
        self.parti = []
        self.righe_classifica = []
        self.incontri = []
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("Mo&stra")
        self.scelta = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in SCELTE_DEL_PANNELLO]))
        self.etichetta("&Tornei")
        self.elenco_tornei = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Parti")
        self.elenco_parti = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE))
        self.etichetta("&Classifica")
        self.elenco_classifica = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Incontri")
        self.elenco_incontri = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        # Nessun pulsante predefinito: Invio ascolta soltanto sull'elenco degli incontri, punto 12.2, e
        # sugli altri elenchi non fa niente; prima, con Ascolta predefinito, Invio su Tornei o su Parti
        # ascoltava l'incontro scelto negli Incontri, che in quel momento non si guardava.
        ascolta, leggi, mostra = self.pulsanti((wx.ID_ANY, "&Ascolta in differita"), (wx.ID_ANY, "&Leggi la cronaca"), (wx.ID_ANY, "&Mostra il risultato"),
                                               predefinito=False)
        tutti, scheda, _chiudi = self.pulsanti((wx.ID_ANY, "Mostra t&utti i risultati"), (wx.ID_ANY, "Scheda del &giocatore"), (wx.ID_CANCEL, "C&hiudi"),
                                              predefinito=False)
        self.invio_su(self.elenco_incontri, self.ascolta)
        ascolta.Bind(wx.EVT_BUTTON, self.ascolta)
        leggi.Bind(wx.EVT_BUTTON, self.leggi)
        mostra.Bind(wx.EVT_BUTTON, self.mostra_risultato)
        tutti.Bind(wx.EVT_BUTTON, self.mostra_tutti)
        scheda.Bind(wx.EVT_BUTTON, self.scheda)
        self.scelta.Bind(wx.EVT_CHOICE, lambda event: self.aggiorna(0))
        self.elenco_tornei.Bind(wx.EVT_LISTBOX, lambda event: self.al_torneo(0))
        self.elenco_parti.Bind(wx.EVT_LISTBOX, lambda event: self.alla_parte())
        self.elenco_incontri.Bind(wx.EVT_LISTBOX_DCLICK, self.ascolta)
        posto = 0
        if torneo_scelto is not None:
            self.scelta.SetSelection(1)
            self.mostrati = self._tornei_da_mostrare()
            posto = next((i for i, t in enumerate(self.mostrati) if t.id == torneo_scelto), 0)
        else:
            self.scelta.SetSelection(0 if any(tuoi_nel_torneo(mondo, t, self.tuoi) for t in mondo.calendario.tornei) else 1)
        self.aggiorna(posto)
        self.completa((720, 720))
        self.elenco_tornei.SetFocus()

    # Gli elenchi.

    def _modo(self):
        return SCELTE_DEL_PANNELLO[self.scelta.GetSelection()][0]

    def _tornei_da_mostrare(self):
        cal = self.mondo.calendario
        modo = self._modo()
        if modo == DIFFERITE:
            return [sede for _voce, sede in cal.sedi_in_differita()]
        insieme = cal.tornei if modo in (CON_I_TUOI, TUTTI_IN_CORSO) else list(reversed(cal.conclusi))
        if modo in (CON_I_TUOI, CONCLUSI_TUOI):
            insieme = [t for t in insieme if tuoi_nel_torneo(self.mondo, t, self.tuoi)]
        return list(insieme)

    def _riga(self, torneo):
        if isinstance(torneo, SedeInDifferita):
            return testi.riga_della_sede_in_differita(torneo)
        return testi.riga_del_pannello(torneo, len(tuoi_nel_torneo(self.mondo, torneo, self.tuoi)))

    def aggiorna(self, posto=None):
        """Riscrive la testata e l'elenco dei tornei tenendo il posto, e sotto le parti, la classifica e gli incontri."""
        posto = self.elenco_tornei.GetSelection() if posto is None else posto
        cal = self.mondo.calendario
        con_i_tuoi = sum(1 for t in cal.tornei if tuoi_nel_torneo(self.mondo, t, self.tuoi))
        self.info.SetLabel(testi.testata_del_pannello(len(cal.tornei), con_i_tuoi, len(cal.conclusi)))
        self.mostrati = self._tornei_da_mostrare()
        righe = [self._riga(t) for t in self.mostrati]
        vuoto = {CON_I_TUOI: "Nessun torneo in corso con i tuoi atleti.", TUTTI_IN_CORSO: "Nessun torneo in corso.",
                 CONCLUSI_TUOI: "Nessun torneo dei tuoi concluso negli ultimi 14 giorni.", TUTTI_CONCLUSI: "Nessun torneo concluso negli ultimi 14 giorni.",
                 DIFFERITE: "Nessuna edizione conclusa con i tuoi da riascoltare."}[self._modo()]
        self._riscrivi(self.elenco_tornei, righe or [vuoto], posto)
        self.al_torneo()
        self.pannello.Layout()

    def _torneo(self):
        indice = self.elenco_tornei.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.mostrati):
            return None
        return self.mostrati[indice]

    def al_torneo(self, posto=None):
        torneo = self._torneo()
        posto = self.elenco_parti.GetSelection() if posto is None else posto
        if torneo is None:
            self.parti = []
            self._riscrivi(self.elenco_parti, ["Nessun torneo scelto."], 0)
        elif isinstance(torneo, SedeInDifferita):
            # Di un'edizione delle differite restano soltanto i tuoi incontri, e il podio nell'albo.
            self.parti = [("I tuoi incontri, col podio della sede", ("differita", None, None))]
            self._riscrivi(self.elenco_parti, [self.parti[0][0]], 0)
        else:
            self.parti = testi.parti_del_torneo(torneo, bool(tuoi_nel_torneo(self.mondo, torneo, self.tuoi)))
            self._riscrivi(self.elenco_parti, [testo for testo, _chiave in self.parti], posto)
        self.alla_parte()

    def _parte(self):
        indice = self.elenco_parti.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.parti):
            return None
        return self.parti[indice][1]

    def alla_parte(self, posti=None):
        """La classifica e gli incontri della parte scelta, tenendo i posti."""
        torneo, chiave = self._torneo(), self._parte()
        posto_classifica, posto_incontri = posti or (self.elenco_classifica.GetSelection(), self.elenco_incontri.GetSelection())
        if torneo is None or chiave is None:
            self.righe_classifica, self.incontri = [], []
            self._riscrivi(self.elenco_classifica, ["Niente da mostrare."], 0)
            self._riscrivi(self.elenco_incontri, ["Niente da mostrare."], 0)
            return
        if isinstance(torneo, SedeInDifferita):
            albo = self.mondo.calendario.albo
            voce = testi.voce_della_sede_in_differita(albo, torneo)
            podio = voce[8] if voce is not None else []
            self.righe_classifica = [(albo.club[p][0] if p is not None else None) if torneo.squadre else p[0] for p in podio]
            self._riscrivi(self.elenco_classifica, testi.podio_della_sede_in_differita(albo, torneo), posto_classifica)
            self.incontri = sorted(torneo.incontri(), key=lambda i: (i.fase, i.turno, i.finalina, i.gruppo, i.posto))
            self._riscrivi(self.elenco_incontri, [testi.incontro_in_elenco(torneo, i) for i in self.incontri] or ["Nessun incontro."], posto_incontri)
            return
        tuoi = tuoi_nel_torneo(self.mondo, torneo, self.tuoi)
        self.righe_classifica = self._gid_della_classifica(torneo, chiave, tuoi)
        self._riscrivi(self.elenco_classifica, testi.classifica_della_parte(torneo, chiave, tuoi), posto_classifica)
        self.incontri = testi.incontri_della_parte(torneo, chiave, tuoi)
        self._riscrivi(self.elenco_incontri, [testi.incontro_in_elenco(torneo, i) for i in self.incontri] or ["Nessun incontro."], posto_incontri)

    @staticmethod
    def _gid_della_classifica(torneo, chiave, tuoi):
        """Gli iscritti delle righe della classifica, nello stesso ordine, per la scheda del giocatore."""
        tipo, indice, lettera = chiave
        if tipo == "girone":
            return tornei.classifica_girone(torneo, torneo.fasi[indice], lettera)
        if tipo == "tabellone":
            gid = []
            for incontro in sorted(torneo.fasi[indice].incontri, key=lambda i: (i.turno, i.finalina, i.posto)):
                if not incontro.giocato and incontro.b is not None:
                    gid.extend((incontro.a, incontro.b))
            return gid
        righe = testi._righe_generali(torneo)
        return [g for g, _riga in righe if tipo != "tuoi" or g in tuoi]

    def _incontro(self):
        indice = self.elenco_incontri.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.incontri):
            return None
        return self.incontri[indice]

    def _riscrivi_tutto(self):
        """Dopo un risultato svelato: gli elenchi si riscrivono tenendo il posto, e il fuoco va sugli incontri, che dicono il risultato."""
        self.aggiorna()
        self.elenco_incontri.SetFocus()

    # L'ascolto, la lettura e i risultati.

    def _ascoltabile(self):
        """L'incontro scelto, se è dei tuoi e si può ancora riascoltare; altrimenti avvisa col suo suono e restituisce None."""
        torneo, incontro = self._torneo(), self._incontro()
        if incontro is None:
            suoni.suona("nessuna_selezione")
            return None, None
        if not incontro.differita:
            self.avvisa("Questo incontro non si può ascoltare: si riascoltano soltanto gli incontri giocati dai tuoi atleti.", self.elenco_incontri, "nessuna_differita")
            return None, None
        if torneo.stato != tornei.IN_CORSO and not isinstance(torneo, SedeInDifferita):
            voce = self.mondo.calendario.differite.get(torneo.modello["id"])
            if voce is None or voce["edizione"] != torneo.edizione:
                self.avvisa("Questo incontro non si può più ascoltare: un'edizione più recente dello stesso torneo ha preso il suo posto.", self.elenco_incontri,
                            "nessuna_differita")
                return None, None
        return torneo, incontro

    def ascolta(self, event=None):
        _torneo, incontro = self._ascoltabile()
        if incontro is None:
            return
        ultimo, self.velocita = ascolta_e_ricorda(self, self.mondo, incontro.differita, incontro.seme, self.impostazioni, self.tuoi, incontro.data,
                                                  "torneo", self.velocita)
        if ultimo is not None:
            self.ultimo = ultimo
            self._svela(incontro)
        self._riscrivi_tutto()

    def leggi(self, event=None):
        _torneo, incontro = self._ascoltabile()
        if incontro is None:
            return
        self.ultimo = leggi_e_ricorda(self, self.mondo, incontro.differita, incontro.seme, self.impostazioni, incontro.data, "torneo")
        self._svela(incontro)
        self._riscrivi_tutto()

    def _svela(self, incontro):
        if not incontro.svelato:
            incontro.svelato = True
            self.svelati += 1

    def mostra_risultato(self, event=None):
        incontro = self._incontro()
        if incontro is None:
            suoni.suona("nessuna_selezione")
            return
        if not incontro.giocato or not incontro.differita or incontro.svelato:
            self.avvisa("Il risultato di questo incontro non è nascosto: si legge già nell'elenco.", self.elenco_incontri, "nessun_risultato_da_svelare")
            return
        self._svela(incontro)
        suoni.suona("risultato_svelato")
        self._riscrivi_tutto()

    def mostra_tutti(self, event=None):
        """Mostra tutti i risultati, risposta 18: svela in un colpo gli incontri dei tuoi da ascoltare, di tutti i tornei, dopo una domanda col no già scelto."""
        quanti = len(self.mondo.calendario.da_svelare())
        if not quanti:
            self.avvisa("Non ci sono incontri dei tuoi ancora da ascoltare: tutti i risultati si leggono già.", self.elenco_incontri, "nessun_risultato_da_svelare")
            return
        domanda = ("Mostrare il risultato dell'incontro dei tuoi ancora da ascoltare? Non si torna indietro." if quanti == 1 else
                   f"Mostrare i risultati dei {quanti} incontri dei tuoi ancora da ascoltare? Non si torna indietro.")
        if not self._conferma(domanda):
            self.elenco_incontri.SetFocus()
            return
        svelati = self.mondo.calendario.svela_tutti()
        self.svelati += svelati
        self.aggiorna()
        suoni.suona("risultati_svelati_tutti")
        wx.MessageBox(f"Mostrati i risultati di {testi.conta(svelati, 'incontro', 'incontri')}.", self.GetTitle(), wx.OK | wx.ICON_INFORMATION, self)
        self.elenco_incontri.SetFocus()

    def scheda(self, event=None):
        """La scheda del giocatore della riga scelta in Classifica; nella coppa, quella della polisportiva."""
        indice = self.elenco_classifica.GetSelection()
        chi = self.righe_classifica[indice] if indice != wx.NOT_FOUND and indice < len(self.righe_classifica) else None
        if isinstance(chi, str):
            p = self.mondo.polisportive.get(chi)
            if p is None:
                suoni.suona("nessuna_selezione")
                return
            dialogo = Lettura(self, f"Scheda di {p.nome}", testi.scheda_polisportiva(p, self.mondo), self.impostazioni)
            try:
                suoni.suona("scheda_polisportiva")
                dialogo.ShowModal()
            finally:
                dialogo.Destroy()
            return
        g = self.mondo.giocatori.get(chi) if chi is not None else None
        if g is None:
            suoni.suona("nessuna_selezione")
            return
        self._scheda_del_giocatore(g, self.impostazioni)


class AlboDOro(_Dialogo):
    """
    L'albo d'oro, risposta 13 di Gabriele, punto 12.1: conserva ogni sede conclusa per sempre, quindi
    ci si arriva per modello, con i mondiali e la coppa in testa, e per anno, dal più recente; per
    l'edizione scelta, i podi delle sue sedi, tutte o soltanto quelle con i tuoi sul podio.
    """

    def __init__(self, genitore, mondo):
        super().__init__(genitore, "Albo d'oro")
        self.mondo = mondo
        self.albo = mondo.calendario.albo
        self.tuoi = tuoi_del_mondo(mondo)
        self.club_tuoi = {i for i, (nome, fondazione) in enumerate(self.albo.club)
                          if (p := mondo.polisportive.get(nome)) is not None and not p.is_cpu_controlled
                          and p.datetime_creazione_sim.date().isoformat() == fondazione}
        importanze = {}
        for voce in self.albo.voci:
            importanze[voce[0]] = max(importanze.get(voce[0], 0.0), voce[3])
        # Un modello per ogni nome che ha avuto: le edizioni passate tengono il nome di allora.
        self.modelli = sorted(importanze, key=lambda m: (-(importanze[m] >= 3), -importanze[m], self.albo.nome_del_modello(m).casefold(), m))
        self.anni = []
        self.edizioni = []
        self.sedi = []
        self.etichetta("&Modello")
        self.scelta_modello = self.aggiungi(wx.Choice(self.pannello, choices=[self.albo.nome_del_modello(m) for m in self.modelli] or ["L'albo è ancora vuoto"]))
        self.etichetta("&Anno")
        self.scelta_anno = self.aggiungi(wx.Choice(self.pannello))
        self.etichetta("M&ostra")
        self.scelta_mostra = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in SCELTE_DELL_ALBO]))
        self.etichetta("&Edizioni")
        self.elenco_edizioni = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("&Podi")
        self.elenco_podi = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        # Senza pulsante predefinito: Invio su un'edizione o su un podio non chiude l'albo, Esc sì.
        self.pulsanti((wx.ID_CANCEL, "C&hiudi"), predefinito=False)
        self.scelta_modello.SetSelection(0)
        self.scelta_mostra.SetSelection(0)
        self.scelta_modello.Bind(wx.EVT_CHOICE, lambda event: self.al_modello())
        self.scelta_anno.Bind(wx.EVT_CHOICE, lambda event: self.all_anno())
        self.scelta_mostra.Bind(wx.EVT_CHOICE, lambda event: self.all_anno())
        self.elenco_edizioni.Bind(wx.EVT_LISTBOX, lambda event: self.all_edizione())
        self.al_modello()
        self.completa((680, 600))
        self.scelta_modello.SetFocus()

    def _modello(self):
        indice = self.scelta_modello.GetSelection()
        return self.modelli[indice] if 0 <= indice < len(self.modelli) else None

    def _con_i_tuoi(self, voce):
        """Vero se sul podio della sede c'è uno dei tuoi: un tuo tesserato, o il club di una tua polisportiva."""
        for posto in voce[8]:
            if voce[1] == modelli_torneo.SQUADRE:
                if posto in self.club_tuoi:
                    return True
            elif posto[0] in self.tuoi or posto[1] in self.club_tuoi:
                return True
        return False

    def al_modello(self):
        modello = self._modello()
        self.anni = sorted({testi.anno_della_voce(v) for v in self.albo.voci if v[0] == modello}, reverse=True)
        self.scelta_anno.Set([str(anno) for anno in self.anni] or ["nessun anno"])
        self.scelta_anno.SetSelection(0)
        self.all_anno()

    def all_anno(self):
        modello = self._modello()
        anno = self.anni[self.scelta_anno.GetSelection()] if self.anni else None
        solo_tuoi = SCELTE_DELL_ALBO[self.scelta_mostra.GetSelection()][0] == SEDI_CON_I_TUOI
        per_numero = {}
        for voce in self.albo.voci:
            if voce[0] == modello and testi.anno_della_voce(voce) == anno and (not solo_tuoi or self._con_i_tuoi(voce)):
                per_numero.setdefault(voce[5], []).append(voce)
        self.edizioni = [per_numero[n] for n in sorted(per_numero, reverse=True)]
        vuoto = "Nessuna sede con i tuoi sul podio in quell'anno." if solo_tuoi else "Nessuna edizione."
        self._riscrivi(self.elenco_edizioni, [testi.riga_edizione_dell_albo(self.albo, voci) for voci in self.edizioni] or [vuoto], 0)
        self.all_edizione()

    def all_edizione(self):
        indice = self.elenco_edizioni.GetSelection()
        self.sedi = sorted(self.edizioni[indice], key=lambda v: v[6]) if 0 <= indice < len(self.edizioni) else []
        self._riscrivi(self.elenco_podi, [testi.podio_dell_albo(self.albo, voce) for voce in self.sedi] or ["Nessun podio."], 0)
