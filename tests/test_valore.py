"""
Test del valore complessivo della tappa 9: con i pesi della tappa 8 è l'indice di prima, le due
parti sommano al totale, i pesi non sono negativi, un mancino specchiato vale quanto il
destrimano più il suo tratto, che sta fra 2 e 6 punti come vuole Gabriele, decisione D26, e con
i pesi misurati dalla taratura un mondo appena nato ha la mediana attorno a 140
e lo stesso monte stipendi di prima, perché l'economia della decisione D22 non cambi.
"""

import datetime
import math
import random

import pytest

import valore
from costanti import (
    ATTRIBUTI_ALLENABILI,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    CARATTERISTICHE_VALORE,
    PESI_TRATTI,
    PESI_VALORE,
    SCALA_STIPENDIO,
    SCALA_VALORE_B,
    VALORE_DI_RIFERIMENTO,
)
from modelli import Giocatore

# I pesi della tappa 8, con cui il valore nuovo deve ridare la formula di prima.
PESI_TAPPA_8 = dict.fromkeys(CARATTERISTICHE_VALORE, 1.0)
TRATTI_TAPPA_8 = {"mancino": 0.0, "ambidestro": 33.0, "giocorapido": 33.0, "cambiovelocita": 33.0}

NASCITA = datetime.datetime(2026, 1, 1)


@pytest.fixture
def giocatori():
    random.seed(140)
    gruppo = [Giocatore(i, NASCITA) for i in range(1, 81)]
    rng = random.Random(1)
    for g in gruppo[::2]:
        for nome in ATTRIBUTI_ALLENABILI:
            setattr(g, nome, rng.uniform(0, 4))
        g._rispetta_tetti()
        g.aggiorna_icv()
    return gruppo


def _formula_di_prima(g):
    somma = sum(getattr(g, nome) for nome in ATTRIBUTI_BASE_CON_ALLENABILI) + sum(getattr(g, nome) for nome in ATTRIBUTI_ALLENABILI)
    return somma + 33 * sum(bool(getattr(g, tratto)) for tratto in ("ambidestro", "giocorapido", "cambiovelocita"))


def test_con_i_pesi_della_tappa_8_l_indice_e_quello_di_prima(giocatori):
    for g in giocatori:
        assert valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) == pytest.approx(_formula_di_prima(g))
        assert g.indice_collettivo_valore == pytest.approx(valore.indice(g))


def test_le_due_parti_sommano_al_totale(giocatori):
    for g in giocatori:
        base, allenato = valore.parti(g)
        assert base + allenato == pytest.approx(valore.indice(g))
        assert (g.icv_base, g.icv_allenato) == (base, allenato)


def test_pesi_non_negativi_e_completi():
    assert set(PESI_VALORE) == set(CARATTERISTICHE_VALORE) and len(CARATTERISTICHE_VALORE) == 24
    assert all(peso >= 0 for peso in PESI_VALORE.values())
    assert all(peso >= 0 for peso in PESI_TRATTI.values())


def _specchia(g):
    """Il mancino specchiato: chiusure e blocchi scambiati di lato, e il tratto del mancino."""
    for coppia in (("chiusurasx", "chiusuradx"), ("bloccosx", "bloccodx")):
        for parte in ("_base", "_allenata"):
            sx, dx = coppia[0] + parte, coppia[1] + parte
            valore_sx, valore_dx = getattr(g, sx), getattr(g, dx)
            setattr(g, sx, valore_dx)
            setattr(g, dx, valore_sx)
    g.mancino = True
    g.ambidestro = False
    g.aggiorna_icv()
    return g


def test_un_mancino_specchiato_vale_quanto_il_destrimano(giocatori):
    for g in giocatori:
        if g.mancino or g.ambidestro:
            continue
        prima = valore.caratteristiche(g)
        indice = valore.indice(g)
        _specchia(g)
        assert valore.caratteristiche(g) == pytest.approx(prima)
        assert valore.indice(g) == pytest.approx(indice + SCALA_VALORE_B * PESI_TRATTI["mancino"])


def test_il_vantaggio_del_mancino_resta_nella_banda_di_gabriele():
    # D26: il vantaggio del mancino nel valore resta piccolo ma visibile, fra 2 e 6 punti. Il peso
    # è la media di quattro semi della taratura, perché con un seme solo andava da 2,9 a 5,6.
    assert 2.0 <= SCALA_VALORE_B * PESI_TRATTI["mancino"] <= 6.0


def test_l_ambidestro_fa_la_media_dei_lati(giocatori):
    g = giocatori[0]
    g.ambidestro, g.mancino = True, False
    c = valore.caratteristiche(g)
    assert c["chiusura_dritto"] == c["chiusura_rovescio"] == pytest.approx((g._get_valore_totale("chiusurasx_base") + g._get_valore_totale("chiusuradx_base")) / 2)
    with pytest.raises(ValueError, match="Parte sconosciuta"):
        valore.caratteristiche(g, "media")


def test_un_mondo_appena_nato_resta_sulla_scala_di_prima():
    # Dalla decisione D26 la scala la cerca la simulazione lunga, perché le casse delle
    # polisportive del computer tornino sui 5000 euro, con la mediana del valore del mondo maturo
    # a 135,5 e lo stipendio mediano vicino a 210 euro: su ottocento neonati la mediana è 134, e
    # la media del fattore dello stipendio sta entro un decimo di quella del valore di prima. La
    # tolleranza è di 7 punti sulla mediana e di un decimo sul fattore.
    stato = random.getstate()
    random.seed(2026)
    try:
        neonati = [Giocatore(i, NASCITA) for i in range(1, 801)]
    finally:
        random.setstate(stato)
    nuovi = sorted(g.indice_collettivo_valore for g in neonati)
    vecchi = [valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in neonati]
    assert 128 <= nuovi[len(nuovi) // 2] <= 142

    def fattore(indici):
        return sum(math.exp((i - VALORE_DI_RIFERIMENTO) / SCALA_STIPENDIO) for i in indici) / len(indici)

    assert fattore(nuovi) == pytest.approx(fattore(vecchi), rel=0.1)
