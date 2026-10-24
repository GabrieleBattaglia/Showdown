"""
Le prove della finestra Mercato e ricerca, gui/mercato_e_ricerca.py, issue 8 e decisione D36.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nascono il 24 ottobre 2026 col passo della finestra. La finestra si apre sul desktop nascosto del conftest, senza
suoni e senza voce, sul mondo di tests/aiuti_mercato.py; i rimandi del ricalcolo, dell'annuncio, della scheda e dei
suoni li fa partire la prova, gli annunci si annotano, e i dialoghi interni rispondono da un copione, al posto di
ShowModal. I tasti arrivano in tre modi, con strumenti/tastiera_simulata.py: messi in coda, perché passino da
IsDialogMessage come quelli veri, per l'ordine del Tab, le lettere rapide e Ctrl+Tab; mandati al controllo, per le
frecce della casella dei preset; e come li vede il gancio dei tasti di wx, fatto a mano, per Invio, Esc e Alt+O, perché
Windows chiama quel gancio soltanto per i tasti veri.
Si provano: le quattro schede e le lettere, uniche in ogni scheda e che arrivano davvero, Chiudi compreso, e quelle di
una scheda nascosta che non fanno niente; l'ordine del Tab; Ctrl+Tab coi suoni delle schede; la casella dei preset con
le frecce, la voce già applicata, Salva filtri che si apre con Invio e dall'elenco aperto ma non con le frecce, e la
casella che torna sulla voce applicata; Salva, la sostituzione, Rinomina e Gestisci, coi preset fra gli esiti e nel
mondo; le porte, con Assumi che non ricorda niente; i 350 e i 1000 millesimi; la stessa persona dopo il ricalcolo;
la scheda della persona, Invio ed Esc; la grazia di Invio, anche dopo un dialogo interno, e il doppio colpo sui
pulsanti; le mosse finite con Alt+O; le offerte, l'amichevole, la sfida e il diario coi loro suoni; le condizioni e
Azzera; la chiusura con e senza esiti; e nessun messaggio di Windows.
Coi collegamenti dello stesso giorno ci sono anche le prove del mercato degli allenatori di prima, che la finestra ha
sostituito, da Ctrl+Maiusc+G e da Assumi: i liberi dal migliore coi loro filtri, l'ingaggio accettato e rifiutato col
posto da offrire, la prelazione, la cassa vuota e le mosse finite, la scheda e il diario; e l'elenco che nasce vuoto.
Col passo dei suoni dello stesso giorno ogni evento della finestra ha il suo preset, e le prove usano il registratore di sempre.
Con le verifiche dello stesso giorno: ogni scheda è un riquadro col testo della linguetta, guardato anche coi nomi MSAA
che legge NVDA; l'elenco che prende il fuoco si rifà subito; la casella lasciata su Salva filtri dall'elenco aperto torna
sulla voce applicata; un dialogo interno fa il ricalcolo e ferma l'annuncio; la Situazione su una riga sola; la scheda
col suo rimando anche all'apertura; i suoni in fila fermati alla chiusura; l'amichevole contro l'unico tuo che gioca; i
massimi dei numeri del motore. Banco.apri fa partire i rimandi dell'apertura, salvo chi la vuole com'è.
"""

import ctypes
import datetime
import random
import re
import sys
import uuid
from pathlib import Path

import pytest
import wx
from aiuti_mercato import ORA, mondo_del_mercato

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import tastiera_simulata as tastiera

import impostazioni
import mercato
import mondo as modulo_mondo
import staff
import testi
from costanti import LIMITE_MOVIMENTI_PER_TICK, MESI_DI_INGAGGIO
from gui import dialoghi
from gui import mercato_e_ricerca as finestra_mr
from gui.mercato_e_ricerca import ALTRI_FILTRI, FILTRI, FILTRI_ALLENATORI, RISULTATI
from modelli import probabilita_accettazione


class Attesa:
    def __init__(self, secondi, funzione):
        self.secondi = secondi
        self.funzione = funzione
        self.viva = True

    def Stop(self):
        self.viva = False


class Pianifica:
    """I rimandi della finestra: si annotano, e partono quando la prova lo dice."""

    def __init__(self):
        self.attese = []

    def __call__(self, secondi, funzione):
        attesa = Attesa(secondi, funzione)
        self.attese.append(attesa)
        return attesa

    def vive(self):
        return sorted({round(a.secondi, 2) for a in self.attese if a.viva})

    def scatta(self, secondi=None):
        """
        Fa partire i rimandi vivi, tutti o quelli dei secondi dati, nell'ordine in cui sono arrivati; anche quelli che
        nascono mentre gli altri partono, come la scheda che segue la riga dopo un ricalcolo, fino a dieci giri.
        """
        for _giro in range(10):
            vive = [a for a in self.attese if a.viva and (secondi is None or round(a.secondi, 2) == secondi)]
            if not vive:
                break
            for attesa in vive:
                if attesa.viva:
                    attesa.viva = False
                    attesa.funzione()
            tastiera.pompa()


class Annunci:
    """Gli annunci dei trovati, annotati: le righe e se la lettura della cronaca era accesa."""

    def __init__(self):
        self.detti = []
        self.svuotati = 0

    def annuncia(self, righe, impostazioni):
        self.detti.append((list(righe), impostazioni["annunci_cronaca"]))

    def svuota(self):
        self.svuotati += 1


class Dialoghi:
    """
    Al posto di ShowModal dei dialoghi interni: annota ogni dialogo che si apre, e i testi letti e le domande, e
    risponde col copione, una funzione per dialogo, che riceve il dialogo e restituisce il codice. Senza copione,
    risponde come chi accetta: Chiudi agli avvisi, Sì alle domande, la conferma con quello che il dialogo propone.
    """

    def __init__(self):
        self.aperti = []
        self.letti = []
        self.domande = []
        self.copione = []

    def __call__(self, chi, dialogo):
        # Come nel ciclo di ShowModal: gli eventi in attesa del dialogo, come il fuoco nel suo testo, arrivano mentre è aperto.
        tastiera.pompa()
        nome = type(dialogo).__name__
        self.aperti.append(nome)
        if isinstance(dialogo, finestra_mr.Avviso):
            self.letti.append(dialogo.testo.GetValue())
        elif isinstance(dialogo, finestra_mr.Domanda):
            self.domande.append(dialogo.testo.GetValue())
        try:
            if self.copione:
                return self.copione.pop(0)(dialogo)
            if isinstance(dialogo, finestra_mr.Avviso):
                return wx.ID_CLOSE
            if isinstance(dialogo, finestra_mr.Domanda):
                return wx.ID_YES
            if hasattr(dialogo, "conferma"):
                dialogo.SetReturnCode(wx.ID_CANCEL)
                dialogo.conferma()
                return dialogo.GetReturnCode()
            return wx.ID_CLOSE
        finally:
            chi._dopo_un_dialogo()


class Messaggi(list):
    """I messaggi di Windows: la finestra non ne deve aprire nessuno."""

    def __call__(self, testo, *args, **kwargs):
        self.append(testo)
        return wx.OK


@pytest.fixture
def mondo():
    return mondo_del_mercato()


@pytest.fixture
def messaggi(monkeypatch):
    finti = Messaggi()
    monkeypatch.setattr(wx, "MessageBox", finti)
    return finti


@pytest.fixture
def dialoghi_finti(monkeypatch):
    finti = Dialoghi()
    monkeypatch.setattr(finestra_mr._ConTestiDaLeggere, "_modale", lambda chi, dialogo: finti(chi, dialogo))
    return finti


class Banco:
    """Il banco di una prova: il mondo, i rimandi, gli annunci, i dialoghi finti, i suoni e le finestre aperte."""

    def __init__(self, mondo, pianifica, annunci, dialoghi_finti, suonati, messaggi):
        self.mondo = mondo
        self.pianifica = pianifica
        self.annunci = annunci
        self.dialoghi = dialoghi_finti
        self.suonati = suonati
        self.messaggi = messaggi
        self.aperte = []

    def apri(self, porta="mercato", posto=None, grazia=False, impostazioni_date=None, rimandi=True):
        """
        Una finestra, mostrata; senza grazia, come se fosse aperta da un po', così il primo Invio conta. Con rimandi,
        partono quelli dell'apertura, come la scheda della persona, che dalle verifiche si scrive col suo rimando.
        """
        f = finestra_mr.MercatoERicerca(None, self.mondo, impostazioni_date or impostazioni.valide(None), porta, posto=posto, pianifica=self.pianifica,
                                        annunci=self.annunci)
        self.aperte.append(f)
        f.Show()
        tastiera.pompa()
        if rimandi:
            self.pianifica.scatta()
        if not grazia:
            f.ultimo_invio = float("-inf")
        return f


@pytest.fixture
def banco(app_wx, mondo, dialoghi_finti, suonati, messaggi):
    b = Banco(mondo, Pianifica(), Annunci(), dialoghi_finti, suonati, messaggi)
    yield b
    for f in reversed(b.aperte):
        f.Destroy()
        # wx distrugge le finestre di primo livello quando il ciclo è libero: qui, una alla volta, e non nelle prove dopo.
        ciclo = wx.GUIEventLoop()
        wx.CallLater(30, ciclo.Exit)
        ciclo.Run()
    # Nessun messaggio di Windows: domande, esiti e avvisi si leggono nei campi dove si scorre col cursore.
    assert b.messaggi == []


def _pausa(chi):
    """Come dopo una pausa: la pressione ripetuta dei pulsanti, la fine dell'ultimo dialogo interno e la grazia di Invio non contano più."""
    chi.__dict__.setdefault("_pressioni", {}).clear()
    chi._fine_di_un_dialogo = float("-inf")
    chi.ultimo_invio = float("-inf")


def _invio(f, controllo=None, fuori_dalla_grazia=True):
    """Invio come lo vede il gancio dei tasti, sul controllo dato o su quello col fuoco; fuori dalla grazia, come dopo una pausa."""
    if fuori_dalla_grazia:
        f.ultimo_invio = float("-inf")
    return tastiera.gancio(controllo or wx.Window.FindFocus(), tastiera.VK_RETURN)


