"""
Test della barra di stato su misura nella finestra, decisione D38, sul desktop nascosto del conftest: la barra di serie,
il rinfresco ogni 20 secondi anche col cursore sopra, che resta sulla stessa riga e nella stessa colonna, la barra che a metà
di un comando aspetta la fine, F7 che la rifà tutta, e la finestra della barra di stato, coi suoi tasti, i suoi avvisi e i
suoi suoni, le chiavi sconosciute che restano e il Salva che la mette nel file delle impostazioni.
"""

import datetime
import random
import types

import pytest
import wx
from aiuti_barra import evento_della_barra

import archivio
import barra
import impostazioni
from gui import barra_di_stato as gui_barra
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from utilita import adesso, adesso_utc


@pytest.fixture
def mondo():
    random.seed(11)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(30, ora)
    mia = Polisportiva("Club Di Prova", "segreta", ora)
    m.polisportive[mia.nome] = mia
    for gid in (2, 5):
        mia.aggiungi_tesserato(gid, m.giocatori[gid].indice_collettivo_valore)
        m.giocatori[gid].appartenenza = mia.nome
    m.miapolisportiva_attiva = mia
    return m


@pytest.fixture
def finestra(app_wx, mondo, monkeypatch):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.NO)
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def _cursore(controllo):
    _trovata, colonna, riga = controllo.PositionToXY(controllo.GetInsertionPoint())
    return colonna, riga


def _metti_il_cursore(controllo, colonna, riga):
    controllo.SetInsertionPoint(controllo.XYToPosition(colonna, riga))
    assert _cursore(controllo) == (colonna, riga)


def _con_la_barra(finestra, scelta):
    finestra.impostazioni = {**finestra.impostazioni, "barra_di_stato": scelta}
    finestra._istantanea.clear()
    finestra.aggiorna_barra()


# La barra nella finestra.

def test_la_barra_di_serie_e_il_rinfresco_ogni_20_secondi(finestra):
    righe = finestra.barra.GetValue().splitlines()
    assert len(righe) == 10 and righe[-1] == "Not:0 mondo pronto" and evento_della_barra(finestra) == "mondo pronto"
    assert finestra.timer.GetInterval() == barra.RINFRESCO_MILLESIMI == 20_000
    # La barra è alta quanto le sue righe.
    alta = finestra.barra.GetMinSize().height
    _con_la_barra(finestra, [["gloria"], ["ultimo_evento"]])
    finestra.applica_aspetto()
    assert finestra.barra.GetMinSize().height < alta and finestra.barra.GetValue() == "Glo:100\nmondo pronto"


def test_il_cursore_resta_dov_era_quando_la_barra_si_riscrive(finestra):
    _con_la_barra(finestra, [["gloria", "cassa"], ["nome_polisportiva", "tesserati", "ultimo_evento"]])
    finestra.ultimo_evento = "un evento piuttosto lungo"
    finestra.aggiorna_barra()
    _metti_il_cursore(finestra.barra, 10, 1)
    # La riga cambia ma resta lunga: il cursore resta sulla stessa riga e nella stessa colonna.
    finestra.ultimo_evento = "un altro evento ancora più lungo"
    finestra._al_rinfresco(None)
    assert finestra.barra.GetValue().splitlines()[1].endswith("un altro evento ancora più lungo") and _cursore(finestra.barra) == (10, 1)
    # La riga si accorcia sotto il cursore: va a fine riga.
    _metti_il_cursore(finestra.barra, 40, 1)
    finestra.ultimo_evento = "corto"
    finestra.aggiorna_barra()
    riga = finestra.barra.GetValue().splitlines()[1]
    assert _cursore(finestra.barra) == (len(riga), 1)
    # Le righe sono meno di prima: il cursore va sull'ultima.
    _metti_il_cursore(finestra.barra, 3, 1)
    _con_la_barra(finestra, [["gloria", "cassa"]])
    assert finestra.barra.GetValue() == "Glo:100 Cas:20.000" and _cursore(finestra.barra) == (3, 0)


def test_a_meta_di_un_comando_la_barra_aspetta_la_fine(finestra):
    viste = []

    def comando():
        finestra.mostra("Un risultato.", "evento del comando")
        viste.append(finestra.barra.GetValue())

    finestra._esegui(comando)
    assert "evento del comando" not in viste[0] and evento_della_barra(finestra) == "evento del comando"


