"""
Test dei conti della taratura del valore, strumenti/taratura_valore.py, senza giocare partite: i
minimi quadrati con i pesi non negativi, la prima stima della scala che conserva mediana e monte
stipendi, le coppie speculari di colpi e battute che hanno un peso solo, e la ricerca della scala
vera per bisezione di strumenti/simulazione_lunga.py, con una simulazione finta.
"""

import math
import random
import statistics
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import simulazione_lunga as sl
import taratura_valore as tv

import costanti


def test_minimi_quadrati_ritrova_i_coefficienti_e_azzera_i_negativi():
    rng = random.Random(1)
    righe, y = [], []
    for _ in range(300):
        a, b, c = rng.uniform(0, 10), rng.uniform(0, 10), rng.uniform(0, 10)
        righe.append([a, b, c, 1.0])
        y.append(2.0 * a + 0.5 * b - 1.5 * c + 3.0 + rng.gauss(0, 0.01))
    coefficienti, escluse = tv.minimi_quadrati(righe, y, vincolate=frozenset((0, 1)))
    assert coefficienti[:2] == pytest.approx([2.0, 0.5], abs=0.01)
    assert coefficienti[2] == pytest.approx(-1.5, abs=0.01) and not escluse
    coefficienti, escluse = tv.minimi_quadrati(righe, y, vincolate=frozenset((0, 1, 2)))
    assert escluse == [2] and coefficienti[2] == 0.0 and coefficienti[0] > 0


def test_le_coppie_speculari_hanno_una_colonna_sola():
    coppie = [gruppo for gruppo in tv.GRUPPI if len(gruppo) == 2]
    assert ("lungolineasx", "lungolineadx") in coppie and ("battutasx", "battutadx") in coppie
    assert len(coppie) == 6
    nomi = [nome for gruppo in tv.GRUPPI for nome in gruppo]
    assert sorted(nomi) == sorted(costanti.CARATTERISTICHE_VALORE)


def test_la_scala_conserva_mediana_e_monte_stipendi(monkeypatch):
    rng = random.Random(2)
    vecchi = [rng.gauss(137.0, 15.0) + (33.0 if rng.random() < 0.3 else 0.0) for _ in range(2000)]
    somme = [v * 0.5 + rng.gauss(0, 3) for v in vecchi]
    giocatori = list(range(len(vecchi)))

    def indice_finto(g, pesi, _tratti, a, b):
        valore_grezzo = vecchi[g] if pesi is tv.PESI_TAPPA_8 else somme[g]
        return a + b * valore_grezzo

    monkeypatch.setattr(tv.valore, "indice", indice_finto)
    a, b = tv.scala(giocatori, {}, {})
    nuovi = [a + b * s for s in somme]
    assert statistics.median(nuovi) == pytest.approx(statistics.median(vecchi))
    assert statistics.fmean(tv.fattore_stipendio(v) for v in nuovi) == pytest.approx(statistics.fmean(tv.fattore_stipendio(v) for v in vecchi), rel=1e-6)
    assert tv.fattore_stipendio(costanti.VALORE_DI_RIFERIMENTO) == 1.0
    assert math.isfinite(a) and b > 0


def _misure_finte(mediana_somme, mediana_tappa_8, a, b):
    # Una simulazione finta: la cassa mediana scende con la dispersione del valore, cioè con B.
    cassa = 5000.0 * math.exp(-4.0 * (b - 1.1))
    return {"casse": (0.0, cassa, 0.0), "stipendi": (110.0, 210.0, 560.0), "monte_su_sponsor": 0.92, "tesserati": 90, "attivi": 100,
            "mediana_valore": a + b * mediana_somme, "mediana_somme": mediana_somme, "mediana_tappa_8": mediana_tappa_8}


def test_la_scala_si_cerca_per_bisezione_sulla_cassa(monkeypatch):
    # D26: la scala si tara sulla simulazione lunga. Con una cassa che scende con B, la bisezione
    # ritrova il B che la porta al bersaglio, e A tiene la mediana del valore della tappa 8.
    monkeypatch.setattr(sl, "con_scala", lambda _anni, semi, a, b, _processi: {s: _misure_finte(100.0, 138.0, a, b) for s in semi})
    monkeypatch.setattr(sl.costanti, "SCALA_VALORE_A", -50.0)
    monkeypatch.setattr(sl.costanti, "SCALA_VALORE_B", 1.0)
    a, b, righe = sl.cerca_scala(10, (1, 2, 3), 5000.0, 1, passi=20, stampa=None)
    assert b == pytest.approx(1.1, abs=1e-4)
    assert a + b * 100.0 == pytest.approx(138.0)
    assert righe[-1].startswith("La scala trovata, da copiare in costanti.py")
    assert sl.PESI_TAPPA_8 is tv.PESI_TAPPA_8