def _clic(controllo):
    tipo = wx.wxEVT_BUTTON if isinstance(controllo, wx.Button) else wx.wxEVT_CHECKBOX if isinstance(controllo, wx.CheckBox) else wx.wxEVT_CHOICE
    evento = wx.CommandEvent(tipo, controllo.GetId())
    evento.SetEventObject(controllo)
    if isinstance(controllo, wx.CheckBox):
        evento.SetInt(int(controllo.GetValue()))
    elif isinstance(controllo, wx.Choice):
        evento.SetInt(controllo.GetSelection())
    controllo.GetEventHandler().ProcessEvent(evento)
    tastiera.pompa()


def _spunta(f, campo, valore=True):
    casella = f.caselle[campo]
    casella.SetValue(valore)
    _clic(casella)


def _scegli_voce(scelta, posto):
    scelta.SetSelection(posto)
    _clic(scelta)


def _scrivi_numero(numero, valore):
    numero.SetValue(valore)
    evento = wx.CommandEvent(wx.wxEVT_TEXT, numero.GetId())
    evento.SetEventObject(numero)
    numero.GetEventHandler().ProcessEvent(evento)
    tastiera.pompa()


def _scegli_persona(f, numero, allenatore=False):
    """La persona scelta nell'elenco, col fuoco, sulla scheda Risultati: ci si va senza il suo suono, come fa la prova."""
    indice = next(i for i, r in enumerate(f.righe) if r.numero == numero and r.allenatore == allenatore)
    if f.libro.GetSelection() != RISULTATI:
        f.libro.ChangeSelection(RISULTATI)
    f.elenco.SetFocus()
    f.elenco.scegli(indice)
    tastiera.pompa()
    return f.righe[indice]


def _focalizzabili(genitore):
    """I controlli che prendono il fuoco dalla tastiera, nell'ordine in cui nascono, dentro i riquadri compresi."""
    trovati = []
    for figlio in genitore.GetChildren():
        if isinstance(figlio, wx.StaticBox):
            trovati.extend(_focalizzabili(figlio))
        elif not isinstance(figlio, wx.StaticText) and figlio.AcceptsFocusFromKeyboard():
            trovati.append(figlio)
    return trovati


def _lettera(etichetta):
    trovata = re.search(r"&(.)", etichetta)
    return trovata.group(1).lower() if trovata else None


def _lettere_della_pagina(pagina):
    """Per ogni controllo della pagina la sua lettera: dall'etichetta per caselle e pulsanti, dal testo che lo precede per gli altri."""
    lettere = []
    for controllo in _focalizzabili(pagina):
        if isinstance(controllo, (wx.Button, wx.CheckBox)):
            lettere.append((controllo, _lettera(controllo.GetLabel())))
            continue
        fratelli = list(controllo.GetParent().GetChildren())
        prima = fratelli[fratelli.index(controllo) - 1]
        lettere.append((controllo, _lettera(prima.GetLabel()) if isinstance(prima, wx.StaticText) else None))
    return lettere


def _pagina_di(f, controllo):
    """Il posto della scheda in cui sta il controllo, a qualunque profondità di riquadri."""
    genitore = controllo.GetParent()
    while genitore is not None and f.libro.FindPage(genitore) == wx.NOT_FOUND:
        genitore = genitore.GetParent()
    return f.libro.FindPage(genitore)


def _fuoco_su(controllo):
    """Vero se il fuoco è sul controllo o dentro di lui, come il campo di uno SpinCtrl; se wx non lo sa, lo dice Windows."""
    fuoco = wx.Window.FindFocus()
    while fuoco is not None:
        if fuoco is controllo or fuoco.GetId() == controllo.GetId():
            return True
        fuoco = fuoco.GetParent()
    maniglia = tastiera.user32.GetFocus()
    return bool(maniglia) and (maniglia == controllo.GetHandle() or bool(ctypes.windll.user32.IsChild(controllo.GetHandle(), maniglia)))


# La forma della finestra e le lettere.

def test_si_apre_massimizzata_col_titolo_e_le_quattro_schede(banco):
    f = banco.apri()
    assert f.IsMaximized() and f.GetTitle() == "Mercato e ricerca di Pat-Bologna"
    assert [f.libro.GetPageText(i) for i in range(f.libro.GetPageCount())] == ["Risultati", "Filtri", "Altri filtri", "Filtri degli allenatori"]
    assert f.libro.GetSelection() == RISULTATI and _fuoco_su(f.elenco)
    assert f.GetEscapeId() == f.pulsante_chiudi.GetId()
    # Il suono della porta, e nient'altro: ci sono mosse, e l'elenco non è vuoto.
    assert banco.suonati == ["dialogo_mercato"]
    assert f.casella_preset.GetStringSelection() == mercato.nome_del_preset_di_serie("mercato")
    assert f.etichetta_trovati.GetLabel() == "&" + testi.etichetta_trovati(len(f.righe))
    assert f.situazione.GetValue() == testi.situazione(banco.mondo)


def test_le_lettere_sono_uniche_in_ogni_scheda_e_ogni_controllo_ne_ha_una(banco):
    f = banco.apri()
    for posto in range(f.libro.GetPageCount()):
        lettere = _lettere_della_pagina(f.libro.GetPage(posto))
        senza = [type(c).__name__ for c, lettera in lettere if lettera is None]
        assert not senza, f"scheda {posto}: controlli senza lettera {senza}"
        tutte = [lettera for _c, lettera in lettere] + ["c"]
        assert len(tutte) == len(set(tutte)), f"scheda {posto}: lettere doppie in {tutte}"
    # I controlli che contano, uno per uno, con la loro lettera.
    attese = {RISULTATI: "spthombdg", FILTRI: "nalvutregpmizdofs", ALTRI_FILTRI: "rvmp123456789nlsaetugdizoq", FILTRI_ALLENATORI: "tvpse"}
    for posto, lettere in attese.items():
        assert "".join(lettera for _c, lettera in _lettere_della_pagina(f.libro.GetPage(posto))) == lettere


def test_le_lettere_arrivano_davvero_soltanto_nella_scheda_visibile(banco):
    f = banco.apri()
    premuti = []
    for pulsante in [c for posto in range(4) for c in _focalizzabili(f.libro.GetPage(posto)) if isinstance(c, wx.Button)] + [f.pulsante_chiudi]:
        # Un gestore in cima, che annota e non lascia andare: le azioni vere non partono.
        pulsante.Bind(wx.EVT_BUTTON, lambda event, p=pulsante: premuti.append(p.GetLabel()))
    for posto in range(4):
        f.libro.SetSelection(posto)
        tastiera.pompa()
        controlli = _lettere_della_pagina(f.libro.GetPage(posto))
        for controllo, lettera in controlli:
            # Si parte da un altro controllo della stessa pagina.
            partenza = next(c for c, _l in controlli if c is not controllo and not isinstance(c, wx.Button))
            partenza.SetFocus()
            tastiera.pompa()
            premuti.clear()
            tastiera.posta_alt(lettera)
            if isinstance(controllo, wx.Button):
                assert premuti == [controllo.GetLabel()], (posto, lettera)
            else:
                assert _fuoco_su(controllo), (posto, lettera, type(wx.Window.FindFocus()).__name__)
        # Chiudi, fuori dalle schede, ha la C in tutte.
        premuti.clear()
        controlli[0][0].SetFocus()
        tastiera.pompa()
        tastiera.posta_alt("c")
        assert premuti == ["&Chiudi"]
    # Una lettera che c'è soltanto in una scheda nascosta non fa niente: la Q di Azzera questi filtri, dalla scheda Risultati.
    f.libro.SetSelection(RISULTATI)
    f.elenco.SetFocus()
    tastiera.pompa()
    premuti.clear()
    tastiera.posta_alt("q")
    assert premuti == [] and _fuoco_su(f.elenco) and f.libro.GetSelection() == RISULTATI


def test_l_ordine_del_tab_segue_quello_dei_controlli(banco):
    f = banco.apri()
    attesi = {
        RISULTATI: [f.situazione, f.casella_preset, f.elenco, f.scheda, f.pulsante_offerta, f.pulsante_amichevole, f.pulsante_sfida, f.pulsante_diario,
                    f.pulsante_gestisci, f.pulsante_chiudi],
        FILTRI: [f.campo_nome, f.caselle["allenatori"], *(f.caselle[c] for c in ("liberi", "in_vendita", "del_computer", "tuoi", "ritirati")),
                 f.scelte["sesso"][0], f.scelte["classe_migliore"][0], f.scelte["classe_peggiore"][0], f.numeri["eta_massima"], f.numeri["eta_minima"],
                 f.numeri["costo_massimo"], f.caselle["disponibili_oggi"], f.scelta_ordine, f.filtri_attivi, f.pulsante_salva, f.pulsante_chiudi],
        FILTRI_ALLENATORI: [f.scelte["tipo_allenatore"][0], f.scelte["visus"][0], f.scelte["posto_attuale"][0], f.numeri["stipendio_capo_massimo"],
                            f.caselle["senza_prelazione_altrui"], f.pulsante_chiudi],
    }
    attesi[ALTRI_FILTRI] = [*(c for c, _l in _lettere_della_pagina(f.libro.GetPage(ALTRI_FILTRI))), f.pulsante_chiudi]
    for posto, controlli in attesi.items():
        f.libro.SetSelection(posto)
        tastiera.pompa()
        controlli[0].SetFocus()
        tastiera.pompa()
        for controllo in controlli[1:]:
            tastiera.posta_tasto(tastiera.VK_TAB)
            assert _fuoco_su(controllo), (posto, controlli.index(controllo))
        # Dopo Chiudi, la linguetta; e Maiusc+Tab torna indietro.
        tastiera.posta_tasto(tastiera.VK_TAB)
        assert _fuoco_su(f.libro)
        tastiera.posta_tasto(tastiera.VK_TAB, shift=True)
        assert _fuoco_su(f.pulsante_chiudi)


def test_ctrl_tab_cambia_scheda_da_ogni_controllo_col_suo_suono(banco):
    f = banco.apri()
    banco.suonati.clear()
    for controllo in (f.elenco, f.scheda, f.casella_preset, f.situazione):
        f.libro.SetSelection(RISULTATI)
        controllo.SetFocus()
        tastiera.pompa()
        banco.suonati.clear()
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True)
        assert f.libro.GetSelection() == FILTRI and banco.suonati == ["scheda_filtri"]
        assert f.libro.GetPage(FILTRI).IsDescendant(wx.Window.FindFocus())
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True)
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True)
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True)
        assert f.libro.GetSelection() == RISULTATI
        assert banco.suonati == ["scheda_filtri", "scheda_altri_filtri", "scheda_filtri_allenatori", "scheda_risultati"]
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True, shift=True)
        assert f.libro.GetSelection() == FILTRI_ALLENATORI and banco.suonati[-1] == "scheda_filtri_allenatori"


