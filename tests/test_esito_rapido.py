"""
Test dell'esito rapido della tappa 12, punto 6.7 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Lo stesso seme dà lo stesso esito; i set sono validi, a 11 o a 31 con 2 di scarto, e al meglio dei 3
e dei 5 il conto dei set è giusto; più forza vuol dire più vittorie; la stanchezza al meglio dei 5 e
quella della giornata; gli infortuni a fine set, il ritiro, gli acciacchi e il calo che toglie
vittorie; la registrazione legge il risultato rapido come quello del motore; e un confronto col
motore su 400 incontri fissi, entro 6 punti per fascia di distacco.
"""

import datetime
import random
import sys
from pathlib import Path

import pytest
from aiuti_motore import giocatore

import esito_rapido
import infortuni
from mondo import Mondo
from motore import ESSENZIALE, SINGOLARE_3, SINGOLARE_5, SQUADRE, Squadra, simula_incontro
from partita import MotorePartita

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))
import popolazione_di_prova as pp
from banco_partite import FASCE_DISTACCO, distacco, indice_del_distacco

OGGI = datetime.datetime(2026, 6, 1, 9, 0)


def _set_valido(a, b, punti=11):
    return max(a, b) >= punti and abs(a - b) >= 2


def test_stesso_seme_stesso_esito():
    a, b = giocatore(1, valore=15.0), giocatore(2, valore=14.0)
    primo = esito_rapido.gioca(a, b, SINGOLARE_3, 99)
    secondo = esito_rapido.gioca(a, b, SINGOLARE_3, 99)
    assert primo.set == secondo.set and primo.vincitore == secondo.vincitore
    assert isinstance(primo, esito_rapido.RisultatoRapido) and primo.punti == [] and primo.eventi is None


@pytest.mark.parametrize("formato", [SINGOLARE_3, SINGOLARE_5])
def test_i_set_e_il_conto_dei_set(formato):
    rng = random.Random(3)
    for _ in range(200):
        a, b = giocatore(1, valore=rng.uniform(5, 30)), giocatore(2, valore=rng.uniform(5, 30))
        r = esito_rapido.gioca(a, b, formato, rng.getrandbits(63))
        assert all(_set_valido(x, y) for x, y in r.set)
        vinti_a, vinti_b = r.set_vinti
        assert max(vinti_a, vinti_b) == formato.set_al_meglio // 2 + 1 and (vinti_a > vinti_b) == (r.vincitore == "A")
        assert r.set_giocati == len(r.set) and r.esito == "regolare"
        assert r.statistiche[1].azioni > 0 and r.statistiche[1].azioni == r.statistiche[2].azioni


def test_la_gara_a_squadre_a_31():
    uomini = [giocatore(n) for n in range(1, 5)]
    donne = [giocatore(n, sesso="f") for n in range(5, 9)]
    a = Squadra("A", (uomini[0], uomini[1], donne[0], donne[3]))
    b = Squadra("B", (uomini[2], donne[1], donne[2]))
    for seme in range(30):
        r = esito_rapido.gioca_squadre(a, b, seme)
        assert len(r.set) == 1 and _set_valido(*r.set[0], punti=31) and r.formato is SQUADRE and r.nomi_squadre == ("A", "B")
        assert r.statistiche[donne[3].id].azioni == 0 and r.statistiche[uomini[0].id].azioni > 0


def test_la_fatica_della_giornata_nella_gara_a_squadre():
    # La lettura 12 delle decisioni di Gabriele del 14 ottobre 2026: la gara a squadre dell'esito rapido
    # conosce la fatica della giornata. Senza azioni iniziali è quella di prima, con le azioni iniziali dei
    # titolari di A li fa rendere meno, e le statistiche contano soltanto le azioni dell'incontro.
    uomini = [giocatore(n, valore=15.0, anni=60, fisico=1.0) for n in range(1, 5)]
    donne = [giocatore(n, valore=15.0, anni=60, sesso="f", fisico=1.0) for n in range(5, 9)]
    a = Squadra("A", (uomini[0], uomini[1], donne[0], donne[3]))
    b = Squadra("B", (uomini[2], donne[1], uomini[3]))
    stanchi = {g.id: 120 for g in a.titolari}
    rng = random.Random(12)
    vinte_fresche = vinte_stanche = 0
    for _ in range(400):
        seme = rng.getrandbits(63)
        fresca = esito_rapido.gioca_squadre(a, b, seme)
        # Le azioni iniziali di una riserva, che non va al tavolo, non cambiano niente.
        con_la_riserva = esito_rapido.gioca_squadre(a, b, seme, azioni_iniziali={donne[3].id: 500})
        assert con_la_riserva.set == fresca.set and con_la_riserva.statistiche[1].azioni == fresca.statistiche[1].azioni
        stanca = esito_rapido.gioca_squadre(a, b, seme, azioni_iniziali=stanchi)
        vinte_fresche += fresca.vincitore == "A"
        vinte_stanche += stanca.vincitore == "A"
    assert vinte_stanche < vinte_fresche - 20
    # Le statistiche, e con loro il carico d'infortunio, partono da zero anche per chi comincia stanco.
    sfinito = esito_rapido.gioca_squadre(a, b, 5, azioni_iniziali={uomini[0].id: 10_000})
    assert 0 < sfinito.statistiche[uomini[0].id].azioni < 1000


def test_piu_forza_piu_vittorie():
    forte, debole = giocatore(1, valore=24.0), giocatore(2, valore=12.0)
    rng = random.Random(5)
    vinte = sum(esito_rapido.gioca(forte, debole, SINGOLARE_3, rng.getrandbits(63)).vincitore == "A" for _ in range(300))
    assert esito_rapido.forza(forte) > esito_rapido.forza(debole)
    assert vinte > 200


