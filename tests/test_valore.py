"""
Test del valore complessivo della tappa 9: con i pesi della tappa 8 è l'indice di prima, le due
parti sommano al totale, i pesi non sono negativi, un mancino specchiato vale quanto il
destrimano più il suo tratto, che sta fra 2 e 6 punti come vuole Gabriele, decisione D26, e con
i pesi misurati dalla taratura un mondo appena nato ha la mediana attorno a 140
e lo stesso monte stipendi di prima, perché l'economia della decisione D22 non cambi.
Dalla tappa 12, punto 1.3 del progetto, le somme si leggono dal dizionario degli attributi, col
ripiego sulla via di prima per chi ne ha uno incompleto: le due vie danno gli stessi numeri fino
all'ultimo bit, e la vista leggera del formato 5 dà gli stessi stipendi della versione 1.60.11.
"""

import datetime
import hashlib
import math
import random
import types

import pytest

import archivio
import valore
from costanti import (
    ATTRIBUTI_ALLENABILI,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    CARATTERISTICHE_VALORE,
    PESI_TRATTI,
    PESI_VALORE,
    SCALA_STIPENDIO,
    SCALA_VALORE_B,
    VALORE_DI_RIFERIMENTO,
)
from modelli import Giocatore

# I pesi della tappa 8, con cui il valore nuovo deve ridare la formula di prima.
PESI_TAPPA_8 = dict.fromkeys(CARATTERISTICHE_VALORE, 1.0)
TRATTI_TAPPA_8 = {"mancino": 0.0, "ambidestro": 33.0, "giocorapido": 33.0, "cambiovelocita": 33.0}

NASCITA = datetime.datetime(2026, 1, 1)


@pytest.fixture
def giocatori():
    random.seed(140)
    gruppo = [Giocatore(i, NASCITA) for i in range(1, 81)]
    rng = random.Random(1)
    for g in gruppo[::2]:
        for nome in ATTRIBUTI_ALLENABILI:
            setattr(g, nome, rng.uniform(0, 4))
        g._rispetta_tetti()
        g.aggiorna_icv()
    return gruppo


def _formula_di_prima(g):
    somma = sum(getattr(g, nome) for nome in ATTRIBUTI_BASE_CON_ALLENABILI) + sum(getattr(g, nome) for nome in ATTRIBUTI_ALLENABILI)
    return somma + 33 * sum(bool(getattr(g, tratto)) for tratto in ("ambidestro", "giocorapido", "cambiovelocita"))


def test_con_i_pesi_della_tappa_8_l_indice_e_quello_di_prima(giocatori):
    for g in giocatori:
        assert valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) == pytest.approx(_formula_di_prima(g))
        assert g.indice_collettivo_valore == pytest.approx(valore.indice(g))


def test_le_due_parti_sommano_al_totale(giocatori):
    for g in giocatori:
        base, allenato = valore.parti(g)
        assert base + allenato == pytest.approx(valore.indice(g))
        assert (g.icv_base, g.icv_allenato) == (base, allenato)


def test_pesi_non_negativi_e_completi():
    assert set(PESI_VALORE) == set(CARATTERISTICHE_VALORE) and len(CARATTERISTICHE_VALORE) == 24
    assert all(peso >= 0 for peso in PESI_VALORE.values())
    assert all(peso >= 0 for peso in PESI_TRATTI.values())


def _specchia(g):
    """Il mancino specchiato: chiusure e blocchi scambiati di lato, e il tratto del mancino."""
    for coppia in (("chiusurasx", "chiusuradx"), ("bloccosx", "bloccodx")):
        for parte in ("_base", "_allenata"):
            sx, dx = coppia[0] + parte, coppia[1] + parte
            valore_sx, valore_dx = getattr(g, sx), getattr(g, dx)
            setattr(g, sx, valore_dx)
            setattr(g, dx, valore_sx)
    g.mancino = True
    g.ambidestro = False
    g.aggiorna_icv()
    return g


def test_un_mancino_specchiato_vale_quanto_il_destrimano(giocatori):
    for g in giocatori:
        if g.mancino or g.ambidestro:
            continue
        prima = valore.caratteristiche(g)
        indice = valore.indice(g)
        _specchia(g)
        assert valore.caratteristiche(g) == pytest.approx(prima)
        assert valore.indice(g) == pytest.approx(indice + SCALA_VALORE_B * PESI_TRATTI["mancino"])


def test_il_vantaggio_del_mancino_resta_nella_banda_di_gabriele():
    # D26: il vantaggio del mancino nel valore resta piccolo ma visibile, fra 2 e 6 punti. Il peso
    # è la media di quattro semi della taratura, perché con un seme solo andava da 2,9 a 5,6.
    assert 2.0 <= SCALA_VALORE_B * PESI_TRATTI["mancino"] <= 6.0


def test_l_ambidestro_fa_la_media_dei_lati(giocatori):
    g = giocatori[0]
    g.ambidestro, g.mancino = True, False
    c = valore.caratteristiche(g)
    assert c["chiusura_dritto"] == c["chiusura_rovescio"] == pytest.approx((g._get_valore_totale("chiusurasx_base") + g._get_valore_totale("chiusuradx_base")) / 2)
    with pytest.raises(ValueError, match="Parte sconosciuta"):
        valore.caratteristiche(g, "media")


