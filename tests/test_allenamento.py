"""Test del costo dell'allenamento, del guadagno con i tetti e dell'autoallenamento."""

import datetime
import random

import pytest

from allenamento import calcola_costo_xp_per_punto, esegui_auto_allenamento, guadagno, limiti
from costanti import ATTRIBUTI_ALLENABILI, MAX_ALLENATO_FISICO, MAX_ALLENATO_SKILL, MAX_TOTALE_PRECISIONE_RESISTENZA, MAX_TOTALE_SKILL_GIOCO
from modelli import Giocatore


@pytest.mark.parametrize(("allenato", "atteso"), [(0, 25), (4.5, 62.5), (9, 100), (12, 150), (15, 200), (19, 500), (20, 500), (25, 500)])
def test_costo_delle_caratteristiche_di_gioco(allenato, atteso):
    assert calcola_costo_xp_per_punto(allenato, False, False) == pytest.approx(atteso)


def test_costo_delle_caratteristiche_fisiche():
    assert calcola_costo_xp_per_punto(0, True, False) == pytest.approx(50)
    # Il tetto della parte allenata fisica è 5: oltre, il costo resta quello di 5.
    assert calcola_costo_xp_per_punto(8, True, False) == calcola_costo_xp_per_punto(5, True, False)


def test_sconto_ipovedenti_solo_sulle_caratteristiche_di_gioco():
    assert calcola_costo_xp_per_punto(0, False, True) == pytest.approx(25 * 0.93)
    assert calcola_costo_xp_per_punto(0, True, True) == pytest.approx(50)


def test_limiti():
    assert limiti("forza_allenata") == (MAX_ALLENATO_FISICO, MAX_TOTALE_PRECISIONE_RESISTENZA)
    assert limiti("bomba_allenata") == (MAX_ALLENATO_SKILL, MAX_TOTALE_SKILL_GIOCO)


def test_guadagno_senza_tetti():
    nuovo, guad, limitato = guadagno(2.0, 5.0, 50, 25.0, 20.0, 40.0)
    assert (nuovo, guad, limitato) == (4.0, 2.0, False)


def test_guadagno_fermato_dal_tetto_dell_allenato():
    nuovo, guad, limitato = guadagno(19.0, 5.0, 1000, 100.0, 20.0, 40.0)
    assert (nuovo, guad, limitato) == (20.0, 1.0, True)


def test_guadagno_fermato_dal_tetto_del_totale():
    nuovo, guad, limitato = guadagno(1.0, 8.5, 1000, 50.0, 5.0, 10.0)
    assert nuovo == pytest.approx(1.5)
    assert guad == pytest.approx(0.5)
    assert limitato


def test_autoallenamento_spende_e_rispetta_i_tetti():
    random.seed(77)
    spesi = 0
    for i in range(200):
        g = Giocatore(i + 1, datetime.datetime(2026, 1, 1))
        g.puntiesperienza = 2000
        prima = {a: getattr(g, a) for a in ATTRIBUTI_ALLENABILI}
        esegui_auto_allenamento(g)
        assert 0 <= g.puntiesperienza <= 2000
        if g.puntiesperienza < 2000:
            spesi += 1
            cresciute = [a for a in ATTRIBUTI_ALLENABILI if getattr(g, a) > prima[a]]
            assert len(cresciute) == 1
        for a in ATTRIBUTI_ALLENABILI:
            lim_a, lim_t = limiti(a)
            assert getattr(g, a) <= lim_a
            assert getattr(g, a) + getattr(g, a.replace("_allenata", "_base")) <= lim_t + 1e-9
    assert spesi > 150


def test_autoallenamento_fermo_senza_esperienza_o_infortunato():
    random.seed(8)
    g = Giocatore(1, datetime.datetime(2026, 1, 1))
    prima = dict(vars(g))
    esegui_auto_allenamento(g)
    assert vars(g) == prima
    g.puntiesperienza = 500
    g.infortunato = True
    esegui_auto_allenamento(g)
    assert g.puntiesperienza == 500
