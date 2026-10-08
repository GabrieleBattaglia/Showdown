"""
Test della partita sonora della tappa 10, partita_sonora.py, senza mai suonare: la cassa vera di
Acusticator fa fallire chi la chiama, e la riproduzione usa una cassa finta e un orologio finto.
Lo spazio: i valori del prototipo come predefiniti, il lato giusto per A e per B, le leggi che si
sostituiscono. La composizione: ogni suono al suo campione, il silenzio in testa accorciato, il volo
che attraversa il tavolo, il suono scelto da tipo, esito e causa, il margine anche al volume massimo,
con lo stesso fattore per ogni buffer, e la paletta che suona nel riscaldamento. La riproduzione: la
coda di zeri, la posizione, la pausa con la maniglia, le code che finiscono, la rampa di chi riparte a
metà. La cronologia: i segmenti fino a ogni punto, sanzione o fine set, che coprono tutto l'incontro;
la velocità di gioco che accorcia pause e procedura e lascia l'azione a tempo reale, con gli stessi
punti; i tratti di procedura di ogni segmento e le pieghe che li fanno durare quanto vuole la velocità.
Dalla decisione D30: il volume della partita, che cresce fino a 100 e al predefinito suona come
l'ascolto libero, e le pause lunghe di ogni segmento, con la pausa di sempre che resta prima.
"""

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from aiuti_dal_vivo import CassaFinta, Orologio, vieta_la_cassa_vera
from aiuti_motore import giocatore

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import resa_prototipo as resa

import impostazioni
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


@pytest.mark.parametrize("volume_partita", [0, 25, 50, 95, 100])
def test_il_margine_tiene_anche_al_volume_massimo(volume_partita):
    battute = [_evento(n, 0.2 * n, E.BATTUTA, (61.0, 25.0), chi=1, parte="A") for n in range(1, 6)]
    buffer = ps.componi(battute, "A").buffer * 1.5
    pronto = ps.per_la_cassa(buffer, volume_partita)
    assert float(np.max(np.abs(pronto))) <= ps.TETTO
    if volume_partita == 0:
        assert not np.any(pronto)
    if volume_partita == 25:
        fattore = ps.fattore_del_volume(25)
        assert np.allclose(pronto, buffer * fattore, atol=1e-6) or float(np.max(np.abs(pronto))) == pytest.approx(ps.TETTO, abs=1e-6)


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


# Le correzioni della revisione: il livello uguale per ogni buffer, la paletta nel riscaldamento,
# la rampa della ripartenza e le pieghe della procedura.

def test_il_volume_della_partita_cresce_fino_in_fondo():
    # Decisione D30: il volume della partita moltiplica il buffer in proporzione da 0 a 100, senza
    # fermarsi a metà come faceva il volume degli effetti oltre il 53.
    fattori = [ps.fattore_del_volume(v) for v in range(101)]
    assert fattori[0] == 0.0 and all(b > a for a, b in itertools.pairwise(fattori))
    assert fattori[50] == pytest.approx(2 * fattori[25]) and fattori[100] == pytest.approx(2 * fattori[50])
    # A 100 il picco di progetto arriva al tetto, senza superarlo; fuori scala vale il bordo.
    assert ps.PICCO_DI_PROGETTO * fattori[100] == pytest.approx(ps.TETTO)
    assert ps.fattore_del_volume(150) == fattori[100] and ps.fattore_del_volume(-5) == 0.0
    # Al volume di progetto, 95, il predefinito delle impostazioni, il fattore è quello dell'ascolto libero approvato.
    assert ps.VOLUME_DI_PROGETTO == 95 == impostazioni.VOLUME_PARTITA_PREDEFINITO == impostazioni.PREDEFINITE["volume_partita"]
    assert ps.fattore_del_volume(ps.VOLUME_DI_PROGETTO) == pytest.approx(resa.GUADAGNO_PARTITA) == pytest.approx(1.0)
    assert (ps.TETTO, ps.GUADAGNO_PARTITA) == (resa.TETTO, resa.GUADAGNO_PARTITA)
    segmento = _segmenti(_incontro())[3]
    buffer = ps.componi(segmento.eventi, "A", da=segmento.inizio, fine=segmento.fine).buffer
    assert np.allclose(ps.per_la_cassa(buffer, impostazioni.VOLUME_PARTITA_PREDEFINITO), resa.con_margine(buffer), atol=1e-6)
    # E il volume più alto suona davvero più forte di quello di progetto, che è già vicino al tetto.
    assert float(np.max(np.abs(ps.per_la_cassa(buffer, 100)))) > float(np.max(np.abs(ps.per_la_cassa(buffer, 95))))


def test_il_fattore_del_volume_e_lo_stesso_per_ogni_buffer():
    segmenti = _segmenti(_incontro())
    for livello in (75, 100):
        fattore = np.float32(ps.fattore_del_volume(livello))
        for segmento in segmenti[1:7]:
            for ascoltatore in ("A", "B"):
                buffer = ps.componi(segmento.eventi, ascoltatore, da=segmento.inizio, fine=segmento.fine).buffer
                assert float(np.max(np.abs(buffer))) <= ps.PICCO_DI_PROGETTO
                # Nessun buffer viene abbassato per conto suo: tutti per lo stesso fattore, punto dopo punto e lato per lato.
                assert np.array_equal(ps.per_la_cassa(buffer, livello), buffer * fattore)


