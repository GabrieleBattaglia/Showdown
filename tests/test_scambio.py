"""
Test della catena degli esiti, ramo per ramo, con un dado scritto: ogni voce del copione è un tiro
oppure una fascia con il suo residuo. Poi la prova di forza: ventimila punti veri senza mai
ErroreMotore, e il doppio tocco soltanto in battuta. Dalla tappa 11 l'abitudine al colpo ripetuto:
chi varia i colpi non ne risente, chi ne ripete uno oltre la quota sì, di più contro un difensore
esperto, mai prima di un certo numero di attacchi, e mai sulla battuta né sulla ribattuta; i due
lati dello stesso colpo contano insieme, e fra giocatori normali l'abitudine resta piccola.
"""

import dataclasses
import random
import statistics

import pytest
from aiuti_motore import NASCITA, DadoScritto, giocatore

from costanti import ATTRIBUTI_BASE_CON_ALLENABILI, CARATTERISTICHE_FISICHE_BASE
from modelli import Giocatore
from motore import ESSENZIALE, SINGOLARE_3, simula_incontro
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
    # Il fallo fatto da chi difende è anche un fallo subito da chi segna: i due conti tornano.
    assert battitore.stats.falli_subiti == sum(ricevitore.stats.falli.values()) == 1
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


def _parate_contro(mancino, copione):
    """Le parate di un punto in cui batte un giocatore, mancino o no, contro lo stesso ricevitore destrimano."""
    battitore = InCampo(giocatore(1, mancino=mancino), "A", TARATURA)
    ricevitore = InCampo(giocatore(2), "B", TARATURA)
    battitore.prepara_punto(ricevitore)
    ricevitore.prepara_punto(battitore)
    passi = []
    gioca_punto(battitore, ricevitore, DadoScritto(copione), TARATURA, passi)
    return [p for p in passi if p.tipo == "parata"], battitore, ricevitore


def test_la_battuta_del_mancino_sorprende_chi_para():
    # D26: la stessa battuta, dello stesso giocatore, arriva da un'angolazione meno abituale se
    # chi batte è mancino, e il goal diventa più probabile; il ricevitore conta la parata.
    copione = [*_inizio_regolare(), (0, 0.5)]
    (destro,), _b, ricevitore_destro = _parate_contro(False, copione)
    (mancino,), _b, ricevitore_mancino = _parate_contro(True, copione)
    assert mancino.prob[0] > destro.prob[0] * 1.03
    assert sum(mancino.prob) == pytest.approx(1.0)
    assert ricevitore_mancino.parate_mancino == 1 and ricevitore_destro.parate_mancino == 0
    assert ricevitore_mancino.sorpresa == pytest.approx(1.0 + TARATURA.SORPRESA_MANCINO)


def test_la_ribattuta_del_mancino_non_sorprende():
    # Il ricevitore mancino ribatte piano: la pallina che torna non ha angolazione da sorprendere.
    copione = [*_inizio_regolare(), (3, 0.5), NON_LENTA, 0.0, (0, 0.5)]
    battitore = InCampo(giocatore(1), "A", TARATURA)
    ricevitore = InCampo(giocatore(2, mancino=True), "B", TARATURA)
    battitore.prepara_punto(ricevitore)
    ricevitore.prepara_punto(battitore)
    passi = []
    esito = gioca_punto(battitore, ricevitore, DadoScritto(copione), TARATURA, passi)
    assert esito.origine == "ribattuta" and battitore.sorpresa > 1.0
    assert battitore.parate_mancino == 0 and ricevitore.parate_mancino == 0


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


def _abituati(attaccante, colpi):
    """Scrive nelle statistiche dell'attaccante gli attacchi dell'incontro fin qui, come dizionario di colpo e quante volte."""
    attaccante.stats.colpi.clear()
    attaccante.stats.colpi.update(colpi)
    attaccante.stats.attacchi = sum(colpi.values())


def test_l_abitudine_al_colpo_ripetuto():
    # Tappa 11, punto 12.2: il difensore si abitua al colpo che l'avversario usa troppo, di più se ha esperienza.
    t = TARATURA
    attaccante = InCampo(giocatore(1), "A", t)
    inesperto = InCampo(giocatore(2), "B", t)
    esperto = InCampo(giocatore(3, esperienza=20.0), "B", t)
    assert t.ABITUDINE_COLPO > 0 and t.QUOTA_ABITUDINE < 1
    vario = {"lungolineasx": 3, "diagonalesx": 3, "singolaspondasx": 3, "doppiaspondadx": 3, "bomba": 3, "triplaspondadx": 3, "lungolineadx": 3}
    _abituati(attaccante, vario)
    assert max(vario.values()) / sum(vario.values()) <= t.QUOTA_ABITUDINE
    assert inesperto.abitudine_al_colpo(attaccante, "lungolineasx") == 0.0
    _abituati(attaccante, {"triplaspondasx": t.ATTACCHI_PER_ABITUDINE - 1})
    assert inesperto.abitudine_al_colpo(attaccante, "triplaspondasx") == 0.0
    _abituati(attaccante, {"triplaspondasx": 30})
    da_inesperto, da_esperto = inesperto.abitudine_al_colpo(attaccante, "triplaspondasx"), esperto.abitudine_al_colpo(attaccante, "triplaspondasx")
    assert da_inesperto == pytest.approx(t.ABITUDINE_COLPO * t.ABITUDINE_SENZA_LETTURA)
    assert da_esperto > da_inesperto and da_esperto < t.ABITUDINE_COLPO
    assert inesperto.abitudine_al_colpo(attaccante, "bomba") == 0.0
    _abituati(attaccante, {"triplaspondasx": 20, "bomba": 10})
    assert 0.0 < inesperto.abitudine_al_colpo(attaccante, "triplaspondasx") < da_inesperto


