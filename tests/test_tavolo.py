"""
Test del tavolo: riferimento, specchio, vista di chi ascolta, traiettorie col metodo delle
immagini, battuta con una sponda prima dello schermo, zone dei colpi e lato dell'arbitro.
"""

import itertools
import math
import random

import pytest
from aiuti_motore import giocatore

from costanti import LARGHEZZA_TAVOLO, META_TAVOLO
from motore import eventi as E
from motore.incontro import COMPLETO, SINGOLARE_3, Incontro
from motore.taratura import TARATURA
from motore.tavolo import (
    FONDO_B,
    SPONDA_DESTRA_A,
    SPONDA_SINISTRA_A,
    distanza_di,
    in_area_di_porta,
    in_tasca,
    intervallo_zona,
    lato_di,
    locale_in_assoluto,
    partenza_massima_battuta,
    posizione_al_tempo,
    posizione_arbitro,
    specchia,
    sponda_assoluta,
    traiettoria,
    vista,
    zona_di_difesa,
)


def test_specchio_due_volte_e_l_identita():
    for x, y in ((0, 0), (12.5, 300), (61, 183), (122, 366)):
        assert specchia(*specchia(x, y)) == (x, y)
    assert locale_in_assoluto("A", 20, 30) == (20, 30)
    assert locale_in_assoluto("B", 20, 30) == (102, 336)


def test_la_vista_ribalta_pan_e_lato_per_b():
    punto = (100.0, 300.0)
    pan_a, distanza_a, lato_a = vista(punto, "A")
    pan_b, distanza_b, lato_b = vista(punto, "B")
    assert pan_a == pytest.approx(-pan_b)
    assert (lato_a, lato_b) == ("destra", "sinistra")
    assert distanza_a == pytest.approx(math.hypot(39, 340))
    assert distanza_b == pytest.approx(math.hypot(39, 106))
    assert lato_di(61, "A") == lato_di(61, "B") == "centro"
    assert zona_di_difesa(10, "A") == "sx" and zona_di_difesa(10, "B") == "dx"
    assert distanza_di(50, "A") == 50 and distanza_di(50, "B") == 316


def test_area_di_porta_e_tasca():
    assert in_tasca((61, 10), "A") and in_area_di_porta((61, 18), "A") and not in_tasca((61, 18), "A")
    assert not in_area_di_porta((61, 25), "A")
    assert in_area_di_porta((61, 350), "B")


def _controlla_rimbalzi(volo):
    """Ogni rimbalzo sta su una sponda, con l'angolo d'uscita uguale a quello d'entrata."""
    for prima, rimbalzo, dopo in zip(volo, volo[1:], volo[2:], strict=False):
        if rimbalzo.tipo not in ("sponda", "curva"):
            continue
        assert rimbalzo.x in (SPONDA_SINISTRA_A, SPONDA_DESTRA_A)
        entrata = abs((rimbalzo.x - prima.x) / (rimbalzo.y - prima.y))
        uscita = abs((dopo.x - rimbalzo.x) / (dopo.y - rimbalzo.y))
        assert entrata == pytest.approx(uscita, rel=1e-6)


def _senza_tappe_di_schermo(volo):
    return [tappa for tappa in volo if tappa.tipo != "sotto_schermo"]


def test_traiettorie_con_sponde():
    volo = traiettoria((61, 30), (100, 340), (SPONDA_SINISTRA_A, SPONDA_DESTRA_A, SPONDA_SINISTRA_A), 600, 2.0, 40, 0.12)
    assert [t.tipo for t in volo].count("sponda") + [t.tipo for t in volo].count("curva") == 3
    assert [t.tipo for t in volo].count("sotto_schermo") == 1
    _controlla_rimbalzi(_senza_tappe_di_schermo(volo))
    for prima, dopo in itertools.pairwise(volo):
        assert dopo.t > prima.t
        assert dopo.v < prima.v
    assert volo[0].t == 2.0 and volo[-1].tipo == "arrivo"
    meta = posizione_al_tempo(volo, (volo[0].t + volo[-1].t) / 2)
    assert 0 <= meta[0] <= LARGHEZZA_TAVOLO and 30 < meta[1] < 340


