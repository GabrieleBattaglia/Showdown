"""
La rassegna delle finestre interne, dal collaudo di Gabriele del 23 ottobre 2026, tappa 14.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Ogni dialogo di gui/ si apre con ShowModal, come lo apre la finestra, sul desktop nascosto del conftest
e senza suonare: dentro il suo ciclo si guarda che sia massimizzato e si preme Esc, che deve chiuderlo.
Se ha un pulsante Chiudi, Esc deve chiuderlo con lo stesso codice del pulsante, premuto in una seconda
apertura; senza Chiudi, deve chiuderlo come Annulla, o come Non adesso nella proposta
dell'aggiornamento. La partita dal vivo tiene il suo Esc, che esce senza svelare il risultato. La rassegna sa
quali dialoghi ci sono: un dialogo nuovo che non ci sta fa fallire la prova, finché non lo si aggiunge
a FABBRICHE. Un Chiudi wx.ID_CLOSE o qualunque, come in un dialogo futuro, risponde a Esc anche lui.
Dal 24 ottobre 2026 ci sono anche la finestra Mercato e ricerca e i suoi dialoghi interni, con i testi da leggere
delle domande, che a Esc valgono No, e degli avvisi; coi collegamenti dello stesso giorno escono il mercato dei
giocatori, quello degli allenatori e la ricerca, che la finestra ha sostituito.
"""

import importlib
import pkgutil
import random
import types

import pytest
import wx
from aiuti_calendario import OGGI, apri, mondo_di_prova, polisportiva
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

import formule
import gui
import impostazioni
import mercato
import modelli_torneo
import testi
from gui import dal_vivo, dialoghi
from gui import editor_tornei as gui_editor
from gui import mercato_e_ricerca as gui_mercato
from gui import sfide as gui_sfide
from gui import tornei as gui_tornei
from motore import COMPLETO, SINGOLARE_3, Incontro, cronaca

# Il codice con cui la rete di sicurezza chiude un dialogo che Esc non ha chiuso, dopo ATTESA millisecondi.
NON_CHIUSO = 4242
ATTESA = 3000


class Messaggi(list):
    """I messaggi di wx, al posto di wx.MessageBox: le domande rispondono sì."""

    def __call__(self, testo, *args, **kwargs):
        self.append(testo)
        stile = args[1] if len(args) > 1 else kwargs.get("style", 0)
        return wx.YES if stile & wx.YES_NO else wx.OK


class Scena:
    """Il mondo delle prove: la tua polisportiva attiva, una del computer, gli allenatori, un torneo aperto e i modelli."""

    def __init__(self):
        self.mondo = mondo_di_prova(20, 20)
        self.club = polisportiva(self.mondo, "Club Di Prova", cpu=False, cassa=50_000, ids=(1, 2, 21, 3))
        self.cpu = polisportiva(self.mondo, "PoliTeam04", cpu=True, cassa=5000, ids=(4, 5, 22, 6))
        self.mondo.miapolisportiva_attiva = self.club
        rng = random.Random(5)
        for _ in range(4):
            self.mondo._nasce_un_allenatore(OGGI, rng)
        self.mondo.aggiorna_fattori_staff()
        apri(self.mondo, OGGI, "Open maschile del martedì")
        self.gestore = modelli_torneo.GestoreModelli()
        self.gestore.crea_predefiniti()

    def tesserati(self):
        return [self.mondo.giocatori[gid] for gid in (1, 2, 21, 3)]


def _dal_vivo(scena):
    g1, g2 = giocatore(101, 12.0), giocatore(102, 13.0)
    gemello = Incontro(g1, g2, SINGOLARE_3, seme=31, dettaglio=COMPLETO, velocita=4)
    return dal_vivo.FinestraDalVivo(None, gemello, cronaca.nomi_dei_giocatori([g1, g2]), cronaca.NORMALE, 4, cassa=CassaFinta(), orologio=Orologio())


