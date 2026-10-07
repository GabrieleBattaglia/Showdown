"""
Test delle regole dell'arbitro, decisione D25: punteggio e fine del set senza tetto, servizi, palle
morte e rotture che ripetono il servizio, ammonizioni e penalità, cambi campo, time-out, sorteggio
e formato. I punti li decide un copione al posto della catena degli esiti; sorteggio e imprevisti
li decide un DadoTruccato. Le lettere del copione: A e B un goal di quella parte, a e b un fallo
dell'altra che dà un punto a quella parte, M una palla morta, X una rottura.
"""

import itertools
import random
from collections import Counter

import pytest
from aiuti_motore import giocatore

import motore.incontro
from motore.dado import DadoTruccato
from motore.incontro import ESSENZIALE, SINGOLARE_3, SINGOLARE_5, Incontro, formato_singolare
from motore.scambio import EsitoPunto

NIENTE = 0.9999
A_BATTE = [0.1, 0.1]


class Copione:
    """Al posto di gioca_punto: restituisce gli esiti scritti, e ricorda chi batte e chi riceve a ogni punto."""

    def __init__(self, lettere):
        self.lettere = list(lettere)
        self.chiamate = []

    def __call__(self, battitore, ricevitore, dado, taratura, passi=None, rottura_al_colpo=0, causa_rottura="paletta_rotta"):
        lettera = self.lettere.pop(0)
        self.chiamate.append((battitore.parte, battitore.id))
        per_parte = {battitore.parte: battitore, ricevitore.parte: ricevitore}
        if lettera in "AB":
            return EsitoPunto("goal", "goal_scambio", False, None, lettera, 2, 2, "scambio", "bomba", "centro")
        if lettera in "ab":
            parte = lettera.upper()
            altra = "B" if parte == "A" else "A"
            return EsitoPunto("fallo", "schermo_contro", False, per_parte[altra].id, parte, 1, 1, "scambio", "bomba", "centro")
        if lettera == "M":
            return EsitoPunto("palla_morta", "colpo_debole", False, battitore.id, None, 0, 1, "scambio", "bomba", "centro")
        return EsitoPunto("rottura", "paletta_rotta", False, battitore.id, None, 0, 1, "scambio", None, "centro")


def _incontro(monkeypatch, lettere, tiri, formato=SINGOLARE_3, **opzioni):
    copione = Copione(lettere)
    monkeypatch.setattr(motore.incontro, "gioca_punto", copione)
    opzioni.setdefault("timeout", False)
    incontro = Incontro(giocatore(1), giocatore(2), formato, seme=1, dettaglio=ESSENZIALE, dado=DadoTruccato(tiri), **opzioni)
    return incontro, copione


def _tiri_semplici(punti, sorteggio=A_BATTE):
    return [*sorteggio, *([NIENTE] * punti)]


def _banda(banda):
    """Il tiro che cade a metà della fascia indicata degli imprevisti, per due giocatori neutri."""
    prova = Incontro(giocatore(1), giocatore(2), SINGOLARE_3, seme=1, dettaglio=ESSENZIALE)
    fasce = prova._fasce_imprevisti(prova.campo[1], prova.campo[2])
    return sum(fasce[:banda]) + fasce[banda] / 2


def test_set_senza_tetto_17_a_15(monkeypatch):
    lettere = "AB" * 5 + "ab" * 5 + "A" + "A" * 6
    incontro, _copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)))
    risultato = incontro.gioca()
    assert risultato.set == [(17, 15), (12, 0)]
    assert risultato.vincitore == "A"


def test_set_12_a_9_con_un_goal_sul_10_a_9(monkeypatch):
    lettere = "AB" * 4 + "aba" + "A" + "B" * 6 + "A" * 6
    incontro, _copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)))
    risultato = incontro.gioca()
    assert risultato.set == [(12, 9), (0, 12), (12, 0)]


def test_due_servizi_a_testa_e_apertura_alternata(monkeypatch):
    lettere = "A" * 6 + "B" * 6 + "A" * 6
    incontro, copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)))
    risultato = incontro.gioca()
    battitori = [parte for parte, _gid in copione.chiamate]
    assert battitori[:6] == ["A", "A", "B", "B", "A", "A"]
    assert battitori[6:8] == ["B", "B"] and battitori[12:14] == ["A", "A"]
    assert [p.numero_servizio for p in risultato.punti[:4]] == [1, 2, 1, 2]


def test_palla_morta_e_rottura_ripetono_lo_stesso_servizio(monkeypatch):
    lettere = "AMXa" + "A" * 4 + "A" * 6
    incontro, copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)))
    risultato = incontro.gioca()
    assert [p.numero_servizio for p in risultato.punti[:5]] == [1, 2, 2, 2, 1]
    assert [parte for parte, _gid in copione.chiamate[:5]] == ["A", "A", "A", "A", "B"]
    assert [p.punteggio for p in risultato.punti[:4]] == [(2, 0), (2, 0), (2, 0), (3, 0)]


