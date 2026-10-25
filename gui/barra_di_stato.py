"""
La finestra della barra di stato su misura di MESS, voce Barra di stato del menu Impostazioni.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-25 con la decisione D38, idea di Gabriele del 24 ottobre, sul modello dei criteri di spareggio di
Tornello, src/gui/dialogs/tiebreak_config_dialog.py, che con NVDA funziona perfettamente. La scelta Riga, da una a
sedici, con Aggiungi riga e Togli riga; l'elenco Dati disponibili, coi soli dati che nessuna riga usa, perché ogni dato
compare una volta sola nella barra, nell'ordine del catalogo; sotto, la spiegazione del dato su cui sei, con l'esempio e
il suo testo di adesso; l'elenco Dati della riga, nel loro ordine, con Sposta su e Sposta giù; l'anteprima della riga,
come sarebbe adesso; Barra di serie, che rimette la barra di partenza, Salva e Annulla. Invio o Spazio sposta il dato su
cui sei da un elenco all'altro, Canc lo toglie dalla riga. Non c'è un pulsante predefinito: Invio fa soltanto quello
che fa sull'elenco, e Salva si preme. Ogni evento ha il suo suono. Le chiavi che questo MESS non conosce, scritte da un
MESS più nuovo, non si vedono ma restano nella loro riga, in fondo, finché la riga c'è.
Lo stesso giorno, dal collaudo di Gabriele, il giro del Tab segue il lavoro: la scelta Riga con Aggiungi riga e Togli
riga, i Dati della riga, la spiegazione, Sposta su e Sposta giù, i Dati disponibili, l'anteprima e i pulsanti della
barra; il fuoco parte dalla scelta Riga. Un elenco vuoto non è disponibile, così esce dal giro del Tab, dove NVDA lo
diceva sconosciuto; se aveva il fuoco, il fuoco va all'altro elenco, o alla scelta Riga se sono vuoti tutti e due. È di
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import wx

import barra as modulo_barra
import suoni
from gui import aspetto
from gui.dialoghi import RIPETIZIONE_IGNORATA, _adesso, _Dialogo, controllo_col_fuoco

INVIO = (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER)
CANC = (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE)


class BarraDiStato(_Dialogo):
    """La barra di stato su misura, D38. In risultato resta la barra scelta, una lista di righe di chiavi, al Salva."""

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, impostazioni, contesto):
        super().__init__(genitore, "Barra di stato")
        self.impostazioni = impostazioni
        # Una funzione che dà il contesto di adesso, per la spiegazione e l'anteprima.
        self.contesto = contesto
        self.risultato = None
        self._ultimo_canc = 0.0
        self._carica(impostazioni["barra_di_stato"])
        self.sizer.Add(wx.StaticText(self.pannello, label=modulo_barra.SPIEGAZIONE_DELLA_FINESTRA), 0, wx.ALL, 8)
        self.etichetta("&Riga")
        self.scelta_riga = self.aggiungi(wx.Choice(self.pannello))
        self.scelta_riga.SetName("Riga")
        self.pulsante_aggiungi_riga, self.pulsante_togli_riga = self.pulsanti((wx.ID_ANY, "&Aggiungi riga"), (wx.ID_ANY, "&Togli riga"), predefinito=False)
        # L'ordine dei controlli è quello del Tab, scelto da Gabriele il 25 ottobre 2026.
        self.etichetta("Dati de&lla riga")
        self.della_riga = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.della_riga.SetName("Dati della riga")
        self.etichetta("S&piegazione del dato")
        self.spiegazione = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
        self.spiegazione.SetName("Spiegazione del dato")
        self.pulsante_su, self.pulsante_giu = self.pulsanti((wx.ID_ANY, "Sposta s&u"), (wx.ID_ANY, "Sposta &giù"), predefinito=False)
        self.etichetta("&Dati disponibili")
        self.disponibili = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.disponibili.SetName("Dati disponibili")
        self.etichetta("Ant&eprima della riga")
        self.anteprima = self.aggiungi(wx.TextCtrl(self.pannello, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP))
        self.anteprima.SetName("Anteprima della riga")
        self.pulsante_di_serie, self.pulsante_salva, _annulla = self.pulsanti((wx.ID_ANY, "&Barra di serie"), (wx.ID_ANY, "&Salva"),
                                                                             (wx.ID_CANCEL, "Annulla"), predefinito=False)
        for campo in (self.spiegazione, self.anteprima):
            campo.SetMinSize((-1, campo.GetCharHeight() * 4))
            aspetto.applica(campo, impostazioni)
        self.scelta_riga.Bind(wx.EVT_CHOICE, self._alla_riga)
        self.disponibili.Bind(wx.EVT_LISTBOX, lambda event: self._spiega_la_scelta(self.disponibili))
        self.della_riga.Bind(wx.EVT_LISTBOX, lambda event: self._spiega_la_scelta(self.della_riga))
        self.disponibili.Bind(wx.EVT_SET_FOCUS, self._al_fuoco_di_un_elenco)
        self.della_riga.Bind(wx.EVT_SET_FOCUS, self._al_fuoco_di_un_elenco)
        self.disponibili.Bind(wx.EVT_LISTBOX_DCLICK, lambda event: self.aggiungi_dato())
        self.della_riga.Bind(wx.EVT_LISTBOX_DCLICK, lambda event: self.togli_dato())
        self.pulsante_aggiungi_riga.Bind(wx.EVT_BUTTON, lambda event: self.aggiungi_riga())
        self.pulsante_togli_riga.Bind(wx.EVT_BUTTON, lambda event: self.togli_riga())
        self.pulsante_su.Bind(wx.EVT_BUTTON, lambda event: self.sposta(-1))
        self.pulsante_giu.Bind(wx.EVT_BUTTON, lambda event: self.sposta(1))
        self.pulsante_di_serie.Bind(wx.EVT_BUTTON, lambda event: self.barra_di_serie())
        self.pulsante_salva.Bind(wx.EVT_BUTTON, lambda event: self.salva())
        # Il gancio dei tasti prima di completa: quello della grazia dell'Invio, legato dopo, wx lo chiama per primo.
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.completa((640, 600))
        self._scrivi(0, 0, 0)
        self._spiega_la_scelta(self.della_riga if self.della_riga.GetCount() else self.disponibili)
        wx.CallAfter(self._al_primo_controllo)

    def _al_primo_controllo(self):
        if self:
            self.scelta_riga.SetFocus()

    # Il modello: le righe coi dati noti, e a parte le chiavi che questo MESS non conosce.

    def _carica(self, barra_scelta):
        self.righe = [[chiave for chiave in riga if chiave in modulo_barra.CATALOGO] for riga in barra_scelta] or [[]]
        self.ignote = [[chiave for chiave in riga if chiave not in modulo_barra.CATALOGO] for riga in barra_scelta] or [[]]
        self.riga = 0

    def chiavi_disponibili(self):
        """I dati che nessuna riga usa, nell'ordine del catalogo."""
        usate = {chiave for riga in self.righe for chiave in riga}
        return [chiave for chiave in modulo_barra.CATALOGO if chiave not in usate]

    def barra_scelta(self):
        """La barra come la salverebbe Salva: ogni riga coi suoi dati, e in fondo le chiavi che questo MESS non conosce."""
        return [riga + ignote for riga, ignote in zip(self.righe, self.ignote, strict=True)]

    # La scrittura dei controlli.

    def _scrivi(self, riga, posto_disponibili=None, posto_della_riga=None):
        """La scelta Riga, i due elenchi e l'anteprima, sulla riga data, con le scelte ai posti dati o dove erano."""
        self.riga = min(max(riga, 0), len(self.righe) - 1)
        voci = [f"Riga {numero}, {modulo_barra.conta_dati(len(dati))}" for numero, dati in enumerate(self.righe, start=1)]
        if self.scelta_riga.GetItems() != voci:
            self.scelta_riga.Set(voci)
        self.scelta_riga.SetSelection(self.riga)
        if posto_disponibili is None:
            posto_disponibili = self.disponibili.GetSelection()
        if posto_della_riga is None:
            posto_della_riga = self.della_riga.GetSelection()
        self._riscrivi(self.disponibili, [modulo_barra.CATALOGO[k].etichetta for k in self.chiavi_disponibili()], posto_disponibili)
        self._riscrivi(self.della_riga, [modulo_barra.CATALOGO[k].etichetta for k in self.righe[self.riga]], posto_della_riga)
        self.anteprima.ChangeValue(modulo_barra.anteprima(self.righe[self.riga], self.contesto()))
        aspetto.ridai_stile(self.anteprima, self.impostazioni)
        self._elenchi_vuoti_fuori_dal_giro()

    @staticmethod
    def _stesso(primo, secondo):
        return primo is not None and (primo is secondo or primo.GetId() == secondo.GetId())

    def _elenchi_vuoti_fuori_dal_giro(self):
        """
        Un elenco vuoto non è disponibile, ed esce dal giro del Tab: NVDA lo diceva sconosciuto. Se aveva il fuoco, il fuoco
        va all'altro elenco, se ha dei dati, altrimenti alla scelta Riga; prima si riaccendono gli elenchi che hanno dati.
        """
        elenchi = (self.della_riga, self.disponibili)
        for elenco in elenchi:
            if elenco.GetCount() and not elenco.IsEnabled():
                elenco.Enable()
        fuoco = controllo_col_fuoco()
        for elenco, altro in (elenchi, tuple(reversed(elenchi))):
            if not elenco.GetCount() and self._stesso(fuoco, elenco):
                (altro if altro.GetCount() else self.scelta_riga).SetFocus()
        for elenco in elenchi:
            if not elenco.GetCount() and elenco.IsEnabled():
                elenco.Disable()

    def _spiega(self, chiave):
        self.spiegazione.ChangeValue(modulo_barra.spiegazione(chiave, self.contesto()) if chiave else "Nessun dato.")
        aspetto.ridai_stile(self.spiegazione, self.impostazioni)

    def _chiave_scelta(self, elenco):
        """La chiave del dato scelto nell'elenco dato, o None."""
        chiavi = self.chiavi_disponibili() if elenco is self.disponibili else self.righe[self.riga]
        posto = elenco.GetSelection()
        return chiavi[posto] if posto != wx.NOT_FOUND and posto < len(chiavi) else None

    def _spiega_la_scelta(self, elenco):
        self._spiega(self._chiave_scelta(elenco))

    def _al_fuoco_di_un_elenco(self, event):
        """Quando un elenco prende il fuoco, sceglie la prima voce se non ce n'è una e la spiega, come in Tornello."""
        elenco = event.GetEventObject()
        if elenco.GetCount() and elenco.GetSelection() == wx.NOT_FOUND:
            elenco.SetSelection(0)
        self._spiega_la_scelta(elenco)
        event.Skip()

    def _alla_riga(self, event):
        self._scrivi(self.scelta_riga.GetSelection(), posto_della_riga=0)

    # I tasti.

    def _tasto(self, event):
        """
        Invio o Spazio su Dati disponibili aggiunge il dato alla riga, su Dati della riga lo toglie; Canc lo toglie. Uno
        Spazio tenuto giù si ignora, e così un Canc tenuto giù o un secondo Canc entro mezzo secondo. Gli altri tasti
        proseguono: Invio fuori dagli elenchi non fa niente, perché non c'è un pulsante predefinito.
        """
        codice = event.GetKeyCode()
        fuoco = controllo_col_fuoco()
        spazio = codice == wx.WXK_SPACE and not event.IsAutoRepeat()
        if event.HasAnyModifiers() or fuoco not in (self.disponibili, self.della_riga):
            event.Skip()
        elif codice in INVIO or spazio:
            if fuoco is self.disponibili:
                self.aggiungi_dato()
            else:
                self.togli_dato()
        elif codice == wx.WXK_SPACE:
            return
        elif codice in CANC and fuoco is self.della_riga:
            adesso = _adesso()
            precedente, self._ultimo_canc = self._ultimo_canc, adesso
            if not event.IsAutoRepeat() and adesso - precedente >= RIPETIZIONE_IGNORATA:
                self.togli_dato()
        else:
            event.Skip()

    # Le azioni.

    def aggiungi_dato(self):
        """Il dato scelto fra i disponibili va in fondo alla riga; la scelta resta allo stesso posto, sul dato che segue."""
        chiave = self._chiave_scelta(self.disponibili)
        if chiave is None:
            suoni.suona("nessuna_selezione")
            return
        posto = self.disponibili.GetSelection()
        self.righe[self.riga].append(chiave)
        suoni.suona("barra_dato_aggiunto")
        self._scrivi(self.riga, posto, len(self.righe[self.riga]) - 1)
        # Coi disponibili finiti il fuoco è passato ai dati della riga, sull'ultimo aggiunto.
        self._spiega_la_scelta(self.disponibili if self.disponibili.GetCount() else self.della_riga)

    def togli_dato(self):
        """Il dato scelto della riga torna fra i disponibili, al suo posto nel catalogo; a riga vuota il fuoco va ai disponibili."""
        chiave = self._chiave_scelta(self.della_riga)
        if chiave is None:
            suoni.suona("nessuna_selezione")
            return
        posto = self.della_riga.GetSelection()
        self.righe[self.riga].remove(chiave)
        suoni.suona("barra_dato_tolto")
        self._scrivi(self.riga, self.chiavi_disponibili().index(chiave), posto)
        # A riga vuota il fuoco è passato ai disponibili, sul dato appena tolto.
        self._spiega_la_scelta(self.della_riga if self.righe[self.riga] else self.disponibili)

    def sposta(self, verso):
        """Sposta su, con verso -1, e Sposta giù, con 1: il dato scelto della riga cambia posto col vicino."""
        chiave = self._chiave_scelta(self.della_riga)
        if chiave is None:
            suoni.suona("nessuna_selezione")
            return
        dati = self.righe[self.riga]
        posto = dati.index(chiave)
        nuovo = posto + verso
        if not 0 <= nuovo < len(dati):
            suoni.suona("barra_dato_al_bordo")
            return
        dati[posto], dati[nuovo] = dati[nuovo], dati[posto]
        suoni.suona("barra_dato_su" if verso < 0 else "barra_dato_giu")
        self._scrivi(self.riga, posto_della_riga=nuovo)

    def aggiungi_riga(self):
        """Una riga vuota dopo quella scelta, che diventa la scelta; oltre le sedici righe no, e un avviso lo dice."""
        if len(self.righe) >= modulo_barra.RIGHE_MASSIME:
            self.avvisa(f"La barra ha già {modulo_barra.RIGHE_MASSIME} righe, il massimo.", self.pulsante_aggiungi_riga, "barra_righe_piene")
            return
        self.righe.insert(self.riga + 1, [])
        self.ignote.insert(self.riga + 1, [])
        suoni.suona("barra_riga_aggiunta")
        self._scrivi(self.riga + 1, posto_della_riga=0)

    def togli_riga(self):
        """La riga scelta se ne va, coi suoi dati, che tornano disponibili; l'ultima riga rimasta no, e un avviso lo dice."""
        if len(self.righe) == 1:
            self.avvisa("La barra ha una riga sola: si può svuotare, ma non togliere.", self.pulsante_togli_riga, "barra_riga_sola")
            return
        del self.righe[self.riga]
        del self.ignote[self.riga]
        suoni.suona("barra_riga_tolta")
        self._scrivi(self.riga, posto_della_riga=0)

    def barra_di_serie(self):
        """Rimette la barra di serie, al posto di quella che si sta preparando; si salva soltanto con Salva."""
        self._carica(modulo_barra.BARRA_DI_SERIE)
        suoni.suona("barra_di_serie_rimessa")
        self._scrivi(0, 0, 0)

    def salva(self):
        self.risultato = self.barra_scelta()
        self.chiudi(wx.ID_OK)
