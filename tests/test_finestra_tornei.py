"""
Test della finestra principale coi tornei e le sfide, tappa 12, passo 3, punti 12.1, 12.8, 12.10 e
12.11 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Sul desktop nascosto del conftest, senza suonare e senza finestre modali vere: il menu Tornei e le voci
nuove del menu Partite nella guida; il calendario, il pannello, la classifica mondiale, gli editor e il
ripristino dalla finestra, con la vista che dice che cosa è cambiato e il mondo che si salva; Salva la
cronaca dell'ultimo incontro di torneo o di sfida ascoltato in differita; il calendario che non si legge
all'avvio e nella barra una volta sola; la sfida in attesa col nome di chi sfida; il suono unico
dell'avanzamento con le notizie dei tornei.
Dal 2026-10-24, col collaudo di gioco, il ripristino fermo a metà, che nel messaggio nomina la cartella dei file già messi da parte.
Con le verifiche li chiama file, perché fermo fra i modelli non ci sono le formule.
Dal passo della finestra Mercato e ricerca, lo stesso giorno, la pressione ripetuta la guarda la base dei dialoghi, e l'orologio delle prove è il suo.
"""

import datetime

import pytest
import wx
from aiuti_barra import evento_della_barra
from aiuti_calendario import OGGI, apri, giorno, iscrivi_tutti, mondo_di_prova, polisportiva

import archivio
import formule
import modelli_torneo
import sfide
import suoni
import testi
from costanti import FILE_MONDO
from gui import dal_vivo, dialoghi
from gui import editor_tornei as gui_editor
from gui import sfide as gui_sfide
from gui import tornei as gui_tornei
from gui.finestra import FinestraPrincipale
from mondo import Mondo
from motore.cronaca import CARTELLA_CRONACHE
from utilita import adesso, adesso_utc

MARTEDI = OGGI + datetime.timedelta(days=1)


class Messaggi(list):
    """I messaggi e le domande, al posto di wx.MessageBox: le domande rispondono come dice risposta."""

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


def _mondo():
    """Un mondo di prova con la tua polisportiva e una del computer, e l'Open maschile del martedì da 12 dopo la prima giornata."""
    mondo = mondo_di_prova(14, 6)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    # I tuoi 1 e 2 giocano l'Open; 13, 15 e 17 fanno la squadra delle sfide, come 14, 16 e 18 per il computer.
    club = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1, 2, 13, 15, 17))
    polisportiva(mondo, "PoliTeam04", cpu=True, cassa=5000, ids=(14, 16, 18))
    mondo.miapolisportiva_attiva = club
    edizioni = apri(mondo, OGGI, "Open maschile del martedì")
    iscrivi_tutti(edizioni[0], mondo, range(1, 13))
    giorno(mondo, MARTEDI)
    return mondo


@pytest.fixture
def finestra(app_wx, messaggi, monkeypatch):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    mondo = _mondo()
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def test_il_menu_tornei_e_la_guida(finestra):
    titoli = [titolo for titolo, _voci in finestra.voci_menu()]
    assert titoli.index("&Tornei") == titoli.index("Pa&rtite") + 1
    lettere = [titolo[titolo.index("&") + 1].lower() for titolo in titoli]
    assert len(lettere) == len(set(lettere))
    guida = testi.guida(finestra.voci_guida())
    assert ("Menu Tornei: Calendario e iscrizioni, Ctrl+U; Iscrizioni dei tuoi atleti, Ctrl+J; Tornei in corso, Ctrl+Y; Albo d'oro, Ctrl+Maiusc+B; "
            "Classifica nazionale, Ctrl+Maiusc+W; Editor dei modelli di torneo, Ctrl+Maiusc+J; Editor delle formule, Ctrl+Maiusc+Y; "
            "Ripristina il calendario predefinito.") in guida
    assert testi.GUIDA_DEI_TORNEI in guida and testi.GUIDA_DELLE_SFIDE in guida and "\n\n" not in guida


