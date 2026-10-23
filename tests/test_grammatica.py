"""Test del motore grammaticale: articoli, preposizioni articolate, accordo degli aggettivi."""

import pytest

from grammatica import (
    Aggettivo,
    Sostantivo,
    accorda_al_torneo,
    con_determinativo,
    con_indeterminativo,
    elenco,
    forma_del_torneo,
    preposizione_articolata,
    torneo_con_preposizione,
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


# La revisione della tappa 14: la preposizione davanti al nome di un torneo.

@pytest.mark.parametrize(
    ("nome", "preposizione", "atteso"),
    [
        ("Campionato italiano maschile", "a", "al Campionato italiano maschile"),
        ("Gran Premio femminile", "a", "al Gran Premio femminile"),
        ("Open misto del mese", "a", "all'Open misto del mese"),
        ("Coppa delle polisportive", "a", "alla Coppa delle polisportive"),
        ("Open femminile del giovedì", "da", "dall'Open femminile del giovedì"),
        ("Campionato italiano femminile", "da", "dal Campionato italiano femminile"),
        ("Coppa delle polisportive", "di", "della Coppa delle polisportive"),
        ("Supercoppa d'inverno", "a", "alla Supercoppa d'inverno"),
        ("Europei a squadre", "a", "agli Europei a squadre"),
        ("Giochi del Mediterraneo", "a", "ai Giochi del Mediterraneo"),
        ("Olimpiadi dello showdown", "a", "alle Olimpiadi dello showdown"),
        ("Sfida dei campioni", "a", "alla Sfida dei campioni"),
        ("Trofeo, edizione speciale", "a", "al Trofeo, edizione speciale"),
        ("Il Trofeo dei Tigli", "a", "al Trofeo dei Tigli"),
        ("Lo Showdown d'oro", "a", "allo Showdown d'oro"),
        ("La Coppa del lago", "da", "dalla Coppa del lago"),
        ("L'Aquila d'argento", "a", "all'Aquila d'argento"),
        ("Le Giornate di Ostia", "a", "alle Giornate di Ostia"),
        ("Gran Premio femminile", "per", "per il Gran Premio femminile"),
        # Un nome che non si riconosce resta com'è, con la preposizione semplice.
        ("Showdown d'autunno", "a", "a Showdown d'autunno"),
        ("Showdown d'autunno", "da", "da Showdown d'autunno"),
        ("I Memorial Rossi", "a", "a I Memorial Rossi"),
        ("Il", "a", "a Il"),
        # Davanti a una a, la d eufonica.
        ("Autunno in gara", "a", "ad Autunno in gara"),
        ("Autunno in gara", "da", "da Autunno in gara"),
    ],
)
def test_la_preposizione_davanti_al_torneo(nome, preposizione, atteso):
    assert torneo_con_preposizione(nome, preposizione) == atteso


def test_i_nomi_dei_tornei_predefiniti_si_riconoscono_tutti():
    # I modelli che viaggiano col programma vogliono tutti la preposizione articolata.
    import json
    import pathlib

    import modelli_torneo
    import percorsi

    cartella = pathlib.Path(percorsi.risorsa(modelli_torneo.RISORSA))
    nomi = [json.loads(file.read_text(encoding="utf-8"))["nome"] for file in cartella.glob("*.json")]
    assert len(nomi) == 10
    for nome in nomi:
        assert torneo_con_preposizione(nome).startswith(("al ", "all'", "alla ")), nome


# La seconda revisione della tappa 14: il solo articolo davanti al nome di un torneo, e l'accordo.

@pytest.mark.parametrize(
    ("nome", "atteso"),
    [
        ("Campionato italiano maschile", "il Campionato italiano maschile"),
        ("Gran Premio femminile", "il Gran Premio femminile"),
        ("Open misto del mese", "l'Open misto del mese"),
        ("Coppa delle polisportive", "la Coppa delle polisportive"),
        ("Europei a squadre", "gli Europei a squadre"),
        ("Giochi del Mediterraneo", "i Giochi del Mediterraneo"),
        ("Il Trofeo dei Tigli", "il Trofeo dei Tigli"),
        ("La Coppa del lago", "la Coppa del lago"),
        ("L'Aquila d'argento", "l'Aquila d'argento"),
        ("Le Giornate di Ostia", "le Giornate di Ostia"),
        # Un nome che non si riconosce resta senza articolo, anche se comincia per a.
        ("Showdown d'autunno", "Showdown d'autunno"),
        ("Autunno in gara", "Autunno in gara"),
        ("", ""),
    ],
)
def test_il_solo_articolo_davanti_al_torneo(nome, atteso):
    assert torneo_con_preposizione(nome, None) == atteso


@pytest.mark.parametrize(
    ("nome", "forma", "annullato"),
    [
        ("Campionato italiano maschile", ("m", "s"), "è annullato"),
        ("Open misto del mese", ("m", "s"), "è annullato"),
        ("Coppa delle polisportive", ("f", "s"), "è annullata"),
        ("Europei a squadre", ("m", "p"), "sono annullati"),
        ("Olimpiadi dello showdown", ("f", "p"), "sono annullate"),
        ("La Sagra del lago", ("f", "s"), "è annullata"),
        ("Le Giornate di Ostia", ("f", "p"), "sono annullate"),
        ("L'Olimpiade di Roma", ("f", "s"), "è annullata"),
        ("L'Aquila d'argento", ("m", "s"), "è annullato"),
        ("Showdown d'autunno", ("m", "s"), "è annullato"),
        ("", ("m", "s"), "è annullato"),
    ],
)
def test_l_accordo_col_torneo(nome, forma, annullato):
    assert forma_del_torneo(nome) == forma
    assert accorda_al_torneo(nome, "annullato") == annullato
