"""
Test del ritiro a fine set e della sconfitta a tavolino, tappa 12, decisione D32, risposte 6, 7 e 8
di Gabriele e la sua regola sugli infortuni, punto 7 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Il ritiro con un generatore truccato, i set aggiunti 11 a 0 e i set giocati; lo stesso nelle due
modalità, con l'evento del ritiro prima della fine dell'incontro; il gemello della partita dal vivo
che ripete il ritiro; l'ambidestro che cambia braccio e non si ritira, e chi era già infortunato che
non si estrae; il ritiro di tutti e due; la somma delle probabilità dei set uguale a un quinto di
quella dell'incontro, e la probabilità che succeda qualcosa uguale a quella di prima; su tanti
incontri gli infortuni che fermano a un quinto e gli eventi in tutto come prima; senza basi, cali e
azioni iniziali il motore identico; il tavolino senza punti né esperienza; il ritiro con i punti
dei soli set giocati, e i diari.
"""

import datetime
import random
import sys
from pathlib import Path

import pytest
from aiuti_motore import giocatore

import esperienza
import infortuni
from costanti import PA_FATTORE_AMICHEVOLE, QUOTA_INFORTUNI_CHE_FERMANO, giorni_da_anni
from modelli import Polisportiva
from mondo import Mondo
from motore import COMPLETO, ESSENZIALE, SINGOLARE_3, SINGOLARE_5, SQUADRE, Incontro, Squadra, a_tavolino, simula_incontro
from motore import cronaca as C
from motore import eventi as E
from motore.campo import fattore_carico
from motore.regia import controlla_invarianti
from partita import MotorePartita

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "strumenti"))
import popolazione_di_prova as pp

OGGI = datetime.datetime(2026, 5, 4, 9, 0)


class Sempre(random.Random):
    """Un generatore truccato: ogni tiro è zero, quindi ogni estrazione che può succedere succede, e la sede è la prima dei pesi."""

    def random(self):
        return 0.0


def _ritiro(a, b, dettaglio=ESSENZIALE, basi=None, seme=5, formato=SINGOLARE_3):
    return simula_incontro(a, b, formato, seme=seme, dettaglio=dettaglio, basi_infortunio=basi or {a.id: 10.0}, caso_infortuni=Sempre())


def test_il_ritiro_a_fine_set_con_i_set_aggiunti():
    a, b = giocatore(1), giocatore(2)
    r = _ritiro(a, b)
    assert r.esito == "ritiro" and r.ritirato == (1,) and r.vincitore == "B"
    assert r.set_giocati == 1 and r.infortuni == [(1, 1, "spalla_dx")]
    primo = r.set[0]
    aggiunti = r.set[1:]
    assert all(s == (0, 11) for s in aggiunti) and len(aggiunti) == (1 if primo[1] > primo[0] else 2)
    assert r.set_vinti[1] == 2
    # Al meglio dei 5 servono tre set all'altro.
    r5 = _ritiro(a, b, formato=SINGOLARE_5)
    assert r5.set_vinti[1] == 3 and r5.set_giocati == 1


def test_il_ritiro_uguale_nelle_due_modalita_con_l_evento():
    a, b = giocatore(1, cognome="Rossi"), giocatore(2, cognome="Bianchi", sesso="f")
    essenziale = _ritiro(a, b)
    completo = _ritiro(a, b, COMPLETO)
    assert completo.punti == essenziale.punti and completo.set == essenziale.set and completo.ritirato == essenziale.ritirato
    assert controlla_invarianti(completo.eventi) == []
    tipi = [e.tipo for e in completo.eventi]
    assert tipi.index(E.RITIRO) < tipi.index(E.FINE_INCONTRO)
    righe = C.componi(completo.momenti, C.nomi_dei_giocatori([a, b]), C.NORMALE)
    assert any(riga.startswith("Rossi si fa male alla spalla destra e non può continuare: si ritira. Vince Bianchi.") for riga in righe)
    assert righe[-1].startswith("Fine dell'incontro: vince Bianchi per ritiro")


