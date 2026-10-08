"""
Test del giocatore in campo: stanchezza di ciascuno, che cala con l'allenamento, mano e rovescio,
paura degli errori, scelta del colpo e lettura dell'avversario, la precisione che pesa la metà e
la sorpresa del mancino in difesa, decisione D26. Qui sta anche la regressione del problema P1: chi
batte gioca con la sua stanchezza, non con quella dell'avversario.
"""

import dataclasses
import itertools
import math
import random

from aiuti_motore import TARATURA_NEUTRA, giocatore

from costanti import COLPI_DELLO_SCAMBIO, COLPI_DI_BATTUTA
from motore.campo import InCampo, allenamento, efficienza, ritmo_della_fatica
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


# I pesi della precisione nel progetto della tappa 9, prima della decisione D26, e il loro posto
# nelle tuple dei pesi delle qualità.
PRECISIONE_DEL_PROGETTO = {"PESI_COLPO": (2, 0.20), "PESI_BOMBA": (2, 0.10), "PESI_BATTUTA": (1, 0.25), "PESI_CHIUSURA": (2, 0.20),
                           "PESI_BLOCCO": (2, 0.20), "PESI_CONTROLLO": (1, 0.25)}


def test_la_precisione_pesa_la_meta_in_tutte_le_qualita():
    # D26: cinque punti allenati di precisione portavano un giocatore dal 53 al 96 per cento di
    # vittorie; ora la precisione pesa la metà, e la metà tolta va alla caratteristica propria.
    for nome, (posto, peso) in PRECISIONE_DEL_PROGETTO.items():
        pesi = getattr(TARATURA, nome)
        assert math.isclose(pesi[posto], peso / 2), nome
        assert math.isclose(sum(pesi), 1.0), nome
    # In campo: due punti di precisione in più, cioè due decimi della scala, alzano ogni qualità
    # di cento volte il peso dimezzato per due decimi; il rovescio toglie il suo dieci per cento.
    normale = _campo(giocatore(1, fisico=3.0))
    preciso = _campo(giocatore(1, fisico=3.0, precisione_base=5.0))

    def aumento(nome):
        posto, _peso = PRECISIONE_DEL_PROGETTO[nome]
        return 100.0 * getattr(TARATURA, nome)[posto] * 0.2

    for indice, colpo in enumerate(COLPI_DELLO_SCAMBIO):
        atteso = aumento("PESI_BOMBA" if colpo == "bomba" else "PESI_COLPO")
        assert math.isclose(preciso.Q[indice] - normale.Q[indice], atteso)
    for indice in range(len(COLPI_DI_BATTUTA)):
        assert math.isclose(preciso.QB[indice] - normale.QB[indice], aumento("PESI_BATTUTA"))
    rovescio = 1.0 - TARATURA.MALUS_ROVESCIO
    for zona, fattore in (("sx", rovescio), ("centro", 1.0), ("dx", 1.0)):
        assert math.isclose(preciso.D[zona] - normale.D[zona], aumento("PESI_CHIUSURA") * fattore)
        assert math.isclose(preciso.B[zona] - normale.B[zona], aumento("PESI_BLOCCO") * fattore)
    assert math.isclose(preciso.C - normale.C, aumento("PESI_CONTROLLO"))
    assert math.isclose(aumento("PESI_COLPO"), 2.0) and math.isclose(aumento("PESI_CHIUSURA"), 2.0)


def test_chi_si_allena_si_stanca_meno():
    # D26: la stanchezza dipende dall'età, dalla resistenza e da quanto si allena, che per ora è
    # la parte allenata della resistenza. A parità di resistenza totale, chi l'ha allenata regge
    # di più; senza allenamento conta soltanto la resistenza totale.
    innato = giocatore(1, anni=25, fisico=3.0, resistenza_base=8.0)
    allenato = giocatore(2, anni=25, fisico=3.0, resistenza_base=4.0, resistenza_allenata=4.0)
    assert allenamento(innato) == 0.0 and math.isclose(allenamento(allenato), 0.8)
    assert ritmo_della_fatica(allenato, TARATURA) < ritmo_della_fatica(innato, TARATURA)
    trentenne = giocatore(3, anni=30, fisico=3.0, resistenza_base=5.0)
    assert math.isclose(ritmo_della_fatica(trentenne, TARATURA), 1.0)
    assert math.isclose(_campo(allenato).ritmo, ritmo_della_fatica(allenato, TARATURA))


