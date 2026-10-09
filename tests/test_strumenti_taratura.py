"""
Test dei conti della taratura del valore, strumenti/taratura_valore.py, quasi senza giocare
partite: i minimi quadrati con i pesi non negativi, la prima stima della scala che conserva
mediana e monte stipendi, le coppie speculari di colpi e battute che hanno un peso solo, e la
ricerca della scala vera per bisezione di strumenti/simulazione_lunga.py, con una simulazione
finta. Dalla revisione di D26: la resistenza ha un prezzo solo, la verifica a coppie somma più
gruppi con poche partite, e la sonda della stanchezza del banco misura soltanto giocatori che
possono esistere. Dalla tappa 11 le parti pure del giro degli estremi del motore: la resa di un
tratto e i verdetti dei bersagli.
"""

import hashlib
import math
import random
import statistics
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import banco_estremi as be
import banco_partite as bp
import popolazione_di_prova as pp
import simulazione_lunga as sl
import taratura_valore as tv
from aiuti_motore import giocatore

import costanti


def test_minimi_quadrati_ritrova_i_coefficienti_e_azzera_i_negativi():
    rng = random.Random(1)
    righe, y = [], []
    for _ in range(300):
        a, b, c = rng.uniform(0, 10), rng.uniform(0, 10), rng.uniform(0, 10)
        righe.append([a, b, c, 1.0])
        y.append(2.0 * a + 0.5 * b - 1.5 * c + 3.0 + rng.gauss(0, 0.01))
    coefficienti, escluse = tv.minimi_quadrati(righe, y, vincolate=frozenset((0, 1)))
    assert coefficienti[:2] == pytest.approx([2.0, 0.5], abs=0.01)
    assert coefficienti[2] == pytest.approx(-1.5, abs=0.01) and not escluse
    coefficienti, escluse = tv.minimi_quadrati(righe, y, vincolate=frozenset((0, 1, 2)))
    assert escluse == [2] and coefficienti[2] == 0.0 and coefficienti[0] > 0


def test_le_coppie_speculari_hanno_una_colonna_sola():
    coppie = [gruppo for gruppo in tv.GRUPPI if len(gruppo) == 2]
    assert ("lungolineasx", "lungolineadx") in coppie and ("battutasx", "battutadx") in coppie
    assert len(coppie) == 6
    nomi = [nome for gruppo in tv.GRUPPI for nome in gruppo]
    assert sorted(nomi) == sorted(costanti.CARATTERISTICHE_VALORE)


def test_la_scala_conserva_mediana_e_monte_stipendi(monkeypatch):
    rng = random.Random(2)
    vecchi = [rng.gauss(137.0, 15.0) + (33.0 if rng.random() < 0.3 else 0.0) for _ in range(2000)]
    somme = [v * 0.5 + rng.gauss(0, 3) for v in vecchi]
    giocatori = list(range(len(vecchi)))

    def indice_finto(g, pesi, _tratti, a, b):
        valore_grezzo = vecchi[g] if pesi is tv.PESI_TAPPA_8 else somme[g]
        return a + b * valore_grezzo

    monkeypatch.setattr(tv.valore, "indice", indice_finto)
    a, b = tv.scala(giocatori, {}, {})
    nuovi = [a + b * s for s in somme]
    assert statistics.median(nuovi) == pytest.approx(statistics.median(vecchi))
    assert statistics.fmean(tv.fattore_stipendio(v) for v in nuovi) == pytest.approx(statistics.fmean(tv.fattore_stipendio(v) for v in vecchi), rel=1e-6)
    assert tv.fattore_stipendio(costanti.VALORE_DI_RIFERIMENTO) == 1.0
    assert math.isfinite(a) and b > 0


def _campione(seme):
    """Un campione finto: somme dei giocatori in attività attorno a 160, i tesserati senza tratti e senza esperienza."""
    rng = random.Random(seme)
    somme = [rng.gauss(160.0, 25.0) for _ in range(3000)]
    return somme, [(s, 1.0) for s in somme[300:]]


