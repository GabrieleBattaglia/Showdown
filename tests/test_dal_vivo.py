"""
Test della finestra dal vivo della decisione D29, sul desktop nascosto del conftest e senza suonare:
la cassa è finta, l'orologio pure, e il battito del timer lo dà la prova. Il pulsante Prosegui con le
sue facce, Pausa, Riprendi, Salta il riscaldamento e il risultato; la pausa e la ripresa dalla stessa
posizione; l'ascolto fino a fine set senza fermate ai punti, con il suo suono in ogni stato; il
cambio di lato a metà punto, ricomposto dal punto in cui si era; Vai alla fine ed Esc, che fermano il
suono con la maniglia; la velocità di gioco con più e meno, che accorcia anche la pausa dopo il punto
in cui si è premuto, e quella cambiata in pausa, che vale alla ripresa; la fine dell'incontro; il
campo della cronaca, letto con Tab, con la guida che segue lato e velocità e torna con F1.
Dalla decisione D30: le pause lunghe, time-out, cambio campo e inizio del set, che né Prosegui né
l'ascolto fino a fine set fanno sentire, e il volume della partita, a parte da quello degli effetti.
"""

import numpy as np
import pytest
import wx
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

import impostazioni
import partita_sonora as ps
import suoni
import testi
from gui import dal_vivo
from gui.dal_vivo import FinestraDalVivo
from motore import COMPLETO, SINGOLARE_3, Incontro, cronaca
from motore import eventi as E

FS = ps.FS
SEME = 31
# I campioni della rampa con cui un buffer riparte a metà.
RAMPA = round(ps.SFUMATURA * FS)


@pytest.fixture(autouse=True)
def cassa_vera_muta(monkeypatch):
    vieta_la_cassa_vera(monkeypatch)


class Vivo:
    """La finestra dal vivo con la sua cassa, il suo orologio, l'incontro gemello e i nomi."""

    def __init__(self, velocita=1, livello=cronaca.NORMALE, seme=SEME, impostazioni=None):
        g1, g2 = giocatore(1, 12.0), giocatore(2, 13.0)
        self.nomi = cronaca.nomi_dei_giocatori([g1, g2])
        self.riferimento = Incontro(g1, g2, SINGOLARE_3, seme=seme, dettaglio=COMPLETO).gioca()
        self.gemello = Incontro(g1, g2, SINGOLARE_3, seme=seme, dettaglio=COMPLETO, velocita=velocita)
        self.cassa = CassaFinta()
        self.orologio = Orologio()
        self.finestra = FinestraDalVivo(None, self.gemello, self.nomi, livello, velocita, impostazioni, cassa=self.cassa, orologio=self.orologio)

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

    def scorri_fino(self, condizione, passo=0.05, massimo=3000.0):
        """Fa passare il tempo, un battito alla volta, finché la condizione è vera; restituisce i secondi passati."""
        inizio = self.orologio.adesso
        while not condizione():
            assert self.orologio.adesso - inizio < massimo, "la condizione non arriva mai"
            self.orologio.adesso += passo
            self.finestra.al_battito()
        return self.orologio.adesso - inizio

    def arrivato(self, tipo):
        """Vero se il suono è arrivato al primo evento del tipo dato nel segmento che suona, secondo le pieghe del buffer."""
        f = self.finestra
        evento = next((e for e in f.segmento.eventi if e.tipo == tipo), None) if f.segmento else None
        posizione = f.riproduttore.posizione()
        return evento is not None and posizione is not None and posizione >= f.resa.secondi(evento.t) - 1e-9

    def testo(self):
        return self.finestra.cronaca.GetValue()

    def etichetta(self):
        return self.finestra.prosegui.GetLabel()

    def guida(self):
        """La guida che il campo deve mostrare, con il lato e la velocità di adesso."""
        f = self.finestra
        return testi.guida_dal_vivo(self.nomi, f.ascoltatore, 3, f.velocita)


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
    # Riparte dallo stesso campione, con cinque millesimi di rampa in testa perché il taglio non faccia clic.
    assert not np.any(ripreso[0])
    assert np.allclose(ripreso[:RAMPA], primo[da:da + RAMPA] * np.linspace(0.0, 1.0, RAMPA, dtype=np.float32)[:, None])
    assert np.array_equal(ripreso[RAMPA:len(primo) - da], primo[da + RAMPA:])
    vivo.fino_a_fermo()
    assert len(vivo.testo().splitlines()) >= len(sentite)


