"""
Le prove della finestra dello staff, tappa 13, decisione D33 e capitolo 4 del progetto, coi dialoghi veri
sul desktop nascosto del conftest e i suoni soltanto registrati: il dialogo dello staff coi tre posti,
l'assunzione dal mercato degli allenatori, accettata e rifiutata, i filtri del mercato, il posto già
occupato, il rinnovo coi tre tentativi, il licenziamento con la buonuscita, le voci del menu e il
riepilogo alla chiusura. Anche le regole del mondo per l'utente: l'offerta e il licenziamento usano una
mossa, il rinnovo no. I messaggi di wx sono sostituiti da un registratore, che risponde come gli si dice.
Dal 24 ottobre 2026, coi collegamenti della finestra Mercato e ricerca, Assumi apre lei, sugli allenatori liberi col
posto scelto: le offerte agli allenatori vanno fra gli esiti dello staff, il resto fra quelli della finestra, che la
vista riassume dopo lo staff, e un'amichevole scelta lì chiude lo staff e si gioca. Le prove del mercato degli
allenatori di prima, coi filtri, l'ingaggio accettato e rifiutato, le mosse finite, la prelazione, la scheda e il
diario, stanno con quelle della finestra, in tests/test_mercato_e_ricerca_finestra.py.
Col passo dei suoni dello stesso giorno ogni evento della finestra ha il suo preset, e le prove usano il registratore di sempre.
"""

import datetime
import random

import pytest
import wx

import archivio
import contratti
import mercato
import mondo as modulo_mondo
import staff
import suoni
import testi
from gui import dialoghi
from gui import mercato_e_ricerca as gui_mercato
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from utilita import adesso_utc

ORA = datetime.datetime(2027, 10, 9, 18, 0)


@pytest.fixture
def mondo():
    random.seed(29)
    m = Mondo()
    m.datetime_corrente_simulazione = ORA
    m.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=2)
    m.crea_giocatori_casuali(30, ORA)
    mia = Polisportiva("Club Dello Staff", None, ORA - datetime.timedelta(days=300))
    mia.cassa = 50_000
    m.polisportive[mia.nome] = mia
    for gid in (3, 7):
        m._entra(mia, m.giocatori[gid])
    m.miapolisportiva_attiva = mia
    rng = random.Random(5)
    for _ in range(8):
        m._nasce_un_allenatore(ORA, rng)
    m.aggiorna_fattori_staff()
    return m


class Messaggi(list):
    """I testi dei messaggi di wx, in ordine; risposta è quello che rispondono le domande."""

    def __init__(self):
        super().__init__()
        self.risposta = wx.YES

    def __call__(self, testo, *args, **kwargs):
        self.append(testo)
        return self.risposta


@pytest.fixture
def messaggi(monkeypatch):
    registro = Messaggi()
    monkeypatch.setattr(wx, "MessageBox", registro)
    return registro


@pytest.fixture
def staff_aperto(app_wx, mondo):
    dialogo = dialoghi.Staff(None, mondo, mondo.miapolisportiva_attiva)
    yield dialogo
    dialogo.Destroy()


def _assumi(mondo, posto=0, indice=0):
    """Mette nello staff dell'utente, al posto dato, il libero all'indice dato dell'ordine del mercato."""
    poli = mondo.miapolisportiva_attiva
    liberi = sorted((a for a in mondo.allenatori.values() if a.libero), key=lambda a: (a.livello, a.eta(ORA), a.numero))
    a = liberi[indice]
    mondo.assumi_allenatore(poli, a, posto, ORA)
    return a


def _in_finestra(mondo, a, giorni=0):
    """Porta la data del mondo dentro la finestra del rinnovo dell'allenatore, più tanti giorni."""
    mondo.datetime_corrente_simulazione = contratti.inizio_finestra(a).replace(hour=18) + datetime.timedelta(days=giorni)