def test_il_ritiro_di_tutti_e_due():
    a, b = giocatore(1), giocatore(2)
    r = _ritiro(a, b, basi={1: 10.0, 2: 10.0})
    primo = r.set[0]
    vince = "A" if primo[0] > primo[1] else "B"
    assert r.esito == "ritiro" and set(r.ritirato) == {1, 2} and r.vincitore == vince and r.set_giocati == 1


def test_l_ambidestro_cambia_braccio_e_non_si_ritira():
    a, b = giocatore(1, ambidestro=True, cognome="Rossi"), giocatore(2, cognome="Bianchi")
    incontro = Incontro(a, b, SINGOLARE_3, seme=5, dettaglio=COMPLETO, basi_infortunio={1: 10.0}, caso_infortuni=Sempre())
    r = incontro.gioca()
    assert r.esito == "regolare" and r.ritirato == () and r.infortuni == [(1, 1, "spalla_dx")]
    assert incontro.campo[1].rovescio == "dx" and incontro.campo[1].mano == "sinistra" and not incontro.campo[1].cambia_mano
    tipi = [e.tipo for e in r.eventi]
    assert E.CAMBIO_BRACCIO in tipi and E.RITIRO not in tipi
    righe = C.componi(r.momenti, C.nomi_dei_giocatori([a, b]), C.NORMALE)
    assert "Rossi si fa male alla spalla destra e continua con il braccio sinistro." in righe


def test_chi_e_gia_infortunato_non_si_estrae():
    a = giocatore(1, ambidestro=True, infortunato=True, infortunio_sede="polso_dx")
    b = giocatore(2)
    r = simula_incontro(a, b, SINGOLARE_3, seme=5, dettaglio=ESSENZIALE, basi_infortunio={1: 10.0}, caso_infortuni=Sempre())
    assert r.infortuni == [] and r.acciacchi == [] and r.esito == "regolare"


def test_la_gara_a_squadre_non_conosce_il_ritiro():
    uomini = [giocatore(n) for n in range(1, 5)]
    donne = [giocatore(n, sesso="f") for n in range(5, 9)]
    a = Squadra("A", (uomini[0], uomini[1], donne[0]))
    b = Squadra("B", (uomini[2], donne[1], donne[2]))
    basi = {g.id: 10.0 for g in (*a.giocatori, *b.giocatori)}
    r = simula_incontro(a, b, SQUADRE, seme=3, dettaglio=ESSENZIALE, basi_infortunio=basi, caso_infortuni=Sempre())
    assert r.esito == "regolare" and r.set_giocati == 1
    assert [gid for gid, set_n, _sede in r.infortuni] == [1, 2, 5, 3, 6, 7] and all(set_n == 1 for _g, set_n, _s in r.infortuni)


def test_le_probabilita_dei_set_sommano_a_un_quinto():
    a, b = giocatore(1), giocatore(2)
    incontro = Incontro(a, b, SINGOLARE_5, seme=1, dettaglio=ESSENZIALE, basi_infortunio={1: 6.0, 2: 6.0})
    for azioni in ((20, 70, 140, 210, 260), (40, 90), (100, 160, 300)):
        sopravvive = 1.0
        prima = 0.0
        for n, a_k in enumerate(azioni, start=1):
            cumulata = max(prima, incontro._cumulata(6.0, a_k, n == len(azioni)))
            p = (cumulata - prima) / (100.0 - prima)
            assert p >= 0.0
            sopravvive *= 1.0 - p
            prima = cumulata
        piena = min(95.0, 6.0 * fattore_carico(azioni[-1]))
        assert 1.0 - sopravvive == pytest.approx(QUOTA_INFORTUNI_CHE_FERMANO * piena / 100.0)
        # Con gli acciacchi, la probabilità che succeda qualcosa è quella di prima.
        q = piena / 100.0
        acciacco = (q - QUOTA_INFORTUNI_CHE_FERMANO * q) / (1.0 - QUOTA_INFORTUNI_CHE_FERMANO * q)
        assert (1.0 - sopravvive) + sopravvive * acciacco == pytest.approx(q)