def test_l_istantanea_si_svuota_dopo_il_comando_e_f7_la_rifa(finestra):
    _con_la_barra(finestra, [["gloria"], ["ultimo_evento"]])
    finestra.mondo.miapolisportiva_attiva.gloria = 150
    finestra.aggiorna_barra()
    assert finestra.barra.GetValue().startswith("Glo:100")
    finestra._esegui(lambda: None)
    assert finestra.barra.GetValue().startswith("Glo:150")
    finestra.mondo.miapolisportiva_attiva.gloria = 175
    finestra.barra.SetFocus()
    wx.Yield()
    if finestra.barra.HasFocus():
        finestra.vai_alla_barra()
        assert finestra.barra.GetValue().startswith("Glo:175")


def test_il_salvataggio_che_non_riesce_compare_in_testa(finestra, monkeypatch):
    monkeypatch.setattr(archivio, "salva_con_avvisi", lambda mondo: (False, []))
    finestra._salva_raccogliendo()
    finestra.aggiorna_barra()
    assert finestra.barra.GetValue().startswith("Slv:fallito Dat:")
    monkeypatch.setattr(archivio, "salva_con_avvisi", lambda mondo: (True, []))
    finestra._salva_raccogliendo()
    finestra.aggiorna_barra()
    assert finestra.barra.GetValue().startswith("Dat:")


# La finestra della barra di stato.

def _finestra_della_barra(finestra, scelta=None):
    if scelta is not None:
        finestra.impostazioni = {**finestra.impostazioni, "barra_di_stato": scelta}
    return gui_barra.BarraDiStato(finestra, finestra.impostazioni, finestra.contesto_della_barra)


def _etichette(elenco):
    return [elenco.GetString(i) for i in range(elenco.GetCount())]


def test_dati_e_righe_si_spostano(finestra, suonati):
    dialogo = _finestra_della_barra(finestra, [["gloria", "cassa"], ["ultimo_evento"]])
    try:
        assert dialogo.scelta_riga.GetItems() == ["Riga 1, 2 dati", "Riga 2, 1 dato"]
        assert _etichette(dialogo.della_riga) == ["Glo, gloria", "Cas, cassa"]
        assert dialogo.disponibili.GetCount() == len(barra.CATALOGO) - 3 and _etichette(dialogo.disponibili)[:2] == ["Dat, data simulata", "giorno della settimana"]
        assert dialogo.anteprima.GetValue() == "Glo:100 Cas:20.000"
        # Il primo dei disponibili va in fondo alla riga; la scelta resta al primo posto, sul dato che segue.
        dialogo.disponibili.SetSelection(0)
        dialogo.aggiungi_dato()
        assert dialogo.righe[0] == ["gloria", "cassa", "data_simulata"] and dialogo.disponibili.GetSelection() == 0
        assert _etichette(dialogo.disponibili)[0] == "giorno della settimana" and dialogo.della_riga.GetSelection() == 2
        assert dialogo.anteprima.GetValue().startswith("Glo:100 Cas:20.000 Dat:")
        # Sposta su e giù, e il bordo.
        dialogo.sposta(-1)
        assert dialogo.righe[0] == ["gloria", "data_simulata", "cassa"] and dialogo.della_riga.GetSelection() == 1
        dialogo.sposta(1)
        dialogo.sposta(1)
        assert dialogo.righe[0] == ["gloria", "cassa", "data_simulata"]
        # Il dato tolto torna fra i disponibili, al suo posto nel catalogo.
        dialogo.della_riga.SetSelection(0)
        dialogo.togli_dato()
        assert dialogo.righe[0] == ["cassa", "data_simulata"] and "Glo, gloria" in _etichette(dialogo.disponibili)
        assert dialogo.disponibili.GetString(dialogo.disponibili.GetSelection()) == "Glo, gloria"
        # Una riga nuova dopo quella scelta, poi via; i suoi dati tornano disponibili.
        dialogo.aggiungi_riga()
        assert len(dialogo.righe) == 3 and dialogo.riga == 1 and dialogo.righe[1] == [] and dialogo.scelta_riga.GetSelection() == 1
        assert dialogo.anteprima.GetValue() == "La riga è vuota, e non si salverà."
        dialogo.disponibili.SetSelection(0)
        dialogo.aggiungi_dato()
        dialogo.togli_riga()
        assert dialogo.righe == [["cassa", "data_simulata"], ["ultimo_evento"]] and dialogo.riga == 1
        assert suonati == ["barra_dato_aggiunto", "barra_dato_su", "barra_dato_giu", "barra_dato_al_bordo", "barra_dato_tolto", "barra_riga_aggiunta",
                           "barra_dato_aggiunto", "barra_riga_tolta"]
    finally:
        dialogo.Destroy()


