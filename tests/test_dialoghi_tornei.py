"""
Test dei dialoghi dei tornei e delle sfide, tappa 12, passo 3, punti 12.2, 12.3, 12.5 e 12.6 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Sul desktop nascosto del conftest, senza suonare: il registratore tiene i suoni, e i messaggi e le
domande sono sostituiti. Il calendario con l'iscrizione, il ritiro dell'iscrizione col rimborso, i tre
rifiuti col loro suono, la pressione ripetuta ignorata e l'iscrizione a mano senza la regola dei due
mesi; il pannello che scorre tornei, parti, classifiche e incontri, il risultato da ascoltare che si
svela con l'ascolto, la lettura o Mostra il risultato, Mostra tutti i risultati con la domanda, il
conteggio e l'avviso quando non c'è niente, Esc che non svela, il gemello uguale al registrato;
l'albo nel suo dialogo; gli editor con le scelte dei giorni, che rifiutano col motivo e non si
chiudono da soli; il lancio e la risposta alle sfide con la formazione; la casella della sala; la
scheda, l'acciacco nella formazione; le notizie e il suono unico dell'avanzamento.
"""

import datetime
import json

import pytest
import wx
from aiuti_calendario import OGGI, apri, giorno, iscrivi_tutti, mondo_di_prova, polisportiva

import formule
import iscrizioni
import modelli_torneo
import sfide
import suoni
import testi
from gui import dal_vivo, dialoghi
from gui import editor_tornei as gui_editor
from gui import sfide as gui_sfide
from gui import tornei as gui_tornei
from mondo import Mondo
from partita import risultato_della_differita

MARTEDI = OGGI + datetime.timedelta(days=1)


class Messaggi(list):
    """I messaggi e le domande della finestra, al posto di wx.MessageBox: le domande rispondono come dice risposta."""

    def __init__(self):
        super().__init__()
        self.risposta = wx.YES

    def __call__(self, testo, *args, **kwargs):
        self.append(testo)
        stile = args[1] if len(args) > 1 else kwargs.get("style", 0)
        return self.risposta if stile & wx.YES_NO else wx.OK


@pytest.fixture
def messaggi(monkeypatch):
    m = Messaggi()
    monkeypatch.setattr(wx, "MessageBox", m)
    return m


@pytest.fixture
def orologio(monkeypatch):
    """L'orologio dei pulsanti del calendario: avanza di un secondo a ogni lettura, così nessuna pressione è una ripetizione."""
    adesso = [1000.0]

    def leggi():
        adesso[0] += 1.0
        return adesso[0]

    monkeypatch.setattr(gui_tornei.time, "monotonic", leggi)
    return adesso


@pytest.fixture
def calendario(app_wx, messaggi, orologio):
    """Un mondo con la tua polisportiva, due uomini e una donna, e gli Open maschili del martedì e il Gran Premio aperti."""
    mondo = mondo_di_prova(20, 20)
    club = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1, 2, 21))
    apri(mondo, OGGI, "Open maschile del martedì", "Gran Premio maschile")
    dialogo = gui_tornei.CalendarioTornei(None, mondo, club)
    yield mondo, club, dialogo
    dialogo.Destroy()


def _scegli_edizione(dialogo, nome, inizio):
    indice = next(i for i, (tipo, ed) in enumerate(dialogo.voci) if tipo == "aperta" and ed.nome == nome and ed.data_inizio == inizio)
    dialogo.elenco.SetSelection(indice)
    dialogo.aggiorna_atleti()
    return dialogo.voci[indice][1]


def _scegli(elenco, voci, gid):
    elenco.SetSelection(next(i for i, v in enumerate(voci) if (v[0] if isinstance(v, tuple) else v).id == gid))


def test_il_calendario_iscrive_e_toglie_coi_suoni_e_i_rimborsi(calendario, suonati):
    mondo, club, dialogo = calendario
    assert dialogo.info.GetLabel().startswith("Club Di Prova: cassa 1.000 euro")
    assert [v[1].nome for v in dialogo.voci].count("Open maschile del martedì") == 2
    ed = _scegli_edizione(dialogo, "Open maschile del martedì", datetime.date(2026, 10, 6))
    assert dialogo.elenco.GetStringSelection().startswith("Open maschile del martedì, maschile, dal 6 ottobre 2026")
    assert {g.id for g in dialogo.iscrivibili} == {1, 2, 21} and dialogo.iscritti == []
    g = mondo.giocatori[1]
    # A mano la regola dei due mesi non c'è, risposta 2: la data del ritmo lontana non ferma niente.
    g.prossimo_torneo = OGGI + datetime.timedelta(days=200)
    dialogo.aggiorna_atleti()
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 1)
    assert "automatica dal " in dialogo.elenco_iscrivibili.GetStringSelection()
    dialogo.iscrivi()
    assert ed.iscritto(1)["origine"] == iscrizioni.MANO and club.cassa == 1000 - ed.quota
    assert suonati == ["iscrizione_fatta"] and dialogo.fatte[0][0] == "iscritto"
    assert [g.id for g, _o in dialogo.iscritti] == [1] and ", iscritto a mano, " in dialogo.elenco_iscritti.GetString(0)
    # Il ritiro dell'iscrizione rimborsa la quota, nella voce dei rimborsi.
    _scegli(dialogo.elenco_iscritti, dialogo.iscritti, 1)
    dialogo.togli()
    assert ed.iscritto(1) is None and club.cassa == 1000 and club.conti_del_mese["rimborsi"] == ed.quota
    assert suonati == ["iscrizione_fatta", "iscrizione_tolta"]
    assert testi.riepilogo_calendario(club, dialogo.fatte).splitlines()[0] == "Calendario e iscrizioni di Club Di Prova: 1 iscrizione e 1 iscrizione tolta."


