"""Test del dado del motore di partita: fasce, residuo, seme e dado truccato."""

import math
import random
from collections import Counter

import pytest

from motore.dado import Dado, DadoTruccato
from motore.eventi import ErroreMotore

TIRI = 100_000


def test_frequenze_delle_fasce():
    dado = Dado(random.Random(1))
    probabilita = (0.2, 0.05, 0.25, 0.5)
    conti = Counter(dado.fascia(probabilita)[0] for _ in range(TIRI))
    for indice, p in enumerate(probabilita):
        assert conti[indice] / TIRI == pytest.approx(p, abs=0.006)


def test_il_residuo_resta_uniforme():
    dado = Dado(random.Random(2))
    residui = {0: [], 1: []}
    for _ in range(TIRI):
        indice, residuo = dado.fascia((0.3, 0.7))
        assert 0.0 <= residuo < 1.0
        residui[indice].append(residuo)
    for valori in residui.values():
        decimi = Counter(int(r * 10) for r in valori)
        for decimo in range(10):
            assert decimi[decimo] / len(valori) == pytest.approx(0.1, abs=0.01)


def test_l_ultima_fascia_prende_il_resto():
    # Le probabilità sommano un poco meno di uno: il tiro che cade oltre resta nell'ultima fascia.
    indice, residuo = DadoTruccato([0.99999999]).fascia((0.5, 0.49999))
    assert indice == 1 and 0.99 < residuo < 1.0


def test_stesso_seme_stessa_sequenza():
    primo, secondo = Dado(random.Random(77)), Dado(random.Random(77))
    assert [primo.fascia((0.1, 0.9)) for _ in range(500)] == [secondo.fascia((0.1, 0.9)) for _ in range(500)]
    assert [primo.pesata((("a", 1), ("b", 3))) for _ in range(200)] == [secondo.pesata((("a", 1), ("b", 3))) for _ in range(200)]


def test_pesata_intero_si_e_softmax():
    dado = Dado(random.Random(3))
    conti = Counter(dado.pesata((("raro", 1), ("frequente", 9))) for _ in range(20_000))
    assert conti["frequente"] / 20_000 == pytest.approx(0.9, abs=0.01)
    interi = Counter(dado.intero(1, 3) for _ in range(9_000))
    assert set(interi) == {1, 2, 3} and min(interi.values()) > 2_700
    scelte = Counter(dado.softmax([0.0, 1.0], 0.5) for _ in range(20_000))
    assert scelte[1] / 20_000 == pytest.approx(1 / (1 + math.exp(-2.0)), abs=0.01)
    assert sum(dado.si(0.25) for _ in range(20_000)) / 20_000 == pytest.approx(0.25, abs=0.01)


def test_il_dado_truccato_finisce_con_errore_motore():
    dado = DadoTruccato([0.1, 0.95])
    assert dado.tiro() == 0.1
    assert dado.fascia((0.5, 0.5)) == (1, pytest.approx(0.9))
    assert dado.rimasti == 0
    with pytest.raises(ErroreMotore):
        dado.tiro()