# La casella dei preset.

def test_le_frecce_sulla_casella_applicano_ogni_preset_intero(banco):
    f = banco.apri()
    casella = f.casella_preset
    casella.SetFocus()
    tastiera.pompa()
    banco.suonati.clear()
    # Dal preset del mercato, il secondo di serie, una freccia giù porta a Tutti in attività.
    posto = casella.GetSelection()
    tastiera.premi(casella, tastiera.VK_DOWN)
    assert casella.GetSelection() == posto + 1
    voce = f.voci[posto + 1]
    assert f.scelta == voce.scelta and f.filtri == mercato.filtri_di_serie(voce.scelta)
    assert banco.suonati == ["mercato_scelta_cambiata"] and f.caselle["tuoi"].GetValue()
    # Il ricalcolo e l'annuncio aspettano l'ultimo tasto: 350 e 1000 millesimi.
    assert banco.pianifica.vive() == [0.35, 1.0]
    prima = len(f.righe)
    banco.pianifica.scatta(0.35)
    assert len(f.righe) > prima and f.etichetta_trovati.GetLabel() == "&" + testi.etichetta_trovati(len(f.righe))
    banco.pianifica.scatta(1.0)
    assert banco.annunci.detti[-1] == ([testi.etichetta_trovati(len(f.righe))], True)
    # Su, alla voce in cima: i filtri attuali, quelli di serie della porta finché non si cambia niente a mano.
    tastiera.premi(casella, tastiera.VK_UP)
    tastiera.premi(casella, tastiera.VK_UP)
    assert casella.GetSelection() == 0 and f.scelta is None and banco.suonati[-1] == "filtri_attuali_ripresi"
    assert f.filtri == f.attuali
    # Con Fine si arriva a Salva filtri...: le frecce non lo aprono, e niente suona.
    banco.suonati.clear()
    tastiera.premi(casella, tastiera.VK_END)
    assert f._voce_della_casella().tipo == mercato.VOCE_SALVA
    assert banco.dialoghi.aperti == [] and banco.suonati == [] and f.scelta is None
    # Il fuoco che lascia la casella la riporta in silenzio sulla voce applicata.
    f.elenco.SetFocus()
    tastiera.pompa()
    assert casella.GetSelection() == 0 and banco.suonati == []


def test_la_voce_gia_applicata_non_fa_niente(banco):
    f = banco.apri()
    banco.suonati.clear()
    _clic(f.casella_preset)
    assert banco.suonati == [] and banco.pianifica.vive() == []


def test_salva_filtri_si_apre_con_invio_e_dall_elenco_aperto(banco):
    f = banco.apri()
    casella = f.casella_preset
    casella.SetFocus()
    casella.SetSelection(casella.GetCount() - 1)
    tastiera.pompa()
    banco.dialoghi.copione.append(lambda d: wx.ID_CANCEL)
    _invio(f, casella)
    assert banco.dialoghi.aperti == ["SalvaFiltri"] and banco.suonati[-2:] == ["dialogo_salva_filtri", "annullato"]
    # Annullato: la casella torna sulla voce applicata.
    assert casella.GetSelection() == f._posto_applicato == mercato.posto_della_scelta(f.voci, "mercato")
    # Dall'elenco aperto, Fine e Invio, come dalla tastiera: Windows chiude l'elenco, e la scelta apre Salva filtri.
    banco.dialoghi.copione.append(lambda d: wx.ID_CANCEL)
    _pausa(f)
    casella.SetFocus()
    tastiera.pompa()
    tastiera.user32.SendMessageW(casella.GetHandle(), 0x014F, 1, 0)
    tastiera.pompa()
    tastiera.posta_tasto(tastiera.VK_END, controllo=casella)
    tastiera.posta_tasto(tastiera.VK_RETURN, controllo=casella)
    assert banco.dialoghi.aperti == ["SalvaFiltri", "SalvaFiltri"]


def test_salva_filtri_salva_sostituisce_e_propone_il_nome(banco):
    f = banco.apri()
    _spunta(f, "ritirati")
    assert f.scelta is None and f.casella_preset.GetSelection() == 0

    def scrivi(nome):
        def risposta(dialogo):
            assert dialogo.GetTitle() == "Salva filtri"
            dialogo.nome.SetValue(nome)
            dialogo.conferma()
            return dialogo.GetReturnCode()
        return risposta

    # Il nome proposto è vuoto: i filtri vengono da un preset di serie.
    proposte = []
    banco.dialoghi.copione.append(lambda d: (proposte.append(d.nome.GetValue()), scrivi("  Giovani mancini ")(d))[1])
    banco.suonati.clear()
    f.salva_filtri()
    assert proposte == [""]
    preset = banco.mondo.filtri_di_ricerca.preset
    assert [(p.numero, p.nome) for p in preset] == [(1, "Giovani mancini")] and preset[0].filtri == f.filtri
    assert banco.suonati == ["dialogo_salva_filtri", "preset_salvato"] and f.esiti.preset == ["Preset salvato: Giovani mancini."]
    assert f.scelta == 1 and f.casella_preset.GetStringSelection() == "Giovani mancini"
    # Un ritocco a mano: la casella torna in cima, e Salva propone il nome del preset da cui vengono i filtri.
    _spunta(f, "liberi", False)
    assert f.scelta is None and f._nome_proposto() == "Giovani mancini"
    # Lo stesso nome, con le maiuscole diverse: la domanda col No; al No il dialogo resta aperto, poi col Sì sostituisce.
    banco.dialoghi.copione.extend([scrivi("GIOVANI MANCINI"), lambda d: wx.ID_CANCEL])
    _pausa(f)
    f.salva_filtri()
    assert banco.dialoghi.domande == ["Esiste già il preset Giovani mancini: sostituirne i filtri con questi?"]
    assert banco.mondo.filtri_di_ricerca.preset[0].filtri != f.filtri
    banco.dialoghi.copione.append(scrivi("giovani mancini"))
    banco.suonati.clear()
    _pausa(f)
    f.salva_filtri()
    assert banco.mondo.filtri_di_ricerca.preset[0].filtri == f.filtri and banco.mondo.filtri_di_ricerca.preset[0].nome == "Giovani mancini"
    assert banco.suonati == ["dialogo_salva_filtri", "domanda", "preset_sostituito"]
    assert f.esiti.preset[-1] == "Preset Giovani mancini: filtri sostituiti con quelli attuali."
    # Un nome di serie non va, e lo dice col suono del campo da correggere: il dialogo resta aperto, e qui si annulla.
    banco.dialoghi.copione.append(scrivi("Salva filtri..."))
    _pausa(f)
    f.salva_filtri()
    assert "è il nome di una voce di serie" in banco.dialoghi.letti[-1] and "campo_da_correggere" in banco.suonati


def test_gestisci_rinomina_sposta_ed_elimina(banco):
    f = banco.apri()
    fdr = mercato.filtri_di_ricerca_di_serie()
    for nome in ("Primo", "Secondo"):
        mercato.salva_preset(fdr, nome, mercato.filtri_di_serie("piu_forti"))
    mercato.ricorda_i_preset(banco.mondo, fdr)
    f.filtri_di_ricerca = mercato.filtri_di_ricerca_del_mondo(banco.mondo)
    f._rifai_la_casella()
    # Il secondo preset applicato dalla casella.
    _scegli_voce(f.casella_preset, mercato.posto_della_scelta(f.voci, 2))
    assert f.scelta == 2

    def gestisci(azioni):
        def risposta(dialogo):
            for azione in azioni:
                azione(dialogo)
            return wx.ID_CLOSE
        return risposta

    def sposta(posto, verso):
        def azione(d):
            d.elenco.SetSelection(posto)
            d.sposta(verso)
            _pausa(d)
        return azione

    def rinomina(d):
        d.elenco.SetSelection(0)
        banco.dialoghi.copione.insert(0, lambda r: (r.nome.SetValue("Il migliore"), r.conferma(), r.GetReturnCode())[2])
        d.rinomina()
        _pausa(d)

    banco.suonati.clear()
    # Secondo su, giù e di nuovo su; poi su e giù ai bordi, che non si spostano; poi il nome nuovo.
    banco.dialoghi.copione.append(gestisci([sposta(1, -1), sposta(0, 1), sposta(1, -1), sposta(0, -1), sposta(1, 1), rinomina]))
    f.gestisci_preset()
    preset = banco.mondo.filtri_di_ricerca.preset
    assert [(p.numero, p.nome) for p in preset] == [(2, "Il migliore"), (1, "Primo")]
    assert banco.suonati == ["dialogo_gestisci_preset", "preset_spostato_su", "preset_spostato_giu", "preset_spostato_su", "preset_non_si_sposta",
                             "preset_non_si_sposta", "dialogo_rinomina_preset", "preset_rinominato"]
    # Gli spostamenti di seguito dello stesso preset sono una riga sola fra gli esiti.
    assert f.esiti.preset == ["Preset Secondo spostato al posto 1 di 2 fra i tuoi.", "Preset Secondo rinominato Il migliore."]
    assert f.casella_preset.GetStringSelection() == "Il migliore" and _fuoco_su(f.pulsante_gestisci)

    def elimina(d):
        d.elenco.SetSelection(0)
        d.elimina()

    banco.dialoghi.copione.append(gestisci([elimina]))
    _pausa(f)
    f.gestisci_preset()
    assert banco.dialoghi.domande[-1] == "Eliminare il preset Il migliore? Le porte che lo riaprivano torneranno al loro preset di serie."
    assert [p.nome for p in banco.mondo.filtri_di_ricerca.preset] == ["Primo"] and banco.suonati[-1] == "preset_eliminato"
    # Era applicato: i filtri restano, e diventano quelli attuali, in cima alla casella.
    assert f.scelta is None and f.casella_preset.GetSelection() == 0 and f.filtri == mercato.filtri_di_serie("piu_forti")
    # Senza preset, l'elenco lo dice, e i pulsanti suonano il tasto a vuoto.
    banco.dialoghi.copione.append(gestisci([elimina]))
    _pausa(f)
    f.gestisci_preset()
    vuota = []
    banco.dialoghi.copione.append(gestisci([lambda d: (vuota.append(d.elenco.GetString(0)), d.rinomina(), d.sposta(1))]))
    banco.suonati.clear()
    _pausa(f)
    f.gestisci_preset()
    assert vuota == [testi.NESSUN_PRESET] and banco.suonati == ["dialogo_gestisci_preset", "nessuna_selezione", "nessuna_selezione"]


