"""
Test dell'esperienza della tappa 11: il libero cresce soltanto con l'età, il fattore del gruppo, le
amichevoli che aggiungono, l'ordine delle fonti nella carriera perfetta e il tetto di 20.
"""

import types

import pytest

import esperienza
from costanti import (
    ANNO_SIMULAZIONE_GIORNI,
    ESPERIENZA_MASSIMA,
    ESPERIENZA_PER_AMICHEVOLE,
    ESPERIENZA_PER_ANNO_DI_VITA,
    ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA,
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
    g = _g()
    esperienza.da_partita(g)
    assert g.esperienza == pytest.approx(ESPERIENZA_PER_AMICHEVOLE)
    esperienza.da_partita(g, esperienza.TORNEO)
    esperienza.da_partita(g, esperienza.SFIDA)
    esperienza.da_piazzamento(g, 1)
    esperienza.da_piazzamento(g, 9)
    assert g.esperienza == pytest.approx(ESPERIENZA_PER_AMICHEVOLE + 0.01 + 0.006 + 0.3)


def test_l_ordine_delle_fonti_nella_carriera_perfetta():
    # Dai 9 ai 50 anni, sempre in polisportiva, un'amichevole nel 90 per cento dei giorni: l'età
    # dà meno delle amichevoli, che danno meno della polisportiva, e in tutto si arriva a 20.
    giorni = 41 * ANNO_SIMULAZIONE_GIORNI
    eta = ESPERIENZA_PER_ANNO_DI_VITA * 41
    amichevoli = ESPERIENZA_PER_AMICHEVOLE * giorni * 0.9
    polisportiva = ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * giorni * 1.05
    assert eta < amichevoli < polisportiva
    assert eta + amichevoli + polisportiva == pytest.approx(ESPERIENZA_MASSIMA, rel=0.1)


def test_il_tetto_di_venti():
    g = _g(19.999)
    esperienza.da_piazzamento(g, 1)
    esperienza.del_giorno(g, True, 1.2)
    assert g.esperienza == ESPERIENZA_MASSIMA