# Come nasce ogni dialogo di gui/ nella rassegna, per nome della classe.
FABBRICHE = {
    "SceltaGiocatore": lambda s: dialoghi.SceltaGiocatore(None, s.mondo),
    "Aspetto": lambda s: dialoghi.Aspetto(None, impostazioni.valide(None)),
    "Conservazione": lambda s: dialoghi.Conservazione(None, s.mondo.conservazione_diari),
    "EffettiSonori": lambda s: dialoghi.EffettiSonori(None, 80),
    "NuovaPolisportiva": lambda s: dialoghi.NuovaPolisportiva(None, s.mondo, proposta="Bologna"),
    "CambiaPolisportiva": lambda s: dialoghi.CambiaPolisportiva(None, s.mondo),
    "PasswordPolisportiva": lambda s: dialoghi.PasswordPolisportiva(None, s.club),
    "ChiediPassword": lambda s: dialoghi.ChiediPassword(None, s.club, "Per chiudere Club Di Prova serve la sua password."),
    "Cifra": lambda s: dialoghi.Cifra(None, "Ingaggio", "Spiegazione.", "&Ingaggio", 500, 1000),
    "PagaArretrati": lambda s: dialoghi.PagaArretrati(None, s.mondo, s.club),
    "Vendite": lambda s: dialoghi.Vendite(None, s.mondo, s.club),
    "SalaAllenamento": lambda s: dialoghi.SalaAllenamento(None, s.mondo, s.club),
    "Contratti": lambda s: dialoghi.Contratti(None, s.mondo, s.club),
    "Staff": lambda s: dialoghi.Staff(None, s.mondo, s.club),
    "OpzioniAmichevole": lambda s: dialoghi.OpzioniAmichevole(None, s.mondo, s.mondo.giocatori[2], s.mondo.giocatori[3]),
    "VelocitaDiGioco": lambda s: dialoghi.VelocitaDiGioco(None, 4),
    "AnnunciDellaCronaca": lambda s: dialoghi.AnnunciDellaCronaca(None, impostazioni.valide(None)),
    "Lettura": lambda s: dialoghi.Lettura(None, "Scheda di prova", "Un testo da leggere."),
    "Caffe": lambda s: dialoghi.Caffe(None, "Offrimi un caffè, se ti va."),
    "Aggiornamento": lambda s: dialoghi.Aggiornamento(None, "1.94.6", "2.0.0", "Note."),
    # Dal 23 ottobre 2026, la cartella del mondo: la domanda col mondo già presente e l'avviso dell'avvio.
    "MondoGiaPresente": lambda s: dialoghi.MondoGiaPresente(None, "Nella cartella c'è già un mondo.", testi.IL_TUO),
    "CartellaAssente": lambda s: dialoghi.CartellaAssente(None, "MESS non trova il mondo."),
    "MondoIllegibile": lambda s: dialoghi.MondoIllegibile(None, "Il salvataggio c'è ma non si può leggere."),
    "ModelloTorneoDialogo": lambda s: gui_editor.ModelloTorneoDialogo(None, s.gestore.modello("modello_1"), formule.leggi()[0], s.gestore),
    "EditorModelli": lambda s: gui_editor.EditorModelli(None, s.gestore),
    "FaseDialogo": lambda s: gui_editor.FaseDialogo(None, {"tipo": formule.GIRONI, "partecipanti": 8, "gironi": 2, "promossi": 2, "finalina": False}, 0, False),
    "EditorFormule": lambda s: gui_editor.EditorFormule(None, s.gestore),
    "FormazioneDialogo": lambda s: gui_sfide.FormazioneDialogo(None, s.mondo, "Rosa di prova", "La rosa.", s.tesserati(), [], lambda ids: None),
    "LanciaSfida": lambda s: gui_sfide.LanciaSfida(None, s.mondo, s.club),
    "SfideInArrivo": lambda s: gui_sfide.SfideInArrivo(None, s.mondo, s.club),
    "StoricoSfide": lambda s: gui_sfide.StoricoSfide(None, s.mondo),
    "CalendarioTornei": lambda s: gui_tornei.CalendarioTornei(None, s.mondo, s.club),
    "PannelloTornei": lambda s: gui_tornei.PannelloTornei(None, s.mondo),
    "AlboDOro": lambda s: gui_tornei.AlboDOro(None, s.mondo),
    "FinestraDalVivo": _dal_vivo,
    # Dal 24 ottobre 2026, la finestra Mercato e ricerca e i suoi dialoghi interni, coi testi da leggere.
    "MercatoERicerca": lambda s: gui_mercato.MercatoERicerca(None, s.mondo, impostazioni.valide(None), "mercato"),
    "SalvaFiltri": lambda s: gui_mercato.SalvaFiltri(None, mercato.filtri_di_ricerca_di_serie(), "Giovani mancini"),
    "RinominaPreset": lambda s: gui_mercato.RinominaPreset(None, mercato.filtri_di_ricerca_di_serie(), mercato.Preset(1, "Giovani mancini", mercato.Filtri())),
    "GestisciPreset": lambda s: gui_mercato.GestisciPreset(None, types.SimpleNamespace(filtri_di_ricerca=mercato.filtri_di_ricerca_di_serie(), impostazioni=None)),
    "PostoDaOffrire": lambda s: gui_mercato.PostoDaOffrire(None, s.mondo, s.club),
    "Condizione": lambda s: gui_mercato.Condizione(None),
    "Avviso": lambda s: gui_mercato.Avviso(None, "Avviso", "Un testo da leggere."),
    "Domanda": lambda s: gui_mercato.Domanda(None, "Domanda", "Una domanda da leggere?"),
}