# Le porte.

def test_ogni_porta_riapre_col_suo_ultimo_preset_e_assumi_non_ricorda_niente(banco):
    f = banco.apri("ricerca")
    assert f.libro.GetSelection() == FILTRI and _fuoco_su(f.campo_nome)
    assert f.casella_preset.GetStringSelection() == mercato.nome_del_preset_di_serie("tutti_in_attivita")
    f.campo_nome.SetValue("ros")
    f.chiudi_la_finestra()
    assert f.GetReturnCode() == wx.ID_CLOSE and f.risultato.vuoti
    stato = mercato.stato_della_porta(banco.mondo, "ricerca")
    assert stato.scelta is None and stato.attuali.nome == "ros"
    g = banco.apri("ricerca")
    assert g.campo_nome.GetValue() == "ros" and g.casella_preset.GetSelection() == 0 and g.filtri == stato.attuali
    # Le altre porte non cambiano; Assumi apre sugli allenatori liberi, e alla chiusura non ricorda niente.
    a = banco.apri(None, posto=2)
    assert a.filtri == mercato.filtri_di_serie("allenatori_liberi") and a.scelta == "allenatori_liberi"
    assert banco.suonati[-1] == "dialogo_mercato_allenatori"
    _spunta(a, "tuoi")
    prima = mercato.filtri_di_ricerca_del_mondo(banco.mondo)
    a.chiudi_la_finestra()
    assert mercato.filtri_di_ricerca_del_mondo(banco.mondo) == prima


# Il ricalcolo, l'annuncio e la scheda.

def test_il_ricalcolo_aspetta_350_millesimi_e_l_annuncio_1000(banco):
    spente = impostazioni.valide({"annunci_cronaca": False})
    f = banco.apri("ricerca", impostazioni_date=spente)
    banco.pianifica.scatta()
    prima = list(f.righe)
    persona = f.righe[3].persona
    f.campo_nome.SetValue(persona.cognome[:3])
    assert f.righe == prima and banco.pianifica.vive() == [0.35, 1.0]
    # Un altro tasto sposta tutte e due le attese.
    f.campo_nome.SetValue(persona.cognome[:4])
    assert len([a for a in banco.pianifica.attese if a.viva]) == 2
    banco.pianifica.scatta(0.35)
    assert all(persona.cognome[:4].casefold() in testi.nome_completo(r.persona).casefold() for r in f.righe)
    assert "Nome, cognome o numero: " + persona.cognome[:4] in f.filtri_attivi.GetValue()
    assert banco.annunci.detti == []
    banco.pianifica.scatta(1.0)
    # Il numero dei trovati arriva anche con la lettura della cronaca spenta.
    assert banco.annunci.detti == [([testi.etichetta_trovati(len(f.righe))], True)] and banco.annunci.svuotati >= 1
    # Una casella ricalcola subito, e annuncia dopo: resta in attesa la scheda, che segue la riga.
    banco.suonati.clear()
    banco.pianifica.scatta()
    _spunta(f, "liberi", False)
    assert banco.suonati == ["casella_liberi_tolta"] and banco.pianifica.vive() == [0.35, 1.0]
    assert f._scheda.in_attesa and f._annuncio.in_attesa and not f._ricalcolo.in_attesa
    assert all(r.stato != mercato.LIBERO for r in f.righe)


def test_la_stessa_persona_resta_scelta_e_gli_eventi_del_ricalcolo_non_contano(banco):
    f = banco.apri("ricerca")
    banco.pianifica.scatta()
    r = _scegli_persona(f, 12)
    banco.pianifica.scatta()
    assert f.ultima_riga == f.righe.index(r) and f.etichetta_scheda.GetLabel() == f"Sc&heda di {testi.nome_completo(r.persona)}"
    # La freccia manda la deselezione con -1: non conta, e la scheda segue la riga nuova dopo 350 millesimi.
    tastiera.premi(f.elenco, tastiera.VK_DOWN)
    assert f.ultima_riga == f.righe.index(r) + 1 and banco.pianifica.vive() == [0.35]
    banco.pianifica.scatta()
    assert f.scheda.GetValue() == testi.scheda_giocatore(f.righe[f.ultima_riga].persona, banco.mondo)
    # Ctrl+Spazio toglie la selezione: le azioni lavorano ancora sulla riga col fuoco.
    tastiera.premi(f.elenco, tastiera.VK_SPACE, ctrl=True)
    assert f.elenco.GetFirstSelected() == -1 and f.riga_scelta() == f.ultima_riga
    # Dopo un filtro resta la stessa persona; se non c'è più, la prima riga.
    _scegli_persona(f, 12)
    _spunta(f, "liberi", False)
    assert f.riga().persona.id == 12 and f.righe.index(f.riga()) != 0
    f.campo_nome.SetValue("zzzzzz")
    banco.pianifica.scatta()
    assert f.righe == [] and f.riga() is None and f.etichetta_scheda.GetLabel() == "Sc&heda"
    assert f.scheda.GetValue() == testi.ELENCO_VUOTO_SENZA_SCHEDA and "elenco_svuotato" in banco.suonati
    f.campo_nome.SetValue("")
    banco.pianifica.scatta()
    assert f.riga_scelta() == 0 and banco.suonati[-1] == "elenco_ripopolato"


def test_invio_sull_elenco_porta_alla_scheda_e_invio_o_esc_tornano(banco):
    f = banco.apri("ricerca")
    r = _scegli_persona(f, 12)
    banco.suonati.clear()
    assert _invio(f, f.elenco)
    assert _fuoco_su(f.scheda) and f.scheda.GetInsertionPoint() == 0 and banco.suonati == ["mercato_scheda_giocatore"]
    assert f.scheda.GetValue() == testi.scheda_giocatore(r.persona, banco.mondo)
    assert _invio(f, f.scheda)
    assert _fuoco_su(f.elenco) and f.riga() is r and banco.suonati[-1] == "ritorno_all_elenco"
    _invio(f, f.elenco)
    assert tastiera.gancio(f.scheda, tastiera.VK_ESCAPE)
    assert _fuoco_su(f.elenco) and f.riga() is r and f.GetReturnCode() == 0 and banco.suonati[-1] == "ritorno_all_elenco"
    # Gli allenatori hanno la loro scheda e il loro suono.
    _spunta(f, "allenatori")
    _spunta(f, "liberi")
    f.elenco.SetFocus()
    _invio(f, f.elenco)
    assert f.scheda.GetValue() == testi.scheda_allenatore(f.riga().persona, banco.mondo) and banco.suonati[-1] == "scheda_allenatore"
    # Con l'elenco vuoto Invio suona il tasto a vuoto.
    f.campo_nome.SetValue("zzzzzz")
    banco.pianifica.scatta()
    f.elenco.SetFocus()
    _invio(f, f.elenco)
    assert banco.suonati[-1] == "nessuna_selezione"


def test_invio_in_un_filtro_porta_all_elenco_dei_risultati(banco):
    f = banco.apri("ricerca")
    f.campo_nome.SetValue("ro")
    assert banco.pianifica.vive() == [0.35, 1.0]
    banco.suonati.clear()
    _invio(f, f.campo_nome)
    # Il ricalcolo subito, niente annuncio, e la scheda Risultati col suo suono.
    assert banco.pianifica.vive() == [0.35] and f.libro.GetSelection() == RISULTATI and _fuoco_su(f.elenco)
    assert banco.suonati == ["scheda_risultati"] and all("ro" in testi.nome_completo(r.persona).casefold() for r in f.righe)
    # Anche dalle caselle, dalle scelte e da Filtri attivi; sull'elenco delle condizioni no.
    for controllo in (f.caselle["liberi"], f.scelte["indole"][0], f.filtri_attivi):
        f.libro.SetSelection(_pagina_di(f, controllo))
        controllo.SetFocus()
        _invio(f, controllo)
        assert f.libro.GetSelection() == RISULTATI and _fuoco_su(f.elenco)
    f.libro.SetSelection(ALTRI_FILTRI)
    f.elenco_condizioni.SetFocus()
    _invio(f, f.elenco_condizioni)
    assert f.libro.GetSelection() == ALTRI_FILTRI


def test_la_grazia_di_invio_dall_apertura_dall_invio_di_prima_e_dai_dialoghi_interni(banco):
    f = banco.apri("mercato", grazia=True)
    banco.suonati.clear()
    # L'apertura conta come un Invio: quello della voce di menu, rimandato da NVDA, si mangia.
    assert tastiera.gancio(f.elenco, tastiera.VK_RETURN)
    assert not _fuoco_su(f.scheda) and banco.suonati == []
    # Un Invio che arriva subito dopo un altro si mangia, una prova sola per tasto.
    _invio(f, f.elenco)
    assert _fuoco_su(f.scheda)
    assert tastiera.gancio(f.scheda, tastiera.VK_RETURN)
    assert _fuoco_su(f.scheda)
    # Dopo un dialogo interno l'Invio rimandato non apre la scheda, e il pulsante che l'ha aperto, dove torna il fuoco, non lo
    # riapre per mezzo secondo: da un pulsante il gancio dei tasti non arriva alla finestra, e lo difende la pressione ripetuta.
    _pausa(f)
    f.gestisci_preset()
    assert banco.dialoghi.aperti == ["GestisciPreset"] and _fuoco_su(f.pulsante_gestisci)
    _clic(f.pulsante_gestisci)
    assert banco.dialoghi.aperti == ["GestisciPreset"]
    f.elenco.SetFocus()
    _pausa(f)
    f.diario()
    assert banco.dialoghi.aperti[-1] == "Lettura"
    assert tastiera.gancio(f.elenco, tastiera.VK_RETURN)
    assert not _fuoco_su(f.scheda)