def test_la_pressione_ripetuta_si_ignora(calendario, suonati, orologio, monkeypatch):
    _mondo, club, dialogo = calendario
    ed = _scegli_edizione(dialogo, "Open maschile del martedì", datetime.date(2026, 10, 6))
    # Un tasto tenuto giù: due pressioni a un decimo l'una dall'altra.
    tempi = iter([10.0, 10.1, 10.2])
    monkeypatch.setattr(gui_tornei.time, "monotonic", lambda: next(tempi))
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 1)
    dialogo.iscrivi()
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 2)
    dialogo.iscrivi()
    dialogo.iscrivi()
    assert ed.ids() == [1] and suonati == ["iscrizione_fatta"] and club.cassa == 1000 - ed.quota


def test_i_rifiuti_del_calendario_col_loro_suono(calendario, suonati, messaggi):
    _mondo, club, dialogo = calendario
    martedi = _scegli_edizione(dialogo, "Open maschile del martedì", datetime.date(2026, 10, 13))
    # La donna non gioca un open maschile: la sua riga lo dice già, e l'iscrizione la rifiuta.
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 21)
    assert ", non può giocarlo, " in dialogo.elenco_iscrivibili.GetStringSelection()
    dialogo.iscrivi()
    assert suonati[-1] == "iscrizione_non_idoneo" and "è un torneo per altri giocatori" in messaggi[-1]
    # Due tornei negli stessi giorni non si giocano: il martedì 13 dura fino al 15, quando comincia il Gran Premio.
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 2)
    dialogo.iscrivi()
    assert martedi.ids() == [2]
    _scegli_edizione(dialogo, "Gran Premio maschile", datetime.date(2026, 10, 15))
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 2)
    dialogo.iscrivi()
    assert suonati[-1] == "iscrizione_sovrapposta" and "Open maschile del martedì, dal 13 ottobre 2026" in messaggi[-1]
    # La cassa che non basta.
    club.cassa = 5
    _scegli(dialogo.elenco_iscrivibili, dialogo.iscrivibili, 1)
    dialogo.iscrivi()
    assert suonati[-1] == "iscrizione_cassa_insufficiente" and messaggi[-1].startswith("La cassa di Club Di Prova ha 5 euro")
    # Niente scelto, o l'edizione prevista, non iscrive.
    dialogo.scelta.SetSelection(1)
    dialogo.aggiorna(0)
    voce = dialogo.voci[0]
    assert voce[0] in ("aperta", "prevista")
    prevista = next(i for i, v in enumerate(dialogo.voci) if v[0] == "prevista")
    dialogo.elenco.SetSelection(prevista)
    dialogo.aggiorna_atleti()
    assert dialogo.elenco_iscrivibili.GetString(0).startswith("Le iscrizioni di questa edizione si aprono il ")
    dialogo.iscrivi()
    assert suonati[-1] == "campo_da_correggere" and messaggi[-1].startswith("Le iscrizioni di questa edizione si aprono il ")


def test_le_edizioni_in_corso_portano_al_pannello(calendario):
    mondo, _club, dialogo = calendario
    ed = _scegli_edizione(dialogo, "Open maschile del martedì", datetime.date(2026, 10, 6))
    iscrivi_tutti(ed, mondo, range(1, 13))
    giorno(mondo, MARTEDI)
    dialogo.scelta.SetSelection(2)
    dialogo.aggiorna(0)
    assert dialogo.voci and dialogo.voci[0][0] == "in_corso"
    assert dialogo.elenco.GetString(0).startswith("Open maschile del martedì, maschile, dal 6 ottobre 2026: in corso in 1 sede, 2 tuoi atleti.")
    dialogo.al_pannello()
    assert dialogo.pannello_chiesto == mondo.calendario.tornei[0].id


# Il pannello.

@pytest.fixture
def pannello(app_wx, messaggi):
    """Un Open maschile del martedì da 12, con due tuoi tesserati, dopo la prima giornata, e il suo pannello."""
    mondo = mondo_di_prova(12, 0)
    polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1, 2))
    edizioni = apri(mondo, OGGI, "Open maschile del martedì")
    iscrivi_tutti(edizioni[0], mondo, range(1, 13))
    giorno(mondo, MARTEDI)
    dialogo = gui_tornei.PannelloTornei(None, mondo, {"velocita_gioco": 4})
    yield mondo, dialogo
    dialogo.Destroy()


def _parte(dialogo, testo):
    dialogo.elenco_parti.SetSelection(next(i for i, (t, _k) in enumerate(dialogo.parti) if t == testo))
    dialogo.alla_parte((0, 0))


def _da_ascoltare(dialogo):
    return next(i for i, incontro in enumerate(dialogo.incontri) if incontro.differita and not incontro.svelato)


