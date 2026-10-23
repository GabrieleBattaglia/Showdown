"""
Test della finestra e dei dialoghi, sul desktop nascosto del conftest: ogni voce dei menu, la
barra di stato, il salvataggio, la chiusura con il riepilogo, la scelta del giocatore, la
ricerca, l'aspetto e l'invito al caffè. Le finestre modali vengono sostituite, perché una prova
che aspetta un tasto non finirebbe mai. Dal 2026-10-07 anche i suoni, che il conftest registra
senza suonarli: le prove in fondo controllano che i comandi facciano sentire il loro evento.
Dal 2026-10-23, con la issue 6, la voce Mercato non disponibile a mosse finite, e Ctrl+K che lo dice
lo stesso: il tasto passa davvero dal ciclo di wx e dai tasti rapidi del menu di Windows.
"""

import datetime
import json
import random
from pathlib import Path

import pytest
import wx

import archivio
import impostazioni
import mondo as modulo_mondo
import partita_sonora
import ricerca
import suoni
import testi
from costanti import FILE_MONDO, LIMITE_MOVIMENTI_PER_TICK, VERSIONE
from gui import dialoghi
from gui import finestra as finestra_modulo
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
    # Nessuna finestra modale vera, neppure un messaggio: la prova non avrebbe nessuno che le chiude.
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.NO)
    f = FinestraPrincipale(mondo, archivio.CARICATO, ["Mondo caricato: prova."], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    f.Show()
    yield f
    if f and not f.IsBeingDeleted():
        f.timer.Stop()
        f.Destroy()
    wx.Yield()


def test_apertura_e_barra(finestra):
    assert finestra.vista.GetValue().startswith("MESS, Manageriale e Simulatore Showdown, versione")
    assert "Mondo caricato: prova." in finestra.vista.GetValue()
    righe = finestra.barra.GetValue().splitlines()
    assert len(righe) == 4 and all(len(r) <= 40 for r in righe)
    assert righe[1].startswith("Club Di Prova g")


def test_ogni_voce_dei_menu_che_mostra_un_testo(finestra):
    con_dialogo = {finestra.scheda_giocatore, finestra.diario_giocatore, finestra.cerca, finestra.cambia_aspetto, finestra.cambia_conservazione,
                   finestra.caffe, finestra.esci, finestra.vai_alla_vista, finestra.vai_alla_barra, finestra.nuova_polisportiva,
                   finestra.cambia_polisportiva, finestra.mercato, finestra.svincola, finestra.password_polisportiva, finestra.chiudi_polisportiva,
                   finestra.cambia_effetti, finestra.cambia_velocita, finestra.amichevole, finestra.sala_allenamento, finestra.contratti,
                   # Dalla tappa 12 i dialoghi dei tornei e delle sfide; il ripristino del calendario chiede prima.
                   finestra.lancia_sfida, finestra.sfide_in_arrivo, finestra.storico_sfide, finestra.calendario_tornei, finestra.iscrizioni_tornei,
                   finestra.tornei_in_corso, finestra.albo_d_oro, finestra.editor_modelli, finestra.editor_formule, finestra.ripristina_calendario,
                   # Dalla 1.79.0 gli annunci della cronaca; dalla tappa 13 lo staff e il mercato degli allenatori.
                   finestra.cambia_annunci, finestra.staff, finestra.mercato_allenatori,
                   # Dalla tappa 14 il manuale, che apre il browser e lascia la vista com'era: lo prova test_il_manuale_nel_browser.
                   finestra.manuale,
                   # Dalla tappa 14, issue 4, le voci del PUB, che aprirebbero la posta per davvero: le provano le prove del PUB.
                   finestra.entra_al_pub, finestra.chiedi_aiuto_al_pub,
                   # Dal 23 ottobre 2026 la cartella del mondo, con la finestra di Windows: la provano le prove della cartella.
                   finestra.scegli_la_cartella_del_mondo}
    provate = 0
    for _titolo, voci in finestra.voci_menu():
        for voce in filter(None, voci):
            testo, _tasto, comando = voce
            if comando in con_dialogo:
                continue
            finestra.vista.ChangeValue("")
            finestra._esegui(comando)
            assert finestra.vista.GetValue(), testo
            assert "\n\n" not in finestra.vista.GetValue(), testo
            provate += 1
    # Salva la cronaca, senza un'amichevole nella sessione, lo dice nella vista; dalla tappa 12 c'è anche la classifica mondiale.
    assert provate == 24
    assert finestra.comandi == 24


def test_i_menu_hanno_tasti_e_lettere_non_ripetuti(finestra):
    tasti = [tasto for _t, voci in finestra.voci_menu() for voce in filter(None, voci) if (tasto := voce[1])]
    assert len(tasti) == len(set(tasti))
    for _titolo, voci in finestra.voci_menu():
        lettere = [voce[0][voce[0].index("&") + 1].lower() for voce in filter(None, voci)]
        assert len(lettere) == len(set(lettere)), lettere
    guida = testi.guida(finestra.voci_guida())
    assert "Scheda del giocatore, Ctrl+G" in guida and "Ctrl+Maiusc+N" in guida and "&" not in guida


def test_salva(finestra, cartella_di_prova):
    finestra.salva()
    assert finestra.vista.GetValue().startswith("Mondo salvato: 30 giocatori e 1 polisportiva.")
    assert finestra.ultimo_evento.startswith("salvato alle ")
    assert archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["polisportiva_attiva"] == "Club Di Prova"


def test_chiusura_salva_e_riassume(finestra, cartella_di_prova, monkeypatch):
    riepiloghi = []
    originale = dialoghi.Lettura.__init__

    def registra(self, genitore, titolo, testo, *args, **kwargs):
        riepiloghi.append((titolo, testo))
        originale(self, genitore, titolo, testo, *args, **kwargs)

    monkeypatch.setattr(dialoghi.Lettura, "__init__", registra)
    finestra.Close()
    wx.Yield()
    assert (cartella_di_prova / FILE_MONDO).exists()
    titolo, testo = riepiloghi[0]
    assert titolo == "Fine sessione"
    assert testo.startswith("Sessione di ") and "Mondo salvato:" in testo and testo.endswith("Arrivederci!")
    assert "caffè" not in testo
    assert "Nella sessione il mondo" not in testo


def test_il_timer_fa_avanzare_il_mondo(finestra, cartella_di_prova, monkeypatch):
    finestra.vista.ChangeValue("Il testo che si sta leggendo.")
    mondo = finestra.mondo
    # Una data a metà mese: un primo del mese nei due giorni avrebbe il suo avviso nella barra.
    mondo.datetime_corrente_simulazione = data_prima = datetime.datetime(2026, 10, 10, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=17)
    # Con un dialogo aperto il mondo aspetta.
    finestra._modali = 1
    finestra._al_minuto(None)
    assert mondo.datetime_corrente_simulazione == data_prima
    finestra._modali = 0
    finestra._al_minuto(None)
    assert mondo.datetime_corrente_simulazione == data_prima + datetime.timedelta(days=2)
    assert finestra.ultimo_evento == "mondo avanzato di 2 giorni"
    assert finestra.rapporto["giorni"] == finestra.rapporto_sessione["giorni"] == 2
    assert finestra.vista.GetValue() == "Il testo che si sta leggendo."
    assert archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["data_simulata"] == mondo.datetime_corrente_simulazione.isoformat()
    finestra._al_minuto(None)
    assert finestra.rapporto_sessione["giorni"] == 2
    riepiloghi = []
    originale = dialoghi.Lettura.__init__

    def registra(self, genitore, titolo, testo, *args, **kwargs):
        riepiloghi.append(testo)
        originale(self, genitore, titolo, testo, *args, **kwargs)

    monkeypatch.setattr(dialoghi.Lettura, "__init__", registra)
    finestra.Close()
    wx.Yield()
    assert "Nella sessione il mondo è andato avanti di 2 giorni simulati." in riepiloghi[0]


def test_diario_del_giocatore_e_della_polisportiva(finestra, monkeypatch):
    def scegli(self):
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", scegli)
    finestra.diario_giocatore()
    g = finestra.mondo.giocatori[1]
    assert finestra.vista.GetValue().startswith(f"Diario di {g.nome} {g.cognome}, ID 1: 1 voce, dalla più recente.")
    assert finestra.ultimo_evento == f"diario di {g.nome} {g.cognome}"
    finestra.diario_polisportiva()
    assert finestra.vista.GetValue().startswith("Diario di Club Di Prova: 1 voce, dalla più recente.")
    assert finestra.vista.GetValue().endswith(": Fondata.")


def test_cambia_conservazione(finestra, monkeypatch):
    def scegli(self):
        assert self.giocatori.GetValue() == 0
        self.giocatori.SetValue(60)
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Conservazione, "ShowModal", scegli)
    finestra.cambia_conservazione()
    assert finestra.mondo.conservazione_diari == {"giocatori": 60, "polisportive": 0}
    assert finestra.vista.GetValue().startswith("Le voci dei diari dei giocatori e degli allenatori si conservano per 60 giorni simulati, quelle delle polisportive per sempre.")


def test_scelta_del_giocatore(app_wx, mondo):
    dialogo = dialoghi.SceltaGiocatore(None, mondo)
    try:
        assert dialogo.elenco.GetCount() == 30
        dialogo.campo.ChangeValue("2")
        dialogo.filtra()
        assert dialogo.visibili[0].id == 2
        assert all(str(g.id).startswith("2") for g in dialogo.visibili)
        cognome = mondo.giocatori[7].cognome
        dialogo.campo.ChangeValue(cognome.lower())
        dialogo.filtra()
        assert mondo.giocatori[7] in dialogo.visibili
        dialogo.elenco.SetSelection(dialogo.visibili.index(mondo.giocatori[7]))
        dialogo.conferma()
        assert dialogo.scelto is mondo.giocatori[7]
        assert dialogo.GetReturnCode() == wx.ID_OK
        dialogo.campo.ChangeValue("nessuno si chiama così")
        dialogo.filtra()
        assert dialogo.elenco.GetCount() == 0
    finally:
        dialogo.Destroy()


