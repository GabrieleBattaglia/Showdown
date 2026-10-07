"""
Test della catena degli esiti, ramo per ramo, con un dado scritto: ogni voce del copione è un tiro
oppure una fascia con il suo residuo. Poi la prova di forza: ventimila punti veri senza mai
ErroreMotore, e il doppio tocco soltanto in battuta.
"""

import dataclasses
import random

import pytest
from aiuti_motore import DadoScritto, giocatore

from costanti import ATTRIBUTI_BASE_CON_ALLENABILI, CARATTERISTICHE_FISICHE_BASE
from motore.campo import InCampo
from motore.dado import Dado
from motore.eventi import CAUSE
from motore.scambio import gioca_punto
from motore.taratura import TARATURA

# Le voci ricorrenti del copione.
BATTUTA_SX = 0.0
REGOLARE = (1, 0.5)
LATERALE = 0.0
FERMATA = (4, 0.5)
CONTROLLO_RIUSCITO = (2, 0.5)
LUNGOLINEA_SX = 0.0
COLPO_RIUSCITO = (2, 0.5)
NON_LENTA = 0.5


def _coppia(taratura=TARATURA):
    battitore = InCampo(giocatore(1), "A", taratura)
    ricevitore = InCampo(giocatore(2), "B", taratura)
    battitore.prepara_punto(ricevitore)
    ricevitore.prepara_punto(battitore)
    return battitore, ricevitore


def _gioca(copione, taratura=TARATURA, **opzioni):
    battitore, ricevitore = _coppia(taratura)
    dado = DadoScritto(copione)
    passi = []
    esito = gioca_punto(battitore, ricevitore, dado, taratura, passi, **opzioni)
    assert dado.rimasti == 0, "Il copione non è stato letto tutto."
    return esito, battitore, ricevitore, passi


def _inizio_regolare():
    return [BATTUTA_SX, REGOLARE, LATERALE]


def test_goal_di_battuta_vale_due():
    esito, battitore, ricevitore, passi = _gioca([*_inizio_regolare(), (0, 0.5)])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.attacchi, esito.origine) == ("goal", "goal_battuta", 2, "A", 0, "battuta")
    assert battitore.stats.goal == battitore.stats.goal_battuta == 1 and ricevitore.stats.goal_subiti == 1
    assert passi[0].tipo == "battuta" and passi[0].zona == "sx"


def test_battuta_irregolare_vale_uno():
    esito, battitore, _ricevitore, _passi = _gioca([BATTUTA_SX, (0, 0.5), 0.0])
    assert (esito.esito, esito.causa, esito.critico, esito.punti, esito.a_chi) == ("fallo", "battuta_senza_rimbalzo", False, 1, "B")
    assert esito.chi_commette == battitore.id and battitore.stats.falli["battuta_senza_rimbalzo"] == 1


def test_il_critico_sceglie_una_causa_critica_e_vale_uno():
    esito, *_resto = _gioca([BATTUTA_SX, (0, 0.05), 0.4])
    assert (esito.causa, esito.critico, esito.punti) == ("battuta_doppio_tocco", True, 1)
    esito, *_resto = _gioca([*_inizio_regolare(), (1, 0.05), 0.0])
    assert (esito.causa, esito.critico, esito.punti, esito.a_chi) == ("paletta_caduta", True, 1, "A")
    esito, *_resto = _gioca([*_inizio_regolare(), FERMATA, CONTROLLO_RIUSCITO, LUNGOLINEA_SX, (0, 0.05), 0.5])
    assert (esito.causa, esito.critico, esito.punti, esito.a_chi) == ("out_volo", True, 1, "A")
    critiche = {codice for tabella in (TARATURA.CAUSE_BATTUTA_CRITICHE, TARATURA.CAUSE_DIFESA_CRITICHE, TARATURA.CAUSE_ATTACCO_CRITICHE) for codice, _peso in tabella}
    assert all(CAUSE[codice].punti == 1 for codice in critiche)


def test_falli_di_difesa():
    casi = ((0.0, "body_touch"), (0.97, "invasione_mano_libera"), (0.996, "invasione_tavola_contatto"))
    for tiro, causa in casi:
        esito, _battitore, ricevitore, _passi = _gioca([*_inizio_regolare(), (1, 0.5), tiro])
        assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.chi_commette) == ("fallo", causa, 1, "A", ricevitore.id)