def test_lo_staff_si_apre_coi_tre_posti(staff_aperto, mondo):
    d = staff_aperto
    poli = mondo.miapolisportiva_attiva
    assert [d.elenco.GetString(i) for i in range(3)] == ["Capo: posto vuoto", "Assistente 1: posto vuoto", "Assistente 2: posto vuoto"]
    assert d.info.GetLabel() == testi.testata_staff(poli, mondo)
    assert "stipendi dello staff 0 euro al mese" in d.info.GetLabel() and "Qualità dello staff 0%" in d.info.GetLabel()
    assert d.previsto.GetValue() == "Posto vuoto: Assumi apre il mercato degli allenatori per questo posto."


def test_le_lettere_del_dialogo_dello_staff_non_si_ripetono(staff_aperto):
    testi_con_lettera = [c.GetLabel() for c in staff_aperto.pannello.GetChildren() if "&" in c.GetLabel()]
    lettere = [t[t.index("&") + 1].lower() for t in testi_con_lettera]
    assert len(lettere) == len(set(lettere)) == 10, testi_con_lettera


def test_nessun_pulsante_predefinito(staff_aperto):
    # Invio sugli elenchi non fa niente, progetto 4.2, come nei dialoghi della tappa 12.
    assert staff_aperto.GetDefaultItem() is None


def test_dallo_staff_al_mercato_e_ritorno(staff_aperto, mondo, messaggi, suonati, monkeypatch):
    d = staff_aperto
    poli = mondo.miapolisportiva_attiva
    aperti = []

    def mercato_finto(posto):
        aperti.append(posto)
        _assumi(mondo, posto)
        # Dalla issue 8 la finestra Mercato e ricerca: le offerte agli allenatori sono dello staff, il resto della finestra.
        return gui_mercato.EsitiDellaFinestra(giocatori=[("Ingaggiato per prova.", True)], allenatori=[("Assunto per prova.", "assunto")],
                                              sfide=["Sfida lanciata per prova."], preset=["Preset salvato: Allenatori."])

    monkeypatch.setattr(d, "apri_il_mercato", mercato_finto)
    d.elenco.SetSelection(1)
    d.assumi()
    assert aperti == [1] and d.esiti == [("Assunto per prova.", "assunto")]
    finestra = d.esiti_della_finestra
    assert (finestra.giocatori, finestra.allenatori, finestra.sfide, finestra.preset, finestra.amichevole) == (
        [("Ingaggiato per prova.", True)], [], ["Sfida lanciata per prova."], ["Preset salvato: Allenatori."], None)
    assert d.elenco.GetString(1).startswith(f"Assistente 1: {testi.nome_allenatore(mondo.allenatori[poli.staff[1]])}, ")
    assert d.durata.GetValue() == staff.durata_proposta(mondo.allenatori[poli.staff[1]], ORA)
    d.assumi()
    assert aperti == [1] and suonati[-1] == "staff_posto_occupato" and messaggi[-1].endswith("per cambiarlo, prima licenzia.")
    # Un'amichevole scelta nella finestra chiude lo staff: la partita la gioca la finestra principale.
    amichevole = (mondo.giocatori[3], mondo.giocatori[10], (3, "fine", "normale"))
    monkeypatch.setattr(d, "apri_il_mercato", lambda posto: gui_mercato.EsitiDellaFinestra(amichevole=amichevole))
    d.elenco.SetSelection(2)
    d.assumi()
    assert d.esiti_della_finestra.amichevole == amichevole and d.GetReturnCode() == wx.ID_CANCEL


def test_assumi_apre_la_finestra_sugli_allenatori_liberi_col_posto_scelto(staff_aperto, mondo, suonati, monkeypatch):
    d = staff_aperto
    viste = []

    def nella_finestra(finestra):
        # La finestra è figlia dello staff, sulla porta di Assumi, e suona lei la sua apertura; lo staff non suona niente.
        viste.append((finestra.porta, finestra.posto, finestra.filtri == mercato.filtri_di_serie("allenatori_liberi"), list(suonati)))
        finestra.esiti.allenatori.append(("Assunto per prova.", "assunto"))
        finestra.chiudi_la_finestra()
        return wx.ID_CLOSE

    monkeypatch.setattr(gui_mercato.MercatoERicerca, "ShowModal", nella_finestra)
    d.elenco.SetSelection(2)
    suonati.clear()
    prima = mercato.filtri_di_ricerca_del_mondo(mondo)
    d.assumi()
    assert viste == [(None, 2, True, ["dialogo_mercato_allenatori"])]
    assert d.esiti == [("Assunto per prova.", "assunto")] and d.GetReturnCode() == 0
    # Assumi non è una porta: alla chiusura la finestra non ricorda niente.
    assert mercato.filtri_di_ricerca_del_mondo(mondo) == prima
    # Chiusa da qualcun altro, come la chiusura per l'aggiornamento, gli esiti arrivano lo stesso, vuoti.
    monkeypatch.setattr(gui_mercato.MercatoERicerca, "ShowModal", lambda finestra: wx.ID_CANCEL)
    assert d.apri_il_mercato(0).vuoti