def test_il_pannello_scorre_tornei_parti_classifiche_e_incontri(pannello):
    mondo, dialogo = pannello
    torneo = mondo.calendario.tornei[0]
    assert dialogo.scelta.GetSelection() == 0 and dialogo.mostrati == [torneo]
    assert dialogo.info.GetLabel() == "Tornei in corso: 1, 1 con i tuoi atleti. Conclusi negli ultimi 14 giorni: 0."
    assert dialogo.elenco_tornei.GetString(0).endswith("; 2 tuoi atleti.")
    parti = [t for t, _k in dialogo.parti]
    assert parti[:2] == ["Classifica generale", "I tuoi incontri"] and any(p.startswith("Girone ") for p in parti)
    assert all(riga.endswith(", in gara") or ", fuori " in riga for riga in [dialogo.elenco_classifica.GetString(i) for i in range(dialogo.elenco_classifica.GetCount())])
    _parte(dialogo, "Girone A")
    assert dialogo.elenco_classifica.GetString(0).startswith("1. ") and ", set " in dialogo.elenco_classifica.GetString(0)
    assert len(dialogo.righe_classifica) == dialogo.elenco_classifica.GetCount()
    _parte(dialogo, "I tuoi incontri")
    assert dialogo.incontri and all(i.a in (1, 2) or i.b in (1, 2) for i in dialogo.incontri)
    assert any(dialogo.elenco_incontri.GetString(i).endswith(", tuo, giocato, da ascoltare.") for i in range(dialogo.elenco_incontri.GetCount()))
    # Tutti i tornei in corso, e i conclusi, che ancora non ci sono.
    dialogo.scelta.SetSelection(3)
    dialogo.aggiorna(0)
    assert dialogo.mostrati == [] and dialogo.elenco_tornei.GetString(0) == "Nessun torneo concluso negli ultimi 14 giorni."


def test_mostra_il_risultato_lo_svela(pannello, suonati, messaggi):
    _mondo, dialogo = pannello
    _parte(dialogo, "I tuoi incontri")
    indice = _da_ascoltare(dialogo)
    incontro = dialogo.incontri[indice]
    dialogo.elenco_incontri.SetSelection(indice)
    dialogo.mostra_risultato()
    assert incontro.svelato and dialogo.svelati == 1 and suonati[-1] == "risultato_svelato"
    assert "da ascoltare" not in dialogo.elenco_incontri.GetString(indice) and dialogo.elenco_incontri.GetSelection() == indice
    # Una seconda volta non c'è più niente di nascosto.
    dialogo.mostra_risultato()
    assert suonati[-1] == "nessun_risultato_da_svelare" and messaggi[-1].startswith("Il risultato di questo incontro non è nascosto")


def test_mostra_tutti_i_risultati_chiede_e_conta(pannello, suonati, messaggi):
    mondo, dialogo = pannello
    quanti = len(mondo.calendario.da_svelare())
    assert quanti >= 2
    # Al no non cambia niente.
    messaggi.risposta = wx.NO
    dialogo.mostra_tutti()
    assert messaggi[-1] == f"Mostrare i risultati dei {quanti} incontri dei tuoi ancora da ascoltare? Non si torna indietro."
    assert len(mondo.calendario.da_svelare()) == quanti and suonati[-2:] == ["domanda", "annullato"]
    messaggi.risposta = wx.YES
    dialogo.mostra_tutti()
    assert not mondo.calendario.da_svelare() and dialogo.svelati == quanti
    assert suonati[-1] == "risultati_svelati_tutti" and messaggi[-1] == f"Mostrati i risultati di {quanti} incontri."
    # Senza niente da svelare avvisa col suo suono, e non chiede niente.
    dialogo.mostra_tutti()
    assert suonati[-1] == "nessun_risultato_da_svelare" and messaggi[-1].startswith("Non ci sono incontri dei tuoi ancora da ascoltare")


def _uscita(monkeypatch, uscita):
    def mostra(self):
        self.uscita = uscita
        return wx.ID_OK

    monkeypatch.setattr(dal_vivo.FinestraDalVivo, "ShowModal", mostra)


def test_l_ascolto_in_differita_svela_e_esc_no(pannello, suonati, monkeypatch):
    _mondo, dialogo = pannello
    _parte(dialogo, "I tuoi incontri")
    indice = _da_ascoltare(dialogo)
    incontro = dialogo.incontri[indice]
    dialogo.elenco_incontri.SetSelection(indice)
    _uscita(monkeypatch, dal_vivo.CON_ESC)
    dialogo.ascolta()
    assert not incontro.svelato and dialogo.ultimo is None and suonati[-2:] == ["differita_al_via", "annullato"]
    _uscita(monkeypatch, dal_vivo.AL_RISULTATO)
    dialogo.elenco_incontri.SetSelection(indice)
    dialogo.ascolta()
    assert incontro.svelato and suonati[-2:] == ["differita_al_via", "risultato_svelato"]
    ultimo = dialogo.ultimo
    assert ultimo.tipo == "torneo" and ultimo.risultato.momenti and ultimo.data_simulata.date() == MARTEDI.date()
    # Il gemello rifatto dalla differita dà il risultato registrato.
    assert [list(s) for s in ultimo.risultato.set] == incontro.set


