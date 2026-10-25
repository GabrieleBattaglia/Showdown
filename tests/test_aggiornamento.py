"""
Le prove dell'aggiornamento automatico, tappa 14, decisione D34, senza rete e senza sostituire niente:
da sorgente il controllo non parte; con un sys.frozen finto la conversazione vera di
gestisci_aggiornamento di GBUtils, con il controllo su GitHub e lo scaricamento sostituiti, passa dalla
finestra, nel suo ordine; le frasi di GBUtils dette in MESS. Poi la finestra, sul desktop nascosto del
conftest: il dialogo della proposta, che allo scadere risponde no, e il suo pulsante Aggiorna;
l'avanzamento nella barra di stato; l'esito che aspetta l'OK; la chiusura per aggiornarsi, che salva il
mondo e non apre il riepilogo di fine sessione; il ritorno in primo piano.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import datetime
import random
import sys
import time
import types

import GBUtils
import pytest
import wx
from aiuti_barra import evento_della_barra
from aiuti_dal_vivo import CassaFinta, vieta_la_cassa_vera
from aiuti_motore import giocatore

import aggiornamento
import archivio
import partita_sonora as ps
from costanti import FILE_MONDO, VERSIONE
from gui import dal_vivo, dialoghi
from gui import finestra as finestra_modulo
from gui import tornei as gui_tornei
from gui.dal_vivo import FinestraDalVivo
from gui.finestra import LIMITE_DELLA_CHIUSURA, NON_INSTALLATO, RIPROVA_DELLA_CHIUSURA, FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from partita import differita_singolare
from suoni import EVENTI
from utilita import adesso, adesso_utc


def _subito(funzione, *argomenti):
    """Al posto di wx.CallAfter: esegue subito, nel filo del controllo."""
    return funzione(*argomenti)


class FinestraFinta:
    """La finestra vista dal filo dell'aggiornamento: annota le chiamate e risponde alla proposta come le si dice."""

    def __init__(self, risposta=True, chiusa=False):
        self.risposta = risposta
        self.chiusa = chiusa
        self.chiamate = []

    def proponi_l_aggiornamento(self, versione_attuale, versione_nuova, note, attesa=None):
        self.chiamate.append(("proponi", versione_attuale, versione_nuova, note, attesa))
        return self.risposta

    def avvisa_dell_aggiornamento(self, testo):
        self.chiamate.append(("avvisa", testo))

    def avanzamento_dell_aggiornamento(self, presi, totale):
        self.chiamate.append(("avanzamento", presi, totale))

    def chiudi_per_aggiornare(self):
        self.chiamate.append(("chiudi",))


@pytest.fixture
def compilato(monkeypatch):
    """
    Un MESS compilato per finta, con la release 2.0.0 su GitHub e uno scaricamento che non scarica:
    restituisce l'elenco di che cosa hanno ricevuto il controllo e lo scaricamento.
    """
    ricevuti = []
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    def controllo(versione, api, *_argomenti, **_opzioni):
        ricevuti.append(("controllo", versione, api))
        return True, "2.0.0", "https://github.com/GabrieleBattaglia/Showdown/releases/download/v2.0.0/MESS.zip", "## Le novità\nIl manuale."

    def scaricamento(indirizzo, app, avanzamento=None, prima_di_sostituire=None, **_opzioni):
        ricevuti.append(("scaricamento", indirizzo, app))
        avanzamento(50, 100)
        prima_di_sostituire()
        return True

    monkeypatch.setattr(GBUtils, "update_checker", controllo)
    monkeypatch.setattr(GBUtils, "perform_update", scaricamento)
    return ricevuti


