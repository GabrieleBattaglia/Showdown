"""
Test della gara a squadre: composizione, rotazione fissa, tre servizi, set a 31 con 2 di scarto,
cambio campo a 16, un time-out e una sostituzione per squadra, chi esce non rientra.
"""

import itertools

import pytest
from aiuti_motore import giocatore

from motore.incontro import COMPLETO, ESSENZIALE, SQUADRE, Incontro, simula_incontro
from motore.regia import controlla_invarianti
from motore.squadre import Squadra, composizione_valida, ordine_di_battuta, problema_squadra


def _squadra(nome, primo_id, sessi="mmf", valori=None, **altro):
    valori = valori or [15.0] * len(sessi)
    return Squadra(nome, tuple(giocatore(primo_id + i, valore=v, sesso=s, **altro) for i, (s, v) in enumerate(zip(sessi, valori, strict=True))))


def test_composizione_della_squadra():
    assert problema_squadra(_squadra("Leoni", 1)) is None
    assert problema_squadra(_squadra("Leoni", 1, "ffmmff")) is None
    assert "da 3 a 6" in problema_squadra(_squadra("Leoni", 1, "mf"))
    assert "da 3 a 6" in problema_squadra(_squadra("Leoni", 1, "mmfmmff"))
    assert "due giocatori di un sesso" in problema_squadra(_squadra("Leoni", 1, "mmmf"))
    doppione = _squadra("Leoni", 1)
    assert "due volte" in problema_squadra(Squadra("Leoni", (*doppione.giocatori, doppione.giocatori[0])))
    fermo = _squadra("Leoni", 1)
    fermo.giocatori[1].infortunato = True
    fermo.giocatori[1].infortunio_sede = "caviglia"
    assert "non può giocare" in problema_squadra(fermo)
    with pytest.raises(ValueError, match="comune"):
        Incontro(_squadra("Leoni", 1), _squadra("Tigri", 3), SQUADRE)


def test_ordine_di_battuta():
    assert ordine_di_battuta("A") == (("A", 0), ("B", 0), ("A", 1), ("B", 1), ("A", 2), ("B", 2))
    assert ordine_di_battuta("B") == (("B", 0), ("A", 0), ("B", 1), ("A", 1), ("B", 2), ("A", 2))


def _turni(risultato):
    """Le coppie di chi batte e chi riceve, nell'ordine, con quanti servizi assegnati ciascuna."""
    turni = []
    for punto in risultato.punti:
        coppia = (punto.battitore, punto.ricevitore)
        if not turni or turni[-1][0] != coppia:
            turni.append([coppia, 0])
        if punto.punti:
            turni[-1][1] += 1
    return turni


def test_rotazione_e_tre_servizi():
    a, b = _squadra("Leoni", 1), _squadra("Tigri", 11, "ffm")
    visti_b = False
    for seme in range(6):
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        ordine = ordine_di_battuta(risultato.sorteggio["batte"])
        ids = {"A": [g.id for g in a.giocatori], "B": [g.id for g in b.giocatori]}
        sequenza = [ids[parte][posto] for parte, posto in ordine]
        attese = [(sequenza[i % 6], sequenza[(i + 1) % 6]) for i in range(40)]
        turni = _turni(risultato)
        assert [coppia for coppia, _n in turni] == attese[:len(turni)]
        assert all(n == 3 for _coppia, n in turni[:-1])
        assert max(p.numero_servizio for p in risultato.punti) == 3
        visti_b |= risultato.sorteggio["batte"] == "B"
        assert turni[0][0] == (sequenza[0], sequenza[1])
    assert visti_b


def test_un_set_a_31_e_il_cambio_campo_a_16():
    a, b = _squadra("Leoni", 1), _squadra("Tigri", 11, "ffm")
    for seme in range(10):
        risultato = simula_incontro(a, b, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        assert len(risultato.set) == 1
        x, y = risultato.set[0]
        assert max(x, y) >= 31 and abs(x - y) >= 2
        cambi = risultato.incontro.cambi_campo
        assert len(cambi) == 1 and cambi[0][0] == 1 and max(cambi[0][1]) >= 16
        prima = [p.punteggio for p in risultato.punti]
        indice = next(i for i, punteggio in enumerate(prima) if max(punteggio) >= 16)
        assert indice == 0 or max(prima[indice - 1]) < 16


def test_time_out_e_sostituzione_una_per_squadra():
    sostituzioni = timeout = 0
    for seme in range(40):
        a = _squadra("Leoni", 1, "mmfmmf", valori=[6.0, 6.0, 6.0, 35.0, 35.0, 35.0], anni=60)
        b = _squadra("Tigri", 11, "ffmffm", valori=[30.0, 30.0, 30.0, 10.0, 10.0, 10.0])
        incontro = Incontro(a, b, SQUADRE, seme=seme, dettaglio=COMPLETO if seme < 5 else ESSENZIALE)
        risultato = incontro.gioca()
        if risultato.eventi:
            assert controlla_invarianti(risultato.eventi) == []
        per_parte = {"A": 0, "B": 0}
        for _set_n, punto_n, parte, esce, entra in risultato.incontro.sostituzioni:
            per_parte[parte] += 1
            dopo = risultato.punti[punto_n:]
            assert all(esce not in (p.battitore, p.ricevitore) for p in dopo)
            assert any(entra in (p.battitore, p.ricevitore) for p in dopo) or not dopo
        assert max(per_parte.values()) <= 1
        assert max(sum(1 for _s, _p, parte in risultato.incontro.timeout if parte == quale) for quale in "AB") <= 1
        for parte, squadra in (("A", a), ("B", b)):
            al_tavolo = [next(g for g in squadra.giocatori if g.id == gid) for gid in incontro.formazione[parte]]
            assert composizione_valida(al_tavolo)
        sostituzioni += len(risultato.incontro.sostituzioni)
        timeout += len(risultato.incontro.timeout)
    assert sostituzioni > 0 and timeout > 0


def test_gli_eventi_delle_squadre():
    a, b = _squadra("Leoni", 1), _squadra("Tigri", 11, "ffm")
    risultato = simula_incontro(a, b, SQUADRE, seme=3, dettaglio=COMPLETO)
    tipi = [e.tipo for e in risultato.eventi]
    assert "CAMBIO_AL_TAVOLO" in tipi and "CAMBIO_BATTITORE" not in tipi
    cambi = [e for e in risultato.eventi if e.tipo == "CAMBIO_AL_TAVOLO"]
    for prima, dopo in itertools.pairwise(cambi):
        assert prima.dati["entra"] == dopo.dati["batte"] or prima.dati["batte"] == dopo.dati["esce"]