def test_scheda_e_diario_senza_un_allenatore(staff_aperto, suonati, monkeypatch):
    # La scheda e il diario degli allenatori della finestra li provano le prove della finestra Mercato e ricerca.
    letti = []
    monkeypatch.setattr(dialoghi.Lettura, "ShowModal", lambda self: letti.append((self.GetTitle(), self.testo.GetValue())) or wx.ID_OK)
    staff_aperto.scheda()
    staff_aperto.diario()
    assert suonati == ["nessuna_selezione", "nessuna_selezione"] and letti == []


def test_scheda_e_diario_dell_allenatore_dello_staff(staff_aperto, mondo, suonati, monkeypatch):
    letti = []
    monkeypatch.setattr(dialoghi.Lettura, "ShowModal", lambda self: letti.append((self.GetTitle(), self.testo.GetValue())) or wx.ID_OK)
    a = _assumi(mondo, 0)
    staff_aperto.aggiorna(0, campi=True)
    staff_aperto.scheda()
    staff_aperto.diario()
    assert suonati[-2:] == ["scheda_allenatore", "diario_allenatore"]
    assert letti == [(f"Scheda di {testi.nome_completo(a)}", testi.scheda_allenatore(a, mondo)), (f"Diario di {testi.nome_completo(a)}", testi.diario_allenatore(a))]


def test_il_rinnovo_dello_staff(staff_aperto, mondo, messaggi, suonati, monkeypatch):
    d = staff_aperto
    poli = mondo.miapolisportiva_attiva
    a = _assumi(mondo, 0)
    d.aggiorna(0, campi=True)
    # Fuori dalla finestra il rinnovo non si propone, e l'esito previsto dice da quando.
    assert d.previsto.GetValue() == mondo.problema_rinnovo_allenatore(poli, a)
    d.rinnova()
    assert suonati[-1] == "rinnovo_fuori_finestra" and a.proposte_rinnovo == 0
    _in_finestra(mondo, a)
    d.aggiorna(0, campi=True)
    assert d.previsto.GetValue().startswith("Accetterebbe al ") and ", in scadenza: chiede " in d.elenco.GetString(0)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: False)
    mosse = mondo.mosse_rimaste(poli)
    d.rinnova()
    assert suonati[-2:] == ["domanda", "staff_rinnovo_rifiutato"] and "2 proposte rimaste, una al giorno." in messaggi[-1]
    assert mondo.mosse_rimaste(poli) == mosse
    d.rinnova()
    assert suonati[-1] == "rinnovo_gia_proposto_oggi"
    _in_finestra(mondo, a, 1)
    d.aggiorna(0, campi=True)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    stipendio, mesi = d.stipendio.GetValue(), d.durata.GetValue()
    scadenza = a.contratto_scadenza
    d.rinnova()
    assert suonati[-1] == "staff_rinnovo_concordato" and messaggi[-1].startswith(f"{testi.nome_completo(a)} ha accettato: dal ")
    assert a.rinnovo_stipendio == stipendio and a.rinnovo_scadenza == contratti.scadenza_dopo(scadenza, mesi)
    assert ", rinnovato dal " in d.elenco.GetString(0)
    assert [esito for _testo, esito in d.esiti] == ["rifiutato", "rinnovato"]
    d.rinnova()
    assert suonati[-1] == "rinnovo_gia_concordato"