def test_la_resistenza_della_scheda_resta_il_fattore_principale():
    # Revisione di D26: la parte allenata conta nella resistenza totale e, meno, come abitudine ad
    # allenarsi. Fra giocatori che nel mondo possono esistere, con l'innata fino a 3 e l'allenata
    # fino a 5, chi ha almeno un punto in più di resistenza totale si stanca sempre più piano,
    # comunque sia divisa: con K_ALLENAMENTO_FATICA a 1 una resistenza 5 tutta allenata reggeva
    # più di una resistenza 6 tutta innata.
    passi = [x / 2 for x in range(11)]
    possibili = [(innata, allenata) for innata in passi if innata <= 3.0 for allenata in passi]
    ritmi = {}
    for gid, (innata, allenata) in enumerate(possibili, start=1):
        g = giocatore(gid, anni=27, resistenza_base=innata, resistenza_allenata=allenata)
        ritmi[innata, allenata] = ritmo_della_fatica(g, TARATURA)
    for (i1, a1), (i2, a2) in itertools.permutations(possibili, 2):
        if i1 + a1 >= i2 + a2 + 1.0:
            assert ritmi[i1, a1] < ritmi[i2, a2], ((i1, a1), (i2, a2))


def test_cinque_set_lunghi_secondo_resistenza_eta_e_allenamento():
    # Un incontro al meglio dei 5 arrivato al quinto set chiede in media 385 azioni. Il giovane
    # con la resistenza più alta che si possa avere, 3 innata e 5 allenata, arriva in fondo quasi
    # fresco, l'anziano poco resistente perde molto, mai sotto il minimo.
    azioni = 385
    giovane = giocatore(1, anni=24, fisico=3.0, resistenza_base=3.0, resistenza_allenata=5.0)
    anziano = giocatore(2, anni=65, fisico=3.0, resistenza_base=1.5)
    eff_giovane = efficienza(azioni, ritmo_della_fatica(giovane, TARATURA), TARATURA)
    eff_anziano = efficienza(azioni, ritmo_della_fatica(anziano, TARATURA), TARATURA)
    assert eff_giovane >= 0.94
    assert 1.0 - TARATURA.FATICA_MAX <= eff_anziano <= 0.75


def test_la_sorpresa_del_mancino_cala_con_l_abitudine_di_chi_ha_esperienza():
    # D26: i colpi del mancino arrivano da un'angolazione meno abituale e premono di più; chi ha
    # esperienza ci si abitua con le parate, chi non ne ha resta sorpreso.
    s = TARATURA.SORPRESA_MANCINO
    assert s > 0
    mancino, destro = _campo(giocatore(2, mancino=True), "B"), _campo(giocatore(3), "B")
    inesperto, esperto = _campo(giocatore(1)), _campo(giocatore(4, esperienza=20.0))
    assert inesperto.sorpresa_contro(destro) == 1.0
    assert math.isclose(inesperto.sorpresa_contro(mancino), 1.0 + s)
    assert math.isclose(esperto.sorpresa_contro(mancino), 1.0 + s)
    inesperto.parate_mancino = esperto.parate_mancino = 200
    assert math.isclose(inesperto.sorpresa_contro(mancino), 1.0 + s)
    assert 1.0 + s * (1.0 - esperto.L) - 1e-9 <= esperto.sorpresa_contro(mancino) < 1.0 + s
    esperto.prepara_punto(mancino)
    assert esperto.sorpresa == esperto.sorpresa_contro(mancino)
    esperto.prepara_punto(destro)
    assert esperto.sorpresa == 1.0