def test_sponde_impossibili():
    with pytest.raises(E.ErroreMotore):
        traiettoria((61, 30), (100, 340), (SPONDA_SINISTRA_A, SPONDA_SINISTRA_A), 600, 0.0, 40, 0.12)


def test_la_battuta_tocca_una_sponda_prima_dello_schermo():
    rng = random.Random(5)
    for _ in range(300):
        destra = rng.random() < 0.5
        u_arrivo = rng.uniform(70.0, 116.0)
        v_arrivo = rng.uniform(331.0, 351.0)
        u_partenza = rng.uniform(61.0, max(61.0, min(100.0, partenza_massima_battuta(u_arrivo, v_arrivo))))
        if destra:
            u_arrivo, u_partenza = LARGHEZZA_TAVOLO - u_arrivo, LARGHEZZA_TAVOLO - u_partenza
        parte = rng.choice("AB")
        sponda = sponda_assoluta(parte, "destra" if destra else "sinistra")
        volo = traiettoria(locale_in_assoluto(parte, u_partenza, 25), locale_in_assoluto(parte, u_arrivo, v_arrivo), (sponda,), 450, 0.0, 40, 0.12)
        rimbalzi = [t for t in volo if t.tipo in ("sponda", "curva")]
        assert len(rimbalzi) == 1
        assert distanza_di(rimbalzi[0].y, parte) < META_TAVOLO
        assert [t.tipo for t in volo].count("sotto_schermo") == 1


@pytest.mark.parametrize("nome", sorted(TARATURA.COLPI))
def test_la_geometria_rende_la_zona_della_tabella(nome):
    colpo = TARATURA.COLPI[nome]
    rng = random.Random(nome)
    for parte in ("A", "B"):
        difensore = "B" if parte == "A" else "A"
        for _ in range(40):
            x_min, x_max = intervallo_zona(colpo.zona, difensore)
            x = rng.uniform(x_min, x_max)
            y = 340.0 if parte == "A" else 26.0
            if nome.startswith("battuta"):
                continue
            partenza = locale_in_assoluto(parte, colpo.partenza_u + rng.uniform(-8, 8), 30)
            sponde = tuple(sponda_assoluta(parte, s) for s in colpo.sponde)
            volo = traiettoria(partenza, (x, y), sponde, colpo.velocita, 0.0, 40, 0.12)
            rimbalzi = [t for t in volo if t.tipo in ("sponda", "curva")]
            assert [t.x for t in rimbalzi] == list(sponde)
            assert zona_di_difesa(volo[-1].x, difensore) == colpo.zona
            assert all(t.y <= FONDO_B for t in volo)


def test_l_arbitro_cambia_lato_a_ogni_cambio_campo():
    assert posizione_arbitro(True)[0] < 0 < LARGHEZZA_TAVOLO < posizione_arbitro(False)[0]
    risultato = Incontro(giocatore(1), giocatore(2), SINGOLARE_3, seme=21, dettaglio=COMPLETO).gioca()
    lati = []
    for evento in risultato.eventi:
        if evento.tipo in (E.ANNUNCIO, E.CAMBIO_CAMPO_INIZIO, E.CAMBIO_CAMPO_FINE):
            lati.append((evento.tipo, evento.pos[0] < 0))
    cambi = 0
    for (tipo_prima, lato_prima), (tipo, lato) in itertools.pairwise(lati):
        if tipo_prima == E.CAMBIO_CAMPO_INIZIO:
            assert tipo == E.CAMBIO_CAMPO_FINE and lato != lato_prima
            cambi += 1
        elif tipo == tipo_prima == E.ANNUNCIO:
            assert lato == lato_prima
    assert cambi == len(risultato.incontro.cambi_campo) >= 1
