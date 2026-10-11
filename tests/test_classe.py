"""
Test della classe della tappa 11, da K0 ad A1: i codici, le soglie fisse e il livello, la
percentuale verso la classe seguente, i pesi congelati, i nati fra la J e la E, il peso
dell'esperienza, gli estremi.
"""

import datetime
import random

import pytest
from aiuti_motore import giocatore

import classe
import costanti
from costanti import ATTRIBUTI_ALLENABILI, ATTRIBUTI_BASE_CON_ALLENABILI, CARATTERISTICHE_FISICHE_BASE
from modelli import Giocatore


@pytest.mark.parametrize(("n", "atteso"), [(1, "A1"), (9, "A9"), (10, "B0"), (45, "E5"), (99, "J9"), (100, "K0")])
def test_i_codici(n, atteso):
    assert classe.codice(n) == atteso


def test_le_soglie_sono_cento_e_scendono():
    assert len(classe.SOGLIE_CLASSE) == 100
    assert classe.soglia(1) == 1.0 and classe.soglia(100) == 0.0
    assert all(a > b for a, b in zip(classe.SOGLIE_CLASSE, classe.SOGLIE_CLASSE[1:], strict=False))
    for livello, punteggio in costanti.ANCORE_CLASSE:
        assert classe.soglia(livello) == pytest.approx(punteggio)


# I punteggi esatti di chi fa da ancora, come li ha misurati strumenti/carriera_perfetta.py nella revisione
# della tappa 11: il nato del primo e del novantanovesimo percentile, il bravo dell'utente a 35 anni.
ANCORE_ESATTE = ((89, 0.204776), (50, 0.404708), (30, 0.609318))


@pytest.mark.parametrize(("livello", "punteggio"), ANCORE_ESATTE)
def test_chi_fa_da_ancora_sta_nel_suo_livello(livello, punteggio):
    # Arrotondate al più vicino, le ancore finivano verso l'alto e chi faceva da ancora cadeva un livello più giù.
    assert classe.livello(punteggio) == livello
    # La carriera perfetta più lenta arriva alla somma congelata, quindi ad A1 a 50 anni con 20 di esperienza.
    assert classe.livello(costanti.PESO_VALORE_CLASSE + costanti.PESO_ESPERIENZA_CLASSE) == 1


def test_i_livelli_si_allargano_dal_basso_verso_l_alto():
    # D31: le soglie più fitte dove stanno i giocatori veri, i nati fra I e F, poi i bravi fra E e D, poi le carriere eccellenti.
    passi = [classe.soglia(n - 1) - classe.soglia(n) for n in (70, 40, 15)]
    assert passi[0] < passi[1] < passi[2]


def test_il_livello_di_un_punteggio():
    assert classe.livello(0.0) == 100 and classe.livello(1.0) == 1 and classe.livello(2.5) == 1
    for n in (2, 37, 64, 99):
        assert classe.livello(classe.soglia(n)) == n
        assert classe.livello(classe.soglia(n) - 1e-9) == n + 1


def test_la_percentuale_verso_la_seguente():
    g = giocatore(3, anni=25)
    c = classe.classe(g)
    assert 0 <= c.percentuale <= 99
    assert c.codice == classe.codice(c.livello)
    medio = (classe.soglia(50) + classe.soglia(49)) / 2
    assert classe.percentuale_verso_la_seguente(g, medio) == 50
    assert classe.percentuale_verso_la_seguente(g, 1.3) is None


def test_cambiare_i_pesi_del_valore_non_cambia_la_classe(monkeypatch):
    g = giocatore(4, anni=25)
    prima = classe.classe(g)
    nuovi = {nome: 2 * peso for nome, peso in costanti.PESI_VALORE.items()}
    monkeypatch.setattr(costanti, "PESI_VALORE", nuovi)
    monkeypatch.setattr(classe.valore, "PESI_VALORE", nuovi)
    monkeypatch.setattr(classe.valore, "SCALA_VALORE_A", 0.0)
    assert classe.classe(g) == prima
    assert costanti.PESI_CLASSE is not costanti.PESI_VALORE


def test_mille_nati_fra_la_j_e_la_e():
    random.seed(17)
    nati = [Giocatore(i, datetime.datetime(2026, 1, 1)) for i in range(1, 1001)]
    lettere = [classe.classe(g).codice[0] for g in nati]
    assert set(lettere) <= set("EFGHIJ")
    assert sum(1 for lettera in lettere if lettera in "FGHI") >= 900


def test_il_peso_dell_esperienza_e_il_trenta_per_cento():
    g = giocatore(5, anni=30)
    g.esperienza = 0.0
    senza = classe.punteggio(g)
    g.esperienza = 20.0
    assert classe.punteggio(g) - senza == pytest.approx(0.3)
    g.esperienza = 40.0
    assert classe.punteggio(g) - senza == pytest.approx(0.3)


def test_tutto_al_tetto_e_a1_e_tutto_a_zero_e_k0():
    g = giocatore(6, anni=30, esperienza=20.0)
    for nome in ATTRIBUTI_BASE_CON_ALLENABILI:
        setattr(g, nome, 10.0 if nome in CARATTERISTICHE_FISICHE_BASE else 40.0)
    assert classe.classe(g).codice == "A1" and classe.punteggio(g) > 2.0
    assert classe.classe(g).percentuale is None
    for nome in (*ATTRIBUTI_BASE_CON_ALLENABILI, *ATTRIBUTI_ALLENABILI):
        setattr(g, nome, 0.0)
    g.esperienza = 0.0
    assert classe.classe(g).codice == "K0" and classe.punteggio(g) == 0.0