def test_un_mondo_appena_nato_resta_sotto_la_scala_del_mondo_allenato():
    # Dalla tappa 11 la scala si tara sul mondo che si allena, all'anno 10 della simulazione lunga:
    # la mediana del valore dei giocatori in attività sta a 135,5, e lo stipendio pagato al decimo
    # percentile a 105 euro. I neonati non si sono ancora allenati, e stanno più in basso: su
    # ottocento la mediana è 127, e la media del fattore dello stipendio è tre quarti di quella del
    # valore della tappa 8, come il progetto aveva previsto per i giocatori mai allenati.
    stato = random.getstate()
    random.seed(2026)
    try:
        neonati = [Giocatore(i, NASCITA) for i in range(1, 801)]
    finally:
        random.setstate(stato)
    nuovi = sorted(g.indice_collettivo_valore for g in neonati)
    vecchi = [valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in neonati]
    assert 122 <= nuovi[len(nuovi) // 2] <= 132

    def fattore(indici):
        return sum(math.exp((i - VALORE_DI_RIFERIMENTO) / SCALA_STIPENDIO) for i in indici) / len(indici)

    assert 0.65 * fattore(vecchi) <= fattore(nuovi) <= 0.9 * fattore(vecchi)


# Dalla tappa 12: le somme veloci, lette dal dizionario degli attributi, e la via di prima.

# Gli stipendi e l'impronta dei valori delle viste del formato 5 di _viste_del_formato_5, calcolati
# una volta dal codice della versione 1.60.11, prima delle somme veloci, il 13 ottobre 2026.
STIPENDI_DELLE_VISTE = [2530, 2310, 3450, 5550, 2060, 240, 1320, 530, 4130, 9000, 8490, 1620, 490, 1860, 410, 2250, 7750, 2870, 2530, 17580, 5470, 2670, 11590, 1520,
                        510, 22400, 11980, 1270, 77400, 4930, 2340, 1180, 1960, 4290, 530, 2100, 17520, 650, 3690, 27300, 5000, 2560, 5880, 2440, 10930, 2760,
                        14780, 310, 1570, 1300, 2390, 1810, 7040, 34560, 460, 1260, 3260, 6220, 3230, 3520]
IMPRONTA_DELLE_VISTE = "aeb5ee627f11c4138e540d136fdaed5021feb33b408d8b4a1fe37de469e91276"


def _viste_del_formato_5():
    """
    Sessanta giocatori del formato 5 come li legge archivio.stipendio_della_1_50, costruiti con un
    seme: tutte le parti delle caratteristiche, i tratti e l'esperienza; a uno su cinque mancano due
    parti, come a un salvataggio vecchio, e la somma passa dalla via di prima.
    """
    rng = random.Random("viste-del-formato-5")
    viste = []
    for gid in range(1, 61):
        dati = {"id": gid, "esperienza": round(rng.uniform(0.0, 15.0), 2), "mancino": rng.random() < 0.15, "ambidestro": rng.random() < 0.1,
                "giocorapido": rng.random() < 0.12, "cambiovelocita": rng.random() < 0.15}
        for nome in ATTRIBUTI_BASE_CON_ALLENABILI:
            dati[nome] = rng.uniform(0.0, 3.0 if nome in ("precisione_base", "resistenza_base", "forza_base") else 12.0)
        for nome in ATTRIBUTI_ALLENABILI:
            dati[nome] = rng.uniform(0.0, 6.0) if rng.random() < 0.6 else 0.0
        if gid % 5 == 0:
            for nome in rng.sample(sorted(ATTRIBUTI_BASE_CON_ALLENABILI + ATTRIBUTI_ALLENABILI), 2):
                del dati[nome]
        viste.append(dati)
    return viste


def _stipendi_e_impronta(viste):
    stipendi = [archivio.stipendio_della_1_50(v) for v in viste]
    indici = [valore.indice(types.SimpleNamespace(**v), archivio.PESI_VALORE_FORMATO_5, archivio.PESI_TRATTI_FORMATO_5, archivio.SCALA_A_FORMATO_5,
                            archivio.SCALA_B_FORMATO_5) for v in viste]
    return stipendi, hashlib.sha256(repr(indici).encode("utf-8")).hexdigest()


def test_la_vista_del_formato_5_da_gli_stipendi_di_prima():
    stipendi, impronta = _stipendi_e_impronta(_viste_del_formato_5())
    assert stipendi == STIPENDI_DELLE_VISTE
    assert impronta == IMPRONTA_DELLE_VISTE


def test_le_due_vie_della_somma_danno_gli_stessi_bit(giocatori):
    giocatori[1].ambidestro, giocatori[1].mancino = True, False
    giocatori[2].ambidestro, giocatori[2].mancino = False, True
    for g in giocatori:
        for pesi in (PESI_VALORE, PESI_TAPPA_8):
            assert valore._somme_dal_dizionario(g.__dict__, pesi) == valore._somme_con_getattr(g, pesi)
    incompleta = types.SimpleNamespace(**dict.fromkeys(ATTRIBUTI_BASE_CON_ALLENABILI, 1.0))
    assert valore._somme(incompleta, PESI_VALORE) == valore._somme_con_getattr(incompleta, PESI_VALORE)
    assert valore._somme(incompleta, PESI_VALORE)[1] == 0.0