def test_la_cronaca_da_leggere_svela(pannello, suonati, monkeypatch):
    _mondo, dialogo = pannello
    letti = []
    vero = dialoghi.Lettura.__init__

    def registra(self, genitore, titolo, testo, *args, **kwargs):
        letti.append((titolo, testo))
        vero(self, genitore, titolo, testo, *args, **kwargs)

    monkeypatch.setattr(dialoghi.Lettura, "__init__", registra)
    monkeypatch.setattr(dialoghi.Lettura, "ShowModal", lambda self: wx.ID_OK)
    _parte(dialogo, "I tuoi incontri")
    indice = _da_ascoltare(dialogo)
    incontro = dialogo.incontri[indice]
    dialogo.elenco_incontri.SetSelection(indice)
    dialogo.leggi()
    assert incontro.svelato and suonati[-1] == "cronaca_torneo_letta"
    titolo, testo = letti[-1]
    nomi = dialogo.ultimo.nomi
    assert titolo == f"Cronaca di {nomi['A'].testo} contro {nomi['B'].testo}" and "Fine dell'incontro: vince " in testo and "\n\n" not in testo


def test_gli_incontri_degli_altri_non_si_ascoltano(pannello, suonati, messaggi):
    _mondo, dialogo = pannello
    _parte(dialogo, "Classifica generale")
    altro = next(i for i, incontro in enumerate(dialogo.incontri) if incontro.giocato and not incontro.differita)
    dialogo.elenco_incontri.SetSelection(altro)
    dialogo.ascolta()
    assert suonati[-1] == "nessuna_differita" and messaggi[-1].startswith("Questo incontro non si può ascoltare")
    dialogo.leggi()
    assert suonati[-1] == "nessuna_differita"


def test_il_gemello_di_ogni_incontro_dei_tuoi_e_il_registrato(pannello):
    mondo, _dialogo = pannello
    for incontro in mondo.calendario.tornei[0].incontri():
        if incontro.differita:
            risultato, _nomi = risultato_della_differita(incontro.differita, incontro.seme)
            assert [list(s) for s in risultato.set] == incontro.set and risultato.esito == incontro.esito


def test_la_scheda_dal_pannello(pannello, suonati, monkeypatch):
    _mondo, dialogo = pannello
    monkeypatch.setattr(dialoghi.Lettura, "ShowModal", lambda self: wx.ID_OK)
    _parte(dialogo, "Girone A")
    dialogo.elenco_classifica.SetSelection(0)
    dialogo.scheda()
    assert suonati[-1] == "mercato_scheda_giocatore"


# L'albo d'oro.

def test_l_albo_d_oro_per_modello_e_per_anno(app_wx):
    mondo = mondo_di_prova(12, 0)
    polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1, 2))
    edizioni = apri(mondo, OGGI, "Open maschile del martedì")
    iscrivi_tutti(edizioni[0], mondo, range(1, 13))
    data = MARTEDI
    while not mondo.calendario.conclusi:
        giorno(mondo, data)
        data += datetime.timedelta(days=1)
    dialogo = gui_tornei.AlboDOro(None, mondo)
    try:
        assert dialogo.scelta_modello.GetString(0) == "Open maschile del martedì" and dialogo.anni == [2026]
        assert dialogo.elenco_edizioni.GetString(0) == "Edizione 1, 6 ottobre 2026: 1 sede, 12 iscritti."
        podio = dialogo.elenco_podi.GetString(0)
        assert podio.startswith("Sede 1, 6 ottobre 2026, 12 iscritti: oro ") and "; legno " in podio
        dialogo.scelta_mostra.SetSelection(1)
        dialogo.all_anno()
        tuoi_sul_podio = any(posto[0] in (1, 2) for posto in mondo.calendario.albo.voci[0][8])
        assert (dialogo.elenco_edizioni.GetCount() == 1 and bool(dialogo.edizioni)) == tuoi_sul_podio
    finally:
        dialogo.Destroy()


# Gli editor.

@pytest.fixture
def gestore(app_wx):
    g = modelli_torneo.GestoreModelli()
    g.crea_predefiniti()
    return g


def test_l_editor_dei_modelli_crea_duplica_ed_elimina(gestore, suonati, messaggi, monkeypatch):
    editor = gui_editor.EditorModelli(None, gestore)
    try:
        assert len(editor.modelli) == 10 and editor.elenco.GetString(0).endswith(", attivo")

        def compila(self):
            # Senza nome il modello non va: l'avviso dice il motivo, e il dialogo resta aperto.
            self.conferma()
            assert self.risultato is None and messaggi[-1].startswith("Il nome deve avere da 3 a 60 caratteri")
            self.nome.ChangeValue("Torneo di prova")
            self.ricorrenza.SetSelection(1)
            self.alla_ricorrenza()
            assert self.giorno.GetCount() == 28 and not self.mese.IsEnabled()
            self.ricorrenza.SetSelection(0)
            self.alla_ricorrenza()
            assert [self.giorno.GetString(i) for i in range(7)][:2] == ["lunedì", "martedì"]
            self.giorno.SetSelection(2)
            self.ricorrenza.SetSelection(2)
            self.alla_ricorrenza()
            assert self.mese.IsEnabled()
            self.ricorrenza.SetSelection(0)
            self.alla_ricorrenza()
            self.giorno.SetSelection(2)
            self.aggiorna()
            assert self.riepilogo.GetValue().startswith("Formula Gironi da 4 e tabellone da 16")
            assert "al primo va il " in self.riepilogo.GetValue() and "denaro nuovo" in self.riepilogo.GetValue()
            self.conferma()
            return wx.ID_OK

        monkeypatch.setattr(gui_editor.ModelloTorneoDialogo, "ShowModal", compila)
        editor.nuovo()
        nuovo = next(m for m in gestore.modelli()[0] if m.nome == "Torneo di prova")
        assert nuovo.ricorrenza == {"tipo": "settimanale", "giorno": 2}
        assert suonati[-3:] == ["dialogo_modello_torneo", "campo_da_correggere", "modello_salvato"]
        assert editor.esiti[-1].startswith("Nuovo modello: Torneo di prova, aperto a tutti, ogni mercoledì, attivo")
        editor.elenco.SetSelection(next(i for i, m in enumerate(editor.modelli) if m.id == nuovo.id))
        editor.duplica()
        assert suonati[-1] == "modello_duplicato" and any(m.nome == "Copia di Torneo di prova" for m in gestore.modelli()[0])
        editor.elenco.SetSelection(next(i for i, m in enumerate(editor.modelli) if m.nome == "Copia di Torneo di prova"))
        editor.elimina()
        assert suonati[-1] == "modello_eliminato" and not any(m.nome == "Copia di Torneo di prova" for m in gestore.modelli()[0])
        # Modificare un modello senza toccare la percentuale non cambia la pendenza dei premi.
        open_martedi = next(m for m in gestore.modelli()[0] if m.nome == "Open maschile del martedì")
        monkeypatch.setattr(gui_editor.ModelloTorneoDialogo, "ShowModal", lambda self: (self.conferma(), wx.ID_OK)[1])
        editor.elenco.SetSelection(next(i for i, m in enumerate(editor.modelli) if m.id == open_martedi.id))
        editor.modifica()
        assert gestore.modello(open_martedi.id) == open_martedi
    finally:
        editor.Destroy()