def test_un_pulsante_premuto_due_volte_di_seguito_conta_una(banco, monkeypatch):
    f = banco.apri("ricerca")
    orologio = [10.0]
    monkeypatch.setattr(dialoghi.time, "monotonic", lambda: orologio[0])
    _scegli_persona(f, f.righe[0].numero)
    _clic(f.pulsante_diario)
    _clic(f.pulsante_diario)
    assert banco.dialoghi.aperti == ["Lettura"]
    orologio[0] += dialoghi.RIPETIZIONE_IGNORATA
    _clic(f.pulsante_diario)
    assert banco.dialoghi.aperti == ["Lettura", "Lettura"]


# Le mosse finite e la polisportiva che manca.

def test_a_mosse_finite_si_oscura_soltanto_l_offerta_e_alt_o_dice_il_perche(banco):
    attiva = banco.mondo.miapolisportiva_attiva
    attiva.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    f = banco.apri("ricerca")
    assert banco.suonati == ["dialogo_ricerca", "mosse_finite"]
    assert not f.pulsante_offerta.IsEnabled()
    assert all(p.IsEnabled() for p in (f.pulsante_amichevole, f.pulsante_sfida, f.pulsante_diario, f.pulsante_gestisci, f.pulsante_salva))
    # Nella scheda Risultati Alt+O dice il perché col suo suono; nella scheda Filtri Alt+O è la lettera di Ordina per.
    f.libro.SetSelection(RISULTATI)
    f.elenco.SetFocus()
    assert tastiera.gancio(f.elenco, "o", alt=True)
    assert banco.dialoghi.letti == [f"Per oggi {attiva.nome} ha finito le mosse di mercato."] and banco.suonati[-1] == "mosse_finite"
    f.libro.SetSelection(FILTRI)
    f.campo_nome.SetFocus()
    assert not tastiera.gancio(f.campo_nome, "o", alt=True)
    # Con le mosse il pulsante torna, e Alt+O passa a Windows.
    attiva.movimenti_oggi = 0
    f._aggiorna_l_offerta()
    f.libro.SetSelection(RISULTATI)
    assert f.pulsante_offerta.IsEnabled() and not tastiera.gancio(f.elenco, "o", alt=True)


def test_senza_polisportiva_attiva_si_cerca_soltanto(banco):
    banco.mondo.miapolisportiva_attiva = None
    f = banco.apri("mercato")
    assert f.GetTitle() == "Mercato e ricerca" and not f.pulsante_offerta.IsEnabled()
    assert banco.suonati == ["dialogo_mercato", "nessuna_polisportiva_attiva"]
    assert f.situazione.GetValue() == "Nessuna polisportiva attiva: puoi solo cercare."
    tastiera.gancio(f.elenco, "o", alt=True)
    assert banco.dialoghi.letti[-1].startswith("Non hai una polisportiva attiva") and banco.suonati[-1] == "nessuna_polisportiva_attiva"
    f.elenco.SetFocus()
    f.amichevole()
    assert banco.suonati[-1] == "nessuna_polisportiva_attiva"


# Le azioni.

def test_l_ingaggio_di_un_libero(banco):
    random.seed(4)
    f = banco.apri("mercato")
    attiva = banco.mondo.miapolisportiva_attiva
    libero = next(r for r in f.righe if r.stato == mercato.LIBERO)
    _scegli_persona(f, libero.numero)
    posto = f.riga_scelta()
    banco.suonati.clear()
    _clic(f.pulsante_offerta)
    assert banco.dialoghi.aperti == ["Cifra", "Domanda", "Avviso"]
    assert banco.dialoghi.domande[0].startswith(f"Offrire a {testi.nome_completo(libero.persona)} un ingaggio di ")
    testo, riuscita = f.esiti.giocatori[0]
    assert banco.suonati == ["dialogo_cifra_ingaggio", "domanda", "ingaggio_accettato" if riuscita else "ingaggio_rifiutato"]
    assert banco.dialoghi.letti == [testo] and banco.mondo.mosse_rimaste(attiva) == LIMITE_MOVIMENTI_PER_TICK - 1
    assert f.situazione.GetValue() == testi.situazione(banco.mondo) and _fuoco_su(f.elenco)
    if riuscita:
        # Chi ha firmato non è più libero: la scelta resta allo stesso posto.
        assert all(r.numero != libero.numero for r in f.righe) and f.riga_scelta() == min(posto, len(f.righe) - 1)
    # L'annullamento della cifra non costa niente.
    _scegli_persona(f, next(r for r in f.righe if r.stato == mercato.LIBERO).numero)
    banco.dialoghi.copione.append(lambda d: wx.ID_CANCEL)
    _pausa(f)
    _clic(f.pulsante_offerta)
    assert banco.suonati[-1] == "annullato" and len(f.esiti.giocatori) == 1


def test_l_ultima_mossa_oscura_l_offerta(banco):
    attiva = banco.mondo.miapolisportiva_attiva
    attiva.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK - 1
    f = banco.apri("mercato")
    in_vendita = next(r for r in f.righe if r.stato == mercato.IN_VENDITA)
    _scegli_persona(f, in_vendita.numero)
    banco.suonati.clear()
    _clic(f.pulsante_offerta)
    assert banco.dialoghi.aperti == ["Domanda", "Avviso"] and banco.dialoghi.domande[0].startswith(f"Comprare {testi.nome_completo(in_vendita.persona)}")
    assert banco.suonati == ["domanda", "acquisto_fatto", "mosse_finite"] and f.esiti.giocatori[0][1] is True
    assert in_vendita.persona.id in attiva.tesserati and not f.pulsante_offerta.IsEnabled()


def test_i_perche_delle_offerte_che_non_si_fanno(banco):
    f = banco.apri("ricerca")
    _spunta(f, "ritirati")
    _scegli_persona(f, 40)
    banco.suonati.clear()
    _clic(f.pulsante_offerta)
    assert banco.suonati == ["offerta_non_possibile"] and "si è ritirat" in banco.dialoghi.letti[-1]
    _pausa(f)
    _scegli_persona(f, 2)
    _clic(f.pulsante_offerta)
    assert banco.suonati[-1] == "offerta_non_possibile" and "è già tu" in banco.dialoghi.letti[-1]


def test_l_offerta_d_acquisto_e_l_ingaggio_di_un_allenatore(banco):
    random.seed(7)
    f = banco.apri("ricerca")
    attiva = banco.mondo.miapolisportiva_attiva
    attiva.cassa = 10_000_000
    del_computer = next(r for r in f.righe if r.stato == mercato.DEL_COMPUTER)
    _scegli_persona(f, del_computer.numero)
    banco.suonati.clear()
    _clic(f.pulsante_offerta)
    assert banco.dialoghi.aperti == ["Cifra", "Domanda", "Avviso"]
    _testo, riuscita = f.esiti.giocatori[0]
    assert banco.suonati == ["dialogo_cifra_offerta_d_acquisto", "domanda", "offerta_d_acquisto_accettata" if riuscita else "offerta_d_acquisto_rifiutata"]
    # Un allenatore libero: prima il posto, che parte dal primo vuoto, poi la cifra e la domanda.
    a = banco.apri(None, posto=0)
    libero = a.righe[0]
    _scegli_persona(a, libero.numero, allenatore=True)
    banco.dialoghi.aperti.clear()
    banco.suonati.clear()
    posti = []
    banco.dialoghi.copione.append(lambda d: (posti.append(d.posto.GetSelection()), d.conferma(), d.GetReturnCode())[2])
    _clic(a.pulsante_offerta)
    assert posti == [0] and banco.dialoghi.aperti == ["PostoDaOffrire", "Cifra", "Domanda", "Avviso"]
    testo, esito = a.esiti.allenatori[0]
    assert banco.suonati == ["dialogo_posto_da_offrire", "dialogo_cifra_ingaggio_allenatore", "domanda", "allenatore_assunto" if esito == "assunto" else "allenatore_rifiuta"]
    assert esito in ("assunto", "rifiutato") and testo == banco.dialoghi.letti[-1]
    # Il posto già occupato dice il perché col suo suono.
    occupato = 1
    _pausa(a)
    _scegli_persona(a, a.righe[0].numero, allenatore=True)
    banco.dialoghi.copione.append(lambda d: (d.posto.SetSelection(occupato), d.conferma(), d.GetReturnCode())[2])
    _clic(a.pulsante_offerta)
    assert banco.suonati[-1] == "staff_posto_occupato"


def test_l_amichevole_sceglie_prima_l_avversario_poi_il_tuo_giocatore(banco):
    f = banco.apri("amichevole")
    assert banco.suonati == ["dialogo_avversario"]
    avversario = next(r for r in f.righe if r.stato == mercato.DEL_COMPUTER)
    _scegli_persona(f, avversario.numero)
    titoli = []
    banco.dialoghi.copione.append(lambda d: (titoli.append(d.GetTitle()), wx.ID_CANCEL)[1])
    _clic(f.pulsante_amichevole)
    assert titoli == [f"Amichevole contro {testi.nome_completo(avversario.persona)}, il tuo giocatore di Pat-Bologna"]
    assert banco.suonati[-2:] == ["dialogo_amichevole", "annullato"] and f.esiti.amichevole is None and f.GetReturnCode() == 0
    _pausa(f)
    _clic(f.pulsante_amichevole)
    assert banco.dialoghi.aperti[-2:] == ["SceltaGiocatore", "OpzioniAmichevole"] and banco.suonati[-2:] == ["dialogo_amichevole", "dialogo_opzioni_amichevole"]
    tuo, contro, scelte = f.esiti.amichevole
    assert contro is avversario.persona and tuo.id in banco.mondo.miapolisportiva_attiva.tesserati and len(scelte) == 3
    assert f.GetReturnCode() == wx.ID_CLOSE and f.risultato is f.esiti and not f.risultato.vuoti
    # Chi oggi non gioca lo dice col suo suono.
    g = banco.apri("ricerca")
    _spunta(g, "ritirati")
    _scegli_persona(g, 40)
    _clic(g.pulsante_amichevole)
    assert banco.suonati[-1] == "non_gioca_oggi"