def test_fino_a_fine_set_non_si_ferma_ai_punti(app_wx, suonati):
    vivo = Vivo(velocita=4)
    try:
        f = vivo.finestra
        _salta_il_riscaldamento(vivo)
        f.fino_a_fine_set()
        assert f.modo == dal_vivo.FINO_A_FINE_SET and vivo.etichetta() == "&Pausa"
        assert suonati == ["riscaldamento_saltato", "dal_vivo_fino_a_fine_set"]
        stati = vivo.fino_a_fermo()
        assert set(stati[:-1]) == {dal_vivo.SUONA} and stati[-1] == dal_vivo.FERMO
        assert f.segmento.chiusura.tipo == E.FINE_SET
        testo = vivo.testo()
        primo_set = vivo.riferimento.set[0]
        assert testo.count("Set 1, ") > 5 and "Fischio lungo. Set a " in testo
        assert f"{max(primo_set)} a {min(primo_set)}" in testo.splitlines()[-2] + testo.splitlines()[-1]
        # Un buffer per segmento, più quello del riscaldamento, tutti fermati con la loro maniglia: a
        # velocità costante nessun buffer riparte per ripiegare la procedura.
        segmenti = sum(1 for e, m, _apre in f.tranche if f.cronologia._chiude(e, m))
        assert segmenti > 6 and len(vivo.cassa.buffer) == 1 + segmenti
        assert vivo.cassa.accese == 0 and f._pieghe == ()
        assert suonati == ["riscaldamento_saltato", "dal_vivo_fino_a_fine_set"]
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
    # Senza impostazioni la partita suona al volume predefinito della partita.
    assert f.volume == impostazioni.VOLUME_PARTITA_PREDEFINITO
    atteso = ps.per_la_cassa(ps.componi(f.segmento.eventi, "B", da=t0, fine=f.segmento.fine).buffer, f.volume)
    da = round(1.5 * FS)
    assert not np.any(vivo.cassa.buffer[-1][0])
    assert np.array_equal(vivo.cassa.buffer[-1][RAMPA:len(atteso) - da], atteso[da + RAMPA:])
    # In pausa il lato cambia alla ripresa, dalla stessa posizione.
    vivo.scorri(0.5)
    f.al_prosegui()
    f.cambia_lato()
    assert f.resa is None and len(vivo.cassa.buffer) == 3
    f.al_prosegui()
    per_a = ps.per_la_cassa(ps.componi(f.segmento.eventi, "A", da=t0, fine=f.segmento.fine).buffer, f.volume)
    da = round(2.0 * FS)
    assert np.array_equal(vivo.cassa.buffer[-1][RAMPA:len(per_a) - da], per_a[da + RAMPA:])


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


# Le correzioni della revisione: Alt+F col suo suono, la guida che segue lato e velocità, F1, e la
# velocità che vale anche per pause e procedura già composte.

def test_alt_f_ha_il_suo_suono_in_ogni_stato(vivo, suonati):
    f = vivo.finestra
    _salta_il_riscaldamento(vivo)
    f.al_prosegui()
    buffer = len(vivo.cassa.buffer)
    # Mentre suona: il modo cambia, il suono lo dice e la partita va avanti senza ripartire.
    f.fino_a_fine_set()
    assert f.modo == dal_vivo.FINO_A_FINE_SET and f.stato == dal_vivo.SUONA
    assert suonati[-1] == "dal_vivo_fino_a_fine_set" and len(vivo.cassa.buffer) == buffer
    # Premuto di nuovo, lo stesso suono conferma che il modo è già quello.
    f.fino_a_fine_set()
    assert suonati[-2:] == ["dal_vivo_fino_a_fine_set", "dal_vivo_fino_a_fine_set"]
    # In pausa il suo suono prende il posto di quello della ripresa, e la partita riparte.
    vivo.scorri(1.0)
    f.al_prosegui()
    assert f.stato == dal_vivo.PAUSA
    f.fino_a_fine_set()
    assert f.stato == dal_vivo.SUONA and f.modo == dal_vivo.FINO_A_FINE_SET
    assert suonati[-2:] == ["dal_vivo_pausa", "dal_vivo_fino_a_fine_set"] and "dal_vivo_ripresa" not in suonati
    assert len(vivo.cassa.buffer) == buffer + 1 and vivo.cassa.accese == 1


