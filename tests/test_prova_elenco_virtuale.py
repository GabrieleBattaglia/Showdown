"""
Le prove del prototipo dell'elenco virtuale della finestra unica, strumenti/prova_elenco_virtuale.py, decisione D36.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
La finestra della prova si apre sul desktop nascosto del conftest, senza suoni e senza voce, in tutte e due le
varianti: l'elenco virtuale e il ListBox col tetto di righe, qui di 40 righe su un mondo di prova di 300 attivi.
Le righe sono quelle della finestra Mercato e ricerca, dai collegamenti della finestra dello stesso 24 ottobre, col
suo motore e testi.riga_trovato, scritte soltanto quando Windows le chiede, e le righe lunghe passano i 300
caratteri dicendo quanti sono; le lettere iniziali le cerca il prototipo, senza che Windows chieda il testo di
tutte le righe; il filtro aspetta 350 millesimi, tiene scelta la stessa persona e annuncia i trovati alla voce e
al display; Scheda lavora sulla riga col fuoco anche dopo Ctrl+Spazio; Esc, battuto davvero sull'elenco, chiude
la finestra come Chiudi. La ricerca per iniziali si prova anche da sola, sui nomi, e le cartelle temporanee
tornano com'erano. Quando la barra verticale dell'elenco virtuale compare o sparisce, per un filtro o per la
finestra che cambia misura, la colonna resta larga quanto l'elenco e la barra orizzontale non compare: lo ha
trovato la verifica del prototipo, il 24 ottobre 2026. Dal passo della finestra, lo stesso giorno, l'elenco virtuale
viene da gui/elenco_virtuale.py e la tastiera simulata da strumenti/tastiera_simulata.py.
"""

import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path

import pytest
import wx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import prova_elenco_virtuale as prova
import tastiera_simulata as tastiera

import mercato
import percorsi
import testi

ATTIVI = 300
TETTO = 40
# Il codice con cui la rete di sicurezza chiude una finestra che Esc non ha chiuso.
NON_CHIUSA = 4242
# Le barre di scorrimento dell'elenco virtuale le mostra Windows da sé, e HasScrollbar di wx non le vede: si
# leggono nello stile della sua finestra, con una copia di user32 tutta della prova.
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetWindowLongW.restype = wintypes.LONG
user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
GWL_STYLE = -16
WS_HSCROLL, WS_VSCROLL = 0x00100000, 0x00200000


class Messaggi(list):
    """I messaggi di wx, al posto di wx.MessageBox: si annotano testo e titolo."""

    def __call__(self, testo, titolo="", *args, **kwargs):
        self.append((testo, titolo))
        return wx.OK


@pytest.fixture(scope="module")
def mondo_e_poli():
    return prova.costruisci_mondo(ATTIVI, prova.SEME)


@pytest.fixture
def messaggi(monkeypatch):
    finti = Messaggi()
    monkeypatch.setattr(wx, "MessageBox", finti)
    return finti


@pytest.fixture(params=[False, True], ids=["virtuale", "listbox"])
def finestra(request, app_wx, mondo_e_poli, messaggi):
    mondo, poli = mondo_e_poli
    dialogo = prova.ProvaElenco(None, mondo, poli, nativo=request.param, tetto=TETTO)
    dialogo.Show()
    prova.pompa()
    yield dialogo
    dialogo.Destroy()
    prova.pompa()


def _clic(controllo):
    evento = wx.CommandEvent(wx.wxEVT_BUTTON if isinstance(controllo, wx.Button) else wx.wxEVT_CHECKBOX, controllo.GetId())
    evento.SetEventObject(controllo)
    if isinstance(controllo, wx.CheckBox):
        evento.SetInt(int(controllo.GetValue()))
    controllo.GetEventHandler().ProcessEvent(evento)
    prova.pompa()


def _barre(controllo):
    """Le barre di scorrimento che Windows mostra sul controllo: (orizzontale, verticale)."""
    stile = user32.GetWindowLongW(controllo.GetHandle(), GWL_STYLE) & 0xFFFFFFFF
    return bool(stile & WS_HSCROLL), bool(stile & WS_VSCROLL)


def _scrivi_nel_campo(dialogo, testo):
    """Il testo nel campo del nome come se lo si scrivesse, poi l'attesa del ricalcolo dopo l'ultimo tasto."""
    prima = len(dialogo.misure["ricalcoli"])
    dialogo.campo.SetValue(testo)
    # Il ricalcolo aspetta l'ultimo tasto: subito non c'è ancora.
    assert len(dialogo.misure["ricalcoli"]) == prima
    assert prova.aspetta(lambda: len(dialogo.misure["ricalcoli"]) > prima)


