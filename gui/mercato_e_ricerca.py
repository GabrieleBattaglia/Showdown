"""
La finestra Mercato e ricerca di MESS, issue 8 e decisione D36.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 col progetto corretto dal critico e le scelte di Gabriele dello stesso giorno: il mercato dei
giocatori, quello degli allenatori, la ricerca e la scelta dell'avversario dell'amichevole diventano una finestra
sola, che si apre massimizzata da ogni porta d'ingresso con il suo ultimo preset, ed Esc la chiude.
Le schede sono native, wx.Notebook, e si cambiano con Ctrl+Tab e Ctrl+Maiusc+Tab, ognuna col suo suono: Risultati,
con la Situazione, la casella dei preset, l'elenco virtuale dei trovati, la scheda della persona in un campo di sola
lettura su più righe e i pulsanti delle azioni; Filtri, coi filtri più usati, Filtri attivi e Salva filtri; Altri
filtri; e Filtri degli allenatori. Le ultime due dicono nella linguetta quanti dei loro filtri sono impostati. Ogni
controllo ha la sua lettera, e le lettere si ripetono da una scheda all'altra, perché Windows le cerca soltanto fra i
controlli visibili; Chiudi, fuori dalle schede, ha la C in tutte. Il passo della finestra ha misurato su wx, sul
desktop nascosto, che Ctrl+Tab cambia scheda da ogni controllo e porta il fuoco nella pagina nuova, che Alt+C
arriva a Chiudi anche da dentro una pagina, da un riquadro e dalla linguetta, e che le lettere di una scheda nascosta
non fanno niente: per questo il gancio dei tasti non li prende.
La casella dei preset ha in cima la voce Filtri attuali, non salvati, poi i preset di Gabriele, poi i dodici preset
di serie, e per ultima Salva filtri..., che si apre con Invio, o scegliendola dall'elenco aperto, mai con le frecce:
scorrendo la casella chiusa ogni preset si applica intero. Un cambio a mano di un filtro porta la casella, in
silenzio, sulla voce in cima, che tiene i filtri fatti a mano. I preset si salvano, si rinominano, si eliminano e si
spostano, e ogni operazione passa subito nel mondo e fra gli esiti della finestra, che alla chiusura la vista
racconta e il mondo salva.
L'elenco si ricalcola 350 millesimi dopo l'ultimo tasto in un campo, in un numero o in una scelta, e subito per le
caselle e i pulsanti; il numero dei trovati arriva alla voce e al display, con gli annunci della cronaca anche se la
loro lettura è spenta, 1000 millesimi dopo l'ultimo tasto. La scheda della persona segue la riga scelta, e Invio
sull'elenco porta lì; Invio ed Esc nella scheda tornano all'elenco, sulla stessa riga.
Un Invio che arriva entro la grazia dall'apertura, dall'Invio di prima o dalla fine di un dialogo interno si mangia,
perché NVDA rimanda Invio come pressioni nuove; e la pressione di un pulsante entro mezzo secondo dalla sua pressione
di prima, o dalla fine di un dialogo interno, si ignora: il passo della finestra ha misurato che il gancio dei tasti
non arriva alla finestra da un pulsante. Le domande, gli esiti e gli avvisi della finestra si leggono in un campo dove si scorre
col cursore, non in un messaggio di Windows: le domande hanno Sì e No, col No già scelto; il lancio della sfida e la cifra, dialoghi
di tutto il gioco, tengono i loro messaggi brevi. A mosse finite si oscura soltanto l'offerta, e
Alt+O sulla scheda Risultati dice il perché col suo suono. L'amichevole si gioca scegliendo prima l'avversario qui, poi
il proprio giocatore: la finestra si chiude e la partita la gioca la finestra principale. Assumi dello staff apre sugli
allenatori liberi col posto già scelto, e non ricorda niente.
Coi collegamenti dello stesso giorno la aprono Ctrl+K, Ctrl+Maiusc+G, Ctrl+F e Ctrl+O della finestra principale e Assumi
dello staff, e chi la apre ne prende gli esiti con esiti_alla_fine, anche quando a chiuderla è stata la chiusura per
l'aggiornamento, che chiude i dialoghi aperti: la porta si ricorda lo stesso.
Dalle verifiche dello stesso giorno: ogni scheda è un riquadro col testo della sua linguetta, conto dei filtri compreso,
perché NVDA, che delle pagine di wx non dice niente, lo dica quando il fuoco ci entra con Ctrl+Tab; l'elenco che prende
il fuoco mentre un ricalcolo aspetta si rifà subito, prima che NVDA ne legga il nome e le righe, e lo stesso fa ogni
dialogo interno, che ferma anche l'annuncio dei trovati, perché non arrivi sopra il dialogo; la casella dei preset
lasciata su Salva filtri dall'elenco aperto torna sulla voce applicata; la Situazione resta su una riga sola, senza
andare a capo a metà di un blocco di quaranta caratteri; anche all'apertura la scheda della persona si scrive col suo
rimando; i suoni dell'apertura messi in fila si fermano alla chiusura; l'amichevole contro l'unico tuo giocatore che
oggi gioca dice che serve un altro avversario, invece di dire che non gioca nessuno; i massimi dei numeri dei filtri
vengono dal motore, che li controlla anche nella lettura. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5,
UltraCode).
"""

import contextlib
import ctypes
import dataclasses
from ctypes import wintypes

import wx

import impostazioni as modulo_impostazioni
import luoghi
import mercato
import ricerca
import staff
import suoni
import testi
from classe import LIVELLI
from classe import codice as codice_della_classe
from costanti import INDOLI
from gui import aspetto, dialoghi
from gui.dal_vivo import annunci_condivisi
from gui.dialoghi import Cifra, Lettura, OpzioniAmichevole, SceltaGiocatore, _Dialogo, _SceltaConTesto
from gui.elenco_virtuale import ElencoVirtuale
from gui.sfide import LanciaSfida
from modelli import probabilita_accettazione
from utilita import adesso_utc

# I ritardi della finestra, in secondi: il ricalcolo dopo l'ultimo tasto, quello dei dialoghi di MESS; l'annuncio dei
# trovati, scelta di Gabriele dopo la prova del prototipo; la scheda che segue la riga; il suono di un numero o di un
# testo quando ci si ferma.
RITARDO_DEL_RICALCOLO = dialoghi.RITARDO_DEL_SUONO_AL_VOLO / 1000
RITARDO_DELL_ANNUNCIO = 1.0
RITARDO_DELLA_SCHEDA = dialoghi.RITARDO_DEL_SUONO_AL_VOLO / 1000
RITARDO_DEL_SUONO = dialoghi.RITARDO_DEL_SUONO_AL_VOLO / 1000
# Le quattro schede, con i loro nomi e i loro suoni.
RISULTATI, FILTRI, ALTRI_FILTRI, FILTRI_ALLENATORI = range(4)
NOMI_DELLE_SCHEDE = ("Risultati", "Filtri", "Altri filtri", "Filtri degli allenatori")
SUONI_DELLE_SCHEDE = ("scheda_risultati", "scheda_filtri", "scheda_altri_filtri", "scheda_filtri_allenatori")
# Il suono d'apertura di ogni porta d'ingresso; Assumi dello staff, porta None, apre come il mercato degli allenatori.
SUONI_DELLE_PORTE = {"mercato": "dialogo_mercato", "allenatori": "dialogo_mercato_allenatori", "ricerca": "dialogo_ricerca", "amichevole": "dialogo_avversario",
                     None: "dialogo_mercato_allenatori"}