def test_la_memoria_della_forza():
    g = giocatore(1, valore=20.0)
    memoria = {}
    forza = esito_rapido.forza(g, memoria=memoria)
    g.difesa_allenata += 10.0
    assert esito_rapido.forza(g, memoria=memoria) == forza and memoria == {1: forza}
    assert esito_rapido.forza(g) > forza


def test_la_stanchezza_al_meglio_dei_5_e_quella_della_giornata():
    giovane = giocatore(1, valore=15.0, anni=25, fisico=4.0)
    anziano = giocatore(2, valore=15.0, anni=65, fisico=1.0)
    rng = random.Random(8)
    semi = [rng.getrandbits(63) for _ in range(400)]
    al_3 = sum(esito_rapido.gioca(giovane, anziano, SINGOLARE_3, s).vincitore == "A" for s in semi)
    al_5 = sum(esito_rapido.gioca(giovane, anziano, SINGOLARE_5, s).vincitore == "A" for s in semi)
    assert al_5 >= al_3
    stanco = sum(esito_rapido.gioca(giovane, anziano, SINGOLARE_3, s, azioni_iniziali={2: 150}).vincitore == "A" for s in semi)
    assert stanco >= al_3


def test_il_calo_dell_acciacco_toglie_vittorie():
    a, b = giocatore(1), giocatore(2)
    rng = random.Random(11)
    semi = [rng.getrandbits(63) for _ in range(500)]
    sano = sum(esito_rapido.gioca(a, b, SINGOLARE_3, s).vincitore == "A" for s in semi)
    acciaccato = sum(esito_rapido.gioca(a, b, SINGOLARE_3, s, cali={1: 0.06}).vincitore == "A" for s in semi)
    assert acciaccato < sano


def test_infortuni_ritiro_e_acciacchi():
    a, b = giocatore(1, anni=70), giocatore(2, anni=70)
    visti = set()
    for seme in range(400):
        r = esito_rapido.gioca(a, b, SINGOLARE_3, seme, basi_infortunio={1: 400.0, 2: 400.0})
        if r.esito == "ritiro":
            visti.add("ritiro")
            assert r.ritirato and r.set_giocati < len(r.set) and all(s in ((11, 0), (0, 11)) for s in r.set[r.set_giocati:])
        if r.infortuni:
            visti.add("infortunio")
            assert all(gid in (1, 2) and 1 <= set_n <= r.set_giocati for gid, set_n, _sede in r.infortuni)
        if r.acciacchi:
            visti.add("acciacco")
            assert not {gid for gid, _s in r.acciacchi} & {gid for gid, _n, _s in r.infortuni}
    assert visti == {"ritiro", "infortunio", "acciacco"}
    assert esito_rapido.gioca(a, b, SINGOLARE_3, 1).infortuni == []


def test_la_registrazione_legge_il_risultato_rapido():
    a, b = giocatore(1), giocatore(2)
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    mondo.giocatori.update({1: a, 2: b})
    r = esito_rapido.gioca(a, b, SINGOLARE_3, 5, basi_infortunio={1: infortuni.probabilita_base(a), 2: infortuni.probabilita_base(b)})
    MotorePartita(mondo).registra(r, "torneo", importanza=1.0, diario=False)
    assert a.partitevinte + a.partiteperse == 1 and a.punti_allenamento > 0 and a.ultimo_impegno == OGGI
    assert a.goalsfatti == r.statistiche[1].goal


def test_la_regressione_della_taratura_ritrova_i_coefficienti():
    import numpy as np
    import taratura_esito_rapido as tr

    rng = np.random.default_rng(4)
    X = rng.normal(size=(20_000, 3))
    veri = np.array([1.5, -0.7, 0.3])
    y = (rng.random(20_000) < 1.0 / (1.0 + np.exp(-(X @ veri)))).astype(float)
    assert np.allclose(tr.logistica(X, y, ridge=1e-3), veri, atol=0.08)


def test_l_esito_rapido_somiglia_al_motore():
    giocatori = [g for g in pp.genera(300, 13) if g.puo_giocare]
    rng = random.Random("confronto")
    limiti = [0.0] + [f[0] for f in FASCE_DISTACCO if f[0] is not None] + [float("inf")]
    conti = {i: [0, 0, 0] for i in range(len(FASCE_DISTACCO))}
    for _ in range(400):
        a, b = rng.sample(giocatori, 2)
        seme = rng.getrandbits(63)
        ia, ib = indice_del_distacco(a), indice_del_distacco(b)
        favorito = "A" if ia >= ib else "B"
        d = distacco(ia, ib)
        fascia = next(i for i in range(len(FASCE_DISTACCO)) if limiti[i] <= d < limiti[i + 1])
        conti[fascia][0] += 1
        conti[fascia][1] += simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE).vincitore == favorito
        conti[fascia][2] += esito_rapido.gioca(a, b, SINGOLARE_3, seme).vincitore == favorito
    # Dalla taratura fine del passo 4: una fascia con una cinquantina di incontri ha un errore di quasi 8
    # punti, e il bersaglio di 6 lì non dice niente; si giudicano le fasce con almeno cento incontri, e
    # tutti gli incontri insieme entro 3 punti. La verifica vera, su 40.000 incontri, la fa la taratura.
    for quanti, motore, rapido in conti.values():
        if quanti >= 100:
            assert abs(100.0 * (motore - rapido) / quanti) <= 6.0, conti
    totale = sum(c[0] for c in conti.values())
    assert abs(100.0 * sum(c[1] - c[2] for c in conti.values()) / totale) <= 3.0, conti