def test_su_tanti_incontri_un_quinto_ferma_e_il_resto_sono_acciacchi():
    # La popolazione di prova, invecchiata fra i 35 e i 70 anni, perché gli infortuni si vedano.
    giocatori = [g for g in pp.genera(400, 11) if g.puo_giocare]
    rng = random.Random("ritiri")
    for g in giocatori:
        g.eta = giorni_da_anni(rng.uniform(35.0, 70.0))
    attesi = fermi = acciacchi = ritiri = 0
    for _ in range(1500):
        a, b = rng.sample(giocatori, 2)
        basi = {g.id: infortuni.probabilita_base(g) for g in (a, b)}
        r = simula_incontro(a, b, SINGOLARE_3, seme=rng.getrandbits(63), dettaglio=ESSENZIALE, basi_infortunio=basi)
        attesi += sum(infortuni.probabilita(g, r.statistiche[g.id].azioni) / 100.0 for g in (a, b))
        fermi += len(r.infortuni)
        acciacchi += len(r.acciacchi)
        ritiri += r.esito == "ritiro"
    totale = fermi + acciacchi
    # Gli eventi in tutto sono quelli di prima, un quinto ferma: entro il rumore di un campione fisso.
    assert abs(totale - attesi) < 4 * attesi ** 0.5
    assert abs(fermi - QUOTA_INFORTUNI_CHE_FERMANO * attesi) < 4 * (QUOTA_INFORTUNI_CHE_FERMANO * attesi) ** 0.5
    assert 0 < ritiri <= fermi


def test_senza_basi_cali_e_azioni_iniziali_il_motore_non_cambia():
    a, b = giocatore(1, valore=15.0), giocatore(2, valore=13.0)
    for seme in (1, 2, 3):
        prima = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE)
        for opzioni in ({"cali": {}}, {"cali": {1: 0.0}}, {"azioni_iniziali": {}}, {"basi_infortunio": None, "cali": None, "azioni_iniziali": None}):
            dopo = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE, **opzioni)
            assert dopo.punti == prima.punti and dopo.set == prima.set
        # Con le basi i punti sono gli stessi fino alla fine dell'incontro, o fino al ritiro: il caso degli infortuni è un altro.
        con_basi = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE, basi_infortunio={1: 0.0, 2: 0.0})
        assert con_basi.punti == prima.punti and con_basi.infortuni == [] and con_basi.acciacchi == []


def test_le_azioni_iniziali_stancano_ma_non_contano_nelle_statistiche():
    a, b = giocatore(1, anni=60), giocatore(2, anni=60)
    fresco = Incontro(a, b, SINGOLARE_3, seme=8, dettaglio=ESSENZIALE)
    stanco = Incontro(a, b, SINGOLARE_3, seme=8, dettaglio=ESSENZIALE, azioni_iniziali={1: 80})
    assert stanco.campo[1].azioni == 80 and stanco.campo[1].stats.azioni == 0
    r = stanco.gioca()
    fresco.gioca()
    assert r.statistiche[1].azioni == stanco.campo[1].azioni - 80
    assert stanco.campo[1].eff < fresco.campo[1].eff or r.punti != fresco.risultato.punti