def test_da_sorgente_il_controllo_non_parte(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert aggiornamento.controlla(FinestraFinta(), chiama_dopo=_subito) is None


def test_dall_eseguibile_la_conversazione_passa_dalla_finestra(compilato):
    finestra = FinestraFinta()
    filo = aggiornamento.controlla(finestra, chiama_dopo=_subito)
    filo.join(10)
    assert not filo.is_alive()
    assert compilato == [("controllo", VERSIONE, aggiornamento.API), ("scaricamento", compilato[1][1], "MESS")]
    assert aggiornamento.API.endswith("/GabrieleBattaglia/Showdown/releases/latest")
    # La proposta riceve l'attesa di GBUtils, due minuti; poi l'avanzamento, l'esito detto in MESS prima della sostituzione, e la chiusura.
    assert finestra.chiamate == [
        ("proponi", VERSIONE, "2.0.0", "## Le novità\nIl manuale.", 120),
        ("avanzamento", 50, 100),
        ("avvisa", "Aggiornamento scaricato: MESS salva il mondo, si chiude per installarlo e si riapre da solo."),
        ("chiudi",),
    ]


def test_non_adesso_o_la_finestra_chiusa_non_aggiornano(compilato):
    finestra = FinestraFinta(risposta=False)
    aggiornamento.controlla(finestra, chiama_dopo=_subito).join(10)
    assert [c[0] for c in finestra.chiamate] == ["proponi"]
    # La finestra che si chiude mentre il controllo gira non riceve niente, e la risposta vale no.
    chiusa = FinestraFinta(chiusa=True)
    aggiornamento.controlla(chiusa, chiama_dopo=_subito).join(10)
    assert chiusa.chiamate == []
    assert [voce[0] for voce in compilato] == ["controllo", "controllo"]


def test_le_frasi_di_gbutils_dette_in_mess():
    assert aggiornamento.traduci("ma il pacchetto non e' ancora pronto.") == "ma il pacchetto non è ancora pronto: te la ripropongo a un prossimo avvio."
    assert aggiornamento.traduci("Hai gia' l'ultima versione,") == "Hai già l'ultima versione,"
    assert aggiornamento.traduci("Disponibile la versione") == "Disponibile la versione"
    # Nessuna frase di MESS ha l'apostrofo al posto dell'accento.
    assert not any(accento in frase for frase in aggiornamento.FRASI.values() for accento in ("e' ", "a' ", "o' ", "u' ", "i' "))


# La finestra.

@pytest.fixture
def mondo():
    random.seed(14)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(20, ora)
    mia = Polisportiva("Club Di Prova", None, ora)
    m.polisportive[mia.nome] = mia
    m.miapolisportiva_attiva = mia
    return m


def _apri(mondo):
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    f.Show()
    return f


def _chiudi(f):
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


@pytest.fixture
def finestra(app_wx, mondo, monkeypatch):
    # Nessun messaggio vero: la prova non avrebbe nessuno che lo chiude. I dialoghi, qui, sono veri.
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    f = _apri(mondo)
    yield f
    _chiudi(f)


def _guardia():
    """Se un dialogo modale restasse aperto per un errore, dopo dieci secondi si chiude: la prova fallisce invece di non finire mai."""
    def sblocca():
        for d in wx.GetTopLevelWindows():
            if isinstance(d, wx.Dialog) and d.IsModal():
                d.EndModal(wx.ID_CANCEL)

    return wx.CallLater(10_000, sblocca)


def test_il_dialogo_della_proposta(app_wx):
    dialogo = dialoghi.Aggiornamento(None, "1.94.6", "2.0.0", "Il manuale nel browser.", attesa=120)
    try:
        testo = dialogo.testo.GetValue()
        assert testo.startswith("È disponibile MESS 2.0.0; tu hai la 1.94.6.\n")
        assert "Se non rispondi entro 2 minuti, il dialogo si chiude da solo" in testo and testo.endswith("Le note della release:\nIl manuale nel browser.")
        assert [b.GetLabel() for b in dialogo.bottoni] == ["&Aggiorna", "&Non adesso"]
        assert dialogo.GetDefaultItem() is dialogo.bottoni[-1] and dialogo.GetEscapeId() == wx.ID_NO
        assert "\n\n" not in testo
    finally:
        dialogo.Destroy()
    assert [dialoghi.durata_dell_attesa(s) for s in (120, 60, 90, 45)] == ["2 minuti", "1 minuto", "1 minuto e 30 secondi", "45 secondi"]
    vuoto = dialoghi.Aggiornamento(None, "1.94.6", "2.0.0", "")
    try:
        assert vuoto.testo.GetValue().endswith("Le note della release:\nNessuna nota scritta per questa versione.") and "entro" not in vuoto.testo.GetValue()
    finally:
        vuoto.Destroy()


class TastoFinto:
    """Un tasto premuto, per _tasto del dialogo."""

    def __init__(self, codice, oggetto, ripetuto=False):
        self.codice, self.oggetto, self.ripetuto, self.saltato = codice, oggetto, ripetuto, False

    def GetKeyCode(self):
        return self.codice

    def GetEventObject(self):
        return self.oggetto

    def IsAutoRepeat(self):
        return self.ripetuto

    def Skip(self):
        self.saltato = True


def test_esc_e_invio_nel_testo_valgono_non_adesso(app_wx, monkeypatch):
    orologio = [100.0]
    monkeypatch.setattr(dialoghi, "_adesso", lambda: orologio[0])
    dialogo = dialoghi.Aggiornamento(None, "1.94.6", "2.0.0", "Note.")
    try:
        # Un Invio subito dopo l'apertura, con NVDA una pressione nuova, cade nella grazia e non risponde.
        orologio[0] += 0.2
        presto = TastoFinto(wx.WXK_RETURN, dialogo.testo)
        dialogo._tasto(presto)
        assert presto.saltato and dialogo.GetReturnCode() == 0
        orologio[0] += 5
        ripetuto = TastoFinto(wx.WXK_RETURN, dialogo.testo, ripetuto=True)
        dialogo._tasto(ripetuto)
        assert ripetuto.saltato and dialogo.GetReturnCode() == 0
        orologio[0] += 5
        dialogo._tasto(TastoFinto(wx.WXK_RETURN, dialogo.testo))
        assert dialogo.GetReturnCode() == wx.ID_NO
        dialogo.SetReturnCode(0)
        dialogo._tasto(TastoFinto(wx.WXK_ESCAPE, dialogo.bottoni[0]))
        assert dialogo.GetReturnCode() == wx.ID_NO
        # Invio su un pulsante resta suo.
        sul_pulsante = TastoFinto(wx.WXK_RETURN, dialogo.bottoni[0])
        dialogo._tasto(sul_pulsante)
        assert sul_pulsante.saltato
    finally:
        dialogo.Destroy()


def test_aggiorna_risponde_si(app_wx):
    dialogo = dialoghi.Aggiornamento(None, "1.94.6", "2.0.0", "Note.", attesa=60)
    guardia = _guardia()
    try:
        evento = wx.CommandEvent(wx.wxEVT_BUTTON, dialogo.bottoni[0].GetId())
        evento.SetEventObject(dialogo.bottoni[0])
        wx.CallAfter(dialogo.bottoni[0].GetEventHandler().ProcessEvent, evento)
        assert dialogo.ShowModal() == wx.ID_YES
    finally:
        guardia.Stop()
        dialogo.Destroy()


def test_la_proposta_che_scade_risponde_no(finestra, suonati):
    guardia = _guardia()
    try:
        assert not finestra.proponi_l_aggiornamento("1.94.6", "2.0.0", "## Le novità\n\nIl manuale.", attesa=0.3)
    finally:
        guardia.Stop()
    # La proposta lasciata scadere ha il suo suono, diverso da Non adesso.
    assert suonati == ["aggiornamento_disponibile", "aggiornamento_scaduto"]
    assert evento_della_barra(finestra) == "aggiornamento rimandato: tempo scaduto" and finestra._modali == 0


def test_non_adesso(finestra, suonati, monkeypatch):
    monkeypatch.setattr(dialoghi.Aggiornamento, "ShowModal", lambda self: wx.ID_NO)
    assert not finestra.proponi_l_aggiornamento("1.94.6", "2.0.0", "Note.", attesa=120)
    assert suonati == ["aggiornamento_disponibile", "annullato"] and evento_della_barra(finestra) == "aggiornamento rimandato"


def test_la_proposta_accettata(finestra, suonati, monkeypatch):
    monkeypatch.setattr(dialoghi.Aggiornamento, "ShowModal", lambda self: wx.ID_YES)
    assert finestra.proponi_l_aggiornamento("1.94.6", "2.0.0", "Note.", attesa=120)
    assert suonati == ["aggiornamento_disponibile", "aggiornamento_scelto"] and evento_della_barra(finestra) == "scarico MESS 2.0.0"


def test_l_avanzamento_nella_barra_di_stato(finestra):
    righe = []
    for presi, totale in ((8, 100), (1, 3), (100, 100), (5 * 1048576, 0)):
        finestra.avanzamento_dell_aggiornamento(presi, totale)
        righe.append(evento_della_barra(finestra))
    assert righe == ["aggiornamento scaricato all'8%", "aggiornamento scaricato al 33%", "aggiornamento scaricato al 100%", "aggiornamento: 5,0 MB scaricati"]


def test_gli_esiti_dalle_frasi_vere_di_gbutils(compilato, monkeypatch):
    # Il pacchetto non ancora pronto: GBUtils mette la versione davanti alla frase.
    monkeypatch.setattr(GBUtils, "update_checker", lambda *_a, **_k: (True, "2.1.0", "", "Note."))
    finestra = FinestraFinta()
    aggiornamento.controlla(finestra, chiama_dopo=_subito).join(10)
    non_pronto = finestra.chiamate[-1][1]
    assert non_pronto == "Disponibile la versione 2.1.0, ma il pacchetto non è ancora pronto: te la ripropongo a un prossimo avvio."
    # Lo scaricamento che non riesce.
    monkeypatch.setattr(GBUtils, "update_checker", lambda *_a, **_k: (True, "2.1.0", "https://github.com/x/MESS.zip", "Note."))
    monkeypatch.setattr(GBUtils, "perform_update", lambda *_a, **_k: False)
    finestra = FinestraFinta()
    aggiornamento.controlla(finestra, chiama_dopo=_subito).join(10)
    non_riuscito = finestra.chiamate[-1][1]
    assert [aggiornamento.esito(t) for t in (aggiornamento.FRASE_PRONTO, non_riuscito, non_pronto, "Un'altra frase.")] == [
        aggiornamento.PRONTO, aggiornamento.NON_RIUSCITO, aggiornamento.NON_PRONTO, None]


@pytest.mark.parametrize(("testo", "suono", "icona"), [
    (aggiornamento.FRASE_PRONTO, "aggiornamento_esito", wx.ICON_INFORMATION),
    (aggiornamento.FRASE_NON_RIUSCITO, "aggiornamento_non_riuscito", wx.ICON_ERROR),
    # Il pacchetto non ancora pronto non è un guasto: dalla terza revisione della tappa 14 ha l'icona dell'avviso.
    (f"Disponibile la versione 2.1.0, {aggiornamento.FRASE_NON_PRONTO}", "aggiornamento_non_pronto", wx.ICON_WARNING),
])
def test_l_esito_aspetta_l_ok(finestra, suonati, monkeypatch, testo, suono, icona):
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, titolo, stile, *a, **k: messaggi.append((testo, titolo, stile)))
    finestra.avvisa_dell_aggiornamento(testo)
    assert messaggi == [(testo, "Aggiornamento di MESS", wx.OK | icona)]
    assert suonati == [suono] and finestra._modali == 0