def test_la_guida_segue_lato_e_velocita_e_torna_con_f1(vivo, suonati):
    f = vivo.finestra
    assert vivo.testo() == vivo.guida() and "F1" in vivo.testo()
    f.cambia_lato()
    f.cambia_velocita(1)
    f.cambia_velocita(1)
    # Prima della prima tranche il campo dice il lato e la velocità di adesso, come il pulsante e il titolo.
    assert f.ascoltatore == "B" and f.velocita == 3
    assert vivo.testo() == vivo.guida()
    assert f"Ascolti da {vivo.nomi['B'].testo}" in vivo.testo() and "ora 3" in vivo.testo()
    # Dopo la prima tranche il campo tiene la cronaca: Alt+L e più non la toccano.
    f.al_prosegui()
    vivo.fino_a_fermo()
    cronaca_della_tranche = vivo.testo()
    assert cronaca_della_tranche.endswith("Fine del riscaldamento.")
    f.cambia_lato()
    f.cambia_velocita(1)
    assert vivo.testo() == cronaca_della_tranche
    # F1 rimette la guida, con il lato e la velocità di adesso, e suona quella della finestra.
    _tasto(f, wx.WXK_F1)
    assert suonati[-1] == "guida" and vivo.testo() == vivo.guida()
    assert f"Ascolti da {vivo.nomi['A'].testo}" in vivo.testo() and "ora 4" in vivo.testo()
    # Ora la guida è di nuovo nel campo, e torna a seguire il lato; la tranche che segue la sostituisce.
    f.cambia_lato()
    assert vivo.testo() == vivo.guida()
    f.al_prosegui()
    vivo.fino_a_fermo()
    assert vivo.testo().startswith("Set 1: apre ")


def _con_il_time_out(segmento):
    return segmento is not None and any(e.tipo == E.TIMEOUT_INIZIO for e in segmento.preambolo)


def test_fino_a_fine_set_il_time_out_non_si_sente(app_wx, suonati):
    # Col seme 5 c'è un time-out nel primo set. Decisione D30: fino a fine set dopo il punto resta
    # la pausa di sempre, in silenzio, e il suono riprende dalla ripresa del gioco, senza il minuto
    # del time-out e senza il suo fischio; il time-out si legge nella cronaca.
    vivo = Vivo(seme=5)
    try:
        f = vivo.finestra
        _salta_il_riscaldamento(vivo)
        f.fino_a_fine_set()
        visti = []

        def al_time_out():
            if not visti or visti[-1] is not f.segmento:
                visti.append(f.segmento)
            return _con_il_time_out(f.segmento)

        vivo.scorri_fino(al_time_out)
        segmento, precedente = visti[-1], visti[-2]
        assert segmento.pausa_lunga and precedente.chiusura.tipo == E.PUNTO
        inizio, fine = (next(e.t for e in segmento.eventi if e.tipo == tipo) for tipo in (E.TIMEOUT_INIZIO, E.TIMEOUT_FINE))
        assert fine - inizio == pytest.approx(60.0, abs=0.01)
        # Il fischio del time-out è il primo evento del segmento, e come tutto il time-out non suona.
        preambolo = {e.n for e in segmento.preambolo}
        assert segmento.eventi[0].tipo == E.FISCHIO and segmento.eventi[0].n in preambolo
        assert not preambolo & {p.evento for p in f.resa.posati}
        assert f.resa.t0 >= segmento.inizio - ps.TOLLERANZA
        # Resta la pausa dopo il punto, 5,5 secondi a velocità 1, come fra due punti qualunque.
        assert f.riproduttore.corrente.anticipo == segmento.attesa_prima(precedente.fine, 1) == pytest.approx(5.5, abs=0.01)
        assert vivo.scorri_fino(lambda: not f.riproduttore.in_anticipo()) == pytest.approx(5.5, abs=0.1)
        # Dopo il time-out la partita va avanti con gli stessi punti, fino a fine set, e la cronaca lo dice.
        vivo.fino_a_fermo()
        assert f.segmento.chiusura.tipo == E.FINE_SET
        assert f.segmento.chiusura.dati["punteggio"] == list(vivo.riferimento.set[0])
        assert "Time-out per " in vivo.testo()
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()