def test_la_sfida_apre_il_lancio_sul_suo_club_e_il_diario(banco):
    f = banco.apri("ricerca")
    r = next(x for x in f.righe if x.stato == mercato.DEL_COMPUTER)
    _scegli_persona(f, r.numero)
    scelti = []
    banco.dialoghi.copione.append(lambda d: (scelti.append(d.elenco.GetStringSelection()), wx.ID_CLOSE)[1])
    banco.suonati.clear()
    _clic(f.pulsante_sfida)
    assert banco.dialoghi.aperti == ["LanciaSfida"] and banco.suonati == ["dialogo_lancia_sfida"] and scelti[0].startswith(r.polisportiva.nome)
    # Un libero non ha un club da sfidare.
    _scegli_persona(f, next(x for x in f.righe if x.stato == mercato.LIBERO).numero)
    _pausa(f)
    _clic(f.pulsante_sfida)
    assert banco.suonati[-1] == "club_non_sfidabile"
    _pausa(f)
    _clic(f.pulsante_diario)
    assert banco.dialoghi.aperti[-1] == "Lettura" and banco.suonati[-1] == "diario_giocatore"


# Le condizioni, Azzera e le linguette.

def test_le_condizioni_azzera_e_le_linguette(banco):
    f = banco.apri("ricerca")
    f.libro.ChangeSelection(ALTRI_FILTRI)
    assert f.elenco_condizioni.GetString(0) == testi.NESSUNA_CONDIZIONE
    banco.suonati.clear()
    f.togli_condizione()
    f.togli_tutte_le_condizioni()
    f.azzera_gli_altri_filtri()
    assert banco.suonati == ["nessuna_selezione"] * 3
    _pausa(f)

    def condizione(dialogo):
        dialogo.criterio.SetSelection(mercato.CRITERI_DELLE_CONDIZIONI.index("ambizione"))
        dialogo.valore.SetValue("50")
        dialogo.conferma()
        return dialogo.GetReturnCode()

    banco.dialoghi.copione.append(condizione)
    f.aggiungi_condizione()
    assert f.filtri.condizioni == (("ambizione", "maggiore", 50.0),) and banco.suonati[-2:] == ["dialogo_filtro_mercato", "filtro_aggiunto"]
    assert f.elenco_condizioni.GetString(0) == testi.condizione_a_parole("ambizione", "maggiore", 50.0) and _fuoco_su(f.elenco_condizioni)
    assert f.libro.GetPageText(ALTRI_FILTRI) == "Altri filtri, 1 attivo" and all(r.persona.ambizione > 50 for r in f.righe)
    # Un valore che non è un numero si dice, col suono del campo da correggere.
    banco.dialoghi.copione.append(lambda d: (d.valore.SetValue("tanto"), d.conferma(), wx.ID_CANCEL)[2])
    _pausa(f)
    f.aggiungi_condizione()
    assert banco.dialoghi.letti[-1] == "Il valore deve essere un numero, per esempio 150 o 12,5." and banco.suonati[-2:] == ["campo_da_correggere", "annullato"]
    _scegli_voce(f.tratti["mancino"], 1)
    assert f.filtri.tratti == {"mancino": True} and banco.suonati[-1] == "filtro_tratto_si"
    banco.pianifica.scatta()
    assert f.libro.GetPageText(ALTRI_FILTRI) == "Altri filtri, 2 attivi"
    _scrivi_numero(f.numeri["stipendio_capo_massimo"], 5000)
    banco.pianifica.scatta()
    assert f.libro.GetPageText(FILTRI_ALLENATORI) == "Filtri degli allenatori, 1 attivo" and banco.suonati[-1] == "filtro_stipendio_capo"
    _pausa(f)
    f.azzera_gli_altri_filtri()
    assert f.filtri.condizioni == () and f.filtri.tratti == {} and f.filtri.stipendio_capo_massimo == 5000 and banco.suonati[-1] == "filtri_azzerati"
    assert f.libro.GetPageText(ALTRI_FILTRI) == "Altri filtri" and f.tratti["mancino"].GetSelection() == 0


def test_la_provincia_resta_quando_cambia_la_regione(banco):
    f = banco.apri("ricerca")
    regione = f.scelte["regione"][0]
    _scegli_voce(regione, 1)
    prima = f.filtri.regione
    provincia = f._province[1][0]
    _scegli_voce(f.scelta_provincia, 1)
    assert f.filtri.provincia == provincia and banco.suonati[-1] == "filtro_provincia"
    _scegli_voce(regione, 2)
    assert f.filtri.regione != prima and f.filtri.provincia == provincia
    assert f.scelta_provincia.GetStringSelection() == provincia and f.scelta_provincia.GetSelection() == f.scelta_provincia.GetCount() - 1
    banco.pianifica.scatta()
    assert f"la provincia {provincia} sta in {prima}" in f.filtri_attivi.GetValue()


def test_la_casella_allenatori_cambia_gli_ordini(banco):
    f = banco.apri("ricerca")
    assert f.scelta_ordine.GetCount() == len(mercato.ORDINI_GIOCATORI)
    _spunta(f, "allenatori")
    assert f.scelta_ordine.GetCount() == len(mercato.ORDINI_ALLENATORI) and banco.suonati[-1] == "casella_allenatori_spuntata"
    assert all(r.allenatore for r in f.righe) and f.etichetta_trovati.GetLabel().endswith("allenatori")
    _scegli_voce(f.scelta_ordine, 4)
    assert f.filtri.ordine_allenatori == mercato.ORDINI_ALLENATORI[4][0] and f.filtri.ordine == "numero"
    _spunta(f, "allenatori", False)
    assert f.scelta_ordine.GetStringSelection() == "Numero, dal più basso" and banco.suonati[-1] == "casella_allenatori_tolta"


def test_esc_fuori_dalla_scheda_chiude_e_i_preset_sono_fra_gli_esiti(banco):
    f = banco.apri("mercato")
    banco.dialoghi.copione.append(lambda d: (d.nome.SetValue("Preset di prova"), d.conferma(), d.GetReturnCode())[2])
    f.salva_filtri()
    f.elenco.SetFocus()
    tastiera.gancio(f.elenco, tastiera.VK_ESCAPE)
    assert f.GetReturnCode() == wx.ID_CLOSE and f.risultato.preset == ["Preset salvato: Preset di prova."] and not f.risultato.vuoti
    assert mercato.stato_della_porta(banco.mondo, "mercato").scelta == banco.mondo.filtri_di_ricerca.preset[0].numero
    assert testi.riepilogo_mercato_e_ricerca(banco.mondo.miapolisportiva_attiva, banco.mondo, preset=f.risultato.preset).startswith(
        "Mercato e ricerca di Pat-Bologna: 1 operazione sui preset.\nPreset salvato: Preset di prova.")


# Gli allenatori, da Ctrl+Maiusc+G e da Assumi: le prove del mercato degli allenatori di prima, dai collegamenti della finestra.

def test_gli_allenatori_liberi_dal_migliore_coi_loro_filtri(banco):
    f = banco.apri("allenatori")
    mondo = banco.mondo
    liberi = [a for a in mondo.allenatori.values() if a.libero]
    assert banco.suonati[0] == "dialogo_mercato_allenatori" and f.GetDefaultItem() is None
    # Dalla classe migliore e, a parità di classe, dal più giovane, come nel mercato degli allenatori di prima.
    oggi = mondo.datetime_corrente_simulazione
    assert [r.persona for r in f.righe] == sorted(liberi, key=lambda a: (a.livello, a.eta(oggi), a.numero)) and all(r.allenatore for r in f.righe)
    assert f.etichetta_trovati.GetLabel() == "&" + testi.etichetta_trovati(len(liberi), True)
    assert f.elenco.testo(0) == testi.riga_trovato(f.righe[0], mondo, "classe", f.memoria)
    # La classe migliore o uguale: il migliore resta, e chi è peggiore di lui no.
    migliore = f.righe[0].persona
    _scegli_voce(f.scelte["classe_migliore"][0], migliore.livello)
    assert banco.suonati[-1] == "filtro_classe_allenatori"
    banco.pianifica.scatta()
    assert migliore in [r.persona for r in f.righe] and all(r.persona.livello <= migliore.livello for r in f.righe)
    _scegli_voce(f.scelte["classe_migliore"][0], 0)
    # Il sesso.
    sesso = f.righe[0].persona.sesso
    _scegli_voce(f.scelte["sesso"][0], 1 if sesso == "m" else 2)
    assert banco.suonati[-1] == "filtro_sesso_allenatori"
    banco.pianifica.scatta()
    assert f.righe and all(r.persona.sesso == sesso for r in f.righe)
    _scegli_voce(f.scelte["sesso"][0], 0)
    banco.pianifica.scatta()
    # Il tipo: gli allenatori della prova sono tutti nati, gli ex giocatori non ci sono, e l'elenco si svuota col suo suono.
    tipo = f.scelte["tipo_allenatore"][0]
    _scegli_voce(tipo, 1)
    assert banco.suonati[-1] == "filtro_tipo_allenatori"
    banco.pianifica.scatta()
    assert f.righe == [] and "elenco_svuotato" in banco.suonati
    _scegli_voce(tipo, 2)
    banco.pianifica.scatta()
    assert len(f.righe) == len(liberi) and banco.suonati[-1] == "elenco_ripopolato"
    # L'età massima, col suo suono quando ci si ferma.
    giovane = min(int(r.persona.eta_anni(mondo.datetime_corrente_simulazione)) for r in f.righe)
    _scrivi_numero(f.numeri["eta_massima"], giovane)
    banco.pianifica.scatta()
    assert f.righe and all(int(r.persona.eta_anni(mondo.datetime_corrente_simulazione)) <= giovane for r in f.righe)
    assert "filtro_eta_allenatori" in banco.suonati