def test_il_rinnovo_rifiutato_tre_volte_si_chiude(staff_aperto, mondo, messaggi, suonati, monkeypatch):
    d = staff_aperto
    a = _assumi(mondo, 0)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: False)
    for giorno in range(3):
        _in_finestra(mondo, a, giorno)
        d.aggiorna(0, campi=True)
        d.rinnova()
    assert suonati[-1] == "staff_rinnovo_chiuso" and "Non vuole più trattare" in messaggi[-1]
    assert ", non tratta più: " in d.elenco.GetString(0) and a.proposte_rinnovo == 3
    _in_finestra(mondo, a, 3)
    d.aggiorna(0, campi=True)
    d.rinnova()
    assert suonati[-1] == "rinnovo_senza_proposte"


def test_il_licenziamento_con_la_buonuscita(staff_aperto, mondo, messaggi, suonati):
    d = staff_aperto
    poli = mondo.miapolisportiva_attiva
    a = _assumi(mondo, 2)
    d.aggiorna(2, campi=True)
    buonuscita = contratti.buonuscita(a, ORA)
    assert buonuscita > 0
    messaggi.risposta = wx.NO
    d.licenzia()
    assert suonati[-2:] == ["domanda", "annullato"] and poli.staff[2] == a.numero
    assert messaggi[-1] == testi.domanda_licenziamento(a, poli, mondo) and testi.euro(buonuscita) in messaggi[-1]
    messaggi.risposta = wx.YES
    cassa, mosse = poli.cassa, mondo.mosse_rimaste(poli)
    d.licenzia()
    assert suonati[-1] == "allenatore_licenziato" and poli.staff[2] == 0 and a.libero
    assert poli.cassa == cassa - buonuscita and mondo.mosse_rimaste(poli) == mosse - 1
    assert d.esiti == [(messaggi[-1], "licenziato")] and d.elenco.GetString(2) == "Assistente 2: posto vuoto"


def test_il_licenziamento_senza_cassa(staff_aperto, mondo, messaggi, suonati):
    poli = mondo.miapolisportiva_attiva
    a = _assumi(mondo, 0)
    poli.cassa = 0
    staff_aperto.aggiorna(0, campi=True)
    staff_aperto.licenzia()
    assert suonati == ["cassa_insufficiente"] and messaggi[-1].startswith(f"Licenziare {testi.nome_completo(a)} costa una buonuscita")


@pytest.fixture
def finestra(app_wx, mondo, monkeypatch):
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(ORA), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def test_le_voci_del_menu_e_il_riepilogo(finestra, mondo, suonati, monkeypatch):
    voci = [voce for _titolo, gruppo in finestra.voci_menu() for voce in gruppo if voce]
    assert ("Staf&f della polisportiva attiva...", "Ctrl+H", finestra.staff) in voci
    assert ("Mercato degli a&llenatori...", "Ctrl+Shift+G", finestra.mercato_allenatori) in voci
    finestra.staff()
    assert suonati[0] == "dialogo_staff" and finestra.vista.GetValue().startswith("Staff di Club Dello Staff: nessuna operazione.\nCapo: nessuno.")
    assert finestra.ultimo_evento == "staff: 0 operazioni"

    # Dalla issue 8 Ctrl+Maiusc+G apre la finestra Mercato e ricerca sugli allenatori liberi, e la vista riassume la finestra.
    def un_assunzione(self):
        assert self.porta == "allenatori" and all(r.allenatore and r.persona.libero for r in self.righe) and self.righe
        self.esiti.allenatori.append(("Assunto per prova.", "assunto"))
        self.chiudi_la_finestra()
        return wx.ID_CLOSE

    monkeypatch.setattr(gui_mercato.MercatoERicerca, "ShowModal", un_assunzione)
    finestra.mercato_allenatori()
    assert "dialogo_mercato_allenatori" in suonati
    righe = finestra.vista.GetValue().splitlines()
    assert righe[:2] == ["Mercato e ricerca di Club Dello Staff: 1 offerta agli allenatori, 1 riuscita.", "Assunto per prova."]
    assert righe[3:] == testi.righe_dello_staff(mondo.miapolisportiva_attiva, mondo)[1:]
    assert finestra.ultimo_evento == "mercato e ricerca: 1 esito"