def test_l_editor_dei_modelli_dice_i_file_illeggibili(gestore, suonati):
    with open(f"{gestore.cartella()}/Rotto.json", "w", encoding="utf-8") as f:
        f.write("{ non è json")
    gestore.azzera_cache()
    editor = gui_editor.EditorModelli(None, gestore)
    try:
        assert "Il calendario dei tornei ha 1 problema: Il modello nel file Rotto.json è scartato" in editor.info.GetLabel()
        assert suonati == ["calendario_illeggibile"]
    finally:
        editor.Destroy()


def _fase(self, tipo, partecipanti=None, gironi=1, promossi=0, finalina=False):
    self.tipo.SetSelection(0 if tipo == formule.GIRONI else 1)
    if partecipanti is not None and self.partecipanti.IsEnabled():
        self.partecipanti.SetValue(partecipanti)
    self.gironi.SetValue(gironi)
    self.promossi.SetValue(promossi)
    self.finalina.SetValue(finalina)
    self.aggiorna()
    self.conferma()
    return wx.ID_OK if self.risultato is not None else wx.ID_CANCEL


def test_l_editor_delle_formule(gestore, suonati, messaggi, monkeypatch, cartella_di_prova):
    editor = gui_editor.EditorFormule(None, gestore)
    try:
        assert len(editor.formule) == 5 and editor.stato.GetValue() == "Formula valida."
        editor.nuova()
        assert suonati[-1] == "formula_nuova" and editor.stato.GetValue() == "Formula valida. Non è ancora salvata."
        editor.nome.SetValue("Gironi da 4 e semifinali")
        # La fase sola, un girone unico, non promuove nessuno: prima si cambia.
        editor.aggiungi_fase()
        assert suonati[-1] == "formula_non_valida" and messaggi[-1].startswith("La fase prima non promuove abbastanza giocatori")
        monkeypatch.setattr(gui_editor.FaseDialogo, "ShowModal", lambda self: _fase(self, formule.GIRONI, 8, gironi=2, promossi=2))
        editor.fasi.SetSelection(0)
        editor.modifica_fase()
        assert suonati[-2:] == ["dialogo_fase", "fase_modificata"]
        assert editor.fasi.GetString(0) == "Fase 1: gironi, 8 partecipanti in 2 gironi da 4, passano 2 per girone"
        assert editor.stato.GetValue().startswith("Formula non valida: L'ultima fase dev'essere la finale")
        # Salvare una formula che non va avvisa e non scrive niente.
        editor.salva()
        assert suonati[-1] == "formula_non_valida"
        # Le fasi del tabellone: i partecipanti arrivano dalla fase prima, bloccati.
        monkeypatch.setattr(gui_editor.FaseDialogo, "ShowModal", lambda self: _fase(self, formule.TABELLONE, finalina=True))
        editor.aggiungi_fase()
        monkeypatch.setattr(gui_editor.FaseDialogo, "ShowModal", lambda self: _fase(self, formule.TABELLONE))
        editor.aggiungi_fase()
        assert suonati[-1] == "fase_aggiunta" and editor.fasi.GetCount() == 3
        assert editor.fasi.GetString(1) == "Fase 2: tabellone da 4, con la finalina per il terzo posto"
        assert editor.stato.GetValue() == "Formula valida. Non è ancora salvata."
        editor.salva()
        assert suonati[-1] == "formula_salvata" and editor.stato.GetValue() == "Formula valida."
        scritte = json.loads((cartella_di_prova / formule.NOME_FILE).read_text(encoding="utf-8"))["formule"]
        assert any(f["nome"] == "Gironi da 4 e semifinali" and len(f["fasi"]) == 3 for f in scritte)
        # Una fase tolta, e la formula usata che non si elimina.
        editor.fasi.SetSelection(2)
        editor.togli_fase()
        assert suonati[-1] == "fase_tolta" and editor.fasi.GetCount() == 2
        editor.scelta.SetSelection(next(i for i, f in enumerate(editor.formule) if f["id"] == "gironi_32"))
        editor.alla_formula()
        editor.elimina()
        assert suonati[-1] == "formula_in_uso" and "Open maschile del martedì" in messaggi[-1]
        # Chiudere con una formula cambiata e non salvata chiede, col no già scelto.
        messaggi.risposta = wx.NO
        editor.chiudi_editor()
        assert editor.GetReturnCode() != wx.ID_CANCEL and suonati[-1] == "annullato"
    finally:
        editor.Destroy()