def test_prosegui_non_fa_sentire_le_pause_lunghe(app_wx, suonati):
    # Prosegui comincia sempre dalla ripresa del gioco: l'inizio del primo set e il time-out del seme 5
    # restano fuori dal suono, e si leggono nella cronaca della tranche.
    vivo = Vivo(seme=5, velocita=8)
    try:
        f = vivo.finestra
        _salta_il_riscaldamento(vivo)
        visti = []
        for _ in range(60):
            f.al_prosegui()
            segmento = f.segmento
            assert f.resa.t0 >= segmento.inizio - ps.TOLLERANZA
            assert not {e.n for e in segmento.preambolo} & {p.evento for p in f.resa.posati}
            vivo.fino_a_fermo(passo=0.1)
            if segmento.pausa_lunga:
                visti.append((segmento, vivo.testo()))
            if _con_il_time_out(segmento):
                break
        tipi = [{e.tipo for e in s.preambolo} for s, _testo in visti]
        assert E.INIZIO_SET in tipi[0] and visti[0][1].startswith("Set 1: apre ")
        assert E.TIMEOUT_INIZIO in tipi[-1] and "Time-out per " in visti[-1][1]
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()


@pytest.mark.parametrize("fino_a_fine_set", [False, True])
def test_le_pause_lunghe_non_si_sentono_mai(app_wx, suonati, monkeypatch, fino_a_fine_set):
    # Col seme 50 l'incontro va al terzo set, con due time-out, un'ammonizione e il cambio campo a
    # metà del terzo set. Si ascolta tutto, con Prosegui o fino a fine set, e nessun buffer composto
    # porta un suono di quello che viene prima della ripresa in un segmento con una pausa lunga.
    composti = []
    componi = ps.componi

    def spia(*args, **kwargs):
        composti.append(componi(*args, **kwargs))
        return composti[-1]

    monkeypatch.setattr(ps, "componi", spia)
    vivo = Vivo(seme=50, velocita=8)
    try:
        f = vivo.finestra
        segmenti = []
        prossimo = f.cronologia.prossimo

        def registra(velocita=None):
            segmento = prossimo(velocita)
            if segmento is not None:
                segmenti.append(segmento)
            return segmento

        f.cronologia.prossimo = registra
        tranche = 0
        while f.stato != dal_vivo.FINITO:
            tranche += 1
            assert tranche < 200
            if fino_a_fine_set:
                f.fino_a_fine_set()
            else:
                f.al_prosegui()
                if f.segmento.riscaldamento:
                    f.al_prosegui()
                    continue
            vivo.fino_a_fermo(passo=0.25)
        assert vivo.gemello.risultato.set == vivo.riferimento.set and len(vivo.riferimento.set) == 3
        lunghi = [s for s in segmenti if s.pausa_lunga]
        tipi = {e.tipo for s in lunghi for e in s.preambolo}
        assert {E.TIMEOUT_INIZIO, E.CAMBIO_CAMPO_INIZIO, E.INIZIO_SET} <= tipi
        assert any(e.tipo == E.CAMBIO_CAMPO_INIZIO and not e.dati["fra_set"] for s in lunghi for e in s.preambolo)
        da_tacere = {e.n for s in lunghi for e in s.preambolo}
        sentiti = {p.evento for resa in composti for p in resa.posati}
        assert sentiti and not da_tacere & sentiti
        # Le pause lunghe hanno anche eventi che suonerebbero, come il fischio del time-out.
        assert any(ps.posati_dell_evento(e) for s in lunghi for e in s.preambolo)
        assert vivo.cassa.accese == 0
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()


