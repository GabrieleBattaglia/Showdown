"""
La finestra Mercato e ricerca di MESS, issue 8 e decisione D36.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 col progetto corretto dal critico e le scelte di Gabriele dello stesso giorno: il mercato dei
giocatori, quello degli allenatori, la ricerca e la scelta dell'avversario dell'amichevole diventano una finestra
sola, che si apre massimizzata da ogni porta d'ingresso con il suo ultimo preset, ed Esc la chiude.
Le schede sono native, wx.Notebook, e si cambiano con Ctrl+Tab e Ctrl+Maiusc+Tab, ognuna col suo suono. Ogni
controllo ha la sua lettera, e le lettere si ripetono da una scheda all'altra, perché Windows le cerca soltanto fra i
controlli visibili; Chiudi, fuori dalle schede, ha la C in tutte. Il passo della finestra ha misurato su wx, sul
desktop nascosto, che Ctrl+Tab cambia scheda da ogni controllo e porta il fuoco nella pagina nuova, che Alt+C
arriva a Chiudi anche da dentro una pagina, da un riquadro e dalla linguetta, e che le lettere di una scheda nascosta
non fanno niente: per questo il gancio dei tasti non li prende.
La casella dei preset ha in cima la voce Filtri attuali, non salvati, poi i preset di Gabriele, poi i dodici preset
di serie, e per ultima Salva filtri..., che si apre con Invio, o scegliendola dall'elenco aperto, mai con le frecce:
scorrendo la casella chiusa ogni preset si applica intero. I preset si salvano, si rinominano, si eliminano e si
spostano, e ogni operazione passa subito nel mondo e fra gli esiti della finestra, che alla chiusura la vista
racconta e il mondo salva.
La scheda della persona segue la riga scelta, e Invio sull'elenco porta lì; Invio ed Esc nella scheda tornano
all'elenco, sulla stessa riga. Un Invio che arriva entro la grazia dall'apertura, dall'Invio di prima o dalla fine di
un dialogo interno si mangia, perché NVDA rimanda Invio come pressioni nuove; e la pressione di un pulsante entro mezzo
secondo dalla sua pressione di prima, o dalla fine di un dialogo interno, si ignora: il passo della finestra ha
misurato che il gancio dei tasti non arriva alla finestra da un pulsante. Le domande, gli esiti e gli avvisi della
finestra si leggono in un campo dove si scorre col cursore, non in un messaggio di Windows: le domande hanno Sì e No,
col No già scelto; il lancio della sfida e la cifra, dialoghi di tutto il gioco, tengono i loro messaggi brevi. A mosse
finite si oscura soltanto l'offerta, e Alt+O sulla scheda Risultati dice il perché col suo suono. L'amichevole si gioca
scegliendo prima l'avversario qui, poi il proprio giocatore: la finestra si chiude e la partita la gioca la finestra
principale. Assumi dello staff apre sugli allenatori liberi col posto già scelto, e non ricorda niente.
Coi collegamenti dello stesso giorno la aprono Ctrl+K, Ctrl+Maiusc+G, Ctrl+F e Ctrl+O della finestra principale e Assumi
dello staff, e chi la apre ne prende gli esiti con esiti_alla_fine, anche quando a chiuderla è stata la chiusura per
l'aggiornamento, che chiude i dialoghi aperti: la porta si ricorda lo stesso.
Dalle verifiche dello stesso giorno: ogni scheda è un riquadro col testo della sua linguetta perché NVDA, che delle
pagine di wx non dice niente, lo dica quando il fuoco ci entra con Ctrl+Tab; l'elenco che prende il fuoco mentre un
ricalcolo aspetta si rifà subito, prima che NVDA ne legga il nome e le righe, e lo stesso fa ogni dialogo interno, che
ferma anche l'annuncio dei trovati, perché non arrivi sopra il dialogo; la casella dei preset lasciata su Salva filtri
dall'elenco aperto torna sulla voce applicata; la Situazione resta su una riga sola; anche all'apertura la scheda della
persona si scrive col suo rimando; i suoni dell'apertura messi in fila si fermano alla chiusura; l'amichevole contro
l'unico tuo giocatore che oggi gioca dice che serve un altro avversario, invece di dire che non gioca nessuno.
La sera dello stesso giorno, con la richiesta di Gabriele sulla finestra a quattro schede e 55 controlli di filtro, uno
per filtro, il costruttore di regole, e le schede tornano due. Risultati resta com'era, con la Situazione, la casella
dei preset, l'elenco dei trovati, la scheda della persona, le azioni e Gestisci i preset, Alt+G. Filtri ha il campo
Trovati, una riga per informazione; la regola in preparazione, nel suo riquadro, col collegamento, e oppure o, che si
vede soltanto quando ci sono regole, il bersaglio, Giocatori o Allenatori, la caratteristica, l'operatore e il valore,
una scelta o un campo secondo la caratteristica, con l'etichetta che dice che cosa scrivere; Aggiungi regola e Azzera;
l'elenco delle regole, dove Canc ne toglie una, Ctrl+Su e Ctrl+Giù la spostano e le lettere E e O cambiano il suo
collegamento; Ordina per, che fa parte del preset; e Salva filtri, che mette nel preset anche la regola in preparazione
quando conta. La regola in preparazione conta appena ha un valore valido, e la e lega prima della o. Ogni mossa rifà il
conto dei trovati dopo 350 millesimi, e l'annuncio alla voce e al display arriva 1000 millesimi dopo l'ultima, soltanto
se dice qualcosa di nuovo. La casella dei preset va in cima, in silenzio, quando cambia qualcosa che conta: le regole,
l'ordine o una regola in preparazione che conta; guardare le caratteristiche, col valore vuoto, non la stacca dal suo
preset. Invio nel Valore con un valore sbagliato resta lì e dice il perché; Aggiungi regola conta come un Invio, perché
quello rimandato da NVDA non porti dall'elenco delle regole ai Risultati. Le misure su wx del passo, sul desktop
nascosto: la coppia di etichetta e controllo del Valore che non si vede perde la sua lettera, perché la lettera di
un'etichetta nascosta porta il fuoco al controllo dopo; SetLabel cambia il nome che NVDA legge; Set e SetSelection
di una scelta non mandano eventi; i tasti dell'elenco delle regole, messi in coda come quelli veri, arrivano al suo
gestore coi loro modificatori. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Lo stesso giorno, con le verifiche del costruttore: dopo Canc, E ed O, che lasciano la scelta sulla stessa riga, il nome
cambiato di quella riga va a Windows, perché NVDA scarta il fuoco ripetuto e non la leggeva; l'elenco che prende il fuoco
segna sempre come detto il conto che NVDA legge nel suo nome, così dopo un Invio veloce l'annuncio di un conto tornato
quello di prima non tace più; senza regole il collegamento nascosto torna alla e; con non ha il dato e ha il dato il
Valore non si vede; il suono del valore scritto che aspettava tace dopo Invio, un dialogo interno o il cambio di scheda;
e le lettere E e O che non cambiano niente hanno due suoni loro, la O sulla prima regola e il collegamento che c'è già,
al posto del tasto a vuoto. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import contextlib
import ctypes
import dataclasses
from ctypes import wintypes

import wx

import impostazioni as modulo_impostazioni
import mercato
import regole as modulo_regole
import staff
import suoni
import testi
from gui import aspetto, dialoghi
from gui.dal_vivo import annunci_condivisi
from gui.dialoghi import Cifra, Lettura, OpzioniAmichevole, SceltaGiocatore, _Dialogo, _SceltaConTesto
from gui.elenco_virtuale import ElencoVirtuale
from gui.sfide import LanciaSfida
from modelli import probabilita_accettazione
from utilita import adesso_utc

# I ritardi della finestra, in secondi: il ricalcolo dopo l'ultima mossa, quello dei dialoghi di MESS; l'annuncio dei
# trovati, scelta di Gabriele dopo la prova del prototipo; la scheda che segue la riga; il suono del valore scritto
# quando ci si ferma.
RITARDO_DEL_RICALCOLO = dialoghi.RITARDO_DEL_SUONO_AL_VOLO / 1000
RITARDO_DELL_ANNUNCIO = 1.0
RITARDO_DELLA_SCHEDA = dialoghi.RITARDO_DEL_SUONO_AL_VOLO / 1000
RITARDO_DEL_SUONO = dialoghi.RITARDO_DEL_SUONO_AL_VOLO / 1000
# Le due schede, con i loro nomi e i loro suoni.
RISULTATI, FILTRI = range(2)
NOMI_DELLE_SCHEDE = ("Risultati", "Filtri")
SUONI_DELLE_SCHEDE = ("scheda_risultati", "scheda_filtri")
# Il suono d'apertura di ogni porta d'ingresso; Assumi dello staff, porta None, apre come il mercato degli allenatori.
SUONI_DELLE_PORTE = {"mercato": "dialogo_mercato", "allenatori": "dialogo_mercato_allenatori", "ricerca": "dialogo_ricerca", "amichevole": "dialogo_avversario",
                     None: "dialogo_mercato_allenatori"}
# Le voci del collegamento e del bersaglio, coi loro suoni.
COLLEGAMENTI_DELLA_SCELTA = ((mercato.E, "e, insieme"), (mercato.O, "o, in alternativa"))
SUONI_DEI_COLLEGAMENTI = {mercato.E: "collegamento_e", mercato.O: "collegamento_o"}
BERSAGLI_DELLA_SCELTA = tuple((bersaglio, mercato.NOMI_DEI_BERSAGLI[bersaglio]) for bersaglio in mercato.BERSAGLI)
SUONI_DEI_BERSAGLI = {mercato.GIOCATORI: "bersaglio_giocatori", mercato.ALLENATORI: "bersaglio_allenatori"}
# Il timbro della caratteristica scelta, uno per tipo.
SUONI_DEI_TIPI = {modulo_regole.NUMERO: "regola_caratteristica_numero", modulo_regole.CLASSE: "regola_caratteristica_classe",
                  modulo_regole.TESTO: "regola_caratteristica_testo", modulo_regole.SCELTA: "regola_caratteristica_scelta",
                  modulo_regole.SI_NO: "regola_caratteristica_si_no"}
# Lo stato del valore della regola in preparazione, e il suono di quando cambia: vuoto, valido, da correggere.
VUOTO, VALIDO, DA_CORREGGERE = "vuoto", "valido", "da_correggere"
SUONI_DEL_VALORE = {VUOTO: "regola_valore_tolto", VALIDO: "regola_valore_scritto", DA_CORREGGERE: "regola_valore_da_correggere"}
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


def voci_del_valore(car):
    """Le voci della scelta del Valore per una scelta o un sì o no: nessun valore in cima, poi le voci, o sì e no."""
    if car.tipo == modulo_regole.SI_NO:
        return ((None, testi.NESSUN_VALORE), (True, "sì"), (False, "no"))
    return ((None, testi.NESSUN_VALORE), *modulo_regole.voci(car))


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
    No già scelto. In risultato resta il nome, senza gli spazi in testa e in coda. Col costruttore di regole, nota dice
    che cosa ne è della regola in preparazione, in un campo da leggere dopo il nome: entra nel preset, o resta fuori, e
    perché; senza nota il campo non c'è.
    """

    GRAZIA_ALL_APERTURA = True

    def __init__(self, genitore, filtri_di_ricerca, proposta="", impostazioni=None, nota=None):
        super().__init__(genitore, "Salva filtri")
        self.filtri_di_ricerca = filtri_di_ricerca
        self.impostazioni = impostazioni
        self.risultato = None
        self.etichetta("&Nome del preset")
        self.nome = self.aggiungi(wx.TextCtrl(self.pannello, value=proposta))
        self.nota = None
        if nota:
            self.etichetta("&Regola in preparazione")
            self.nota = self.aggiungi(wx.TextCtrl(self.pannello, value=nota, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2))
            self.nota.SetMinSize((-1, self.nota.GetCharHeight() * 3))
            aspetto.applica(self.nota, modulo_impostazioni.valide(impostazioni))
        salva, _annulla = self.pulsanti((wx.ID_OK, "&Salva"), (wx.ID_CANCEL, "Annulla"))
        salva.Bind(wx.EVT_BUTTON, self.conferma)
        self.completa((440, 240))
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