def test_il_calendario_dalla_finestra_iscrive_e_salva(finestra, suonati, cartella_di_prova, monkeypatch):
    mondo = finestra.mondo
    istanti = iter(range(100, 200))
    # La pressione ripetuta la guarda la base dei dialoghi, dal 24 ottobre 2026.
    monkeypatch.setattr(dialoghi.time, "monotonic", lambda: float(next(istanti)))

    def iscrivi(self):
        self.elenco.SetSelection(next(i for i, (tipo, ed) in enumerate(self.voci) if tipo == "aperta" and ed.nome == "Open maschile del martedì"))
        self.aggiorna_atleti()
        indice = next(i for i, g in enumerate(self.iscrivibili) if g.id == 13)
        self.elenco_iscrivibili.SetSelection(indice)
        self.iscrivi()
        return wx.ID_CANCEL

    monkeypatch.setattr(gui_tornei.CalendarioTornei, "ShowModal", iscrivi)
    finestra.calendario_tornei()
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0] == "Calendario e iscrizioni di Club Di Prova: 1 iscrizione."
    assert righe[1].startswith("Iscritto ") and finestra.ultimo_evento == "calendario: 1 iscrizione, 0 tolte"
    assert suonati[0] == "dialogo_calendario_tornei" and "iscrizione_fatta" in suonati and suonati[-1] == "lavoro_concluso"
    assert (cartella_di_prova / FILE_MONDO).exists()
    assert any(13 in ed.ids() for ed in mondo.calendario.edizioni if ed.nome == "Open maschile del martedì")
    # Le iscrizioni dei tuoi atleti, Ctrl+J, aprono lo stesso dialogo col suo suono.
    monkeypatch.setattr(gui_tornei.CalendarioTornei, "ShowModal", lambda self: wx.ID_CANCEL)
    suonati.clear()
    finestra.iscrizioni_tornei()
    assert suonati == ["dialogo_iscrizioni_tornei", "lavoro_concluso"]
    assert finestra.vista.GetValue() == "Calendario e iscrizioni di Club Di Prova: nessuna iscrizione cambiata."


def _uscita(monkeypatch, uscita):
    def mostra(self):
        self.uscita = uscita
        return wx.ID_OK

    monkeypatch.setattr(dal_vivo.FinestraDalVivo, "ShowModal", mostra)


def test_il_pannello_dalla_finestra_e_la_cronaca_dell_incontro_di_torneo(finestra, suonati, cartella_di_prova, monkeypatch):
    _uscita(monkeypatch, dal_vivo.AL_RISULTATO)

    def ascolta(self):
        self.elenco_parti.SetSelection(1)
        self.alla_parte((0, 0))
        indice = next(i for i, incontro in enumerate(self.incontri) if incontro.differita and not incontro.svelato)
        self.elenco_incontri.SetSelection(indice)
        self.ascolta()
        return wx.ID_CANCEL

    monkeypatch.setattr(gui_tornei.PannelloTornei, "ShowModal", ascolta)
    finestra.tornei_in_corso()
    v = finestra.incontro
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0] == "Pannello dei tornei: 1 risultato mostrato."
    assert righe[1] == f"L'ultimo incontro, {v.nomi['A'].testo} contro {v.nomi['B'].testo}, ha la cronaca da salvare con Ctrl+Maiusc+O."
    assert suonati[:2] == ["dialogo_tornei_in_corso", "differita_al_via"] and suonati[-1] == "lavoro_concluso"
    assert (cartella_di_prova / FILE_MONDO).exists() and v.tipo == "torneo"
    finestra.salva_cronaca()
    file = next((cartella_di_prova / CARTELLA_CRONACHE).iterdir())
    assert finestra.vista.GetValue() == f"La cronaca normale dell'incontro di torneo fra {v.nomi['A'].testo} e {v.nomi['B'].testo} è nel file {file}."
    assert file.read_text(encoding="utf-8").startswith(f"Cronaca dell'incontro fra {v.nomi['A'].testo} e {v.nomi['B'].testo}, singolare al meglio dei 3 set.")


