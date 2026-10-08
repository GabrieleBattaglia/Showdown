"""
Test della finestra dal vivo della decisione D29, sul desktop nascosto del conftest e senza suonare:
la cassa è finta, l'orologio pure, e il battito del timer lo dà la prova. Il pulsante Prosegui con le
sue facce, Pausa, Riprendi, Salta il riscaldamento e il risultato; la pausa e la ripresa dalla stessa
posizione; l'ascolto fino a fine set senza fermate ai punti; il cambio di lato a metà punto,
ricomposto dal punto in cui si era; Vai alla fine ed Esc, che fermano il suono con la maniglia; la
velocità di gioco con più e meno; la fine dell'incontro; il campo della cronaca, letto con Tab.
"""

import numpy as np
import pytest
import wx
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

import partita_sonora as ps
from gui import dal_vivo
from gui.dal_vivo import FinestraDalVivo
from motore import COMPLETO, SINGOLARE_3, Incontro, cronaca
from motore import eventi as E

FS = ps.FS
SEME = 31


@pytest.fixture(autouse=True)
def cassa_vera_muta(monkeypatch):
    vieta_la_cassa_vera(monkeypatch)


class Vivo:
    """La finestra dal vivo con la sua cassa, il suo orologio, l'incontro gemello e i nomi."""

    def __init__(self, velocita=1, livello=cronaca.NORMALE):
        g1, g2 = giocatore(1, 12.0), giocatore(2, 13.0)
        self.nomi = cronaca.nomi_dei_giocatori([g1, g2])
        self.riferimento = Incontro(g1, g2, SINGOLARE_3, seme=SEME, dettaglio=COMPLETO).gioca()
        self.gemello = Incontro(g1, g2, SINGOLARE_3, seme=SEME, dettaglio=COMPLETO, velocita=velocita)
        self.cassa = CassaFinta()
        self.orologio = Orologio()
        self.finestra = FinestraDalVivo(None, self.gemello, self.nomi, livello, velocita, cassa=self.cassa, orologio=self.orologio)

    def scorri(self, secondi, passo=0.05):
        """Fa passare il tempo, con un battito del timer a ogni passo."""
        fine = self.orologio.adesso + secondi
        while self.orologio.adesso < fine - 1e-9:
            self.orologio.adesso = min(fine, self.orologio.adesso + passo)
            self.finestra.al_battito()

    def fino_a_fermo(self, passo=0.05, massimo=3000.0):
        """Fa passare il tempo finché la tranche finisce; restituisce gli stati visti a ogni battito."""
        stati = []
        inizio = self.orologio.adesso
        while self.finestra.stato == dal_vivo.SUONA:
            assert self.orologio.adesso - inizio < massimo, "la tranche non finisce mai"
            self.orologio.adesso += passo
            self.finestra.al_battito()
            stati.append(self.finestra.stato)
        return stati

    def testo(self):
        return self.finestra.cronaca.GetValue()

    def etichetta(self):
        return self.finestra.prosegui.GetLabel()


@pytest.fixture
def vivo(app_wx):
    v = Vivo()
    yield v
    v.finestra.timer.Stop()
    v.finestra.Destroy()


def _salta_il_riscaldamento(vivo):
    vivo.finestra.al_prosegui()
    assert vivo.etichetta() == "&Salta il riscaldamento"
    vivo.finestra.al_prosegui()
    assert vivo.finestra.stato == dal_vivo.FERMO


def test_l_apertura(vivo):
    f = vivo.finestra
    assert vivo.etichetta() == "&Prosegui" and f.stato == dal_vivo.FERMO
    assert f.GetTitle() == f"Dal vivo, {vivo.nomi['A'].testo} contro {vivo.nomi['B'].testo}, velocità 1"
    testo = vivo.testo()
    assert testo.startswith(f"Partita dal vivo: {vivo.nomi['A'].testo} contro {vivo.nomi['B'].testo}, al meglio dei 3 set.")
    assert "Alt+F" in testo and "Alt+L" in testo and "Alt+V" in testo and "Esc" in testo and "\n\n" not in testo
    assert f.cronaca.IsMultiLine() and not f.cronaca.IsEditable()
    # Il campo della cronaca viene subito dopo il pulsante, nell'ordine del Tab, e prima degli altri pulsanti.
    figli = list(f.pannello.GetChildren())
    assert figli.index(f.prosegui) < figli.index(f.cronaca) < figli.index(f.fine_set) < figli.index(f.lato) < figli.index(f.alla_fine)
    assert f.prosegui.GetId() == f.GetDefaultItem().GetId()
    assert vivo.cassa.buffer == []