def test_l_ingaggio_accettato_di_un_allenatore_e_il_posto_occupato(banco, monkeypatch):
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    f = banco.apri("allenatori")
    mondo = banco.mondo
    attiva = mondo.miapolisportiva_attiva
    a = _scegli_persona(f, f.righe[0].numero, allenatore=True).persona
    richiesta = staff.ingaggio_richiesto(a, staff.CAPO, attiva)
    # Dal progetto 3.1 e dalla revisione l'ingaggio porta la reputazione del club, fra la metà e il doppio.
    stipendi = staff.stipendio_richiesto(a, staff.CAPO) * MESI_DI_INGAGGIO
    assert stipendi / 2 <= richiesta <= stipendi * 2 <= attiva.cassa
    cassa, mosse = attiva.cassa, mondo.mosse_rimaste(attiva)
    domanda = testi.domanda_offerta_allenatore(a, attiva, 0, richiesta, probabilita_accettazione(richiesta, richiesta), mondo)
    banco.suonati.clear()
    _clic(f.pulsante_offerta)
    # Il posto parte dal primo vuoto, il capo; la cifra dalla richiesta; poi la domanda col No già scelto, e l'esito da leggere.
    assert banco.dialoghi.aperti == ["PostoDaOffrire", "Cifra", "Domanda", "Avviso"]
    assert banco.dialoghi.domande == [domanda] and domanda.endswith("Userai una delle 5 mosse che ti restano oggi.")
    assert banco.suonati == ["dialogo_posto_da_offrire", "dialogo_cifra_ingaggio_allenatore", "domanda", "allenatore_assunto"]
    assert attiva.staff[0] == a.numero and a.polisportiva == attiva.nome and a.ruolo == staff.CAPO
    assert attiva.cassa == cassa - richiesta and mondo.mosse_rimaste(attiva) == mosse - 1
    testo = banco.dialoghi.letti[-1]
    assert testo.startswith(f"{testi.nome_completo(a)} ha accettato l'ingaggio di ") and f.esiti.allenatori == [(testo, "assunto")]
    # Chi ha firmato non è più fra i liberi, e la Situazione lo dice.
    assert all(r.numero != a.numero for r in f.righe) and f.situazione.GetValue() == testi.situazione(mondo)
    # Un posto già occupato, scelto a mano, dice il perché col suo suono.
    _pausa(f)
    _scegli_persona(f, f.righe[0].numero, allenatore=True)
    banco.dialoghi.copione.append(lambda d: (d.posto.SetSelection(0), d.conferma(), d.GetReturnCode())[2])
    _clic(f.pulsante_offerta)
    assert banco.suonati[-1] == "staff_posto_occupato" and banco.dialoghi.letti[-1] == "Quel posto dello staff è già occupato."


def test_l_ingaggio_rifiutato_di_un_allenatore_usa_la_mossa(banco, monkeypatch):
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: False)
    mondo = banco.mondo
    attiva = mondo.miapolisportiva_attiva
    staff_di_prima = list(attiva.staff)
    # Da Assumi, sul posto vuoto scelto nello staff: la scelta del posto parte da lì.
    f = banco.apri(None, posto=2)
    a = _scegli_persona(f, f.righe[0].numero, allenatore=True).persona
    mosse = mondo.mosse_rimaste(attiva)
    posti = []
    banco.dialoghi.copione.append(lambda d: (posti.append(d.posto.GetSelection()), d.conferma(), d.GetReturnCode())[2])
    _clic(f.pulsante_offerta)
    assert posti == [2] and banco.suonati[-1] == "allenatore_rifiuta" and a.libero and attiva.staff == staff_di_prima
    assert mondo.mosse_rimaste(attiva) == mosse - 1
    assert f.esiti.allenatori == [(banco.dialoghi.letti[-1], "rifiutato")] and "ha rifiutato l'ingaggio di " in banco.dialoghi.letti[-1]
    assert f"Rifiuta l'offerta di {attiva.nome}, un ingaggio di " in testi.diario_allenatore(a)


def test_gli_allenatori_senza_mosse_senza_cassa_e_in_prelazione(banco):
    mondo = banco.mondo
    attiva = mondo.miapolisportiva_attiva
    # La revisione del 22 ottobre 2026: la prelazione per un'altra tua polisportiva ha il suo suono, non quello del tasto a vuoto.
    f = banco.apri("allenatori")
    r = f.righe[0]
    r.persona.prelazione, r.persona.prelazione_fino = "Un altro tuo club", ORA + datetime.timedelta(days=5)
    _scegli_persona(f, r.numero, allenatore=True)
    banco.suonati.clear()
    _clic(f.pulsante_offerta)
    assert banco.suonati == ["allenatore_in_prelazione"] and "soltanto Un altro tuo club" in banco.dialoghi.letti[-1]
    r.persona.prelazione = r.persona.prelazione_fino = None
    # Con la cassa vuota il perché è la cassa, col suo suono.
    attiva.cassa = 0
    _pausa(f)
    _clic(f.pulsante_offerta)
    assert banco.suonati[-1] == "cassa_insufficiente" and banco.dialoghi.letti[-1] == f"La cassa di {attiva.nome} è vuota."
    # Senza mosse anche Assumi apre con l'offerta oscurata, e Alt+O dice il perché.
    attiva.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    banco.suonati.clear()
    g = banco.apri(None, posto=0)
    assert banco.suonati == ["dialogo_mercato_allenatori", "mosse_finite"] and not g.pulsante_offerta.IsEnabled()
    g.elenco.SetFocus()
    assert tastiera.gancio(g.elenco, "o", alt=True)
    assert banco.dialoghi.letti[-1] == f"Per oggi {attiva.nome} ha finito le mosse di mercato." and banco.suonati[-1] == "mosse_finite"


def test_la_scheda_e_il_diario_di_un_allenatore(banco):
    f = banco.apri("allenatori")
    a = _scegli_persona(f, f.righe[0].numero, allenatore=True).persona
    banco.suonati.clear()
    _invio(f, f.elenco)
    assert f.scheda.GetValue() == testi.scheda_allenatore(a, banco.mondo) and banco.suonati == ["scheda_allenatore"]
    assert f.etichetta_scheda.GetLabel() == f"Sc&heda di {testi.nome_completo(a)}"
    letti = []
    banco.dialoghi.copione.append(lambda d: (letti.append((d.GetTitle(), d.testo.GetValue())), wx.ID_OK)[1])
    _pausa(f)
    _clic(f.pulsante_diario)
    assert banco.dialoghi.aperti[-1] == "Lettura" and banco.suonati[-1] == "diario_allenatore"
    assert letti == [(f"Diario di {testi.nome_completo(a)}", testi.diario_allenatore(a))] and "Entra nel mondo dello showdown" in letti[0][1]


def test_la_finestra_che_si_apre_vuota_lo_dice(banco, monkeypatch):
    # Dal mercato di prima: l'elenco che nasce vuoto suona subito dopo l'apertura.
    monkeypatch.setattr(mercato, "cerca", lambda *a, **k: [])
    banco.apri("mercato")
    assert banco.suonati == ["dialogo_mercato", "elenco_svuotato"]


@pytest.mark.parametrize("nome", ["SceltaGiocatore", "Cifra", "OpzioniAmichevole", "SalvaFiltri", "RinominaPreset", "PostoDaOffrire", "Condizione"])
def test_i_dialoghi_che_confermano_con_invio_contano_l_apertura_come_un_invio(app_wx, mondo, nome):
    # Dalla critica del progetto: un Invio tenuto giù sulla voce di menu sceglieva il primo giocatore e faceva partire l'amichevole.
    attiva = mondo.miapolisportiva_attiva
    fabbriche = {
        "SceltaGiocatore": lambda: dialoghi.SceltaGiocatore(None, mondo),
        "Cifra": lambda: dialoghi.Cifra(None, "Ingaggio", "Spiegazione.", "&Ingaggio", 500, 1000),
        "OpzioniAmichevole": lambda: dialoghi.OpzioniAmichevole(None, mondo, mondo.giocatori[2], mondo.giocatori[30]),
        "SalvaFiltri": lambda: finestra_mr.SalvaFiltri(None, mercato.filtri_di_ricerca_di_serie(), "Giovani"),
        "RinominaPreset": lambda: finestra_mr.RinominaPreset(None, mercato.filtri_di_ricerca_di_serie(), mercato.Preset(1, "Giovani", mercato.Filtri())),
        "PostoDaOffrire": lambda: finestra_mr.PostoDaOffrire(None, mondo, attiva),
        "Condizione": lambda: finestra_mr.Condizione(None),
    }
    dialogo = fabbriche[nome]()
    try:
        dialogo.Show()
        tastiera.pompa()
        fuoco = wx.Window.FindFocus() or dialogo
        # Subito dopo l'apertura Invio si mangia, e subito dopo un altro Invio anche; dopo una pausa, va avanti.
        assert tastiera.gancio(fuoco, tastiera.VK_RETURN) and dialogo.GetReturnCode() == 0
        assert tastiera.gancio(fuoco, tastiera.VK_RETURN)
        dialogo.ultimo_invio = float("-inf")
        assert not tastiera.gancio(fuoco, tastiera.VK_RETURN)
    finally:
        dialogo.Destroy()
        ciclo = wx.GUIEventLoop()
        wx.CallLater(30, ciclo.Exit)
        ciclo.Run()


# Dalle verifiche della finestra, il 24 ottobre 2026.

ROLE_SYSTEM_GROUPING = 20


def _genitori_msaa(maniglia):
    """Nome e ruolo MSAA del controllo e dei suoi genitori, come li vede NVDA: con oleacc e IDispatch di pywin32."""
    import pythoncom
    oleacc = ctypes.WinDLL("oleacc")
    oleacc.AccessibleObjectFromWindow.restype = ctypes.c_long
    oleacc.AccessibleObjectFromWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    iid = ctypes.create_string_buffer(uuid.UUID("{00020400-0000-0000-C000-000000000046}").bytes_le, 16)
    puntatore = ctypes.c_void_p()
    assert oleacc.AccessibleObjectFromWindow(maniglia, 0xFFFFFFFC, iid, ctypes.byref(puntatore)) == 0 and puntatore.value
    oggetto = pythoncom.ObjectFromAddress(puntatore.value, pythoncom.IID_IDispatch)
    catena = []
    while oggetto is not None and len(catena) < 12:
        catena.append((oggetto.Invoke(-5003, 0, pythoncom.DISPATCH_PROPERTYGET, True, 0), oggetto.Invoke(-5006, 0, pythoncom.DISPATCH_PROPERTYGET, True, 0)))
        try:
            genitore = oggetto.Invoke(-5000, 0, pythoncom.DISPATCH_PROPERTYGET, True)
        except pythoncom.com_error:
            break
        oggetto = genitore.QueryInterface(pythoncom.IID_IDispatch) if genitore is not None else None
    return catena