def test_piu_dentro_un_punto_accorcia_la_pausa_che_lo_segue(app_wx, suonati):
    vivo = Vivo()
    try:
        f = vivo.finestra
        _salta_il_riscaldamento(vivo)
        f.fino_a_fine_set()
        vivo.scorri(1.0)
        for _ in range(7):
            f.cambia_velocita(1)
        primo = f.segmento
        vivo.scorri_fino(lambda: f.segmento is not primo)
        secondo = f.segmento
        ripresa = next(e for e in secondo.eventi if e.tipo in (E.RECUPERO, E.CONSEGNA))
        # La pausa il motore l'ha scritta a velocità 1, in fondo al punto: nel buffer dura un ottavo.
        assert ripresa.t - primo.fine == pytest.approx(5.5, abs=0.01)
        sentita = f.resa.secondi(ripresa.t) - f.resa.secondi(primo.fine)
        assert sentita == pytest.approx(5.5 / 8, abs=0.01)
        assert vivo.scorri_fino(lambda: f.riproduttore.posizione() >= f.resa.secondi(ripresa.t)) == pytest.approx(5.5 / 8, abs=0.1)
        # E il recupero che segue, svolto dal motore dopo il cambio, è già a velocità 8.
        assert vivo.gemello.regia.velocita == 8.0
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()


def test_la_velocita_cambiata_in_pausa_vale_alla_ripresa(app_wx, suonati):
    # Prima della decisione D30 la prova si fermava dentro il time-out, che ora non si sente: si
    # ferma invece dentro la pausa dopo il primo punto, 5,5 secondi a velocità 1.
    vivo = Vivo()
    try:
        f = vivo.finestra
        _salta_il_riscaldamento(vivo)
        f.fino_a_fine_set()
        primo = f.segmento
        vivo.scorri_fino(lambda: f.segmento is not primo)
        ripresa = f.segmento.eventi[0]
        assert ripresa.tipo in (E.RECUPERO, E.CONSEGNA) and not f.segmento.pausa_lunga
        assert ripresa.t - primo.fine == pytest.approx(5.5, abs=0.01)
        vivo.scorri(2.0)
        f.al_prosegui()
        assert f.stato == dal_vivo.PAUSA
        restavano = 5.5 - f.posizione
        assert restavano == pytest.approx(3.5, abs=0.06)
        for _ in range(3):
            f.cambia_velocita(1)
        f.al_prosegui()
        assert f.stato == dal_vivo.SUONA and suonati[-1] == "dal_vivo_ripresa"
        # Della pausa ne mancavano 3,5 secondi: a velocità 4 durano meno di uno.
        assert vivo.scorri_fino(lambda: f.riproduttore.posizione() >= f.resa.secondi(ripresa.t) - 1e-9) == pytest.approx(restavano / 4, abs=0.06)
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()


def test_la_partita_suona_al_suo_volume(app_wx, suonati):
    # Decisione D30: il volume della partita viene dalle impostazioni, e quello degli effetti non lo tocca.
    suoni.imposta_volume(0)
    vivo = Vivo(impostazioni=impostazioni.valide({"volume_partita": 40, "volume_effetti": 0}))
    try:
        f = vivo.finestra
        assert f.volume == 40
        f.al_prosegui()
        atteso = ps.per_la_cassa(ps.componi(f.segmento.eventi, "A", da=f.segmento.inizio, fine=f.segmento.fine, anticipo=ps.ANTICIPO).buffer, 40)
        assert np.any(atteso)
        assert np.array_equal(vivo.cassa.buffer[0][:len(atteso)], atteso)
        assert not np.any(vivo.cassa.buffer[0][len(atteso):])
    finally:
        vivo.finestra.timer.Stop()
        vivo.finestra.Destroy()
    # A volume zero la partita tace, ma il tempo scorre e la tranche finisce lo stesso.
    muta = Vivo(impostazioni=impostazioni.valide({"volume_partita": 0}))
    try:
        f = muta.finestra
        f.al_prosegui()
        assert f.stato == dal_vivo.SUONA and muta.cassa.buffer == []
        muta.fino_a_fermo()
        assert f.stato == dal_vivo.FERMO and muta.testo().endswith("Fine del riscaldamento.")
    finally:
        muta.finestra.timer.Stop()
        muta.finestra.Destroy()