# Le sfide.

@pytest.fixture
def sfidanti(app_wx, messaggi):
    """La tua polisportiva e una del computer, ciascuna con due uomini e una donna, più una riserva."""
    mondo = mondo_di_prova(10, 10)
    club = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1, 2, 11, 3))
    cpu = polisportiva(mondo, "PoliTeam04", cpu=True, cassa=5000, ids=(4, 5, 12, 6))
    return mondo, club, cpu


def test_il_lancio_di_una_sfida_con_la_formazione(sfidanti, suonati, messaggi):
    mondo, club, _cpu = sfidanti
    dialogo = gui_sfide.LanciaSfida(None, mondo, club)
    try:
        assert dialogo.info.GetLabel().startswith("Club Di Prova: 2 sfide da lanciare questo mese.")
        assert dialogo.elenco.GetString(0).startswith("PoliTeam04, forza ")
        assert dialogo.formazione.problema() is None and dialogo.formazione.stato.GetValue().startswith("Formazione valida: al tavolo ")
        # Tre titolari dello stesso sesso non vanno: lo stato lo dice, col suono, e il lancio avvisa.
        uomini = [i for i, g in enumerate(dialogo.formazione.convocabili) if g.sesso == "m"]
        for posto, indice in enumerate(uomini[:3]):
            dialogo.formazione.scelte[posto].SetSelection(indice)
        for scelta in dialogo.formazione.scelte[3:]:
            scelta.SetSelection(0)
        dialogo.formazione.al_cambio()
        assert dialogo.formazione.stato.GetValue() == "Formazione non valida: Al tavolo servono due giocatori di un sesso e uno dell'altro."
        assert suonati[-1] == "formazione_non_valida"
        dialogo.lancia()
        assert suonati[-1] == "formazione_non_valida" and messaggi[-1] == "Al tavolo servono due giocatori di un sesso e uno dell'altro."
        dialogo.formazione.riempi(dialogo.formazione.convocabili, sfide.proposta(mondo, club))
        dialogo.lancia()
        s = (mondo.sfide.attive or mondo.sfide.storico)[-1]
        atteso = "sfida_accettata_dall_avversario" if s.stato == sfide.ACCETTATA else "sfida_rifiutata_dall_avversario"
        assert suonati[-1] == atteso and dialogo.esiti and messaggi[-1] == dialogo.esiti[-1]
        assert messaggi[-1].startswith("PoliTeam04 accetta: si gioca domani, con ") or messaggi[-1].startswith("PoliTeam04 rifiuta: ")
    finally:
        dialogo.Destroy()


def test_le_sfide_in_arrivo_si_accettano_o_si_rifiutano(sfidanti, suonati, messaggi):
    mondo, club, cpu = sfidanti
    oggi = mondo.datetime_corrente_simulazione.date()
    rapporto = Mondo.rapporto_vuoto(oggi)
    convocati = sfide.convoca(mondo, cpu, oggi + datetime.timedelta(days=1))
    sfide._proponi(mondo, cpu, club, convocati, oggi, rapporto)
    dialogo = gui_sfide.SfideInArrivo(None, mondo, club)
    try:
        assert dialogo.elenco.GetString(0).startswith("PoliTeam04 sfida Club Di Prova, forza ") and "; rispondi entro il " in dialogo.elenco.GetString(0)
        dialogo.accetta()
        assert suonati[-1] == "sfida_accettata" and mondo.sfide.attive[0].stato == sfide.ACCETTATA
        assert messaggi[-1].startswith("Sfida accettata: si gioca domani contro PoliTeam04, con ")
        assert dialogo.elenco.GetString(0) == "Nessuna sfida aspetta la tua risposta."
        dialogo.accetta()
        assert suonati[-1] == "nessuna_selezione"
    finally:
        dialogo.Destroy()
    sfide._proponi(mondo, cpu, club, convocati, oggi, rapporto)
    dialogo = gui_sfide.SfideInArrivo(None, mondo, club)
    try:
        dialogo.rifiuta()
        assert suonati[-1] == "sfida_rifiutata" and messaggi[-1] == "Sfida di PoliTeam04 rifiutata."
    finally:
        dialogo.Destroy()


def test_con_meno_di_tre_convocabili_la_formazione_lo_dice(sfidanti, suonati, messaggi):
    # Dalla prova della finestra vera: con due soli tesserati liberi il lancio non mostra un doppione, ma il perché.
    mondo, club, _cpu = sfidanti
    for gid in (2, 3):
        mondo._lascia(club, mondo.giocatori[gid])
    dialogo = gui_sfide.LanciaSfida(None, mondo, club)
    try:
        scelte = [s.GetSelection() for s in dialogo.formazione.scelte[:3]]
        assert scelte == [0, 1, wx.NOT_FOUND]
        atteso = "Quel giorno soltanto 2 tesserati possono giocare, senza altri impegni: per una squadra ne servono tre, due di un sesso e uno dell'altro."
        assert dialogo.formazione.stato.GetValue() == f"Formazione non valida: {atteso}"
        dialogo.lancia()
        assert suonati[-1] == "formazione_non_valida" and messaggi[-1] == atteso
    finally:
        dialogo.Destroy()