def test_la_classifica_mondiale_nella_vista(finestra, suonati):
    mondo = finestra.mondo
    mondo.giocatori[5].punti_mondiali = 120.0
    mondo.giocatori[1].punti_mondiali = 40.0
    mondo.giocatori[16].punti_mondiali = 70.0
    finestra.classifica_mondiale()
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0].startswith("Classifica nazionale per sempre") and righe[1] == "Uomini: 2 giocatori in classifica, ecco i primi 2."
    assert righe[2].startswith("1. ") and ", 120,0 punti, ori 0, " in righe[2]
    assert righe[3].endswith(", tuo tesserato") and righe[4] == "Donne: 1 giocatrice in classifica, ecco i primi 1."
    assert suonati[-1] == "classifica_mondiale" and finestra.ultimo_evento == "classifica nazionale"


def test_le_sfide_dalla_finestra_e_lo_storico(finestra, suonati, cartella_di_prova, monkeypatch, messaggi):
    mondo = finestra.mondo
    club, cpu = mondo.polisportive["Club Di Prova"], mondo.polisportive["PoliTeam04"]

    def lancia(self):
        self.lancia()
        return wx.ID_CANCEL

    monkeypatch.setattr(gui_sfide.LanciaSfida, "ShowModal", lancia)
    finestra.lancia_sfida()
    assert finestra.vista.GetValue().startswith("Sfide lanciate da Club Di Prova: 1.\nPoliTeam04 ")
    assert suonati[0] == "dialogo_lancia_sfida" and suonati[-1] == "lavoro_concluso"
    # Le sfide in arrivo, senza nessuna da rispondere: dal collaudo di gioco del 25 ottobre 2026 la finestra non si apre.
    finestra.sfide_in_arrivo()
    assert finestra.vista.GetValue() == testi.nessuna_sfida_in_arrivo() and suonati[-1] == "nessuna_sfida_in_arrivo"
    # Una sfida accettata e giocata all'avanzamento di domani entra nello storico, con la differita.
    mondo.sfide.attive.clear()
    oggi = mondo.datetime_corrente_simulazione.date()
    domani = oggi + datetime.timedelta(days=1)
    convocati = {"sfidante": [g.id for g in sfide.convoca(mondo, club, domani)], "sfidata": [g.id for g in sfide.convoca(mondo, cpu, domani)]}
    s = sfide.Sfida(mondo.sfide.nuovo_id(), sfide.iscrizioni.club_della(club), sfide.iscrizioni.club_della(cpu), oggi, oggi, sfide.ACCETTATA, domani, convocati)
    mondo.sfide.attive.append(s)
    mondo.datetime_corrente_simulazione += datetime.timedelta(days=1)
    sfide.giorno(mondo, mondo.datetime_corrente_simulazione, Mondo.rapporto_vuoto(adesso()))
    assert s.stato == sfide.GIOCATA and s.differita
    _uscita(monkeypatch, dal_vivo.ALLA_FINE)

    def ascolta(self):
        self.elenco.SetSelection(self.voci.index(s))
        self.ascolta()
        return wx.ID_CANCEL

    monkeypatch.setattr(gui_sfide.StoricoSfide, "ShowModal", ascolta)
    suonati.clear()
    finestra.storico_sfide()
    assert suonati[:4] == ["storico_sfide", "differita_al_via", "resto_dell_incontro", "risultato_svelato"]
    v = finestra.incontro
    assert v.tipo == "sfida" and v.nomi["A"].testo == "Club Di Prova" and v.risultato.formato.tipo == "squadre"
    finestra.salva_cronaca()
    assert finestra.vista.GetValue().startswith("La cronaca normale della sfida fra Club Di Prova e PoliTeam04 è nel file ")
    assert suonati[-1] == "cronaca_salvata"


def test_il_ripristino_del_calendario(finestra, suonati, cartella_di_prova, messaggi):
    gestore = modelli_torneo.GestoreModelli()
    messaggi.risposta = wx.NO
    finestra.ripristina_calendario()
    assert suonati[-2:] == ["domanda", "annullato"]
    messaggi.risposta = wx.YES
    finestra.ripristina_calendario()
    assert finestra.vista.GetValue().startswith("Il calendario predefinito è tornato. Quello di prima è nella cartella ")
    assert suonati[-1] == "calendario_ripristinato"
    assert any(p.name.startswith(modelli_torneo.PREFISSO_RIPRISTINO) for p in (cartella_di_prova / modelli_torneo.CARTELLA).iterdir())
    assert len(gestore.modelli()[0]) == 10


