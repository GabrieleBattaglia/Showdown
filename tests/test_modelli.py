"""Test della nascita dei giocatori, della gloria richiesta, della probabilità di accettazione e delle polisportive."""

import datetime
import json
import random

import pytest

from costanti import (
    ARCHETIPI_ALLENAMENTO,
    ATTRIBUTI_ALLENABILI,
    ATTRIBUTI_BASE_CON_ALLENABILI,
    CARATTERISTICHE_FISICHE_BASE,
    ETA_MAX_CREAZIONE_GIORNI,
    ETA_MIN_CREAZIONE_GIORNI,
    GLORIA_RICHIESTA_MINIMA_ASSOLUTA,
    MAX_GLORIA_RICHIESTA,
    MAX_PRECISIONE_RESISTENZA,
    MAX_SKILL_VALUE,
    giorni_da_anni,
)
from modelli import Giocatore, Polisportiva, probabilita_accettazione

NASCITA = datetime.datetime(2026, 1, 1)


@pytest.fixture
def giocatori():
    random.seed(20261006)
    return [Giocatore(i, NASCITA) for i in range(1, 61)]


def test_nascita_dentro_i_limiti(giocatori):
    for g in giocatori:
        assert g.sesso in ("m", "f")
        assert ETA_MIN_CREAZIONE_GIORNI <= g.eta <= ETA_MAX_CREAZIONE_GIORNI
        assert g.eta < g.etaritiro and g.eta < g.etamorte
        assert g.nome and g.cognome and g.nome != "*"
        assert g.archetipo_allenamento in ARCHETIPI_ALLENAMENTO
        assert g.descrizione_fisica
        assert not (g.mancino and g.ambidestro)
        for nome_base in ATTRIBUTI_BASE_CON_ALLENABILI:
            tetto = MAX_PRECISIONE_RESISTENZA if nome_base in CARATTERISTICHE_FISICHE_BASE else MAX_SKILL_VALUE
            assert 0 <= getattr(g, nome_base) <= tetto * 0.6
        for nome_allenato in ATTRIBUTI_ALLENABILI:
            assert getattr(g, nome_allenato) == 0.0


def test_indice_di_valore(giocatori):
    for g in giocatori:
        bonus = 33 * sum(bool(getattr(g, f)) for f in ("ambidestro", "giocorapido", "cambiovelocita"))
        somma = sum(getattr(g, a) for a in ATTRIBUTI_BASE_CON_ALLENABILI)
        assert g.indice_collettivo_valore == pytest.approx(somma + bonus)


def test_parametri_alla_nascita():
    random.seed(1)
    g = Giocatore(7, NASCITA, ipovedente="s", eta=1500, attacco_allenata=99, precisione_allenata="3.5", puntiesperienza="12")
    assert g.ipovedente is True
    assert g.eta == 1500
    assert g.attacco_allenata == 20.0
    assert g.precisione_allenata == 3.5
    assert g.puntiesperienza == 12


def _giocatore_neutro(eta_anni, icv):
    random.seed(5)
    g = Giocatore(1, NASCITA)
    g.ambidestro = g.giocorapido = g.cambiovelocita = False
    g.eta = giorni_da_anni(eta_anni)
    g.indice_collettivo_valore = icv
    return g


def test_gloria_richiesta_al_picco():
    assert _giocatore_neutro(17, 100).gloria_richiesta == int(100 * 0.9 * 2.7 + 12)


def test_gloria_richiesta_cala_con_l_eta():
    assert _giocatore_neutro(55, 100).gloria_richiesta == int(100 * 0.9 * 0.1 + 12)
    assert _giocatore_neutro(30, 100).gloria_richiesta < _giocatore_neutro(20, 100).gloria_richiesta


def test_gloria_richiesta_ai_bordi():
    assert _giocatore_neutro(60, 0).gloria_richiesta == max(GLORIA_RICHIESTA_MINIMA_ASSOLUTA, 12)
    assert _giocatore_neutro(17, 10000).gloria_richiesta == MAX_GLORIA_RICHIESTA


def test_probabilita_accettazione():
    assert probabilita_accettazione(100, 100) == pytest.approx(50.0)
    assert probabilita_accettazione(70, 100) == 3.0
    assert probabilita_accettazione(130, 100) == 97.0
    assert probabilita_accettazione(115, 100) == pytest.approx(73.5)
    assert probabilita_accettazione(50, 0) == 97.0