def test_ricerca(app_wx, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.Ricerca(None)
    try:
        dialogo.valore.ChangeValue("cento")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi == ["Il valore deve essere un numero, per esempio 150 o 12,5."]
        dialogo.valore.ChangeValue("150,5")
        dialogo.conferma()
        assert dialogo.risultato == ("attivi", "valore", "maggiore", 150.5, "i giocatori in attività, valore maggiore di 150,5")
        dialogo.criterio.SetSelection([chiave for chiave, *_resto in ricerca.CRITERI].index("ipovedente"))
        dialogo.al_criterio()
        assert not dialogo.valore.IsEnabled()
        dialogo.condizione.SetSelection(1)
        dialogo.conferma()
        assert dialogo.risultato[1:4] == ("ipovedente", "no", None)
    finally:
        dialogo.Destroy()
    filtro = dialoghi.Ricerca(None, con_ambito=False, titolo="Aggiungi un filtro", pulsante="&Aggiungi")
    try:
        assert filtro.ambito is None
        filtro.criterio.SetSelection([chiave for chiave, *_resto in ricerca.CRITERI].index("sesso"))
        filtro.al_criterio()
        assert not filtro.valore.IsEnabled()
        filtro.condizione.SetSelection(1)
        filtro.conferma()
        assert filtro.risultato == (None, "sesso", "f", None, "sesso donna")
        # La classe si scrive come nella scheda, e la descrizione del filtro la dice allo stesso modo.
        filtro.criterio.SetSelection([chiave for chiave, *_resto in ricerca.CRITERI].index("classe"))
        filtro.al_criterio()
        assert filtro.valore.IsEnabled() and [filtro.condizione.GetString(i) for i in range(filtro.condizione.GetCount())] == ["migliore di", "peggiore di"]
        filtro.valore.ChangeValue("Z9")
        filtro.conferma()
        assert avvisi[-1].startswith("La classe si scrive come nella scheda, per esempio G4")
        filtro.valore.ChangeValue("e0")
        filtro.conferma()
        assert filtro.risultato == (None, "classe", "migliore", 40, "classe migliore di E0")
    finally:
        filtro.Destroy()


def test_aspetto(app_wx):
    dialogo = dialoghi.Aspetto(None, {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50], "volume_effetti": 30})
    try:
        assert dialogo.valori() == impostazioni.valide({"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50], "volume_effetti": 30})
        dialogo.ai_predefiniti()
        # I predefiniti dell'aspetto non toccano il volume degli effetti.
        assert dialogo.valori() == impostazioni.valide({"volume_effetti": 30})
        dialogo.conferma()
        assert dialogo.risultato == impostazioni.valide({"volume_effetti": 30})
    finally:
        dialogo.Destroy()


def test_impostazioni_salvate_e_rilette(cartella_di_prova):
    assert impostazioni.carica() == impostazioni.PREDEFINITE
    assert impostazioni.salva({"dimensione": 30, "colore_testo": [10, 20, 30], "colore_sfondo": [0, 0, 0]})
    assert impostazioni.carica()["dimensione"] == 30
    (cartella_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text(json.dumps({"dimensione": 900, "colore_testo": "rosso"}), encoding="utf-8")
    assert impostazioni.carica() == impostazioni.PREDEFINITE


def test_caffe_invio_chiude(app_wx):
    dialogo = dialoghi.Caffe(None, "Offrimi un caffè, se ti va.")
    try:
        assert dialogo.bottoni[0].GetLabel() == "Dona con &PayPal"
        assert dialogo.bottoni[-1].GetLabel() == "&Chiudi"
        assert dialogo.GetDefaultItem() is dialogo.bottoni[-1]
    finally:
        dialogo.Destroy()


class _Tasto:
    """Un tasto premuto, per _tasto del dialogo: il codice, il controllo da cui parte, e se è una ripetizione."""

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


def _invio_come_wx(dialogo):
    """
    Invio come lo vede wx: il gancio della tastiera di Windows crea wxEVT_CHAR_HOOK sul controllo che
    ha il fuoco, e l'evento sale fino al dialogo. Un WM_KEYDOWN messo in coda con PostMessage non
    passa dal gancio, prova della terza revisione della tappa 14, e SendInput toccherebbe lo schermo vero.
    """
    fuoco = wx.Window.FindFocus()
    bersaglio = fuoco if fuoco is not None and fuoco.GetTopLevelParent() is dialogo else dialogo
    evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
    evento.SetEventObject(bersaglio)
    evento.SetKeyCode(wx.WXK_RETURN)
    bersaglio.GetEventHandler().ProcessEvent(evento)


def test_caffe_invio_nel_testo_chiude_davvero(app_wx, monkeypatch):
    # L'area in sola lettura su più righe, che ha il fuoco, si teneva Invio, e il caffè restava aperto.
    donazioni = []
    monkeypatch.setattr(dialoghi.webbrowser, "open", lambda *a, **k: donazioni.append(a))
    dialogo = dialoghi.Caffe(None, "Offrimi un caffè, se ti va.")
    # Come se l'invito fosse aperto da un po': Invio cade fuori dalla grazia dell'apertura.
    dialogo.ultimo_invio = float("-inf")
    fuoco = []

    def premi():
        dialogo.testo.SetFocus()
        fuoco.append(wx.Window.FindFocus() is dialogo.testo)
        _invio_come_wx(dialogo)

    rete = wx.CallLater(3000, lambda: dialogo.IsModal() and dialogo.EndModal(4242))
    wx.CallAfter(premi)
    try:
        codice = dialogo.ShowModal()
    finally:
        rete.Stop()
        dialogo.Destroy()
    assert fuoco == [True] and codice == wx.ID_OK and donazioni == []


def test_caffe_invio_tenuto_giu_e_sui_pulsanti(app_wx, monkeypatch):
    orologio = [100.0]
    monkeypatch.setattr(dialoghi, "_adesso", lambda: orologio[0])
    dialogo = dialoghi.Caffe(None, "Offrimi un caffè, se ti va.")
    try:
        # L'Invio tenuto giù dalla voce del menu, con NVDA: pressioni nuove, mai ripetute per wx, ogni 30 ms
        # dall'apertura; non chiudono, perché ognuna cade nella grazia della precedente.
        for _ in range(40):
            orologio[0] += 0.03
            tenuto = _Tasto(wx.WXK_RETURN, dialogo.testo)
            dialogo._tasto(tenuto)
            assert tenuto.saltato and dialogo.GetReturnCode() == 0
        # Una ripetizione che wx riconosce non chiude nemmeno lei.
        orologio[0] += 5
        ripetuto = _Tasto(wx.WXK_RETURN, dialogo.testo, ripetuto=True)
        dialogo._tasto(ripetuto)
        assert ripetuto.saltato and dialogo.GetReturnCode() == 0
        # Sul pulsante di PayPal Invio resta suo, e dona soltanto chi lo sceglie.
        orologio[0] += 5
        sul_pulsante = _Tasto(wx.WXK_RETURN, dialogo.bottoni[0])
        dialogo._tasto(sul_pulsante)
        assert sul_pulsante.saltato and dialogo.GetReturnCode() == 0
        dialogo._tasto(_Tasto(wx.WXK_NUMPAD_ENTER, dialogo.testo))
        assert dialogo.GetReturnCode() == wx.ID_OK
        dialogo.SetReturnCode(0)
        dialogo._tasto(_Tasto(wx.WXK_ESCAPE, dialogo.bottoni[0]))
        assert dialogo.GetReturnCode() == wx.ID_OK
    finally:
        dialogo.Destroy()


# Le operazioni delle polisportive, tappa 7.

def _nome(g):
    return f"{g.nome} {g.cognome}"


def test_nuova_polisportiva(finestra, cartella_di_prova, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.NuovaPolisportiva(finestra, finestra.mondo, proposta="Bologna")
    try:
        dialogo.nome.ChangeValue("club di prova")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi[-1] == "Esiste già una polisportiva che si chiama Club Di Prova."
        dialogo.nome.ChangeValue("Circolo dei ciechi")
        dialogo.password.ChangeValue("abc")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi[-1] == "La password e la conferma non coincidono."
        dialogo.conferma_password.ChangeValue("abc")
        dialogo.conferma()
        # Dalla tappa 14 anche la sede, il comune proposto, che basta confermare.
        assert dialogo.risultato == ("Circolo dei ciechi", "abc", True, "Bologna")
    finally:
        dialogo.Destroy()

    def fonda(self):
        self.nome.ChangeValue("Circolo dei ciechi")
        self.sede.SetValue("pescocost")
        self.conferma()
        return wx.ID_OK

    # Il comune scritto a metà: dalla revisione della tappa 14 Fonda chiede prima, e qui si risponde sì.
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo) or wx.YES)
    monkeypatch.setattr(dialoghi.NuovaPolisportiva, "ShowModal", fonda)
    finestra.nuova_polisportiva()
    assert avvisi[-1] == "Vuoi fondare la polisportiva Circolo dei ciechi? Sede: Pescocostanzo, provincia dell'Aquila, Abruzzo."
    nuova = finestra.mondo.polisportive["Circolo dei ciechi"]
    assert finestra.mondo.miapolisportiva_attiva is nuova and not nuova.protetta and nuova.luogo == "Pescocostanzo"
    assert finestra.vista.GetValue().startswith("Hai fondato Circolo dei ciechi. È la tua polisportiva attiva.")
    assert "\nSede: Pescocostanzo, provincia dell'Aquila, Abruzzo\n" in finestra.vista.GetValue()
    assert "Circolo dei ciechi" in archivio.leggi(cartella_di_prova / FILE_MONDO)["mondo"]["polisportive"]


def test_cambia_polisportiva(finestra, monkeypatch):
    mondo = finestra.mondo
    seconda = mondo.fonda_polisportiva("Seconda squadra", attiva=False)
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.CambiaPolisportiva(finestra, mondo)
    try:
        assert dialogo.elenco.GetCount() == 2
        assert dialogo.elenco.GetString(dialogo.elenco.GetSelection()).startswith("Club Di Prova, attiva, 2 tesserati su 15")
        dialogo.conferma()
        assert dialogo.scelta is None and avvisi[-1] == "La password di Club Di Prova non è giusta."
        dialogo.password.ChangeValue("segreta")
        dialogo.conferma()
        assert dialogo.scelta is mondo.polisportive["Club Di Prova"]
    finally:
        dialogo.Destroy()

    def scegli_la_seconda(self):
        self.elenco.SetSelection(1)
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.CambiaPolisportiva, "ShowModal", scegli_la_seconda)
    finestra.cambia_polisportiva()
    assert mondo.miapolisportiva_attiva is seconda
    assert finestra.vista.GetValue().startswith("[TUA] Seconda squadra")


def test_mercato(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: messaggi.append(testo) or wx.YES)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(mondo.datetime_corrente_simulazione)]
    for gid in (10, 11):
        mondo._tessera(cpu, mondo.giocatori[gid])
    mondo.metti_in_vendita(cpu, mondo.giocatori[11], 500)
    dialogo = dialoghi.Mercato(finestra, mondo, poli)
    try:
        liberi = [g for g in mondo.giocatori.values() if g.appartenenza == "*" and not g.ritirato]
        assert len(dialogo.righe) == len(liberi) + 1
        valori = [c.giocatore.indice_collettivo_valore for c in dialogo.righe]
        assert valori == sorted(valori, reverse=True)
        assert dialogo.etichetta_trovati.GetLabel() == f"&Giocatori trovati: {len(liberi) + 1}"
        assert dialogo.elenco_filtri.GetString(0) == "Nessun filtro: compaiono tutti."
        # Dalla issue 7 l'elenco dice, dopo nome e cognome, la classe e l'età completa.
        primo = dialogo.righe[0].giocatore
        assert dialogo.trovati.GetString(0) == testi.riga_mercato(dialogo.righe[0])
        assert dialogo.trovati.GetString(0).startswith(f"{_nome(primo)}, {testi.codice_classe(primo)}, {testi.eta_completa(primo)}, valore ")
        dialogo.scelta.SetSelection(3)
        dialogo.aggiorna()
        assert [c.giocatore.id for c in dialogo.righe] == [10]
        dialogo.scelta.SetSelection(2)
        dialogo.aggiorna()
        assert [c.giocatore.id for c in dialogo.righe] == [11]
        # Chi è in vendita si compra al prezzo chiesto, dopo la conferma.
        dialogo.trovati.SetSelection(0)
        dialogo.offri()
        assert mondo.giocatori[11].appartenenza == poli.nome
        assert messaggi[-2].startswith(f"Comprare {_nome(mondo.giocatori[11])} da {cpu.nome} per 500 euro?")
        assert dialogo.esiti[-1] == (messaggi[-1], True)
        # A un libero si offre l'ingaggio scelto nel dialogo della cifra.
        dialogo.scelta.SetSelection(1)
        dialogo.aggiorna()
        candidato = dialogo.righe[0]

        def ingaggio_chiesto(self):
            self.valore = candidato.costo
            return wx.ID_OK

        monkeypatch.setattr(dialoghi.Cifra, "ShowModal", ingaggio_chiesto)
        dialogo.trovati.SetSelection(0)
        dialogo.offri()
        assert candidato.giocatore.appartenenza == poli.nome
        assert messaggi[-2].startswith(f"Offrire a {_nome(candidato.giocatore)} un ingaggio di ")
        assert messaggi[-1].startswith(f"{_nome(candidato.giocatore)} ha accettato l'ingaggio di ")
        assert dialogo.info.GetLabel().startswith(f"Club Di Prova: cassa {testi.euro(poli.cassa)}, gloria 100, tesserati 4 su 15, mosse rimaste 3 su 5.")
    finally:
        dialogo.Destroy()

    def cento_euro(self):
        self.valore = 100
        return wx.ID_OK

    def un_offerta(self):
        self.trovati.SetSelection(0)
        self.offri()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Cifra, "ShowModal", cento_euro)
    monkeypatch.setattr(dialoghi.Mercato, "ShowModal", un_offerta)
    finestra.mercato()
    assert finestra.vista.GetValue().startswith("Mercato di Club Di Prova: 1 offerta, 1 riuscita.")
    assert finestra.ultimo_evento == "mercato: 1 offerta"