def test_i_due_lati_dello_stesso_colpo_contano_insieme():
    # La revisione della tappa 11: la tripla sponda allenata dai due lati sfuggiva all'abitudine contata colpo per colpo.
    t = TARATURA
    attaccante = InCampo(giocatore(1), "A", t)
    difensore = InCampo(giocatore(2), "B", t)
    _abituati(attaccante, {"triplaspondasx": 30})
    da_un_lato = difensore.abitudine_al_colpo(attaccante, "triplaspondasx")
    _abituati(attaccante, {"triplaspondasx": 15, "triplaspondadx": 15})
    assert difensore.abitudine_al_colpo(attaccante, "triplaspondasx") == difensore.abitudine_al_colpo(attaccante, "triplaspondadx") == pytest.approx(da_un_lato)
    assert difensore.abitudine_al_colpo(attaccante, "doppiaspondasx") == 0.0
    # La bomba è un tipo da sola.
    _abituati(attaccante, {"bomba": 15, "lungolineasx": 15})
    assert difensore.abitudine_al_colpo(attaccante, "bomba") == difensore.abitudine_al_colpo(attaccante, "lungolineasx") > 0.0


def test_fra_giocatori_normali_l_abitudine_resta_piccola(monkeypatch):
    """
    Fra nati veri, che nessuno ha allenato, l'abitudine si accende in poche parate e toglie poco:
    nei primi attacchi dell'incontro il colpo preferito supera la quota per caso. La revisione della
    tappa 11 l'aveva trovata accesa in un terzo delle parate, col 4 per cento della pressione in meno.
    """
    stato = random.getstate()
    random.seed(77)
    try:
        nati = [Giocatore(i, NASCITA) for i in range(1, 61)]
    finally:
        random.setstate(stato)
    abitudini = []
    originale = InCampo.abitudine_al_colpo

    def spia(self, attaccante, colpo):
        abitudini.append(originale(self, attaccante, colpo))
        return abitudini[-1]

    monkeypatch.setattr(InCampo, "abitudine_al_colpo", spia)
    rng = random.Random(78)
    for _ in range(60):
        a, b = rng.sample(nati, 2)
        simula_incontro(a, b, SINGOLARE_3, seme=rng.getrandbits(63), dettaglio=ESSENZIALE)
    assert len(abitudini) > 3000
    assert sum(1 for x in abitudini if x > 0.0) / len(abitudini) < 0.27
    assert statistics.fmean(abitudini) < 0.035


def _parata_del_colpo(colpi_di_chi_attacca):
    """Le fasce della parata di un lungolinea sinistro dello scambio, con gli attacchi già giocati da chi attacca."""
    battitore, ricevitore = _coppia()
    _abituati(ricevitore, colpi_di_chi_attacca)
    passi = []
    gioca_punto(battitore, ricevitore, DadoScritto([*_inizio_regolare(), FERMATA, CONTROLLO_RIUSCITO, LUNGOLINEA_SX, COLPO_RIUSCITO, (0, 0.5)]), TARATURA, passi)
    return [p for p in passi if p.tipo == "parata"]


def test_il_colpo_ripetuto_preme_meno_soltanto_nello_scambio():
    # La battuta del punto non risente degli attacchi del battitore; il colpo dello scambio ripetuto sì.
    fresca, nello_scambio = _parata_del_colpo({})
    abituata, ripetuto = _parata_del_colpo({"lungolineasx": 30})
    assert abituata.prob == pytest.approx(fresca.prob)
    assert ripetuto.prob[0] < nello_scambio.prob[0] and sum(ripetuto.prob) == pytest.approx(1.0)


def test_la_battuta_e_la_ribattuta_non_risentono_dell_abitudine():
    battitore, ricevitore = _coppia()
    _abituati(battitore, {"lungolineasx": 30})
    _abituati(ricevitore, {"lungolineasx": 30})
    passi = []
    gioca_punto(battitore, ricevitore, DadoScritto([*_inizio_regolare(), (3, 0.5), NON_LENTA, 0.0, (0, 0.5)]), TARATURA, passi)
    con = [p.prob for p in passi if p.tipo == "parata"]
    battitore, ricevitore = _coppia()
    passi = []
    gioca_punto(battitore, ricevitore, DadoScritto([*_inizio_regolare(), (3, 0.5), NON_LENTA, 0.0, (0, 0.5)]), TARATURA, passi)
    senza = [p.prob for p in passi if p.tipo == "parata"]
    assert len(con) == len(senza) == 2
    assert con == pytest.approx(senza)


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