def test_la_ricerca_per_iniziali_somma_le_lettere_e_ripete_la_stessa():
    nomi = ["anna neri", "andrea bassi", "bruno rossi", "anna verdi", "bice ricci"]
    ricerca = prova.RicercaPerIniziali(attesa=1.0)
    # La prima lettera parte dalla riga dopo quella col fuoco, e senza fuoco dalla prima.
    assert ricerca.cerca("A", nomi, len(nomi), -1, 10.0) == 0
    # La stessa lettera ripetuta passa al nome seguente che comincia così, a giro.
    assert ricerca.cerca("a", nomi, len(nomi), 0, 10.1) == 1
    assert ricerca.cerca("a", nomi, len(nomi), 1, 10.2) == 3
    assert ricerca.cerca("a", nomi, len(nomi), 3, 10.3) == 0
    # Dopo l'attesa si ricomincia; lettere diverse battute di seguito si sommano, a partire dalla riga col fuoco.
    assert ricerca.cerca("b", nomi, len(nomi), 0, 12.0) == 2
    assert ricerca.cerca("i", nomi, len(nomi), 2, 12.5) == 4
    assert ricerca.testo == "bi"
    # Un nome che non c'è non muove niente; e la ricerca guarda soltanto le righe mostrate.
    assert ricerca.cerca("x", nomi, len(nomi), 4, 20.0) is None
    assert ricerca.cerca("b", nomi, 3, 2, 30.0) == 2
    assert not ricerca.in_corso(40.0)


def test_le_cartelle_della_prova_sono_temporanee_e_tornano_com_erano():
    programma, mondo = percorsi.cartella_del_programma(), percorsi.cartella()
    with prova.cartelle_temporanee() as temporanea:
        assert percorsi.cartella() == temporanea
        assert percorsi.cartella_del_programma() != programma
        assert os.path.isfile(percorsi.file_della_cartella())
    assert (percorsi.cartella_del_programma(), percorsi.cartella()) == (programma, mondo)
    assert not os.path.exists(temporanea)


def test_le_righe_sono_quelle_della_finestra_e_le_lunghe_passano_i_300_caratteri(finestra, mondo_e_poli):
    mondo, _poli = mondo_e_poli
    elenco = finestra.elenco
    # Dai collegamenti della finestra le righe vengono dal suo motore: i liberi, chi è in vendita e i tesserati del computer, dal valore più alto.
    tutti = mercato.cerca(mondo, prova.FILTRI_DELLA_PROVA)
    assert len(finestra.visibili) == len(tutti) >= ATTIVI - 1
    assert [r.numero for r in finestra.visibili] == [r.numero for r in tutti]
    assert {r.stato for r in tutti} == {mercato.LIBERO, mercato.IN_VENDITA, mercato.DEL_COMPUTER}
    valori = [r.persona.indice_collettivo_valore for r in tutti]
    assert valori == sorted(valori, reverse=True)
    prima = testi.riga_trovato(tutti[0], mondo, "valore_alto")
    if finestra.nativo:
        assert elenco.mostrate == elenco.GetCount() == TETTO
        assert finestra.etichetta_trovati.GetLabel() == f"&Trovati: {testi.intero(len(tutti))}, nell'elenco i primi {TETTO}"
        assert elenco.GetString(0) == prima
    else:
        assert elenco.mostrate == elenco.GetItemCount() == len(tutti)
        assert finestra.etichetta_trovati.GetLabel() == f"&Trovati: {testi.intero(len(tutti))}"
        # Windows chiede soltanto le righe che mostra, e le riceve da fuori come le leggerebbe uno screen reader.
        assert 0 < elenco.scritte < len(tutti) // 2
        assert prova.testo_letto(elenco, 0, 1024) == prima
        # La colonna è larga quanto l'elenco.
        assert elenco.GetColumnWidth(0) == elenco.GetClientSize().width
    assert finestra.elenco.col_fuoco() == 0
    finestra.lunghe.SetValue(True)
    _clic(finestra.lunghe)
    for indice in (0, elenco.mostrate - 1):
        riga = elenco.testo(indice)
        g = finestra.visibili[indice].persona
        assert len(riga) > prova.LUNGHEZZA_DELLE_RIGHE_LUNGHE
        assert riga.startswith(f"{testi.nome_completo(g)}, ") and f", ID {g.id}, " in riga
        assert riga.endswith(f", fine della riga di {len(riga)} caratteri")
    if not finestra.nativo:
        # A chi chiede la riga con il buffer da 260 caratteri arrivano 259 caratteri; con uno grande, tutta.
        assert prova.caratteri_letti(elenco, 0, 260) == 259
        assert prova.testo_letto(elenco, 0, 4096) == elenco.testo(0)
    else:
        assert prova.caratteri_letti(elenco, 0) == len(elenco.testo(0))