def test_cifra(app_wx, monkeypatch):
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo))
    dialogo = dialoghi.Cifra(None, "Ingaggio", "Spiegazione.", "&Ingaggio", 500, 300, lambda cifra: f"Nota per {cifra}.")
    try:
        assert dialogo.cifra.GetValue() == 300 and dialogo.cifra.GetMax() == 300
        assert dialogo.nota.GetLabel() == "Nota per 300."
        dialogo.cifra.SetValue(0)
        dialogo.conferma()
        assert dialogo.valore is None and avvisi == ["La cifra deve essere di almeno 1 euro."]
        dialogo.cifra.SetValue(120)
        dialogo.conferma()
        assert dialogo.valore == 120
    finally:
        dialogo.Destroy()


def test_arretrati_e_vendite(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    g = mondo.giocatori[2]
    g.arretrati = 300
    g.pazienza = 40.
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)

    def paga_tutto(self):
        assert self.debitori == [g] and self.cifra.GetValue() == 300
        self.paga()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.PagaArretrati, "ShowModal", paga_tutto)
    finestra.paga_arretrati()
    assert g.arretrati == 0 and poli.cassa == 20_000 - 300
    assert finestra.vista.GetValue().startswith(f"Pagati 300 euro a {_nome(g)}.")
    finestra.paga_arretrati()
    assert finestra.vista.GetValue().startswith("Nessun tesserato di Club Di Prova aspetta arretrati.")

    def vendi_il_primo(self):
        self.prezzo.SetValue(1500)
        self.metti()
        return wx.ID_CANCEL

    monkeypatch.setattr(dialoghi.Vendite, "ShowModal", vendi_il_primo)
    finestra.vendite()
    primo = max((mondo.giocatori[gid] for gid in poli.tesserati), key=lambda x: x.indice_collettivo_valore)
    assert poli.in_vendita == {primo.id: 1500}
    assert finestra.vista.GetValue() == f"{_nome(primo)} è in vendita a 1.500 euro."
    finestra.bilancio()
    assert finestra.vista.GetValue().startswith(f"Bilancio di Club Di Prova: in cassa {testi.euro(poli.cassa)}.")


def test_avviso_degli_stipendi_non_pagati(finestra):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    poli.cassa = 0
    poli.gloria = 1
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 31, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    finestra._al_minuto(None)
    assert mondo.datetime_corrente_simulazione.day == 1
    assert finestra.ultimo_evento == "stipendi non pagati, vedi il bilancio"
    assert finestra.barra.GetValue().splitlines()[3] == "stipendi non pagati, vedi il bilancio"


def test_svincolo(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva

    def scegli(self):
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.SceltaGiocatore, "ShowModal", scegli)
    finestra.svincola()
    assert poli.tesserati == [2, 5]
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.YES)
    finestra.svincola()
    assert poli.tesserati == [5] and mondo.giocatori[2].appartenenza == "*"
    assert finestra.vista.GetValue().startswith(f"{_nome(mondo.giocatori[2])} è svincolat")


def test_password_e_chiusura(finestra, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    avvisi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: avvisi.append(testo) or wx.YES)
    dialogo = dialoghi.PasswordPolisportiva(finestra, poli)
    try:
        dialogo.attuale.ChangeValue("sbagliata")
        dialogo.conferma()
        assert dialogo.risultato is None and avvisi[-1] == "La password attuale non è giusta."
        dialogo.attuale.ChangeValue("segreta")
        dialogo.conferma()
        assert dialogo.risultato == ""
    finally:
        dialogo.Destroy()
    # Chiudere una polisportiva protetta chiede la password: senza, non succede nulla.
    finestra.chiudi_polisportiva()
    assert "Club Di Prova" in mondo.polisportive

    def togli(self):
        self.attuale.ChangeValue("segreta")
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.PasswordPolisportiva, "ShowModal", togli)
    finestra.password_polisportiva()
    assert not poli.protetta
    assert finestra.vista.GetValue() == "Club Di Prova non è protetta da password."
    finestra.chiudi_polisportiva()
    assert "Club Di Prova" not in mondo.polisportive and mondo.miapolisportiva_attiva is None
    assert finestra.vista.GetValue().startswith("Club Di Prova ha chiuso per sempre: 2 giocatori tornano liberi.")
    assert mondo.giocatori[2].appartenenza == "*"
    finestra.mercato()
    assert finestra.vista.GetValue().startswith("Non hai una polisportiva attiva")


def test_chiudere_una_protetta_con_la_password(finestra, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.YES)

    def giusta(self):
        self.password.ChangeValue("segreta")
        self.conferma()
        return self.GetReturnCode()

    monkeypatch.setattr(dialoghi.ChiediPassword, "ShowModal", giusta)
    finestra.chiudi_polisportiva()
    assert "Club Di Prova" not in finestra.mondo.polisportive


# Gli effetti sonori, decisione D24: il conftest li registra senza suonarli.

def _guasto(*_args):
    raise OSError("disco pieno")