# La finestra.

class MercatoERicerca(_ConTestiDaLeggere, _Dialogo):
    """
    La finestra Mercato e ricerca. porta è una di mercato.PORTE, da cui la finestra riapre col suo ultimo preset e a
    cui alla chiusura lascia la voce scelta, i filtri attuali e la regola in preparazione; None per Assumi dello staff,
    che apre sugli allenatori liberi col posto dato e non ricorda niente. pianifica(secondi, funzione) fa i rimandi,
    wx.CallLater di serie; annunci sono quelli che dicono i trovati, di serie quelli della sessione. In risultato, alla
    chiusura, gli EsitiDellaFinestra. Le prove sostituiscono pianifica, annunci e _modale.
    Lo stato dei filtri è fatto di filtri, le regole dell'elenco e l'ordine, e di preparazione, la regola in
    preparazione; quelli che contano, con la preparazione se ha un valore valido, li dà _contano. attuali e
    _preparazione_attuale sono quelli della voce in cima alla casella, Filtri attuali, non salvati: mentre la casella sta
    su un preset li tiene da parte, e la voce in cima li riprende com'erano.
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
        self.memoria = mercato.Memoria(mondo)
        self.esiti = EsitiDellaFinestra()
        self.risultato = None
        self.filtri_di_ricerca = mercato.filtri_di_ricerca_del_mondo(mondo)
        if porta is None:
            scelta = "allenatori_liberi"
            self.attuali = mercato.filtri_di_serie(scelta)
            ricordata = mercato.Preparazione(mercato.E, mercato.ALLENATORI, "nome", "contiene", "")
        else:
            stato = mercato.stato_della_porta(mondo, porta)
            scelta, self.attuali, ricordata = stato.scelta, stato.attuali, stato.preparazione
        try:
            self.filtri = mercato.filtri_della_voce(self.filtri_di_ricerca, scelta, self.attuali)
        except KeyError:
            scelta = mercato.PRESET_DELLA_PORTA[porta]
            self.filtri = mercato.filtri_di_serie(scelta)
        self.scelta = scelta
        # All'apertura con un preset il valore in preparazione si svuota; Ctrl+F la rimette sul nome.
        self.preparazione = ricordata if scelta is None else mercato.svuota_il_valore(ricordata)
        if porta == "ricerca":
            self.preparazione = mercato.preparazione_della_ricerca_veloce(self.preparazione)
        self._preparazione_attuale = self.preparazione if scelta is None else ricordata
        # Il tuo preset da cui vengono i filtri attuali: Salva filtri ne propone il nome.
        self._origine = None
        self._spostato = None
        self.righe = []
        self.ultima_riga = -1
        self._ordine_delle_righe = self.filtri.ordine
        self._in_ricalcolo = False
        self._applico = False
        self._chiusa = False
        self._persona_della_scheda = None
        self._testo_della_scheda = None
        self._testo_dei_trovati = None
        self._ultimo_annuncio = None
        self._ultimo_canc = float("-inf")
        self._vuoto = dialoghi._ElencoCheSiRestringe()
        self._riquadri_delle_schede = []
        self._caratteristiche = []
        self._operatori = []
        self._voci_del_valore = []
        # Il resto dei suoni dell'apertura, che aspetta il suo turno: alla chiusura si ferma.
        self._fila = None
        self._costruisci()
        self._rifai_la_casella()
        self._scrivi_i_controlli()
        # Il ricalcolo chiede la scheda col suo rimando, anche adesso: all'apertura il fuoco va sull'elenco, e la
        # scheda, che costa una quarantina di millesimi, si scrive subito dopo, o appena prende il fuoco.
        self.ricalcola()
        self._ultimo_annuncio = self._testo_dell_annuncio()
        self._aggiorna_la_situazione()
        self._aggiorna_l_offerta()
        self.Bind(wx.EVT_CHAR_HOOK, self._tasto)
        self.Bind(wx.EVT_CLOSE, self._alla_chiusura)
        self.completa((980, 720))
        if porta == "ricerca":
            self.libro.SetSelection(FILTRI)
            self.valore_scritto.SetFocus()
            self.valore_scritto.SelectAll()
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
        lo dice quando il fuoco ci entra, come il riquadro della regola in preparazione.
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
    def _coppia(genitore, griglia, etichetta, fabbrica):
        """
        Etichetta e controllo sulla stessa riga della griglia: l'etichetta nasce prima, e NVDA ne prende il nome del
        controllo. Restituisce l'etichetta e il controllo.
        """
        testo = wx.StaticText(genitore, label=etichetta)
        griglia.Add(testo, 0, wx.ALIGN_CENTER_VERTICAL)
        controllo = fabbrica(genitore)
        griglia.Add(controllo, 1, wx.EXPAND)
        return testo, controllo

    def _campo(self, genitore, griglia, etichetta, fabbrica):
        return self._coppia(genitore, griglia, etichetta, fabbrica)[1]

    @staticmethod
    def _mostra_coppia(etichetta, controllo, visibile, testo):
        """
        La coppia di etichetta e controllo, visibile o nascosta, con l'etichetta data; vero se è cambiato qualcosa.
        Nascosta, l'etichetta perde la sua lettera: il passo l'ha misurato, la lettera di un'etichetta nascosta porta
        il fuoco al primo controllo visibile dopo di lei, e Alt+L senza regole finiva sul bersaglio.
        """
        voluto = testo if visibile else testo.replace("&", "")
        cambiata = etichetta.GetLabel() != voluto or controllo.IsShown() != visibile
        if etichetta.GetLabel() != voluto:
            etichetta.SetLabel(voluto)
        if controllo.IsShown() != visibile:
            etichetta.Show(visibile)
            controllo.Show(visibile)
        return cambiata

    def _pulsante(self, genitore, sizer, etichetta, azione, identificativo=wx.ID_ANY):
        pulsante = wx.Button(genitore, identificativo, etichetta)
        sizer.Add(pulsante, 0, wx.ALL, 4)
        pulsante.Bind(wx.EVT_BUTTON, azione)
        return pulsante

    def _costruisci(self):
        self.libro = wx.Notebook(self.pannello)
        self.aggiungi(self.libro, 1)
        self._costruisci_i_risultati(*self._pagina(NOMI_DELLE_SCHEDE[RISULTATI]))
        self._costruisci_i_filtri(*self._pagina(NOMI_DELLE_SCHEDE[FILTRI]))
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_chiudi = self._pulsante(self.pannello, riga, "&Chiudi", self.chiudi_la_finestra, wx.ID_CLOSE)
        self.sizer.Add(riga, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

    def _costruisci_i_risultati(self, pagina, sizer):
        griglia = self._griglia(sizer)
        # Su più righe: wx toglie dal giro del Tab, e quindi anche dalla sua lettera, un campo a una riga in sola lettura.
        # Senza andare a capo, dalla verifica con la lente di NVDA: a capo a metà di una frase il display braille la
        # spezzava; la riga in più è per la barra orizzontale.
        self.situazione = self._campo(pagina, griglia, "&Situazione",
                                      lambda g: wx.TextCtrl(g, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP))
        self.situazione.SetMinSize((-1, self.situazione.GetCharHeight() * 2))
        aspetto.applica(self.situazione, self.impostazioni)
        self.casella_preset = self._campo(pagina, griglia, "&Preset dei filtri", lambda g: wx.Choice(g))
        self.casella_preset.Bind(wx.EVT_CHOICE, self._al_preset)
        self.casella_preset.Bind(wx.EVT_KILL_FOCUS, self._casella_lasciata)
        self.etichetta_trovati = wx.StaticText(pagina, label="&Trovati")
        sizer.Add(self.etichetta_trovati, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.elenco = ElencoVirtuale(pagina, self._testo_della_riga)
        # Soltanto le righe degli allenatori si riscrivono a ogni domanda: dicono fino a che ora sono riservati a te, che segue l'ora vera.
        self.elenco.riscrivi_sempre = lambda indice: indice < len(self.righe) and self.righe[indice].allenatore
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
        """
        La scheda Filtri, nell'ordine del Tab: Trovati, poi nel riquadro della regola in preparazione collegamento,
        bersaglio, caratteristica, operatore e valore, poi Aggiungi regola, Azzera, l'elenco delle regole, Ordina per e
        Salva filtri. Il Valore è una coppia di etichetta e scelta e una di etichetta e campo: se ne vede una sola.
        """
        griglia = self._griglia(sizer)
        # Su più righe e senza andare a capo, come la Situazione: una riga per informazione, alto quattro righe più la barra.
        self.campo_trovati = self._campo(pagina, griglia, "&Trovati",
                                         lambda g: wx.TextCtrl(g, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_DONTWRAP))
        self.campo_trovati.SetMinSize((-1, self.campo_trovati.GetCharHeight() * 5))
        aspetto.applica(self.campo_trovati, self.impostazioni)
        scatola, riquadro = self._riquadro(pagina, "Regola in preparazione", sizer)
        griglia = self._griglia(riquadro)
        testi_delle_voci = [testo for _chiave, testo in COLLEGAMENTI_DELLA_SCELTA]
        self.etichetta_collegamento, self.scelta_collegamento = self._coppia(scatola, griglia, "Co&llegamento", lambda g: wx.Choice(g, choices=testi_delle_voci))
        self.scelta_bersaglio = self._campo(scatola, griglia, "&Bersaglio", lambda g: wx.Choice(g, choices=[testo for _b, testo in BERSAGLI_DELLA_SCELTA]))
        self.scelta_caratteristica = self._campo(scatola, griglia, "C&aratteristica", lambda g: wx.Choice(g))
        self.scelta_operatore = self._campo(scatola, griglia, "&Operatore", lambda g: wx.Choice(g))
        self.etichetta_valore_scelto, self.valore_scelto = self._coppia(scatola, griglia, "&Valore", lambda g: wx.Choice(g))
        self.etichetta_valore_scritto, self.valore_scritto = self._coppia(scatola, griglia, "&Valore", lambda g: wx.TextCtrl(g))
        self.valore_scritto.SetMaxLength(modulo_regole.LUNGHEZZA_MASSIMA_DEL_TESTO)
        self.scelta_collegamento.Bind(wx.EVT_CHOICE, self._al_collegamento)
        self.scelta_bersaglio.Bind(wx.EVT_CHOICE, self._al_bersaglio)
        self.scelta_caratteristica.Bind(wx.EVT_CHOICE, self._alla_caratteristica)
        self.scelta_operatore.Bind(wx.EVT_CHOICE, self._all_operatore)
        self.valore_scelto.Bind(wx.EVT_CHOICE, self._al_valore_scelto)
        self.valore_scritto.Bind(wx.EVT_TEXT, self._al_valore_scritto)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_aggiungi = self._pulsante(pagina, riga, "A&ggiungi regola", lambda event: self.aggiungi_la_regola())
        self.pulsante_azzera = self._pulsante(pagina, riga, "A&zzera", lambda event: self.azzera())
        sizer.Add(riga, 0, wx.ALL, 4)
        sizer.Add(wx.StaticText(pagina, label="&Regole"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
        self.regole = wx.ListBox(pagina, style=wx.LB_SINGLE)
        self.regole.SetMinSize((-1, self.regole.GetCharHeight() * 6))
        sizer.Add(self.regole, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.regole.Bind(wx.EVT_KEY_DOWN, self._tasto_sulle_regole)
        griglia = self._griglia(sizer)
        self._ordini = [(chiave, nome[0].upper() + nome[1:]) for chiave, nome in mercato.ORDINI]
        self.scelta_ordine = self._campo(pagina, griglia, "Ordina &per", lambda g: wx.Choice(g, choices=[testo for _chiave, testo in self._ordini]))
        self.scelta_ordine.Bind(wx.EVT_CHOICE, self._all_ordine)
        riga = wx.BoxSizer(wx.HORIZONTAL)
        self.pulsante_salva = self._pulsante(pagina, riga, "&Salva filtri...", lambda event: self.salva_filtri())
        sizer.Add(riga, 0, wx.ALL, 4)
        # I controlli della scheda Filtri su cui Invio porta all'elenco dei Risultati.
        self._controlli_dei_filtri = [self.campo_trovati, self.scelta_collegamento, self.scelta_bersaglio, self.scelta_caratteristica, self.scelta_operatore,
                                      self.valore_scelto, self.valore_scritto, self.regole, self.scelta_ordine]

    # I controlli dai filtri.

    @staticmethod
    def _metti(scelta, voci, valore):
        """La scelta sulla voce del valore; un valore che fra le voci non c'è lascia la prima."""
        posto = next((i for i, (v, _testo) in enumerate(voci) if v == valore and type(v) is type(valore)), 0)
        if scelta.GetSelection() != posto:
            scelta.SetSelection(posto)

    def _metti_le_voci(self, scelta, voci, valore):
        """Le voci della scelta, cambiate soltanto se sono diverse, e la scelta sul valore: il passo ha misurato che Set e SetSelection non mandano eventi."""
        testi_delle_voci = [testo for _valore, testo in voci]
        if scelta.GetItems() != testi_delle_voci:
            scelta.Set(testi_delle_voci)
        self._metti(scelta, voci, valore)

    def _caratteristica(self):
        return mercato.caratteristica(self.preparazione.bersaglio, self.preparazione.caratteristica)

    def _scrivi_la_preparazione(self):
        """
        I controlli della regola in preparazione: il collegamento soltanto con delle regole, e il Valore della
        caratteristica, scelta o campo, soltanto con un operatore che ne vuole uno. Dalle verifiche del costruttore: senza
        regole il collegamento torna alla e, perché una o rimasta mentre era nascosto, dopo Canc o Azzera, tornava con la
        prima regola nuova e apriva un'alternativa che nessuno aveva chiesto; con non ha il dato e ha il dato il Valore non
        si vede, perché quello che ci si scrive non conta.
        """
        if not self.filtri.regole and self.preparazione.collegamento != mercato.E:
            self.preparazione = dataclasses.replace(self.preparazione, collegamento=mercato.E)
        prep = self.preparazione
        car = self._caratteristica()
        serve = prep.operatore not in modulo_regole.SENZA_VALORE
        self._applico = True
        try:
            cambiata = self._mostra_coppia(self.etichetta_collegamento, self.scelta_collegamento, bool(self.filtri.regole), "Co&llegamento")
            self._metti(self.scelta_collegamento, COLLEGAMENTI_DELLA_SCELTA, prep.collegamento)
            self._metti(self.scelta_bersaglio, BERSAGLI_DELLA_SCELTA, prep.bersaglio)
            self._caratteristiche = [(chiave, c.nome) for chiave, c in mercato.CATALOGO[prep.bersaglio].items()]
            self._metti_le_voci(self.scelta_caratteristica, self._caratteristiche, prep.caratteristica)
            self._operatori = list(modulo_regole.operatori(car))
            self._metti_le_voci(self.scelta_operatore, self._operatori, prep.operatore)
            a_scelta = car.tipo in (modulo_regole.SCELTA, modulo_regole.SI_NO)
            etichetta = testi.etichetta_del_valore(car)
            cambiata = self._mostra_coppia(self.etichetta_valore_scelto, self.valore_scelto, a_scelta and serve, etichetta) or cambiata
            cambiata = self._mostra_coppia(self.etichetta_valore_scritto, self.valore_scritto, not a_scelta and serve, etichetta) or cambiata
            if a_scelta:
                self._voci_del_valore = list(voci_del_valore(car))
                self._metti_le_voci(self.valore_scelto, self._voci_del_valore, prep.valore)
            elif self.valore_scritto.GetValue() != prep.valore:
                self.valore_scritto.ChangeValue(prep.valore)
        finally:
            self._applico = False
        if cambiata:
            self.libro.GetPage(FILTRI).Layout()

    def _scrivi_le_regole(self, posto=0):
        """L'elenco delle regole, una riga ciascuna, o la riga che dice come si aggiungono; la linguetta e il riquadro della scheda col loro conto."""
        regole = self.filtri.regole
        righe = [testi.regola_a_parole(regola, i, regole) for i, regola in enumerate(regole)] or [testi.NESSUNA_REGOLA]
        self._riscrivi(self.regole, righe, posto)
        testo = testi.linguetta_dei_filtri(len(regole))
        if self.libro.GetPageText(FILTRI) != testo:
            self.libro.SetPageText(FILTRI, testo)
            # Il riquadro della scheda dice lo stesso della linguetta: è il nome che NVDA legge entrando con Ctrl+Tab.
            self._riquadri_delle_schede[FILTRI].SetLabel(testo)
            self.libro.GetPage(FILTRI).Layout()

    def _scrivi_i_controlli(self):
        """Tutti i controlli della scheda Filtri dai filtri e dalla preparazione, senza che i loro gestori li prendano per mosse."""
        self._scrivi_le_regole()
        self._scrivi_la_preparazione()
        self._applico = True
        try:
            self._metti(self.scelta_ordine, self._ordini, self.filtri.ordine)
        finally:
            self._applico = False
        self._stato_suonato = self._stato_del_valore()

    # Le mosse.

    def _contano(self):
        """I filtri che contano: le regole dell'elenco, più la regola in preparazione se ha un valore valido, e l'ordine."""
        return mercato.con_la_preparazione(self.filtri, self.preparazione)

    def _lascia_la_voce_in_cima(self):
        """Prima che la casella vada su un preset: la voce in cima tiene da parte i filtri attuali e la loro regola in preparazione."""
        if self.scelta is None:
            self.attuali = self.filtri
            self._preparazione_attuale = self.preparazione

    def _dopo_la_mossa(self, prima):
        """
        Dopo ogni mossa, con prima i filtri che contavano: se contano filtri diversi, la casella va in silenzio sulla voce
        in cima, che tiene i filtri fatti a mano, e se erano quelli di un tuo preset Salva filtri ne proporrà il nome;
        guardare le caratteristiche col valore vuoto non la stacca dal suo preset. Poi il ricalcolo e l'annuncio,
        ciascuno col suo ritardo dall'ultima mossa.
        """
        if self.scelta is not None and self._contano() != prima:
            self._origine = self.scelta if _di_gabriele(self.scelta) else None
            self.scelta = None
            self._metti_la_casella(0)
        if self.scelta is None:
            self.attuali = self.filtri
            self._preparazione_attuale = self.preparazione
        self._ricalcolo.chiedi()
        self._annuncio.chiedi()

    def _con_la_preparazione(self, **campi):
        """La regola in preparazione cambia, e la mossa conta come tale."""
        prima = self._contano()
        self.preparazione = dataclasses.replace(self.preparazione, **campi)
        return prima

    def _al_collegamento(self, event=None):
        collegamento = COLLEGAMENTI_DELLA_SCELTA[self.scelta_collegamento.GetSelection()][0]
        if self._applico or collegamento == self.preparazione.collegamento:
            return
        prima = self._con_la_preparazione(collegamento=collegamento)
        suoni.suona(SUONI_DEI_COLLEGAMENTI[collegamento])
        self._dopo_la_mossa(prima)

    def _al_bersaglio(self, event=None):
        bersaglio = BERSAGLI_DELLA_SCELTA[self.scelta_bersaglio.GetSelection()][0]
        if self._applico or bersaglio == self.preparazione.bersaglio:
            return
        prima = self._contano()
        # Risposta di Gabriele del 24 ottobre sera: giocatori e allenatori non si mescolano, quindi con delle regole il
        # cambio di bersaglio le toglie, dopo la domanda col No già scelto; al No il bersaglio resta quello di prima.
        if self.filtri.regole:
            if not self._conferma(testi.domanda_cambio_di_bersaglio(len(self.filtri.regole), bersaglio)):
                self._metti(self.scelta_bersaglio, BERSAGLI_DELLA_SCELTA, self.preparazione.bersaglio)
                return
            self.filtri = mercato.Filtri((), self.filtri.ordine)
            self._scrivi_le_regole()
        self.preparazione = mercato.con_il_bersaglio(self.preparazione, bersaglio)
        self._scrivi_la_preparazione()
        self._stato_suonato = self._stato_del_valore()
        suoni.suona(SUONI_DEI_BERSAGLI[bersaglio])
        self._dopo_la_mossa(prima)

    def _alla_caratteristica(self, event=None):
        chiave = self._caratteristiche[self.scelta_caratteristica.GetSelection()][0]
        if self._applico or chiave == self.preparazione.caratteristica:
            return
        prima = self._contano()
        self.preparazione = mercato.con_la_caratteristica(self.preparazione, chiave)
        self._scrivi_la_preparazione()
        self._stato_suonato = VUOTO
        suoni.suona(SUONI_DEI_TIPI[self._caratteristica().tipo])
        self._dopo_la_mossa(prima)

    def _all_operatore(self, event=None):
        operatore = self._operatori[self.scelta_operatore.GetSelection()][0]
        if self._applico or operatore == self.preparazione.operatore:
            return
        prima = self._con_la_preparazione(operatore=operatore)
        # Dalle verifiche del costruttore: con non ha il dato e ha il dato il Valore si nasconde, e con gli altri torna. Lo
        # stato del valore si segna in silenzio, perché suona l'operatore, e il primo tasto scritto dopo non suona per niente.
        self._scrivi_la_preparazione()
        self._lascia_il_valore()
        suoni.suona("regola_operatore")
        self._dopo_la_mossa(prima)

    def _al_valore_scelto(self, event=None):
        valore = self._voci_del_valore[self.valore_scelto.GetSelection()][0]
        if self._applico or (valore == self.preparazione.valore and type(valore) is type(self.preparazione.valore)):
            return
        prima = self._con_la_preparazione(valore=valore)
        suoni.suona("regola_valore_tolto" if valore is None else "regola_valore_scelto")
        self._dopo_la_mossa(prima)

    def _al_valore_scritto(self, event=None):
        """
        Il valore scritto: i caratteri di controllo, come un a capo incollato, si tolgono mentre si scrive, perché la
        porta possa ricordarlo; il suono arriva quando ci si ferma, e soltanto se il valore cambia stato.
        """
        if self._applico:
            return
        scritto = self.valore_scritto.GetValue()
        pulito = modulo_regole.senza_caratteri_di_controllo(scritto)
        if pulito != scritto:
            punto = self.valore_scritto.GetInsertionPoint()
            self.valore_scritto.ChangeValue(pulito)
            self.valore_scritto.SetInsertionPoint(min(punto, len(pulito)))
        if pulito == self.preparazione.valore:
            return
        prima = self._con_la_preparazione(valore=pulito)
        self._suono_fermo.chiedi()
        self._dopo_la_mossa(prima)

    def _stato_del_valore(self):
        """Lo stato della regola in preparazione: VALIDO se conta, VUOTO col Valore vuoto o su nessun valore, DA_CORREGGERE con un valore sbagliato."""
        regola, perche = mercato.regola_pronta(self.preparazione)
        if regola is not None:
            return VALIDO
        return VUOTO if perche is None else DA_CORREGGERE

    def _suona_quando_ci_si_ferma(self):
        """Il suono del valore scritto, quando ci si ferma, soltanto se il suo stato è cambiato dall'ultima volta."""
        stato = self._stato_del_valore()
        if stato != self._stato_suonato:
            self._stato_suonato = stato
            suoni.suona(SUONI_DEL_VALORE[stato])

    def _lascia_il_valore(self):
        """
        Il suono del valore scritto che aspettava non serve più, perché sei passato ad altro, e lo stato del valore si segna
        come suonato, in silenzio. Dalla verifica dei suoni del costruttore: dopo Invio, un dialogo interno o il cambio di
        scheda il suono arrivava 350 millesimi dopo l'ultimo tasto, sopra la scheda nuova, il dialogo o il campo da correggere.
        """
        self._suono_fermo.ferma()
        self._stato_suonato = self._stato_del_valore()

    def _all_ordine(self, event=None):
        ordine = self._ordini[self.scelta_ordine.GetSelection()][0]
        if self._applico or ordine == self.filtri.ordine:
            return
        prima = self._contano()
        self.filtri = dataclasses.replace(self.filtri, ordine=ordine)
        suoni.suona("mercato_ordine_cambiato")
        self._dopo_la_mossa(prima)

    def _valore_visibile(self):
        return self.valore_scelto if self.valore_scelto.IsShown() else self.valore_scritto

    def aggiungi_la_regola(self):
        """
        Aggiungi regola: la regola in preparazione va in fondo all'elenco, si svuota soltanto il valore e il fuoco va
        sulla regola nuova. Conta come un Invio: Windows preme il pulsante e porta il fuoco sull'elenco delle regole, e
        l'Invio rimandato da NVDA, che il gancio vede arrivare lì, si mangia invece di portare ai Risultati. Con una
        regola vuota o sbagliata l'avviso e il fuoco sul Valore; al limite delle regole il suo suono.
        """
        if self._ripetuta("aggiungi"):
            return
        nuovi, perche = mercato.aggiungi_la_regola(self.filtri, self.preparazione)
        if perche == mercato.AL_LIMITE:
            self.leggi(testi.regola_non_aggiunta(self.preparazione, perche), "regole_al_limite", self.regole)
            return
        if perche is not None:
            self.avvisa(testi.regola_non_aggiunta(self.preparazione, perche), self._valore_visibile())
            return
        prima = self._contano()
        self.filtri = nuovi
        self.preparazione = mercato.svuota_il_valore(self.preparazione)
        self._scrivi_le_regole(len(nuovi.regole) - 1)
        self._scrivi_la_preparazione()
        self._stato_suonato = VUOTO
        self.regole.SetFocus()
        self.ultimo_invio = dialoghi._adesso()
        suoni.suona("regola_aggiunta")
        self._dopo_la_mossa(prima)

    def azzera(self):
        """Azzera: toglie tutte le regole, chiedendo prima, col No già scelto, quando sono più d'una; senza regole il tasto a vuoto."""
        if self._ripetuta("azzera"):
            return
        quante = len(self.filtri.regole)
        if not quante:
            suoni.suona("nessuna_selezione")
            return
        if quante > 1 and not self._conferma(testi.domanda_azzera_le_regole(quante)):
            self._torna(self.pulsante_azzera)
            return
        prima = self._contano()
        self.filtri = mercato.Filtri((), self.filtri.ordine)
        self._scrivi_le_regole()
        self._scrivi_la_preparazione()
        suoni.suona("regole_azzerate")
        self._dopo_la_mossa(prima)
        self._torna(self.pulsante_azzera)

    def _tasto_sulle_regole(self, event):
        """
        I tasti dell'elenco delle regole: Canc toglie la regola scelta, Ctrl+Su e Ctrl+Giù la spostano, E ed O cambiano il
        suo collegamento. Gli altri vanno all'elenco. Il passo ha misurato che, messi in coda come quelli veri, arrivano
        qui coi loro modificatori; il Canc vero ha il codice del tasto, quello del tastierino col blocco spento l'altro.
        """
        codice = event.GetKeyCode()
        if codice in (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE) and not event.HasAnyModifiers():
            self.togli_la_regola(event.IsAutoRepeat())
        elif codice in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_NUMPAD_UP, wx.WXK_NUMPAD_DOWN) and event.ControlDown() and not (event.AltDown() or event.ShiftDown()):
            self.sposta_la_regola(-1 if codice in (wx.WXK_UP, wx.WXK_NUMPAD_UP) else 1)
        elif codice in (ord("E"), ord("O")) and not event.HasAnyModifiers():
            self.cambia_il_collegamento(mercato.E if codice == ord("E") else mercato.O)
        else:
            event.Skip()

    def _regola_scelta(self):
        """Il posto della regola scelta nell'elenco, o None, col tasto a vuoto, se non ci sono regole."""
        posto = self.regole.GetSelection()
        if not self.filtri.regole or posto == wx.NOT_FOUND or posto >= len(self.filtri.regole):
            suoni.suona("nessuna_selezione")
            return None
        return posto

    def togli_la_regola(self, ripetuto=False):
        """Canc: la regola scelta esce, e la scelta resta allo stesso posto. Un tasto tenuto giù, o un secondo Canc entro mezzo secondo, si ignora."""
        adesso = dialoghi._adesso()
        precedente, self._ultimo_canc = self._ultimo_canc, adesso
        if ripetuto or adesso - precedente < dialoghi.RIPETIZIONE_IGNORATA:
            return
        posto = self._regola_scelta()
        if posto is None:
            return
        prima = self._contano()
        self.filtri = mercato.togli_la_regola(self.filtri, posto)
        self._scrivi_le_regole(min(posto, len(self.filtri.regole) - 1))
        self._scrivi_la_preparazione()
        suoni.suona("regola_tolta")
        self._rileggi_la_regola_scelta(posto)
        self._dopo_la_mossa(prima)

    def sposta_la_regola(self, verso):
        """Ctrl+Su e Ctrl+Giù: la regola scelta si sposta di un posto, e la scelta la segue; al bordo il suo suono."""
        posto = self._regola_scelta()
        if posto is None:
            return
        spostata = mercato.sposta_la_regola(self.filtri, posto, verso)
        if spostata is None:
            suoni.suona("regola_al_bordo")
            return
        prima = self._contano()
        self.filtri, nuovo = spostata
        self._scrivi_le_regole(nuovo)
        suoni.suona("regola_spostata_su" if verso < 0 else "regola_spostata_giu")
        self._dopo_la_mossa(prima)

    def cambia_il_collegamento(self, collegamento):
        """
        E ed O sull'elenco delle regole: il collegamento della regola scelta. Dalle verifiche del costruttore, quando non
        cambia niente ci sono due suoni loro, al posto del tasto a vuoto, che è di quando non c'è niente di scelto: la O
        sulla prima regola, che ha sempre la e, e il collegamento che la regola ha già, anche la E sulla prima; e non
        conta come mossa.
        """
        posto = self._regola_scelta()
        if posto is None:
            return
        nuovi = mercato.cambia_il_collegamento(self.filtri, posto, collegamento)
        if nuovi is None:
            suoni.suona("collegamento_della_prima" if posto == 0 and collegamento == mercato.O else "collegamento_invariato")
            return
        prima = self._contano()
        self.filtri = nuovi
        self._scrivi_le_regole(posto)
        suoni.suona(SUONI_DEI_COLLEGAMENTI[collegamento])
        self._rileggi_la_regola_scelta(posto)
        self._dopo_la_mossa(prima)

    def _rileggi_la_regola_scelta(self, scelta_di_prima):
        """
        Dopo Canc, E ed O, quando l'elenco delle regole ha il fuoco e la scelta resta sulla stessa riga, che però dice
        un'altra regola: dalla verifica con la lente di NVDA, il fuoco tornava sullo stesso oggetto, e NVDA, che scarta il
        fuoco ripetuto, non leggeva la riga nuova. Il nome cambiato di quella riga, mandato a Windows, NVDA lo legge per
        l'oggetto col fuoco, alla voce e al display. Se la scelta si sposta, basta il fuoco nuovo, e così niente si legge
        due volte.
        """
        posto = self.regole.GetSelection()
        if posto == wx.NOT_FOUND or posto != scelta_di_prima or not _stesso(dialoghi.controllo_col_fuoco(), self.regole):
            return
        wx.Accessible.NotifyEvent(wx.ACC_EVENT_OBJECT_NAMECHANGE, self.regole, wx.OBJID_CLIENT, posto + 1)

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
        Una voce della casella dei preset: un preset si applica intero, con le sue regole e il suo ordine, e svuota il
        valore in preparazione; la voce in cima riprende tutto com'era, regola in preparazione compresa. Salva filtri si
        apre soltanto scelto dall'elenco aperto, con Invio o col clic, mai con le frecce; la voce già applicata non fa
        niente. Dalla verifica con la lente di NVDA: uscendo con Tab, Maiusc+Tab, Alt+lettera o Ctrl+Tab dall'elenco
        aperto su Salva filtri, Windows manda prima l'uscita del fuoco, con la casella ancora sulla voce di prima, e poi
        la scelta di Salva filtri, a elenco chiuso; adesso la casella torna in silenzio sulla voce applicata.
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
            self.filtri, self.preparazione, suono = self.attuali, self._preparazione_attuale, "filtri_attuali_ripresi"
        else:
            self._lascia_la_voce_in_cima()
            self.filtri = mercato.filtri_della_voce(self.filtri_di_ricerca, voce.scelta, self.attuali)
            self.preparazione = mercato.svuota_il_valore(self.preparazione)
            suono = "mercato_scelta_cambiata"
        self.scelta = voce.scelta
        self._posto_applicato = posto
        self._scrivi_i_controlli()
        suoni.suona(suono)
        self._ricalcolo.chiedi()
        self._annuncio.chiedi()

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
        """
        Salva filtri: le regole dell'elenco e l'ordine diventano un tuo preset. La regola in preparazione che conta entra
        come ultima regola, se le regole sono meno di 50; il dialogo dice che cosa ne è, e perché resta fuori.
        """
        if self._ripetuta("salva_filtri"):
            return
        fuoco = dialoghi.controllo_col_fuoco()
        da_salvare, esito = mercato.filtri_per_salva_filtri(self.filtri, self.preparazione)
        nota = testi.preparazione_nel_preset(self.preparazione, esito)
        with self._interno(SalvaFiltri(self, self.filtri_di_ricerca, self._nome_proposto(), self.impostazioni, nota), "dialogo_salva_filtri") as dialogo:
            nome = dialogo.risultato if self._modale(dialogo) == wx.ID_OK else None
        if nome is None:
            suoni.suona("annullato")
            self._metti_la_casella(self._posto_applicato)
            self._torna(fuoco)
            return
        nuovi = self.filtri_di_ricerca.copia()
        try:
            preset, sostituito = mercato.salva_preset(nuovi, nome, da_salvare)
        except ValueError as errore:
            self._metti_la_casella(self._posto_applicato)
            self.avvisa(str(errore), fuoco)
            return
        if self.preset_cambiati(nuovi, testi.esito_preset_salvato(preset.nome, sostituito), "preset_sostituito" if sostituito else "preset_salvato"):
            # Il preset salvato è la voce scelta, che la porta riaprirà; la voce in cima tiene da parte quello che c'era.
            self._lascia_la_voce_in_cima()
            if esito == mercato.AGGIUNTA:
                self.filtri = da_salvare
                self.preparazione = mercato.svuota_il_valore(self.preparazione)
                self._scrivi_i_controlli()
                self._scrivi_le_regole(len(self.filtri.regole) - 1)
            self.scelta = preset.numero
            self._metti_la_casella(mercato.posto_della_scelta(self.voci, preset.numero))
            self._ricalcolo.chiedi()
        else:
            self._metti_la_casella(self._posto_applicato)
        self._torna(fuoco)

    def preset_cambiati(self, nuovi, esito, suono, chi_avvisa=None, spostato=None):
        """
        I preset di Gabriele dopo un'operazione: passano subito nel mondo, e l'operazione fra gli esiti della finestra,
        una riga sola per gli spostamenti di seguito dello stesso preset; la casella si rifà. Una scelta o un'origine che
        punta a un preset eliminato torna alla voce in cima, coi filtri di adesso. Falso, con l'avviso, se il mondo non li prende.
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
            self.attuali = self.filtri
            self._preparazione_attuale = self.preparazione
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
        L'elenco coi filtri che contano adesso: resta scelta la stessa persona, o il posto di ripiego, e l'etichetta
        dell'elenco e il campo Trovati si rifanno; quando l'elenco si svuota o torna pieno, il suo suono. Gli eventi
        dell'elenco di questo momento non contano: la scheda si chiede dopo.
        """
        self._ricalcolo.ferma()
        r = self.riga()
        contano = self._contano()
        self.righe = mercato.cerca(self.mondo, contano, self.memoria, self.preparazione.bersaglio)
        self._ordine_delle_righe = contano.ordine
        posto = mercato.indice_della_persona(self.righe, r.numero, r.allenatore, ripiego) if r is not None else (0 if self.righe else None)
        self._in_ricalcolo = True
        try:
            self.elenco.mostra(len(self.righe), posto, [testi.nome_completo(riga.persona).casefold() for riga in self.righe])
        finally:
            self._in_ricalcolo = False
        self.ultima_riga = self.elenco.col_fuoco() if self.righe else -1
        self._aggiorna_le_etichette(contano)
        primo = self._vuoto.pieno is None
        passaggio = self._vuoto.passaggio(bool(self.righe))
        if passaggio and not primo:
            suoni.in_coda(passaggio)
        self._scheda.chiedi()

    def _aggiorna_le_etichette(self, contano):
        """L'etichetta dell'elenco, che NVDA legge come suo nome, coi trovati; e il campo Trovati, che tiene la riga dove sta il cursore."""
        etichetta = testi.trovati(self.righe, contano)
        if self.etichetta_trovati.GetLabel() != etichetta:
            self.etichetta_trovati.SetLabel(etichetta)
            self.libro.GetPage(RISULTATI).Layout()
        testo = testi.riepilogo_dei_trovati(self.righe, self.filtri, self.preparazione, self.mondo)
        if testo != self._testo_dei_trovati:
            _vero, _colonna, riga = self.campo_trovati.PositionToXY(self.campo_trovati.GetInsertionPoint())
            self.campo_trovati.ChangeValue(testo)
            aspetto.ridai_stile(self.campo_trovati, self.impostazioni)
            righe = testo.count("\n") + 1
            self.campo_trovati.SetInsertionPoint(self.campo_trovati.XYToPosition(0, min(max(riga, 0), righe - 1)))
            self._testo_dei_trovati = testo

    def _testo_dell_annuncio(self):
        return testi.annuncio_dei_trovati(self.righe, self._contano(), self.preparazione)

    def annuncia(self, forzato=False):
        """
        I trovati alla voce e al display, al posto di quello di prima, anche con la lettura della cronaca spenta; prima,
        il ricalcolo che aspettava. Soltanto se dice qualcosa di nuovo rispetto all'ultimo annuncio, salvo forzato, per
        Invio nel Valore con un valore sbagliato, che dice subito il perché.
        """
        self._annuncio.ferma()
        self._ricalcolo.subito()
        testo = self._testo_dell_annuncio()
        if testo == self._ultimo_annuncio and not forzato:
            return
        self._ultimo_annuncio = testo
        self.annunci.svuota()
        self.annunci.annuncia([testo], {**self.impostazioni, "annunci_cronaca": True})

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
        e le righe; l'annuncio dei trovati non serve più, perché NVDA li dice nel nome, e conta come detto. Dalla
        verifica con la lente di NVDA: con una freccia sulla casella dei preset e subito Tab, Alt+T, Maiusc+Tab o
        Ctrl+Tab, NVDA leggeva l'elenco di prima, e mezzo secondo dopo l'elenco cambiava senza che lo rileggesse.
        """
        event.Skip()
        if self._in_ricalcolo:
            return
        self._ricalcolo.subito()
        # Dalla verifica del costruttore con la lente di NVDA: il conto che NVDA legge nel nome conta come detto anche
        # quando l'annuncio non aspettava più, perché Invio nei Filtri o sulla casella l'aveva già fermato; prima l'ultimo
        # annuncio restava quello vecchio, e un conto che tornava quello di prima non si annunciava.
        self._annuncio.ferma()
        self._ultimo_annuncio = self._testo_dell_annuncio()

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
        noti = (self.elenco, self.scheda, self.casella_preset, *self._controlli_dei_filtri)
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
        torna all'elenco, nella casella dei preset apre Salva filtri o porta all'elenco, nella scheda Filtri fa subito il
        ricalcolo e porta all'elenco dei Risultati, salvo nel Valore con un valore sbagliato; sui pulsanti è di Windows, e
        i pulsanti si difendono con _ripetuta. Esc nella scheda torna all'elenco. Alt+O sull'offerta oscurata, nella
        scheda Risultati, dice il perché.
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
        """Invio dopo la grazia: sulla Situazione e sulla linguetta non fa niente."""
        if controllo is self.elenco:
            self.vai_alla_scheda()
        elif controllo is self.scheda:
            self.torna_all_elenco()
        elif controllo is self.casella_preset:
            self._invio_sulla_casella()
        elif controllo is self.valore_scritto and self._stato_del_valore() == DA_CORREGGERE:
            self._valore_da_correggere()
        elif any(controllo is filtro for filtro in self._controlli_dei_filtri):
            self._ai_risultati()

    def _valore_da_correggere(self):
        """
        Invio nel Valore con un valore sbagliato: il fuoco resta lì, col suono del campo da correggere, e l'annuncio dice
        subito il perché; il suono del valore scritto che aspettava, lo stesso errore detto due volte, tace.
        """
        self._lascia_il_valore()
        suoni.suona("campo_da_correggere")
        self.annuncia(forzato=True)

    def _ai_risultati(self):
        """
        Invio nella scheda Filtri: subito il ricalcolo che aspettava, niente annuncio né suono del valore scritto, e il
        fuoco sull'elenco della scheda Risultati.
        """
        self._ricalcolo.subito()
        self._annuncio.ferma()
        self._lascia_il_valore()
        if self.libro.GetSelection() != RISULTATI:
            self.libro.SetSelection(RISULTATI)
        self.elenco.SetFocus()

    def _scheda_cambiata(self, event):
        """
        Il cambio di scheda, con Ctrl+Tab, Ctrl+Maiusc+Tab o con Invio nei filtri, che porta ai Risultati: il suono della
        scheda; lasciando i Filtri, il suono del valore scritto che aspettava tace.
        """
        event.Skip()
        pagina = event.GetSelection()
        if pagina != FILTRI:
            self._lascia_il_valore()
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
        suo titolo e il suo testo. Dalla verifica dei suoni del costruttore, lo stesso per il suono del valore scritto.
        """
        self._ricalcolo.subito()
        self._annuncio.ferma()
        self._lascia_il_valore()
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

    def _dopo_un_esito(self, persona):
        """
        Dopo un esito: la memoria dimentica la persona toccata e le righe, perché uno stato può cambiare, come il libero
        che firma e diventa tuo; poi l'elenco si ricalcola sullo stesso posto.
        """
        self.memoria.dimentica(persona)
        self.memoria.dimentica_le_righe()
        self.ricalcola(ripiego=self.riga_scelta())

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
        self.leggi(testo, suono)
        self._dopo_un_esito(r.persona)
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
        voce scelta, i filtri attuali e la regola in preparazione della voce in cima; in risultato gli esiti.
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
            preparazione = self.preparazione if self.scelta is None else self._preparazione_attuale
            # I filtri vengono dai controlli e dai preset, e fanno sempre il giro del salvataggio: se non lo facessero, la
            # porta riaprirebbe come prima; la preparazione la ripulisce dai caratteri di controllo ricorda_la_porta.
            with contextlib.suppress(ValueError):
                mercato.ricorda_la_porta(self.mondo, self.porta, mercato.StatoDellaPorta(self.scelta, self.attuali, preparazione))
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
