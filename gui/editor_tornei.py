"""
Gli editor dei tornei di MESS: i modelli di torneo e le formule, copiati da Terminal Beast e corretti.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-14 con il terzo passo della tappa 12, decisioni D9, D13 e D32 e punto 12.5 del
progetto. EditorModelli viene da TournamentEditorDialog, ModelloTorneoDialogo da
TournamentConfigDialog, EditorFormule da FormulaEditorDialog e FaseDialogo da PhaseConfigDialog, tutti
di Terminal Beast, con i loro difetti corretti: la validazione sta in un posto solo, formule.py e
modelli_torneo.py, e i dialoghi la chiedono e dicono il motivo sul campo da correggere; la formula
valida non chiude più il dialogo da sola; una formula usata non si elimina, e l'avviso dice da quali
modelli; la percentuale al primo diventa la pendenza vera, anche oltre i dieci posti premiati; i file
che non si leggono si dicono all'apertura, con il loro suono, invece di finire in un registro.
Gli editor cambiano soltanto le edizioni future: ogni edizione aperta conserva una copia congelata del
suo modello e della sua formula, D9 e D32.
Ogni dialogo segue lo schema degli altri: pannello che scorre, adatta_finestra, etichette con la
lettera, avvisi che lasciano aperto il dialogo col suono del loro perché, nessuna misura in pixel; la
ricorrenza e l'importanza si scelgono in elenchi a tendina, non scrivendo numeri.
"""

import copy

import wx

import classe
import formule
import modelli_torneo
import suoni
import testi
import tornei
from gui.dialoghi import _Dialogo

TIPI = ((modelli_torneo.INDIVIDUALE, "Individuale"), (modelli_torneo.SQUADRE, "A squadre"))
SESSI = (("m", "Maschile"), ("f", "Femminile"), ("aperto", "Aperto a tutti, misto"))
RICORRENZE = ((modelli_torneo.SETTIMANALE, "Settimanale"), (modelli_torneo.MENSILE, "Mensile"), (modelli_torneo.ANNUALE, "Annuale"))
SET = (3, 5)
FINALI_DA = ((0, "Nessuna fase finale diversa"), (2, "La finale"), (4, "Dalle semifinali"), (8, "Dai quarti"))
QUALIFICAZIONI = ((modelli_torneo.NESSUNA, "Nessuna, iscrizione libera"), (modelli_torneo.PUNTI_ANNO, "I migliori per i punti dell'ultimo anno"),
                  (modelli_torneo.GLORIA, "Le polisportive con più gloria"))
IMPORTANZE = tuple(x / 4 for x in range(2, 21))
CONTRIBUTI = tuple(x / 4 for x in range(0, 21))
CLASSI = (None, *(classe.codice(n) for n in range(1, classe.LIVELLI + 1)))
NESSUN_LIMITE = "nessun limite"


def _numero_corto(valore):
    return testi.numero(valore, 2).rstrip("0").rstrip(",")