def _fino_a(condizione, secondi=5.0):
    """
    Fa girare un ciclo di eventi di wx finché la condizione è vera o finisce il tempo: i timer, come i
    nuovi tentativi della chiusura, scattano soltanto in un ciclo che gira, non con wx.Yield.
    """
    fine = time.monotonic() + secondi
    ciclo = wx.GUIEventLoop()

    def guarda():
        if condizione() or time.monotonic() > fine:
            ciclo.Exit()
        else:
            wx.CallLater(20, guarda)

    wx.CallLater(20, guarda)
    attivo = wx.EventLoopActivator(ciclo)
    try:
        ciclo.Run()
    finally:
        del attivo
    return condizione()


def test_chiudi_per_aggiornare_nella_differita_non_svela_il_risultato(finestra, suonati, monkeypatch):
    """
    Una differita aperta dal pannello dei tornei mentre arriva la chiusura per aggiornare: la finestra
    dal vivo esce come con Esc, il timer e il suono si fermano, il risultato resta da scoprire,
    decisione D30, e la chiusura riprova da sola finché la finestra principale si chiude.
    """
    vieta_la_cassa_vera(monkeypatch)
    casse = []
    monkeypatch.setattr(ps, "Cassa", lambda: casse.append(CassaFinta()) or casse[-1])
    differita = differita_singolare(giocatore(1, 12.0), giocatore(2, 13.0), {}, {}, {}, 3)
    visti = []

    def durante():
        vivo = next(d for d in wx.GetTopLevelWindows() if isinstance(d, FinestraDalVivo) and d.IsModal())
        vivo.al_prosegui()
        visti.append((vivo.stato, vivo.timer.IsRunning(), casse[0].accese))
        finestra.chiudi_per_aggiornare()
        visti.append((vivo.uscita, vivo.timer.IsRunning(), casse[0].accese, vivo.GetReturnCode()))

    guardia = _guardia()
    wx.CallAfter(durante)
    try:
        ultimo, _velocita = gui_tornei.ascolta_e_ricorda(finestra, finestra.mondo, differita, 7, finestra.impostazioni, {1}, None, "torneo")
    finally:
        guardia.Stop()
    assert visti == [(dal_vivo.SUONA, True, 1), (dal_vivo.CON_ESC, False, 0, wx.ID_CANCEL)]
    assert ultimo is None and "differita_interrotta" in suonati and "risultato_svelato" not in suonati
    # Il dialogo era aperto: la finestra principale non si è chiusa subito, ma al primo nuovo tentativo.
    assert suonati[-1] == "differita_interrotta" and finestra._per_aggiornare
    assert _fino_a(lambda: finestra.chiusa)
    assert suonati[-1] == "uscita"
    wx.Yield()
    assert not finestra