def test_nel_riscaldamento_la_paletta_di_chi_riceve_suona():
    preliminari = _segmenti(_incontro())[0]
    sulla_paletta = [e for e in preliminari.eventi if e.tipo == E.RISCALDAMENTO_COLPO and e.volo[-1].tipo == "paletta"]
    assert len(sulla_paletta) > 10
    parate = [p for p in ps.posa(preliminari.eventi) if p.ruolo == "parata"]
    # Una parata per ogni volo che arriva sulla paletta, al suo istante e nel suo punto, con il giro delle varianti.
    assert [(p.t, p.posizioni[0]) for p in parate] == [(e.volo[-1].t, (e.volo[-1].x, e.volo[-1].y)) for e in sulla_paletta]
    assert [p.variante for p in parate[:5]] == [0, 1, 2, 3, 0]
    # Nel gioco la paletta del volo resta muta: suona la parata, che è un evento a sé.
    volo = [e for s in _segmenti(_incontro())[1:4] for e in s.eventi if e.tipo == E.VOLO and e.volo[-1].tipo == "paletta"]
    assert volo and not [p for p in ps.posati_del_volo(volo[0]) if p.ruolo == "parata"]


def test_la_ripartenza_a_meta_ha_la_rampa_in_testa():
    cassa, orologio = CassaFinta(), Orologio()
    rip = ps.Riproduttore(cassa, orologio)
    buffer = _rumore(2.0)
    rip.suona(buffer, da=1.0, anticipo=0.3)
    acceso = cassa.buffer[0]
    testa, rampa = round(0.3 * FS), round(ps.SFUMATURA * FS)
    # Dopo il silenzio dell'attesa il primo campione è zero, e la rampa sale per cinque millesimi.
    assert not np.any(acceso[:testa + 1])
    assert np.all(np.diff(acceso[testa:testa + rampa, 0]) > 0)
    assert np.array_equal(acceso[testa + rampa:testa + round(1.0 * FS)], buffer[round(1.0 * FS) + rampa:])
    assert rip.in_anticipo()
    orologio.adesso += 0.31
    assert not rip.in_anticipo()
    # Da capo niente rampa: il buffer comincia già col suo silenzio.
    rip.suona(buffer)
    assert np.array_equal(cassa.buffer[1][:len(buffer)], buffer)
    # Con tieni_le_code si ferma soltanto il buffer corrente, e la coda di quello di prima va avanti.
    rip.suona(buffer, sovrapponi=True)
    rip.suona(buffer, da=0.5, tieni_le_code=True)
    assert cassa.maniglie[1].fermate == 0 and cassa.maniglie[2].fermate == 1 and cassa.accese == 2


def test_le_pieghe_spostano_quello_che_viene_dopo():
    pieghe = ((2.0, 6.0, 0.25),)
    assert ps.secondi_del_buffer(1.0, 0.0, pieghe) == 1.0
    assert ps.secondi_del_buffer(4.0, 0.0, pieghe) == pytest.approx(2.5)
    assert ps.secondi_del_buffer(10.0, 0.0, pieghe) == pytest.approx(7.0)
    assert ps.secondi_del_buffer(10.0, 3.0, pieghe) == pytest.approx(4.75)
    for s in (0.5, 2.2, 2.9, 3.0, 6.5):
        assert ps.secondi_del_buffer(ps.istante_del_motore(s, 0.0, pieghe), 0.0, pieghe) == pytest.approx(s)
    # Una piega che allunga, per chi rallenta.
    assert ps.secondi_del_buffer(10.0, 1.0, ((2.0, 4.0, 2.0),)) == pytest.approx(11.0)
    # Due battute, a 1 e a 8 secondi, con la procedura in mezzo ripiegata a un quarto: la seconda arriva tre secondi prima, uguale.
    battute = [_evento(1, 1.0, E.BATTUTA, (61.0, 25.0), chi=1, parte="A"), _evento(2, 8.0, E.BATTUTA, (61.0, 25.0), chi=1, parte="A")]
    dritto = ps.componi(battute, "A", da=0.0)
    piegato = ps.componi(battute, "A", da=0.0, pieghe=pieghe)
    n = len(piegato.posati[1].mono)
    assert piegato.pieghe == pieghe and piegato.durata == pytest.approx(dritto.durata - 3.0, abs=2 / FS)
    assert np.array_equal(piegato.buffer[:round(2.0 * FS)], dritto.buffer[:round(2.0 * FS)])
    assert np.array_equal(piegato.buffer[round(5.0 * FS):round(5.0 * FS) + n], dritto.buffer[round(8.0 * FS):round(8.0 * FS) + n])
    assert piegato.secondi(8.0) == pytest.approx(5.0) and piegato.istante(5.0) == pytest.approx(8.0)
    assert piegato.in_silenzio(3.0) and not piegato.in_silenzio(5.0)