def test_il_tavolino():
    a, b = giocatore(1), giocatore(2)
    r = a_tavolino(a, b, SINGOLARE_3, "A")
    assert r.esito == "tavolino" and r.vincitore == "B" and r.set == [(0, 11), (0, 11)] and r.set_giocati == 0 and r.punti == []
    assert a_tavolino(a, b, SINGOLARE_5, "B").set == [(11, 0)] * 3
    uomini = [giocatore(n) for n in range(1, 5)]
    donne = [giocatore(n, sesso="f") for n in range(5, 9)]
    squadre = a_tavolino(Squadra("A", (uomini[0], uomini[1], donne[0])), Squadra("B", (uomini[2], donne[1], donne[2])), SQUADRE, "B")
    assert squadre.set == [(31, 0)] and squadre.nomi_squadre == ("A", "B")
    with pytest.raises(ValueError):
        a_tavolino(a, b, SINGOLARE_3, "C")


def _mondo_con(*giocatori):
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    for g in giocatori:
        mondo.giocatori[g.id] = g
    mia = Polisportiva("Club Di Prova", None, OGGI)
    mondo.polisportive[mia.nome] = mia
    return mondo, mia


def test_il_tavolino_non_da_punti_ne_esperienza():
    a, b = giocatore(1), giocatore(2, infortunato=True, infortunio_sede="ginocchio")
    mondo, mia = _mondo_con(a, b)
    mondo._entra(mia, a)
    mondo._entra(mia, b)
    frasi = MotorePartita(mondo).registra(a_tavolino(a, b, SINGOLARE_3, "B"), esperienza.TORNEO)
    for g in (a, b):
        assert (g.punti_allenamento, g.esperienza, g.costanza, g.partitevinte, g.partiteperse, g.setsvinti) == (0.0, 0.0, 0.0, 0, 0, 0)
    assert a.diario[0]["testo"].startswith("Vince a tavolino la partita del torneo contro ")
    assert b.diario[0]["testo"].endswith(": è infortunato.")
    assert frasi and "vince a tavolino" in frasi[0]


def test_il_ritiro_da_i_punti_dei_soli_set_giocati(monkeypatch):
    a, b = giocatore(1), giocatore(2)
    mondo, _mia = _mondo_con(a, b)
    r = _ritiro(a, b)
    set_vinti_b = 1 if r.set[0][1] > r.set[0][0] else 0
    frasi = MotorePartita(mondo).registra(r)
    assert b.partitevinte == 1 and a.partiteperse == 1 and a.setsvinti + b.setsvinti == 1
    assert b.punti_allenamento == pytest.approx((2.0 + 0.5 * set_vinti_b + 1.0) * PA_FATTORE_AMICHEVOLE)
    assert a.punti_allenamento == pytest.approx((2.0 + 0.5 * (1 - set_vinti_b)) * PA_FATTORE_AMICHEVOLE)
    assert a.infortunato and a.infortunio_sede == "spalla_dx" and a.diario[0]["testo"].startswith("Si infortuna alla spalla destra")
    assert any("si ritira" in v.get("testo", "") for v in a.diario)
    assert any(f.startswith(f"{a.nome} {a.cognome}: si infortuna") for f in frasi)


def test_il_gemello_della_partita_dal_vivo_ripete_ritiro_e_acciacchi(monkeypatch):
    # Con una base altissima il ritiro e gli acciacchi arrivano presto: si cercano due semi fissi.
    monkeypatch.setattr(infortuni, "probabilita_base", lambda _g: 400.0)
    visti = set()
    for seme in range(1, 80):
        a, b = giocatore(1), giocatore(2)
        mondo, _mia = _mondo_con(a, b)
        risultato, gemello = MotorePartita(mondo).amichevole_da_assistere(1, 2, seme=seme)
        ripetuto = gemello.gioca()
        assert ripetuto.punti == risultato.punti and ripetuto.set == risultato.set
        assert ripetuto.infortuni == risultato.infortuni and ripetuto.acciacchi == risultato.acciacchi and ripetuto.ritirato == risultato.ritirato
        if risultato.esito == "ritiro":
            visti.add("ritiro")
        if risultato.acciacchi:
            visti.add("acciacco")
        if visti == {"ritiro", "acciacco"}:
            break
    assert visti == {"ritiro", "acciacco"}
