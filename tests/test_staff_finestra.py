"""
Le prove della finestra dello staff, tappa 13, decisione D33 e capitolo 4 del progetto, coi dialoghi veri
sul desktop nascosto del conftest e i suoni soltanto registrati: il dialogo dello staff coi tre posti,
l'assunzione dal mercato degli allenatori, accettata e rifiutata, i filtri del mercato, il posto già
occupato, il rinnovo coi tre tentativi, il licenziamento con la buonuscita, le voci del menu e il
riepilogo alla chiusura. Anche le regole del mondo per l'utente: l'offerta e il licenziamento usano una
mossa, il rinnovo no. I messaggi di wx sono sostituiti da un registratore, che risponde come gli si dice.
"""

import datetime
import random

import pytest
import wx

import archivio
import contratti
import mondo as modulo_mondo
import staff
import testi
from costanti import LIMITE_MOVIMENTI_PER_TICK, MESI_DI_INGAGGIO
from gui import dialoghi
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva, probabilita_accettazione
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


@pytest.fixture
def mercato_aperto(app_wx, mondo):
    dialogo = dialoghi.MercatoAllenatori(None, mondo, mondo.miapolisportiva_attiva)
    yield dialogo
    dialogo.Destroy()


@pytest.fixture
def cifra_chiesta(monkeypatch):
    """Il dialogo della cifra risponde con la richiesta dell'allenatore, o con la cifra scritta qui."""
    scelta = {"cifra": None}

    def risponde(self):
        self.valore = scelta["cifra"] if scelta["cifra"] is not None else self.cifra.GetValue()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Cifra, "ShowModal", risponde)
    return scelta


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
    assert "stipendi dello staff 0 euro al mese" in d.info.GetLabel() and "Qualità dello staff 0 su 100" in d.info.GetLabel()
    assert d.previsto.GetValue() == "Posto vuoto: Assumi apre il mercato degli allenatori per questo posto."


def test_le_lettere_dei_dialoghi_dello_staff_non_si_ripetono(staff_aperto, mercato_aperto):
    for d, quante in ((staff_aperto, 10), (mercato_aperto, 10)):
        testi_con_lettera = [c.GetLabel() for c in d.pannello.GetChildren() if "&" in c.GetLabel()]
        lettere = [t[t.index("&") + 1].lower() for t in testi_con_lettera]
        assert len(lettere) == len(set(lettere)) == quante, testi_con_lettera


def test_nessun_pulsante_predefinito(staff_aperto, mercato_aperto):
    # Invio sugli elenchi non fa niente, progetto 4.2, come nei dialoghi della tappa 12.
    for d in (staff_aperto, mercato_aperto):
        assert d.GetDefaultItem() is None


def test_il_mercato_mostra_i_liberi_dal_migliore(mercato_aperto, mondo):
    d = mercato_aperto
    liberi = [a for a in mondo.allenatori.values() if a.libero]
    assert len(d.righe) == len(liberi) == 8
    assert [a.livello for a in d.righe] == sorted(a.livello for a in liberi)
    assert d.etichetta_trovati.GetLabel() == "&Allenatori liberi: 8"
    assert d.trovati.GetString(0) == testi.riga_allenatore(d.righe[0], mondo)
    assert d.posto.GetSelection() == 0 and d.posto.GetString(0) == "Capo, vuoto"
    assert d.info.GetLabel() == f"Club Dello Staff: cassa 50.000 euro, posti vuoti: capo, assistente 1 e assistente 2, mosse rimaste 5 su {LIMITE_MOVIMENTI_PER_TICK}."


def test_i_filtri_del_mercato(mercato_aperto, mondo, suonati):
    d = mercato_aperto
    migliore = d.righe[0]
    d.classe.SetSelection(migliore.livello)
    d.aggiorna(suono="filtro_classe_allenatori")
    assert all(a.livello <= migliore.livello for a in d.righe) and migliore in d.righe
    assert suonati[-1] == "filtro_classe_allenatori"
    d.classe.SetSelection(0)
    sesso = d.righe[0].sesso
    d.sesso.SetSelection(1 if sesso == "m" else 2)
    d.aggiorna()
    assert d.righe and all(a.sesso == sesso for a in d.righe)
    d.sesso.SetSelection(0)
    d.tipo.SetSelection(1)
    d.aggiorna()
    # Gli allenatori della prova sono tutti nati: gli ex giocatori non ci sono, e l'elenco si svuota col suo suono.
    assert d.righe == [] and suonati[-1] == "elenco_svuotato"
    d.tipo.SetSelection(2)
    d.aggiorna()
    assert len(d.righe) == 8 and suonati[-1] == "elenco_ripopolato"
    giovane = min(int(a.eta_anni(ORA)) for a in d.righe)
    d.eta.SetValue(giovane)
    d.aggiorna()
    assert d.righe and all(int(a.eta_anni(ORA)) <= giovane for a in d.righe)