def test_chiudi_per_aggiornare_annulla_gli_altri_dialoghi(finestra, suonati):
    lettura = dialoghi.Lettura(finestra, "Prova", "Un testo da leggere.")
    guardia = _guardia()
    wx.CallAfter(finestra.chiudi_per_aggiornare)
    try:
        assert lettura.ShowModal() == wx.ID_CANCEL
    finally:
        guardia.Stop()
        lettura.Destroy()
    assert not finestra.chiusa
    assert _fino_a(lambda: finestra.chiusa) and suonati == ["uscita"]
    wx.Yield()


def test_chiudi_per_aggiornare_smette_di_riprovare_e_lo_dice(finestra, suonati, monkeypatch):
    orologio = [1000.0]
    monkeypatch.setattr(finestra_modulo, "time", types.SimpleNamespace(monotonic=lambda: orologio[0]))
    rinviati = []
    monkeypatch.setattr(wx, "CallLater", lambda millisecondi, funzione, *a, **k: rinviati.append((millisecondi, funzione)))
    finestra._modali = 1
    finestra.chiudi_per_aggiornare()
    orologio[0] += LIMITE_DELLA_CHIUSURA - 1
    finestra.chiudi_per_aggiornare()
    assert rinviati == [(RIPROVA_DELLA_CHIUSURA, finestra.chiudi_per_aggiornare)] * 2
    # Oltre il limite lo script di sostituzione ha rinunciato: MESS resta aperto, e lo dirà quando il messaggio si chiude.
    orologio[0] += 2
    finestra.chiudi_per_aggiornare()
    assert rinviati[-1] == (RIPROVA_DELLA_CHIUSURA, finestra._di_che_non_si_e_installato)
    assert not finestra.chiusa and not finestra._per_aggiornare and suonati == []
    finestra._modali = 0
    finestra._di_che_non_si_e_installato()
    # Il suono suo, dalla terza revisione: quello dell'aggiornamento non riuscito resta allo scaricamento.
    assert finestra.vista.GetValue() == NON_INSTALLATO and suonati == ["aggiornamento_non_installato"]
    assert EVENTI["aggiornamento_non_installato"] == "mess_aggiornamento_non_installato" != EVENTI["aggiornamento_non_riuscito"]
    riga = evento_della_barra(finestra)
    assert riga == "aggiornamento non installato"
    assert len(rinviati) == 3 and not finestra.chiusa