@pytest.fixture
def scena(app_wx, monkeypatch):
    vieta_la_cassa_vera(monkeypatch)
    monkeypatch.setattr(wx, "MessageBox", Messaggi())
    return Scena()


def _dialoghi_di_gui():
    """I nomi delle classi dei dialoghi di tutti i moduli di gui/, quelli che verranno compresi; senza le basi, che cominciano con il trattino basso."""
    for modulo in pkgutil.iter_modules(gui.__path__):
        importlib.import_module(f"gui.{modulo.name}")
    trovati, da_vedere = set(), [dialoghi._Dialogo]
    while da_vedere:
        for figlio in da_vedere.pop().__subclasses__():
            da_vedere.append(figlio)
            if figlio.__module__.startswith("gui.") and not figlio.__name__.startswith("_"):
                trovati.add(figlio.__name__)
    return trovati


def _apri(dialogo, azione):
    """
    Apre il dialogo con ShowModal e, dentro il suo ciclo, guarda se è massimizzato e fa l'azione.
    Restituisce il codice di chiusura, NON_CHIUSO se l'azione non lo ha chiuso, e se era massimizzato.
    """
    visto = {}

    def dentro():
        visto["massimizzato"] = dialogo.IsMaximized()
        azione(dialogo)

    rete = wx.CallLater(ATTESA, lambda: dialogo.IsModal() and dialogo.EndModal(NON_CHIUSO))
    wx.CallAfter(dentro)
    try:
        codice = dialogo.ShowModal()
    finally:
        rete.Stop()
    return codice, visto.get("massimizzato")


def _esc(dialogo):
    """Esc come lo vede wx: il gancio dei tasti parte dal controllo che ha il fuoco, o dal dialogo, e sale."""
    fuoco = wx.Window.FindFocus()
    bersaglio = fuoco if fuoco is not None and fuoco.GetTopLevelParent() is dialogo else dialogo
    evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
    evento.SetEventObject(bersaglio)
    evento.SetKeyCode(wx.WXK_ESCAPE)
    bersaglio.GetEventHandler().ProcessEvent(evento)


def _premi(pulsante):
    def azione(_dialogo):
        evento = wx.CommandEvent(wx.wxEVT_BUTTON, pulsante.GetId())
        evento.SetEventObject(pulsante)
        pulsante.GetEventHandler().ProcessEvent(evento)

    return azione


