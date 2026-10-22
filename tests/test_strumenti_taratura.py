"""
Test dei conti della taratura del valore, strumenti/taratura_valore.py, quasi senza giocare
partite: i minimi quadrati con i pesi non negativi, la prima stima della scala che conserva
mediana e monte stipendi, le coppie speculari di colpi e battute che hanno un peso solo, e la
ricerca della scala vera per bisezione di strumenti/simulazione_lunga.py, con una simulazione
finta. Dalla revisione di D26: la resistenza ha un prezzo solo, la verifica a coppie somma più
gruppi con poche partite, e la sonda della stanchezza del banco misura soltanto giocatori che
possono esistere. Dalla tappa 11: la costanza nella popolazione di prova e nella regressione, le
parti pure del giro degli estremi del motore, cioè la resa di un tratto e i verdetti dei bersagli, e
il controllo di solvibilità della prova lunga. Dalla revisione della tappa 11: le fasce del
favorito del banco con la scala ferma della 1.50.0, e l'oblio dell'apprendista nei mondi sintetici
della carriera perfetta, che scatta a ogni mese come nel mondo vero.
"""

import datetime
import hashlib
import math
import random
import statistics
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))

import banco_estremi as be
import banco_partite as bp
import carriera_perfetta as cp
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


def test_la_costanza_e_un_controllo_e_si_verifica_a_coppie():
    # Tappa 11, punto 12.2: la costanza recente entra fra i regressori di controllo, e la verifica a
    # coppie la misura piena contro zero, al posto del punto di resistenza allenata.
    assert "costanza" in tv.CONTROLLI and "costanza" in tv.COLONNE
    fermo = giocatore(1, costanza=0.0)
    costante = giocatore(1, costanza=costanti.COSTANZA_PIENA)
    assert tv.regressori(costante)[tv.COLONNE.index("costanza")] == 1.0 and tv.regressori(fermo)[tv.COLONNE.index("costanza")] == 0.0
    assert tv.modificato(fermo, "costanza").costanza == costanti.COSTANZA_PIENA and tv.modificato(costante, "costanza_zero").costanza == 0.0
    assert [nome for nome, _m in tv.VERIFICHE].count("la costanza piena contro la costanza zero") == 1
    assert not any("resistenza allenata" in nome for nome, _m in tv.VERIFICHE)


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


def test_il_controllo_di_solvibilita_della_prova_lunga():
    anni = [{"numero_anno": 1, "tesserati": 90, "attivi": 100, "casse": (0, 5000, 0)}, {"numero_anno": 2, "tesserati": 80, "attivi": 100, "casse": (0, 5000, 0)},
            {"numero_anno": 3, "tesserati": 90, "attivi": 100, "casse": (0, 1500, 0)}, {"numero_anno": 4, "tesserati": 90, "attivi": 100, "casse": (0, 16000, 0)}]
    assert [anno for anno, _t, _c in sl.fuori_dalla_solvibilita(anni)] == [2, 3, 4]


def test_la_prova_lunga_controlla_i_primi_100_tesserati():
    # La decisione 1 di Gabriele del 14 ottobre 2026: il computer tessera i campioni, e la prova lunga
    # vuole i primi 100 del mondo per valore tesserati almeno all'80 per cento in tutti gli anni.
    annuali = [{"numero_anno": n, "tesserati": 90, "attivi": 100, "primi_100": primi} for n, primi in ((1, 95.0), (2, 79.0), (3, 81.0), (4, 60.0))]
    righe = sl.controlli_della_tappa_12(4, [7], {7: (annuali, [])})
    assert "primi 100 tesserati sotto l'80 per cento in 2 anni, dall'anno 2 all'anno 4" in righe[-1]
    for m in annuali:
        m["primi_100"] = 80.0
    assert sl.controlli_della_tappa_12(4, [7], {7: (annuali, [])})[-1].endswith("tutti dentro.")