# Le caselle dei filtri: l'etichetta con la lettera, e i suoni di quando si spunta e di quando si toglie.
CASELLE_DEI_FILTRI = {
    "allenatori": ("&Allenatori invece dei giocatori", "casella_allenatori_spuntata", "casella_allenatori_tolta"),
    "liberi": ("&Liberi", "casella_liberi_spuntata", "casella_liberi_tolta"),
    "in_vendita": ("In &vendita da altri, solo per i giocatori", "casella_in_vendita_spuntata", "casella_in_vendita_tolta"),
    "del_computer": ("Tesserati del comp&uter", "casella_del_computer_spuntata", "casella_del_computer_tolta"),
    "tuoi": ("&Tuoi tesserati", "casella_tuoi_spuntata", "casella_tuoi_tolta"),
    "ritirati": ("&Ritirati, solo per i giocatori", "casella_ritirati_spuntata", "casella_ritirati_tolta"),
    "disponibili_oggi": ("&Disponibili oggi per un'amichevole", "casella_disponibili_oggi_spuntata", "casella_disponibili_oggi_tolta"),
    "senza_acciacchi": ("&Escludi infortunati e acciaccati", "casella_senza_acciacchi_spuntata", "casella_senza_acciacchi_tolta"),
    "solo_ritirati_che_allenano": ("Solo i ri&tirati che allenano", "casella_solo_ritirati_che_allenano_spuntata", "casella_solo_ritirati_che_allenano_tolta"),
    "solo_nuovi": ("Solo i n&uovi arrivati della sessione", "casella_solo_nuovi_spuntata", "casella_solo_nuovi_tolta"),
    "comprendi_usciti": ("Comprendi &gli usciti di scena", "casella_comprendi_usciti_spuntata", "casella_comprendi_usciti_tolta"),
    "senza_prelazione_altrui": ("&Escludi chi è in prelazione per altri", "casella_senza_prelazione_altrui_spuntata", "casella_senza_prelazione_altrui_tolta"),
}
# Le voci delle scelte dei filtri: il valore del campo e il testo della scelta.
SESSI = ((None, "Tutti"), ("m", "Uomini"), ("f", "Donne"))
CLASSI = ((0, "Qualunque"), *((n, codice_della_classe(n)) for n in range(1, LIVELLI + 1)))
TIPI_DI_ALLENATORE = ((None, "Qualunque"), (staff.EX, "Ex giocatori"), (staff.NATO, "Nati allenatori"))
VISUS = ((None, "Qualunque"), *((visus, visus.capitalize()) for visus in staff.VISUS))
POSTI_ATTUALI = ((None, "Qualunque"), (staff.CAPO, "Capo allenatore"), (staff.ASSISTENTE, "Assistente"))
INDOLI_DELLA_SCELTA = ((None, "Qualunque"), *((chiave, dati["nome"].capitalize()) for chiave, dati in INDOLI.items()))
VOCI_DEI_TRATTI = ((None, "Indifferente"), (True, "Sì"), (False, "No"))
SUONI_DEI_TRATTI = {None: "filtro_tratto_indifferente", True: "filtro_tratto_si", False: "filtro_tratto_no"}
# Le scelte dei filtri, nell'ordine dei campi: l'etichetta con la lettera, le voci e il suono a ogni freccia.
SCELTE_DEI_FILTRI = {
    "sesso": ("S&esso", SESSI, "filtro_sesso_allenatori"),
    "classe_migliore": ("Classe mi&gliore o uguale a", CLASSI, "filtro_classe_allenatori"),
    "classe_peggiore": ("Classe &peggiore o uguale a", CLASSI, "filtro_classe_peggiore"),
    "indole": ("I&ndole", INDOLI_DELLA_SCELTA, "filtro_indole"),
    "tipo_allenatore": ("&Tipo di allenatore", TIPI_DI_ALLENATORE, "filtro_tipo_allenatori"),
    "visus": ("&Visus", VISUS, "filtro_visus"),
    "posto_attuale": ("&Posto attuale", POSTI_ATTUALI, "filtro_posto_attuale"),
}
# I numeri dei filtri: l'etichetta con la lettera, il massimo, che è quello del motore, e il suono di quando ci si ferma.
NUMERI_DEI_FILTRI = {
    "eta_massima": ("Età &massima in anni, zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["eta_massima"], "filtro_eta_allenatori"),
    "eta_minima": ("Età m&inima in anni, zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["eta_minima"], "filtro_eta_minima"),
    "costo_massimo": ("Costo massimo in euro, &zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["costo_massimo"], "filtro_costo_massimo"),
    "valore_minimo": ("Va&lore minimo in punti, zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["valore_minimo"], "filtro_valore_minimo"),
    "stipendio_massimo": ("&Stipendio massimo in euro al mese, zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["stipendio_massimo"],
                          "filtro_stipendio_massimo"),
    "mesi_contratto_massimi": ("Mesi di contr&atto rimasti al massimo, zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["mesi_contratto_massimi"],
                               "filtro_mesi_contratto"),
    "stipendio_capo_massimo": ("&Stipendio chiesto da capo al massimo, zero per nessun limite", mercato.MASSIMI_DEI_NUMERI["stipendio_capo_massimo"],
                               "filtro_stipendio_capo"),
}
# I testi dei filtri: l'etichetta con la lettera, e il suono di quando ci si ferma; il nome non suona, perché NVDA dice le lettere.
TESTI_DEI_FILTRI = {
    "nome": ("&Nome, cognome o numero", None),
    "comune": ("Co&mune, una parte del nome", "filtro_comune"),
    "polisportiva": ("&Polisportiva, una parte del nome", "filtro_polisportiva"),
}
CB_GETDROPPEDSTATE = 0x0157
# user32 in una copia tutta sua, con la firma che serve qui: la casella dei preset aperta o chiusa.
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendMessageW.restype = ctypes.c_ssize_t
_user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]


def _pianifica_con_wx(secondi, funzione):
    return wx.CallLater(max(1, round(secondi * 1000)), funzione)


def aperta(scelta):
    """Vero se l'elenco della scelta è aperto: allora Invio ed Esc sono di Windows, che lo chiude."""
    return isinstance(scelta, wx.Choice) and bool(_user32.SendMessageW(scelta.GetHandle(), CB_GETDROPPEDSTATE, 0, 0))


def _di_gabriele(scelta):
    """Vero per la scelta di un preset di Gabriele, il suo numero: un intero, e non vero o falso."""
    return isinstance(scelta, int) and not isinstance(scelta, bool)


def _stesso(primo, secondo):
    """Vero se i due controlli sono lo stesso, anche quando wx ne restituisce un altro oggetto Python: si guarda anche il numero."""
    return primo is secondo or (primo is not None and secondo is not None and primo.GetId() == secondo.GetId())


class Rimando:
    """
    Una funzione da chiamare un po' dopo l'ultima richiesta, con pianifica(secondi, funzione), che restituisce un
    oggetto con Stop(), come wx.CallLater: ogni richiesta sposta l'attesa. subito la chiama adesso, se aspettava.
    """

    def __init__(self, pianifica, secondi, funzione):
        self._pianifica = pianifica
        self.secondi = secondi
        self._funzione = funzione
        self._attesa = None

    @property
    def in_attesa(self):
        return self._attesa is not None

    def chiedi(self):
        self.ferma()
        self._attesa = self._pianifica(self.secondi, self._scatta)

    def subito(self):
        """Chiama adesso la funzione che aspettava: vero se aspettava."""
        if self._attesa is None:
            return False
        self.ferma()
        self._funzione()
        return True

    def ferma(self):
        attesa, self._attesa = self._attesa, None
        if attesa is not None:
            # Il timer di wx di una finestra già chiusa può essere andato.
            with contextlib.suppress(RuntimeError):
                attesa.Stop()

    def _scatta(self):
        if self._attesa is None:
            return
        self._attesa = None
        # Se nel frattempo la finestra si è chiusa, i suoi controlli non ci sono più.
        with contextlib.suppress(RuntimeError):
            self._funzione()


@dataclasses.dataclass
class EsitiDellaFinestra:
    """
    Quello che la finestra lascia alla chiusura: le offerte ai giocatori, coppie di testo e riuscita; quelle agli
    allenatori, coppie di testo ed esito, assunto o rifiutato; i testi delle sfide lanciate; l'amichevole scelta, la
    terna del tuo giocatore, dell'avversario e delle opzioni, che la finestra principale gioca; i testi delle
    operazioni sui preset.
    """
    giocatori: list = dataclasses.field(default_factory=list)
    allenatori: list = dataclasses.field(default_factory=list)
    sfide: list = dataclasses.field(default_factory=list)
    amichevole: tuple | None = None
    preset: list = dataclasses.field(default_factory=list)

    @property
    def vuoti(self):
        return not (self.giocatori or self.allenatori or self.sfide or self.amichevole or self.preset)


# I testi da leggere: domande, esiti e avvisi della finestra in un campo dove si scorre col cursore, non in un messaggio di Windows.

class Avviso(_SceltaConTesto):
    """Un avviso o un esito da leggere nel campo che ha il fuoco, col solo Chiudi; Esc, e Invio nel testo, chiudono."""

    def __init__(self, genitore, titolo, testo, impostazioni=None):
        super().__init__(genitore, titolo, testo, ((wx.ID_CLOSE, "&Chiudi"),), wx.ID_CLOSE, impostazioni)


class Domanda(_SceltaConTesto):
    """Una domanda da leggere nel campo che ha il fuoco, con Sì e No, il No già scelto: Esc, e Invio nel testo, valgono No."""

    def __init__(self, genitore, titolo, testo, impostazioni=None):
        super().__init__(genitore, titolo, testo, ((wx.ID_YES, "&Sì"), (wx.ID_CANCEL, "&No")), wx.ID_CANCEL, impostazioni)


class _ConTestiDaLeggere:
    """
    Per la finestra e i suoi dialoghi interni: avvisa e _conferma con Avviso e Domanda al posto dei messaggi di Windows,
    e i dialoghi interni aperti con _modale. Alla fine di ognuno la grazia di Invio riparte, e per mezzo secondo i
    pulsanti non si premono: così un Invio rimandato da NVDA non fa niente in chi li ha aperti, nemmeno sul pulsante
    che li ha aperti, dove torna il fuoco. Il passo della finestra ha misurato che il gancio dei tasti fatto a mano su un
    pulsante non arriva alla finestra: per i pulsanti la difesa è _ripetuta. Le prove sostituiscono _modale.
    """

    impostazioni = None
    _fine_di_un_dialogo = float("-inf")

    def _dopo_un_dialogo(self):
        self.ultimo_invio = self._fine_di_un_dialogo = dialoghi._adesso()

    def _modale(self, dialogo):
        try:
            return dialogo.ShowModal()
        finally:
            self._dopo_un_dialogo()

    @contextlib.contextmanager
    def _interno(self, dialogo, suono=None):
        """Un dialogo interno, col suono della sua apertura, distrutto alla fine."""
        try:
            if suono:
                suoni.suona(suono)
            yield dialogo
        finally:
            dialogo.Destroy()
            self._dopo_un_dialogo()

    def _ripetuta(self, nome):
        """La pressione ripetuta della base, e anche quella che arriva entro mezzo secondo dalla fine di un dialogo interno."""
        ripetuta = super()._ripetuta(nome)
        return ripetuta or dialoghi._adesso() - self._fine_di_un_dialogo < dialoghi.RIPETIZIONE_IGNORATA

    def leggi(self, testo, suono=None, fuoco=None):
        """Un avviso o un esito da leggere, col suo suono; alla fine il fuoco torna sul controllo dato, se c'è."""
        if suono:
            suoni.suona(suono)
        with self._interno(Avviso(self, self.GetTitle(), testo, self.impostazioni)) as dialogo:
            self._modale(dialogo)
        self._torna(fuoco)

    def avvisa(self, testo, controllo, suono="campo_da_correggere"):
        self.leggi(testo, suono, controllo)

    def _conferma(self, domanda):
        """La domanda col No già scelto e il suono delle domande; al No suona l'annullamento."""
        with self._interno(Domanda(self, self.GetTitle(), domanda, self.impostazioni), "domanda") as dialogo:
            si = self._modale(dialogo) == wx.ID_YES
        if not si:
            suoni.suona("annullato")
        return si


# I dialoghi interni della finestra.

class SalvaFiltri(_ConTestiDaLeggere, _Dialogo):
    """
    Salva filtri: il nome del preset, proposto da chi apre e tutto selezionato. Un nome che non va lo dice, col suono
    del campo da correggere; quello di un tuo preset, senza badare alle maiuscole, chiede se sostituirne i filtri, col
    No già scelto. In risultato resta il nome, senza gli spazi in testa e in coda.
    """

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, filtri_di_ricerca, proposta="", impostazioni=None):
        super().__init__(genitore, "Salva filtri")
        self.filtri_di_ricerca = filtri_di_ricerca
        self.impostazioni = impostazioni
        self.risultato = None
        self.etichetta("&Nome del preset")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello, value=proposta))
        salva, _annulla = self.pulsanti((wx.ID_OK, "&Salva"), (wx.ID_CANCEL, "Annulla"))
        salva.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((440, 200))
        self.nome.SetFocus()
        self.nome.SelectAll()

    def conferma(self, event=None):
        if self._ripetuta("salva"):
            return
        nome = self.nome.GetValue()
        problema = mercato.problema_del_nome(self.filtri_di_ricerca, nome)
        if problema is not None:
            self.avvisa(problema, self.nome)
            return
        esistente = mercato.preset_col_nome(self.filtri_di_ricerca, nome)
        if esistente is not None and not self._conferma(testi.domanda_sostituzione_preset(esistente.nome)):
            self._torna(self.nome)
            return
        self.risultato = nome.strip()
        self.chiudi(wx.ID_OK)


class RinominaPreset(_ConTestiDaLeggere, _Dialogo):
    """Il nuovo nome di un tuo preset, che parte da quello di adesso, tutto selezionato. In risultato resta il nome nuovo."""

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, filtri_di_ricerca, preset, impostazioni=None):
        super().__init__(genitore, f"Rinomina il preset {preset.nome}")
        self.filtri_di_ricerca = filtri_di_ricerca
        self.preset = preset
        self.impostazioni = impostazioni
        self.risultato = None
        self.etichetta("&Nuovo nome del preset")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello, value=preset.nome))
        rinomina, _annulla = self.pulsanti((wx.ID_OK, "&Rinomina"), (wx.ID_CANCEL, "Annulla"))
        rinomina.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((440, 200))
        self.nome.SetFocus()
        self.nome.SelectAll()

    def conferma(self, event=None):
        if self._ripetuta("rinomina"):
            return
        problema = mercato.problema_del_nome(self.filtri_di_ricerca, self.nome.GetValue(), self.preset.numero)
        if problema is not None:
            self.avvisa(problema, self.nome)
            return
        self.risultato = self.nome.GetValue().strip()
        self.chiudi(wx.ID_OK)


