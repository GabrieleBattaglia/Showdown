"""
Test della gara a squadre e del ritiro nella finestra dal vivo, tappa 12, punti 7.4 e 8.9 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Sul desktop nascosto del conftest, con la cassa finta e l'orologio finto, senza suonare: la gara a
squadre in differita si ascolta fino alla fine, dalla parte della tua squadra, col titolo e la guida
che lo dicono; il cambio al tavolo ha il suo suono e il campo dice chi gioca; il gemello rifatto dalla
differita dà gli stessi punti della gara registrata. Il ritiro ha il suo suono e una fermata sua,
prima del triplice fischio, e si sente col fuoco su Prosegui.
"""

import random

import pytest
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

import partita_sonora as ps
import testi
from gui import dal_vivo
from gui.dal_vivo import FinestraDalVivo
from motore import COMPLETO, ESSENZIALE, SINGOLARE_3, SQUADRE, Incontro, Squadra, cronaca
from motore import eventi as E
from partita import differita_squadre, gemello_da_differita, nomi_dell_incontro


@pytest.fixture(autouse=True)
def cassa_vera_muta(monkeypatch):
    vieta_la_cassa_vera(monkeypatch)


class Sempre(random.Random):
    """Un generatore truccato: ogni estrazione che può succedere succede, come nelle prove del ritiro."""

    def random(self):
        return 0.0


def _squadre():
    a = Squadra("Club Di Prova", (giocatore(1, 12.0, cognome="Rossi"), giocatore(2, 11.0, cognome="Verdi"), giocatore(3, 11.5, sesso="f", cognome="Neri")))
    b = Squadra("PoliTeam04", (giocatore(4, 12.0, cognome="Bianchi"), giocatore(5, 11.0, sesso="f", cognome="Gialli"),
                              giocatore(6, 11.5, sesso="f", cognome="Blu"), giocatore(7, 10.0, cognome="Viola")))
    return a, b


def _tutto(finestra, orologio, massimo=20000):
    """Ascolta tutta la gara con Ascolta fino a fine set, un battito dopo l'altro; restituisce i testi del campo a fine tranche."""
    testi_visti = []
    battiti = 0
    while finestra.stato != dal_vivo.FINITO:
        if finestra.stato == dal_vivo.FERMO:
            finestra.fino_a_fine_set()
        orologio.adesso += 0.05
        finestra.al_battito()
        battiti += 1
        assert battiti < massimo, "la gara non finisce mai"
        if finestra.stato != dal_vivo.SUONA:
            testi_visti.append(finestra.cronaca.GetValue())
    return testi_visti


def test_la_gara_a_squadre_in_differita_si_ascolta_dalla_parte_della_tua_squadra(app_wx, suonati, monkeypatch):
    a, b = _squadre()
    registrato = Incontro(a, b, SQUADRE, seme=21, dettaglio=ESSENZIALE).gioca()
    differita = differita_squadre(a, b, {}, None)
    gemello = gemello_da_differita(differita, 21, velocita=4)
    nomi = nomi_dell_incontro(gemello)
    posati = []
    vero_componi = ps.componi

    def componi(eventi, *args, **kwargs):
        resa = vero_componi(eventi, *args, **kwargs)
        posati.extend(p.ruolo for p in resa.posati)
        return resa

    monkeypatch.setattr(ps, "componi", componi)
    orologio = Orologio()
    finestra = FinestraDalVivo(None, gemello, nomi, cronaca.NORMALE, 4, cassa=CassaFinta(), orologio=orologio, ascoltatore="B", differita=True)
    try:
        assert finestra.GetTitle() == "In differita, Club Di Prova contro PoliTeam04, velocità 4"
        guida = finestra.cronaca.GetValue()
        assert guida.startswith("Partita in differita: Club Di Prova contro PoliTeam04, gara a squadre, un set a 31 punti.")
        assert "Ascolti da PoliTeam04" in guida and "Alt+L passa dalla parte dell'altra squadra" in guida and "\n\n" not in guida
        assert finestra.lato.GetLabel() == "Cambia &lato, ora ascolti da PoliTeam04"
        visti = _tutto(finestra, orologio)
        assert finestra.stato == dal_vivo.FINITO
        assert "cambio_al_tavolo" in posati and "fischio_triplo" in posati
        campo = "\n".join(visti)
        assert "Al tavolo " in campo and "L'arbitro legge le formazioni: Club Di Prova con Rossi, Verdi e Neri" in campo
        assert "\n\n" not in campo
    finally:
        finestra.timer.Stop()
        finestra.Destroy()
    # Il gemello rifatto dalle fotografie dà gli stessi punti della gara registrata.
    rifatto = gemello_da_differita(differita, 21).gioca()
    assert rifatto.set == registrato.set and rifatto.punti == registrato.punti