def test_i_controlli_della_verifica_nella_prova_lunga():
    # La verifica del 15 ottobre 2026: i primi 10 e 20 tesserati, la soglia del mondiale del mondo
    # contro quella della carriera perfetta, la cassa mediana del computer che non corre a regime: dal 21
    # ottobre 2026 la banda è di 3.000 euro l'anno, scelta di Gabriele che lascia crescere la cassa.
    soglia = costanti.PUNTI_PER_IL_MONDIALE
    annuali = [{"numero_anno": n, "primi_10": 9 if n < 30 else 6, "primi_20": 18, "soglia_mondiale": {"m": soglia["m"] + 40, "f": soglia["f"] - 5},
                "casse": (0, 10_000 + 4_000 * max(0, n - 45), 0)} for n in range(1, 61)]
    fuori = sl.fuori_dai_controlli_della_verifica(annuali)
    assert fuori[0] == "dei primi 10 tesserati meno di 8 in 31 anni, dall'anno 30 all'anno 60, al più basso 6"
    assert fuori[1].startswith("soglia del mondiale per gli uomini dall'anno 40 al 60 in media ") and len(fuori) == 3
    assert fuori[2].startswith("cassa mediana del computer che cresce di 4000 euro l'anno dall'anno 45 al 60")
    for m in annuali:
        m["primi_10"], m["soglia_mondiale"], m["casse"] = 8, dict(soglia), (0, 9_000 + 2_500 * max(0, m["numero_anno"] - 45), 0)
    assert sl.fuori_dai_controlli_della_verifica(annuali) == []
    # Le misure di prima, senza le chiavi nuove, passano senza i controlli nuovi.
    assert sl.fuori_dai_controlli_della_verifica([{"numero_anno": 50, "primi_100": 90.0, "casse": (0, 5000, 0)}]) == []


def test_i_bersagli_dello_staff_nella_prova_lunga():
    # La tappa 13, progetto 6.3 e risposta 32: il capo al 95 per cento e i liberi almeno quanti i club senza
    # capo dall'anno 20, lo staff entro un quinto del monte; i numeri per decennio stanno in una riga a parte.
    # Prima dell'anno 20 il mondo giovane non conta.
    annuali = [{"numero_anno": n, "con_capo": 90.0 if n < 23 else 97.0, "senza_capo": 3, "staff_pieno": 20.0, "qualita_staff": (0.3, 0.5, 0.7),
                "staff_sul_monte": 25.0 if n == 30 else 6.0, "allenatori": 900, "allenatori_liberi": 2 if n in (12, 25) else 40,
                "liberi_per_lettera": {"C": 3, "H": 37}} for n in range(1, 41)]
    righe = sl.controlli_della_tappa_13(40, [7], {7: annuali})
    assert righe[0].startswith("Seme 7, lo staff per decennio: anno 10, con un capo 90,0 per cento, staff pieno 20,0, qualità 0,30, 0,50 e 0,70, ")
    assert "allenatori 900, liberi 40 (C 3, H 37)" in righe[0]
    assert righe[1] == ("Seme 7, i bersagli dello staff della tappa 13: FUORI polisportive con un capo sotto il 95 per cento in 3 anni, dall'anno 20 "
                        "all'anno 22, al più basso 90,0; allenatori liberi meno delle polisportive senza capo in 1 anni, dall'anno 25 all'anno 25; "
                        "staff oltre il 20 per cento del monte in 1 anni, dall'anno 30 all'anno 30.")
    for m in annuali:
        m["con_capo"], m["allenatori_liberi"], m["staff_sul_monte"] = 96.0, 40, 6.0
    assert sl.controlli_della_tappa_13(40, [7], {7: annuali})[1].endswith("tutti dentro.")
    # Le misure di prima, senza lo staff, non danno righe.
    assert sl.controlli_della_tappa_13(40, [7], {7: [{"numero_anno": 10}]}) == []


def test_lo_scenario_dell_utente_spende_con_la_regola_della_1_60_11():
    # La verifica del 15 ottobre 2026: la polisportiva dell'utente nasce coi 20.000 euro del capitale,
    # sopra la soglia della cassa piena, e la regola del computer della decisione 1 le avrebbe dato il
    # premio; la decisione 2 vuole la partenza com'era, lo sponsor più un ventiquattresimo della cassa.
    import economia

    for sponsor, cassa in ((1500, 18_500), (1500, 13_000), (900, 5_000)):
        assert sl.spesa_mensile_utente(sponsor, cassa) == sponsor + cassa / costanti.PARTI_DI_CASSA_PER_STIPENDI
    differenza = economia.spesa_mensile_cpu(1500, 18_500) - sl.spesa_mensile_utente(1500, 18_500)
    assert differenza == pytest.approx((18_500 - costanti.SOGLIA_CASSA_PIENA_CPU) / costanti.MESI_CASSA_PIENA_CPU) and differenza > 1000