def test_ripiega_solo_quello_che_non_e_ancora_suonato():
    procedure = [(1.0, 3.0, 1.0), (5.0, 65.0, 1.0)]
    assert ps.ripiega(procedure, 1) == ()
    gia = ps.ripiega(procedure, 4)
    assert gia == ((1.0, 3.0, 0.25), (5.0, 65.0, 0.25))
    # Dal secondo 20 del motore a velocità 8: quello che è già suonato resta com'era.
    nuove = ps.ripiega(procedure, 8, gia, da=20.0)
    assert nuove == ((1.0, 3.0, 0.25), (5.0, 20.0, 0.25), (20.0, 65.0, 0.125))
    # Tornando alla velocità a cui il motore l'ha svolto, il resto non si piega più.
    assert ps.ripiega(procedure, 1, nuove, da=30.0) == ((1.0, 3.0, 0.25), (5.0, 20.0, 0.25), (20.0, 30.0, 0.125))
    # Alla stessa velocità non cambia niente: le pieghe contigue allo stesso fattore si fondono.
    assert ps.ripiega(procedure, 4, gia, da=20.0) == gia


def test_i_tratti_di_procedura_sono_il_tempo_che_la_velocita_accorcia():
    eventi, tratti = {}, {}
    for velocita in (1.0, 4.0):
        segmenti = _segmenti(_incontro(velocita, seme=5), velocita)
        eventi[velocita] = [e for s in segmenti for e in s.eventi]
        tratti[velocita] = [t for s in segmenti for t in s.procedure]
        assert {v for _a, _b, v in tratti[velocita]} == {velocita}
    tipi = {e.tipo for e in eventi[1.0]}
    assert {E.TIMEOUT_INIZIO, E.CAMBIO_CAMPO_INIZIO} <= tipi

    def azione(velocita, i):
        """Il tempo fra l'evento i e il seguente che non è pausa né procedura: non dipende dalla velocità."""
        a, b = eventi[velocita][i].t, eventi[velocita][i + 1].t
        return (b - a) - sum(max(0.0, min(b, tb) - max(a, ta)) for ta, tb, _v in tratti[velocita] if ta < b and tb > a)

    for i in range(len(eventi[1.0]) - 1):
        assert azione(1.0, i) == pytest.approx(azione(4.0, i), abs=0.004), (eventi[1.0][i].tipo, eventi[1.0][i + 1].tipo)


# La decisione D30: le pause lunghe, che non si sentono mai, e la pausa di sempre che resta.

def test_il_segmento_sa_se_ha_una_pausa_lunga():
    segmenti = _segmenti(_incontro(seme=50))
    con_la_pausa = [s for s in segmenti if s.pausa_lunga]
    # Ogni set comincia con la sua pausa lunga, l'inizio del set; poi i due time-out e il cambio campo del terzo set.
    tipi = [{e.tipo for e in s.preambolo} & ps.PAUSE_LUNGHE for s in con_la_pausa]
    assert sum(E.INIZIO_SET in t for t in tipi) == 3
    assert sum(E.TIMEOUT_INIZIO in t for t in tipi) == 2 and sum(E.CAMBIO_CAMPO_INIZIO in t for t in tipi) == 3
    for s in segmenti:
        # Il preambolo è tutto quello che viene prima della ripresa del gioco, e la ripresa è l'inizio.
        assert all(e.t <= s.inizio + ps.TOLLERANZA for e in s.preambolo)
        if s.preambolo:
            assert s.eventi[len(s.preambolo)].t == s.inizio
        if not s.pausa_lunga:
            assert not {e.tipo for e in s.eventi[:len(s.preambolo)]} & ps.PAUSE_LUNGHE
    # Il riscaldamento non ha preambolo: comincia con l'incontro.
    assert segmenti[0].riscaldamento and segmenti[0].preambolo == [] and not segmenti[0].pausa_lunga


def test_la_pausa_di_sempre_prima_della_pausa_lunga():
    for velocita in (1.0, 4.0):
        segmenti = _segmenti(_incontro(velocita, seme=50), velocita)
        for precedente, segmento in itertools.pairwise(segmenti):
            primo = segmento.eventi[0]
            if any(e.tipo == E.TIMEOUT_INIZIO for e in segmento.preambolo):
                # Dopo il punto il motore lascia la pausa fra i punti, alla velocità di gioco; poi il fischio del time-out.
                assert precedente.chiusura.tipo == E.PUNTO and primo.tipo == E.FISCHIO
                assert segmento.attesa_prima(precedente.fine, velocita) == pytest.approx(5.5 / velocita, abs=0.002)
                # Alla velocità di adesso, se è cambiata, la pausa si ripiega come tutta la procedura.
                assert segmento.attesa_prima(precedente.fine, 8) == pytest.approx(5.5 / 8, abs=0.002)
            if precedente.riscaldamento:
                # Dopo il riscaldamento il primo set comincia subito: la sua pausa lunga non lascia niente prima.
                assert segmento.pausa_lunga and primo.tipo == E.INIZIO_SET
                assert segmento.attesa_prima(precedente.fine, velocita) == pytest.approx(0.0, abs=0.002)