class GestisciPreset(_ConTestiDaLeggere, _Dialogo):
    """
    La gestione dei tuoi preset, nell'ordine della casella: Rinomina, Elimina, che chiede col No già scelto, Sposta su
    e Sposta giù. Ogni operazione la fa la finestra, che la passa subito nel mondo e fra i suoi esiti. Invio
    sull'elenco non fa niente; senza preset i pulsanti suonano il tasto a vuoto.
    """

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, finestra):
        super().__init__(genitore, "Gestisci i preset")
        self.finestra = finestra
        self.impostazioni = finestra.impostazioni
        self.etichetta("&I tuoi preset, nell'ordine della casella")
        self.elenco = self.aggiungi(wx.ListBox(self.pannello, style=wx.LB_SINGLE), 1)
        self.elenco.SetMinSize((-1, self.elenco.GetCharHeight() * 8))
        voci = ((wx.ID_ANY, "&Rinomina..."), (wx.ID_ANY, "&Elimina"), (wx.ID_ANY, "Sposta s&u"), (wx.ID_ANY, "Sposta &giù"), (wx.ID_CLOSE, "&Chiudi"))
        self.pulsante_rinomina, self.pulsante_elimina, self.pulsante_su, self.pulsante_giu, chiudi = self.pulsanti(*voci, predefinito=False)
        self.pulsante_rinomina.Bind(wx.EVT_BUTTON, self.rinomina)
        self.pulsante_elimina.Bind(wx.EVT_BUTTON, self.elimina)
        self.pulsante_su.Bind(wx.EVT_BUTTON, lambda event: self.sposta(-1))
        self.pulsante_giu.Bind(wx.EVT_BUTTON, lambda event: self.sposta(1))
        chiudi.Bind(wx.EVT_BUTTON, lambda event: self.chiudi(wx.ID_CLOSE))
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.aggiorna(0)
        self.completa((520, 420))
        self.elenco.SetFocus()

    @property
    def preset(self):
        return self.finestra.filtri_di_ricerca.preset

    def aggiorna(self, posto=None):
        posto = self.elenco.GetSelection() if posto is None else posto
        self._riscrivi(self.elenco, [p.nome for p in self.preset] or [testi.NESSUN_PRESET], posto)

    def _tasto(self, event):
        # La grazia di Invio l'ha già fatta la base, che lo chiama dopo: sull'elenco Invio non fa niente.
        if event.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and _stesso(event.GetEventObject(), self.elenco):
            return
        event.Skip()

    def _scelto(self):
        indice = self.elenco.GetSelection()
        if not self.preset or indice == wx.NOT_FOUND or indice >= len(self.preset):
            suoni.suona("nessuna_selezione")
            return None, indice
        return self.preset[indice], indice

    def rinomina(self, event=None):
        if self._ripetuta("rinomina"):
            return
        preset, posto = self._scelto()
        if preset is None:
            return
        with self._interno(RinominaPreset(self, self.finestra.filtri_di_ricerca, preset, self.impostazioni), "dialogo_rinomina_preset") as dialogo:
            nome = dialogo.risultato if self._modale(dialogo) == wx.ID_OK else None
        if nome is None:
            suoni.suona("annullato")
        else:
            nuovi = self.finestra.filtri_di_ricerca.copia()
            mercato.rinomina_preset(nuovi, preset.numero, nome)
            self.finestra.preset_cambiati(nuovi, testi.esito_preset_rinominato(preset.nome, nome.strip()), "preset_rinominato", self)
            self.aggiorna(posto)
        self._torna(self.pulsante_rinomina)

    def elimina(self, event=None):
        if self._ripetuta("elimina"):
            return
        preset, posto = self._scelto()
        if preset is None:
            return
        if self._conferma(testi.domanda_eliminazione_preset(preset.nome)):
            nuovi = self.finestra.filtri_di_ricerca.copia()
            mercato.elimina_preset(nuovi, preset.numero)
            self.finestra.preset_cambiati(nuovi, testi.esito_preset_eliminato(preset.nome), "preset_eliminato", self)
            self.aggiorna(min(posto, len(self.preset) - 1))
        self._torna(self.pulsante_elimina)

    def sposta(self, verso):
        pulsante = self.pulsante_su if verso < 0 else self.pulsante_giu
        if self._ripetuta("su" if verso < 0 else "giu"):
            return
        preset, posto = self._scelto()
        if preset is None:
            return
        nuovi = self.finestra.filtri_di_ricerca.copia()
        if not mercato.sposta_preset(nuovi, preset.numero, verso):
            suoni.suona("preset_non_si_sposta")
            return
        nuovo_posto = posto + verso
        esito = testi.esito_preset_spostato(preset.nome, nuovo_posto + 1, len(nuovi.preset))
        if self.finestra.preset_cambiati(nuovi, esito, "preset_spostato_su" if verso < 0 else "preset_spostato_giu", self, spostato=preset.numero):
            self.aggiorna(nuovo_posto)
        self._torna(pulsante)


class PostoDaOffrire(_ConTestiDaLeggere, _Dialogo):
    """Il posto dello staff da offrire a un allenatore libero, che parte da quello dato; le frecce suonano. In risultato resta il posto."""

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, mondo, poli, posto=0, impostazioni=None):
        super().__init__(genitore, "Posto da offrire")
        self.impostazioni = impostazioni
        self.risultato = None
        self.etichetta("&Posto da offrire")
        self.posto = self.aggiungi(wx.Choice(self.pannello, choices=[testi.voce_del_posto(poli, i, mondo) for i in range(staff.POSTI)]))
        self.posto.SetSelection(posto if 0 <= posto < staff.POSTI else 0)
        avanti, _annulla = self.pulsanti((wx.ID_OK, "&Avanti"), (wx.ID_CANCEL, "Annulla"))
        avanti.Bind(wx.EVT_BUTTON, self.conferma)
        self.posto.Bind(wx.EVT_CHOICE, lambda event: suoni.suona("staff_posto_scelto"))
        self.completa((440, 200))
        self.posto.SetFocus()

    def conferma(self, event=None):
        self.risultato = self.posto.GetSelection()
        self.chiudi(wx.ID_OK)


class Condizione(_ConTestiDaLeggere, _Dialogo):
    """
    Una condizione sulle caratteristiche, per Altri filtri: la caratteristica, fra i criteri numerici che non hanno già
    un campo, maggiore di o minore di, e il valore. In risultato resta la terna di criterio, condizione e valore.
    """

    GRAZIA_ALL_APERTURA = True
    CONDIZIONI = ricerca.CONDIZIONI[ricerca.NUMERO]

    def __init__(self, genitore, impostazioni=None):
        super().__init__(genitore, "Aggiungi una condizione")
        self.impostazioni = impostazioni
        self.risultato = None
        self.etichetta("&Caratteristica")
        self.criterio = self.aggiungi(wx.Choice(self.pannello, choices=[ricerca.nome_criterio(c) for c in mercato.CRITERI_DELLE_CONDIZIONI]))
        self.criterio.SetSelection(0)
        self.etichetta("C&ondizione")
        self.condizione = self.aggiungi(wx.Choice(self.pannello, choices=[nome for _chiave, nome in self.CONDIZIONI]))
        self.condizione.SetSelection(0)
        self.etichetta("&Valore")
        self.valore = self.aggiungi(wx.TextCtrl(self.pannello))
        aggiungi, _annulla = self.pulsanti((wx.ID_OK, "&Aggiungi"), (wx.ID_CANCEL, "Annulla"))
        aggiungi.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((440, 300))
        self.criterio.SetFocus()

    def conferma(self, event=None):
        try:
            valore = ricerca.leggi_numero(self.valore.GetValue())
        except ValueError:
            self.avvisa("Il valore deve essere un numero, per esempio 150 o 12,5.", self.valore)
            return
        self.risultato = (mercato.CRITERI_DELLE_CONDIZIONI[self.criterio.GetSelection()], self.CONDIZIONI[self.condizione.GetSelection()][0], valore)
        self.chiudi(wx.ID_OK)


# La finestra.