def test_l_ingaggio_accettato(mercato_aperto, mondo, messaggi, suonati, cifra_chiesta, monkeypatch):
    d = mercato_aperto
    poli = mondo.miapolisportiva_attiva
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    a = d.righe[0]
    richiesta = staff.ingaggio_richiesto(a, staff.CAPO, poli)
    assert richiesta == staff.stipendio_richiesto(a, staff.CAPO) * MESI_DI_INGAGGIO
    cassa = poli.cassa
    domanda = testi.domanda_offerta_allenatore(a, poli, 0, richiesta, probabilita_accettazione(richiesta, richiesta), mondo)
    d.trovati.SetSelection(0)
    d.ingaggia()
    assert suonati == ["dialogo_cifra_ingaggio_allenatore", "domanda", "allenatore_assunto"]
    assert messaggi[0] == domanda and domanda.endswith("Userai una delle 5 mosse che ti restano oggi.")
    assert poli.staff[0] == a.numero and a.polisportiva == poli.nome and a.ruolo == staff.CAPO
    assert poli.cassa == cassa - richiesta and mondo.mosse_rimaste(poli) == LIMITE_MOVIMENTI_PER_TICK - 1
    assert messaggi[-1].startswith(f"{testi.nome_completo(a)} ha accettato l'ingaggio di ") and d.esiti == [(messaggi[-1], "assunto")]
    # Il posto è occupato, l'elenco ha un libero in meno, e la scelta del posto lo dice.
    assert len(d.righe) == 7 and d.posto.GetString(0) == f"Capo, occupato da {testi.nome_allenatore(a)}"
    d.trovati.SetSelection(0)
    d.ingaggia()
    assert suonati[-1] == "staff_posto_occupato" and messaggi[-1] == "Quel posto dello staff è già occupato."


def test_l_ingaggio_rifiutato_usa_la_mossa(mercato_aperto, mondo, messaggi, suonati, cifra_chiesta, monkeypatch):
    d = mercato_aperto
    poli = mondo.miapolisportiva_attiva
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: False)
    d.posto.SetSelection(2)
    a = d.righe[0]
    d.trovati.SetSelection(0)
    d.ingaggia()
    assert suonati[-1] == "allenatore_rifiuta" and a.libero and poli.staff == [0, 0, 0]
    assert mondo.mosse_rimaste(poli) == LIMITE_MOVIMENTI_PER_TICK - 1
    assert d.esiti == [(messaggi[-1], "rifiutato")] and "ha rifiutato l'ingaggio di " in messaggi[-1]
    assert f"Rifiuta l'offerta di {poli.nome}, un ingaggio di " in testi.diario_allenatore(a)


def test_senza_mosse_l_offerta_non_si_fa(mercato_aperto, mondo, messaggi, suonati):
    poli = mondo.miapolisportiva_attiva
    poli.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    mercato_aperto.trovati.SetSelection(0)
    mercato_aperto.ingaggia()
    assert suonati == ["mosse_finite"] and "ha finito le mosse di mercato" in messaggi[-1]


def test_dallo_staff_al_mercato_e_ritorno(staff_aperto, mondo, messaggi, suonati, monkeypatch):
    d = staff_aperto
    poli = mondo.miapolisportiva_attiva
    aperti = []

    def mercato_finto(posto):
        aperti.append(posto)
        _assumi(mondo, posto)
        return [("Assunto per prova.", "assunto")]

    monkeypatch.setattr(d, "apri_il_mercato", mercato_finto)
    d.elenco.SetSelection(1)
    d.assumi()
    assert aperti == [1] and d.esiti == [("Assunto per prova.", "assunto")]
    assert d.elenco.GetString(1).startswith(f"Assistente 1: {testi.nome_allenatore(mondo.allenatori[poli.staff[1]])}, ")
    assert d.durata.GetValue() == staff.durata_proposta(mondo.allenatori[poli.staff[1]], ORA)
    d.assumi()
    assert aperti == [1] and suonati[-1] == "staff_posto_occupato" and messaggi[-1].endswith("per cambiarlo, prima licenzia.")


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


def test_scheda_e_diario_dell_allenatore(staff_aperto, mercato_aperto, mondo, suonati, monkeypatch):
    letti = []
    monkeypatch.setattr(dialoghi.Lettura, "ShowModal", lambda self: letti.append((self.GetTitle(), self.testo.GetValue())) or wx.ID_OK)
    staff_aperto.scheda()
    assert suonati == ["nessuna_selezione"] and letti == []
    mercato_aperto.trovati.SetSelection(0)
    a = mercato_aperto.righe[0]
    mercato_aperto.scheda()
    mercato_aperto.diario()
    assert suonati[-2:] == ["scheda_allenatore", "diario_allenatore"]
    assert letti == [(f"Scheda di {testi.nome_completo(a)}", testi.scheda_allenatore(a, mondo)),
                     (f"Diario di {testi.nome_completo(a)}", testi.diario_allenatore(a))]
    assert "Entra nel mondo dello showdown" in letti[1][1]


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

    def un_assunzione(self):
        self.esiti.append(("Assunto per prova.", "assunto"))
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.MercatoAllenatori, "ShowModal", un_assunzione)
    finestra.mercato_allenatori()
    assert "dialogo_mercato_allenatori" in suonati
    assert finestra.vista.GetValue().startswith("Staff di Club Dello Staff: 1 operazione.\nAssunto per prova.\nCapo: nessuno.")
    assert finestra.ultimo_evento == "staff: 1 operazione"


def test_il_suono_della_notizia_dello_staff_all_apertura(finestra, mondo, suonati):
    mondo.staff_appena_nato = True
    finestra.problemi_all_avvio = False
    finestra.suoni_d_avvio()
    assert suonati == ["avvio", "staff_appena_nato"]


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