def test_i_limiti_e_la_barra_di_serie(finestra, suonati, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo) or wx.OK)
    dialogo = _finestra_della_barra(finestra, [["gloria"]])
    try:
        # Con la riga sola, Togli riga dice di no; con sedici righe, Aggiungi riga.
        dialogo.togli_riga()
        for _n in range(barra.RIGHE_MASSIME - 1):
            dialogo.aggiungi_riga()
        assert len(dialogo.righe) == barra.RIGHE_MASSIME
        dialogo.aggiungi_riga()
        assert len(dialogo.righe) == barra.RIGHE_MASSIME
        assert avvisi == ["La barra ha una riga sola: si può svuotare, ma non togliere.", "La barra ha già 16 righe, il massimo."]
        assert suonati[0] == "barra_riga_sola" and suonati[-1] == "barra_righe_piene"
        # Su un elenco vuoto il tasto a vuoto.
        dialogo.scelta_riga.SetSelection(3)
        dialogo._alla_riga(None)
        suonati.clear()
        dialogo.togli_dato()
        dialogo.sposta(1)
        assert suonati == ["nessuna_selezione", "nessuna_selezione"]
        dialogo.barra_di_serie()
        assert dialogo.righe == [list(r) for r in barra.BARRA_DI_SERIE] and dialogo.disponibili.GetCount() == 0
        dialogo.disponibili.SetFocus()
        dialogo.aggiungi_dato()
        assert suonati[-2:] == ["barra_di_serie_rimessa", "nessuna_selezione"]
    finally:
        dialogo.Destroy()


def test_le_chiavi_sconosciute_restano_nella_loro_riga(finestra):
    dialogo = _finestra_della_barra(finestra, [["dato_di_domani", "gloria"], ["ultimo_evento"]])
    try:
        assert dialogo.righe == [["gloria"], ["ultimo_evento"]] and _etichette(dialogo.della_riga) == ["Glo, gloria"]
        dialogo.salva()
        assert dialogo.risultato == [["gloria", "dato_di_domani"], ["ultimo_evento"]]
    finally:
        dialogo.Destroy()


def _tasto(codice, ripetuto=False, modificatori=False):
    saltati = []
    return types.SimpleNamespace(GetKeyCode=lambda: codice, IsAutoRepeat=lambda: ripetuto, HasAnyModifiers=lambda: modificatori,
                                 ControlDown=lambda: modificatori, AltDown=lambda: False, ShiftDown=lambda: False,
                                 Skip=lambda: saltati.append(True), saltati=saltati)