def test_la_rassegna_conta_tutti_i_dialoghi():
    # Un dialogo nuovo prende le due regole dalla base, ma la rassegna lo deve aprire per dirlo.
    assert _dialoghi_di_gui() == set(FABBRICHE)


@pytest.mark.parametrize("nome", sorted(FABBRICHE))
def test_ogni_dialogo_si_apre_massimizzato_ed_esc_lo_chiude(scena, suonati, nome):
    dialogo = FABBRICHE[nome](scena)
    try:
        chiudi = dialoghi.pulsante_chiudi(dialogo)
        codice, massimizzato = _apri(dialogo, _esc)
        assert massimizzato, f"{nome} non si apre massimizzato"
        assert codice != NON_CHIUSO, f"{nome}: Esc non lo chiude"
        if isinstance(dialogo, dal_vivo.FinestraDalVivo):
            # La partita dal vivo ha il suo Esc: esce senza svelare il risultato, decisione D30.
            assert chiudi is None and dialogo.uscita == dal_vivo.CON_ESC and codice == wx.ID_CANCEL
        if chiudi is not None:
            assert dialogo.GetEscapeId() == chiudi.GetId()
        else:
            # Senza Chiudi, Esc chiude come Annulla, e mai come una conferma: nella proposta
            # dell'aggiornamento come Non adesso, wx.ID_NO. Dalla terza revisione della tappa 14.
            annulla = wx.ID_NO if isinstance(dialogo, dialoghi.Aggiornamento) else wx.ID_CANCEL
            assert codice == annulla, f"{nome}: Esc chiude con {codice}, non come Annulla"
    finally:
        dialogo.Destroy()
    if chiudi is None:
        return
    # Il pulsante, in un dialogo nuovo come li apre la finestra: wx non riapre lo stesso dialogo una seconda volta.
    dialogo = FABBRICHE[nome](scena)
    try:
        col_pulsante, _massimizzato = _apri(dialogo, _premi(dialoghi.pulsante_chiudi(dialogo)))
        assert col_pulsante == codice, f"{nome}: Esc chiude con {codice}, Chiudi con {col_pulsante}"
    finally:
        dialogo.Destroy()


class ConChiudi(dialoghi._Dialogo):
    """Un dialogo come quelli che verranno: Fai e un Chiudi con l'identificativo dato, che conta le pressioni."""

    def __init__(self, identificativo):
        super().__init__(None, "Prova del Chiudi")
        self.premuto = 0
        _fai, self.pulsante = self.pulsanti((wx.ID_ANY, "&Fai"), (identificativo, "C&hiudi"))
        self.pulsante.Bind(wx.EVT_BUTTON, self.al_chiudi)
        self.completa((300, 200))

    def al_chiudi(self, event=None):
        self.premuto += 1
        self.chiudi(wx.ID_CLOSE)


@pytest.mark.parametrize("identificativo", [wx.ID_CLOSE, wx.ID_ANY])
def test_esc_preme_anche_un_chiudi_che_wx_non_conosce(app_wx, identificativo):
    # Senza la regola della base, Esc su un Chiudi wx.ID_CLOSE, o qualunque, non farebbe niente.
    dialogo = ConChiudi(identificativo)
    try:
        assert dialogo.GetEscapeId() == dialogo.pulsante.GetId()
        codice, massimizzato = _apri(dialogo, _esc)
        assert massimizzato and codice == wx.ID_CLOSE and dialogo.premuto == 1
    finally:
        dialogo.Destroy()


def test_senza_chiudi_esc_resta_quello_di_wx(app_wx):
    # OK e Annulla: Esc vale Annulla, come prima; e un pulsante che si chiama altrimenti non è un Chiudi.
    dialogo = dialoghi.VelocitaDiGioco(None, 4)
    try:
        assert dialoghi.pulsante_chiudi(dialogo) is None and dialogo.GetEscapeId() == wx.ID_ANY
    finally:
        dialogo.Destroy()
