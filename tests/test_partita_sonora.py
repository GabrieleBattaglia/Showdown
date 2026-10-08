"""
Test della partita sonora della tappa 10, partita_sonora.py, senza mai suonare: la cassa vera di
Acusticator fa fallire chi la chiama, e la riproduzione usa una cassa finta e un orologio finto.
Lo spazio: i valori del prototipo come predefiniti, il lato giusto per A e per B, le leggi che si
sostituiscono. La composizione: ogni suono al suo campione, il silenzio in testa accorciato, il volo
che attraversa il tavolo, il suono scelto da tipo, esito e causa, il margine anche al volume massimo.
La riproduzione: la coda di zeri, la posizione, la pausa con la maniglia, le code che finiscono. La
cronologia: i segmenti fino a ogni punto, sanzione o fine set, che coprono tutto l'incontro; la
velocità di gioco che accorcia pause e procedura e lascia l'azione a tempo reale, con gli stessi punti.
"""

import math

import numpy as np
import pytest
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

import partita_sonora as ps
from motore import COMPLETO, SINGOLARE_3, Incontro
from motore import eventi as E
from motore.eventi import Evento
from motore.tavolo import traiettoria, vista, volume

FS = ps.FS


@pytest.fixture(autouse=True)
def cassa_vera_muta(monkeypatch):
    vieta_la_cassa_vera(monkeypatch)


def _evento(n, t, tipo, pos=None, **campi):
    return Evento(n=n, t=t, tipo=tipo, fase=E.GIOCO, pos=pos, **campi)


def _energia(stereo):
    return float(np.sum(stereo[:, 0] ** 2)), float(np.sum(stereo[:, 1] ** 2))


# Lo spazio.

def test_lo_spazio_predefinito_e_quello_del_prototipo():
    spazio = ps.Spazio()
    for pos in ((10.0, 20.0), (61.0, 183.0), (110.0, 340.0), (-40.0, 183.0)):
        for ascoltatore in ("A", "B"):
            pan, vol, taglio = spazio.punto(pos, ascoltatore)
            pan_motore, distanza, _lato = vista(pos, ascoltatore)
            assert pan == pytest.approx(pan_motore)
            assert vol == pytest.approx(volume(distanza))
            assert taglio == pytest.approx(min(18000.0, max(1500.0, 18000.0 * 60.0 / max(distanza, 60.0))))


def test_la_sinistra_di_a_e_la_destra_di_b():
    spazio = ps.SPAZIO
    pan_a, vol_a, taglio_a = spazio.punto((15.0, 30.0), "A")
    pan_b, vol_b, taglio_b = spazio.punto((15.0, 30.0), "B")
    assert pan_a < -0.5 and pan_b > 0.5
    # Vicino ad A: per A è forte e chiaro, per B, all'altra testata, piano e cupo.
    assert vol_a > 2 * vol_b and taglio_a > taglio_b


def test_le_leggi_dello_spazio_si_sostituiscono():
    ombra = ps.Spazio(cupo_solo_dietro_lo_schermo=True)
    assert ombra.punto((61.0, 150.0), "A")[2] == ombra.taglio_massimo
    assert ombra.punto((61.0, 300.0), "A")[2] < ombra.taglio_massimo
    stretta = ps.Spazio(larghezza_lontana=0.5)
    assert stretta.punto((10.0, 366.0), "A")[0] == pytest.approx(0.5 * ps.SPAZIO.punto((10.0, 366.0), "A")[0])
    assert stretta.punto((10.0, 100.0), "A")[0] == pytest.approx(ps.SPAZIO.punto((10.0, 100.0), "A")[0])
    # Per B la metà lontana è quella di A.
    assert stretta.punto((10.0, 0.0), "B")[0] == pytest.approx(0.5 * ps.SPAZIO.punto((10.0, 0.0), "B")[0])
    piano = ps.Spazio(volume_riferimento=75.0)
    assert piano.punto((61.0, 300.0), "A")[1] < ps.SPAZIO.punto((61.0, 300.0), "A")[1]


# La composizione.