def test_i_comandi_suonano_il_loro_evento(finestra, suonati):
    voci = {voce[0]: voce[2] for _titolo, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    for testo in ("&Guida ai comandi", "&Informazioni", "&Novità", "&TOP 10", "&Classifica per valore", "Vista &principale", "&Barra di stato",
                  "R&isultati della ricerca", "&Riepilogo dell'ultimo avanzamento", "&Scheda della polisportiva attiva", "&Bilancio della polisportiva attiva",
                  "&Tesserati della polisportiva attiva", "&Elenco delle polisportive", "&Vecchie glorie"):
        finestra._esegui(voci[testo])
    assert suonati == ["guida", "informazioni", "novita", "top_10", "classifica", "fuoco_vista", "fuoco_barra", "nessuna_ricerca", "nessun_avanzamento",
                       "scheda_polisportiva", "bilancio", "tesserati_polisportiva", "elenco_polisportive", "vecchie_glorie"]
    finestra.mondo.miapolisportiva_attiva = None
    finestra._esegui(voci["&Tesserati della polisportiva attiva"])
    assert suonati[-1] == "nessuna_polisportiva_attiva"
    assert finestra.vista.GetValue().startswith("Non hai una polisportiva attiva: fondane una con Ctrl+N")


def test_annullare_un_dialogo_suona(finestra, suonati):
    finestra.scheda_giocatore()
    finestra.cerca()
    finestra.cambia_aspetto()
    finestra.cambia_effetti()
    finestra.cambia_velocita()
    finestra.cambia_annunci()
    assert suonati == ["dialogo_scheda_giocatore", "annullato", "dialogo_ricerca", "annullato", "dialogo_aspetto", "annullato", "dialogo_effetti_sonori", "annullato",
                       "dialogo_velocita_di_gioco", "annullato", "dialogo_annunci_cronaca", "annullato"]


def test_gli_annunci_della_cronaca(finestra, suonati, monkeypatch, cartella_di_prova):
    # 1.79.0, coi predefiniti di Gabriele: lettura automatica accesa, alla sintesi automatica e al braille, display di 40 celle.
    voci = {voce[0]: voce for _t, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    assert voci["A&nnunci della cronaca..."][1] is None
    predefinite = impostazioni.carica()
    assert (predefinite["annunci_cronaca"], predefinite["annunci_dove"], predefinite["annunci_sintesi"], predefinite["annunci_celle"],
            predefinite["annunci_lettura_minima"]) == (True, "entrambi", "automatica", 40, 2000)

    def mostra(self):
        assert self.leggi.GetValue() and self.dove.GetStringSelection() == "alla sintesi e al braille"
        assert self.sintesi.GetStringSelection().startswith("automatica") and self.celle.GetValue() == 40 and self.lettura.GetValue() == 2000
        assert (self.celle.GetMin(), self.celle.GetMax()) == (0, impostazioni.CELLE_MASSIME)
        self.leggi.SetValue(False)
        self.dove.SetSelection(2)
        self.sintesi.SetSelection(2)
        self.celle.SetValue(20)
        self.lettura.SetValue(1500)
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.AnnunciDellaCronaca, "ShowModal", mostra)
    finestra.cambia_annunci()
    assert suonati == ["dialogo_annunci_cronaca", "annunci_cronaca_salvati"]
    salvate = impostazioni.carica()
    assert (salvate["annunci_cronaca"], salvate["annunci_dove"], salvate["annunci_sintesi"], salvate["annunci_celle"], salvate["annunci_lettura_minima"]) == (
        False, "braille", "jaws", 20, 1500)
    assert finestra.ultimo_evento == "annunci della cronaca spenti"


def test_le_impostazioni_degli_annunci_si_controllano():
    # Valori fuori dalle scelte o dai limiti tornano ai predefiniti.
    valide = impostazioni.valide({"annunci_cronaca": "sì", "annunci_dove": "altrove", "annunci_sintesi": "festival", "annunci_celle": 161,
                                  "annunci_lettura_minima": 50})
    assert (valide["annunci_cronaca"], valide["annunci_dove"], valide["annunci_sintesi"], valide["annunci_celle"], valide["annunci_lettura_minima"]) == (
        True, "entrambi", "automatica", 40, 2000)
    valide = impostazioni.valide({"annunci_cronaca": False, "annunci_dove": "sintesi", "annunci_sintesi": "sapi5", "annunci_celle": 0,
                                  "annunci_lettura_minima": 60_000})
    assert (valide["annunci_cronaca"], valide["annunci_dove"], valide["annunci_sintesi"], valide["annunci_celle"], valide["annunci_lettura_minima"]) == (
        False, "sintesi", "sapi5", 0, 60_000)


def test_la_velocita_di_gioco(finestra, suonati, monkeypatch, cartella_di_prova):
    # Sul modello di Terminal Beast: un numero solo, che si salva nelle impostazioni e vale per tutte le partite dal vivo.
    def scegli(velocita):
        def mostra(self):
            assert self.velocita.GetValue() == finestra.impostazioni["velocita_gioco"]
            assert (self.velocita.GetMin(), self.velocita.GetMax()) == (impostazioni.VELOCITA_MINIMA, impostazioni.VELOCITA_MASSIMA)
            self.velocita.SetValue(velocita)
            self.conferma()
            return wx.ID_OK
        return mostra

    voci = {voce[0]: voce for _t, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    assert voci["&Velocità di gioco..."][1] is None
    # Decisione D30: chi non l'ha mai scelta parte da 4.
    assert impostazioni.carica()["velocita_gioco"] == 4 == impostazioni.VELOCITA_PREDEFINITA
    monkeypatch.setattr(dialoghi.VelocitaDiGioco, "ShowModal", scegli(6))
    finestra.cambia_velocita()
    assert suonati == ["dialogo_velocita_di_gioco", "velocita_di_gioco_salvata"]
    assert impostazioni.carica()["velocita_gioco"] == 6 and finestra.impostazioni["velocita_gioco"] == 6
    assert finestra.ultimo_evento == "velocità di gioco 6"
    # Un file che non si scrive lo dice la barra, e la velocità vale comunque per la sessione.
    monkeypatch.setattr(impostazioni, "salva", lambda _impostazioni: False)
    monkeypatch.setattr(dialoghi.VelocitaDiGioco, "ShowModal", scegli(8))
    finestra.cambia_velocita()
    assert suonati[-1] == "impostazioni_non_salvate" and finestra.ultimo_evento == "velocità di gioco non salvata"
    assert finestra.impostazioni["velocita_gioco"] == 8


@pytest.mark.parametrize(("valore", "letto"), [(1, 1), (8, 8), (5, 5), (0, 4), (9, 4), (True, 4), ("3", 4), (2.5, 4), (None, 4)])
def test_la_velocita_si_valida(valore, letto):
    assert impostazioni.valide({"velocita_gioco": valore})["velocita_gioco"] == letto


def test_la_velocita_gia_salvata_resta_com_era(cartella_di_prova):
    # Decisione D30: il 4 vale per chi non ha mai salvato la velocità; chi l'ha salvata la ritrova.
    (cartella_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text('{"dimensione": 14, "velocita_gioco": 1}', encoding="utf-8")
    assert impostazioni.carica()["velocita_gioco"] == 1
    (cartella_di_prova / impostazioni.FILE_IMPOSTAZIONI).write_text('{"dimensione": 14}', encoding="utf-8")
    letto = impostazioni.carica()
    assert letto["velocita_gioco"] == 4 and letto["dimensione"] == 14
    assert impostazioni.valide(None)["velocita_gioco"] == 4


@pytest.mark.parametrize(("origine", "avvisi", "atteso"), [
    (archivio.CARICATO, False, "avvio"), (archivio.NATO, False, "avvio_mondo_nuovo"), (archivio.DALLA_COPIA, True, "avvio_dalla_copia"),
    (archivio.CARICATO, True, "avvio_con_avvisi"), (archivio.NATO, True, "avvio_con_avvisi"),
])
def test_il_suono_dell_avvio(app_wx, mondo, suonati, origine, avvisi, atteso):
    rapporto = Mondo.rapporto_vuoto(adesso()) | {"ticks": 3, "giorni": 3}
    f = FinestraPrincipale(mondo, origine, [], rapporto, mondo.datetime_ultimo_run_reale, avvisi_all_avvio=avvisi)
    try:
        f.suoni_d_avvio()
        if origine == archivio.NATO:
            # Il mondo appena nato avanza subito di un giorno, e quel giorno non suona.
            assert suonati == [atteso]
            assert f.ultimo_evento == "mondo pronto"
        else:
            assert suonati == [atteso, "mondo_avanzato_piu_giorni"]
            assert f.ultimo_evento == "mondo avanzato di 3 giorni"
    finally:
        f.timer.Stop()
        f.Destroy()
        wx.Yield()


def test_i_tre_esiti_del_salvataggio(finestra, suonati, monkeypatch):
    finestra.salva()
    scrivi = archivio.scrivi
    monkeypatch.setattr(archivio, "scrivi", lambda *args: (scrivi(*args)[0], ["La copia di sicurezza non si è potuta aggiornare: prova."]))
    finestra.salva()
    assert "La copia di sicurezza non si è potuta aggiornare: prova." in finestra.vista.GetValue()
    monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra.salva()
    assert suonati == ["salvataggio_riuscito", "salvataggio_con_avviso", "salvataggio_non_riuscito"]
    assert finestra.ultimo_evento == "salvataggio non riuscito"


def test_un_operazione_che_non_si_salva(finestra, suonati, monkeypatch):
    def fonda(self):
        self.nome.ChangeValue("Circolo dei ciechi")
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.NuovaPolisportiva, "ShowModal", fonda)
    monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra.nuova_polisportiva()
    assert suonati == ["dialogo_nuova_polisportiva", "polisportiva_fondata", "salvataggio_non_riuscito"]
    assert finestra.vista.GetValue().startswith("Hai fondato Circolo dei ciechi.")
    assert finestra.vista.GetValue().endswith("Salvataggio non riuscito: disco pieno. Il salvataggio precedente è rimasto com'era.")


def test_l_avanzamento_suona_una_volta_sola(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 10, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    finestra._modali = 1
    finestra._al_minuto(None)
    assert suonati == []
    finestra._modali = 0
    finestra._al_minuto(None)
    evento, testo = suoni.evento_avanzamento(finestra.rapporto, True, True)
    assert suonati == [evento]
    assert finestra.ultimo_evento == testo
    assert finestra.barra.GetValue().splitlines()[3] == testo
    # Senza giorni maturati il timer tace.
    finestra._al_minuto(None)
    assert suonati == [evento]
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra._al_minuto(None)
    assert suonati == [evento, "salvataggio_non_riuscito"]
    assert finestra.ultimo_evento == "mondo avanzato di un giorno, non salvato"


def test_gli_stipendi_non_pagati_suonano(finestra, suonati):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    poli.cassa = 0
    poli.gloria = 1
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 31, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=9)
    finestra._al_minuto(None)
    assert finestra.rapporto["mesi"] == 1
    assert suonati == ["stipendi_non_pagati"]


@pytest.mark.parametrize(("guasto", "atteso"), [(False, "uscita"), (True, "uscita_senza_salvataggio")])
def test_l_uscita_aspetta_il_suo_suono(finestra, suonati, monkeypatch, guasto, atteso):
    if guasto:
        monkeypatch.setattr(archivio, "scrivi", _guasto)
    finestra.Close()
    wx.Yield()
    assert suonati == [atteso]
    assert suonati.dettagli[0]["sync"] == suoni.ATTESA_USCITA


def test_l_elenco_che_si_svuota_e_si_riempie(app_wx, mondo, suonati):
    dialogo = dialoghi.SceltaGiocatore(None, mondo)
    try:
        dialogo.campo.ChangeValue("2")
        dialogo.filtra()
        dialogo.campo.ChangeValue("zzzz")
        dialogo.filtra()
        dialogo.campo.ChangeValue("zzzzz")
        dialogo.filtra()
        dialogo.campo.ChangeValue("")
        dialogo.filtra()
        dialogo.campo.ChangeValue("zzzz")
        dialogo.filtra()
        dialogo.conferma()
        assert suonati == ["elenco_svuotato", "elenco_ripopolato", "elenco_svuotato", "nessuna_selezione"]
        assert dialogo.scelto is None
    finally:
        dialogo.Destroy()


def test_i_suoni_delle_password(finestra, suonati, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    dialogo = dialoghi.PasswordPolisportiva(finestra, finestra.mondo.miapolisportiva_attiva)
    try:
        dialogo.attuale.ChangeValue("sbagliata")
        dialogo.conferma()
        dialogo.attuale.ChangeValue("segreta")
        dialogo.nuova.ChangeValue("nuova")
        dialogo.conferma()
    finally:
        dialogo.Destroy()
    nuova = dialoghi.NuovaPolisportiva(finestra, finestra.mondo)
    try:
        nuova.nome.ChangeValue("x")
        nuova.conferma()
    finally:
        nuova.Destroy()
    assert suonati == ["password_sbagliata", "password_non_coincidono", "campo_da_correggere"]


def test_i_suoni_del_mercato(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.YES)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: False)
    valori = ["1000000", "0"]

    def filtro(self):
        self.valore.ChangeValue(valori.pop(0))
        self.conferma()
        return wx.ID_OK

    def cifra(self):
        self.valore = self.cifra.GetValue()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Ricerca, "ShowModal", filtro)
    monkeypatch.setattr(dialoghi.Cifra, "ShowModal", cifra)
    dialogo = dialoghi.Mercato(finestra, mondo, poli)
    try:
        assert suonati == []
        dialogo.scelta.SetSelection(2)
        dialogo.aggiorna(suono="mercato_scelta_cambiata")
        dialogo.ordine.SetSelection(1)
        dialogo.aggiorna(suono="mercato_ordine_cambiato")
        dialogo.scelta.SetSelection(1)
        dialogo.aggiorna(suono="mercato_scelta_cambiata")
        dialogo.togli_tutti()
        # Un filtro che non lascia nessuno suona come l'elenco che si svuota, e toglierlo come l'elenco che torna pieno.
        dialogo.aggiungi_filtro()
        dialogo.togli_filtro()
        dialogo.aggiungi_filtro()
        dialogo.togli_tutti()
        dialogo.trovati.SetSelection(0)
        dialogo.offri()
        assert suonati == ["elenco_svuotato", "mercato_ordine_cambiato", "elenco_ripopolato", "nessuna_selezione",
                           "dialogo_filtro_mercato", "elenco_svuotato", "elenco_ripopolato", "dialogo_filtro_mercato", "filtro_aggiunto", "filtri_tutti_tolti",
                           "dialogo_cifra_ingaggio", "domanda", "ingaggio_rifiutato"]
        poli.movimenti_oggi = 5
        dialogo.offri()
        assert suonati[-1] == "mosse_finite"
        poli.cassa = 0
        dialogo.offri()
        assert suonati[-1] == "cassa_insufficiente"
    finally:
        dialogo.Destroy()


def test_il_mercato_che_si_apre_vuoto(finestra, suonati, monkeypatch):
    monkeypatch.setattr(dialoghi.mercato, "candidati", lambda *a, **k: [])
    finestra.mercato()
    assert suonati == ["dialogo_mercato", "elenco_svuotato", "lavoro_concluso"]


# La voce Mercato a mosse finite, issue 6 di Gabriele: non disponibile, e Ctrl+K lo dice lo stesso.

MF_BYCOMMAND, MF_GRAYED = 0x0, 0x1
WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
VK_K, VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN = 0x4B, 0x10, 0x11, 0x12, 0x5B, 0x5C
VK_LSHIFT, VK_RSHIFT, VK_LCONTROL, VK_RCONTROL, VK_LMENU, VK_RMENU = 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5
# Ctrl+K vuole il solo Ctrl sinistro giù: Maiuscolo, Alt e i tasti di Windows su, o il tasto rapido non corrisponde.
MODIFICATORI_DI_CTRL_K = {VK_CONTROL: True, VK_LCONTROL: True, VK_RCONTROL: False, VK_SHIFT: False, VK_LSHIFT: False, VK_RSHIFT: False,
                          VK_MENU: False, VK_LMENU: False, VK_RMENU: False, VK_LWIN: False, VK_RWIN: False}


def _user32_dei_tasti():
    """ctypes e user32 con le firme che servono a premere un tasto dentro il processo e a leggere i menu di Windows, in una copia tutta sua."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetKeyboardState.restype = wintypes.BOOL
    user32.GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    user32.SetKeyboardState.restype = wintypes.BOOL
    user32.SetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.MapVirtualKeyW.restype = wintypes.UINT
    user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    user32.GetMenu.restype = wintypes.HMENU
    user32.GetMenu.argtypes = [wintypes.HWND]
    user32.GetMenuState.restype = wintypes.UINT
    user32.GetMenuState.argtypes = [wintypes.HMENU, wintypes.UINT, wintypes.UINT]
    return ctypes, user32


def _grigia_per_windows(finestra, voce):
    """
    Vero se nel menu di Windows della finestra la voce è grigia, cioè non disponibile, come la legge NVDA.
    Windows conosce la voce col numero di wx ridotto a 16 bit, come in wxMenuItem::GetMSWId.
    """
    _ctypes, user32 = _user32_dei_tasti()
    stato = user32.GetMenuState(user32.GetMenu(finestra.GetHandle()), voce.GetId() & 0xFFFF, MF_BYCOMMAND)
    assert stato != 0xFFFFFFFF, "la voce non è nel menu di Windows"
    return bool(stato & MF_GRAYED)


def _svuota_la_coda():
    """Fa elaborare al ciclo di wx i messaggi in coda, tasti rapidi dei menu compresi, come il ciclo del programma."""
    ciclo = wx.EventLoopBase.GetActive()
    attivatore = None
    if ciclo is None:
        ciclo = wx.GUIEventLoop()
        attivatore = wx.EventLoopActivator(ciclo)
    applicazione = wx.GetApp()
    try:
        for _ in range(500):
            if ciclo.Pending():
                ciclo.Dispatch()
            elif applicazione.HasPendingEvents():
                applicazione.ProcessPendingEvents()
            else:
                break
    finally:
        del attivatore


def _ctrl_k(finestra, gancio=True):
    """
    Ctrl+K nella vista principale come la tastiera vera, sul desktop nascosto. Se gancio è vero, prima
    l'evento wxEVT_CHAR_HOOK che il gancio dei tasti di wx crea per un tasto vero, e che sale fino alla
    finestra: se un gestore lo tiene, senza Skip, wx butta il tasto, e qui finisce. Poi Ctrl e K giù per
    il filo, con SetKeyboardState, e WM_KEYDOWN della K messo in coda con PostMessage: il ciclo di wx lo
    passa ai tasti rapidi del menu, come il tasto vero. Il gancio va rifatto perché Windows lo chiama
    soltanto per i tasti veri, e SendInput li manderebbe allo schermo vero.
    """
    ctypes, user32 = _user32_dei_tasti()
    if gancio:
        evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
        evento.SetEventObject(finestra.vista)
        evento.SetKeyCode(ord("K"))
        evento.SetControlDown(True)
        if finestra.vista.GetEventHandler().ProcessEvent(evento) and not evento.IsNextEventAllowed():
            return
    prima = (ctypes.c_ubyte * 256)()
    user32.GetKeyboardState(prima)
    stato = (ctypes.c_ubyte * 256)(*prima)
    for codice, giu in MODIFICATORI_DI_CTRL_K.items():
        stato[codice] = 0x80 if giu else 0
    stato[VK_K] = 0x80
    lparam = 1 | ((user32.MapVirtualKeyW(VK_K, 0) & 0xFF) << 16)
    hwnd = finestra.vista.GetHandle()
    try:
        user32.SetKeyboardState(stato)
        user32.PostMessageW(hwnd, WM_KEYDOWN, VK_K, lparam)
        _svuota_la_coda()
        stato[VK_K] = 0
        user32.SetKeyboardState(stato)
        user32.PostMessageW(hwnd, WM_KEYUP, VK_K, lparam | (1 << 30) | (1 << 31))
        _svuota_la_coda()
    finally:
        user32.SetKeyboardState(prima)


def _apri_il_menu(finestra, voce):
    """L'apertura del menu della voce, come la dice wx quando Windows lo prepara."""
    finestra.GetEventHandler().ProcessEvent(wx.MenuEvent(wx.wxEVT_MENU_OPEN, 0, voce.GetMenu()))


def test_la_voce_del_mercato_segue_le_mosse(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    voce = finestra.voci_del_menu[finestra.mercato]
    assert voce.IsEnabled() and not _grigia_per_windows(finestra, voce)
    # Le mosse finite: alla fine di un comando qualunque la voce non è disponibile, e Windows la dà grigia.
    poli.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    finestra._esegui(finestra.bilancio)
    assert not voce.IsEnabled() and _grigia_per_windows(finestra, voce)
    # Il comando dice che le mosse sono finite, col loro suono, e il dialogo non si apre.
    suonati.clear()
    finestra.mercato()
    assert finestra.vista.GetValue() == "Per oggi Club Di Prova ha finito le mosse di mercato."
    assert suonati == ["mosse_finite"] and finestra.ultimo_evento == "nessuna mossa"
    # Lo svincolo, che usa anche lui una mossa, lo dice con le stesse parole.
    finestra.vista.ChangeValue("")
    finestra.svincola()
    assert finestra.vista.GetValue() == "Per oggi Club Di Prova ha finito le mosse di mercato." and suonati == ["mosse_finite", "mosse_finite"]
    # Un'altra polisportiva attiva, che ha le sue mosse: la voce torna disponibile.
    seconda = mondo.fonda_polisportiva("Seconda squadra", attiva=False)

    def scegli_la_seconda(self):
        self.elenco.SetSelection(1)
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.CambiaPolisportiva, "ShowModal", scegli_la_seconda)
    finestra._esegui(finestra.cambia_polisportiva)
    assert mondo.miapolisportiva_attiva is seconda and voce.IsEnabled()
    # All'apertura del menu la voce si rimette in pari anche senza un comando.
    mondo.miapolisportiva_attiva = poli
    _apri_il_menu(finestra, voce)
    assert not voce.IsEnabled()
    # Senza polisportiva attiva la voce resta disponibile, e il comando lo dice come sempre.
    mondo.miapolisportiva_attiva = None
    _apri_il_menu(finestra, voce)
    assert voce.IsEnabled()
    mondo.miapolisportiva_attiva = poli
    _apri_il_menu(finestra, voce)
    assert not voce.IsEnabled()
    # Il giorno nuovo rende le mosse: col mondo che avanza la voce torna disponibile.
    mondo.datetime_corrente_simulazione = datetime.datetime(2026, 10, 10, 12, 0)
    mondo.datetime_ultimo_run_reale = adesso_utc() - datetime.timedelta(hours=17)
    finestra._al_minuto(None)
    assert mondo.mosse_rimaste(poli) == LIMITE_MOVIMENTI_PER_TICK and voce.IsEnabled() and not _grigia_per_windows(finestra, voce)


def test_la_voce_del_mercato_all_apertura(app_wx, mondo):
    # Il mondo caricato con le mosse già finite: la voce non è disponibile da subito.
    mondo.miapolisportiva_attiva.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    f = FinestraPrincipale(mondo, archivio.CARICATO, [], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale)
    try:
        assert not f.voci_del_menu[f.mercato].IsEnabled()
    finally:
        f.timer.Stop()
        f.Destroy()
        wx.Yield()


def test_ctrl_k_a_mosse_finite_sul_desktop_nascosto(finestra, suonati):
    poli = finestra.mondo.miapolisportiva_attiva
    voce = finestra.voci_del_menu[finestra.mercato]
    # Con le mosse il gancio lascia passare Ctrl+K, che arriva al tasto rapido del menu: il mercato si apre.
    # Nel ciclo di wx può scattare anche il suono in coda di una prova di prima: si guarda che ci sia quello del mercato.
    comandi = finestra.comandi
    _ctrl_k(finestra)
    assert "dialogo_mercato" in suonati and finestra.comandi == comandi + 1, (list(suonati), finestra.comandi - comandi)
    # Come tratta Windows il tasto rapido di una voce disattivata: lo prende e non manda il comando.
    # Senza il gancio della finestra Ctrl+K a mosse finite resterebbe muto.
    poli.movimenti_oggi = LIMITE_MOVIMENTI_PER_TICK
    finestra.aggiorna_le_voci()
    assert not voce.IsEnabled()
    suonati.clear()
    finestra.vista.ChangeValue("Il testo di prima.")
    comandi = finestra.comandi
    _ctrl_k(finestra, gancio=False)
    assert finestra.comandi == comandi and finestra.vista.GetValue() == "Il testo di prima.", (list(suonati), finestra.vista.GetValue())
    assert "mosse_finite" not in suonati and "dialogo_mercato" not in suonati, list(suonati)
    # Col gancio, come col tasto vero, la vista dice che le mosse sono finite, col loro suono.
    suonati.clear()
    _ctrl_k(finestra)
    assert finestra.vista.GetValue() == "Per oggi Club Di Prova ha finito le mosse di mercato."
    assert suonati == ["mosse_finite"] and finestra.comandi == comandi + 1
    # La voce rimasta indietro si rimette in pari prima del tasto: disponibile senza mosse, Ctrl+K dice lo stesso che sono finite.
    voce.Enable(True)
    suonati.clear()
    _ctrl_k(finestra)
    assert suonati == ["mosse_finite"] and not voce.IsEnabled()
    # Non disponibile con le mosse tornate: Windows apre il menu per finta prima di guardare la voce, e la trova
    # già disponibile; il mercato si apre anche senza il gancio.
    poli.movimenti_oggi = 0
    suonati.clear()
    comandi = finestra.comandi
    _ctrl_k(finestra, gancio=False)
    assert "dialogo_mercato" in suonati and voce.IsEnabled() and finestra.comandi == comandi + 1, (list(suonati), voce.IsEnabled())


def test_i_tre_esiti_del_pagamento(finestra, suonati, monkeypatch):
    mondo = finestra.mondo
    poli = mondo.miapolisportiva_attiva
    primo, secondo = mondo.giocatori[2], mondo.giocatori[5]
    primo.arretrati, secondo.arretrati = 300, 200
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    dialogo = dialoghi.PagaArretrati(finestra, mondo, poli)

    def scegli(g, cifra=None):
        dialogo.elenco.SetSelection(dialogo.debitori.index(g))
        dialogo.al_giocatore()
        if cifra is not None:
            dialogo.cifra.SetValue(cifra)
        dialogo.paga()

    try:
        scegli(primo, 100)
        scegli(primo)
        scegli(secondo)
        dialogo.paga()
        assert suonati == ["arretrati_pagati_in_parte", "arretrati_saldati", "arretrati_tutti_saldati", "nessuna_selezione"]
        secondo.arretrati = 50
        poli.cassa = 0
        dialogo.aggiorna()
        dialogo.paga()
        assert suonati[-1] == "cassa_insufficiente"
    finally:
        dialogo.Destroy()


def test_i_suoni_delle_vendite(finestra, suonati, monkeypatch):
    monkeypatch.setattr(wx, "MessageBox", lambda *a, **k: wx.OK)
    dialogo = dialoghi.Vendite(finestra, finestra.mondo, finestra.mondo.miapolisportiva_attiva)
    try:
        dialogo.metti()
        dialogo.metti()
        dialogo.togli()
        dialogo.togli()
    finally:
        dialogo.Destroy()
    assert suonati == ["messo_in_vendita", "prezzo_di_vendita_cambiato", "tolto_dalla_vendita", "vendita_non_attiva"]


def test_il_volume_degli_effetti(finestra, suonati, monkeypatch, cartella_di_prova):
    def scegli(volume, volume_partita=None):
        def mostra(self):
            assert self.volume_partita.GetValue() == finestra.impostazioni["volume_partita"]
            self.volume.SetValue(volume)
            self.prova()
            if volume_partita is not None:
                self.volume_partita.SetValue(volume_partita)
                self.prova_partita()
            self.conferma()
            return wx.ID_OK
        return mostra

    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(80))
    finestra.cambia_effetti()
    assert suonati == ["dialogo_effetti_sonori", "prova_volume_effetti", "effetti_sonori_applicati"]
    assert [d["fattore"] for d in suonati.dettagli] == [1.0, 1.6, 1.6]
    assert impostazioni.carica()["volume_effetti"] == 80
    # Il volume della partita, toccato o no, resta com'era: il predefinito, 50.
    assert impostazioni.carica()["volume_partita"] == 50
    assert finestra.ultimo_evento == "volume effetti 80, partita 50"
    # A zero tacciono la prova e la conferma; l'aspetto, salvato dopo, non cambia il volume.
    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(0))
    finestra.cambia_effetti()
    assert suonati == ["dialogo_effetti_sonori", "prova_volume_effetti", "effetti_sonori_applicati", "dialogo_effetti_sonori"]
    assert suoni.volume_effetti() == 0

    def ok(self):
        self.conferma()
        return wx.ID_OK

    monkeypatch.setattr(dialoghi.Aspetto, "ShowModal", ok)
    finestra.cambia_aspetto()
    assert impostazioni.carica()["volume_effetti"] == 0
    assert len(suonati) == 4