def test_la_simulazione_salva_il_mondo_alla_fine(tmp_path, monkeypatch):
    # Con salva la simulazione scrive il mondo e lo stato del caso, per misurare il giorno a regime;
    # il mondo riletto ha gli stessi giocatori, e il caso di chi chiama resta com'era.
    import ast

    import archivio
    import percorsi
    from mondo import Mondo

    file = tmp_path / "mondi" / "lunga_5_anno_0.json.gz"
    stato = random.getstate()
    mondo, _righe = sl.simula(seme=5, giorni=2, stampa=None, misura_ogni_anno=False, salva=file)
    assert random.getstate() == stato
    monkeypatch.setattr(percorsi, "cartella", lambda: str(tmp_path))
    riletto = Mondo()
    archivio.costruisci(archivio.leggi(str(file)), riletto)
    assert set(riletto.giocatori) == set(mondo.giocatori) and riletto.datetime_corrente_simulazione == mondo.datetime_corrente_simulazione
    # Le misure nuove della verifica del 15 ottobre 2026: i primi 10 e 20 tesserati e la soglia del mondiale.
    m = sl.misure(mondo)
    assert 0 <= m["primi_10"] <= 10 and m["primi_10"] <= m["primi_20"] <= 20 and set(m["soglia_mondiale"]) == {"m", "f"}
    caso = ast.literal_eval((tmp_path / "mondi" / "lunga_5_anno_0.caso").read_text(encoding="utf-8"))
    assert isinstance(caso, tuple) and caso != stato


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


def test_le_fasce_del_favorito_non_seguono_la_scala_dell_economia(monkeypatch):
    """
    Il distacco del favorito del banco della tappa 9 si misura con la scala ferma della 1.50.0: se
    l'economia ritocca la scala del valore, l'indice cambia ma il distacco no, e le partite restano
    nella loro fascia. Così il prima e il dopo di una taratura si confrontano sulla stessa misura.
    """
    import valore
    forte, debole = giocatore(1, valore=16.0), giocatore(2, valore=12.0)
    distacco = bp.distacco(bp.indice_del_distacco(forte), bp.indice_del_distacco(debole))
    assert bp.indice_del_distacco(forte) == pytest.approx(valore.indice(forte, a=-82.61, b=1.3878))
    monkeypatch.setattr(valore, "SCALA_VALORE_A", -10.0)
    monkeypatch.setattr(valore, "SCALA_VALORE_B", 0.9)
    assert bp.distacco(bp.indice_del_distacco(forte), bp.indice_del_distacco(debole)) == pytest.approx(distacco)
    assert bp.distacco(valore.indice(forte), valore.indice(debole)) != pytest.approx(distacco)


def test_l_oblio_dei_mondi_sintetici_scatta_ogni_mese():
    """Un passo d'un anno dei mondi sintetici fa dimenticare all'apprendista quanto i tre mesi e mezzo del mondo vero, non un mese solo."""
    g = giocatore(31, valore=10.0, fisico=2.5, anni=30, talento=False, maturazione=None, apprendista_rapido=True)
    g.attacco_allenata = 10.0
    cp.allena_a_passi(g, 30.0, 31.0, 0.0, "completa")
    mesi = costanti.ANNO_SIMULAZIONE_GIORNI / costanti.GIORNI_PER_MESE
    oblio = costanti.TRATTI_ALLENAMENTO["apprendista_rapido"]["oblio_mensile"]
    assert g.attacco_allenata == pytest.approx(10.0 * oblio ** mesi)
    assert mesi > 3.5