def test_la_scala_in_forma_chiusa():
    # Tappa 11, punto 12.4: A tiene la mediana del valore a 135,5, B porta lo stipendio al decimo percentile dei tesserati a 105.
    campioni = [_campione(1), _campione(2)]
    a, b = sl.scala_in_forma_chiusa(campioni)
    somme = [s for attivi, _t in campioni for s in attivi]
    assert a + b * statistics.median(somme) == pytest.approx(135.5)
    stipendi = [sl._stipendio(a + b * s, m) for _a, tesserati in campioni for s, m in tesserati]
    assert abs(sl.percentile(stipendi, 0.1) - 105.0) <= 10.0
    assert b > 0


def _misure_finte(a, b, sponsor):
    # Una simulazione finta: la cassa mediana cresce con lo sponsor; il campione non dipende dalla scala.
    somme, tesserati = _campione(3)
    return {"casse": (0.0, 5000.0 * sponsor / 20.0, 0.0), "stipendi": (105.0, 210.0, 560.0), "monte_su_sponsor": 0.92, "tesserati": 90, "attivi": 100,
            "mediana_valore": a + b * statistics.median(somme), "somme_attivi": somme, "tesserati_campione": tesserati}


def test_l_economia_si_cerca_con_la_scala_e_poi_lo_sponsor(monkeypatch):
    monkeypatch.setattr(sl, "con_scala", lambda _anni, semi, a, b, _processi, sponsor: {s: _misure_finte(a, b, sponsor) for s in semi})
    a, b, sponsor, righe = sl.cerca_economia(10, (1, 2), 5000.0, 1, giri=3, passi=20, stampa=None, sponsor_iniziale=18.0)
    assert sponsor == pytest.approx(20.0, abs=0.01)
    assert (a, b) == pytest.approx(sl.scala_in_forma_chiusa([_campione(3), _campione(3)]))
    assert righe[-1].startswith("L'economia trovata, da copiare in costanti.py")
    assert sl.PESI_TAPPA_8 is tv.PESI_TAPPA_8


def test_la_resistenza_ha_un_prezzo_solo_comunque_sia_divisa():
    # Revisione di D26: la resistenza entra nella regressione col totale, innata o allenata che
    # sia; quanto rende in più la parte allenata, come abitudine ad allenarsi, lo dice la verifica
    # a coppie, perché nelle popolazioni di prova la regressione non sa separarla.
    innato = giocatore(1, anni=27, resistenza_base=3.0, resistenza_allenata=0.0)
    allenato = giocatore(1, anni=27, resistenza_base=1.0, resistenza_allenata=2.0)
    assert tv.regressori(innato) == tv.regressori(allenato)
    assert "allenamento" not in tv.COLONNE and tv.COLONNE.count("resistenza") == 1


def test_la_verifica_a_coppie_somma_i_gruppi_e_da_il_mancino_per_seme():
    soggetti = [giocatore(10 + i, valore=10.0 + 4 * i) for i in range(2)]
    avversari = [giocatore(100 + i, valore=12.0) for i in range(2)]
    altri = [giocatore(20 + i, valore=14.0 + 4 * i) for i in range(2)]
    righe = tv.verifica_a_coppie([(soggetti, avversari, 1), (altri, avversari, 2)], costanti.PESI_VALORE, costanti.PESI_TRATTI,
                                 costanti.SCALA_VALORE_A, costanti.SCALA_VALORE_B)
    assert righe[0].startswith("Quinto passo, la verifica a coppie: 4 soggetti destrimani in 2 gruppi")
    assert len(righe) == 2 + len(tv.VERIFICHE)
    assert righe[-1].startswith("Il mancino gruppo per gruppo")