def test_il_volume_della_partita(finestra, suonati, monkeypatch, cartella_di_prova):
    # Decisione D30: nel dialogo degli effetti, accanto a quello degli effetti, con il suo suono di
    # prova, che suona al fattore della partita anche con gli effetti a zero.
    def scegli(volume, volume_partita):
        def mostra(self):
            etichette = [figlio.GetLabel() for figlio in self.pannello.GetChildren() if isinstance(figlio, wx.StaticText)]
            assert "&Volume degli effetti" in etichette and "Volume della &partita dal vivo" in etichette
            assert (self.volume_partita.GetMin(), self.volume_partita.GetMax()) == (0, 100)
            self.volume.SetValue(volume)
            self.volume_partita.SetValue(volume_partita)
            self.prova_partita()
            self.conferma()
            return wx.ID_OK
        return mostra

    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(0, 100))
    finestra.cambia_effetti()
    assert suonati == ["dialogo_effetti_sonori", "prova_volume_partita"]
    assert suonati.dettagli[1]["preset"] == "mess_prova_volume_partita"
    assert suonati.dettagli[1]["fattore"] == pytest.approx(partita_sonora.fattore_del_volume(100))
    assert impostazioni.carica()["volume_partita"] == 100 and finestra.impostazioni["volume_partita"] == 100
    assert finestra.ultimo_evento == "volume effetti 0, partita 100"
    # A zero la prova della partita tace, anche con gli effetti accesi; il volume si salva lo stesso. Il
    # dialogo si apre in silenzio, perché gli effetti erano a zero, e la conferma suona al volume nuovo.
    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(50, 0))
    finestra.cambia_effetti()
    assert suonati[2:] == ["effetti_sonori_applicati"]
    assert impostazioni.carica()["volume_partita"] == 0
    # Un file che non si scrive lo dice la barra.
    monkeypatch.setattr(impostazioni, "salva", lambda _impostazioni: False)
    monkeypatch.setattr(dialoghi.EffettiSonori, "ShowModal", scegli(50, 60))
    finestra.cambia_effetti()
    assert suonati[-1] == "impostazioni_non_salvate" and finestra.ultimo_evento == "volumi non salvati"
    assert finestra.impostazioni["volume_partita"] == 60