def test_la_resa_di_riferimento_vuole_tutti_i_sedici_gruppi():
    """Con le sole battute e i colpi la media del primo tratto era un'altra, e le rese relative più alte di un terzo."""
    assert be.gruppi_mancanti(be.scelte("tutte")) == []
    assert "precisione" in be.gruppi_mancanti(be.scelte("colpi"))
    rese = {nomi: [(0.01, 0.001)] for nomi in be.GRUPPI.values()}
    assert be.resa_di_riferimento(rese) == pytest.approx(0.01)
    del rese[be.GRUPPI["precisione"]]
    with pytest.raises(ValueError, match="precisione"):
        be.resa_di_riferimento(rese)


def test_la_sonda_dell_acciacco_tiene_la_proporzione_delle_prime_stime():
    # Tappa 12, punto 13.1: ogni giocatore contro il gemello, con e senza calo; il minimo e il massimo trovati stanno nella proporzione di 0,012 e 0,028.
    giocatori = [g for g in pp.genera(40, 5) if g.puo_giocare]
    righe, (minimo, massimo) = bp.sonda_acciacco(giocatori, 12, 4, random.Random(3), {})
    assert righe[0].startswith("Sonda dell'acciacco: 12 incontri") and "ACCIACCO_CALO_MINIMO" in righe[-1]
    assert minimo > 0 and massimo / minimo == pytest.approx(0.028 / 0.012, rel=0.01)


def test_la_gloria_in_forma_chiusa():
    # Tappa 12, punto 13.4: i coefficienti del palmarès portano la quota mediana al 50 per cento e il primo
    # decimo il più vicino possibile al 65; il fattore della gloria richiesta dà il rapporto chiesto.
    rng = random.Random(8)
    club = []
    for i in range(400):
        coppe = 30.0 if i % 10 == 0 else rng.uniform(0.0, 3.0)
        club.append((rng.uniform(120.0, 150.0), rng.uniform(5.0, 40.0), coppe))
    richieste = [rng.uniform(150.0, 350.0) for _ in range(300)]
    k_medaglie, k_coppe, fattore, (mediana, decimo) = sl.gloria_in_forma_chiusa([(club, richieste)], rapporto=1.5)
    assert mediana == pytest.approx(50.0, abs=1.0) and k_medaglie > 0 and k_coppe >= 0
    assert decimo == pytest.approx(65.0, abs=6.0)
    glorie = [resto + k_medaglie * rm + k_coppe * rc for resto, rm, rc in club]
    assert fattore * statistics.median(richieste) / statistics.median(glorie) == pytest.approx(1.5)


def test_i_fattori_e_le_esperienze_della_carriera_perfetta():
    # Tappa 12, punto 10.4: la parte delle partite si divide nelle proporzioni 40, 34 e 4 di D32, e
    # l'esperienza fonte per fonte, dalla decisione 8 di Gabriele del 14 ottobre 2026, dà 2,5, 3, 4,5 e
    # 8, coi tornei divisi 50, 20 e 30.
    grezzi = {"torneo": 1500.0, "amichevole": 14000.0, "sfida": 800.0}
    fattori = cp.fattori_per_totale(20_000.0, 4428.0, grezzi)
    parti = {fonte: fattori[fonte] * grezzi[fonte] for fonte in grezzi}
    assert sum(parti.values()) == pytest.approx(20_000.0 - 4428.0)
    assert parti["torneo"] / parti["amichevole"] == pytest.approx(40 / 34) and parti["sfida"] / parti["amichevole"] == pytest.approx(4 / 34)
    conteggi = {"amichevoli": 3500.0, "sfide": 300.0, "giorni": 4649.4, "incontri_torneo": 600.0, "fasi": 150.0, "piazzamenti": 60.0}
    esperienze = cp.esperienze_dai_conteggi(conteggi)
    assert esperienze["amichevoli"] * conteggi["amichevoli"] == pytest.approx(2.5) and esperienze["sfide"] * conteggi["sfide"] == pytest.approx(3.0)
    assert esperienze["club"] * conteggi["giorni"] == pytest.approx(4.5)
    assert sum(esperienze[v] * conteggi[v] for v in ("incontri_torneo", "fasi", "piazzamenti")) == pytest.approx(8.0)
    assert esperienze["fasi"] * conteggi["fasi"] == pytest.approx(8.0 * 0.2)