def test_il_riepilogo_dice_le_sfide_decadute():
    rapporto = Mondo.rapporto_vuoto(OGGI) | {"ticks": 3, "giorni": 3, "sfide_decadute": 2,
                                             "notizie": ["PoliTeam04 sfida Club Di Prova, il 5 ottobre 2026: si risponde entro il 6 ottobre 2026."]}
    testo = testi.riepilogo_avanzamento(rapporto)
    assert "PoliTeam04 sfida Club Di Prova, il 5 ottobre 2026: si risponde entro il 6 ottobre 2026. 2 sfide alle tue polisportive sono decadute senza risposta." in testo
    assert "entro domani" not in testo


def test_la_formazione_dice_l_acciacco(sfidanti):
    mondo, _club, _cpu = sfidanti
    g = mondo.giocatori[1]
    oggi = mondo.datetime_corrente_simulazione
    g.acciacco_fino, g.acciacco_calo, g.acciacco_giorni, g.acciacco_sede = oggi + datetime.timedelta(days=3), 0.02, 4, "caviglia"
    assert testi.riga_convocabile(g, mondo).endswith(", uomo, acciaccato")
    assert testi.acciacco(g, oggi) == f"acciaccato alla caviglia fino al {testi.data_breve(g.acciacco_fino)}: rende un poco meno"
    assert ", acciaccato alla caviglia fino al " in testi.riga_allenando(g, mondo)
    scheda = testi.scheda_giocatore(g, mondo)
    # Con 3 giorni rimasti su 4 il calo di oggi è tre quarti di quello del primo giorno.
    assert "Acciaccato alla caviglia fino al " in scheda and ": rende un poco meno, oggi il 1,5 per cento" in scheda


# La sala allenamento.

def test_la_casella_dell_iscrizione_automatica(sfidanti, suonati):
    mondo, club, _cpu = sfidanti
    sala = dialoghi.SalaAllenamento(None, mondo, club)
    try:
        g = sala.allenandi[0]
        assert sala.automatica.GetValue() and sala.automatica.GetLabel() == "Iscrizione a&utomatica ai tornei"
        sala.automatica.SetValue(False)
        sala.all_automatica()
        assert not g.iscrizione_automatica and suonati[-1] == "iscrizione_automatica_spenta"
        assert sala.cambi() == [testi.cambio_in_sala(g)] and sala.cambi()[0].endswith(", iscrizione automatica ai tornei spenta.")
        sala.automatica.SetValue(True)
        sala.all_automatica()
        assert g.iscrizione_automatica and suonati[-1] == "iscrizione_automatica_accesa" and sala.cambi() == []
    finally:
        sala.Destroy()


# La scheda e le notizie.

def test_la_scheda_ha_i_tornei_e_il_palmares(sfidanti):
    mondo, club, _cpu = sfidanti
    g = mondo.giocatori[1]
    g.prossimo_torneo = datetime.datetime(2026, 12, 18, 9, 0)
    scheda = testi.scheda_giocatore(g, mondo)
    assert "[TORNEI E PALMARÈS]" in scheda and "Tornei giocati: 0 | Medaglie: nessuna | Gare a squadre: 0 vinte, 0 perse" in scheda
    assert "Classifica mondiale maschile: 0,0 punti, non ancora in classifica" in scheda
    assert "Iscrizione automatica ai tornei: accesa, dal 18 dicembre 2026." in scheda
    g.iscrizione_automatica = False
    assert "Iscrizione automatica ai tornei: spenta, si iscrive a mano dal calendario." in testi.scheda_giocatore(g, mondo)
    altro = mondo.giocatori[4]
    altro.prossimo_torneo = None
    assert "Ritmo dei tornei: può iscriversi al primo torneo utile." in testi.scheda_giocatore(altro, mondo)
    poli = testi.scheda_polisportiva(club, mondo)
    assert "Palmarès degli ultimi cinque anni" in poli and "Sfide: 0 vinte e 0 perse | Sfide da lanciare: 2" in poli


def _rapporto(**voci):
    return Mondo.rapporto_vuoto(OGGI) | {"ticks": 1, "giorni": 1} | voci


