"""
Test dell'esperienza della tappa 11: il libero cresce soltanto con l'età, il fattore del gruppo, le
amichevoli che aggiungono, l'ordine delle fonti nella carriera perfetta e il tetto di 20.
"""

import itertools
import types

import pytest

import esperienza
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    ESPERIENZA_MASSIMA,
    ESPERIENZA_PER_AMICHEVOLE,
    ESPERIENZA_PER_ANNO_DI_VITA,
    ESPERIENZA_PER_FASE_SUPERATA,
    ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA,
    ESPERIENZA_PER_PARTITA_TORNEO,
    ESPERIENZA_PER_SFIDA,
    ESPERIENZA_PIAZZAMENTO_BASE,
    ESPERIENZA_RISERVA_QUOTA,
    SCALA_PIAZZAMENTI,
)


def _g(esp=0.0):
    return types.SimpleNamespace(esperienza=esp)


def test_il_libero_cresce_soltanto_con_l_eta():
    g = _g()
    for _ in range(ANNO_SIMULAZIONE_GIORNI):
        esperienza.del_giorno(g, in_polisportiva=False, fattore=3.0)
    assert g.esperienza == pytest.approx(ESPERIENZA_PER_ANNO_DI_VITA)


def test_in_polisportiva_si_cresce_di_piu_col_fattore_del_gruppo():
    g = _g()
    esperienza.del_giorno(g, in_polisportiva=True, fattore=1.05)
    assert g.esperienza == pytest.approx(ESPERIENZA_PER_ANNO_DI_VITA / ANNO_SIMULAZIONE_GIORNI + 1.05 * ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA)


def test_il_fattore_del_gruppo():
    assert esperienza.fattore_gruppo([]) == 1.0
    assert esperienza.fattore_gruppo([_g(5.0), _g(5.0)]) == pytest.approx(1.05)
    assert esperienza.fattore_gruppo([_g(20.0)]) == pytest.approx(1.2)


def test_le_partite_e_i_piazzamenti_aggiungono():
    # Dalla tappa 12 ogni fonte per l'importanza, calcolata dalle costanti e mai scritta a mano.
    g = _g()
    esperienza.da_partita(g)
    assert g.esperienza == pytest.approx(ESPERIENZA_PER_AMICHEVOLE)
    esperienza.da_partita(g, esperienza.TORNEO, 4.0)
    esperienza.da_partita(g, esperienza.SFIDA)
    esperienza.da_piazzamento(g, 1, 1.5)
    esperienza.da_piazzamento(g, 13)
    esperienza.da_fasi(g, 3, 2.0)
    esperienza.da_riserva(g)
    atteso = (ESPERIENZA_PER_AMICHEVOLE + 4.0 * ESPERIENZA_PER_PARTITA_TORNEO + ESPERIENZA_PER_SFIDA + 1.5 * ESPERIENZA_PIAZZAMENTO_BASE
              + 2.0 * 3 * ESPERIENZA_PER_FASE_SUPERATA + ESPERIENZA_RISERVA_QUOTA * ESPERIENZA_PER_SFIDA)
    assert g.esperienza == pytest.approx(atteso)


def test_i_piazzamenti_a_scalare_per_i_primi_dodici():
    premi = [esperienza.premio_piazzamento(posto) for posto in range(1, 15)]
    assert premi[:12] == pytest.approx([ESPERIENZA_PIAZZAMENTO_BASE * s for s in SCALA_PIAZZAMENTI])
    assert all(a > b for a, b in itertools.pairwise(premi[:12])) and premi[12:] == [0.0, 0.0]
    assert esperienza.premio_piazzamento(0) == 0.0


def test_l_ordine_delle_fonti_nella_carriera_perfetta():
    # Dalla tappa 12, D32: con i conteggi della carriera perfetta della taratura, 3.614 amichevoli,
    # 265 sfide e 460 incontri di torneo, le fonti vanno dalla più piccola alla più grande: sfide, età,
    # amichevoli, club e tornei, per i numeri del progetto 1,5, 2,05, 2,5, 5 e 9, e la somma è circa 20.
    giorni = 41 * ANNO_SIMULAZIONE_GIORNI
    eta = ESPERIENZA_PER_ANNO_DI_VITA * 41
    amichevoli = ESPERIENZA_PER_AMICHEVOLE * 3614
    sfide = ESPERIENZA_PER_SFIDA * 265
    club = ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * giorni * 1.05
    assert sfide < eta < amichevoli < club
    tornei = ESPERIENZA_MASSIMA - (eta + amichevoli + sfide + club)
    assert club < tornei < 11.0


def test_il_tetto_di_venti():
    g = _g(19.999)
    esperienza.da_piazzamento(g, 1)
    esperienza.del_giorno(g, True, 1.2)
    assert g.esperienza == ESPERIENZA_MASSIMA