def test_invio_spazio_e_canc_sugli_elenchi(finestra, suonati, monkeypatch):
    dialogo = _finestra_della_barra(finestra, [["gloria"]])
    fuoco = [dialogo.disponibili]
    monkeypatch.setattr(gui_barra, "controllo_col_fuoco", lambda: fuoco[0])
    try:
        dialogo.disponibili.SetSelection(0)
        dialogo._tasto(_tasto(wx.WXK_RETURN))
        dialogo._tasto(_tasto(wx.WXK_SPACE))
        # Uno Spazio tenuto giù non aggiunge niente, e non arriva all'elenco.
        ripetuto = _tasto(wx.WXK_SPACE, ripetuto=True)
        dialogo._tasto(ripetuto)
        assert dialogo.righe[0] == ["gloria", "data_simulata", "giorno_della_settimana"] and not ripetuto.saltati
        fuoco[0] = dialogo.della_riga
        dialogo.della_riga.SetSelection(0)
        dialogo._tasto(_tasto(wx.WXK_DELETE))
        # Un secondo Canc entro mezzo secondo è un tasto tenuto giù.
        dialogo._tasto(_tasto(wx.WXK_DELETE))
        assert dialogo.righe[0] == ["data_simulata", "giorno_della_settimana"]
        dialogo._tasto(_tasto(wx.WXK_SPACE))
        assert dialogo.righe[0] == ["giorno_della_settimana"]
        # Con un modificatore, o fuori dagli elenchi, il tasto prosegue.
        con_alt = _tasto(ord("S"), modificatori=True)
        dialogo._tasto(con_alt)
        fuoco[0] = dialogo.scelta_riga
        invio = _tasto(wx.WXK_RETURN)
        dialogo._tasto(invio)
        assert con_alt.saltati and invio.saltati and dialogo.risultato is None
        assert suonati == ["barra_dato_aggiunto", "barra_dato_aggiunto", "barra_dato_tolto", "barra_dato_tolto"]
    finally:
        dialogo.Destroy()


def test_la_voce_del_menu_salva_la_barra(finestra, suonati, monkeypatch):
    def mostra(self):
        self.togli_riga()
        self.salva()
        return wx.ID_OK

    monkeypatch.setattr(gui_barra.BarraDiStato, "ShowModal", mostra)
    finestra._esegui(finestra.cambia_barra)
    assert suonati == ["dialogo_barra_di_stato", "barra_riga_tolta", "barra_di_stato_salvata"]
    salvata = impostazioni.carica()["barra_di_stato"]
    assert salvata == [list(r) for r in barra.BARRA_DI_SERIE[1:]] and finestra.impostazioni["barra_di_stato"] == salvata
    assert len(finestra.barra.GetValue().splitlines()) == 9 and evento_della_barra(finestra) == "barra di stato salvata"
    # Con Annulla resta tutto com'era.
    monkeypatch.setattr(gui_barra.BarraDiStato, "ShowModal", lambda self: wx.ID_CANCEL)
    suonati.clear()
    finestra._esegui(finestra.cambia_barra)
    assert suonati == ["dialogo_barra_di_stato", "annullato"] and impostazioni.carica()["barra_di_stato"] == salvata


# La spiegazione delle sigle, richiesta di Gabriele del 25 ottobre 2026.

def _vai(finestra, colonna, riga):
    """Il cursore va alla colonna e alla riga date, e si lascia il tasto, come con le frecce."""
    _metti_il_cursore(finestra.barra, colonna, riga)
    finestra._mossa_nella_barra(_tasto(wx.WXK_RIGHT))


def test_entrando_in_un_dato_con_la_sigla_se_ne_sente_il_nome(finestra, voce_finta):
    _con_la_barra(finestra, [["nome_polisportiva", "gloria", "cassa"], ["ultimo_evento"]])
    assert finestra.barra.GetValue() == "Club Di Prova Glo:100 Cas:20.000\nmondo pronto"
    _vai(finestra, 14, 0)
    # Alla sintesi e al display braille, con la scelta automatica, cioè NVDA nelle prove.
    assert voce_finta.detti == [("nvda", "gloria")] and voce_finta.braille == [("nvda", "gloria")]
    # Dentro lo stesso dato non si ripete.
    _vai(finestra, 17, 0)
    _vai(finestra, 20, 0)
    assert voce_finta.detti == [("nvda", "gloria")]
    # Sullo spazio niente; rientrando nello stesso dato, di nuovo.
    _vai(finestra, 21, 0)
    _vai(finestra, 20, 0)
    _vai(finestra, 25, 0)
    assert [testo for _uscita, testo in voce_finta.detti] == ["gloria", "gloria", "cassa"]
    # I dati senza sigla non si spiegano: il nome della polisportiva e l'ultimo evento.
    _vai(finestra, 3, 0)
    _vai(finestra, 2, 1)
    assert [testo for _uscita, testo in voce_finta.detti] == ["gloria", "gloria", "cassa"]