class ModelloTorneoDialogo(_Dialogo):
    """
    Un modello di torneo, nuovo o da modificare, da TournamentConfigDialog di Terminal Beast: un'etichetta
    per ogni campo del punto 3.3 del progetto, la ricorrenza con le sue scelte di giorni e mesi a parole,
    l'importanza a passi di un quarto, la percentuale al primo che diventa la pendenza, e il Riepilogo,
    in sola lettura, che si aggiorna a ogni cambio. Salva controlla il modello col modulo e, se non va,
    avvisa sul campo da correggere; il dialogo non si chiude mai da solo. In risultato resta il modello.
    """

    def __init__(self, genitore, modello, formule_valide, gestore):
        super().__init__(genitore, f"Modello di torneo: {modello.nome}" if modello.nome else "Nuovo modello di torneo")
        self.modello = copy.deepcopy(modello)
        self.formule = formule_valide
        self.gestore = gestore
        self.risultato = None
        self.etichetta("&Nome, da 3 a 60 caratteri")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello, value=modello.nome))
        self.etichetta("N&ote")
        self.note = self.aggiungi(wx.TextCtrl(self.pannello, value=modello.note, style=wx.TE_MULTILINE))
        self.attivo = self.aggiungi(wx.CheckBox(self.pannello, label="&Attivo: apre le sue edizioni"))
        self.attivo.SetValue(modello.attivo)
        self.etichetta("&Tipo")
        self.tipo = self._scelta([nome for _k, nome in TIPI], [k for k, _n in TIPI].index(modello.tipo))
        self.etichetta("&Sesso, per i tornei individuali")
        self.sesso = self._scelta([nome for _k, nome in SESSI], next((i for i, (k, _n) in enumerate(SESSI) if k == modello.sesso), 2))
        self.etichetta("&Formula")
        nomi_formule = [f"{f['nome']}, fino a {formule.tetto(f)} iscritti per sede" for f in self.formule]
        posto = next((i for i, f in enumerate(self.formule) if f["id"] == modello.formula), 0)
        self.formula = self._scelta(nomi_formule or ["nessuna formula valida"], posto)
        self.etichetta("&Ricorrenza")
        self.ricorrenza = self._scelta([nome for _k, nome in RICORRENZE], [k for k, _n in RICORRENZE].index(modello.ricorrenza["tipo"]))
        self.etichetta("&Giorno")
        self.giorno = self.aggiungi(wx.Choice(self.pannello))
        self.etichetta("M&ese, per la ricorrenza annuale")
        self.mese = self._scelta([modelli_torneo.nome_del_mese(n) for n in range(1, 13)], modello.ricorrenza.get("mese", 1) - 1)
        self.etichetta("Giorni d'&iscrizione prima dell'inizio")
        self.giorni_iscrizione = self._numero(*modelli_torneo.GIORNI_ISCRIZIONE, modello.giorni_iscrizione)
        self.etichetta("Minimo d'is&critti")
        self.minimo = self._numero(modelli_torneo.MINIMO_ISCRITTI, formule.PARTECIPANTI_MASSIMI, modello.minimo_iscritti)
        self.etichetta("Set &base degli incontri, al meglio di")
        self.set_al_meglio = self._scelta([f"{n} set" for n in SET], SET.index(modello.set_al_meglio))
        self.etichetta("Set delle fasi fina&li, al meglio di")
        self.set_finali = self._scelta([f"{n} set" for n in SET], SET.index(modello.set_finali))
        self.etichetta("Fasi finali &da")
        self.finali_da = self._scelta([nome for _k, nome in FINALI_DA], [k for k, _n in FINALI_DA].index(modello.finali_da))
        self.etichetta("T&urni al giorno")
        self.turni = self._numero(*modelli_torneo.INCONTRI_AL_GIORNO, modello.incontri_al_giorno)
        self.etichetta("Im&portanza, che pesa punti, esperienza, classifica e palmarès")
        self.importanza = self._scelta([_numero_corto(x) for x in IMPORTANZE], IMPORTANZE.index(modello.importanza) if modello.importanza in IMPORTANZE else 2)
        self.etichetta("&Quota d'iscrizione, in euro")
        self.quota = self._numero(0, modelli_torneo.QUOTA_MASSIMA, modello.quota_iscrizione)
        self.etichetta("Contributo della federa&zione, 1 raddoppia il montepremi")
        self.contributo = self._scelta([_numero_corto(x) for x in CONTRIBUTI],
                                       CONTRIBUTI.index(modello.contributo_federazione) if modello.contributo_federazione in CONTRIBUTI else 4)
        self.etichetta("&Montepremi minimo per sede, in euro")
        self.montepremi_minimo = self._numero(0, modelli_torneo.MONTEPREMI_MINIMO_MASSIMO, modello.montepremi_minimo)
        self.etichetta("Quanti posti &hanno un premio")
        self.posti = self._numero(1, formule.PARTECIPANTI_MASSIMI, modello.posti_premiati)
        self.etichetta("Percentuale del montepremi al primo")
        # La percentuale di partenza è quella della pendenza del modello: finché non cambiano lei e i
        # posti, la pendenza resta quella, senza l'arrotondamento della percentuale.
        self._partenza = (round(tornei.prima_percentuale(modello.pendenza_premi, modello.posti_premiati)), modello.posti_premiati, modello.pendenza_premi)
        self.percentuale = self._numero(1, 100, self._partenza[0])
        self.etichetta("Qualificazione")
        self.qualificazione = self._scelta([nome for _k, nome in QUALIFICAZIONI], [k for k, _n in QUALIFICAZIONI].index(modello.qualificazione))
        self.etichetta("Classe minima, la più debole ammessa")
        self.classe_minima = self._scelta([c or NESSUN_LIMITE for c in CLASSI], CLASSI.index(modello.classe_minima))
        self.etichetta("Classe massima, la più forte ammessa")
        self.classe_massima = self._scelta([c or NESSUN_LIMITE for c in CLASSI], CLASSI.index(modello.classe_massima))
        self.etichetta("Età minima in anni, zero per nessun limite")
        self.eta_minima = self._numero(0, modelli_torneo.ETA[1], modello.eta_minima or 0)
        self.etichetta("Età massima in anni, zero per nessun limite")
        self.eta_massima = self._numero(0, modelli_torneo.ETA[1], modello.eta_massima or 0)
        self.etichetta("Riepilogo")
        self.riepilogo = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2), 1)
        salva, _annulla = self.pulsanti((wx.ID_OK, "Sal&va"), (wx.ID_CANCEL, "Annulla"))
        salva.Bind(wx.EVT_BUTTON, self.conferma)
        self._giorni_della_ricorrenza(modello.ricorrenza["giorno"])
        for controllo in (self.tipo, self.sesso, self.formula, self.giorno, self.mese, self.set_al_meglio, self.set_finali, self.finali_da, self.importanza,
                          self.contributo, self.qualificazione, self.classe_minima, self.classe_massima):
            controllo.Bind(wx.EVT_CHOICE, self.aggiorna)
        self.ricorrenza.Bind(wx.EVT_CHOICE, self.alla_ricorrenza)
        for controllo in (self.giorni_iscrizione, self.minimo, self.turni, self.quota, self.montepremi_minimo, self.posti, self.percentuale, self.eta_minima,
                          self.eta_massima):
            controllo.Bind(wx.EVT_SPINCTRL, self.aggiorna)
            controllo.Bind(wx.EVT_TEXT, self.aggiorna)
        self.attivo.Bind(wx.EVT_CHECKBOX, self.aggiorna)
        self.aggiorna()
        self.completa((640, 700))
        self.nome.SetFocus()

    def _scelta(self, voci, posto):
        controllo = self.aggiungi(wx.Choice(self.pannello, choices=list(voci)))
        controllo.SetSelection(max(0, min(posto, len(voci) - 1)))
        return controllo

    def _numero(self, minimo, massimo, valore):
        return self.aggiungi(wx.SpinCtrl(self.pannello, min=minimo, max=massimo, initial=max(minimo, min(massimo, valore))))

    # La ricorrenza.

    def _tipo_della_ricorrenza(self):
        return RICORRENZE[self.ricorrenza.GetSelection()][0]

    def _giorni_della_ricorrenza(self, giorno):
        """Le voci della scelta del giorno: i nomi dei giorni della settimana, oppure i giorni del mese, da 1 a 28."""
        if self._tipo_della_ricorrenza() == modelli_torneo.SETTIMANALE:
            self.giorno.Set([modelli_torneo.nome_del_giorno(n) for n in range(7)])
            self.giorno.SetSelection(giorno if 0 <= giorno <= 6 else 0)
        else:
            self.giorno.Set([str(n) for n in range(1, 29)])
            self.giorno.SetSelection(giorno - 1 if 1 <= giorno <= 28 else 0)
        self.mese.Enable(self._tipo_della_ricorrenza() == modelli_torneo.ANNUALE)

    def alla_ricorrenza(self, event=None):
        self._giorni_della_ricorrenza(0 if self._tipo_della_ricorrenza() == modelli_torneo.SETTIMANALE else 1)
        self.aggiorna()

    # Il modello dai campi.

    def _formula(self):
        indice = self.formula.GetSelection()
        return self.formule[indice] if 0 <= indice < len(self.formule) else None

    def dati(self):
        """Il modello come lo dicono i campi, come dizionario, senza controllarlo."""
        tipo = TIPI[self.tipo.GetSelection()][0]
        ricorrenza_tipo = self._tipo_della_ricorrenza()
        if ricorrenza_tipo == modelli_torneo.SETTIMANALE:
            ricorrenza = {"tipo": ricorrenza_tipo, "giorno": self.giorno.GetSelection()}
        elif ricorrenza_tipo == modelli_torneo.MENSILE:
            ricorrenza = {"tipo": ricorrenza_tipo, "giorno": self.giorno.GetSelection() + 1}
        else:
            ricorrenza = {"tipo": ricorrenza_tipo, "mese": self.mese.GetSelection() + 1, "giorno": self.giorno.GetSelection() + 1}
        formula = self._formula()
        posti = self.posti.GetValue()
        tetto = formule.tetto(formula) if formula else posti
        if (self.percentuale.GetValue(), posti) == self._partenza[:2]:
            pendenza = self._partenza[2]
        else:
            pendenza = tornei.pendenza_per_prima(self.percentuale.GetValue(), min(posti, tetto))
        return {
            "id": self.modello.id, "nome": self.nome.GetValue().strip(), "note": self.note.GetValue(), "attivo": self.attivo.GetValue(), "tipo": tipo,
            "sesso": SESSI[self.sesso.GetSelection()][0] if tipo == modelli_torneo.INDIVIDUALE else None,
            "formula": formula["id"] if formula else self.modello.formula, "ricorrenza": ricorrenza, "giorni_iscrizione": self.giorni_iscrizione.GetValue(),
            "minimo_iscritti": self.minimo.GetValue(), "set_al_meglio": SET[self.set_al_meglio.GetSelection()], "set_finali": SET[self.set_finali.GetSelection()],
            "finali_da": FINALI_DA[self.finali_da.GetSelection()][0], "incontri_al_giorno": self.turni.GetValue(),
            "importanza": IMPORTANZE[self.importanza.GetSelection()], "quota_iscrizione": self.quota.GetValue(),
            "contributo_federazione": CONTRIBUTI[self.contributo.GetSelection()], "montepremi_minimo": self.montepremi_minimo.GetValue(),
            "posti_premiati": posti, "pendenza_premi": pendenza,
            "qualificazione": QUALIFICAZIONI[self.qualificazione.GetSelection()][0], "classe_minima": CLASSI[self.classe_minima.GetSelection()],
            "classe_massima": CLASSI[self.classe_massima.GetSelection()], "eta_minima": self.eta_minima.GetValue() or None,
            "eta_massima": self.eta_massima.GetValue() or None,
        }

    def aggiorna(self, event=None):
        """Il riepilogo con i campi di adesso: la formula, i giorni, i set, i premi stimati e il denaro nuovo; o il motivo per cui il modello non va."""
        self.sesso.Enable(TIPI[self.tipo.GetSelection()][0] == modelli_torneo.INDIVIDUALE)
        dati = self.dati()
        problema = modelli_torneo.problema_dei_campi(dati)
        if problema:
            testo = f"Così il modello non va: {problema}"
        else:
            modello = modelli_torneo.ModelloTorneo.da_dizionario(dati)
            formula = self._formula()
            testo = " ".join(filter(None, [testi.riepilogo_formula(formula, modello), testi.riepilogo_premi(modello, formula),
                                            modelli_torneo.problema(modello, self.formule) or ""]))
        if self.riepilogo.GetValue() != testo:
            self.riepilogo.ChangeValue(testo)

    def _campo_del_problema(self, problema):
        """Il campo da correggere per il motivo dato, dalle parole del motivo; il nome se non si capisce."""
        parole = problema.casefold()
        for chiave, campo in (("minimo d'iscritti", self.minimo), ("posti premiati", self.posti), ("formula", self.formula), ("giorni d'iscrizione", self.giorni_iscrizione),
                              ("ricorrenza", self.ricorrenza), ("giorno", self.giorno), ("mese", self.mese), ("qualificazione", self.qualificazione),
                              ("classe", self.classe_minima), ("età", self.eta_minima), ("filtri", self.classe_minima), ("squadre", self.tipo),
                              ("sesso", self.sesso), ("quota", self.quota), ("montepremi", self.montepremi_minimo), ("turni", self.turni), ("note", self.note)):
            if chiave in parole:
                return campo
        return self.nome

    def conferma(self, event=None):
        """Salva il modello, se il modulo lo accetta; altrimenti avvisa sul campo da correggere, e il dialogo resta aperto."""
        dati = self.dati()
        problema = self.gestore.problema_nome(dati["nome"], escluso=self.modello.id) or modelli_torneo.problema_dei_campi(dati)
        if problema is None:
            problema = modelli_torneo.problema(modelli_torneo.ModelloTorneo.da_dizionario(dati), self.formule)
        if problema:
            self.avvisa(problema, self._campo_del_problema(problema) if "nome" not in problema.casefold().split(":")[0] else self.nome)
            return
        self.risultato = modelli_torneo.ModelloTorneo.da_dizionario(dati)
        self.chiudi(wx.ID_OK)