def test_difesa_irregolare_che_entra_e_goal_da_due():
    esito, battitore, ricevitore, _passi = _gioca([*_inizio_regolare(), (1, 0.5), 0.75, 0.1])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.chi_commette) == ("goal", "goal_dopo_difesa_irregolare", 2, "A", ricevitore.id)
    assert battitore.stats.goal == 1 and ricevitore.stats.falli["goal_dopo_difesa_irregolare"] == 1
    esito, *_resto = _gioca([*_inizio_regolare(), (1, 0.5), 0.75, 0.9])
    assert (esito.esito, esito.causa, esito.punti) == ("fallo", "difesa_irregolare", 1)


def test_parata_fuori():
    esito, *_resto = _gioca([*_inizio_regolare(), (2, 0.5)])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi) == ("fallo", "out_in_difesa", 1, "A")


def test_ribattuta_lenta_e_ribattuta_in_porta():
    esito, *_resto = _gioca([*_inizio_regolare(), (3, 0.5), 0.001])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi) == ("palla_morta", "ribattuta_lenta", 0, None)
    esito, battitore, ricevitore, passi = _gioca([*_inizio_regolare(), (3, 0.5), NON_LENTA, 0.0, (0, 0.5)])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.origine, esito.attacchi) == ("goal", "goal_ribattuta", 2, "B", "ribattuta", 1)
    assert [p.tipo for p in passi] == ["battuta", "parata", "ribattuta", "parata", "goal"]
    assert passi[3].chi is battitore and passi[2].zona == "sx"
    assert ricevitore.stats.goal == 1


def _probabilita_della_parata(blocco, taratura):
    """Le fasce della parata di una battuta, contro un ricevitore con il blocco indicato su entrambi i lati."""
    battitore = InCampo(giocatore(1), "A", taratura)
    ricevitore = InCampo(giocatore(2, bloccosx_base=blocco, bloccodx_base=blocco), "B", taratura)
    battitore.prepara_punto(ricevitore)
    ricevitore.prepara_punto(battitore)
    passi = []
    gioca_punto(battitore, ricevitore, DadoScritto([*_inizio_regolare(), (0, 0.5)]), taratura, passi)
    return next(p.prob for p in passi if p.tipo == "parata")


def test_senza_il_suo_peso_il_blocco_sceglie_soltanto_fra_ribattuta_e_fermata():
    # Regressione della taratura: in un softmax unico il blocco migliore toglieva peso alla
    # ribattuta e lo spargeva anche su goal e falli, e allenarlo faceva perdere punti.
    taratura = dataclasses.replace(TARATURA, PESO_BLOCCO_PARATA=0.0)
    debole, forte = _probabilita_della_parata(4.0, taratura), _probabilita_della_parata(30.0, taratura)
    assert forte[:3] == pytest.approx(debole[:3])
    assert forte[3] < debole[3] and forte[4] > debole[4]
    assert forte[3] + forte[4] == pytest.approx(debole[3] + debole[4])


def test_col_suo_peso_il_blocco_ferma_anche_i_goal():
    debole, forte = _probabilita_della_parata(4.0, TARATURA), _probabilita_della_parata(30.0, TARATURA)
    assert TARATURA.PESO_BLOCCO_PARATA > 0
    assert forte[0] < debole[0] and forte[3] < debole[3]
    assert sum(forte) == pytest.approx(1.0) and sum(debole) == pytest.approx(1.0)


def test_controllo_trattenuto_e_paletta_caduta():
    esito, *_resto = _gioca([*_inizio_regolare(), FERMATA, (0, 0.5)])
    assert (esito.esito, esito.causa, esito.critico, esito.punti, esito.a_chi, esito.origine) == ("fallo", "pallina_trattenuta", False, 1, "A", "controllo")
    esito, *_resto = _gioca([*_inizio_regolare(), FERMATA, (0, 0.05)])
    assert (esito.causa, esito.critico, esito.punti) == ("paletta_caduta", True, 1)


def test_la_pallina_che_sfugge():
    esito, _battitore, ricevitore, _passi = _gioca([*_inizio_regolare(), FERMATA, (1, 0.5), 0.01])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.chi_commette) == ("goal", "autogoal", 2, "A", ricevitore.id)
    esito, *_resto = _gioca([*_inizio_regolare(), FERMATA, (1, 0.5), 0.05])
    assert (esito.esito, esito.causa, esito.punti) == ("palla_morta", "pallina_ferma", 0)
    esito, _battitore, _ricevitore, passi = _gioca([*_inizio_regolare(), FERMATA, (1, 0.5), 0.5, LUNGOLINEA_SX, (1, 0.5)])
    assert (esito.esito, esito.causa) == ("palla_morta", "colpo_debole")
    assert any(p.tipo == "sfuggita" and p.esito == "recupero" for p in passi)