def test_ne_l_arrivo_ne_la_riscrittura_spiegano_il_dato(finestra, voce_finta):
    _con_la_barra(finestra, [["gloria", "cassa"], ["ultimo_evento"]])
    _vai(finestra, 10, 0)
    assert [testo for _uscita, testo in voce_finta.detti] == ["cassa"]
    # La riscrittura sposta i dati sotto il cursore, che finisce sulla gloria: non è una mossa, e tace.
    finestra.mondo.miapolisportiva_attiva.gloria = 1_000_000
    finestra._istantanea.clear()
    finestra.aggiorna_barra()
    assert finestra.barra.GetValue().startswith("Glo:1000000 Cas:") and finestra._dato_sotto_il_cursore == "gloria"
    finestra._mossa_nella_barra(_tasto(wx.WXK_SHIFT))
    assert [testo for _uscita, testo in voce_finta.detti] == ["cassa"]
    # Arrivando sulla barra, il dato su cui sta il cursore si ricorda in silenzio.
    finestra.vista.SetFocus()
    _metti_il_cursore(finestra.barra, 2, 0)
    finestra._alla_barra(_tasto(wx.WXK_TAB))
    finestra._mossa_nella_barra(_tasto(wx.WXK_TAB))
    assert [testo for _uscita, testo in voce_finta.detti] == ["cassa"]
    # La sintesi scelta per gli annunci vale anche qui.
    finestra.impostazioni = {**finestra.impostazioni, "annunci_sintesi": "sapi5"}
    _vai(finestra, 13, 0)
    assert voce_finta.detti[-1] == ("sapi5", "cassa") and voce_finta.braille[-1] == ("nvda", "cassa")


# I ritocchi del collaudo di Gabriele del 25 ottobre 2026.

def _detti(voce_finta):
    return [testo for _uscita, testo in voce_finta.detti]


def _con_tasto(finestra, colonna, riga, codice, ctrl=False):
    """Il cursore va alla colonna e alla riga date col tasto dato: il tasto scende, il cursore si muove, il tasto si lascia."""
    finestra._tasto_giu_nella_barra(_tasto(codice, modificatori=ctrl))
    _metti_il_cursore(finestra.barra, colonna, riga)
    finestra._mossa_nella_barra(_tasto(codice, modificatori=ctrl))


def test_le_frecce_verticali_cambiano_riga_in_silenzio(finestra, voce_finta):
    _con_la_barra(finestra, [["gloria", "cassa"], ["tesserati", "disponibili"], ["ultimo_evento"]])
    # Con la freccia giù si arriva nei tesserati senza sentirne il nome, e nemmeno muovendosi dentro lo stesso dato.
    _con_tasto(finestra, 2, 1, wx.WXK_DOWN)
    _con_tasto(finestra, 4, 1, wx.WXK_RIGHT)
    assert _detti(voce_finta) == [] and finestra._attesa_lunga is None
    # Con la freccia destra nel dato seguente sì.
    _con_tasto(finestra, 10, 1, wx.WXK_RIGHT)
    assert _detti(voce_finta) == ["disponibili"]
    # Ctrl+Giù lasciando prima Ctrl: conta la freccia, e tace.
    finestra._tasto_giu_nella_barra(_tasto(wx.WXK_DOWN, modificatori=True))
    _metti_il_cursore(finestra.barra, 1, 0)
    finestra._mossa_nella_barra(_tasto(wx.WXK_CONTROL, modificatori=False))
    finestra._mossa_nella_barra(_tasto(wx.WXK_DOWN, modificatori=False))
    assert _detti(voce_finta) == ["disponibili"] and finestra._dato_sotto_il_cursore == "gloria"
    # Ctrl+Inizio e Pagina giù cambiano riga in silenzio; Inizio senza Ctrl si muove nella riga, e parla.
    _con_tasto(finestra, 0, 1, wx.WXK_PAGEDOWN)
    _con_tasto(finestra, 0, 0, wx.WXK_HOME, ctrl=True)
    assert _detti(voce_finta) == ["disponibili"]
    _con_tasto(finestra, 0, 1, wx.WXK_HOME)
    assert _detti(voce_finta) == ["disponibili", "tesserati"]