def test_ogni_suono_cade_al_suo_campione():
    battuta = _evento(1, 10.0, E.BATTUTA, (40.0, 25.0), chi=1, parte="A")
    parata = _evento(2, 10.537, E.PARATA, (80.0, 340.0), chi=2, parte="B")
    resa = ps.componi([battuta, parata], "A", da=9.9)
    assert resa.t0 == 9.9
    atteso = np.zeros_like(resa.buffer)
    for posato in resa.posati:
        stereo = ps.spazializza(posato, "A")
        inizio = round((posato.t - 9.9) * FS)
        atteso[inizio:inizio + len(stereo)] += stereo
    assert np.array_equal(resa.buffer, atteso)
    assert [round((p.t - resa.t0) * FS) for p in resa.posati] == [round(0.1 * FS), round(0.637 * FS)]
    # Il primo campione che suona è quello della battuta, esatto.
    sola = ps.componi([battuta], "A", da=9.5)
    sorgente = ps.sorgente("battuta")
    primo = int(np.flatnonzero(sorgente)[0])
    assert int(np.flatnonzero(np.abs(sola.buffer[:, 0]) > 0)[0]) == round(0.5 * FS) + primo


def test_il_silenzio_in_testa_si_accorcia_e_la_fine_si_allunga():
    battuta = _evento(1, 10.0, E.BATTUTA, (40.0, 25.0), chi=1, parte="A")
    annuncio = _evento(2, 6.0, E.ANNUNCIO, (-40.0, 183.0), durata=1.6)
    resa = ps.componi([annuncio, battuta], "A", da=5.0, fine=14.0, anticipo=ps.ANTICIPO)
    assert resa.t0 == pytest.approx(10.0 - ps.ANTICIPO)
    assert resa.durata >= 14.0 - resa.t0
    # Senza anticipo il buffer comincia da da, e gli eventi di prima non suonano.
    intera = ps.componi([annuncio, battuta], "A", da=5.0)
    assert intera.t0 == 5.0
    assert ps.componi([battuta], "A", da=10.5).posati == []


def test_il_lato_e_la_distanza_per_a_e_per_b():
    battuta = _evento(1, 3.0, E.BATTUTA, (15.0, 30.0), chi=1, parte="A")
    per_a = ps.componi([battuta], "A").buffer
    per_b = ps.componi([battuta], "B").buffer
    sinistra_a, destra_a = _energia(per_a)
    sinistra_b, destra_b = _energia(per_b)
    assert sinistra_a > 4 * destra_a and destra_b > 4 * sinistra_b
    assert sinistra_a + destra_a > 4 * (sinistra_b + destra_b)


def test_la_diagonale_attraversa_il_tavolo():
    volo = traiettoria((110.0, 340.0), (15.0, 30.0), (), 420.0, 20.0, 40.0, 0.12, "paletta")
    evento = _evento(5, 20.0, E.VOLO, (15.0, 30.0), durata=volo[-1].t - volo[0].t, volo=volo, chi=2, parte="B")
    for ascoltatore, lato_iniziale in (("A", 1), ("B", 0)):
        resa = ps.componi([evento], ascoltatore)
        rotolamento = next(p for p in resa.posati if p.ruolo == "rotolamento")
        stereo = ps.spazializza(rotolamento, ascoltatore)
        quinto = len(stereo) // 5
        prima, ultima = _energia(stereo[:quinto]), _energia(stereo[-quinto:])
        # Per A la pallina parte da destra e arriva a sinistra, per B il contrario.
        assert prima[lato_iniziale] > 3 * prima[1 - lato_iniziale]
        assert ultima[1 - lato_iniziale] > 3 * ultima[lato_iniziale]


def test_il_suono_si_sceglie_da_tipo_esito_e_causa():
    assert ps.suoni_fermi(_evento(1, 0.0, E.BATTUTA, causa="battuta_a_vuoto")) == [("colpo_a_vuoto", 0.0)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.BATTUTA, causa="battuta_doppio_tocco")) == [("battuta", 0.0), ("secondo_tocco", ps.RITARDO_SECONDO_TOCCO)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.COLPO, causa="paletta_caduta")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.FALLO, causa="paletta_caduta")) == [("paletta_caduta", 0.0)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.FALLO, causa="out_sponda")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.PARATA, causa="body_touch")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.PARATA, esito="goal")) == []
    assert ps.suoni_fermi(_evento(1, 0.0, E.PARATA, esito="ferma")) == [("parata", 0.0)]
    assert ps.suoni_fermi(_evento(1, 0.0, E.CHIAMATA)) == []


def test_due_rumori_di_fila_non_sono_uguali():
    parate = [_evento(n, 1.0 + n, E.PARATA, (61.0, 30.0), esito="ferma", chi=1, parte="A") for n in range(1, 4)]
    posati = ps.posa(parate)
    assert [p.variante for p in posati] == [0, 1, 2]
    assert not np.array_equal(posati[0].mono, posati[1].mono)


