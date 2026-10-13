"""
Test delle formule dei tornei della tappa 12, formule.py, punto 3.5 del progetto: ogni regola della
validazione con un caso valido e uno sbagliato, la cascata, la lettura dei predefiniti in una
cartella vuota, il file rovinato e la formula scartata col motivo, la scrittura che rifiuta le
formule non valide, l'eliminazione di una formula usata rifiutata col nome dei modelli, e la
struttura adattata agli iscritti veri del punto 4.4.
"""

import copy
import json
import types

import pytest

import formule


@pytest.fixture(autouse=True)
def cache_pulita():
    formule.azzera_cache()
    yield
    formule.azzera_cache()


def _fase(tipo="tabellone", partecipanti=2, gironi=0, promossi=0, finalina=False):
    return {"tipo": tipo, "partecipanti": partecipanti, "gironi": gironi, "promossi": promossi, "finalina": finalina}


def _formula(*fasi, id_formula="prova", nome="Formula di prova"):
    return {"id": id_formula, "nome": nome, "descrizione": "", "fasi": list(fasi)}


def _gironi_32():
    return _formula(_fase("gironi", 32, 8, 2), _fase(partecipanti=16), _fase(partecipanti=8), _fase(partecipanti=4, finalina=True), _fase())


def test_le_formule_predefinite_sono_valide_e_si_copiano_accanto_al_gioco(cartella_di_prova):
    valide, scartate = formule.leggi()
    assert not scartate
    assert [f["id"] for f in valide] == ["gironi_32", "gironi_64", "tabellone_32", "girone_unico_8", "squadre_64"]
    assert (cartella_di_prova / formule.NOME_FILE).exists()
    assert formule.tetto(formule.formula("gironi_64")) == 64
    assert formule.formula("non_c_e") is None


def test_la_lettura_restituisce_copie():
    valide, _scartate = formule.leggi()
    valide[0]["nome"] = "Cambiata"
    assert formule.leggi()[0][0]["nome"] != "Cambiata"


def test_una_formula_valida_passa():
    assert formule.valida_formula(_gironi_32()) is None
    assert formule.valida_formula(_formula(_fase("gironi", 8, 1, 1))) is None
    assert formule.valida_formula(_formula(_fase(partecipanti=1024), *(_fase(partecipanti=2 ** k) for k in range(9, 0, -1)))) is None


@pytest.mark.parametrize(("formula", "parole"), [
    (_formula(), "da 1 a 12 fasi"),
    (_formula(*(_fase("gironi", 4, 2, 1) for _ in range(13))), "da 1 a 12 fasi"),
    (_formula(_fase(partecipanti=2048), *(_fase(partecipanti=2 ** k) for k in range(10, 0, -1))), "da 2 a 1024"),
    (_formula(_fase("gironi", 1, 1, 0)), "da 2 a 1024"),
    (_formula(_fase("gironi", 8, 0, 1)), "almeno un girone"),
    (_formula(_fase("gironi", 9, 2, 1), _fase()), "parti uguali"),
    (_formula(_fase("gironi", 26, 2, 1), _fase()), "da 2 a 12"),
    (_formula(_fase("gironi", 8, 8, 1), _fase(partecipanti=8), _fase(partecipanti=4), _fase()), "da 2 a 12"),
    (_formula(_fase("gironi", 8, 2, 4), _fase(partecipanti=8), _fase(partecipanti=4), _fase()), "da 1 a 3"),
    (_formula(_fase("gironi", 8, 2, 0), _fase()), "da 1 a 3"),
    (_formula(_fase("gironi", 8, 2, 1, finalina=True), _fase()), "finalina"),
    (_formula(_fase(partecipanti=6), _fase(partecipanti=3)), "potenza di 2"),
    (_formula(_fase(partecipanti=8, gironi=2), _fase(partecipanti=4), _fase()), "né promossi"),
    (_formula(_fase(partecipanti=8, finalina=True), _fase(partecipanti=4), _fase()), "soltanto con 4"),
    (_formula(_fase("gironi", 8, 2, 2), _fase(partecipanti=8), _fase(partecipanti=4), _fase()), "deve avere 4 partecipanti"),
    (_formula(_fase(partecipanti=8), _fase(partecipanti=8), _fase(partecipanti=4), _fase()), "deve avere 4 partecipanti"),
    (_formula(_fase(partecipanti=8), _fase("gironi", 4, 2, 1)), "finale di un tabellone"),
    (_formula(_fase(partecipanti=4, finalina=True), _fase("gironi", 2, 1, 0)), "viene la finale"),
    (_formula(_fase("gironi", 8, 2, 2)), "finale di un tabellone"),
])
def test_ogni_regola_rifiuta_col_suo_motivo(formula, parole):
    problema = formule.valida_formula(formula)
    assert problema is not None and parole in problema, problema