def test_il_cursor_routing_del_display_spiega_il_dato(finestra, voce_finta):
    _con_la_barra(finestra, [["gloria", "cassa"], ["ultimo_evento"]])
    finestra._controllo_attivo = True
    # Il cursore si sposta senza tasti, come col cursor routing: il controllo del cursore lo vede.
    _metti_il_cursore(finestra.barra, 9, 0)
    finestra._controlla_il_cursore()
    assert _detti(voce_finta) == ["cassa"] and voce_finta.braille[-1] == ("nvda", "cassa")
    # Mentre un tasto è giù, il controllo aspetta che lo si lasci.
    finestra._tasto_giu_nella_barra(_tasto(wx.WXK_LEFT))
    _metti_il_cursore(finestra.barra, 1, 0)
    finestra._controlla_il_cursore()
    assert _detti(voce_finta) == ["cassa"]
    finestra._mossa_nella_barra(_tasto(wx.WXK_LEFT))
    assert _detti(voce_finta) == ["cassa", "gloria"]


def test_dieci_secondi_fermi_nel_dato_e_parte_la_spiegazione_lunga(finestra, voce_finta):
    _con_la_barra(finestra, [["gloria", "cassa"], ["tesserati"], ["ultimo_evento"]])
    _con_tasto(finestra, 9, 0, wx.WXK_RIGHT)
    _con_tasto(finestra, 1, 0, wx.WXK_LEFT)
    attesa = finestra._attesa_lunga
    assert _detti(voce_finta) == ["cassa", "gloria"] and attesa is not None and attesa.IsRunning()
    # Muovendosi dentro il dato l'attesa riparte da capo.
    _con_tasto(finestra, 3, 0, wx.WXK_RIGHT)
    assert finestra._attesa_lunga is not attesa and finestra._attesa_lunga.IsRunning() and not attesa.IsRunning()
    finestra._spiega_a_lungo()
    lunga = barra.spiegazione_lunga(barra.CATALOGO["gloria"])
    assert _detti(voce_finta) == ["cassa", "gloria", lunga]
    # Una volta sola per ingresso.
    _con_tasto(finestra, 4, 0, wx.WXK_RIGHT)
    finestra._spiega_a_lungo()
    assert _detti(voce_finta) == ["cassa", "gloria", lunga] and finestra._attesa_lunga is None
    # Uscendo dal dato, o dalla barra, l'attesa si ferma e non parla.
    _con_tasto(finestra, 9, 0, wx.WXK_RIGHT)
    assert finestra._attesa_lunga is not None
    _con_tasto(finestra, 2, 1, wx.WXK_DOWN)
    assert finestra._attesa_lunga is None
    _con_tasto(finestra, 10, 0, wx.WXK_UP)
    _con_tasto(finestra, 1, 0, wx.WXK_LEFT)
    assert finestra._attesa_lunga is not None
    finestra._via_dalla_barra(_tasto(wx.WXK_TAB))
    assert finestra._attesa_lunga is None and not finestra._controllo_attivo
    finestra._spiega_a_lungo()
    assert _detti(voce_finta) == ["cassa", "gloria", lunga, "cassa", "gloria"]


def test_il_giro_del_tab_della_finestra_della_barra(finestra):
    dialogo = _finestra_della_barra(finestra, [["gloria", "cassa"]])
    try:
        figli = list(dialogo.pannello.GetChildren())
        ordine = [dialogo.scelta_riga, dialogo.pulsante_aggiungi_riga, dialogo.pulsante_togli_riga, dialogo.della_riga, dialogo.spiegazione,
                  dialogo.disponibili, dialogo.anteprima, dialogo.pulsante_di_serie, dialogo.pulsante_salva]
        posti = [figli.index(controllo) for controllo in ordine]
        assert posti == sorted(posti)
    finally:
        dialogo.Destroy()