def test_l_ordine_delle_notizie_dei_tornei_e_delle_sfide():
    tutto = _rapporto(tuoi_non_pagati=1, calendario_con_problemi=1, sfide_in_attesa=1, tuoi_titoli_mondiali=1, tue_medaglie_oro=2, tue_coppe_oro=1,
                      tue_medaglie_argento=1, tue_medaglie_bronzo=1, tue_medaglie_legno=1, tue_coppe_argento=1, tue_coppe_bronzo=1, tue_coppe_legno=1,
                      tue_sfide_vinte=1, tue_sfide_perse=1, tue_sfide_a_tavolino=1, tuoi_qualificati=3, tue_qualificazioni_coppa=1, tue_iscrizioni_saltate=2,
                      tuoi_venduti=1, tuoi_infortuni_in_gara=1, tuoi_tavolini=1, tuoi_acciacchi=2, tuoi_tornei_conclusi=1, tue_iscrizioni=3, sfide_decadute=1,
                      tue_edizioni_annullate=1, mesi=1, mondiali_conclusi=1)
    attesi = [
        ("tuoi_non_pagati", "stipendi_non_pagati", "stipendi non pagati, vedi il bilancio"),
        ("calendario_con_problemi", "calendario_illeggibile", "calendario dei tornei con problemi"),
        ("sfide_in_attesa", "sfida_ricevuta", "sfida da PoliTeam04, rispondi oggi"),
        ("tuoi_titoli_mondiali", "tuo_titolo_mondiale", "tuo atleta campione del mondo"),
        ("tue_medaglie_oro", "tua_medaglia_oro", "2 medaglie d'oro per i tuoi"),
        ("tue_coppe_oro", "tua_coppa_oro", "coppa d'oro per la tua polisportiva"),
        ("tue_medaglie_argento", "tua_medaglia_argento", "1 medaglia d'argento per i tuoi"),
        ("tue_medaglie_bronzo", "tua_medaglia_bronzo", "1 medaglia di bronzo per i tuoi"),
        ("tue_medaglie_legno", "tua_medaglia_legno", "1 medaglia di legno per i tuoi"),
        ("tue_coppe_argento", "tua_coppa_argento", "coppa d'argento per la tua polisportiva"),
        ("tue_coppe_bronzo", "tua_coppa_bronzo", "coppa di bronzo per la tua polisportiva"),
        ("tue_coppe_legno", "tua_coppa_legno", "coppa di legno per la tua polisportiva"),
        ("tue_sfide_vinte", "tua_sfida_vinta", "1 sfida vinta"),
        ("tue_sfide_perse", "tua_sfida_persa", "1 sfida persa"),
        ("tue_sfide_a_tavolino", "tua_sfida_a_tavolino", "1 sfida persa a tavolino"),
        ("tuoi_qualificati", "tuoi_qualificati_mondiale", "3 tuoi atleti convocati al mondiale"),
        ("tue_qualificazioni_coppa", "tua_qualificazione_coppa", "tua polisportiva qualificata alla coppa"),
        ("tue_iscrizioni_saltate", "tue_iscrizioni_saltate", "2 iscrizioni saltate per la cassa"),
        ("tuoi_venduti", "tuo_tesserato_venduto", "1 tuo giocatore venduto"),
        ("tuoi_infortuni_in_gara", "tuo_infortunio_in_gara", "1 tuo atleta infortunato in gara"),
        ("tuoi_tavolini", "tuo_tavolino", "1 tuo atleta perde a tavolino"),
        ("tuoi_acciacchi", "tuo_acciacco", "2 tuoi atleti acciaccati in gara"),
        ("tuoi_tornei_conclusi", "tuo_torneo_concluso", "1 torneo dei tuoi concluso"),
        ("tue_iscrizioni", "tue_iscrizioni_automatiche", "3 iscrizioni automatiche dei tuoi"),
        ("sfide_decadute", "sfida_decaduta", "1 sfida decaduta senza risposta"),
        ("tue_edizioni_annullate", "edizione_annullata", "1 torneo dei tuoi annullato"),
        ("mesi", "primo_del_mese", "primo del mese, stipendi pagati"),
        ("mondiali_conclusi", "mondiale_concluso", "campionato mondiale concluso"),
    ]
    for chiave, evento, testo in attesi:
        assert suoni.evento_avanzamento(tutto, True, True, "PoliTeam04") == (evento, testo), chiave
        tutto[chiave] = 0
    assert suoni.evento_avanzamento(tutto, True, True) == ("mondo_avanzato", "mondo avanzato di un giorno")


def test_la_sfida_in_attesa_e_quella_decaduta_nella_barra():
    # Il nome di chi sfida, se ci sta nei quaranta caratteri; altrimenti la forma corta.
    assert suoni.evento_avanzamento(_rapporto(sfide_in_attesa=1), True, True, "Polisportiva Dal Nome Lunghissimo Di Prova")[1] == "sfida ricevuta, rispondi oggi"
    assert suoni.evento_avanzamento(_rapporto(sfide_in_attesa=2), True, True, "PoliTeam04")[1] == "2 sfide da rispondere oggi"
    # Una sfida arrivata e decaduta durante un recupero di più giorni non dice rispondi oggi.
    recupero = _rapporto(ticks=3, giorni=3, sfide_ricevute=1, sfide_decadute=1, sfide_in_attesa=0)
    assert suoni.evento_avanzamento(recupero, True, True, None) == ("sfida_decaduta", "1 sfida decaduta senza risposta")


def test_ogni_notizia_nuova_sta_nella_barra():
    chiavi = ("calendario_con_problemi", "sfide_in_attesa", "tuoi_titoli_mondiali", "tue_medaglie_oro", "tue_coppe_oro", "tue_medaglie_argento",
              "tue_medaglie_bronzo", "tue_medaglie_legno", "tue_coppe_argento", "tue_coppe_bronzo", "tue_coppe_legno", "tue_sfide_vinte", "tue_sfide_perse",
              "tue_sfide_a_tavolino", "tuoi_qualificati", "tue_qualificazioni_coppa", "tue_iscrizioni_saltate", "tuoi_infortuni_in_gara", "tuoi_tavolini",
              "tuoi_acciacchi", "tuoi_tornei_conclusi", "tue_iscrizioni", "sfide_decadute", "tue_edizioni_annullate", "mondiali_conclusi")
    for chiave in chiavi:
        for quanti in (1, 999):
            evento, testo = suoni.evento_avanzamento(_rapporto(**{chiave: quanti}), True, True, "PoliTeam04")
            assert evento in suoni.EVENTI and len(testo) <= 40, testo