def test_le_lettere_iniziali_le_cerca_il_prototipo(finestra):
    elenco = finestra.elenco
    quante = elenco.mostrate
    nomi = finestra.nomi[:quante]
    iniziali = [nome[0] for nome in nomi]
    # La lettera la cui prima riga sta più in basso: la ricerca di Windows chiederebbe tutte le righe prima.
    lettera = max(set(iniziali[1:]), key=lambda iniziale: iniziali.index(iniziale, 1))
    attesa = iniziali.index(lettera, 1)
    scritte = []
    if not finestra.nativo:
        elenco.riscrivi()
        prova.pompa()
        vera = elenco._riga
        elenco._riga = lambda indice: (scritte.append(indice), vera(indice))[1]
    elenco.SetFocus()
    elenco.scegli(0)
    prova.pompa()
    scritte.clear()
    prova.batti(elenco, lettera.upper())
    assert elenco.col_fuoco() == attesa
    if not finestra.nativo:
        assert elenco.GetFirstSelected() == attesa
        # Si scrivono soltanto le righe della pagina d'arrivo, non quelle che stanno in mezzo.
        primo = elenco.GetTopItem()
        assert scritte and all(primo <= indice <= primo + elenco.GetCountPerPage() for indice in scritte)
    assert finestra.lettere.testo == lettera
    # La stessa lettera ripetuta passa al nome seguente che comincia così, a giro.
    prova.batti(elenco, lettera)
    seguente = next((i for i in range(attesa + 1, quante) if iniziali[i] == lettera), iniziali.index(lettera))
    assert elenco.col_fuoco() == seguente
    # Due lettere diverse di seguito si sommano: dalla prima riga, le prime due lettere di un nome dalla quinta riga in giù.
    elenco.scegli(0)
    prova.pompa()
    finestra.lettere.testo = ""
    prefisso = next(nome[:2] for nome in nomi[4:] if nome[0] != nome[1])
    for carattere in prefisso:
        prova.batti(elenco, carattere)
    assert elenco.col_fuoco() == next(i for i in range(1, quante) if nomi[i].startswith(prefisso))


def test_il_filtro_si_ferma_tiene_la_persona_e_annuncia_i_trovati(finestra, voce_finta, messaggi):
    elenco = finestra.elenco
    elenco.scegli(5)
    prova.pompa()
    persona = finestra.visibili[5].persona
    chiave = persona.cognome[:3].casefold()
    _scrivi_nel_campo(finestra, chiave.upper())
    attesi = [r.numero for r in finestra.tutti if chiave in testi.nome_completo(r.persona).casefold()]
    assert [r.numero for r in finestra.visibili] == attesi
    assert finestra.visibili[elenco.col_fuoco()].persona is persona
    trovati = f"Trovati: {testi.intero(len(attesi))}"
    assert finestra.etichetta_trovati.GetLabel() == "&" + trovati
    assert ("nvda", trovati) in voce_finta.detti
    assert ("nvda", trovati) in voce_finta.braille
    # Il numero si cerca dall'inizio, e quello uguale viene per primo.
    _scrivi_nel_campo(finestra, str(persona.id))
    assert finestra.visibili[0].persona is persona
    assert all(str(r.numero).startswith(str(persona.id)) for r in finestra.visibili)
    assert finestra.visibili[elenco.col_fuoco()].persona is persona
    # Nessuno, perché nessun numero comincia con lo zero: l'elenco è vuoto, e Scheda lo dice.
    _scrivi_nel_campo(finestra, "0")
    assert finestra.visibili == [] and elenco.mostrate == 0
    assert finestra.etichetta_trovati.GetLabel() == "&Trovati: 0"
    assert ("nvda", "Trovati: 0") in voce_finta.detti
    _clic(finestra.pulsante_scheda)
    assert messaggi[-1][0].startswith("L'elenco è vuoto")
    # Di nuovo tutti: la scelta va alla prima riga.
    _scrivi_nel_campo(finestra, "")
    assert len(finestra.visibili) == len(finestra.tutti)
    assert elenco.col_fuoco() == 0
    # Alla chiusura la console dice i tempi: qui quattro ricalcoli.
    assert finestra.riepilogo().startswith("Finestra pronta in ") and "; 4 ricalcoli, in media " in finestra.riepilogo()


def test_tornando_a_tutti_dopo_un_filtro_vuoto_non_compare_la_barra_orizzontale(app_wx, mondo_e_poli):
    """
    Dal filtro senza trovati a tutti, la barra verticale torna e stringe l'elenco virtuale, e Windows lo dice
    mentre l'elenco aggiorna ancora le sue barre: la colonna resta larga quanto l'elenco, e non compare la
    barra orizzontale, con cui le frecce sinistra e destra farebbero scorrere l'elenco di lato.
    """
    mondo, poli = mondo_e_poli
    dialogo = prova.ProvaElenco(None, mondo, poli, tetto=TETTO)
    dialogo.Show()
    prova.pompa()
    try:
        elenco = dialogo.elenco
        for chiave, verticale in (("", True), ("0", False), ("", True), ("0", False), ("", True)):
            if chiave or dialogo.campo.GetValue():
                _scrivi_nel_campo(dialogo, chiave)
                prova.pompa()
            assert _barre(elenco) == (False, verticale), f"filtro {chiave!r}"
            assert elenco.GetColumnWidth(0) == elenco.GetClientSize().width
    finally:
        dialogo.Destroy()
        prova.pompa()