def test_il_ripristino_del_calendario_che_non_riesce(finestra, suonati, messaggi, monkeypatch):
    # Dalla V228 il ripristino che non riesce ha il suo suono, e non più quello del calendario illeggibile, che parla d'altro.
    def non_riesce(self):
        raise PermissionError(13, "Accesso negato")

    monkeypatch.setattr(modelli_torneo.GestoreModelli, "ripristina_predefiniti", non_riesce)
    messaggi.risposta = wx.YES
    finestra.ripristina_calendario()
    assert finestra.vista.GetValue() == "Il calendario predefinito non si è potuto rimettere: [Errno 13] Accesso negato."
    assert evento_della_barra(finestra) == "calendario non ripristinato"
    assert suonati[-2:] == ["domanda", "calendario_non_ripristinato"] and "calendario_illeggibile" not in suonati


def test_il_ripristino_fermo_a_meta_nomina_la_cartella(finestra, suonati, messaggi, monkeypatch, cartella_di_prova):
    # Dal collaudo di gioco: il ripristino che si ferma dopo aver messo da parte una parte dei file dice dove sono.
    def non_si_copia(_cartella):
        raise PermissionError(13, "Accesso negato")

    monkeypatch.setattr(modelli_torneo, "_copia_predefiniti", non_si_copia)
    messaggi.risposta = wx.YES
    finestra.ripristina_calendario()
    da_parte = next(p for p in (cartella_di_prova / modelli_torneo.CARTELLA).iterdir() if p.name.startswith(modelli_torneo.PREFISSO_RIPRISTINO))
    assert finestra.vista.GetValue() == ("Il calendario predefinito non si è potuto rimettere: [Errno 13] Accesso negato. "
                                         f"I file di prima già messi da parte sono nella cartella {da_parte}.")
    assert suonati[-2:] == ["domanda", "calendario_non_ripristinato"]


def test_il_ripristino_fermo_fra_i_modelli_non_promette_le_formule(finestra, messaggi, monkeypatch, cartella_di_prova):
    # Dalle verifiche del collaudo di gioco: fermo al terzo modello, da parte ci sono soltanto due modelli, e il messaggio
    # non dice più che ci sono anche le formule.
    sposta, spostati = modelli_torneo.shutil.move, []

    def al_terzo_si_ferma(origine, destinazione):
        if len(spostati) == 2:
            raise PermissionError(13, "Accesso negato")
        spostati.append(origine)
        return sposta(origine, destinazione)

    monkeypatch.setattr(modelli_torneo.shutil, "move", al_terzo_si_ferma)
    messaggi.risposta = wx.YES
    finestra.ripristina_calendario()
    da_parte = next(p for p in (cartella_di_prova / modelli_torneo.CARTELLA).iterdir() if p.name.startswith(modelli_torneo.PREFISSO_RIPRISTINO))
    assert len(list(da_parte.iterdir())) == 2 and not (da_parte / formule.NOME_FILE).exists()
    assert finestra.vista.GetValue().endswith(f" I file di prima già messi da parte sono nella cartella {da_parte}.")
    assert "formule" not in finestra.vista.GetValue()


def test_gli_editor_dalla_finestra(finestra, suonati, monkeypatch):
    finestra.editor_modelli()
    assert finestra.vista.GetValue() == "Nessun modello di torneo cambiato." and suonati[-2:] == ["dialogo_editor_modelli", "lavoro_concluso"]

    def salva_una_formula(self):
        self.nuova()
        self.salva()
        return wx.ID_CANCEL

    monkeypatch.setattr(gui_editor.EditorFormule, "ShowModal", salva_una_formula)
    finestra.editor_formule()
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0] == "Formule dei tornei: le modifiche valgono per le edizioni future." and righe[1].startswith("Formula salvata: Nuova formula, ")
    assert suonati[-1] == "lavoro_concluso" and "formula_salvata" in suonati