def test_l_ordine_delle_fonti_d_esperienza():
    # La decisione 8 di Gabriele del 14 ottobre 2026: dalla fonte più piccola alla più grande, età,
    # amichevoli, sfide, club e tornei, sempre 20 a 50 anni. L'età dai 9 ai 50 anni fa circa 2 da sé.
    eta = costanti.ESPERIENZA_PER_ANNO_DI_VITA * (cp.ETA_USCITA - cp.ETA_INGRESSO)
    fonti = (eta, cp.ESPERIENZA_AMICHEVOLI, cp.ESPERIENZA_SFIDE, cp.ESPERIENZA_CLUB, cp.ESPERIENZA_TORNEI)
    assert list(fonti) == sorted(fonti) and len(set(fonti)) == len(fonti)
    assert sum(fonti) == pytest.approx(costanti.ESPERIENZA_MASSIMA, abs=0.1)


@pytest.fixture
def classe_ripristinata(monkeypatch):
    """La somma, le ancore e le soglie della classe tornano quelle di prima alla fine della prova, anche se lo strumento le cambia."""
    import classe

    for modulo, nome in ((costanti, "SOMMA_CARRIERA_PERFETTA"), (costanti, "ANCORE_CLASSE"), (classe, "SOMMA_CARRIERA_PERFETTA"), (classe, "SOGLIE_CLASSE"),
                         (classe, "_SOGLIE_CRESCENTI")):
        monkeypatch.setattr(modulo, nome, getattr(modulo, nome))
    return classe


def test_il_ricalcolo_della_classe_si_fa_una_volta_e_converte(classe_ripristinata, monkeypatch):
    # La decisione 7 di Gabriele del 14 ottobre 2026: la somma e le ancore della tappa 11 si convertono
    # ai pesi nuovi della classe una volta sola, poi tornano congelate.
    classe = classe_ripristinata
    assert set(cp.PESI_CLASSE_PRIMA) == set(costanti.PESI_CLASSE) and set(cp.PESI_TRATTI_CLASSE_PRIMA) == set(costanti.PESI_TRATTI_CLASSE)
    # Il ricalcolo del 15 ottobre 2026 è già in costanti.py, e un altro si rifiuta; la prova rimette la
    # classe della tappa 11 nel processo per provare la conversione.
    assert cp.PESI_CLASSE_PRIMA["battutasx"] == 0.71 and not cp.classe_da_ricalcolare()
    with pytest.raises(SystemExit, match="già stata ricalcolata"):
        cp.ricalcola_classe(types.SimpleNamespace(), print)
    cp.imposta_classe(cp.SOMMA_CARRIERA_PERFETTA_PRIMA, cp.ANCORE_CLASSE_PRIMA)
    assert cp.classe_da_ricalcolare()
    # La somma: quella di prima per il rapporto medio, per difetto al decimo.
    carriere = [{"somma_50": 330.0, "somma_50_prima": 300.0}, {"somma_50": 230.0, "somma_50_prima": 200.0}]
    somma, rapporti = cp.somma_convertita(carriere)
    assert rapporti == pytest.approx([1.1, 1.15]) and somma == math.floor(cp.SOMMA_CARRIERA_PERFETTA_PRIMA * 1.125 * 10) / 10
    # Le ancore: tutte per definizione, anche il bravo col suo caso tipico, dalla verifica del 15 ottobre 2026.
    nati = cp.nati(300, 11)
    bravo = giocatore(5, valore=12.0, anni=35, esperienza=9.0)
    ancore, esatti = cp.ancore_ricalcolate(somma, nati, bravo)
    somme = sorted(classe.somma_classe(g) for g in nati)
    assert esatti[89] == pytest.approx(costanti.PESO_VALORE_CLASSE * somme[3] / somma)
    assert esatti[50] == pytest.approx(costanti.PESO_VALORE_CLASSE * somme[297] / somma)
    assert esatti[30] == pytest.approx(costanti.PESO_VALORE_CLASSE * classe.somma_classe(bravo) / somma + costanti.PESO_ESPERIENZA_CLASSE * 9.0 / 20.0)
    assert [n for n, _p in ancore] == [100, 89, 50, 30, 1] and all(p == math.floor(esatti[n] * 1000) / 1000 for n, p in ancore[1:4])
    # Messa la classe nuova nel processo, chi fa da ancora sta nel suo livello, il contesto la porta ai
    # processi, e un secondo ricalcolo si rifiuta.
    cp.imposta_classe(somma, ancore)
    assert all(classe.livello(esatti[n]) == n for n in (89, 50, 30)) and classe.soglia(30) == ancore[3][1]
    assert cp.classe_in_vigore() == (somma, ancore) and not cp.classe_da_ricalcolare()
    with pytest.raises(SystemExit, match="già stata ricalcolata"):
        cp.ricalcola_classe(types.SimpleNamespace(), print)
    assert cp.blocco_costanti(*cp.fonti_in_vigore(), (somma, ancore, esatti))[-3:] == [
        f"SOMMA_CARRIERA_PERFETTA = {somma}", f"ANCORE_CLASSE = {ancore!r}",
        f"E in tests/test_classe.py: ANCORE_ESATTE = ((89, {esatti[89]:.6f}), (50, {esatti[50]:.6f}), (30, {esatti[30]:.6f}))"]


