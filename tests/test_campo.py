"""
Test del giocatore in campo: stanchezza di ciascuno, mano e rovescio, paura degli errori, scelta del
colpo e lettura dell'avversario. Qui sta anche la regressione del problema P1: chi batte gioca con
la sua stanchezza, non con quella dell'avversario.
"""

import dataclasses
import itertools
import math
import random

from aiuti_motore import TARATURA_NEUTRA, giocatore

from costanti import COLPI_DELLO_SCAMBIO, COLPI_DI_BATTUTA
from motore.campo import InCampo
from motore.dado import Dado
from motore.scambio import gioca_punto
from motore.taratura import TARATURA


def _campo(g, parte="A", taratura=TARATURA):
    return InCampo(g, parte, taratura)


def _efficienza(c, azioni):
    c.azioni = azioni
    c.prepara_punto(_campo(giocatore(99), "B"))
    return c.eff


def test_stanchezza_piena_all_inizio_e_calante():
    c = _campo(giocatore(1))
    valori = [_efficienza(c, azioni) for azioni in (0, 50, 200, 600, 2000)]
    assert valori[0] == 1.0
    assert all(dopo < prima for prima, dopo in itertools.pairwise(valori))
    assert valori[-1] >= 1.0 - TARATURA.FATICA_MAX


def test_stanchezza_piu_rapida_per_gli_anziani_e_i_poco_resistenti():
    giovane = _efficienza(_campo(giocatore(1, anni=28, fisico=5.0)), 300)
    anziano = _efficienza(_campo(giocatore(2, anni=62, fisico=5.0)), 300)
    debole = _efficienza(_campo(giocatore(3, anni=28, fisico=1.0)), 300)
    assert anziano < giovane and debole < giovane


def test_chi_batte_gioca_con_la_sua_stanchezza():
    # Regressione del problema P1: il vecchio motore passava a chi batte la resistenza del primo
    # giocatore. Qui due giocatori uguali, uno fresco e uno stanco: la battuta di ciascuno ha la
    # pressione della sua qualità per la sua efficienza, e quella dello stanco è più bassa.
    fresco, stanco = _campo(giocatore(1), "A"), _campo(giocatore(2), "B")
    stanco.azioni = 3000
    dado = Dado(random.Random(4))
    pressioni = {"A": [], "B": []}
    for battitore, ricevitore in ((fresco, stanco), (stanco, fresco)):
        for _ in range(40):
            battitore.prepara_punto(ricevitore)
            ricevitore.prepara_punto(battitore)
            passi = []
            gioca_punto(battitore, ricevitore, dado, TARATURA, passi)
            battuta = passi[0]
            if battuta.esito == "regolare":
                indice = COLPI_DI_BATTUTA.index(battuta.colpo)
                assert math.isclose(battuta.valore, TARATURA.PRESSIONE_BATTUTA * battitore.QB[indice] * battitore.eff)
                pressioni[battitore.parte].append(battuta.valore)
    assert pressioni["A"] and pressioni["B"]
    assert max(pressioni["B"]) < min(pressioni["A"])


def test_rovescio_del_destrimano_e_del_mancino():
    destro = _campo(giocatore(1))
    mancino = _campo(giocatore(2, mancino=True))
    assert destro.rovescio == "sx" and mancino.rovescio == "dx"
    assert destro.D["sx"] < destro.D["dx"] and mancino.D["dx"] < mancino.D["sx"]
    assert destro.D["sx"] == mancino.D["dx"]
    assert destro.dritto("dx") is True and destro.dritto("sx") is False and destro.dritto("centro") is None


def test_ambidestro_senza_rovescio_che_cambia_mano():
    c = _campo(giocatore(1, ambidestro=True))
    assert c.rovescio is None and c.cambia_mano and c.mano == "destra"
    d_sx, _b, cambio = c.difesa("sx")
    assert cambio and c.mano == "sinistra"
    assert d_sx == c.D["sx"] * (1 - TARATURA.COSTO_CAMBIO_MANO)
    assert c.difesa("sx")[2] is False
    assert c.difesa("centro")[2] is False
    assert c.difesa("dx")[2] is True and c.mano == "destra"


def test_ambidestro_col_braccio_destro_infortunato_gioca_di_sinistro():
    c = _campo(giocatore(1, ambidestro=True, infortunato=True, infortunio_sede="polso_dx"))
    assert c.mano == "sinistra" and not c.cambia_mano and c.rovescio == "dx"
    assert c.difesa("dx")[2] is False


def test_la_paura_degli_errori_cresce_col_temperamento_e_cala_con_l_esperienza():
    avversario = _campo(giocatore(99), "B")
    paure = []
    for temperamento, esperienza in ((20.0, 0.0), (80.0, 0.0), (80.0, 15.0)):
        c = _campo(giocatore(1, temperamento=temperamento, esperienza=esperienza))
        c.prepara_punto(avversario)
        paure.append(c.mf)
    assert paure[0] < paure[1]
    assert paure[2] < paure[1]


def test_lucido_e_esperto_sceglie_il_colpo_migliore():
    taratura = dataclasses.replace(TARATURA_NEUTRA, T0=1e-4, K_LETTURA=1e-6)
    forte = {f"{nome}_base": 4.0 for nome in COLPI_DELLO_SCAMBIO}
    forte["diagonaledx_base"] = 38.0
    c = InCampo(giocatore(1, esperienza=20.0, **forte), "A", taratura)
    c.osservati = 10_000
    c.prepara_punto(InCampo(giocatore(2), "B", taratura))
    migliore = COLPI_DELLO_SCAMBIO.index("diagonaledx")
    assert c.prob_colpi[migliore] > 0.99


def _entropia(probabilita):
    return -sum(p * math.log(p) for p in probabilita if p > 0)


def test_lo_stanco_sceglie_con_piu_entropia():
    avversario = _campo(giocatore(2), "B")
    variati = {f"{nome}_base": 6.0 + 2.5 * i for i, nome in enumerate(COLPI_DELLO_SCAMBIO)}
    riposato = _campo(giocatore(1, esperienza=10.0, **variati))
    stanco = _campo(giocatore(1, esperienza=10.0, **variati))
    stanco.azioni = 3000
    riposato.prepara_punto(avversario)
    stanco.prepara_punto(avversario)
    assert stanco.temperatura > riposato.temperatura
    assert _entropia(stanco.prob_colpi) > _entropia(riposato.prob_colpi)


def _verso(c, zona):
    return sum(p for nome, p in zip(COLPI_DELLO_SCAMBIO, c.prob_colpi, strict=True) if TARATURA.COLPI[nome].zona == zona)


def test_contro_un_mancino_l_inesperto_tira_sul_suo_dritto():
    mancino = _campo(giocatore(2, mancino=True), "B")
    inesperto = _campo(giocatore(1, esperienza=0.0))
    esperto = _campo(giocatore(3, esperienza=20.0))
    esperto.osservati = 500
    inesperto.prepara_punto(mancino)
    esperto.prepara_punto(mancino)
    # Il dritto del mancino è a sinistra: l'abitudine ci tira lo stesso, la lettura no.
    assert _verso(inesperto, "sx") > _verso(inesperto, "dx")
    assert _verso(esperto, "dx") > _verso(esperto, "sx")
