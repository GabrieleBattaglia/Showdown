"""
Test della finestra e dei dialoghi, sul desktop nascosto del conftest: ogni voce dei menu, la
barra di stato, il salvataggio, la chiusura con il riepilogo, la scelta del giocatore, la
ricerca, l'aspetto e l'invito al caffè. Le finestre modali vengono sostituite, perché una prova
che aspetta un tasto non finirebbe mai.
"""

import datetime
import json
import random

import pytest
import wx

import archivio
import impostazioni
import testi
from costanti import FILE_MONDO
from gui import dialoghi
from gui.finestra import FinestraPrincipale
from modelli import Polisportiva
from mondo import Mondo
from utilita import adesso


@pytest.fixture
def mondo():
    random.seed(11)
    ora = adesso()
    m = Mondo()
    m.datetime_corrente_simulazione = ora
    m.datetime_ultimo_run_reale = ora - datetime.timedelta(hours=2)
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
    # Nessuna finestra modale vera: la prova non avrebbe nessuno che le chiude.
    monkeypatch.setattr(wx.Dialog, "ShowModal", lambda self: wx.ID_CANCEL)
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
    con_dialogo = {finestra.scheda_giocatore, finestra.cerca, finestra.cambia_aspetto, finestra.caffe, finestra.esci, finestra.vai_alla_vista, finestra.vai_alla_barra}
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
    assert provate == 17
    assert finestra.comandi == 17


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
        dialogo.criterio.SetSelection(4)
        dialogo.al_criterio()
        assert not dialogo.valore.IsEnabled()
        dialogo.condizione.SetSelection(1)
        dialogo.conferma()
        assert dialogo.risultato[1:4] == ("ipovedente", "no", None)
    finally:
        dialogo.Destroy()


def test_aspetto(app_wx):
    dialogo = dialoghi.Aspetto(None, {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50]})
    try:
        assert dialogo.valori() == {"dimensione": 20, "colore_testo": [100, 100, 100], "colore_sfondo": [0, 0, 50]}
        dialogo.ai_predefiniti()
        assert dialogo.valori() == impostazioni.valide(None)
        dialogo.conferma()
        assert dialogo.risultato == impostazioni.valide(None)
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
