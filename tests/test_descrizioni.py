"""Test delle descrizioni fisiche: vocabolario, forma dei testi, regole di età e sesso, curve di crescita."""

import json
import random
import statistics

import pytest

import descrizioni

ETA_PROVA = (9.5, 12, 15, 17, 22, 30, 41, 55, 66, 80)
DIFETTI = ("  ", " ,", ",,", "..", " .", "(", ")", "None", " e e ", " ed ed ", ", e e ", "  ")


def giocatori(quanti, seme=1):
    rng = random.Random(seme)
    for i in range(quanti):
        sesso = "m" if i % 2 == 0 else "f"
        yield sesso, descrizioni.genera_tratti(sesso, rng)


def test_ogni_aggettivo_del_vocabolario_ha_le_quattro_forme():
    for chiave, aggettivo in descrizioni.vocabolario()["_aggettivi"].items():
        forme = (aggettivo.ms, aggettivo.mp, aggettivo.fs, aggettivo.fp)
        assert all(forme), chiave
        assert aggettivo.chiave == chiave


def test_i_testi_sono_ben_formati():
    for sesso, tratti in giocatori(300):
        for eta in ETA_PROVA:
            testo = descrizioni.descrivi(tratti, sesso, eta)
            assert testo[0].isupper(), testo
            assert testo.endswith("."), testo
            for difetto in DIFETTI:
                assert difetto not in testo, (difetto, testo)


def test_la_descrizione_non_cambia_se_non_cambia_eta():
    for sesso, tratti in giocatori(50):
        copia = json.loads(json.dumps(tratti))
        assert descrizioni.descrivi(tratti, sesso, 33) == descrizioni.descrivi(copia, sesso, 33)


def test_barba_solo_ai_maschi_adulti_e_trucco_solo_alle_femmine():
    parole_barba = ("barba", "pizzetto", "baffi", "basette", "sbarbato", "ben rasato")
    for sesso, tratti in giocatori(300):
        for eta in ETA_PROVA:
            testo = descrizioni.descrivi(tratti, sesso, eta)
            if sesso == "f" or eta < descrizioni.ETA_BARBA:
                assert not any(p in testo for p in parole_barba), testo
            if sesso == "m" or eta < descrizioni.ETA_TRUCCO:
                assert "trucco" not in testo, testo


def test_capelli_tinti_solo_dall_eta_della_tinta():
    sesso, tratti = next(giocatori(1))
    tratti["capelli"]["tinta"] = "fucsia"
    assert "fucsia" not in descrizioni.descrivi(tratti, sesso, 11)
    assert "fucsia" in descrizioni.descrivi(tratti, sesso, 20) or "calvo" in descrizioni.descrivi(tratti, sesso, 20)


@pytest.mark.parametrize(("eta", "maschio", "femmina"), [(10, "ragazzino", "ragazzina"), (20, "ragazzo", "ragazza"), (35, "uomo", "donna")])
def test_la_persona_segue_eta(eta, maschio, femmina):
    for sesso, tratti in giocatori(20):
        parola = maschio if sesso == "m" else femmina
        assert f" {parola} " in descrizioni.descrivi(tratti, sesso, eta)


def test_altezza_media_degli_adulti():
    altezze = {"m": [], "f": []}
    for sesso, tratti in giocatori(4000, seme=7):
        altezze[sesso].append(descrizioni.fisico(tratti, sesso, 30)[0])
    assert 174.5 <= statistics.fmean(altezze["m"]) <= 177.5
    assert 161.5 <= statistics.fmean(altezze["f"]) <= 164.5


def test_si_cresce_fino_a_diciotto_anni():
    for sesso, tratti in giocatori(100):
        altezze = [descrizioni.fisico(tratti, sesso, eta)[0] for eta in range(9, 19)]
        pesi = [descrizioni.fisico(tratti, sesso, eta)[1] for eta in range(9, 19)]
        assert altezze == sorted(altezze)
        assert pesi == sorted(pesi)
        assert altezze[-1] - altezze[0] >= 20


def test_nessun_adulto_sotto_il_peso_minimo():
    for sesso, tratti in giocatori(2000, seme=3):
        for eta in (18, 30, 50):
            altezza, peso = descrizioni.fisico(tratti, sesso, eta)
            assert peso / (altezza / 100) ** 2 >= 16.5, (sesso, eta, altezza, peso)