def test_campi_e_tipi_controllati():
    formula = _gironi_32()
    formula["punti_vittoria"] = 3
    assert "campi sconosciuti" in formule.valida_formula(formula)
    formula = _gironi_32()
    del formula["descrizione"]
    assert "mancano" in formule.valida_formula(formula)
    formula = _gironi_32()
    formula["fasi"][0]["pareggio"] = 1
    assert "campi sconosciuti" in formule.valida_formula(formula)
    formula = _gironi_32()
    formula["fasi"][1]["partecipanti"] = True
    assert "numeri interi" in formule.valida_formula(formula)
    formula = _gironi_32()
    formula["fasi"][2]["finalina"] = 1
    assert "sì o no" in formule.valida_formula(formula)
    formula = _gironi_32()
    formula["fasi"][0]["tipo"] = "svizzero"
    assert "gironi o a tabellone" in formule.valida_formula(formula)
    assert "nome" in formule.valida_formula(_gironi_32() | {"nome": "ab"})


def test_l_ultima_fase_a_gironi_ammette_qualunque_promosso():
    assert formule.valida_formula(_formula(_fase(partecipanti=8), _fase(partecipanti=4), _fase("gironi", 2, 1, 0))) is None
    assert "da 0 a 3" in formule.valida_formula(_formula(_fase("gironi", 4, 1, 4)))


def test_la_cascata_ricalcola_le_fasi_seguenti():
    formula = _gironi_32()
    formula["fasi"][0].update(partecipanti=64, gironi=16)
    formule.aggiorna_cascata(formula["fasi"], 0)
    assert [f["partecipanti"] for f in formula["fasi"]] == [64, 32, 16, 8, 4]
    assert formule.valida_formula(formula) is not None
    formula["fasi"][1:] = [_fase(partecipanti=32), _fase(partecipanti=16), _fase(partecipanti=8), _fase(partecipanti=4, finalina=True), _fase()]
    assert formule.valida_formula(formula) is None


def test_un_file_rovinato_si_dice_col_motivo(cartella_di_prova):
    (cartella_di_prova / formule.NOME_FILE).write_text("{ non è json", encoding="utf-8")
    valide, scartate = formule.leggi()
    assert valide == [] and scartate[0][0] == formule.NOME_FILE and "non si legge" in scartate[0][1]


def test_una_formula_sbagliata_si_scarta_e_le_altre_restano(cartella_di_prova):
    sbagliata = _formula(_fase(partecipanti=6), id_formula="sbagliata")
    doppia = copy.deepcopy(_gironi_32())
    contenuto = {"formule": [_gironi_32(), sbagliata, doppia, "testo"]}
    (cartella_di_prova / formule.NOME_FILE).write_text(json.dumps(contenuto), encoding="utf-8")
    valide, scartate = formule.leggi()
    assert [f["id"] for f in valide] == ["prova"]
    motivi = dict(scartate)
    assert "potenza di 2" in motivi["sbagliata"]
    assert "già di un'altra formula" in motivi["prova"]
    assert "non è descritta" in motivi["la formula numero 4"]


def test_la_scrittura_rifiuta_e_poi_scrive(cartella_di_prova):
    with pytest.raises(ValueError, match="potenza di 2"):
        formule.scrivi([_formula(_fase(partecipanti=6))])
    with pytest.raises(ValueError, match="stesso identificativo"):
        formule.scrivi([_gironi_32(), _gironi_32()])
    assert not (cartella_di_prova / formule.NOME_FILE).exists()
    formule.scrivi([_gironi_32()])
    assert [f["id"] for f in formule.leggi()[0]] == ["prova"]
    assert not list(cartella_di_prova.glob("*.tmp"))