def test_il_riscaldamento_e_il_primo_punto(vivo, suonati):
    f = vivo.finestra
    f.al_prosegui()
    assert f.stato == dal_vivo.SUONA and vivo.etichetta() == "&Salta il riscaldamento"
    assert len(vivo.cassa.buffer) == 1
    # Il campo non cambia mentre suona: la cronaca arriva a tranche finita.
    assert vivo.testo().startswith("Partita dal vivo")
    stati = vivo.fino_a_fermo()
    assert stati[-1] == dal_vivo.FERMO and vivo.etichetta() == "&Prosegui"
    assert "Riscaldamento, un minuto." in vivo.testo() and vivo.testo().endswith("Fine del riscaldamento.")
    assert vivo.cassa.accese == 0
    f.al_prosegui()
    assert vivo.etichetta() == "&Pausa"
    vivo.fino_a_fermo()
    righe = vivo.testo().splitlines()
    assert righe[0].startswith("Set 1: apre ") and righe[1] == f"Set 1, {vivo.nomi['A'].testo} 0, {vivo.nomi['B'].testo} 0."
    assert "\n\n" not in vivo.testo()
    # Prosegui non fa suonare niente della finestra: si sente soltanto la partita.
    assert suonati == []
    assert len(vivo.cassa.buffer) == 2 and vivo.cassa.accese == 0


def test_saltare_il_riscaldamento(vivo, suonati):
    _salta_il_riscaldamento(vivo)
    assert suonati == ["riscaldamento_saltato"]
    assert vivo.testo().endswith("Fine del riscaldamento.")
    assert vivo.cassa.accese == 0


def test_la_pausa_e_la_ripresa_dalla_stessa_posizione(vivo, suonati):
    f = vivo.finestra
    _salta_il_riscaldamento(vivo)
    f.al_prosegui()
    primo = vivo.cassa.buffer[-1]
    vivo.scorri(2.0)
    f.al_prosegui()
    assert f.stato == dal_vivo.PAUSA and vivo.etichetta() == "&Riprendi"
    assert suonati[-1] == "dal_vivo_pausa" and vivo.cassa.accese == 0
    assert f.posizione == pytest.approx(2.0)
    # In pausa il campo dice quello che si è sentito fin lì.
    sentite = vivo.testo().splitlines()
    assert sentite[0].startswith("Set 1")
    f.al_prosegui()
    assert f.stato == dal_vivo.SUONA and vivo.etichetta() == "&Pausa" and suonati[-1] == "dal_vivo_ripresa"
    ripreso = vivo.cassa.buffer[-1]
    da = round(2.0 * FS)
    assert np.array_equal(ripreso[:len(primo) - da], primo[da:])
    vivo.fino_a_fermo()
    assert len(vivo.testo().splitlines()) >= len(sentite)


def test_fino_a_fine_set_non_si_ferma_ai_punti(app_wx, suonati):
    vivo = Vivo(velocita=4)
    try:
        f = vivo.finestra
        _salta_il_riscaldamento(vivo)
        f.fino_a_fine_set()
        assert f.modo == dal_vivo.FINO_A_FINE_SET and vivo.etichetta() == "&Pausa"
        stati = vivo.fino_a_fermo()
        assert set(stati[:-1]) == {dal_vivo.SUONA} and stati[-1] == dal_vivo.FERMO
        assert f.segmento.chiusura.tipo == E.FINE_SET
        testo = vivo.testo()
        primo_set = vivo.riferimento.set[0]
        assert testo.count("Set 1, ") > 5 and "Fischio lungo. Set a " in testo
        assert f"{max(primo_set)} a {min(primo_set)}" in testo.splitlines()[-2] + testo.splitlines()[-1]
        # Un buffer per segmento, tutti fermati con la loro maniglia.
        assert len(vivo.cassa.buffer) > 6 and vivo.cassa.accese == 0
        assert suonati == ["riscaldamento_saltato"]
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()