def test_il_cambio_al_tavolo_ha_il_suo_suono_breve_dalla_parte_di_chi_entra():
    a, b = _squadre()
    risultato = Incontro(a, b, SQUADRE, seme=8, dettaglio=COMPLETO).gioca()
    cambi = [e for e in risultato.eventi if e.tipo == E.CAMBIO_AL_TAVOLO]
    assert cambi
    for evento in cambi:
        assert ps.suoni_fermi(evento) == [("cambio_al_tavolo", 0.0)]
        posati = ps.posati_dell_evento(evento)
        assert [p.ruolo for p in posati] == ["cambio_al_tavolo"] and posati[0].posizioni == [evento.pos]
    assert ps.durata_della_sorgente("cambio_al_tavolo") < 0.2
    # Il campo dice chi gioca adesso, a ogni livello, anche alla sintetica che non dice il cambio.
    nomi = cronaca.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
    voci = [(e, m, i == 0) for m in risultato.momenti for i, e in enumerate(m.eventi) if e.tipo == E.CAMBIO_AL_TAVOLO]
    for livello in cronaca.LIVELLI:
        righe = testi.righe_degli_eventi(voci, nomi, livello)
        assert sum(1 for r in righe if r.startswith("Al tavolo ")) == len(voci)


def _ritiro_completo():
    a, b = giocatore(1, cognome="Rossi"), giocatore(2, cognome="Bianchi", sesso="f")
    incontro = Incontro(a, b, SINGOLARE_3, seme=5, dettaglio=COMPLETO, basi_infortunio={1: 10.0}, caso_infortuni=Sempre())
    return a, b, incontro


def test_il_ritiro_ha_il_suo_suono_e_una_fermata_sua():
    _a, _b, incontro = _ritiro_completo()
    cronologia = ps.Cronologia(incontro)
    segmenti = []
    while (segmento := cronologia.prossimo(1.0)) is not None:
        segmenti.append(segmento)
    chiusure = [s.chiusura.tipo for s in segmenti]
    assert E.RITIRO in chiusure
    indice = chiusure.index(E.RITIRO)
    ritiro = segmenti[indice]
    assert not ritiro.fine_set and not ritiro.ultimo
    assert "ritiro" in [p.ruolo for p in ps.posa(ritiro.udibili)]
    # Il triplice fischio e la fine dell'incontro vengono nel segmento dopo, l'ultimo.
    ultimo = segmenti[indice + 1]
    assert ultimo.ultimo and any(e.tipo == E.FISCHIO and e.fischio == E.TRIPLO for e in ultimo.eventi)
    assert segmenti[indice - 1].chiusura.tipo == E.FINE_SET
    assert ps.SUONI["ritiro"] == "mess_partita_ritiro"


def test_il_ritiro_si_sente_col_fuoco_su_prosegui(app_wx, suonati):
    a, b, incontro = _ritiro_completo()
    nomi = cronaca.nomi_dei_giocatori([a, b])
    orologio = Orologio()
    finestra = FinestraDalVivo(None, incontro, nomi, cronaca.NORMALE, 8, cassa=CassaFinta(), orologio=orologio)
    try:
        tranche = 0
        ritiro_letto = False
        while finestra.stato != dal_vivo.FINITO and tranche < 400:
            finestra.al_prosegui()
            tranche += 1
            while finestra.stato == dal_vivo.SUONA:
                orologio.adesso += 0.05
                finestra.al_battito()
            testo = finestra.cronaca.GetValue()
            if "non può continuare: si ritira" in testo:
                ritiro_letto = True
                # La fermata del ritiro: l'incontro non è ancora finito, il triplice fischio viene dopo.
                assert finestra.stato == dal_vivo.FERMO and "Fine dell'incontro" not in testo
        assert ritiro_letto and finestra.stato == dal_vivo.FINITO
        assert "Fine dell'incontro: vince Bianchi per ritiro" in finestra.cronaca.GetValue()
    finally:
        finestra.timer.Stop()
        finestra.Destroy()