@pytest.mark.parametrize("volume_effetti", [0, 25, 50, 100])
def test_il_margine_tiene_anche_al_volume_massimo(volume_effetti):
    battute = [_evento(n, 0.2 * n, E.BATTUTA, (61.0, 25.0), chi=1, parte="A") for n in range(1, 6)]
    buffer = ps.componi(battute, "A").buffer * 1.5
    pronto = ps.per_la_cassa(buffer, volume_effetti)
    assert float(np.max(np.abs(pronto))) <= ps.TETTO
    if volume_effetti == 0:
        assert not np.any(pronto)
    if volume_effetti == 25:
        assert np.allclose(pronto, buffer * 0.5, atol=1e-6) or float(np.max(np.abs(pronto))) == pytest.approx(ps.TETTO, abs=1e-6)


def test_le_sorgenti_si_preparano_tutte():
    ps.svuota_cache()
    ps.prepara()
    ruoli = {chiave[0] for chiave in ps._CACHE}
    assert ruoli == set(ps.SUONI.values())


# La riproduzione.

def _rumore(secondi):
    return np.full((round(secondi * FS), 2), 0.25, dtype=np.float32)


def test_il_buffer_parte_con_la_coda_di_zeri_e_si_ferma_con_la_maniglia():
    cassa, orologio = CassaFinta(), Orologio()
    rip = ps.Riproduttore(cassa, orologio)
    voce = rip.suona(_rumore(2.0), anticipo=0.5)
    acceso = cassa.buffer[0]
    assert len(acceso) == round(0.5 * FS) + round(2.0 * FS) + round(ps.CODA_DI_ZERI * FS)
    assert not np.any(acceso[:round(0.5 * FS)]) and not np.any(acceso[-round(ps.CODA_DI_ZERI * FS):])
    assert rip.posizione() == 0.0
    orologio.adesso += 1.5
    assert rip.posizione() == pytest.approx(1.0)
    assert rip.ferma() == pytest.approx(1.0)
    assert cassa.maniglie[0].fermate == 1 and voce.maniglia is None
    # La ripresa riparte dal secondo della pausa.
    rip.suona(_rumore(2.0), da=1.0)
    assert len(cassa.buffer[1]) == round(1.0 * FS) + round(ps.CODA_DI_ZERI * FS)
    orologio.adesso += 0.99
    assert not rip.battito()
    orologio.adesso += 0.02
    assert rip.battito() and rip.finito()
    assert cassa.maniglie[1].fermate == 1


def test_le_code_finiscono_di_suonare_e_il_silenzio_non_va_alla_cassa():
    cassa, orologio = CassaFinta(), Orologio()
    rip = ps.Riproduttore(cassa, orologio)
    rip.suona(_rumore(1.0))
    orologio.adesso += 0.6
    rip.suona(_rumore(1.0), sovrapponi=True)
    assert cassa.maniglie[0].fermate == 0
    orologio.adesso += 0.5
    assert not rip.battito()
    assert cassa.maniglie[0].fermate == 1 and cassa.maniglie[1].fermate == 0
    rip.suona(np.zeros((FS, 2), dtype=np.float32))
    assert len(cassa.buffer) == 2 and cassa.maniglie[1].fermate == 1
    orologio.adesso += 0.4
    assert rip.posizione() == pytest.approx(0.4)


# La cronologia e la velocità di gioco.

def _incontro(velocita=1.0, seme=31):
    return Incontro(giocatore(1, 12.0), giocatore(2, 13.0), SINGOLARE_3, seme=seme, dettaglio=COMPLETO, velocita=velocita)


def _segmenti(incontro, velocita=None):
    cronologia = ps.Cronologia(incontro)
    segmenti = []
    while (segmento := cronologia.prossimo(velocita)) is not None:
        segmenti.append(segmento)
    return segmenti


def test_i_segmenti_coprono_tutto_l_incontro():
    riferimento = _incontro().gioca()
    segmenti = _segmenti(_incontro())
    assert [e.n for s in segmenti for e in s.eventi] == [e.n for e in riferimento.eventi]
    assert segmenti[0].riscaldamento and segmenti[0].chiusura.tipo == E.RISCALDAMENTO_FINE
    assert segmenti[-1].ultimo and segmenti[-1].chiusura.tipo == E.FINE_INCONTRO
    chiusure = [s.chiusura.tipo for s in segmenti[1:]]
    assert set(chiusure) <= {E.PUNTO, E.RIPETIZIONE, E.AMMONIZIONE, E.PENALITA, E.FINE_SET, E.FINE_INCONTRO}
    assert chiusure.count(E.FINE_SET) == len(riferimento.set) - 1
    assert sum(1 for s in segmenti if s.fine_set) == len(riferimento.set)
    for segmento in segmenti:
        # Un punto che non chiude il suo segmento è quello che chiude il set, e sta col fischio lungo.
        dentro = [e for e in segmento.eventi[:-1] if e.tipo in (E.PUNTO, E.PENALITA)]
        assert len(dentro) <= 1
        if dentro:
            assert segmento.fine_set and ps.set_finito(dentro[0].punteggio, SINGOLARE_3)
        assert segmento.fine == pytest.approx(segmento.chiusura.t + segmento.chiusura.durata)
        assert segmento.eventi[0].t <= segmento.inizio <= segmento.fine
        # Si riparte dalla ripresa del gioco: il recupero o la consegna, se nel segmento c'è un punto.
        primo_del_punto = next((e for e, m, apre in segmento.voci if apre and m.genere == "punto"), None)
        if primo_del_punto is not None and not any(e.tipo in ps.SANZIONI for e in segmento.eventi):
            assert primo_del_punto.tipo in (E.RECUPERO, E.CONSEGNA) and segmento.inizio == primo_del_punto.t