@pytest.mark.parametrize(("valore", "letto"), [(0, 0), (100, 100), (37, 37), (101, 50), (-1, 50), (True, 50), ("30", 50), (12.5, 50), (None, 50)])
def test_il_volume_della_partita_si_valida(valore, letto):
    assert impostazioni.valide({"volume_partita": valore})["volume_partita"] == letto


def test_il_suono_di_prova_segue_l_ultimo_campo_toccato(app_wx, suonati):
    # Due campi, un solo suono rimandato: se si passa all'altro campo prima che suoni, vale l'ultimo.
    dialogo = dialoghi.EffettiSonori(None, 50, 95)
    try:
        dialogo.al_volume()
        dialogo.al_volume_partita()
        assert dialogo._timer_del_suono.args == (dialogo.prova_partita,)
        dialogo._timer_del_suono.Stop()
        dialogo.al_volume()
        assert dialogo._timer_del_suono.args == (dialogo.prova,)
        dialogo._timer_del_suono.Stop()
    finally:
        dialogo.Destroy()


def test_il_tic_della_probabilita(app_wx, suonati):
    dialogo = dialoghi.Cifra(None, "Ingaggio", "Spiegazione.", "&Ingaggio", 500, 1000, lambda cifra: f"Nota per {cifra}.", lambda cifra: cifra / 10)
    try:
        dialogo.aggiorna()
        assert suonati == []
        dialogo.cifra.SetValue(900)
        dialogo.tic_della_probabilita()
        assert suonati == ["probabilita_ingaggio"]
        assert suonati.dettagli[0]["semitoni"] == pytest.approx(suoni.probabilita_in_semitoni(90))
    finally:
        dialogo.Destroy()