class EditorModelli(_Dialogo):
    """
    L'editor dei modelli di torneo, da TournamentEditorDialog di Terminal Beast: l'elenco con sesso,
    ricorrenza e attivo, e i pulsanti Nuovo, Modifica, Duplica, Elimina e Chiudi. I modelli che non si
    leggono si dicono in testa all'apertura, col loro suono. In esiti restano le frasi delle modifiche.
    """

    def __init__(self, genitore, gestore=None):
        super().__init__(genitore, "Editor dei modelli di torneo")
        self.gestore = gestore or modelli_torneo.GestoreModelli()
        self.esiti = []
        self.modelli = []
        self.problemi = self.gestore.problemi()
        self.info = wx.StaticText(self.pannello, label="")
        self.sizer.Add(self.info, 0, wx.ALL, 8)
        self.etichetta("&Modelli")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        nuovo, modifica, duplica, elimina, _chiudi = self.pulsanti((wx.ID_ANY, "&Nuovo"), (wx.ID_ANY, "M&odifica"), (wx.ID_ANY, "&Duplica"),
                                                                 (wx.ID_ANY, "&Elimina"), (wx.ID_CANCEL, "C&hiudi"))
        nuovo.Bind(wx.EVT_BUTTON, self.nuovo)
        modifica.Bind(wx.EVT_BUTTON, self.modifica)
        duplica.Bind(wx.EVT_BUTTON, self.duplica)
        elimina.Bind(wx.EVT_BUTTON, self.elimina)
        self.elenco.Bind(wx.EVT_LISTBOX_DCLICK, self.modifica)
        self.aggiorna(0)
        self.completa((640, 480))
        self.elenco.SetFocus()
        if self.problemi:
            suoni.in_coda("calendario_illeggibile")

    def aggiorna(self, posto=None, id_scelto=None):
        posto = self.elenco.GetSelection() if posto is None else posto
        self.modelli, _scartati = self.gestore.modelli()
        if id_scelto is not None:
            posto = next((i for i, m in enumerate(self.modelli) if m.id == id_scelto), posto)
        testa = f"{testi.conta(len(self.modelli), 'modello', 'modelli')} nella cartella tornei. Cambiano soltanto le edizioni future."
        if self.problemi:
            testa += " " + testi.calendario_illeggibile(self.problemi)
        self.info.SetLabel(testa)
        self._riscrivi(self.elenco, [testi.riga_modello(m) for m in self.modelli] or ["Nessun modello: se ne crea uno con Nuovo."], posto)
        self.pannello.Layout()

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if indice == wx.NOT_FOUND or indice >= len(self.modelli):
            suoni.suona("nessuna_selezione")
            return None
        return self.modelli[indice]

    def _dialogo(self, modello):
        """Il dialogo del modello: il modello salvato, o None se annullato."""
        dialogo = ModelloTorneoDialogo(self, modello, formule.leggi()[0], self.gestore)
        try:
            suoni.suona("dialogo_modello_torneo")
            if dialogo.ShowModal() != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return None
            nuovo = dialogo.risultato
        finally:
            dialogo.Destroy()
        try:
            self.gestore.salva(nuovo)
        except (OSError, ValueError) as errore:
            self.avvisa(f"Il modello non si è potuto salvare: {errore}", self.elenco)
            return None
        suoni.suona("modello_salvato")
        return nuovo

    def nuovo(self, event=None):
        modello = modelli_torneo.ModelloTorneo(id=self.gestore.nuovo_id(), nome="")
        salvato = self._dialogo(modello)
        if salvato is not None:
            self.esiti.append(f"Nuovo modello: {testi.riga_modello(salvato)}.")
            self.aggiorna(id_scelto=salvato.id)
        self.elenco.SetFocus()

    def modifica(self, event=None):
        modello = self._scelto()
        if modello is None:
            return
        salvato = self._dialogo(modello)
        if salvato is not None:
            self.esiti.append(f"Modello cambiato: {testi.riga_modello(salvato)}.")
            self.aggiorna(id_scelto=salvato.id)
        self.elenco.SetFocus()

    def duplica(self, event=None):
        modello = self._scelto()
        if modello is None:
            return
        try:
            copia = self.gestore.duplica(modello.id)
        except (OSError, ValueError) as errore:
            self.avvisa(f"Il modello non si è potuto duplicare: {errore}", self.elenco)
            return
        suoni.suona("modello_duplicato")
        self.esiti.append(f"Modello duplicato: {copia.nome}, fermo finché non lo modifichi." if not copia.attivo else f"Modello duplicato: {copia.nome}.")
        self.aggiorna(id_scelto=copia.id)
        self.elenco.SetFocus()

    def elimina(self, event=None):
        modello = self._scelto()
        if modello is None:
            return
        if not self._conferma(f"Eliminare il modello {modello.nome}? Le edizioni già aperte restano, le future no."):
            self.elenco.SetFocus()
            return
        try:
            self.gestore.elimina(modello.id)
        except (OSError, ValueError) as errore:
            self.avvisa(f"Il modello non si è potuto eliminare: {errore}", self.elenco)
            return
        suoni.suona("modello_eliminato")
        self.esiti.append(f"Modello eliminato: {modello.nome}.")
        self.aggiorna()
        self.elenco.SetFocus()