def test_la_carriera_perfetta_gioca_il_calendario():
    # Tappa 12, punto 10.4: una carriera corta, coi mondi sintetici piccoli, gioca tornei, sfide e
    # amichevoli; il totale è la seduta più i punti grezzi per i fattori, e il blocco si stampa.
    import mondi_sintetici as ms
    mondo_10 = ms.mondo_sintetico(60, 10, 3)
    regime = ms.mondo_sintetico(120, None, 4, primo_id=600_000, candidati=420)
    cp.prepara_contesto(cp.contesto_in_dizionari(mondo_10, regime, cp.calendario_predefinito(150)))
    fattori, esperienze = cp.fonti_in_vigore()
    nato = next(g for g in cp.nati(60, 11) if cp.senza_tratti(g))
    r = cp.Carriera(nato, 11, fattori, esperienze, giorni=150, coda_da=cp.ETA_INGRESSO).gioca().riassunto()
    assert r["storia"]["tornei"] >= 1 and r["storia"]["incontri_torneo"] >= 2 and r["storia"]["amichevoli"] > 50 and r["storia"]["sfide"] >= 3
    assert r["seduta"] == 150 and r["punti_totali"] == pytest.approx(150 + sum(r["grezzi"][f] * fattori[f] for f in fattori))
    assert r["conteggi"]["giorni"] == pytest.approx(150 * cp.FATTORE_GRUPPO) and r["eta_a1"] > cp.ETA_INGRESSO
    assert cp.blocco_costanti(fattori, esperienze)[1].startswith("PA_FATTORE_AMICHEVOLE = ")
    # La decisione 7: la carriera dice la somma a fine carriera anche coi pesi di prima, per il ricalcolo della classe.
    assert r["somma_50_prima"] > cp.somma_classe_prima(nato) > 0 and 0.8 < r["somma_50"] / r["somma_50_prima"] < 1.2