def test_polisportiva_tesserati_e_indice():
    # Il nome resta come lo si scrive, senza spazi in più: decisione D19.
    p = Polisportiva("  prova   di club ", None, NASCITA)
    assert p.nome == "prova di club"
    p.aggiungi_tesserato(3, 120.0)
    p.aggiungi_tesserato(3, 120.0)
    p.aggiungi_tesserato(4, 80.0)
    assert p.tesserati == [3, 4]
    assert p.indicecollettivotesserati == 200.0
    p.rimuovi_tesserato(3, 120.0)
    p.rimuovi_tesserato(99, 50.0)
    assert p.tesserati == [4]
    assert p.indicecollettivotesserati == 80.0


def test_polisportiva_del_computer_senza_password():
    p = Polisportiva("PoliTeam01 abab-cdcd", "segreta", NASCITA, is_cpu_controlled=True)
    assert p.impronta_password is None
    assert not p.protetta


def test_password_conservata_come_impronta():
    p = Polisportiva("Club", "segreta", NASCITA)
    assert p.protetta
    assert "segreta" not in p.impronta_password
    assert not hasattr(p, "password")
    assert p.verifica_password("segreta")
    assert not p.verifica_password("Segreta")
    assert not p.verifica_password("")
    p.imposta_password("nuova")
    assert p.verifica_password("nuova") and not p.verifica_password("segreta")
    p.imposta_password("")
    assert not p.protetta
    assert p.verifica_password("qualunque")


def test_impronte_con_sale_diverso():
    from utilita import crea_impronta, verifica_impronta
    prima, seconda = crea_impronta("uguale"), crea_impronta("uguale")
    assert prima != seconda
    assert verifica_impronta("uguale", prima) and verifica_impronta("uguale", seconda)
    assert not verifica_impronta("uguale", "rotta")
    assert not verifica_impronta("uguale", None)
    assert not verifica_impronta("uguale", prima.replace("pbkdf2_sha256", "md5"))


def test_giocatore_da_e_verso_il_dizionario(giocatori):
    for g in giocatori:
        dati = json.loads(json.dumps(g.a_dizionario()))
        assert "indice_collettivo_valore" not in dati and "descrizione_fisica" not in dati
        assert vars(Giocatore.da_dizionario(dati)) == vars(g)


def test_giocatore_senza_tratti_salva_il_suo_aspetto():
    random.seed(2)
    g = Giocatore(9, NASCITA, descrizione_fisica="Ha un viso tondo.", altezza=170, peso=65)
    assert not hasattr(g, "tratti")
    dati = json.loads(json.dumps(g.a_dizionario()))
    assert (dati["altezza"], dati["peso"], dati["descrizione_fisica"]) == (170, 65, "Ha un viso tondo.")
    assert vars(Giocatore.da_dizionario(dati)) == vars(g)


@pytest.mark.parametrize(("campo", "valore"), [("eta", "dieci"), ("puntiesperienza", True), ("mancino", 1), ("forza_base", None), ("datacreazione_reale", "ieri")])
def test_giocatore_con_un_campo_non_valido(giocatori, campo, valore):
    dati = giocatori[0].a_dizionario()
    dati[campo] = valore
    with pytest.raises(ValueError, match=campo):
        Giocatore.da_dizionario(dati)


def test_giocatore_con_un_campo_mancante(giocatori):
    dati = giocatori[0].a_dizionario()
    del dati["cognome"]
    with pytest.raises(ValueError, match="manca il campo cognome"):
        Giocatore.da_dizionario(dati)


def test_polisportiva_da_e_verso_il_dizionario():
    p = Polisportiva("Club", "segreta", NASCITA)
    p.aggiungi_tesserato(4, 80.0)
    dati = json.loads(json.dumps(p.a_dizionario()))
    ricostruita = Polisportiva.da_dizionario(dati)
    assert ricostruita.tesserati == [4]
    assert ricostruita.indicecollettivotesserati == 0.0
    assert ricostruita.verifica_password("segreta")
    ricostruita.indicecollettivotesserati = 80.0
    assert vars(ricostruita) == vars(p)
    dati["tesserati"] = [4, "cinque"]
    with pytest.raises(ValueError, match="tesserati"):
        Polisportiva.da_dizionario(dati)


def test_eta_della_polisportiva():
    p = Polisportiva("Club", None, NASCITA)
    assert p.eta_sim(NASCITA + datetime.timedelta(days=110)) == "1/0/2 sim"
    assert p.eta_sim(None) == "Età N/D"