def test_gli_elenchi_vuoti_escono_dal_giro_del_tab(finestra, monkeypatch):
    dialogo = _finestra_della_barra(finestra)
    chiamati = []
    try:
        # La barra di serie usa tutti i dati: Dati disponibili è vuoto e non disponibile.
        assert not dialogo.disponibili.IsEnabled() and dialogo.della_riga.IsEnabled()
        dialogo.della_riga.SetSelection(0)
        dialogo.togli_dato()
        assert dialogo.disponibili.IsEnabled() and dialogo.disponibili.GetCount() == 1
        # Il dato torna nella riga: i disponibili finiscono, e il fuoco che stava lì passa ai dati della riga.
        monkeypatch.setattr(gui_barra, "controllo_col_fuoco", lambda: dialogo.disponibili)
        monkeypatch.setattr(dialogo.della_riga, "SetFocus", lambda: chiamati.append("della riga"))
        dialogo.disponibili.SetSelection(0)
        dialogo.aggiungi_dato()
        assert not dialogo.disponibili.IsEnabled() and chiamati == ["della riga"]
        # Una riga che si svuota manda il fuoco ai disponibili; con tutti e due gli elenchi vuoti, alla scelta Riga.
        dialogo._carica([["gloria"], ["cassa"]])
        dialogo._scrivi(0, 0, 0)
        monkeypatch.setattr(gui_barra, "controllo_col_fuoco", lambda: dialogo.della_riga)
        monkeypatch.setattr(dialogo.disponibili, "SetFocus", lambda: chiamati.append("disponibili"))
        dialogo.della_riga.SetSelection(0)
        dialogo.togli_dato()
        assert not dialogo.della_riga.IsEnabled() and chiamati == ["della riga", "disponibili"]
    finally:
        dialogo.Destroy()


# Invio sulla barra, idea di Gabriele del 25 ottobre 2026.

def test_ogni_voce_di_invio_sta_nei_menu(finestra):
    assert all(finestra.comando_della_voce(voce) is not None for voce in set(barra.VOCI_DEI_DATI.values()))


def test_invio_sulla_barra_apre_la_voce_del_dato(finestra, suonati):
    chiamate = []
    finestra.sfide_in_arrivo = lambda: chiamate.append("sfide in arrivo")
    finestra.riepilogo = lambda: chiamate.append("riepilogo")
    _con_la_barra(finestra, [["sfide_ricevute", "durata_sessione"], ["notizie_ultimo_avanzamento", "ultimo_evento"]])
    assert finestra.barra.GetValue().startswith("Sfr:0 Dur:")
    comandi = finestra.comandi
    _metti_il_cursore(finestra.barra, 2, 0)
    finestra.invio_nella_barra()
    _metti_il_cursore(finestra.barra, 1, 1)
    finestra.invio_nella_barra()
    assert chiamate == ["sfide in arrivo", "riepilogo"] and finestra.comandi == comandi + 2
    # La durata della sessione non apre niente, e nemmeno lo spazio fra due dati: il tasto a vuoto.
    suonati.clear()
    _metti_il_cursore(finestra.barra, 7, 0)
    finestra.invio_nella_barra()
    _metti_il_cursore(finestra.barra, 5, 0)
    finestra.invio_nella_barra()
    assert suonati == ["nessuna_selezione", "nessuna_selezione"] and len(chiamate) == 2


def test_ctrl_frecce_spostano_i_dati_della_riga(finestra, suonati, monkeypatch):
    # Dal 25 ottobre 2026, richiesta di Gabriele: al posto dei pulsanti Sposta su e Sposta giù, coi loro suoni.
    dialogo = _finestra_della_barra(finestra, [["gloria", "cassa", "sponsor"]])
    monkeypatch.setattr(gui_barra, "controllo_col_fuoco", lambda: dialogo.della_riga)
    try:
        assert not hasattr(dialogo, "pulsante_su") and not hasattr(dialogo, "pulsante_giu")
        dialogo.della_riga.SetSelection(0)
        dialogo._tasto(_tasto(wx.WXK_DOWN, modificatori=True))
        assert dialogo.righe[0] == ["cassa", "gloria", "sponsor"] and dialogo.della_riga.GetSelection() == 1
        dialogo._tasto(_tasto(wx.WXK_NUMPAD_UP, modificatori=True))
        dialogo._tasto(_tasto(wx.WXK_UP, modificatori=True))
        assert dialogo.righe[0] == ["gloria", "cassa", "sponsor"] and suonati == ["barra_dato_giu", "barra_dato_su", "barra_dato_al_bordo"]
        # La freccia senza Ctrl resta all'elenco.
        freccia = _tasto(wx.WXK_DOWN)
        dialogo._tasto(freccia)
        assert freccia.saltati and dialogo.righe[0] == ["gloria", "cassa", "sponsor"]
    finally:
        dialogo.Destroy()