def test_seconda_infrazione_in_penalita_anche_diversa_e_in_un_altro_set(monkeypatch):
    sanzione_a = _banda(0)
    lettere = "A" * 12
    tiri = [*A_BATTE, sanzione_a, 0.0, *([NIENTE] * 5), sanzione_a, 0.3, *([NIENTE] * 5)]
    incontro, copione = _incontro(monkeypatch, lettere, tiri)
    risultato = incontro.gioca()
    assert risultato.incontro.sanzioni == [(1, 0, 1, "ammonizione", "raschiare_paletta"), (2, 0, 1, "penalita", "muovere_tavolo")]
    # Il secondo set parte sul 2 a 0 per B, e l'ordine di battuta non cambia: apre B.
    assert risultato.set[1] == (12, 2) and copione.chiamate[6] == ("B", 2)
    assert risultato.statistiche[1].ammonizioni == 1 and risultato.statistiche[1].penalita == 1


def test_mascherina_e_telefono_sono_penalita_subito(monkeypatch):
    lettere = "A" * 11
    tiri = [*A_BATTE, _banda(2), *([NIENTE] * 3), _banda(5), *([NIENTE] * 6)]
    incontro, _copione = _incontro(monkeypatch, lettere, tiri)
    risultato = incontro.gioca()
    assert [s[2:] for s in risultato.incontro.sanzioni] == [(1, "penalita", "mascherina_toccata"), (2, "penalita", "telefono")]
    assert risultato.punti[0].punteggio == (2, 2)
    assert risultato.set == [(12, 2), (12, 0)]


def test_una_penalita_chiude_il_set(monkeypatch):
    lettere = "AB" * 4 + "abb" + "A" * 12
    tiri = [*A_BATTE, *([NIENTE] * 11), _banda(2), *([NIENTE] * 12)]
    incontro, _copione = _incontro(monkeypatch, lettere, tiri)
    risultato = incontro.gioca()
    assert risultato.set[0] == (9, 12)
    assert risultato.incontro.sanzioni[0][3] == "penalita"


def test_cambi_campo(monkeypatch):
    lettere = "A" * 6 + "B" * 6 + "A" * 6
    incontro, _copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)))
    risultato = incontro.gioca()
    assert risultato.incontro.cambi_campo == [(1, "fine set"), (2, "fine set"), (3, (6, 0))]
    lettere = "A" * 12
    incontro, _copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)))
    assert incontro.gioca().incontro.cambi_campo == [(1, "fine set")]
    lettere = "A" * 18
    incontro, _copione = _incontro(monkeypatch, lettere, _tiri_semplici(len(lettere)), formato=SINGOLARE_5)
    assert incontro.gioca().incontro.cambi_campo == [(1, "fine set"), (2, "fine set")]


def test_al_massimo_un_time_out_per_set():
    contati = 0
    for seme in range(40):
        risultato = Incontro(giocatore(1, valore=20.0), giocatore(2, valore=8.0), SINGOLARE_5, seme=seme, dettaglio=ESSENZIALE).gioca()
        per_set = Counter((set_n, parte) for set_n, _punto, parte in risultato.incontro.timeout)
        assert all(n == 1 for n in per_set.values())
        contati += len(per_set)
    assert contati > 0


@pytest.mark.parametrize(("tiri", "batte"), [((0.1, 0.1), "A"), ((0.1, 0.9), "B"), ((0.6, 0.1), "B"), ((0.6, 0.9), "A")])
def test_il_sorteggio_decide_chi_apre(monkeypatch, tiri, batte):
    lettere = "A" * 12
    incontro, copione = _incontro(monkeypatch, lettere, [*tiri, *([NIENTE] * 12)])
    incontro.gioca()
    assert incontro.info_sorteggio["batte"] == batte == copione.chiamate[0][0]
    assert incontro.info_sorteggio["vince"] == ("A" if tiri[0] < 0.5 else "B")


def test_sorteggio_coerente_negli_incontri_veri():
    rng = random.Random(3)
    for seme in range(30):
        risultato = Incontro(giocatore(1, valore=rng.uniform(5, 30)), giocatore(2), SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE).gioca()
        assert risultato.punti[0].parte_battitore == risultato.sorteggio["batte"]
        aperture = [p.parte_battitore for p in risultato.punti if p.punto_n == 1]
        assert all(prima != dopo for prima, dopo in itertools.pairwise(aperture))


def test_formato_solo_3_o_5():
    assert formato_singolare(3) is SINGOLARE_3 and formato_singolare(5) is SINGOLARE_5
    for n in (1, 2, 4, 7):
        with pytest.raises(ValueError, match=r"Il numero di set deve essere 3 o 5\."):
            formato_singolare(n)