class MercatoERicerca(_ConTestiDaLeggere, _Dialogo):
    """
    La finestra Mercato e ricerca. porta è una di mercato.PORTE, da cui la finestra riapre col suo ultimo preset e a
    cui alla chiusura lascia la voce scelta e i filtri attuali; None per Assumi dello staff, che apre sugli allenatori
    liberi col posto dato e non ricorda niente. pianifica(secondi, funzione) fa i rimandi, wx.CallLater di serie;
    annunci sono quelli che dicono i trovati, di serie quelli della sessione. In risultato, alla chiusura, gli
    EsitiDellaFinestra. Le prove sostituiscono pianifica, annunci e _modale.
    """

    def __init__(self, genitore, mondo, impostazioni, porta, posto=None, pianifica=None, annunci=None):
        attiva = mondo.miapolisportiva_attiva
        super().__init__(genitore, testi.titolo_mercato_e_ricerca(attiva))
        self.mondo = mondo
        self.impostazioni = modulo_impostazioni.valide(impostazioni)
        self.porta = porta
        self.posto = posto
        self.annunci = annunci if annunci is not None else annunci_condivisi()
        pianifica = pianifica or _pianifica_con_wx
        self._pianifica = pianifica
        self._ricalcolo = Rimando(pianifica, RITARDO_DEL_RICALCOLO, self.ricalcola)
        self._annuncio = Rimando(pianifica, RITARDO_DELL_ANNUNCIO, self.annuncia)
        self._scheda = Rimando(pianifica, RITARDO_DELLA_SCHEDA, self.aggiorna_la_scheda)
        self._suono_fermo = Rimando(pianifica, RITARDO_DEL_SUONO, self._suona_quando_ci_si_ferma)
        self._suono_da_fare = None
        self.memoria = mercato.Memoria(mondo)
        self.esiti = EsitiDellaFinestra()
        self.risultato = None
        self.filtri_di_ricerca = mercato.filtri_di_ricerca_del_mondo(mondo)
        if porta is None:
            scelta = "allenatori_liberi"
            self.attuali = mercato.filtri_di_serie(scelta)
        else:
            stato = mercato.stato_della_porta(mondo, porta)
            scelta, self.attuali = stato.scelta, stato.attuali
        try:
            self.filtri = mercato.filtri_della_voce(self.filtri_di_ricerca, scelta, self.attuali)
        except KeyError:
            scelta = mercato.PRESET_DELLA_PORTA[porta]
            self.filtri = mercato.filtri_di_serie(scelta)
        self.scelta = scelta
        # Il tuo preset da cui vengono i filtri attuali: Salva filtri ne propone il nome.
        self._origine = None
        self._spostato = None
        self.righe = []
        self.ultima_riga = -1
        self._ordine_delle_righe = self.filtri.ordine_scelto
        self._in_ricalcolo = False
        self._applico = False
        self._chiusa = False
        self._persona_della_scheda = None
        self._testo_della_scheda = None
        self._testo_dei_filtri_attivi = None
        self._vuoto = dialoghi._ElencoCheSiRestringe()
        self._controlli_dei_filtri = []
        self._riquadri_delle_schede = []
        # Il resto dei suoni dell'apertura, che aspetta il suo turno: alla chiusura si ferma.
        self._fila = None
        self._costruisci()
        self._rifai_la_casella()
        self._scrivi_i_controlli()
        # Il ricalcolo chiede la scheda col suo rimando, anche adesso: all'apertura il fuoco va sull'elenco, e la
        # scheda, che costa una quarantina di millesimi, si scrive subito dopo, o appena prende il fuoco.
        self.ricalcola()
        self._aggiorna_la_situazione()
        self._aggiorna_l_offerta()
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.Bind(wx.EVT_CLOSE, self._alla_chiusura)
        self.completa((980, 720))
        if porta == "ricerca":
            self.libro.SetSelection(FILTRI)
            self.campo_nome.SetFocus()
            self.campo_nome.SelectAll()
        else:
            self.elenco.SetFocus()
        self.libro.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._scheda_cambiata)
        # L'apertura conta come un Invio: quello della voce di menu, rimandato da NVDA, non apre una scheda.
        self.ultimo_invio = dialoghi._adesso()
        self._suoni_dell_apertura(attiva)

    # La costruzione.

    def _pagina(self, nome):
        """
        Una scheda: la pagina della Notebook, e dentro un riquadro grande quanto lei, col testo della linguetta, che fa
        da genitore a tutti i suoi controlli. Restituisce il riquadro e il suo sizer. Dalla verifica con la lente di
        NVDA: una pagina di wx, per Windows, è un riquadro senza ruolo, che NVDA non dice, e la linguetta è la stessa
        per tutte le pagine, quindi con Ctrl+Tab NVDA diceva soltanto il controllo; un riquadro col nome, invece, NVDA
        lo dice quando il fuoco ci entra, come i riquadri Luogo o Chi cercare.
        """
        pannello = wx.Panel(self.libro)
        pannello.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.libro.AddPage(pannello, nome)
        scatola, sizer = self._riquadro(pannello, nome, pannello.GetSizer(), 1)
        self._riquadri_delle_schede.append(scatola)
        return scatola, sizer

    @staticmethod
    def _riquadro(genitore, titolo, dove, proporzione=0):
        """
        Un riquadro nativo, senza lettera, nel sizer dato: i suoi controlli nascono suoi figli, come vuole wx, e NVDA lo
        dice quando ci si entra. Il passo della finestra ha misurato che le lettere rapide vanno anche da dentro un
        riquadro, verso la pagina e verso Chiudi.
        """
        scatola = wx.StaticBox(genitore, label=titolo)
        sizer = wx.StaticBoxSizer(scatola, wx.VERTICAL)
        dove.Add(sizer, proporzione, wx.EXPAND | wx.ALL, 6)
        return scatola, sizer

    @staticmethod
    def _griglia(sizer):
        griglia = wx.FlexGridSizer(0, 2, 4, 8)
        griglia.AddGrowableCol(1, 1)
        sizer.Add(griglia, 0, wx.EXPAND | wx.ALL, 4)
        return griglia

    @staticmethod
    def _campo(genitore, griglia, etichetta, fabbrica):
        """Etichetta e controllo sulla stessa riga della griglia: l'etichetta nasce prima, e NVDA ne prende il nome del controllo."""
        griglia.Add(wx.StaticText(genitore, label=etichetta), 0, wx.ALIGN_CENTER_VERTICAL)
        controllo = fabbrica(genitore)
        griglia.Add(controllo, 1, wx.EXPAND)
        return controllo

    def _casella(self, genitore, sizer, campo):
        etichetta, spuntata, tolta = CASELLE_DEI_FILTRI[campo]
        casella = wx.CheckBox(genitore, label=etichetta)
        sizer.Add(casella, 0, wx.ALL, 3)
        casella.Bind(wx.EVT_CHECKBOX, lambda event: self._alla_casella(campo, casella.GetValue(), spuntata, tolta))
        self._controlli_dei_filtri.append(casella)
        self.caselle[campo] = casella
        return casella

    def _scelta(self, genitore, griglia, campo, etichetta=None, voci=None, suono=None):
        predefinita, voci_di_serie, suono_di_serie = SCELTE_DEI_FILTRI.get(campo, (None, None, None))
        voci = voci if voci is not None else voci_di_serie
        scelta = self._campo(genitore, griglia, etichetta or predefinita, lambda g: wx.Choice(g, choices=[testo for _valore, testo in voci]))
        self.scelte[campo] = (scelta, voci)
        suono = suono or suono_di_serie
        scelta.Bind(wx.EVT_CHOICE, lambda event: self._alla_scelta(campo, suono))
        self._controlli_dei_filtri.append(scelta)
        return scelta

    def _numero(self, genitore, griglia, campo):
        etichetta, massimo, suono = NUMERI_DEI_FILTRI[campo]
        numero = self._campo(genitore, griglia, etichetta, lambda g: wx.SpinCtrl(g, min=0, max=massimo, initial=0))
        self.numeri[campo] = numero
        for tipo in (wx.EVT_SPINCTRL, wx.EVT_TEXT):
            numero.Bind(tipo, lambda event: self._al_numero(campo, suono))
        self._controlli_dei_filtri.append(numero)
        return numero

    def _testo(self, genitore, griglia, campo):
        etichetta, suono = TESTI_DEI_FILTRI[campo]
        testo = self._campo(genitore, griglia, etichetta, lambda g: wx.TextCtrl(g))
        self.testi_dei_filtri[campo] = testo
        testo.Bind(wx.EVT_TEXT, lambda event: self._al_testo(campo, suono))
        self._controlli_dei_filtri.append(testo)
        return testo

    def _pulsante(self, genitore, sizer, etichetta, azione, identificativo=wx.ID_ANY):
        pulsante = wx.Button(genitore, identificativo, etichetta)
        sizer.Add(pulsante, 0, wx.ALL, 4)
        pulsante.Bind(wx.EVT_BUTTON, azione)
        return pulsante

    def _costruisci(self):
        self.caselle, self.scelte, self.numeri, self.testi_dei_filtri, self.tratti = {}, {}, {}, {}, {}
        self.libro = wx.Notebook(self.pannello)
        self.aggiungi(self.libro, 1)
        self._costruisci_i_risultati(*self._pagina(NOMI_DELLE_SCHEDE[RISULTATI]))
        self._costruisci_i_filtri(*self._pagina(NOMI_DELLE_SCHEDE[FILTRI]))
        self._costruisci_gli_altri_filtri(*self._pagina(NOMI_DELLE_SCHEDE[ALTRI_FILTRI]))
        self._costruisci_i_filtri_degli_allenatori(*self._pagina(NOMI_DELLE_SCHEDE[FILTRI_ALLENATORI]))
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_chiudi = self._pulsante(self.pannello, riga, "&Chiudi", self.chiudi_la_finestra, wx.ID_CLOSE)
        self.sizer.Add(riga, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

    def _costruisci_i_risultati(self, pagina, sizer):
        griglia = self._griglia(sizer)
        # Su più righe: wx toglie dal giro del Tab, e quindi anche dalla sua lettera, un campo a una riga in sola lettura.
        # Senza andare a capo, dalla verifica con la lente di NVDA: il testo è una riga sola a blocchi di quaranta
        # caratteri, e a capo a metà di un blocco il display braille lo spezzava; la riga in più è per la barra orizzontale.
        self.situazione = self._campo(pagina, griglia, "&Situazione",
                                      lambda g: wx.TextCtrl(g, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP))
        self.situazione.SetMinSize((-1, self.situazione.GetCharHeight() * 2))
        aspetto.applica(self.situazione, self.impostazioni)
        self.casella_preset = self._campo(pagina, griglia, "&Preset dei filtri", lambda g: wx.Choice(g))
        self.casella_preset.Bind(wx.EVT_CHOICE, self._al_preset)
        self.casella_preset.Bind(wx.EVT_KILL_FOCUS, self._casella_lasciata)
        self.etichetta_trovati = wx.StaticText(pagina, label="&" + testi.etichetta_trovati(0))
        sizer.Add(self.etichetta_trovati, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.elenco = ElencoVirtuale(pagina, self._testo_della_riga)
        self.elenco.SetMinSize((-1, self.elenco.GetCharHeight() * 8))
        sizer.Add(self.elenco, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        for tipo in (wx.EVT_LIST_ITEM_FOCUSED, wx.EVT_LIST_ITEM_SELECTED):
            self.elenco.Bind(tipo, self._alla_riga)
        self.elenco.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda event: self.vai_alla_scheda())
        self.elenco.Bind(wx.EVT_SET_FOCUS, self._elenco_col_fuoco)
        self.etichetta_scheda = wx.StaticText(pagina, label=testi.etichetta_della_scheda(None))
        sizer.Add(self.etichetta_scheda, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.scheda = wx.TextCtrl(pagina, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.scheda.SetMinSize((-1, self.scheda.GetCharHeight() * 8))
        aspetto.applica(self.scheda, self.impostazioni)
        sizer.Add(self.scheda, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.scheda.Bind(wx.EVT_SET_FOCUS, self._scheda_col_fuoco)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_offerta = self._pulsante(pagina, riga, "Fai un'&offerta...", self.offerta)
        self.pulsante_amichevole = self._pulsante(pagina, riga, "A&michevole...", self.amichevole)
        self.pulsante_sfida = self._pulsante(pagina, riga, "Sfida il suo clu&b...", self.sfida)
        self.pulsante_diario = self._pulsante(pagina, riga, "&Diario", self.diario)
        self.pulsante_gestisci = self._pulsante(pagina, riga, "&Gestisci i preset...", self.gestisci_preset)
        sizer.Add(riga, 0, wx.ALL, 4)

    def _costruisci_i_filtri(self, pagina, sizer):
        griglia = self._griglia(sizer)
        self.campo_nome = self._testo(pagina, griglia, "nome")
        self._casella(pagina, sizer, "allenatori")
        scatola, riquadro = self._riquadro(pagina, "Chi cercare", sizer)
        for campo in ("liberi", "in_vendita", "del_computer", "tuoi", "ritirati"):
            self._casella(scatola, riquadro, campo)
        griglia = self._griglia(sizer)
        self._scelta(pagina, griglia, "sesso")
        self._scelta(pagina, griglia, "classe_migliore")
        self._scelta(pagina, griglia, "classe_peggiore")
        self._numero(pagina, griglia, "eta_massima")
        self._numero(pagina, griglia, "eta_minima")
        self._numero(pagina, griglia, "costo_massimo")
        self._casella(pagina, sizer, "disponibili_oggi")
        griglia = self._griglia(sizer)
        # L'ordine cambia voci con la casella Allenatori: si riempie in _scrivi_l_ordine.
        self.scelta_ordine = self._campo(pagina, griglia, "&Ordina per", lambda g: wx.Choice(g))
        self.scelta_ordine.Bind(wx.EVT_CHOICE, self._all_ordine)
        self._controlli_dei_filtri.append(self.scelta_ordine)
        sizer.Add(wx.StaticText(pagina, label="&Filtri attivi"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.filtri_attivi = wx.TextCtrl(pagina, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.filtri_attivi.SetMinSize((-1, self.filtri_attivi.GetCharHeight() * 6))
        aspetto.applica(self.filtri_attivi, self.impostazioni)
        sizer.Add(self.filtri_attivi, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self._controlli_dei_filtri.append(self.filtri_attivi)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_salva = self._pulsante(pagina, riga, "&Salva filtri...", lambda event: self.salva_filtri())
        sizer.Add(riga, 0, wx.ALL, 4)

    def _costruisci_gli_altri_filtri(self, pagina, sizer):
        # Due colonne di riquadri, perché la pagina non diventi più alta dello schermo: l'ordine del Tab resta quello in cui nascono.
        colonne = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(colonne, 1, wx.EXPAND)
        sinistra, destra = wx.BoxSizer(wx.VERTICAL), wx.BoxSizer(wx.VERTICAL)
        colonne.Add(sinistra, 1, wx.EXPAND)
        colonne.Add(destra, 1, wx.EXPAND)
        scatola, riquadro = self._riquadro(pagina, "Luogo", sinistra)
        griglia = self._griglia(riquadro)
        self._scelta(scatola, griglia, "regione", "&Regione", (("", "Qualunque"), *((regione, regione) for regione in luoghi.regioni())), "filtro_regione")
        # La provincia cambia voci con la regione: si riempie in _scrivi_la_provincia.
        self.scelta_provincia = self._campo(scatola, griglia, "Pro&vincia", lambda g: wx.Choice(g))
        self.scelta_provincia.Bind(wx.EVT_CHOICE, self._alla_provincia)
        self._controlli_dei_filtri.append(self.scelta_provincia)
        self._testo(scatola, griglia, "comune")
        self._testo(scatola, griglia, "polisportiva")
        scatola, riquadro = self._riquadro(pagina, "Tratti", sinistra)
        griglia = self._griglia(riquadro)
        for numero, tratto in enumerate(mercato.TRATTI, 1):
            scelta = self._campo(scatola, griglia, f"Tratto &{numero}, {ricerca.nome_criterio(tratto).lower()}",
                                 lambda g: wx.Choice(g, choices=[testo for _valore, testo in VOCI_DEI_TRATTI]))
            scelta.Bind(wx.EVT_CHOICE, lambda event, tratto=tratto: self._al_tratto(tratto))
            self.tratti[tratto] = scelta
            self._controlli_dei_filtri.append(scelta)
        scatola, riquadro = self._riquadro(pagina, "Indole, soldi e contratto", destra)
        griglia = self._griglia(riquadro)
        self._scelta(scatola, griglia, "indole")
        self._numero(scatola, griglia, "valore_minimo")
        self._numero(scatola, griglia, "stipendio_massimo")
        self._numero(scatola, griglia, "mesi_contratto_massimi")
        scatola, riquadro = self._riquadro(pagina, "Salute, carriera e sessione", destra)
        for campo in ("senza_acciacchi", "solo_ritirati_che_allenano", "solo_nuovi", "comprendi_usciti"):
            self._casella(scatola, riquadro, campo)
        scatola, riquadro = self._riquadro(pagina, "Condizioni", destra, 1)
        riquadro.Add(wx.StaticText(scatola, label="Con&dizioni sulle caratteristiche"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 4)
        self.elenco_condizioni = wx.ListBox(scatola, style=wx.LB_SINGLE)
        self.elenco_condizioni.SetMinSize((-1, self.elenco_condizioni.GetCharHeight() * 4))
        riquadro.Add(self.elenco_condizioni, 1, wx.EXPAND | wx.ALL, 4)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_aggiungi = self._pulsante(scatola, riga, "Agg&iungi una condizione...", lambda event: self.aggiungi_condizione())
        self.pulsante_togli = self._pulsante(scatola, riga, "Togli la condi&zione", lambda event: self.togli_condizione())
        self.pulsante_togli_tutte = self._pulsante(scatola, riga, "Togli tutte le c&ondizioni", lambda event: self.togli_tutte_le_condizioni())
        riquadro.Add(riga, 0, wx.ALL, 2)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_azzera = self._pulsante(pagina, riga, "Azzera &questi filtri", lambda event: self.azzera_gli_altri_filtri())
        sizer.Add(riga, 0, wx.ALL, 4)

    def _costruisci_i_filtri_degli_allenatori(self, pagina, sizer):
        griglia = self._griglia(sizer)
        self._scelta(pagina, griglia, "tipo_allenatore")
        self._scelta(pagina, griglia, "visus")
        self._scelta(pagina, griglia, "posto_attuale")
        self._numero(pagina, griglia, "stipendio_capo_massimo")
        self._casella(pagina, sizer, "senza_prelazione_altrui")

    # I controlli dai filtri.

    @staticmethod
    def _metti(scelta, voci, valore):
        """La scelta sulla voce del valore; un valore che fra le voci non c'è lascia la prima."""
        posto = next((i for i, (v, _testo) in enumerate(voci) if v == valore and type(v) is type(valore)), 0)
        if scelta.GetSelection() != posto:
            scelta.SetSelection(posto)

    def _voci_dell_ordine(self):
        ordini = mercato.ORDINI_ALLENATORI if self.filtri.allenatori else mercato.ORDINI_GIOCATORI
        return [(chiave, nome[0].upper() + nome[1:]) for chiave, nome in ordini]

    def _scrivi_l_ordine(self):
        voci = self._voci_dell_ordine()
        testi_delle_voci = [testo for _chiave, testo in voci]
        if self.scelta_ordine.GetItems() != testi_delle_voci:
            self.scelta_ordine.Set(testi_delle_voci)
        self._metti(self.scelta_ordine, voci, self.filtri.ordine_scelto)
        self._ordini = voci

    def _voci_della_provincia(self):
        """Le province della regione scelta, o tutte; la provincia scelta fuori regione resta, in fondo, e Filtri attivi lo dice."""
        voci = [("", "Qualunque"), *((provincia, provincia) for provincia in luoghi.province(self.filtri.regione or None))]
        if self.filtri.provincia and all(valore != self.filtri.provincia for valore, _testo in voci):
            voci.append((self.filtri.provincia, self.filtri.provincia))
        return voci

    def _scrivi_la_provincia(self):
        voci = self._voci_della_provincia()
        testi_delle_voci = [testo for _valore, testo in voci]
        if self.scelta_provincia.GetItems() != testi_delle_voci:
            self.scelta_provincia.Set(testi_delle_voci)
        self._metti(self.scelta_provincia, voci, self.filtri.provincia)
        self._province = voci

    def _scrivi_le_condizioni(self, posto=0):
        righe = [testi.condizione_a_parole(*condizione) for condizione in self.filtri.condizioni] or [testi.NESSUNA_CONDIZIONE]
        self._riscrivi(self.elenco_condizioni, righe, posto)

    def _scrivi_i_controlli(self):
        """Tutti i controlli delle quattro schede dai filtri, senza che i loro gestori li prendano per cambi a mano."""
        self._applico = True
        try:
            for campo, testo in self.testi_dei_filtri.items():
                if testo.GetValue() != getattr(self.filtri, campo):
                    testo.ChangeValue(getattr(self.filtri, campo))
            for campo, casella in self.caselle.items():
                casella.SetValue(bool(getattr(self.filtri, campo)))
            for campo, (scelta, voci) in self.scelte.items():
                self._metti(scelta, voci, getattr(self.filtri, campo))
            for campo, numero in self.numeri.items():
                valore = round(getattr(self.filtri, campo))
                if numero.GetValue() != valore:
                    numero.SetValue(valore)
            for tratto, scelta in self.tratti.items():
                self._metti(scelta, VOCI_DEI_TRATTI, self.filtri.tratti.get(tratto))
            self._scrivi_l_ordine()
            self._scrivi_la_provincia()
            self._scrivi_le_condizioni()
        finally:
            self._applico = False

    # I cambi a mano.

    def _cambiati(self, nuovi):
        """
        I filtri nuovi, cambiati a mano: falso, e niente cambia, se sono uguali a prima. Altrimenti diventano i filtri
        attuali, la casella va in silenzio sulla voce in cima, e se erano quelli di un tuo preset, Salva filtri ne
        proporrà il nome.
        """
        if nuovi == self.filtri:
            return False
        if self.scelta is not None:
            self._origine = self.scelta if _di_gabriele(self.scelta) else None
            self.scelta = None
        self.filtri = nuovi
        self.attuali = nuovi.copia()
        self._metti_la_casella(0)
        return True

    def _con(self, campo, valore):
        nuovi = self.filtri.copia()
        setattr(nuovi, campo, valore)
        return nuovi

    def _dopo_un_tasto(self):
        """Dopo un tasto in un campo, un numero o una scelta: il ricalcolo e l'annuncio, ciascuno col suo ritardo dall'ultimo tasto."""
        self._ricalcolo.chiedi()
        self._annuncio.chiedi()

    def _subito(self):
        """Dopo una casella o un pulsante, che cambiano una volta sola: il ricalcolo subito, l'annuncio col suo ritardo."""
        self.ricalcola()
        self._annuncio.chiedi()

    def _quando_ci_si_ferma(self, suono):
        if suono:
            self._suono_da_fare = suono
            self._suono_fermo.chiedi()

    def _suona_quando_ci_si_ferma(self):
        suono, self._suono_da_fare = self._suono_da_fare, None
        if suono:
            suoni.suona(suono)

    def _alla_casella(self, campo, valore, spuntata, tolta):
        if self._applico or not self._cambiati(self._con(campo, valore)):
            return
        if campo == "allenatori":
            self._applico = True
            try:
                self._scrivi_l_ordine()
            finally:
                self._applico = False
        suoni.suona(spuntata if valore else tolta)
        self._subito()

    def _alla_scelta(self, campo, suono):
        scelta, voci = self.scelte[campo]
        if self._applico or not self._cambiati(self._con(campo, voci[scelta.GetSelection()][0])):
            return
        if campo == "regione":
            self._applico = True
            try:
                self._scrivi_la_provincia()
            finally:
                self._applico = False
        suoni.suona(suono)
        self._dopo_un_tasto()

    def _alla_provincia(self, event=None):
        if self._applico or not self._cambiati(self._con("provincia", self._province[self.scelta_provincia.GetSelection()][0])):
            return
        suoni.suona("filtro_provincia")
        self._dopo_un_tasto()

    def _all_ordine(self, event=None):
        campo = "ordine_allenatori" if self.filtri.allenatori else "ordine"
        if self._applico or not self._cambiati(self._con(campo, self._ordini[self.scelta_ordine.GetSelection()][0])):
            return
        suoni.suona("mercato_ordine_cambiato")
        self._dopo_un_tasto()

    def _al_tratto(self, tratto):
        voluto = VOCI_DEI_TRATTI[self.tratti[tratto].GetSelection()][0]
        nuovi = self.filtri.copia()
        if voluto is None:
            nuovi.tratti.pop(tratto, None)
        else:
            nuovi.tratti[tratto] = voluto
        if self._applico or not self._cambiati(nuovi):
            return
        suoni.suona(SUONI_DEI_TRATTI[voluto])
        self._dopo_un_tasto()

    def _al_numero(self, campo, suono):
        if self._applico or not self._cambiati(self._con(campo, self.numeri[campo].GetValue())):
            return
        self._quando_ci_si_ferma(suono)
        self._dopo_un_tasto()

    def _al_testo(self, campo, suono):
        if self._applico or not self._cambiati(self._con(campo, self.testi_dei_filtri[campo].GetValue())):
            return
        self._quando_ci_si_ferma(suono)
        self._dopo_un_tasto()

    # La casella dei preset.

    def _rifai_la_casella(self):
        """Le voci della casella dei preset, con la voce applicata scelta: Filtri attuali, i tuoi, quelli di serie, Salva filtri."""
        self.voci = mercato.voci_della_casella(self.filtri_di_ricerca)
        nomi = [voce.nome for voce in self.voci]
        if self.casella_preset.GetItems() != nomi:
            self.casella_preset.Set(nomi)
        posto = mercato.posto_della_scelta(self.voci, self.scelta)
        self._metti_la_casella(posto if posto is not None else 0)

    def _metti_la_casella(self, posto):
        self._posto_applicato = posto
        if self.casella_preset.GetSelection() != posto:
            self.casella_preset.SetSelection(posto)

    def _voce_della_casella(self):
        posto = self.casella_preset.GetSelection()
        return self.voci[posto] if 0 <= posto < len(self.voci) else self.voci[0]

    def _al_preset(self, event=None):
        """
        Una voce della casella dei preset: un preset si applica intero, la voce in cima riprende i filtri fatti a mano;
        Salva filtri si apre soltanto scelto dall'elenco aperto, con Invio o col clic, mai con le frecce; la voce già
        applicata non fa niente. Dalla verifica con la lente di NVDA: uscendo con Tab, Maiusc+Tab, Alt+lettera o
        Ctrl+Tab dall'elenco aperto su Salva filtri, Windows manda prima l'uscita del fuoco, con la casella ancora
        sulla voce di prima, e poi la scelta di Salva filtri, a elenco chiuso; la casella restava lì, e tornandoci NVDA
        leggeva Salva filtri. Adesso torna in silenzio sulla voce applicata, come quando il fuoco la lascia.
        """
        posto = self.casella_preset.GetSelection()
        voce = self._voce_della_casella()
        if voce.tipo == mercato.VOCE_SALVA:
            if aperta(self.casella_preset):
                self.salva_filtri()
            elif not _stesso(dialoghi.controllo_col_fuoco(), self.casella_preset):
                self._metti_la_casella(self._posto_applicato)
            return
        if posto == self._posto_applicato:
            return
        if voce.tipo == mercato.VOCE_ATTUALI:
            filtri, suono = self.attuali.copia(), "filtri_attuali_ripresi"
        else:
            filtri, suono = mercato.filtri_della_voce(self.filtri_di_ricerca, voce.scelta, self.attuali), "mercato_scelta_cambiata"
        self.filtri = filtri
        self.scelta = voce.scelta
        self._posto_applicato = posto
        self._scrivi_i_controlli()
        suoni.suona(suono)
        self._dopo_un_tasto()

    def _casella_lasciata(self, event):
        """Il fuoco lascia la casella ferma su Salva filtri...: torna in silenzio sulla voce applicata."""
        event.Skip()
        with contextlib.suppress(RuntimeError):
            if self._voce_della_casella().tipo == mercato.VOCE_SALVA and not aperta(self.casella_preset):
                self._metti_la_casella(self._posto_applicato)

    def _invio_sulla_casella(self):
        if self._voce_della_casella().tipo == mercato.VOCE_SALVA:
            self.salva_filtri()
            return
        self._ricalcolo.subito()
        self._annuncio.ferma()
        self.elenco.SetFocus()

    # I preset.

    def _nome_proposto(self):
        """Il nome che Salva filtri propone: quello del tuo preset applicato, o di quello da cui vengono i filtri attuali; vuoto altrimenti."""
        numero = self.scelta if _di_gabriele(self.scelta) else self._origine if self.scelta is None else None
        preset = mercato.preset_col_numero(self.filtri_di_ricerca, numero)
        return preset.nome if preset is not None else ""

    def salva_filtri(self):
        if self._ripetuta("salva_filtri"):
            return
        fuoco = dialoghi.controllo_col_fuoco()
        with self._interno(SalvaFiltri(self, self.filtri_di_ricerca, self._nome_proposto(), self.impostazioni), "dialogo_salva_filtri") as dialogo:
            nome = dialogo.risultato if self._modale(dialogo) == wx.ID_OK else None
        if nome is None:
            suoni.suona("annullato")
            self._metti_la_casella(self._posto_applicato)
            self._torna(fuoco)
            return
        nuovi = self.filtri_di_ricerca.copia()
        try:
            preset, sostituito = mercato.salva_preset(nuovi, nome, self.filtri)
        except ValueError as errore:
            self._metti_la_casella(self._posto_applicato)
            self.avvisa(str(errore), fuoco)
            return
        if self.preset_cambiati(nuovi, testi.esito_preset_salvato(preset.nome, sostituito), "preset_sostituito" if sostituito else "preset_salvato"):
            # Il preset salvato è la voce scelta, che la porta riaprirà.
            self.scelta = preset.numero
            self._metti_la_casella(mercato.posto_della_scelta(self.voci, preset.numero))
        else:
            self._metti_la_casella(self._posto_applicato)
        self._torna(fuoco)

    def preset_cambiati(self, nuovi, esito, suono, chi_avvisa=None, spostato=None):
        """
        I preset di Gabriele dopo un'operazione: passano subito nel mondo, e l'operazione fra gli esiti della finestra,
        una riga sola per gli spostamenti di seguito dello stesso preset; la casella si rifà. Una scelta o un'origine che
        punta a un preset eliminato torna alla voce in cima. Falso, con l'avviso, se il mondo non li prende.
        """
        try:
            mercato.ricorda_i_preset(self.mondo, nuovi)
        except ValueError as errore:
            (chi_avvisa or self).leggi(f"I preset non si possono salvare: {errore}.", "campo_da_correggere")
            return False
        self.filtri_di_ricerca = nuovi
        if spostato is not None and spostato == self._spostato and self.esiti.preset:
            self.esiti.preset[-1] = esito
        else:
            self.esiti.preset.append(esito)
        self._spostato = spostato
        numeri = {p.numero for p in nuovi.preset}
        if _di_gabriele(self.scelta) and self.scelta not in numeri:
            self.scelta = None
            self.attuali = self.filtri.copia()
        if _di_gabriele(self._origine) and self._origine not in numeri:
            self._origine = None
        self._rifai_la_casella()
        suoni.suona(suono)
        return True

    def gestisci_preset(self, event=None):
        if self._ripetuta("gestisci"):
            return
        with self._interno(GestisciPreset(self, self), "dialogo_gestisci_preset") as dialogo:
            self._modale(dialogo)
        self._torna(self.pulsante_gestisci)

    # Le condizioni e Azzera.

    def aggiungi_condizione(self):
        if self._ripetuta("aggiungi"):
            return
        with self._interno(Condizione(self, self.impostazioni), "dialogo_filtro_mercato") as dialogo:
            nuova = dialogo.risultato if self._modale(dialogo) == wx.ID_OK else None
        if nuova is None:
            suoni.suona("annullato")
            self._torna(self.pulsante_aggiungi)
            return
        nuovi = self.filtri.copia()
        nuovi.condizioni = (*nuovi.condizioni, nuova)
        self._cambiati(nuovi)
        self._scrivi_le_condizioni(len(nuovi.condizioni) - 1)
        self.elenco_condizioni.SetFocus()
        suoni.suona("filtro_aggiunto")
        self._subito()

    def togli_condizione(self):
        if self._ripetuta("togli"):
            return
        posto = self.elenco_condizioni.GetSelection()
        if not self.filtri.condizioni or posto == wx.NOT_FOUND:
            suoni.suona("nessuna_selezione")
            return
        nuovi = self.filtri.copia()
        nuovi.condizioni = tuple(c for i, c in enumerate(nuovi.condizioni) if i != posto)
        self._cambiati(nuovi)
        self._scrivi_le_condizioni(min(posto, len(nuovi.condizioni) - 1))
        self.elenco_condizioni.SetFocus()
        suoni.suona("filtro_tolto")
        self._subito()

    def togli_tutte_le_condizioni(self):
        if self._ripetuta("togli_tutte"):
            return
        if not self.filtri.condizioni:
            suoni.suona("nessuna_selezione")
            return
        self._cambiati(self._con("condizioni", ()))
        self._scrivi_le_condizioni()
        self.elenco_condizioni.SetFocus()
        suoni.suona("filtri_tutti_tolti")
        self._subito()

    def azzera_gli_altri_filtri(self):
        if self._ripetuta("azzera"):
            return
        if not self._cambiati(mercato.azzera(self.filtri, mercato.CAMPI_ALTRI_FILTRI)):
            suoni.suona("nessuna_selezione")
            return
        self._scrivi_i_controlli()
        suoni.suona("filtri_azzerati")
        self._subito()

    # L'elenco, il ricalcolo e l'annuncio.

    def _testo_della_riga(self, indice):
        return testi.riga_trovato(self.righe[indice], self.mondo, self._ordine_delle_righe, self.memoria)

    def riga_scelta(self):
        """La riga su cui lavorano le azioni: quella col fuoco, o l'ultima che lo ha avuto; -1 se l'elenco è vuoto."""
        indice = self.elenco.col_fuoco()
        if indice < 0:
            indice = self.ultima_riga
        return indice if 0 <= indice < len(self.righe) else -1

    def riga(self):
        indice = self.riga_scelta()
        return self.righe[indice] if indice >= 0 else None

    def ricalcola(self, ripiego=0):
        """
        L'elenco coi filtri di adesso: resta scelta la stessa persona, o il posto di ripiego, e l'etichetta, Filtri
        attivi e le linguette si rifanno; quando l'elenco si svuota o torna pieno, il suo suono. Gli eventi dell'elenco
        di questo momento non contano: la scheda si chiede dopo.
        """
        self._ricalcolo.ferma()
        r = self.riga()
        self.righe = mercato.cerca(self.mondo, self.filtri, self.memoria)
        self._ordine_delle_righe = self.filtri.ordine_scelto
        posto = mercato.indice_della_persona(self.righe, r.numero, r.allenatore, ripiego) if r is not None else (0 if self.righe else None)
        self._in_ricalcolo = True
        try:
            self.elenco.riscrivi_sempre = self.filtri.allenatori
            self.elenco.mostra(len(self.righe), posto, [testi.nome_completo(riga.persona).casefold() for riga in self.righe])
        finally:
            self._in_ricalcolo = False
        self.ultima_riga = self.elenco.col_fuoco() if self.righe else -1
        self._aggiorna_le_etichette()
        primo = self._vuoto.pieno is None
        passaggio = self._vuoto.passaggio(bool(self.righe))
        if passaggio and not primo:
            suoni.in_coda(passaggio)
        self._scheda.chiedi()

    def _aggiorna_le_etichette(self):
        etichetta = "&" + testi.etichetta_trovati(len(self.righe), self.filtri.allenatori)
        if self.etichetta_trovati.GetLabel() != etichetta:
            self.etichetta_trovati.SetLabel(etichetta)
            self.libro.GetPage(RISULTATI).Layout()
        testo = testi.filtri_attivi(self.filtri, self.mondo)
        if testo != self._testo_dei_filtri_attivi:
            self.filtri_attivi.ChangeValue(testo)
            aspetto.ridai_stile(self.filtri_attivi, self.impostazioni)
            self._testo_dei_filtri_attivi = testo
        for pagina, campi in ((ALTRI_FILTRI, mercato.CAMPI_ALTRI_FILTRI), (FILTRI_ALLENATORI, mercato.CAMPI_FILTRI_ALLENATORI)):
            testo = testi.linguetta(NOMI_DELLE_SCHEDE[pagina], mercato.quanti_impostati(self.filtri, campi))
            if self.libro.GetPageText(pagina) != testo:
                self.libro.SetPageText(pagina, testo)
                # Il riquadro della scheda dice lo stesso della linguetta: è il nome che NVDA legge entrando con Ctrl+Tab.
                self._riquadri_delle_schede[pagina].SetLabel(testo)
                self.libro.GetPage(pagina).Layout()

    def annuncia(self):
        """Il numero dei trovati alla voce e al display, al posto di quello di prima, anche con la lettura della cronaca spenta; prima, il ricalcolo che aspettava."""
        self._annuncio.ferma()
        self._ricalcolo.subito()
        self.annunci.svuota()
        self.annunci.annuncia([testi.etichetta_trovati(len(self.righe), self.filtri.allenatori)], {**self.impostazioni, "annunci_cronaca": True})

    def _alla_riga(self, event):
        """Il fuoco o la selezione su una riga: la scheda la segue; la deselezione con -1 e gli eventi del ricalcolo non contano."""
        event.Skip()
        if self._in_ricalcolo:
            return
        indice = event.GetIndex()
        if indice >= 0:
            self.ultima_riga = indice
            self._scheda.chiedi()

    # La scheda della persona.

    def aggiorna_la_scheda(self):
        """Etichetta e testo della scheda per la riga scelta; il cursore torna all'inizio quando cambia la persona."""
        self._scheda.ferma()
        r = self.riga()
        etichetta = testi.etichetta_della_scheda(r)
        if self.etichetta_scheda.GetLabel() != etichetta:
            self.etichetta_scheda.SetLabel(etichetta)
            self.libro.GetPage(RISULTATI).Layout()
        persona = (r.allenatore, r.numero) if r is not None else None
        testo = testi.scheda_della_riga(r, self.mondo)
        if testo != self._testo_della_scheda or persona != self._persona_della_scheda:
            self.scheda.ChangeValue(testo)
            aspetto.ridai_stile(self.scheda, self.impostazioni)
            if persona != self._persona_della_scheda:
                self.scheda.SetInsertionPoint(0)
            self._testo_della_scheda = testo
        self._persona_della_scheda = persona

    def _scheda_col_fuoco(self, event):
        """
        La scheda prende il fuoco: dal controllo finale del 24 ottobre il ricalcolo che aspettava si fa prima, così la
        scheda è già quella della persona nuova e l'annuncio dei trovati non arriva sopra la lettura.
        """
        event.Skip()
        if not self._in_ricalcolo and self._ricalcolo.subito():
            self._annuncio.ferma()
        if self._scheda.in_attesa:
            self.aggiorna_la_scheda()

    def _elenco_col_fuoco(self, event):
        """
        L'elenco prende il fuoco: il ricalcolo che aspettava si fa adesso, prima che NVDA ne legga il nome, coi trovati,
        e le righe; l'annuncio dei trovati non serve più, perché NVDA li dice nel nome. Dalla verifica con la lente di
        NVDA: con una freccia sulla casella dei preset e subito Tab, Alt+T, Maiusc+Tab o Ctrl+Tab, NVDA leggeva l'elenco
        di prima, e mezzo secondo dopo l'elenco cambiava senza che lo rileggesse.
        """
        event.Skip()
        if self._in_ricalcolo:
            return
        self._ricalcolo.subito()
        self._annuncio.ferma()

    def vai_alla_scheda(self):
        """Invio sull'elenco, o il doppio clic: la scheda della riga, col fuoco all'inizio; con l'elenco vuoto, il tasto a vuoto."""
        indice = self.riga_scelta()
        if indice < 0:
            suoni.suona("nessuna_selezione")
            return
        self.elenco.scegli(indice)
        self.aggiorna_la_scheda()
        self.scheda.SetFocus()
        self.scheda.SetInsertionPoint(0)
        suoni.suona("scheda_allenatore" if self.righe[indice].allenatore else "mercato_scheda_giocatore")

    def torna_all_elenco(self):
        """
        Invio o Esc nella scheda: il fuoco torna sull'elenco, sulla stessa persona. Dal controllo finale del 24 ottobre
        il ricalcolo che aspettava si fa prima di leggere la riga, che altrimenti cambierebbe sotto la persona.
        """
        self._ricalcolo.subito()
        indice = self.riga_scelta()
        self.elenco.SetFocus()
        if indice >= 0:
            self.elenco.scegli(indice)
        suoni.suona("ritorno_all_elenco")

    # I tasti.

    def _controllo_di(self, oggetto):
        """Il controllo della finestra a cui va il tasto: l'oggetto dell'evento, o il primo dei suoi genitori che la finestra conosce."""
        noti = (self.elenco, self.scheda, self.casella_preset, self.elenco_condizioni, *self._controlli_dei_filtri)
        while isinstance(oggetto, wx.Window) and not _stesso(oggetto, self):
            if isinstance(oggetto, wx.Button):
                return oggetto
            noto = next((controllo for controllo in noti if _stesso(controllo, oggetto)), None)
            if noto is not None:
                return noto
            oggetto = oggetto.GetParent()
        return None

    def _tasto(self, event):
        """
        Il gancio dei tasti della finestra. Ogni Invio che arriva qui passa dalla grazia, una prova sola per tasto; a
        elenco aperto di una scelta va a Windows, che lo chiude. Poi Invio sull'elenco porta alla scheda, nella scheda
        torna all'elenco, nella casella dei preset apre Salva filtri o porta all'elenco, nei filtri fa subito il
        ricalcolo e porta all'elenco della scheda Risultati, sui pulsanti è di Windows, e i pulsanti si difendono con
        _ripetuta. Esc nella scheda torna all'elenco. Alt+O sull'offerta oscurata, nella scheda Risultati, dice il perché.
        """
        codice = event.GetKeyCode()
        controllo = self._controllo_di(event.GetEventObject())
        if codice in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not event.HasAnyModifiers():
            if aperta(controllo):
                event.Skip()
            elif dialoghi.invio_da_ignorare(self, event):
                return
            elif isinstance(controllo, wx.Button):
                event.Skip()
            else:
                self._invio(controllo)
            return
        if codice == wx.WXK_ESCAPE and not event.HasAnyModifiers() and controllo is self.scheda:
            self.torna_all_elenco()
            return
        if (codice == ord("O") and event.AltDown() and not event.ControlDown() and not event.ShiftDown() and not self.pulsante_offerta.IsEnabled()
                and self.libro.GetSelection() == RISULTATI):
            self.perche_niente_offerte()
            return
        event.Skip()

    def _invio(self, controllo):
        """Invio dopo la grazia: sull'elenco delle condizioni, sulla Situazione e sulla linguetta non fa niente."""
        if controllo is self.elenco:
            self.vai_alla_scheda()
        elif controllo is self.scheda:
            self.torna_all_elenco()
        elif controllo is self.casella_preset:
            self._invio_sulla_casella()
        elif any(controllo is filtro for filtro in self._controlli_dei_filtri):
            self._ai_risultati()

    def _ai_risultati(self):
        """Invio in un filtro: subito il ricalcolo che aspettava, niente annuncio, e il fuoco sull'elenco della scheda Risultati."""
        self._ricalcolo.subito()
        self._annuncio.ferma()
        if self.libro.GetSelection() != RISULTATI:
            self.libro.SetSelection(RISULTATI)
        self.elenco.SetFocus()

    def _scheda_cambiata(self, event):
        """Il cambio di scheda, con Ctrl+Tab, Ctrl+Maiusc+Tab o con Invio in un filtro, che porta ai Risultati: il suono della scheda."""
        event.Skip()
        pagina = event.GetSelection()
        if 0 <= pagina < len(SUONI_DELLE_SCHEDE):
            suoni.suona(SUONI_DELLE_SCHEDE[pagina])

    # La Situazione e l'offerta.

    def _aggiorna_la_situazione(self):
        testo = testi.situazione(self.mondo)
        if self.situazione.GetValue() != testo:
            self.situazione.ChangeValue(testo)
            aspetto.ridai_stile(self.situazione, self.impostazioni)

    def _offerte_finite(self):
        p = self.mondo.miapolisportiva_attiva
        return p is None or self.mondo.mosse_rimaste(p) <= 0

    def _aggiorna_l_offerta(self):
        """Si oscura soltanto l'offerta, a mosse finite o senza polisportiva attiva; se aveva il fuoco, prima passa all'elenco."""
        abilitata = not self._offerte_finite()
        if self.pulsante_offerta.IsEnabled() != abilitata:
            if not abilitata and dialoghi.controllo_col_fuoco() is self.pulsante_offerta:
                self.elenco.SetFocus()
            self.pulsante_offerta.Enable(abilitata)

    def perche_niente_offerte(self):
        """Alt+O sull'offerta oscurata: il perché, col suo suono."""
        p = self.mondo.miapolisportiva_attiva
        if p is None:
            self.leggi(mercato.offerta_possibile(self.mondo, None, None).problema, "nessuna_polisportiva_attiva", dialoghi.controllo_col_fuoco())
        else:
            self.leggi(testi.mosse_finite(p), "mosse_finite", dialoghi.controllo_col_fuoco())

    def _suoni_dell_apertura(self, attiva):
        """Il suono della porta, poi in coda le mosse finite, o la polisportiva che manca al mercato, e l'elenco che nasce vuoto."""
        suoni.suona(SUONI_DELLE_PORTE[self.porta])
        seguenti = []
        if attiva is not None and self.mondo.mosse_rimaste(attiva) <= 0:
            seguenti.append("mosse_finite")
        elif attiva is None and self.porta in ("mercato", "allenatori"):
            seguenti.append("nessuna_polisportiva_attiva")
        if not self.righe:
            seguenti.append("elenco_svuotato")
        self._in_fila(seguenti)

    def _in_fila(self, eventi):
        """
        I suoni uno dopo l'altro, ciascuno quando è finito il precedente: in_coda ne aspetta uno solo. Il resto aspetta
        in self._fila, che la chiusura ferma: dalla verifica del comportamento, con Esc subito dopo l'apertura il suono
        dell'elenco vuoto arrivava dopo quello della finestra chiusa.
        """
        self._fila = None
        if self._chiusa:
            return
        eventi = list(eventi)
        while eventi:
            suoni.in_coda(eventi.pop(0))
            if eventi and suoni.attesa() > 0:
                resto = tuple(eventi)
                self._fila = self._pianifica(suoni.attesa() + 2 * suoni.PAUSA_IN_CODA, lambda resto=resto: self._in_fila(resto))
                return

    @contextlib.contextmanager
    def _interno(self, dialogo, suono=None):
        """
        Un dialogo interno della finestra, come nella base; prima, il ricalcolo che aspettava si fa subito e l'annuncio
        dei trovati si ferma. Dalla verifica con la lente di NVDA: con un filtro cambiato e subito Salva filtri, Gestisci,
        un'offerta o un'altra azione, l'annuncio scattava dentro il dialogo e arrivava alla voce e al display sopra il
        suo titolo e il suo testo.
        """
        self._ricalcolo.subito()
        self._annuncio.ferma()
        with super()._interno(dialogo, suono) as aperto:
            yield aperto

    # Le azioni.

    def _riga_per_le_azioni(self):
        """La riga su cui lavora un pulsante, che torna scelta; con l'elenco vuoto il tasto a vuoto, e None."""
        indice = self.riga_scelta()
        if indice < 0:
            suoni.suona("nessuna_selezione")
            return None
        self.elenco.scegli(indice)
        return self.righe[indice]

    def _cifra(self, titolo, spiegazione, etichetta, iniziale, p, suono, nota=None, probabilita=None):
        """La cifra scelta, oppure None se si annulla: suono è quello dell'apertura."""
        with self._interno(Cifra(self, titolo, spiegazione, etichetta, iniziale, p.cassa, nota, probabilita), suono) as dialogo:
            valore = dialogo.valore if self._modale(dialogo) == wx.ID_OK else None
        if valore is None:
            suoni.suona("annullato")
        return valore

    def _motivo(self, p, r, importo, posto=None):
        """Il suono di un'offerta che dopo la cifra non si può fare: la cassa che non basta, o il motivo del motore."""
        if importo > p.cassa:
            return "cassa_insufficiente"
        return mercato.offerta_possibile(self.mondo, p, r, posto).motivo or mercato.OFFERTA_NON_POSSIBILE

    def offerta(self, event=None):
        """
        L'offerta alla persona della riga, secondo chi è: l'ingaggio a un libero, l'acquisto a chi è in vendita, l'offerta
        d'acquisto a un tesserato del computer, l'ingaggio per un posto dello staff a un allenatore libero. Se non si può,
        il perché col suono del motivo. L'esito si legge, va fra gli esiti, e l'elenco si ricalcola.
        """
        if self._ripetuta("offerta"):
            return
        r = self._riga_per_le_azioni()
        if r is None:
            return
        p = self.mondo.miapolisportiva_attiva
        possibile = mercato.offerta_possibile(self.mondo, p, r)
        if possibile.problema is not None:
            self.leggi(possibile.problema, possibile.motivo, self.elenco)
            return
        fare = {mercato.INGAGGIO: self._ingaggio, mercato.ACQUISTO: self._acquisto, mercato.OFFERTA_D_ACQUISTO: self._offerta_d_acquisto,
                mercato.INGAGGIO_ALLENATORE: self._ingaggio_allenatore}[possibile.azione]
        esito = fare(r, p)
        if esito is None:
            self._torna(self.elenco)
            return
        testo, suono, riuscita = esito
        if r.allenatore:
            self.esiti.allenatori.append((testo, riuscita))
        else:
            self.esiti.giocatori.append((testo, riuscita))
            self.memoria.dimentica(r.persona)
        self.leggi(testo, suono)
        self.ricalcola(ripiego=self.riga_scelta())
        self._aggiorna_la_situazione()
        self._aggiorna_l_offerta()
        self.elenco.SetFocus()
        if self._offerte_finite():
            suoni.in_coda("mosse_finite")

    def _ingaggio(self, r, p):
        g = r.persona
        nome = testi.nome_completo(g)
        richiesta = self.memoria.ingaggio(g, p)
        # Dalla tappa 11 la spiegazione comincia con il contratto che il giocatore propone, D31.
        spiegazione = f"{testi.proposta_di_contratto(g, self.mondo)} Per firmare, {nome} chiede {testi.euro(richiesta)} d'ingaggio: più offri, più è probabile che accetti."
        importo = self._cifra(f"Ingaggio di {nome}", spiegazione, "&Ingaggio da offrire, in euro", richiesta, p, "dialogo_cifra_ingaggio",
                              lambda cifra: f"Accetterebbe {testi.con_articolo('al', testi.percento(probabilita_accettazione(cifra, richiesta)))}.",
                              lambda cifra: probabilita_accettazione(cifra, richiesta))
        if importo is None:
            return None
        problema = self.mondo.problema_offerta(p, g, importo)
        if problema:
            self.leggi(problema, self._motivo(p, r, importo), self.elenco)
            return None
        if not self._conferma(testi.domanda_ingaggio(r, importo, probabilita_accettazione(importo, richiesta), p, self.mondo)):
            return None
        accetta, probabilita = self.mondo.offerta(p, g, importo)
        return testi.esito_ingaggio(g, p, accetta, importo, probabilita), "ingaggio_accettato" if accetta else "ingaggio_rifiutato", accetta

    def _acquisto(self, r, p):
        g = r.persona
        if not self._conferma(testi.domanda_acquisto(r, p, self.mondo)):
            return None
        prezzo = self.mondo.acquista(p, g)
        return testi.esito_acquisto(g, r.polisportiva, p, prezzo), "acquisto_fatto", True

    def _offerta_d_acquisto(self, r, p):
        g = r.persona
        nome = testi.nome_completo(g)
        importo = self._cifra("Offerta d'acquisto", f"{nome} vale {testi.euro(r.costo)} sul mercato: {r.polisportiva.nome} lo cede se l'offerta le basta.",
                              "&Cifra da offrire, in euro", r.costo, p, "dialogo_cifra_offerta_d_acquisto")
        if importo is None:
            return None
        problema = self.mondo.problema_offerta_d_acquisto(p, g, importo)
        if problema:
            self.leggi(problema, self._motivo(p, r, importo), self.elenco)
            return None
        if not self._conferma(testi.domanda_offerta_d_acquisto(r, importo, p, self.mondo)):
            return None
        accettata = self.mondo.offerta_d_acquisto(p, g, importo)
        suono = "offerta_d_acquisto_accettata" if accettata else "offerta_d_acquisto_rifiutata"
        return testi.esito_offerta_d_acquisto(g, r.polisportiva, p, accettata, importo), suono, accettata

    def _posto_di_partenza(self, p):
        """Il posto da cui parte la scelta: quello di Assumi, se è vuoto, altrimenti il primo vuoto."""
        if self.posto is not None and 0 <= self.posto < staff.POSTI and not p.staff[self.posto]:
            return self.posto
        return next((i for i, numero in enumerate(p.staff) if not numero), 0)

    def _ingaggio_allenatore(self, r, p):
        a = r.persona
        with self._interno(PostoDaOffrire(self, self.mondo, p, self._posto_di_partenza(p), self.impostazioni), "dialogo_posto_da_offrire") as dialogo:
            posto = dialogo.risultato if self._modale(dialogo) == wx.ID_OK else None
        if posto is None:
            suoni.suona("annullato")
            return None
        possibile = mercato.offerta_possibile(self.mondo, p, r, posto)
        if possibile.problema is not None:
            self.leggi(possibile.problema, possibile.motivo, self.elenco)
            return None
        ruolo = staff.CAPO if posto == 0 else staff.ASSISTENTE
        richiesta = staff.ingaggio_richiesto(a, ruolo, p)
        importo = self._cifra(f"Ingaggio di {testi.nome_completo(a)}", testi.spiegazione_ingaggio_allenatore(a, p, posto, self.mondo), "&Ingaggio da offrire, in euro",
                              richiesta, p, "dialogo_cifra_ingaggio_allenatore",
                              lambda cifra: f"Accetterebbe {testi.con_articolo('al', testi.percento(probabilita_accettazione(cifra, richiesta)))}.",
                              lambda cifra: probabilita_accettazione(cifra, richiesta))
        if importo is None:
            return None
        problema = self.mondo.problema_offerta_allenatore(p, a, posto, importo)
        if problema:
            self.leggi(problema, self._motivo(p, r, importo, posto), self.elenco)
            return None
        if not self._conferma(testi.domanda_offerta_allenatore(a, p, posto, importo, probabilita_accettazione(importo, richiesta), self.mondo)):
            return None
        accetta, probabilita = self.mondo.offerta_allenatore(p, a, posto, importo)
        testo = testi.esito_offerta_allenatore(a, p, accetta, importo, probabilita)
        return testo, "allenatore_assunto" if accetta else "allenatore_rifiuta", "assunto" if accetta else "rifiutato"

    def amichevole(self, event=None):
        """
        L'amichevole contro la persona della riga: prima l'avversario, qui, poi il tuo giocatore fra i disponibili della
        polisportiva attiva, e le opzioni. Alla conferma la finestra si chiude, e la partita la gioca la finestra principale.
        """
        if self._ripetuta("amichevole"):
            return
        r = self._riga_per_le_azioni()
        if r is None:
            return
        p = self.mondo.miapolisportiva_attiva
        possibile = mercato.amichevole_possibile(self.mondo, p, r)
        if possibile.problema is not None:
            self.leggi(possibile.problema, possibile.motivo, self.elenco)
            return
        if not p.tesserati:
            self.leggi(f"{p.nome} non ha tesserati da far giocare.", "rosa_vuota", self.elenco)
            return
        avversario = r.persona
        tuoi = mercato.tuoi_per_l_amichevole(self.mondo, p, avversario)
        if not tuoi:
            # Dalla verifica del comportamento: se l'avversario scelto è proprio l'unico dei tuoi che oggi gioca, il
            # testo non dice più che non gioca nessuno, ma che a lui serve un altro avversario, col suono di chi come
            # avversario oggi non va.
            if [g.id for g in mercato.tuoi_per_l_amichevole(self.mondo, p, None)] == [avversario.id]:
                self.leggi(testi.unico_per_l_amichevole(avversario, p), mercato.NON_GIOCA_OGGI, self.elenco)
            else:
                self.leggi(testi.nessuno_per_l_amichevole(self.mondo, adesso_utc(), poli=p), "nessun_giocatore_oggi", self.elenco)
            return
        titolo = f"Amichevole contro {testi.nome_completo(avversario)}, il tuo giocatore di {p.nome}"
        with self._interno(SceltaGiocatore(self, self.mondo, titolo, "&Avanti", tuoi), "dialogo_amichevole") as dialogo:
            tuo = dialogo.scelto if self._modale(dialogo) == wx.ID_OK else None
        if tuo is None:
            suoni.suona("annullato")
            self._torna(self.elenco)
            return
        ultime = (self.impostazioni["amichevole_set"], self.impostazioni["amichevole_modo"], self.impostazioni["amichevole_livello"])
        with self._interno(OpzioniAmichevole(self, self.mondo, tuo, avversario, ultime), "dialogo_opzioni_amichevole") as dialogo:
            scelte = dialogo.risultato if self._modale(dialogo) == wx.ID_OK else None
        if scelte is None:
            suoni.suona("annullato")
            self._torna(self.elenco)
            return
        self.esiti.amichevole = (tuo, avversario, scelte)
        self.chiudi_la_finestra()

    def sfida(self, event=None):
        """La sfida al club della persona della riga, col lancio aperto su quella polisportiva; i lanci vanno fra gli esiti."""
        if self._ripetuta("sfida"):
            return
        r = self._riga_per_le_azioni()
        if r is None:
            return
        p = self.mondo.miapolisportiva_attiva
        possibile = mercato.sfida_possibile(self.mondo, p, r)
        if possibile.problema is not None:
            self.leggi(possibile.problema, possibile.motivo, self.elenco)
            return
        with self._interno(LanciaSfida(self, self.mondo, p, self.impostazioni, bersaglio=r.polisportiva.nome), "dialogo_lancia_sfida") as dialogo:
            self._modale(dialogo)
            lanciate = list(dialogo.esiti)
        self.esiti.sfide.extend(lanciate)
        self._aggiorna_la_situazione()
        self._torna(self.elenco)

    def diario(self, event=None):
        if self._ripetuta("diario"):
            return
        r = self._riga_per_le_azioni()
        if r is None:
            return
        if r.allenatore:
            testo, suono = testi.diario_allenatore(r.persona), "diario_allenatore"
        else:
            testo, suono = testi.diario_giocatore(r.persona), "diario_giocatore"
        with self._interno(Lettura(self, f"Diario di {testi.nome_completo(r.persona)}", testo, self.impostazioni), suono) as dialogo:
            self._modale(dialogo)
        self._torna(self.elenco)

    # La chiusura.

    def _alla_chiusura(self, event):
        self.chiudi_la_finestra()

    def chiudi_la_finestra(self, event=None):
        """
        Chiudi, Esc e la chiusura della finestra: i rimandi si fermano e il display si svuota; una porta vera ricorda la
        voce scelta e i filtri attuali; in risultato gli esiti.
        """
        if self._chiusa:
            return
        self._chiusa = True
        for rimando in (self._ricalcolo, self._annuncio, self._scheda, self._suono_fermo):
            rimando.ferma()
        fila, self._fila = self._fila, None
        if fila is not None:
            with contextlib.suppress(RuntimeError):
                fila.Stop()
        self.annunci.svuota()
        if self.porta is not None:
            # I filtri vengono dai controlli e dai preset, e fanno sempre il giro del salvataggio: se non lo facessero, la porta riaprirebbe come prima.
            with contextlib.suppress(ValueError):
                mercato.ricorda_la_porta(self.mondo, self.porta, mercato.StatoDellaPorta(self.scelta, self.attuali.copia()))
        self.risultato = self.esiti
        self.chiudi(wx.ID_CLOSE)

    def esiti_alla_fine(self):
        """
        Gli esiti, per chi ha aperto la finestra, dopo ShowModal: se a chiuderla è stato qualcun altro, come la chiusura
        per l'aggiornamento, che chiude i dialoghi aperti, la chiusura della finestra si fa adesso, porta compresa.
        """
        if self.risultato is None:
            self.chiudi_la_finestra()
        return self.risultato