def test_chiudi_per_aggiornare_dice_il_salvataggio_non_riuscito(finestra, suonati, monkeypatch):
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, titolo, stile, *a, **k: messaggi.append((testo, titolo, stile)))
    monkeypatch.setattr(FinestraPrincipale, "_salva_raccogliendo", lambda self: (False, ["Il disco è pieno."], []))
    finestra.chiudi_per_aggiornare()
    assert finestra.chiusa and suonati == ["uscita_senza_salvataggio"]
    assert messaggi == [("Il mondo non si è salvato prima dell'aggiornamento. Il disco è pieno.\n"
                         "Alla riapertura ritroverai il mondo dell'ultimo salvataggio riuscito. Con OK MESS si chiude e installa la versione nuova.",
                         "Aggiornamento di MESS", wx.OK | wx.ICON_ERROR)]
    wx.Yield()
    assert not finestra


def test_chiudi_per_aggiornare_salva_e_non_apre_il_riepilogo(finestra, suonati, cartella_di_prova, monkeypatch):
    riepiloghi = []
    monkeypatch.setattr(dialoghi.Lettura, "ShowModal", lambda self: riepiloghi.append(self.GetTitle()) or wx.ID_OK)
    # Con un messaggio aperto la chiusura aspetta, e riprova.
    rinviati = []
    monkeypatch.setattr(wx, "CallLater", lambda millisecondi, funzione, *a, **k: rinviati.append((millisecondi, funzione)))
    finestra._modali = 1
    finestra.chiudi_per_aggiornare()
    assert rinviati == [(RIPROVA_DELLA_CHIUSURA, finestra.chiudi_per_aggiornare)] and not finestra.chiusa
    assert not (cartella_di_prova / FILE_MONDO).exists()
    finestra._modali = 0
    finestra.chiudi_per_aggiornare()
    assert finestra.chiusa
    wx.Yield()
    assert (cartella_di_prova / FILE_MONDO).exists()
    assert riepiloghi == [] and suonati == ["uscita"]
    assert not finestra
    # Il filo dell'aggiornamento può chiamare ancora: la finestra chiusa non fa niente.
    finestra.chiudi_per_aggiornare()
    finestra.avanzamento_dell_aggiornamento(1, 2)


def test_porta_in_primo_piano(finestra, suonati):
    finestra.Iconize(True)
    finestra.porta_in_primo_piano()
    assert not finestra.IsIconized() and suonati == ["primo_piano"]
    finestra.chiusa = True
    finestra.porta_in_primo_piano()
    assert suonati == ["primo_piano"]
    finestra.chiusa = False