def test_lo_staff_riassume_anche_la_finestra_e_gioca_l_amichevole(finestra, mondo, suonati, monkeypatch, cartella_di_prova):
    poli = mondo.miapolisportiva_attiva
    salvati = []
    vero = archivio.salva_con_avvisi
    monkeypatch.setattr(archivio, "salva_con_avvisi", lambda m: (salvati.append(m), vero(m))[1])

    def staff_con_la_finestra(self):
        self.esiti.append(("Assunto per prova.", "assunto"))
        self.esiti_della_finestra.giocatori.append(("Ingaggiato per prova.", True))
        self.esiti_della_finestra.preset.append("Preset salvato: Allenatori.")
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Staff, "ShowModal", staff_con_la_finestra)
    finestra.staff()
    # Prima lo staff, poi quello che si è fatto nella finestra aperta da Assumi, senza le offerte agli allenatori, che sono dello staff.
    staff_di_adesso = testi.riepilogo_staff(poli, [("Assunto per prova.", "assunto")], mondo)
    finestra_di_adesso = testi.riepilogo_mercato_e_ricerca(poli, mondo, [("Ingaggiato per prova.", True)], preset=["Preset salvato: Allenatori."])
    assert finestra.vista.GetValue() == f"{staff_di_adesso}\n{finestra_di_adesso}"
    assert finestra_di_adesso.startswith("Mercato e ricerca di Club Dello Staff: 1 offerta ai giocatori, 1 riuscita; 1 operazione sui preset.")
    assert finestra.ultimo_evento == "staff: 1 operazione, mercato e ricerca: 2 esiti" and suonati[-1] == "lavoro_concluso" and salvati == [mondo]
    # Senza le operazioni dello staff, i preset della finestra bastano a salvare.
    def soltanto_un_preset(self):
        self.esiti_della_finestra.preset.append("Preset salvato: Capi.")
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Staff, "ShowModal", soltanto_un_preset)
    finestra.staff()
    assert finestra.vista.GetValue().startswith("Staff di Club Dello Staff: nessuna operazione.\n") and len(salvati) == 2
    # Con un'amichevole scelta nella finestra, la partita la gioca la finestra principale, coi riepiloghi davanti.
    giocate = []
    monkeypatch.setattr(finestra, "gioca_amichevole", lambda tuo, avversario, scelte, prima=None: giocate.append((tuo, avversario, scelte, prima)))
    amichevole = (mondo.giocatori[3], mondo.giocatori[10], (3, "fine", "normale"))

    def con_un_amichevole(self):
        self.esiti_della_finestra.amichevole = amichevole
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Staff, "ShowModal", con_un_amichevole)
    finestra.staff()
    assert giocate == [(*amichevole, testi.riepilogo_staff(poli, [], mondo))]


def test_il_suono_della_notizia_dello_staff_all_apertura(finestra, mondo, suonati, monkeypatch):
    mondo.staff_appena_nato = True
    finestra.problemi_all_avvio = False
    finestra.suoni_d_avvio()
    assert suonati == ["avvio", "staff_appena_nato"]
    # Dal collaudo del 23 ottobre 2026 il fischietto arriva un secondo dopo la fine dell'avvio, non subito.
    rinviati = []
    monkeypatch.setattr(suoni, "attesa", lambda: 0.4)
    monkeypatch.setattr(wx, "CallLater", lambda millisecondi, funzione, *argomenti, **opzioni: rinviati.append((millisecondi, argomenti)))
    finestra.suoni_d_avvio()
    assert rinviati == [(1400, ("staff_appena_nato",))]
    rinviati.clear()
    suoni.in_coda("avanzamento")
    assert rinviati == [(int((0.4 + suoni.PAUSA_IN_CODA) * 1000), ("avanzamento",))]


def test_dopo_un_rifiuto_restano_le_cifre_scritte(staff_aperto, mondo, messaggi, suonati, monkeypatch):
    d = staff_aperto
    a = _assumi(mondo, 0)
    _in_finestra(mondo, a)
    d.aggiorna(0, campi=True)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: False)
    offerta = d.stipendio.GetValue() - 10
    d.stipendio.SetValue(offerta)
    d.rinnova()
    assert suonati[-1] == "staff_rinnovo_rifiutato" and d.stipendio.GetValue() == offerta