def test_eliminare_una_formula_usata_si_rifiuta_col_nome_dei_modelli():
    modelli = [types.SimpleNamespace(nome="Open del sabato", formula="gironi_32"), types.SimpleNamespace(nome="aperto del lunedì", formula="gironi_32"),
               types.SimpleNamespace(nome="Gran Premio", formula="gironi_64")]
    assert formule.in_uso("gironi_32", modelli) == ["aperto del lunedì", "Open del sabato"]
    with pytest.raises(ValueError, match="aperto del lunedì, Open del sabato"):
        formule.elimina("gironi_32", modelli)
    formule.elimina("tabellone_32", modelli)
    assert formule.formula("tabellone_32") is None and formule.formula("gironi_32") is not None
    with pytest.raises(ValueError, match="non c'è"):
        formule.elimina("tabellone_32", modelli)


def test_il_nuovo_identificativo_e_il_primo_libero():
    assert formule.nuovo_id([]) == "formula_1"
    assert formule.nuovo_id([{"id": "formula_1"}, {"id": "formula_3"}]) == "formula_2"


# La struttura adattata agli iscritti veri, punto 4.4.

def _descrivi(struttura):
    righe = []
    for fase in struttura:
        if fase["tipo"] == formule.GIRONI:
            righe.append(("gironi", tuple(fase["grandezze"]), fase["promossi"]))
        else:
            righe.append(("tabellone", fase["grandezza"], fase["qualificati"], fase["finalina"]))
    return righe


@pytest.mark.parametrize(("iscritti", "attesa"), [
    (32, [("gironi", (4,) * 8, 2), ("tabellone", 16, 16, True)]),
    (20, [("gironi", (4,) * 5, 2), ("tabellone", 16, 10, True)]),
    (13, [("gironi", (5, 4, 4), 2), ("tabellone", 8, 6, True)]),
    (6, [("gironi", (3, 3), 2), ("tabellone", 4, 4, True)]),
    (5, [("gironi", (5,), 2), ("tabellone", 2, 2, False)]),
    (4, [("gironi", (4,), 2), ("tabellone", 2, 2, False)]),
])
def test_la_struttura_degli_esempi_del_progetto(iscritti, attesa):
    assert _descrivi(formule.struttura(formule.formula("gironi_32"), iscritti)) == attesa


def test_la_struttura_regge_da_2_al_tetto_per_ogni_formula_predefinita():
    for formula in formule.leggi()[0]:
        for n in range(2, formule.tetto(formula) + 1):
            struttura = formule.struttura(formula, n)
            assert struttura[-1]["ultima"] and not any(f["ultima"] for f in struttura[:-1])
            if struttura[0]["tipo"] == formule.GIRONI:
                grandezze = struttura[0]["grandezze"]
                assert sum(grandezze) == n and max(grandezze) - min(grandezze) <= 1
            else:
                assert struttura[0]["qualificati"] == n and struttura[0]["grandezza"] >= n
    with pytest.raises(ValueError, match="al massimo 32"):
        formule.struttura(formule.formula("gironi_32"), 33)


def test_un_tabellone_dopo_i_gironi_e_i_gironi_dopo_un_tabellone():
    formula = _formula(_fase(partecipanti=32), _fase(partecipanti=16), _fase("gironi", 8, 2, 2), _fase(partecipanti=4, finalina=True), _fase())
    assert formule.valida_formula(formula) is None
    struttura = formule.struttura(formula, 20)
    assert _descrivi(struttura) == [("tabellone", 32, 20, False), ("gironi", (4, 4), 2), ("tabellone", 4, 4, True)]
    assert struttura[0]["turni"] == 2
    # Con cinque iscritti il primo tabellone da otto, in due turni, lascia due giocatori: il girone da
    # due promuoverebbe uno solo, quindi decide il torneo, e la finale non serve.
    corta = formule.struttura(formula, 5)
    assert _descrivi(corta) == [("tabellone", 8, 5, False), ("gironi", (2,), 0)] and corta[-1]["ultima"]
    # Con tre iscritti il primo tabellone da quattro, in due turni, lascia il vincitore: il torneo finisce lì.
    corta = formule.struttura(formula, 3)
    assert _descrivi(corta) == [("tabellone", 4, 3, False)] and corta[0]["ultima"]