def test_ogni_scheda_e_un_riquadro_che_nvda_dice_col_testo_della_linguetta(banco):
    # Dalla verifica con la lente di NVDA: la pagina di wx è un riquadro senza ruolo, che NVDA non dice, e con Ctrl+Tab
    # NVDA diceva soltanto il controllo. Adesso ogni scheda è un riquadro col testo della linguetta, conto compreso.
    f = banco.apri()
    for posto in range(f.libro.GetPageCount()):
        pagina = f.libro.GetPage(posto)
        figli = list(pagina.GetChildren())
        assert len(figli) == 1 and isinstance(figli[0], wx.StaticBox) and figli[0].GetLabel() == f.libro.GetPageText(posto)
        assert all(figli[0].IsDescendant(c) for c in _focalizzabili(pagina))
    # Il conto della linguetta cambia anche nel riquadro.
    _spunta(f, "senza_acciacchi")
    assert f.libro.GetPageText(ALTRI_FILTRI) == testi.linguetta("Altri filtri", 1) == f._riquadri_delle_schede[ALTRI_FILTRI].GetLabel()
    # Come lo vede NVDA: dopo Ctrl+Tab, fra i genitori del controllo col fuoco c'è il raggruppamento col nome della scheda.
    for _volta in range(2):
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True)
    assert f.libro.GetSelection() == ALTRI_FILTRI
    assert (testi.linguetta("Altri filtri", 1), ROLE_SYSTEM_GROUPING) in _genitori_msaa(tastiera.user32.GetFocus())
    tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True)
    assert ("Filtri degli allenatori", ROLE_SYSTEM_GROUPING) in _genitori_msaa(tastiera.user32.GetFocus())


@pytest.mark.parametrize("via", ["Tab", "Alt+T"])
def test_l_elenco_che_prende_il_fuoco_si_rifa_prima_che_nvda_lo_legga(banco, via):
    # Dalla verifica con la lente di NVDA: con una freccia sulla casella dei preset e subito il fuoco sull'elenco,
    # NVDA leggeva il nome e le righe dell'elenco di prima, e il ricalcolo arrivava dopo, senza che li rileggesse.
    f = banco.apri()
    f.casella_preset.SetFocus()
    tastiera.pompa()
    prima = len(f.righe)
    tastiera.premi(f.casella_preset, tastiera.VK_DOWN)
    assert banco.pianifica.vive() == [0.35, 1.0] and len(f.righe) == prima
    if via == "Tab":
        tastiera.posta_tasto(tastiera.VK_TAB)
    else:
        tastiera.posta_alt("t")
    assert _fuoco_su(f.elenco)
    assert len(f.righe) > prima and len(f.righe) == len(mercato.cerca(banco.mondo, f.filtri))
    assert f.etichetta_trovati.GetLabel() == "&" + testi.etichetta_trovati(len(f.righe))
    # NVDA dice i trovati nel nome dell'elenco: l'annuncio non parte.
    assert 1.0 not in banco.pianifica.vive()
    banco.pianifica.scatta()
    assert banco.annunci.detti == []


@pytest.mark.parametrize("via", ["Tab", "Alt+T", "Ctrl+Tab"])
def test_la_casella_lasciata_dall_elenco_aperto_su_salva_filtri_torna_sulla_voce_applicata(banco, via):
    # Dalla verifica con la lente di NVDA: Windows manda prima l'uscita del fuoco, con la casella ancora sulla voce di
    # prima, poi la scelta di Salva filtri a elenco chiuso; la casella restava lì, e NVDA, tornandoci, leggeva Salva filtri.
    f = banco.apri()
    casella = f.casella_preset
    casella.SetFocus()
    tastiera.pompa()
    applicato = f._posto_applicato
    banco.suonati.clear()
    tastiera.user32.SendMessageW(casella.GetHandle(), 0x014F, 1, 0)
    tastiera.pompa()
    tastiera.posta_tasto(tastiera.VK_END, controllo=casella)
    if via == "Tab":
        tastiera.posta_tasto(tastiera.VK_TAB, controllo=casella)
    elif via == "Alt+T":
        tastiera.posta_alt("t", controllo=casella)
    else:
        tastiera.posta_tasto(tastiera.VK_TAB, ctrl=True, controllo=casella)
    tastiera.aspetta(lambda: not finestra_mr.aperta(casella) and not _fuoco_su(casella), 1.0)
    tastiera.aspetta(lambda: False, 0.2)
    assert not _fuoco_su(casella) and banco.dialoghi.aperti == []
    assert casella.GetSelection() == applicato == f._posto_applicato and f.scelta == "mercato"
    assert "mercato_scelta_cambiata" not in banco.suonati and "filtri_attuali_ripresi" not in banco.suonati


def test_un_dialogo_interno_fa_il_ricalcolo_e_ferma_l_annuncio(banco):
    # Dalla verifica con la lente di NVDA: con un filtro cambiato e subito un dialogo interno, l'annuncio dei trovati
    # scattava dentro il dialogo e arrivava alla voce e al display sopra il suo titolo e il suo testo.
    f = banco.apri("ricerca")
    visti = []

    def guarda(dialogo):
        visti.append((type(dialogo).__name__, banco.pianifica.vive(), all("ro" in testi.nome_completo(r.persona).casefold() for r in f.righe)))
        return wx.ID_CANCEL

    f.campo_nome.SetValue("ro")
    assert banco.pianifica.vive() == [0.35, 1.0]
    banco.dialoghi.copione.append(guarda)
    _pausa(f)
    _clic(f.pulsante_salva)
    # Dentro il dialogo l'elenco è già quello del nome scritto, e l'annuncio non aspetta più.
    assert visti and visti[0][0] == "SalvaFiltri" and 1.0 not in visti[0][1] and visti[0][2]
    # Una persona scelta, poi una casella, che annuncia dopo un secondo, e subito il diario.
    _scegli_persona(f, f.righe[0].numero)
    _spunta(f, "ritirati")
    assert 1.0 in banco.pianifica.vive()
    banco.dialoghi.copione.append(guarda)
    _pausa(f)
    _clic(f.pulsante_diario)
    assert visti[-1][0] == "Lettura" and 1.0 not in visti[-1][1]
    banco.pianifica.scatta()
    assert banco.annunci.detti == []


def test_la_situazione_resta_su_una_riga_sola(banco):
    # Dalla verifica con la lente di NVDA: andava a capo a metà di un blocco di quaranta caratteri, e il display lo spezzava.
    f = banco.apri()
    assert f.situazione.HasFlag(wx.TE_DONTWRAP) and f.situazione.HasFlag(wx.TE_MULTILINE)
    assert len(f.situazione.GetValue()) > 120 and f.situazione.GetNumberOfLines() == 1


def test_la_scheda_si_scrive_col_suo_rimando_anche_all_apertura(banco):
    # Dalla verifica del comportamento: la scheda costava una quarantina di millesimi all'apertura; adesso la scrive il
    # suo rimando, e se prende il fuoco prima, la scrive subito.
    f = banco.apri(rimandi=False)
    assert banco.pianifica.vive() == [0.35] and f.scheda.GetValue() == ""
    banco.pianifica.scatta()
    assert f.scheda.GetValue() == testi.scheda_giocatore(f.riga().persona, banco.mondo)
    g = banco.apri(rimandi=False)
    g.scheda.SetFocus()
    tastiera.pompa()
    assert g.scheda.GetValue() == testi.scheda_giocatore(g.riga().persona, banco.mondo)


def test_i_suoni_dell_apertura_in_fila_si_fermano_alla_chiusura(banco, monkeypatch):
    # Dalla verifica del comportamento: con Esc subito dopo l'apertura, il suono dell'elenco vuoto arrivava dopo quello
    # della finestra chiusa.
    f = banco.apri()
    # Un suono che dura: il seguente aspetta il suo turno nella fila della finestra.
    monkeypatch.setattr(finestra_mr.suoni, "in_coda", lambda evento, **opzioni: banco.suonati.append(evento))
    monkeypatch.setattr(finestra_mr.suoni, "attesa", lambda: 0.2)
    banco.suonati.clear()
    f._in_fila(["mosse_finite", "elenco_svuotato"])
    assert banco.suonati == ["mosse_finite"] and f._fila is not None and f._fila.viva
    f.chiudi_la_finestra()
    assert f._fila is None
    banco.pianifica.scatta()
    assert banco.suonati == ["mosse_finite"]


def test_l_amichevole_contro_l_unico_tuo_giocatore_che_oggi_gioca(banco, monkeypatch):
    # Dalla verifica del comportamento: la finestra diceva che oggi non giocava nessuno dei tuoi, e invece lui gioca, ma
    # non contro sé stesso.
    p = banco.mondo.miapolisportiva_attiva
    unico = banco.mondo.giocatori[p.tesserati[0]]
    monkeypatch.setattr(mercato, "tuoi_per_l_amichevole", lambda mondo, poli, avversario: [g for g in (unico,) if g is not avversario])
    f = banco.apri("ricerca")
    _spunta(f, "tuoi")
    _scegli_persona(f, unico.id)
    _clic(f.pulsante_amichevole)
    assert banco.dialoghi.letti[-1] == testi.unico_per_l_amichevole(unico, p) and banco.suonati[-1] == "non_gioca_oggi"
    assert "Pat-Bologna" in banco.dialoghi.letti[-1] and "scegli un altro avversario" in banco.dialoghi.letti[-1]
    # Con un altro avversario, il tuo giocatore è lui.
    altro = next(r for r in f.righe if r.stato == mercato.DEL_COMPUTER and r.persona.puo_giocare_amichevole(banco.mondo.datetime_corrente_simulazione))
    _pausa(f)
    _scegli_persona(f, altro.numero)
    scelti = []
    banco.dialoghi.copione.append(lambda d: (scelti.append([g.id for g in d.tutti]), wx.ID_CANCEL)[1])
    _clic(f.pulsante_amichevole)
    assert banco.dialoghi.aperti[-1] == "SceltaGiocatore" and scelti == [[unico.id]]


def test_i_massimi_dei_numeri_sono_quelli_del_motore(banco):
    f = banco.apri()
    assert {campo: numero.GetMax() for campo, numero in f.numeri.items()} == mercato.MASSIMI_DEI_NUMERI