def _lotti(fatti, subiti, somma):
    return [{"fatti": fatti, "subiti": subiti, "vinte": 0, "giocate": 1, "somma": somma, "soggetti": 1} for _l in range(be.LOTTI)]


def test_la_resa_di_un_tratto_del_giro_degli_estremi():
    # La resa è il rating guadagnato per punto di somma pesata, e il suo errore viene dai lotti; nessuna resa se la somma non cresce.
    prima = _lotti(1000, 1000, 150.0)
    dopo = _lotti(1100, 1000, 160.0)
    dopo[0]["fatti"] = 1200
    resa, errore = be.resa_di_un_tratto(prima, dopo)
    assert resa == pytest.approx(math.log(sum(x["fatti"] for x in dopo) / sum(x["subiti"] for x in dopo)) / 10.0)
    assert 0.0 < errore < resa
    assert be.resa_di_un_tratto(prima, _lotti(1100, 1000, 150.0)) is None
    rese = be.rese_della_prova(prima, [dopo, _lotti(1300, 1000, 170.0)])
    assert len(rese) == 2 and rese[1][0] > 0


def test_i_verdetti_del_giro_degli_estremi():
    # Troppo sopra 1,5 volte la resa di riferimento oltre il 30 per cento, incerto con l'errore grande,
    # scende se il rating cala oltre il rumore, satura sotto metà; il primo tratto non è mai troppo.
    rif = 0.01
    rese = [(0.03, 0.001), (0.03, 0.001), (0.03, 0.005), (-0.01, 0.001), (0.002, 0.001), (0.01, 0.001), None]
    giudizi = dict(be.verdetto_dei_tratti(rese, rif))
    assert 0.30 not in giudizi
    assert giudizi[0.45] == "troppo" and giudizi[0.60] == "troppo, ma incerto" and giudizi[0.70] == "scende" and giudizi[0.80] == "satura"
    assert 0.90 not in giudizi and 1.00 not in giudizi
    assert dict(be.verdetto_dei_tratti([(0.01, 0.003), *[(0.01, 0.0001)] * 6], rif)) == {0.30: "incerto"}
    gemelli = {"attacchi_per_punto": 4.5}
    buono = {"attacchi_per_punto": 7.0, "punti_per_set": 11.5, "falli_per_punto": 0.4, "limite_tecnico": 0}
    assert all(dentro for _frase, dentro in be.verdetto_dei_campioni(buono, gemelli))
    cattivo = {"attacchi_per_punto": 10.0, "punti_per_set": 9.0, "falli_per_punto": 0.1, "limite_tecnico": 2}
    assert not any(dentro for _frase, dentro in be.verdetto_dei_campioni(cattivo, gemelli))


def test_le_prove_del_giro_degli_estremi(monkeypatch):
    # Ventiquattro caratteristiche da sole, le otto coppie di lato, tutti i colpi insieme e tutto; i
    # sedici gruppi della taratura del valore coprono ogni caratteristica una volta; portare a un
    # livello non toglie mai l'allenata che c'è già.
    prove = be.prove()
    assert len(prove) == 24 + 8 + 2 and prove[-1][0] == "tutto"
    nomi = sorted(c for gruppo in be.GRUPPI.values() for c in gruppo)
    assert len(be.GRUPPI) == 16 and nomi == sorted(c[:-9] for c in costanti.ATTRIBUTI_ALLENABILI)
    assert {nomi for _nome, nomi in be.scelte("colpi")} >= {(c,) for c in be.COLPI}
    g = giocatore(1, triplaspondasx_base=6.0, triplaspondasx_allenata=10.0)
    assert be.portato(g, ("triplaspondasx",), 0.7).triplaspondasx_allenata == pytest.approx(22.0)
    assert be.portato(g, ("triplaspondasx",), 0.3).triplaspondasx_allenata == 10.0 and g.triplaspondasx_allenata == 10.0
    monkeypatch.setattr(be, "NATI", 600)
    soggetti, avversari, (basso, alto) = be.soggetti_e_avversari(4, 6, 5)
    assert len(soggetti) == 4 and len(avversari) == 6 and basso < alto
    assert all(be.senza_tratti(g) and basso <= be.valore.somma_pesata(g) <= alto for g in soggetti + avversari)
    be.prepara(soggetti, avversari, 8, 5, be.TARATURA)
    lotti, esiti = be.gioca_prova(("triplaspondasx",), 1.0)
    assert sum(lotto["giocate"] for lotto in lotti) == 8 and esiti["incontri"] == 8
    assert be.misure_esiti(esiti)["punti_per_set"] > 0