def test_la_sala_con_la_casella_dell_iscrizione_automatica(finestra, monkeypatch):
    def spegni(self):
        self.automatica.SetValue(False)
        self.all_automatica()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.SalaAllenamento, "ShowModal", spegni)
    finestra.sala_allenamento()
    righe = finestra.vista.GetValue().splitlines()
    assert righe[0] == "Sala allenamento di Club Di Prova: nessuna spesa e 1 cambio di programma, d'intensità o d'iscrizione."
    assert righe[1].endswith(", iscrizione automatica ai tornei spenta.")


def test_il_calendario_illeggibile_all_avvio_e_nella_barra(app_wx, messaggi, monkeypatch, cartella_di_prova, suonati):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    mondo = _mondo()
    gestore = modelli_torneo.GestoreModelli()
    (cartella_di_prova / modelli_torneo.CARTELLA / "Rotto.json").write_text("{ non è json", encoding="utf-8")
    gestore.azzera_cache()
    f = FinestraPrincipale(mondo, archivio.CARICATO, [], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    try:
        assert f.vista.GetValue().startswith("Il calendario dei tornei ha 1 problema: Il modello nel file Rotto.json è scartato")
        assert "rimettendo il calendario predefinito dal menu Tornei" in f.vista.GetValue().splitlines()[0]
        f.suoni_d_avvio()
        assert suonati == ["avvio", "calendario_illeggibile"]
        rapporto = Mondo.rapporto_vuoto(adesso()) | {"ticks": 1, "giorni": 1, "calendario_con_problemi": 1}
        # Già detto all'avvio: la barra non lo ripete finché non cambia.
        assert f._evento_avanzamento(rapporto, True) == ("mondo_avanzato", "mondo avanzato di un giorno")
        (cartella_di_prova / modelli_torneo.CARTELLA / "Rotto anche questo.json").write_text("[]", encoding="utf-8")
        gestore.azzera_cache()
        assert f._evento_avanzamento(rapporto, True) == ("calendario_illeggibile", "calendario dei tornei con problemi")
        assert f._evento_avanzamento(rapporto, True) == ("mondo_avanzato", "mondo avanzato di un giorno")
    finally:
        f.timer.Stop()
        f.Destroy()


def test_la_sfida_in_attesa_e_le_notizie_nella_barra(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    club, cpu = mondo.polisportive["Club Di Prova"], mondo.polisportive["PoliTeam04"]
    oggi = mondo.datetime_corrente_simulazione.date()
    sfide._proponi(mondo, cpu, club, sfide.convoca(mondo, cpu, oggi + datetime.timedelta(days=1)), oggi, Mondo.rapporto_vuoto(adesso()))
    rapporto = Mondo.rapporto_vuoto(adesso()) | {"ticks": 1, "giorni": 1, "sfide_in_attesa": 1}
    assert finestra._evento_avanzamento(rapporto, True) == ("sfida_ricevuta", "sfida da PoliTeam04, rispondi oggi")
    # L'avanzamento vero: una medaglia d'oro dei tuoi, col suo suono solo, e la frase nel riepilogo.
    medaglia = Mondo.rapporto_vuoto(adesso()) | {"ticks": 1, "giorni": 1, "tue_medaglie_oro": 1, "tornei_conclusi": 1, "incontri_torneo": 5,
                                                 "notizie": ["Mario Rossi vince la medaglia d'oro all'Open maschile del martedì."]}
    monkeypatch.setattr(mondo, "processa_tempo_trascorso", lambda: medaglia)
    suonati.clear()
    finestra.avanza()
    assert suonati == ["tua_medaglia_oro"] and finestra.ultimo_evento == "1 medaglia d'oro per i tuoi"
    finestra.riepilogo()
    assert "Mario Rossi vince la medaglia d'oro all'Open maschile del martedì." in finestra.vista.GetValue()
    assert "In Italia: 1 torneo concluso e 5 incontri di torneo." in finestra.vista.GetValue()
    assert suoni.EVENTI["tua_medaglia_oro"] == "mess_medaglia_oro"
