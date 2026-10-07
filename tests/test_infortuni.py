"""
Test degli infortuni con la sede, tappa 9: pesi delle sedi per mano, il fattore dell'ambidestro,
la durata non più divisa per cinque, puo_giocare per sede e tratto, la guarigione che toglie la
sede, e le frasi del diario.
"""

import datetime
import random

import pytest
from aiuti_motore import giocatore

import infortuni
from costanti import CARICO_INFORTUNIO_MASSIMO, CARICO_INFORTUNIO_MINIMO, FATTORE_INFORTUNIO_AMBIDESTRO
from mondo import Mondo

OGGI = datetime.datetime(2026, 3, 1, 9, 0)


def test_pesi_delle_sedi_per_mano():
    destro = dict(infortuni.pesi_sedi(giocatore(1)))
    mancino = dict(infortuni.pesi_sedi(giocatore(2, mancino=True)))
    ambidestro = dict(infortuni.pesi_sedi(giocatore(3, ambidestro=True)))
    assert (destro["spalla_dx"], destro["spalla_sx"]) == (12, 3)
    assert (mancino["spalla_dx"], mancino["spalla_sx"]) == (3, 12)
    assert ambidestro["spalla_dx"] == ambidestro["spalla_sx"] == 7.5
    assert destro["schiena"] == mancino["schiena"] == ambidestro["schiena"] == 22
    rng = random.Random(1)
    sedi = [infortuni.estrai_sede(giocatore(1), rng) for _ in range(5000)]
    assert sedi.count("spalla_dx") > 3 * sedi.count("spalla_sx")


def test_il_fattore_dell_ambidestro_e_il_carico():
    destro, ambidestro = giocatore(1, anni=50), giocatore(2, anni=50, ambidestro=True)
    assert infortuni.probabilita(ambidestro, 130) == pytest.approx(FATTORE_INFORTUNIO_AMBIDESTRO * infortuni.probabilita(destro, 130))
    assert infortuni.fattore_carico(0) == CARICO_INFORTUNIO_MINIMO
    assert infortuni.fattore_carico(100_000) == CARICO_INFORTUNIO_MASSIMO
    assert infortuni.probabilita(destro, 60) < infortuni.probabilita(destro, 200)


def test_la_durata_non_e_piu_divisa_per_cinque():
    destro, ambidestro = giocatore(1, anni=40), giocatore(2, anni=40, ambidestro=True)
    for seme in range(20):
        assert infortuni.durata(destro, "polso_dx", random.Random(seme)) == infortuni.durata(ambidestro, "polso_dx", random.Random(seme))
    ginocchio = [infortuni.durata(destro, "ginocchio", random.Random(s)) for s in range(50)]
    caviglia = [infortuni.durata(destro, "caviglia", random.Random(s)) for s in range(50)]
    assert sum(ginocchio) > sum(caviglia)


def test_chi_puo_giocare():
    g = giocatore(1)
    assert g.puo_giocare
    g.infortunato, g.infortunio_sede = True, "polso_dx"
    assert not g.puo_giocare
    g.ambidestro = True
    assert g.puo_giocare
    g.infortunio_sede = "ginocchio"
    assert not g.puo_giocare
    g.infortunio_sede = "non_precisata"
    assert not g.puo_giocare
    g.infortunato, g.ritirato = False, True
    assert not g.puo_giocare


def test_le_frasi_del_diario():
    fine = datetime.datetime(2026, 3, 3)
    assert infortuni.testo_diario(giocatore(1), "polso_dx", fine) == "Si infortuna al polso destro: resterà fermo fino al 3 marzo 2026."
    assert infortuni.testo_diario(giocatore(2, sesso="f"), "caviglia", fine) == "Si infortuna alla caviglia: resterà ferma fino al 3 marzo 2026."
    assert infortuni.testo_diario(giocatore(3, ambidestro=True), "polso_dx", fine) == "Si infortuna al polso destro: fino al 3 marzo 2026 giocherà con il braccio sinistro."
    assert infortuni.testo_diario(giocatore(4), "non_precisata", fine) == "Si infortuna: resterà fermo fino al 3 marzo 2026."


def test_l_infortunio_dopo_la_partita_e_la_guarigione(monkeypatch):
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    g = giocatore(1)
    mondo.giocatori[g.id] = g
    monkeypatch.setattr(infortuni, "probabilita", lambda _g, _azioni: 100.0)
    frase = infortuni.infortuna(mondo, g, 150, random.Random(3))
    assert g.infortunato and g.infortunio_sede in infortuni.SEDI_VALIDE and g.infortunio_fine_datetime > OGGI
    assert frase.startswith(f"{g.nome} {g.cognome}: si infortuna ")
    assert g.diario[0]["testo"].startswith("Si infortuna ")
    assert infortuni.infortuna(mondo, g, 150, random.Random(3)) is None
    rapporto = {"guariti": 0, "usciti": 0, "morti": 0, "ritirati": 0}
    g.etamorte = g.etaritiro = 10 ** 6
    monkeypatch.setattr("mondo.PROB_USCITA_PREMATURA_GIORNALIERA", 0)
    mondo._fai_invecchiare(g.infortunio_fine_datetime + datetime.timedelta(days=1), rapporto)
    assert not g.infortunato and g.infortunio_sede is None and rapporto["guariti"] == 1