def test_la_velocita_accorcia_pause_e_procedura_e_non_l_azione():
    lento = _incontro(1.0).gioca()
    veloce = _incontro(4.0).gioca()
    assert veloce.set == lento.set and [p.esito for p in veloce.punti] == [p.esito for p in lento.punti]
    assert veloce.durata_simulata < 0.75 * lento.durata_simulata
    reali = (E.VOLO, E.CONTROLLO, E.FISCHIO, E.CONSEGNA)
    scalati = (E.RECUPERO, E.ANNUNCIO, E.DOMANDA_PRONTO, E.CHIAMATA, E.SORTEGGIO)
    for m_lento, m_veloce in zip(lento.momenti, veloce.momenti, strict=True):
        tipi = [e.tipo for e in m_lento.eventi]
        assert tipi == [e.tipo for e in m_veloce.eventi]
        for e_lento, e_veloce in zip(m_lento.eventi, m_veloce.eventi, strict=True):
            if e_lento.tipo in reali:
                assert e_veloce.durata == pytest.approx(e_lento.durata, abs=1e-6)
            elif e_lento.tipo in scalati:
                assert e_veloce.durata == pytest.approx(e_lento.durata / 4, abs=2e-3)
        # Dal fischio del via alla battuta è azione: resta a tempo reale.
        if m_lento.genere == "punto" and E.FISCHIO in tipi and E.BATTUTA in tipi:
            via, battuta = tipi.index(E.FISCHIO), tipi.index(E.BATTUTA)
            if via < battuta:
                assert m_veloce.eventi[battuta].t - m_veloce.eventi[via].t == pytest.approx(m_lento.eventi[battuta].t - m_lento.eventi[via].t, abs=2e-3)
    # La pausa fra due punti, dal punto alla ripresa che segue, è un quarto.
    pause = []
    for risultato in (lento, veloce):
        eventi = risultato.eventi
        indice = next(i for i, e in enumerate(eventi) if e.tipo == E.PUNTO and eventi[i + 1].tipo in (E.RECUPERO, E.CONSEGNA))
        pause.append(eventi[indice + 1].t - eventi[indice].t)
    assert pause[1] == pytest.approx(pause[0] / 4, abs=2e-3)


def test_la_velocita_cambia_a_meta_incontro_con_gli_stessi_punti():
    riferimento = _incontro().gioca()
    gemello = _incontro()
    cronologia = ps.Cronologia(gemello)
    velocita = 1.0
    while cronologia.prossimo(velocita) is not None:
        assert gemello.regia.velocita == velocita
        velocita = 1.0 + (velocita % 8)
    assert gemello.risultato.set == riferimento.set
    assert gemello.risultato.durata_simulata < riferimento.durata_simulata
    with pytest.raises(ValueError, match="maggiore di zero"):
        _incontro().imposta_velocita(0)


def test_ogni_segmento_si_compone_dentro_il_margine():
    segmenti = _segmenti(_incontro(seme=5), 3.0)
    ultimo_fine = None
    for indice, segmento in enumerate(segmenti[:12]):
        fresco = indice % 2 == 0 or ultimo_fine is None
        da = segmento.inizio if fresco else ultimo_fine
        resa = ps.componi(segmento.eventi, "A" if indice % 3 else "B", da=da, fine=segmento.fine, anticipo=ps.ANTICIPO if fresco else None)
        assert resa.durata >= segmento.fine - resa.t0 - 1 / FS
        assert float(np.max(np.abs(ps.per_la_cassa(resa.buffer, 100)))) <= ps.TETTO
        assert math.isfinite(float(np.sum(resa.buffer)))
        ultimo_fine = segmento.fine