def test_la_carriera_perfetta_va_al_mondiale_coi_punti_e_si_misura_in_media():
    # La revisione del 14 ottobre 2026: la carriera va al mondiale coi punti dell'ultimo anno, come nel
    # mondo, e i bersagli si leggono sulla media delle estrazioni di ogni nato.
    import mondi_sintetici as ms
    mondo_10 = ms.mondo_sintetico(60, 10, 3)
    regime = ms.mondo_sintetico(120, None, 4, primo_id=600_000, candidati=420)
    cp.prepara_contesto(cp.contesto_in_dizionari(mondo_10, regime, cp.calendario_predefinito(150)))
    fattori, esperienze = cp.fonti_in_vigore()
    nato = next(g for g in cp.nati(60, 11) if cp.senza_tratti(g))
    c = cp.Carriera(nato, 11, fattori, esperienze, giorni=150, coda_da=cp.ETA_INGRESSO)
    oggi = cp.DATA_INIZIO + datetime.timedelta(days=400)
    c.punti_recenti = [(oggi.toordinal() - 400, 5000.0), (oggi.toordinal() - 30, costanti.PUNTI_PER_IL_MONDIALE["m"] - 1)]
    mondiale = types.SimpleNamespace(data_apertura=oggi, data_inizio=oggi + datetime.timedelta(days=10), data_fine=oggi + datetime.timedelta(days=12))
    c.g.sesso = "m"
    c._mondiale_che_apre([mondiale], oggi)
    assert c.mondiale is None and c.punti_dell_anno(oggi) == costanti.PUNTI_PER_IL_MONDIALE["m"] - 1
    c.punti_recenti.append((oggi.toordinal() - 10, 1.0))
    c._mondiale_che_apre([mondiale], oggi)
    assert c.mondiale is mondiale
    carriere = [{"seme": s, "id": s, "estrazione": k, "eta_a1": eta, "punti_totali": 100.0 * eta, "seduta": 10.0, "esperienza_libera": 20.0,
                 "grezzi": {"torneo": 1.0}, "grezzi_mondiale": 0.0, "conteggi": {"giorni": 1.0}, "storia": {"mondiali": k}}
                for s, etas in ((1, (49.0, 50.0, 51.0)), (2, (48.0, 48.5, 49.0))) for k, eta in enumerate(etas)]
    medie = cp.medie_per_nato(carriere)
    assert [m["eta_a1"] for m in medie] == [50.0, 48.5] and medie[0]["rappresentante"]["eta_a1"] == 50.0
    assert medie[0]["eta_a1_max"] == 51.0 and medie[0]["mondiali"] == 1.0
    # La decisione 6 di Gabriele del 14 ottobre 2026: il bersaglio è la media di tutte le carriere vedenti.
    tutte = cp.media_di_tutte(carriere)
    assert tutte["eta_a1"] == pytest.approx(49.25) and tutte["seme"] is None and tutte["punti_totali"] == pytest.approx(4925.0)
    assert tutte["rappresentante"]["eta_a1"] == 49.0 and tutte["eta_a1_min"] == 48.0 and tutte["eta_a1_max"] == 51.0
    assert cp.ETA_A1_BERSAGLIO == 50.0 and cp.BANDA_ETA_A1[0] < cp.ETA_A1_BERSAGLIO < cp.BANDA_ETA_A1[1]
    # La verifica del 15 ottobre 2026: l'errore della media sui nati, e il giudizio che ne tiene conto.
    assert cp.errore_della_media(medie) == pytest.approx(statistics.stdev((50.0, 48.5)) / math.sqrt(2)) and cp.errore_della_media(medie[:1]) == 0.0
    assert cp.giudizio_eta(49.9, 0.1) == "dentro" and cp.giudizio_eta(49.5, 0.3) == "dentro l'errore della media" and cp.giudizio_eta(49.0, 0.3) == "FUORI"


def test_il_totale_del_passo_seguente_viene_dalla_retta_di_tutti_i_passi():
    # Con una misura sola la pendenza di prima stima, 25 anni per logaritmo; con due la secante; con
    # più la retta ai minimi quadrati di tutte, che non rincorre il rumore dell'ultima; il passo resta
    # entro 0,15 di logaritmo dall'ultimo totale provato.
    assert cp.prossimo_totale([(10.0, 50.5)]) == pytest.approx(10.0 + 0.5 / 25.0)
    assert cp.prossimo_totale([(10.0, 51.0), (10.1, 48.0)]) == pytest.approx(10.0 + 1.0 / 30.0)
    punti = [(10.0, 51.0), (10.1, 48.0), (10.05, 49.9), (10.04, 50.4)]
    x = [p[0] for p in punti]
    y = [p[1] for p in punti]
    pendenza = statistics.linear_regression(x, y).slope
    assert cp.prossimo_totale(punti) == pytest.approx(statistics.fmean(x) + (50.0 - statistics.fmean(y)) / pendenza)
    # Una pendenza che non scende torna alla prima stima, e il passo si ferma a 0,15.
    assert cp.prossimo_totale([(10.0, 49.0), (10.1, 49.5)]) == pytest.approx(statistics.fmean((10.0, 10.1)) + (50.0 - 49.25) / -25.0)
    assert cp.prossimo_totale([(10.0, 60.0)]) == pytest.approx(10.15)