@pytest.mark.parametrize(("tiri", "causa"), [((0.1, 0.5), "schermo_contro"), ((0.1, 0.05), "schermo_sopra"), ((0.9, 0.1), "out_tavola_contatto"), ((0.9, 0.5), "out_sponda")])
def test_falli_d_attacco(tiri, causa):
    esito, _battitore, ricevitore, _passi = _gioca([*_inizio_regolare(), FERMATA, CONTROLLO_RIUSCITO, LUNGOLINEA_SX, (0, 0.5), *tiri])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.chi_commette, esito.attacchi) == ("fallo", causa, 1, "A", ricevitore.id, 1)
    assert esito.colpo_decisivo == "lungolineasx"


def test_goal_da_scambio():
    esito, _battitore, ricevitore, passi = _gioca([*_inizio_regolare(), FERMATA, CONTROLLO_RIUSCITO, LUNGOLINEA_SX, COLPO_RIUSCITO, (0, 0.5)])
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi, esito.origine, esito.attacchi, esito.zona) == ("goal", "goal_scambio", 2, "B", "scambio", 1, "dx")
    assert ricevitore.stats.attacchi == 1 and ricevitore.stats.colpi["lungolineasx"] == 1 and ricevitore.stats.attacchi_verso["dx"] == 1
    assert [p.tipo for p in passi] == ["battuta", "parata", "controllo", "colpo", "parata", "goal"]


def test_limite_tecnico_in_palla_morta():
    taratura = dataclasses.replace(TARATURA, LIMITE_COLPI_PUNTO=3)
    ribattuta = [(3, 0.5), NON_LENTA, 0.0]
    esito, *_resto = _gioca([*_inizio_regolare(), *ribattuta, *ribattuta, (3, 0.5), NON_LENTA], taratura)
    assert (esito.esito, esito.causa, esito.punti, esito.attacchi) == ("palla_morta", "limite_tecnico", 0, 2)


def test_rottura_al_colpo_indicato_oppure_assente():
    esito, *_resto = _gioca([*_inizio_regolare(), FERMATA, CONTROLLO_RIUSCITO], rottura_al_colpo=1, causa_rottura="pallina_rotta")
    assert (esito.esito, esito.causa, esito.punti, esito.a_chi) == ("rottura", "pallina_rotta", 0, None)
    esito, *_resto = _gioca([*_inizio_regolare(), FERMATA, CONTROLLO_RIUSCITO, LUNGOLINEA_SX, (0, 0.5), 0.1, 0.5], rottura_al_colpo=2)
    assert esito.esito == "fallo"


def _giocatore_a_caso(gid, rng):
    g = giocatore(gid, anni=rng.uniform(12, 70), sesso=rng.choice("mf"), mancino=rng.random() < 0.1, ambidestro=rng.random() < 0.05,
                  giocorapido=rng.random() < 0.12, cambiovelocita=rng.random() < 0.15, temperamento=rng.uniform(0, 100), esperienza=rng.uniform(0, 20))
    if g.mancino:
        g.ambidestro = False
    for nome in ATTRIBUTI_BASE_CON_ALLENABILI:
        setattr(g, nome, rng.uniform(0, 10 if nome in CARATTERISTICHE_FISICHE_BASE else 40))
    g.aggiorna_icv()
    return g


def test_ventimila_punti_veri_senza_errori_e_doppio_tocco_solo_in_battuta():
    rng = random.Random(9)
    dado = Dado(random.Random(10))
    giocatori = [_giocatore_a_caso(i, rng) for i in range(1, 41)]
    esiti = set()
    for punto in range(20_000):
        if punto % 100 == 0:
            a, b = rng.sample(giocatori, 2)
            battitore, ricevitore = InCampo(a, "A", TARATURA), InCampo(b, "B", TARATURA)
        battitore.prepara_punto(ricevitore)
        ricevitore.prepara_punto(battitore)
        passi = []
        esito = gioca_punto(battitore, ricevitore, dado, TARATURA, passi, rottura_al_colpo=rng.choice((0, 0, 0, 1, 2)))
        esiti.add(esito.esito)
        assert esito.punti == {"goal": 2, "fallo": 1, "palla_morta": 0, "rottura": 0}[esito.esito]
        for indice, passo in enumerate(passi):
            if passo.causa == "battuta_doppio_tocco":
                assert indice <= 1 and passi[0].tipo == "battuta"
        battitore, ricevitore = ricevitore, battitore
    assert esiti == {"goal", "fallo", "palla_morta", "rottura"}
    for tabella in (TARATURA.CAUSE_DIFESA, TARATURA.CAUSE_DIFESA_CRITICHE, TARATURA.CAUSE_ATTACCO_CRITICHE):
        assert "battuta_doppio_tocco" not in dict(tabella)