def test_la_sonda_della_stanchezza_misura_giocatori_possibili():
    # La resistenza innata nasce fra 0 e il 60 per cento del suo vecchio massimo, cioè 3, e non
    # cresce; dalla tappa 11 il totale arriva al tetto di 10, e la costanza va da 0 alla costanza
    # piena. Un giovane con 5 di innata, o un trentenne con 5 senza allenarsi, nel mondo non esistono.
    innata_massima = costanti.MAX_PRECISIONE_RESISTENZA * 0.6
    for descrizione, _anni, innata, allenata, costanza, _dove, _intervallo in bp.CASI_FATICA:
        assert 0.0 <= innata <= innata_massima, descrizione
        assert allenata >= 0.0 and innata + allenata <= costanti.MAX_TOTALE_PRECISIONE_RESISTENZA, descrizione
        assert 0.0 <= costanza <= costanti.COSTANZA_PIENA, descrizione
    assert any(innata + allenata == costanti.MAX_TOTALE_PRECISIONE_RESISTENZA for _d, _a, innata, allenata, *_resto in bp.CASI_FATICA)


# Le impronte delle caratteristiche di due popolazioni di prova, prese con il codice della versione
# 1.50.0, prima della tappa 11: 400 giocatori col seme 9 e 300 col seme 19 dal numero 500001.
IMPRONTE_DELLA_1_50 = {(400, 9): "30b1f475249eb057d4d2e7fb82c691e0fdd6cf0d32bf40666f7983b83b76b971",
                       (300, 19): "91a99f5d97f0b14fc53496c49816faec9913f7292686336794dd2b7f96d44bfa"}


def _impronta(giocatori):
    righe = []
    for g in giocatori:
        valori = [round(getattr(g, n), 9) for n in costanti.ATTRIBUTI_INVECCHIABILI]
        righe.append(f"{g.id}:{g.sesso}:{g.eta}:{g.mancino}:{g.ambidestro}:{g.ipovedente}:{g.giocorapido}:{g.cambiovelocita}:{round(g.esperienza, 6)}:{valori}")
    return hashlib.sha256("\n".join(righe).encode()).hexdigest()


def test_la_popolazione_di_prova_resta_quella_della_1_50_salvo_la_costanza():
    # Tappa 11, risposta 6: senza i tetti dell'allenata nel gioco, la popolazione tiene le sue bande, e
    # la regressione del valore resta sulla stessa popolazione; la costanza viene da un generatore a parte.
    for (quanti, seme), impronta in IMPRONTE_DELLA_1_50.items():
        giocatori = pp.genera(quanti, seme, primo_id=1 if seme == 9 else 500_001)
        assert _impronta(giocatori) == impronta
        assert all(0.0 <= g.costanza <= costanti.COSTANZA_PIENA for g in giocatori)
        assert max(g.costanza for g in giocatori) > 1.5
        for g in giocatori:
            for nome in costanti.ATTRIBUTI_ALLENABILI:
                banda = pp.BANDA_ALLENATA_FISICA if nome in costanti.ALLENATE_FISICHE else pp.BANDA_ALLENATA_GIOCO
                assert getattr(g, nome) <= banda
    assert (pp.BANDA_ALLENATA_FISICA, pp.BANDA_ALLENATA_GIOCO) == (5.0, 20.0)