class FaseDialogo(_Dialogo):
    """
    Una fase di una formula, da PhaseConfigDialog di Terminal Beast: il tipo, i partecipanti, bloccati
    dopo la prima fase al numero che arriva dalla precedente, i gironi, i promossi per girone e la
    finalina, soltanto per il tabellone da 4. La validazione è quella del modulo delle formule; il
    dialogo dice il motivo sul campo e resta aperto. In risultato resta la fase.
    """

    def __init__(self, genitore, fase, indice, ultima, bloccati=None):
        super().__init__(genitore, f"Fase {indice + 1}")
        self.indice = indice
        self.ultima = ultima
        self.bloccati = bloccati
        self.risultato = None
        self.etichetta("&Tipo")
        self.tipo = self.aggiungi(wx.Choice(self.pannello, choices=["Gironi", "Tabellone, eliminazione diretta"]))
        self.tipo.SetSelection(0 if fase["tipo"] == formule.GIRONI else 1)
        self.etichetta("&Partecipanti" + (", arrivano dalla fase prima" if bloccati is not None else ""))
        self.partecipanti = self.aggiungi(wx.SpinCtrl(self.pannello, min=formule.PARTECIPANTI_MINIMI, max=formule.PARTECIPANTI_MASSIMI,
                                                      initial=bloccati if bloccati is not None else fase["partecipanti"]))
        self.partecipanti.Enable(bloccati is None)
        self.etichetta("&Gironi")
        self.gironi = self.aggiungi(wx.SpinCtrl(self.pannello, min=1, max=formule.PARTECIPANTI_MASSIMI // formule.COMPONENTI_MINIMI, initial=max(1, fase["gironi"])))
        self.etichetta("P&romossi per girone")
        self.promossi = self.aggiungi(wx.SpinCtrl(self.pannello, min=0, max=formule.COMPONENTI_MASSIMI - 1, initial=fase["promossi"]))
        self.finalina = self.aggiungi(wx.CheckBox(self.pannello, label="&Finalina per il terzo posto, soltanto nel tabellone da 4"))
        self.finalina.SetValue(fase["finalina"])
        ok, _annulla = self.pulsanti((wx.ID_OK, "&OK"), (wx.ID_CANCEL, "Annulla"))
        ok.Bind(wx.EVT_BUTTON, self.conferma)
        self.tipo.Bind(wx.EVT_CHOICE, self.aggiorna)
        self.partecipanti.Bind(wx.EVT_SPINCTRL, self.aggiorna)
        self.partecipanti.Bind(wx.EVT_TEXT, self.aggiorna)
        self.aggiorna()
        self.completa((480, 380))
        self.tipo.SetFocus()

    def fase(self):
        gironi = self.tipo.GetSelection() == 0
        return {"tipo": formule.GIRONI if gironi else formule.TABELLONE, "partecipanti": self.partecipanti.GetValue(),
                "gironi": self.gironi.GetValue() if gironi else 0, "promossi": self.promossi.GetValue() if gironi else 0,
                "finalina": bool(self.finalina.GetValue()) and not gironi and self.partecipanti.GetValue() == formule.PARTECIPANTI_FINALINA}

    def aggiorna(self, event=None):
        """Gironi e promossi valgono per i gironi, la finalina soltanto per il tabellone da 4."""
        gironi = self.tipo.GetSelection() == 0
        self.gironi.Enable(gironi)
        self.promossi.Enable(gironi)
        self.finalina.Enable(not gironi and self.partecipanti.GetValue() == formule.PARTECIPANTI_FINALINA)

    def conferma(self, event=None):
        fase = self.fase()
        problema = formule.valida_fase(fase, self.indice, self.ultima)
        if problema:
            parole = problema.casefold()
            campo = self.promossi if "promossi" in parole else self.gironi if "giron" in parole else self.finalina if "finalina" in parole else self.partecipanti
            self.avvisa(problema, campo if campo.IsEnabled() else self.tipo)
            return
        self.risultato = fase
        self.chiudi(wx.ID_OK)


class EditorFormule(_Dialogo):
    """
    L'editor delle formule, da FormulaEditorDialog di Terminal Beast: la formula in una scelta, il nome,
    la descrizione, le fasi in un elenco, i pulsanti Nuova formula, Elimina formula, Aggiungi fase,
    Modifica fase, Togli fase, Salva e Chiudi, e lo stato, che dice formula valida o il motivo. Salva
    scrive il file delle formule e non chiude il dialogo; una formula che dei modelli usano non si
    elimina, e l'avviso dice quali. In esiti restano le frasi delle modifiche salvate.
    """

    def __init__(self, genitore, gestore=None):
        super().__init__(genitore, "Editor delle formule")
        self.gestore = gestore or modelli_torneo.GestoreModelli()
        self.esiti = []
        self.formule, _scartate = formule.leggi()
        self.salvate = {f["id"] for f in self.formule}
        self.modificata = False
        self.etichetta("&Formula")
        self.scelta = self.aggiungi(wx.Choice(self.pannello))
        self.etichetta("&Nome")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello))
        self.etichetta("&Descrizione")
        self.descrizione = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE))
        self.etichetta("F&asi")
        self.fasi = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.etichetta("S&tato della formula")
        self.stato = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
        nuova, elimina, aggiungi = self.pulsanti((wx.ID_ANY, "N&uova formula"), (wx.ID_ANY, "&Elimina formula"), (wx.ID_ANY, "A&ggiungi fase"))
        modifica, togli, salva, _chiudi = self.pulsanti((wx.ID_ANY, "&Modifica fase"), (wx.ID_ANY, "T&ogli fase"), (wx.ID_ANY, "&Salva"),
                                                        (wx.ID_CANCEL, "C&hiudi"), predefinito=False)
        nuova.Bind(wx.EVT_BUTTON, self.nuova)
        elimina.Bind(wx.EVT_BUTTON, self.elimina)
        aggiungi.Bind(wx.EVT_BUTTON, self.aggiungi_fase)
        modifica.Bind(wx.EVT_BUTTON, self.modifica_fase)
        togli.Bind(wx.EVT_BUTTON, self.togli_fase)
        salva.Bind(wx.EVT_BUTTON, self.salva)
        self.Bind(wx.EVT_BUTTON, self.chiudi_editor, id=wx.ID_CANCEL)
        self.scelta.Bind(wx.EVT_CHOICE, lambda event: self.alla_formula())
        self.nome.Bind(wx.EVT_TEXT, self.al_nome)
        self.descrizione.Bind(wx.EVT_TEXT, self.alla_descrizione)
        self.fasi.Bind(wx.EVT_LISTBOX_DCLICK, self.modifica_fase)
        self._riempi_scelta(0)
        self.completa((600, 560))
        self.scelta.SetFocus()

    # La formula di adesso.

    def _riempi_scelta(self, posto):
        self.scelta.Set([f["nome"] or "formula senza nome" for f in self.formule] or ["nessuna formula: se ne crea una con Nuova formula"])
        self.scelta.SetSelection(max(0, min(posto, self.scelta.GetCount() - 1)))
        self.alla_formula()

    def corrente(self):
        indice = self.scelta.GetSelection()
        return self.formule[indice] if 0 <= indice < len(self.formule) else None

    def alla_formula(self, posto=0):
        f = self.corrente()
        self.nome.ChangeValue(f["nome"] if f else "")
        self.descrizione.ChangeValue(f["descrizione"] if f else "")
        self.aggiorna_fasi(posto)

    def aggiorna_fasi(self, posto=None):
        f = self.corrente()
        posto = self.fasi.GetSelection() if posto is None else posto
        righe = [testi.riga_fase(fase, i) for i, fase in enumerate(f["fasi"])] if f else []
        self._riscrivi(self.fasi, righe or ["Nessuna fase: si aggiunge con Aggiungi fase."], posto)
        self.aggiorna_stato()

    def aggiorna_stato(self):
        f = self.corrente()
        if f is None:
            testo = "Nessuna formula scelta."
        else:
            problema = formule.valida_formula(f)
            testo = "Formula valida." if problema is None else f"Formula non valida: {problema}"
            if f["id"] not in self.salvate:
                testo += " Non è ancora salvata."
        if self.stato.GetValue() != testo:
            self.stato.ChangeValue(testo)

    def al_nome(self, event=None):
        f = self.corrente()
        if f is None:
            return
        f["nome"] = self.nome.GetValue().strip()
        self.scelta.SetString(self.scelta.GetSelection(), f["nome"] or "formula senza nome")
        self.modificata = True
        self.aggiorna_stato()

    def alla_descrizione(self, event=None):
        f = self.corrente()
        if f is None:
            return
        f["descrizione"] = self.descrizione.GetValue().strip()
        self.modificata = True
        self.aggiorna_stato()

    # Le formule.

    def nuova(self, event=None):
        """Una formula nuova, ancora da salvare: un girone unico da 8, da cambiare."""
        nuova = {"id": formule.nuovo_id(self.formule), "nome": "Nuova formula", "descrizione": "",
                 "fasi": [{"tipo": formule.GIRONI, "partecipanti": 8, "gironi": 1, "promossi": 0, "finalina": False}]}
        self.formule.append(nuova)
        self.modificata = True
        self._riempi_scelta(len(self.formule) - 1)
        suoni.suona("formula_nuova")
        self.nome.SetFocus()
        self.nome.SelectAll()

    def elimina(self, event=None):
        f = self.corrente()
        if f is None:
            suoni.suona("nessuna_selezione")
            return
        modelli, _scartati = self.gestore.modelli()
        usata = formule.in_uso(f["id"], modelli)
        if usata:
            self.avvisa(f"La formula {f['nome']} è usata da {testi.conta(len(usata), 'modello', 'modelli')}: {', '.join(usata)}. Prima si cambia la loro formula.",
                        self.scelta, "formula_in_uso")
            return
        if not self._conferma(f"Eliminare la formula {f['nome']}?"):
            self.scelta.SetFocus()
            return
        if f["id"] in self.salvate:
            try:
                formule.elimina(f["id"], modelli)
            except (OSError, ValueError) as errore:
                self.avvisa(str(errore), self.scelta, "formula_in_uso")
                return
            self.salvate.discard(f["id"])
        posto = self.scelta.GetSelection()
        self.formule.remove(f)
        suoni.suona("formula_eliminata")
        self.esiti.append(f"Formula eliminata: {f['nome']}.")
        self._riempi_scelta(posto)
        self.scelta.SetFocus()

    def salva(self, event=None):
        """Scrive il file con le formule valide, se quella di adesso lo è; altrimenti dice perché. Il dialogo resta aperto."""
        f = self.corrente()
        if f is None:
            suoni.suona("nessuna_selezione")
            return
        problema = formule.valida_formula(f)
        if problema:
            self.avvisa(problema, self.fasi, "formula_non_valida")
            return
        valide = [x for x in self.formule if formule.valida_formula(x) is None]
        try:
            formule.scrivi(valide)
        except (OSError, ValueError) as errore:
            self.avvisa(f"Le formule non si sono potute salvare: {errore}", self.scelta, "formula_non_valida")
            return
        self.salvate = {x["id"] for x in valide}
        self.modificata = any(x["id"] not in self.salvate for x in self.formule)
        suoni.suona("formula_salvata")
        self.esiti.append(f"Formula salvata: {f['nome']}, " + "; ".join(testi.riga_fase(fase, i) for i, fase in enumerate(f["fasi"])) + ".")
        self.aggiorna_stato()

    # Le fasi.

    def _dialogo_fase(self, fase, indice, ultima, bloccati):
        dialogo = FaseDialogo(self, fase, indice, ultima, bloccati)
        try:
            suoni.suona("dialogo_fase")
            if dialogo.ShowModal() != wx.ID_OK or dialogo.risultato is None:
                suoni.suona("annullato")
                return None
            return dialogo.risultato
        finally:
            dialogo.Destroy()

    def aggiungi_fase(self, event=None):
        f = self.corrente()
        if f is None:
            suoni.suona("nessuna_selezione")
            return
        if len(f["fasi"]) >= formule.FASI_MASSIME:
            self.avvisa(f"Una formula ha al massimo {formule.FASI_MASSIME} fasi.", self.fasi, "formula_non_valida")
            return
        bloccati = formule.partecipanti_dopo(f["fasi"][-1]) if f["fasi"] else None
        if bloccati is not None and bloccati < formule.PARTECIPANTI_MINIMI:
            self.avvisa("La fase prima non promuove abbastanza giocatori per un'altra fase: prima si cambiano i suoi promossi, con Modifica fase.",
                        self.fasi, "formula_non_valida")
            return
        tipo = formule.TABELLONE if bloccati is not None and formule.potenza_di_due(bloccati) else formule.GIRONI
        proposta = {"tipo": tipo, "partecipanti": bloccati or 8, "gironi": 1 if tipo == formule.GIRONI else 0, "promossi": 0, "finalina": False}
        fase = self._dialogo_fase(proposta, len(f["fasi"]), True, bloccati)
        if fase is None:
            return
        f["fasi"].append(fase)
        self.modificata = True
        suoni.suona("fase_aggiunta")
        self.aggiorna_fasi(len(f["fasi"]) - 1)
        self.fasi.SetFocus()

    def _fase_scelta(self):
        f = self.corrente()
        indice = self.fasi.GetSelection()
        if f is None or indice == wx.NOT_FOUND or indice >= len(f["fasi"]):
            suoni.suona("nessuna_selezione")
            return None, None
        return f, indice

    def modifica_fase(self, event=None):
        f, indice = self._fase_scelta()
        if f is None:
            return
        bloccati = formule.partecipanti_dopo(f["fasi"][indice - 1]) if indice > 0 else None
        fase = self._dialogo_fase(dict(f["fasi"][indice]), indice, indice == len(f["fasi"]) - 1, bloccati)
        if fase is None:
            return
        f["fasi"][indice] = fase
        # Come _update_phases_cascade di Terminal Beast: le fasi che seguono prendono i partecipanti dalla precedente.
        formule.aggiorna_cascata(f["fasi"], indice)
        self.modificata = True
        suoni.suona("fase_modificata")
        self.aggiorna_fasi(indice)
        self.fasi.SetFocus()

    def togli_fase(self, event=None):
        f, indice = self._fase_scelta()
        if f is None:
            return
        del f["fasi"][indice]
        if indice > 0:
            formule.aggiorna_cascata(f["fasi"], indice - 1)
        self.modificata = True
        suoni.suona("fase_tolta")
        self.aggiorna_fasi(max(0, indice - 1))
        self.fasi.SetFocus()

    def chiudi_editor(self, event=None):
        """Chiude, ma prima chiede se ci sono formule cambiate e non salvate, col no già scelto."""
        if self.modificata and not self._conferma("Ci sono formule cambiate e non salvate: chiudere lo stesso e perderle?"):
            self.scelta.SetFocus()
            return
        self.chiudi(wx.ID_CANCEL)