def test_il_cambio_di_lato_a_meta_punto(vivo, suonati):
    f = vivo.finestra
    _salta_il_riscaldamento(vivo)
    f.al_prosegui()
    t0 = f.resa.t0
    vivo.scorri(1.5)
    f.cambia_lato()
    assert f.ascoltatore == "B" and suonati[-1] == "dal_vivo_cambio_lato"
    assert f.lato.GetLabel() == f"Cambia &lato, ora ascolti da {vivo.nomi['B'].testo}"
    assert vivo.cassa.maniglie[-2].fermate == 1 and vivo.cassa.accese == 1
    atteso = ps.per_la_cassa(ps.componi(f.segmento.eventi, "B", da=t0, fine=f.segmento.fine).buffer, 50)
    da = round(1.5 * FS)
    assert np.array_equal(vivo.cassa.buffer[-1][:len(atteso) - da], atteso[da:])
    # In pausa il lato cambia alla ripresa, dalla stessa posizione.
    vivo.scorri(0.5)
    f.al_prosegui()
    f.cambia_lato()
    assert f.resa is None and len(vivo.cassa.buffer) == 3
    f.al_prosegui()
    per_a = ps.per_la_cassa(ps.componi(f.segmento.eventi, "A", da=t0, fine=f.segmento.fine).buffer, 50)
    da = round(2.0 * FS)
    assert np.array_equal(vivo.cassa.buffer[-1][:len(per_a) - da], per_a[da:])


def test_vai_alla_fine_ferma_il_suono_con_la_maniglia(vivo, suonati):
    f = vivo.finestra
    f.al_prosegui()
    vivo.scorri(1.0)
    f.alla_fine.Command(wx.CommandEvent(wx.wxEVT_BUTTON, f.alla_fine.GetId()))
    assert f.uscita == dal_vivo.ALLA_FINE and f.GetReturnCode() == wx.ID_OK
    assert vivo.cassa.accese == 0 and suonati == []


def _tasto(finestra, codice, carattere=None):
    evento = wx.KeyEvent(wx.wxEVT_CHAR_HOOK)
    evento.SetKeyCode(codice)
    if carattere is not None:
        evento.SetUnicodeKey(carattere)
    finestra._tasto(evento)


def test_esc_esce(vivo, suonati):
    f = vivo.finestra
    _salta_il_riscaldamento(vivo)
    f.al_prosegui()
    _tasto(f, wx.WXK_ESCAPE)
    assert f.uscita == dal_vivo.CON_ESC and f.GetReturnCode() == wx.ID_CANCEL
    assert vivo.cassa.accese == 0


def test_piu_e_meno_cambiano_la_velocita(vivo, suonati):
    f = vivo.finestra
    _tasto(f, ord("-"), ord("-"))
    assert f.velocita == 1 and suonati == ["dal_vivo_velocita_al_limite"]
    _tasto(f, ord("+"), ord("+"))
    _tasto(f, wx.WXK_NUMPAD_ADD)
    assert f.velocita == 3 and suonati[-2:] == ["dal_vivo_piu_veloce", "dal_vivo_piu_veloce"]
    assert f.GetTitle().endswith("velocità 3")
    _tasto(f, wx.WXK_NUMPAD_SUBTRACT)
    assert f.velocita == 2 and suonati[-1] == "dal_vivo_piu_lenta"
    for _ in range(10):
        _tasto(f, ord("+"), ord("+"))
    assert f.velocita == 8 and suonati[-1] == "dal_vivo_velocita_al_limite"
    # La velocità vale dal momento che il motore svolge dopo il cambio.
    f.al_prosegui()
    assert vivo.gemello.regia.velocita == 8.0
    _tasto(f, ord("-"), ord("-"))
    f.al_prosegui()
    f.al_prosegui()
    assert vivo.gemello.regia.velocita == 7.0


def test_la_fine_dell_incontro_porta_al_risultato(app_wx, suonati):
    vivo = Vivo(velocita=8, livello=cronaca.SINTETICA)
    try:
        f = vivo.finestra
        tranche = 0
        while f.stato != dal_vivo.FINITO:
            f.fino_a_fine_set()
            vivo.fino_a_fermo(passo=0.1)
            tranche += 1
            assert tranche < 10
        assert tranche == len(vivo.riferimento.set)
        assert vivo.etichetta() == "Fine dell'incontro: vai al &risultato"
        assert vivo.testo().splitlines()[-1].startswith("Fine dell'incontro: vince ")
        assert vivo.gemello.risultato.set == vivo.riferimento.set
        f.fino_a_fine_set()
        f.cambia_lato()
        assert suonati[-2:] == ["incontro_finito", "incontro_finito"] and f.ascoltatore == "A"
        f.al_prosegui()
        assert f.uscita == dal_vivo.AL_RISULTATO and f.GetReturnCode() == wx.ID_OK
        assert vivo.cassa.accese == 0
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()