def test_cambiando_misura_alla_finestra_non_compare_la_barra_orizzontale(app_wx, mondo_e_poli):
    """
    Lo stesso quando la barra verticale compare o sparisce perché la finestra cambia misura: con un filtro le
    cui righe stanno tutte nella finestra massimizzata e non in quella ripristinata.
    """
    mondo, poli = mondo_e_poli
    dialogo = prova.ProvaElenco(None, mondo, poli, tetto=TETTO)
    dialogo.Show()
    prova.pompa()
    try:
        elenco = dialogo.elenco
        nella_massimizzata = elenco.GetCountPerPage()
        dialogo.Restore()
        prova.pompa()
        nella_ripristinata = elenco.GetCountPerPage()
        dialogo.Maximize()
        prova.pompa()
        assert nella_ripristinata + 4 < nella_massimizzata
        # Un pezzo di nome che lascia più righe di quante ne stanno nella finestra ripristinata, e meno della massimizzata.
        conti = {}
        for nome in dialogo.nomi_di_tutti:
            for pezzo in {nome[i:i + lunghezza] for lunghezza in (2, 3) for i in range(len(nome) - lunghezza + 1)} - {""}:
                if " " not in pezzo:
                    conti[pezzo] = conti.get(pezzo, 0) + 1
        chiave = next(pezzo for pezzo, quanti in sorted(conti.items()) if nella_ripristinata + 2 <= quanti <= nella_massimizzata - 2)
        _scrivi_nel_campo(dialogo, chiave)
        prova.pompa()
        assert len(dialogo.visibili) == conti[chiave]
        for passo, azione, verticale in (("massimizzata", None, False), ("ripristinata", dialogo.Restore, True), ("di nuovo massimizzata", dialogo.Maximize, False),
                                         ("di nuovo ripristinata", dialogo.Restore, True)):
            if azione is not None:
                azione()
                prova.pompa()
            assert _barre(elenco) == (False, verticale), f"filtro {chiave!r}, finestra {passo}"
            assert elenco.GetColumnWidth(0) == elenco.GetClientSize().width
    finally:
        dialogo.Destroy()
        prova.pompa()


def test_scheda_lavora_sulla_riga_col_fuoco_anche_dopo_ctrl_spazio(finestra, messaggi):
    elenco = finestra.elenco
    elenco.SetFocus()
    elenco.scegli(3)
    prova.pompa()
    finestra.eventi.clear()
    prova.premi(elenco, prova.VK_DOWN)
    assert elenco.col_fuoco() == 4
    if finestra.nativo:
        assert finestra.eventi == [("selezionata", 4)]
    else:
        # La freccia manda la deselezione con -1, il fuoco e la selezione: il -1 non conta.
        assert finestra.eventi == [("deselezionata", -1), ("fuoco", 4), ("selezionata", 4)]
        assert finestra.ultima_riga == 4
        prova.premi(elenco, prova.VK_SPACE, ctrl=True)
        assert elenco.GetFirstSelected() == -1 and elenco.col_fuoco() == 4
    _clic(finestra.pulsante_scheda)
    assert messaggi[-1] == (elenco.testo(4), f"Riga 5 di {testi.intero(elenco.mostrate)}")
    if not finestra.nativo:
        assert elenco.GetFirstSelected() == 4


@pytest.mark.parametrize("nativo", [False, True], ids=["virtuale", "listbox"])
def test_si_apre_massimizzata_e_esc_la_chiude_come_chiudi(app_wx, mondo_e_poli, nativo):
    mondo, poli = mondo_e_poli
    dialogo = prova.ProvaElenco(None, mondo, poli, nativo=nativo, tetto=TETTO)
    visto = {}

    def dentro():
        visto["massimizzata"] = dialogo.IsMaximized()
        tastiera.posta_esc(dialogo.elenco)

    rete = wx.CallLater(3000, lambda: dialogo.IsModal() and dialogo.EndModal(NON_CHIUSA))
    wx.CallAfter(dentro)
    try:
        assert dialogo.GetEscapeId() == dialogo.pulsante_chiudi.GetId()
        codice = dialogo.ShowModal()
    finally:
        rete.Stop()
        dialogo.Destroy()
    assert visto["massimizzata"]
    assert codice == wx.ID_CLOSE
