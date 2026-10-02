"""Test del motore grammaticale: articoli, preposizioni articolate, accordo degli aggettivi."""

import pytest

from grammatica import (
    Aggettivo,
    Sostantivo,
    con_determinativo,
    con_indeterminativo,
    elenco,
    preposizione_articolata,
)


@pytest.mark.parametrize(
    ("lemma", "genere", "numero", "atteso"),
    [
        ("naso", "m", "s", "il naso"),
        ("sguardo", "m", "s", "lo sguardo"),
        ("gnomo", "m", "s", "lo gnomo"),
        ("occhio", "m", "s", "l'occhio"),
        ("incarnato", "m", "s", "l'incarnato"),
        ("occhi", "m", "p", "gli occhi"),
        ("zigomi", "m", "p", "gli zigomi"),
        ("capelli", "m", "p", "i capelli"),
        ("bocca", "f", "s", "la bocca"),
        ("arcata", "f", "s", "l'arcata"),
        ("labbra", "f", "p", "le labbra"),
    ],
)
def test_articolo_determinativo(lemma, genere, numero, atteso):
    assert con_determinativo(Sostantivo(lemma, genere, numero)) == atteso


@pytest.mark.parametrize(
    ("lemma", "genere", "numero", "atteso"),
    [
        ("naso", "m", "s", "un naso"),
        ("sguardo", "m", "s", "uno sguardo"),
        ("zigomo", "m", "s", "uno zigomo"),
        ("uomo", "m", "s", "un uomo"),
        ("bocca", "f", "s", "una bocca"),
        ("arcata", "f", "s", "un'arcata"),
        ("occhiaie", "f", "p", "occhiaie"),
    ],
)
def test_articolo_indeterminativo(lemma, genere, numero, atteso):
    assert con_indeterminativo(Sostantivo(lemma, genere, numero)) == atteso


def test_partitivo():
    assert con_indeterminativo(Sostantivo("occhi", "m", "p"), partitivo=True) == "degli occhi"
    assert con_indeterminativo(Sostantivo("capelli", "m", "p"), partitivo=True) == "dei capelli"
    assert con_indeterminativo(Sostantivo("labbra", "f", "p"), partitivo=True) == "delle labbra"


@pytest.mark.parametrize(
    ("preposizione", "lemma", "genere", "numero", "atteso"),
    [
        ("da", "carnagione", "f", "s", "dalla carnagione"),
        ("da", "occhi", "m", "p", "dagli occhi"),
        ("da", "capelli", "m", "p", "dai capelli"),
        ("da", "viso", "m", "s", "dal viso"),
        ("da", "incarnato", "m", "s", "dall'incarnato"),
        ("da", "sguardo", "m", "s", "dallo sguardo"),
        ("su", "guance", "f", "p", "sulle guance"),
        ("di", "sguardo", "m", "s", "dello sguardo"),
        ("con", "naso", "m", "s", "con il naso"),
    ],
)
def test_preposizione_articolata(preposizione, lemma, genere, numero, atteso):
    assert con_determinativo(Sostantivo(lemma, genere, numero), preposizione) == atteso


def test_preposizione_davanti_ad_aggettivo():
    # L'articolo dipende dalla parola che segue: davanti a un aggettivo che comincia per s impura si usa lo.
    assert preposizione_articolata("da", Sostantivo("strano", "m")) == "dallo"
    assert preposizione_articolata("da", Sostantivo("bel", "m")) == "dal"


@pytest.mark.parametrize(
    ("ms", "mp", "fs", "fp"),
    [
        ("rosso", "rossi", "rossa", "rosse"),
        ("bianco", "bianchi", "bianca", "bianche"),
        ("lungo", "lunghi", "lunga", "lunghe"),
        ("malinconico", "malinconici", "malinconica", "malinconiche"),
        ("greco", "greci", "greca", "greche"),
        ("liscio", "lisci", "liscia", "lisce"),
        ("riccio", "ricci", "riccia", "ricce"),
        ("grigio", "grigi", "grigia", "grigie"),
        ("ampio", "ampi", "ampia", "ampie"),
        ("dolce", "dolci", "dolce", "dolci"),
        ("latteo", "lattei", "lattea", "lattee"),
        ("nocciola", "nocciola", "nocciola", "nocciola"),
        ("blu", "blu", "blu", "blu"),
        ("all'insù", "all'insù", "all'insù", "all'insù"),
        ("biondo cenere", "biondo cenere", "biondo cenere", "biondo cenere"),
        ("ben curato", "ben curati", "ben curata", "ben curate"),
        ("leggermente storto", "leggermente storti", "leggermente storta", "leggermente storte"),
    ],
)
def test_forme_degli_aggettivi(ms, mp, fs, fp):
    aggettivo = Aggettivo(ms)
    assert (aggettivo.ms, aggettivo.mp, aggettivo.fs, aggettivo.fp) == (ms, mp, fs, fp)


def test_aggettivo_con_complemento():
    aggettivo = Aggettivo(base="pettinato", dopo="all'indietro")
    assert aggettivo.chiave == "pettinato all'indietro"
    assert aggettivo.accorda(Sostantivo("capelli", "m", "p")) == "pettinati all'indietro"
    assert aggettivo.accorda(("f", "p")) == "pettinate all'indietro"


@pytest.mark.parametrize(
    ("parti", "atteso"),
    [
        ([], ""),
        (["alto"], "alto"),
        (["alto", "robusto"], "alto e robusto"),
        (["corti", "mossi", "folti"], "corti, mossi e folti"),
        (["alta", "esile"], "alta ed esile"),
        (["alto", None, "robusto"], "alto e robusto"),
    ],
)
def test_elenco(parti, atteso):
    assert elenco(parti) == atteso