def test_l_errore_imprevisto(finestra, suonati, monkeypatch, programma_di_prova):
    messaggi = []
    monkeypatch.setattr(wx, "MessageBox", lambda testo, *a, **k: messaggi.append(testo))
    finestra.errore_imprevisto(ValueError, ValueError("prova"))
    assert suonati == ["errore_imprevisto"]
    # Dalla tappa 14 il messaggio non rimanda più alla console, ma al registro accanto al programma.
    assert messaggi == [f"Il comando si è interrotto per un errore imprevisto: ValueError, prova. Il resoconto completo è nel file MESS - Errori.log, "
                        f"nella cartella {programma_di_prova}: allegalo quando chiedi aiuto."]
    assert finestra._modali == 0


# Il manuale nel browser, tappa 14.

def test_il_manuale_nel_browser(finestra, suonati, monkeypatch):
    aperti = []
    monkeypatch.setattr(finestra_modulo.os, "startfile", aperti.append, raising=False)
    finestra.vista.ChangeValue("Il testo che si sta leggendo.")
    voci = {voce[0]: voce[1:] for _titolo, elenco in finestra.voci_menu() for voce in filter(None, elenco)}
    assert voci["&Manuale"] == ("Shift+F1", finestra.manuale)
    finestra._esegui(finestra.manuale)
    assert [Path(p).name for p in aperti] == ["manuale.html"] and Path(aperti[0]).is_file()
    # La vista resta com'era, la barra dice dov'è il manuale.
    assert suonati == ["manuale"] and finestra.vista.GetValue() == "Il testo che si sta leggendo."
    assert finestra.barra.GetValue().splitlines()[3] == "manuale nel browser"
    assert "Manuale, Maiusc+F1" in testi.guida(finestra.voci_guida())


def test_il_manuale_che_manca_o_non_si_apre(finestra, suonati, monkeypatch, cartella_di_prova):
    import percorsi

    monkeypatch.setattr(percorsi, "risorsa", lambda nome: str(cartella_di_prova / nome))
    monkeypatch.setattr(finestra_modulo.os, "startfile", lambda percorso: pytest.fail("un manuale che non c'è non si apre"), raising=False)
    finestra.manuale()
    assert finestra.vista.GetValue().startswith(f"Il manuale non c'è: dovrebbe essere il file {cartella_di_prova / 'manuale.html'}.")
    (cartella_di_prova / "manuale.html").write_text("<html></html>", encoding="utf-8")

    def senza_browser(_percorso):
        raise OSError(2, "Nessuna applicazione associata")

    monkeypatch.setattr(finestra_modulo.os, "startfile", senza_browser, raising=False)
    finestra.manuale()
    assert finestra.vista.GetValue().startswith("Il manuale non si apre nel browser: Nessuna applicazione associata.")
    # Il manuale che manca ha il suo suono, diverso da quello delle novità che non si leggono.
    assert suonati == ["manuale_mancante", "manuale_mancante"]


# Le voci del PUB, il gruppo di supporto, tappa 14, issue 4. La finestra della mail, l'apertura della
# posta, gli appunti e le informazioni del computer si sostituiscono sempre: nessuna prova apre la
# posta, tocca gli appunti veri o dipende dal computer su cui gira.

INFORMAZIONI_DI_PROVA = (
    ("windows", "Windows 11 Pro"), ("windows_versione", "25H2"), ("windows_build", "26300.7171"), ("architettura", "x64"),
    ("processore", "AMD Ryzen 9 7950X 16-Core Processor"), ("nuclei", 32), ("memoria_totale", "31,9 GB"), ("memoria_libera", "18,2 GB"),
    ("lingua", "it_IT"), ("screen_reader", "NVDA 2026.3.1"), ("schermo", "2560x1440"), ("scala", None), ("python", "3.14.7 64 bit"),
    ("compilato", False),
)


class MailPreparate(list):
    """Le mail che finestra_mail avrebbe preparato, in ordine; risposta è il suo esito, e separatori i decimali chiesti alle informazioni."""

    def __init__(self):
        super().__init__()
        self.risposta = True
        self.separatori = []


@pytest.fixture
def informazioni_finte(monkeypatch):
    """Le informazioni del computer, sempre le stesse: quelle vere dipendono da dove gira la prova."""
    import GBUtils

    separatori = []

    def finte(separatore="."):
        separatori.append(separatore)
        return list(INFORMAZIONI_DI_PROVA)

    monkeypatch.setattr(GBUtils, "informazioni_di_sistema", finte)
    return separatori


@pytest.fixture
def mail_preparate(monkeypatch, informazioni_finte):
    """Al posto di finestra_mail di GBwx: registra con che cosa si sarebbe aperta, e restituisce l'esito che la prova sceglie."""
    import GBUtils
    import GBwx

    preparate = MailPreparate()
    preparate.separatori = informazioni_finte

    def finta(genitore, titolo, destinatario, oggetto, corpo, spiegazione, passi, pulsanti, senza_posta="", misura=(560, 420)):
        preparate.append({"titolo": titolo, "destinatario": destinatario, "oggetto": oggetto, "corpo": corpo, "spiegazione": spiegazione,
                          "passi": passi, "pulsanti": pulsanti, "senza_posta": senza_posta, "modali": genitore._modali})
        return preparate.risposta

    monkeypatch.setattr(GBwx, "finestra_mail", finta)
    monkeypatch.setattr(GBUtils, "apri_mail", lambda *mail, **opzioni: pytest.fail("nessuna prova apre la posta"))
    return preparate


def test_le_voci_del_pub_nel_menu_aiuto(finestra):
    aiuto = dict(finestra.voci_menu())["&Aiuto"]
    # Dopo il caffè, precedute da un separatore, senza tasto rapido.
    assert aiuto[-4:] == (("&Offrimi un caffè...", None, finestra.caffe), None,
                          ("&Entra al PUB (gruppo di supporto)...", None, finestra.entra_al_pub),
                          ("&Chiedi aiuto al PUB...", None, finestra.chiedi_aiuto_al_pub))
    assert "Offrimi un caffè; Entra al PUB (gruppo di supporto); Chiedi aiuto al PUB." in testi.guida(finestra.voci_guida())


def test_entra_al_pub(finestra, suonati, mail_preparate):
    import GBUtils

    finestra.vista.ChangeValue("Il testo che si sta leggendo.")
    finestra._esegui(finestra.entra_al_pub)
    mail = mail_preparate[-1]
    assert mail["destinatario"] == GBUtils.PUB_ISCRIZIONE == "prg-user-blind+subscribe@googlegroups.com"
    assert mail["titolo"] == "Entra al PUB, il gruppo di supporto" and mail["oggetto"] == "Iscrizione al PUB"
    assert mail["corpo"] == "Invia questo messaggio così com'è per iscriverti al PUB. Google ti scriverà per chiederti di confermare."
    assert "{programma}" in mail["spiegazione"] and "\n\n" not in mail["spiegazione"]
    # Nei passi basta l'indirizzo: Google non legge oggetto e testo, e l'ultimo passo dice di spedire.
    assert [testo for _istruzione, testo in mail["passi"]] == [GBUtils.PUB_ISCRIZIONE, None]
    assert mail["pulsanti"] == testi.PULSANTI_DEL_PUB and set(mail["pulsanti"]) == {"apri", "passi", "ok", "chiudi", "annulla"}
    assert mail["senza_posta"] == testi.SENZA_POSTA_DEL_PUB
    # Finché la finestra della mail è aperta il mondo non avanza; la vista resta com'era, la barra dice l'esito.
    assert mail["modali"] == 1 and finestra._modali == 0
    assert suonati == ["pub_entra"] and finestra.vista.GetValue() == "Il testo che si sta leggendo."
    assert finestra.barra.GetValue().splitlines()[3] == "mail d'iscrizione al PUB pronta"
    # Chiusa prima di preparare la mail: il suono dell'annullamento.
    mail_preparate.risposta = False
    finestra.entra_al_pub()
    assert suonati == ["pub_entra", "pub_entra", "annullato"]
    assert finestra.barra.GetValue().splitlines()[3] == "iscrizione al PUB annullata"


def test_chiedi_aiuto_al_pub(finestra, suonati, mail_preparate, programma_di_prova):
    import GBUtils

    finestra._esegui(finestra.chiedi_aiuto_al_pub)
    mail = mail_preparate[-1]
    assert mail["destinatario"] == GBUtils.PUB_GRUPPO == "prg-user-blind@googlegroups.com"
    assert mail["titolo"] == "Chiedi aiuto al PUB" and mail["oggetto"] == f"Chiedo per MESS {VERSIONE}"
    # La memoria con la virgola, all'italiana; la scala che non si legge resta fuori, e il falso si dice no.
    assert mail_preparate.separatori == [","]
    assert mail["corpo"].splitlines() == [
        "Scrivi qui la tua domanda, al posto di questa riga.",
        # Una riga che resta nella mail spedita, e parla a chi la riceve, non a chi la scrive.
        "Informazioni su MESS e sul computer di chi scrive:",
        f"Programma: MESS {VERSIONE}",
        "Sistema operativo: Windows 11 Pro",
        "Versione di Windows: 25H2",
        "Build di Windows: 26300.7171",
        "Architettura: x64",
        "Processore: AMD Ryzen 9 7950X 16-Core Processor",
        "Nuclei logici: 32",
        "Memoria: 31,9 GB",
        "Memoria libera: 18,2 GB",
        "Lingua di sistema: it_IT",
        "Screen reader: NVDA 2026.3.1",
        "Schermo: 2560x1440",
        "Python: 3.14.7 64 bit",
        "Programma compilato: no",
    ]
    # L'indirizzo mailto resta sotto il limite oltre il quale certi programmi di posta lo tagliano.
    assert len(GBUtils.indirizzo_mailto(mail["destinatario"], mail["oggetto"], mail["corpo"])) <= 2000
    assert [testo for _istruzione, testo in mail["passi"]] == [GBUtils.PUB_GRUPPO, mail["oggetto"], mail["corpo"], None]
    assert [istruzione[:13] for istruzione, _testo in mail["passi"]] == ["Passo 1 di 4.", "Passo 2 di 4.", "Passo 3 di 4.", "Passo 4 di 4."]
    assert f"con l'oggetto Chiedo per MESS {VERSIONE}." in mail["spiegazione"] and "\n\n" not in mail["spiegazione"]
    # La libertà di cancellare le informazioni la dicono la spiegazione e il passo del testo, non la mail.
    assert "sotto ci sono le informazioni sul tuo computer, utili a chi ti risponde, che puoi cancellare se preferisci." in mail["spiegazione"]
    assert "le informazioni sul computer, sotto, puoi cancellarle se preferisci." in mail["passi"][2][0]
    # Senza registri, niente da allegare, e nessuna avvertenza sui percorsi.
    assert "Allega" not in mail["spiegazione"] and mail["passi"][-1][0].startswith("Passo 4 di 4. Spedisci la mail.")
    assert "utente di Windows" not in mail["spiegazione"] + mail["passi"][-1][0]
    assert suonati == ["pub_aiuto"] and finestra.barra.GetValue().splitlines()[3] == "mail d'aiuto al PUB pronta"
    # Un registro vuoto non si allega; uno scritto sì, con la cartella in cui sta.
    errori = programma_di_prova / "MESS - Errori.log"
    errori.write_text("", encoding="utf-8")
    finestra.chiedi_aiuto_al_pub()
    assert "Allega" not in mail_preparate[-1]["spiegazione"]
    errori.write_text("2026-10-23 08:00:00,000 MESS 2.0.0 si avvia.\n", encoding="utf-8")
    finestra.chiedi_aiuto_al_pub()
    allega = (f"Allega alla mail anche il file MESS - Errori.log, che sta accanto al programma, nella cartella {programma_di_prova}: aiuta a "
              f"capire che cosa è andato storto.")
    # Il registro, a differenza del testo, può contenere percorsi col nome dell'utente di Windows: lo dicono la spiegazione e l'ultimo passo.
    riservatezza = "Il registro può contenere dei percorsi con il nome del tuo utente di Windows: controllalo prima di spedire."
    assert mail_preparate[-1]["spiegazione"].splitlines()[2:4] == [allega, riservatezza]
    assert mail_preparate[-1]["passi"][-1][0].startswith(f"Passo 4 di 4. {allega} {riservatezza} Poi spedisci la mail.")
    # Con il crash della volta prima, i file sono due.
    (programma_di_prova / "MESS - Crash precedente.log").write_text("Fatal Python error: Segmentation fault\n", encoding="utf-8")
    finestra.chiedi_aiuto_al_pub()
    assert ("Allega alla mail anche i file MESS - Crash precedente.log e MESS - Errori.log, che stanno accanto al programma, nella cartella "
            f"{programma_di_prova}: aiutano a capire che cosa è andato storto.") in mail_preparate[-1]["spiegazione"]
    plurale = "I registri possono contenere dei percorsi con il nome del tuo utente di Windows: controllali prima di spedire."
    assert plurale in mail_preparate[-1]["spiegazione"].splitlines() and plurale in mail_preparate[-1]["passi"][-1][0]
    # Il resoconto che non si è potuto mettere da parte resta nel file del crash, e si allega quello.
    (programma_di_prova / "MESS - Crash precedente.log").unlink()
    (programma_di_prova / "MESS - Crash.log").write_text("Fatal Python error: Segmentation fault\n", encoding="utf-8")
    finestra.crash_precedente = str(programma_di_prova / "MESS - Crash.log")
    finestra.chiedi_aiuto_al_pub()
    assert "anche i file MESS - Crash.log e MESS - Errori.log, che stanno" in mail_preparate[-1]["spiegazione"]
    mail_preparate.risposta = False
    finestra.chiedi_aiuto_al_pub()
    assert suonati[-2:] == ["pub_aiuto", "annullato"] and finestra.barra.GetValue().splitlines()[3] == "richiesta d'aiuto annullata"


def test_la_finestra_della_mail_con_le_parole_di_mess(finestra, monkeypatch, informazioni_finte):
    # La finestra vera di GBwx, con apri_mail, gli appunti e il programma di posta sostituiti: al posto
    # dell'attesa di un tasto si legge l'area di testo e si preme Apri, o OK fino all'ultimo passo.
    import GBUtils
    import GBwx

    aperte, copiati, viste = [], [], []
    programma = ["Thunderbird"]
    monkeypatch.setattr(GBUtils, "programma_di_posta", lambda: programma[0])
    monkeypatch.setattr(GBUtils, "apri_mail", lambda *mail, **opzioni: aperte.append(mail) or True)
    monkeypatch.setattr(GBwx, "_negli_appunti", lambda testo: copiati.append(testo) or True)

    def mostra(dialogo):
        viste.append(dialogo.testo.GetValue())
        if programma[0]:
            dialogo._apri()
        else:
            while not dialogo.riuscita:
                dialogo._avanti()
                viste.append(dialogo.testo.GetValue())
        return wx.ID_OK

    monkeypatch.setattr(wx.Dialog, "ShowModal", mostra)
    finestra.chiedi_aiuto_al_pub()
    oggetto = f"Chiedo per MESS {VERSIONE}"
    assert viste[0].startswith("Il pulsante Apri nel programma di posta prepara in Thunderbird una mail al PUB") and "{programma}" not in viste[0]
    assert [mail[:2] for mail in aperte] == [(GBUtils.PUB_GRUPPO, oggetto)] and aperte[0][2].startswith("Scrivi qui la tua domanda")
    assert copiati == [] and finestra.barra.GetValue().splitlines()[3] == "mail d'aiuto al PUB pronta"
    # Senza programma di posta, un passo alla volta: ogni passo copia il suo testo negli appunti.
    programma[0] = None
    viste.clear()
    finestra.chiedi_aiuto_al_pub()
    assert copiati[:2] == [GBUtils.PUB_GRUPPO, oggetto] and copiati[2] == aperte[0][2] and len(copiati) == 3
    assert viste[0] == f"{testi.SENZA_POSTA_DEL_PUB}\n{testi.mail_d_aiuto_al_pub(INFORMAZIONI_DI_PROVA)['passi'][0][0]}\n{GBUtils.PUB_GRUPPO}"
    assert viste[-1].startswith("Passo 4 di 4. Spedisci la mail.")
    assert finestra.barra.GetValue().splitlines()[3] == "mail d'aiuto al PUB pronta"
    copiati.clear()
    finestra.entra_al_pub()
    assert copiati == [GBUtils.PUB_ISCRIZIONE] and len(aperte) == 1
    assert finestra.barra.GetValue().splitlines()[3] == "mail d'iscrizione al PUB pronta"


# Il crash della volta prima, tappa 14.

def test_il_crash_della_volta_prima_all_apertura(app_wx, mondo, suonati, monkeypatch, programma_di_prova):
    resoconto = programma_di_prova / "MESS - Crash precedente.log"
    f = FinestraPrincipale(mondo, archivio.CARICATO, [], Mondo.rapporto_vuoto(adesso()), mondo.datetime_ultimo_run_reale, crash_precedente=str(resoconto))
    try:
        assert f.vista.GetValue().startswith(f"L'ultima volta MESS si è chiuso di colpo per un errore grave. Il resoconto è nel file MESS - Crash precedente.log, "
                                             f"nella cartella {programma_di_prova}: allegalo, insieme a MESS - Errori.log, quando chiedi aiuto.\nMESS, ")
        f.suoni_d_avvio()
        assert suonati == ["avvio", "crash_precedente"]
        # Staccato di un secondo dalla fine dell'avvio, come la notizia dello staff.
        rinviati = []
        monkeypatch.setattr(suoni, "attesa", lambda: 0.4)
        monkeypatch.setattr(wx, "CallLater", lambda millisecondi, funzione, *argomenti, **opzioni: rinviati.append((millisecondi, argomenti)))
        f.suoni_d_avvio()
        assert rinviati == [(1400, ("crash_precedente",))]
    finally:
        f.timer.Stop()
        f.Destroy()
        wx.Yield()


def test_il_suono_di_prova_aspetta_che_ci_si_fermi(app_wx, suonati):
    # Tre ritocchi di fila danno un suono solo, al volume dell'ultimo, quando ci si ferma.
    dialogo = dialoghi.EffettiSonori(None, 50)
    try:
        for valore in (60, 70, 80):
            dialogo.volume.SetValue(valore)
            dialogo.al_volume()
        assert suonati == []
        # I timer di wx scattano soltanto dentro un ciclo degli eventi: qui ne gira uno per un secondo.
        ciclo = wx.GUIEventLoop()
        wx.CallLater(1000, ciclo.Exit)
        ciclo.Run()
        assert suonati == ["prova_volume_effetti"]
        assert suonati.dettagli[0]["fattore"] == pytest.approx(1.6)
    finally:
        dialogo.Destroy()


def test_ogni_domanda_si_o_no_ha_il_no_gia_scelto():
    # Un Invio di troppo non deve mai confermare un'operazione: vale anche al mercato, dalla 1.39.6.
    radice = Path(__file__).resolve().parent.parent / "gui"
    senza = [f"{p.name}:{n}" for p in sorted(radice.glob("*.py")) for n, riga in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
             if "wx.YES_NO" in riga and "wx.NO_DEFAULT" not in riga]
    assert not senza, f"domande con il Sì già scelto: {senza}"
