"""
Test della issue 11, decisione D37 del 24 ottobre 2026: i blocchi avvengono soltanto sulle sponde, anche
quello di una pallina arrivata al centro, e il controllo palla porta la pallina al punto da cui parte il
colpo che il motore ha già scelto, con una delle tre possibilità di Gabriele compatibili con il colpo:
dal punto del blocco o da uno vicino sulla stessa sponda, dal centro, o dall'altra sponda. Chi controlla
meglio porta più spesso la pallina altrove; la paletta non la porta oltre la sua velocità massima, e il
controllo resta più breve della pallina trattenuta. Le palle morte si fermano a centrocampo, lontane dai
giocatori. Il blocco ha il suo suono, mess_partita_blocco, al suo istante e sulla sua sponda nel buffer
composto, e il suono del controllo si sposta con la pallina; la cronaca dice il blocco sulla sponda e
dove il giocatore porta la pallina. Gli esiti sono quelli della modalità essenziale con gli stessi
semi, che la regia non tocca; l'impronta del motore la guarda tests/test_identita_motore.py.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
"""

import dataclasses
import math
import random

import numpy as np
import pytest
from aiuti_dal_vivo import vieta_la_cassa_vera
from aiuti_motore import giocatore
from test_identita_motore import _risultato_in_json

import partita_sonora as ps
from motore import cronaca as C
from motore import eventi as E
from motore.eventi import Evento
from motore.incontro import COMPLETO, ESSENZIALE, SINGOLARE_3, SQUADRE, Incontro, simula_incontro
from motore.regia import (
    AL_CENTRO,
    ALTRA_SPONDA,
    CENTROCAMPO,
    DAL_BLOCCO,
    DISTANZE_SULLA_SPONDA,
    TRASPORTI,
    VELOCITA_TRASPORTO,
    aree_di_partenza,
    controlla_invarianti,
)
from motore.scambio import EsitoPunto, Passo
from motore.taratura import TARATURA
from motore.tavolo import CENTRO_X, LARGHEZZA_TAVOLO, LUNGHEZZA_TAVOLO, MARGINE_GIOCO, distanza_di, lato_di, locale_in_assoluto

INCONTRI = 24
GARE_A_SQUADRE = 3


def _giocatori(rng):
    a = giocatore(1, valore=rng.uniform(8, 30), mancino=rng.random() < 0.2, giocorapido=rng.random() < 0.3, cognome="Rossi", nome="Mario")
    b = giocatore(2, valore=rng.uniform(8, 30), ambidestro=rng.random() < 0.3, sesso="f", cognome="Bianchi", nome="Anna")
    return a, b


def _partite(dettaglio):
    """Ventiquattro singolari e tre gare a squadre con semi fissi, nella modalità indicata, con i nomi della cronaca."""
    rng = random.Random(11)
    partite = []
    for seme in range(INCONTRI):
        a, b = _giocatori(rng)
        partite.append((simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=dettaglio), C.nomi_dei_giocatori([a, b])))
    from motore.squadre import Squadra

    for seme in range(GARE_A_SQUADRE):
        a = Squadra("Leoni", tuple(giocatore(i, valore=rng.uniform(8, 30), sesso=s) for i, s in ((1, "m"), (2, "m"), (3, "f"))))
        b = Squadra("Tigri", tuple(giocatore(i, valore=rng.uniform(8, 30), sesso=s) for i, s in ((11, "f"), (12, "f"), (13, "m"))))
        nomi = C.nomi_dei_giocatori([*a.giocatori, *b.giocatori], squadre=(a, b))
        partite.append((simula_incontro(a, b, SQUADRE, seme=200 + seme, dettaglio=dettaglio), nomi))
    return partite


@pytest.fixture(scope="module")
def partite():
    return _partite(COMPLETO)


def _sulla_sponda(x):
    return math.isclose(x, MARGINE_GIOCO, abs_tol=0.05) or math.isclose(x, LARGHEZZA_TAVOLO - MARGINE_GIOCO, abs_tol=0.05)


def _blocchi(risultato):
    """I blocchi dell'incontro, con l'indice nell'elenco degli eventi."""
    for indice, ev in enumerate(risultato.eventi):
        if ev.tipo == E.PARATA and ev.esito == "fermata":
            yield indice, ev


# La scena.

def test_nessun_blocco_al_centro(partite):
    blocchi = dal_centro = 0
    for risultato, _nomi in partite:
        eventi = risultato.eventi
        for indice, ev in _blocchi(risultato):
            blocchi += 1
            dal_centro += ev.dati["zona"] == "centro"
            # Contro la sponda, quella della zona o la più vicina per la pallina arrivata al centro, e il volo arriva proprio lì.
            assert _sulla_sponda(ev.pos[0]) and ev.lato in ("sinistra", "destra"), (ev.n, ev.pos)
            if ev.dati["zona"] != "centro":
                assert ev.lato == {"sx": "sinistra", "dx": "destra"}[ev.dati["zona"]]
            volo = next(e for e in reversed(eventi[:indice]) if e.tipo == E.VOLO)
            assert (round(volo.volo[-1].x, 1), round(volo.volo[-1].y, 1)) == ev.pos and volo.volo[-1].tipo == "paletta"
            assert distanza_di(ev.pos[1], ev.parte) == pytest.approx(ev.distanza) and 15.0 - 0.05 <= ev.distanza <= 35.0 + 0.05
        assert controlla_invarianti(eventi) == []
    assert blocchi >= 1000 and dal_centro >= 150


def _controlli_col_colpo(risultato):
    eventi = risultato.eventi
    for indice, ev in enumerate(eventi):
        if ev.tipo == E.CONTROLLO and (ev.dati or {}).get("porta_a") is not None:
            yield ev, eventi[indice + 1]


def test_il_controllo_porta_la_pallina_dove_parte_il_colpo(partite):
    visti = dict.fromkeys(TRASPORTI, 0)
    recuperi = 0
    for risultato, _nomi in partite:
        for ev, colpo in _controlli_col_colpo(risultato):
            dati = ev.dati
            trasporto = dati["trasporto"]
            visti[trasporto] += 1
            recuperi += ev.esito == "recupero"
            assert ev.esito in ("riuscito", "recupero") and colpo.tipo == E.COLPO and colpo.chi == ev.chi
            assert colpo.pos == tuple(dati["porta_a"])
            # La possibilità è compatibile con il colpo, nel riferimento di chi tira.
            u_blocco = locale_in_assoluto(ev.parte, *ev.pos)[0]
            u, v = locale_in_assoluto(ev.parte, *colpo.pos)
            lato = "sinistra" if u_blocco < CENTRO_X else "destra"
            aree = aree_di_partenza(TARATURA.COLPI[colpo.colpo])
            if trasporto == DAL_BLOCCO:
                assert lato in aree and u == pytest.approx(u_blocco, abs=0.15)
                assert DISTANZE_SULLA_SPONDA[0] - 0.05 <= v <= DISTANZE_SULLA_SPONDA[1] + 0.05
            elif trasporto == AL_CENTRO:
                assert "centro" in aree and abs(u - CENTRO_X) <= TARATURA.SCOSTAMENTO_MASSIMO + 0.05 and 25.0 - 0.05 <= v <= 40.0 + 0.05
            else:
                altro = "destra" if lato == "sinistra" else "sinistra"
                dalla_sponda = u if altro == "sinistra" else LARGHEZZA_TAVOLO - u
                assert altro in aree and MARGINE_GIOCO - 0.05 <= dalla_sponda <= MARGINE_GIOCO + TARATURA.SCOSTAMENTO_MASSIMO + 0.05
            # La paletta non porta la pallina oltre la sua velocità, e il controllo resta più breve della pallina trattenuta.
            strada = math.dist(ev.pos, colpo.pos)
            assert 0.0 < dati["presa"] < ev.durata < TARATURA.DURATA_TRATTENUTA[0]
            assert strada / (ev.durata - dati["presa"]) <= VELOCITA_TRASPORTO + 0.5, (ev.n, strada, ev.durata)
            assert colpo.t == pytest.approx(ev.t + ev.durata, abs=2e-3)
    assert all(quanti >= 100 for quanti in visti.values()), visti
    assert recuperi >= 3


def test_le_aree_di_partenza_dei_colpi():
    attese = {
        "lungolineasx": ("sinistra",), "lungolineadx": ("destra",), "diagonalesx": ("destra",), "diagonaledx": ("sinistra",),
        "singolaspondasx": ("centro", "destra"), "singolaspondadx": ("centro", "sinistra"),
        "doppiaspondasx": ("centro", "destra"), "doppiaspondadx": ("centro", "sinistra"),
        "triplaspondasx": ("centro", "destra"), "triplaspondadx": ("centro", "sinistra"), "bomba": ("centro",),
    }
    assert {nome: aree_di_partenza(TARATURA.COLPI[nome]) for nome in attese} == attese


def _incontro_scritto(seme=1, **campi_b):
    incontro = Incontro(giocatore(1, cognome="Rossi"), giocatore(2, cognome="Bianchi", sesso="f", **campi_b), SINGOLARE_3, seme=seme, dettaglio=COMPLETO)
    return incontro, incontro.campo[1], incontro.campo[2]


def _gioca_passi(incontro, a, b, passi, esito):
    """Un punto scritto a mano, battuto da a: la ripresa e gli eventi del punto, come li fa la regia."""
    regia = incontro.regia
    eventi = regia.inizio_set(1, a)
    eventi += regia.ripresa(a, b, 1, (0, 0), False, passi, (0, 0))
    eventi += regia.punto(passi, esito, (0, 0))
    return eventi


def _battuta_e_blocco(a, b, zona="sx"):
    return [Passo("battuta", a, "battutasx", zona, "regolare", None, False, 40.0, (0.05, 0.95)),
            Passo("parata", b, "battutasx", zona, "fermata", None, False, 30.0, (0.2, 0.01, 0.01, 0.2, 0.58))]


def _trasporto_dopo(colpo, seme):
    """Battuta, blocco di b sulla sua sponda sinistra, controllo riuscito, il colpo indicato e il goal: il trasporto scelto."""
    incontro, a, b = _incontro_scritto(seme)
    zona = TARATURA.COLPI[colpo].zona
    passi = [*_battuta_e_blocco(a, b), Passo("controllo", b, None, "sx", "riuscito", None, False, 0.8, (0.01, 0.05, 0.94)),
             Passo("colpo", b, colpo, zona, "colpo", None, False, 40.0, (0.05, 0.05, 0.9)),
             Passo("parata", a, colpo, zona, "goal", "goal_scambio", False, 20.0, (0.6, 0.1, 0.1, 0.1, 0.1)),
             Passo("goal", b, colpo, zona, "goal", "goal_scambio")]
    esito = EsitoPunto("goal", "goal_scambio", False, None, "B", 2, 1, "scambio", colpo, zona)
    eventi = _gioca_passi(incontro, a, b, passi, esito)
    assert controlla_invarianti(eventi) == []
    blocco = next(e for e in eventi if e.tipo == E.PARATA and e.esito == "fermata")
    assert blocco.lato == "sinistra" and blocco.pos[0] == pytest.approx(LARGHEZZA_TAVOLO - MARGINE_GIOCO)
    controllo = next(e for e in eventi if e.tipo == E.CONTROLLO)
    return controllo.dati["trasporto"]


def test_le_possibilita_compatibili_con_il_colpo():
    # Il blocco è sulla sponda sinistra di chi tira: il lungolinea sinistro parte da lì, il destro dall'altra
    # sponda, la bomba dal centro; i colpi di sponda dal centro o dal lato opposto alla loro prima sponda.
    attese = {"lungolineasx": {DAL_BLOCCO}, "lungolineadx": {ALTRA_SPONDA}, "diagonaledx": {DAL_BLOCCO}, "diagonalesx": {ALTRA_SPONDA},
              "bomba": {AL_CENTRO}, "singolaspondasx": {AL_CENTRO, ALTRA_SPONDA}, "doppiaspondadx": {DAL_BLOCCO, AL_CENTRO}}
    for colpo, possibili in attese.items():
        scelti = {_trasporto_dopo(colpo, seme) for seme in range(30)}
        assert scelti == possibili, (colpo, scelti)


def test_chi_controlla_meglio_porta_la_pallina_altrove():
    incontro, _a, b = _incontro_scritto()
    regia = incontro.regia
    blocco = (LARGHEZZA_TAVOLO - MARGINE_GIOCO, LUNGHEZZA_TAVOLO - 25.0)
    resta = {}
    for qualita in (5.0, 60.0):
        regia.campo[b.id].C = qualita
        for recupero in (False, True):
            regia.rng = random.Random(3)
            scelte = [regia._partenza_dopo_il_blocco(b.id, blocco, "doppiaspondadx", recupero)[0] for _ in range(2000)]
            assert set(scelte) == {DAL_BLOCCO, AL_CENTRO}
            resta[qualita, recupero] = scelte.count(DAL_BLOCCO) / len(scelte)
    # Col controllo a 5 tira dal blocco quattro volte su cinque, a 60 una su quattro; dopo un recupero quasi sempre dal blocco.
    assert resta[5.0, False] == pytest.approx(0.8, abs=0.04) and resta[60.0, False] == pytest.approx(0.25, abs=0.04)
    assert resta[60.0, True] > 0.75 and resta[5.0, True] > 0.9


def _palla_morta(causa, seme):
    incontro, a, b = _incontro_scritto(seme)
    passi = _battuta_e_blocco(a, b)
    if causa == "pallina_ferma":
        passi += [Passo("controllo", b, None, "sx", "sfuggita", None, False, 20.0, (0.01, 0.1, 0.89)),
                  Passo("sfuggita", b, None, "sx", "pallina_ferma", "pallina_ferma"), Passo("palla_morta", b, None, "sx", "palla_morta", causa)]
        esito = EsitoPunto("palla_morta", causa, False, b.id, None, 0, 0, "controllo", None, "sx")
    elif causa == "ribattuta_lenta":
        passi[1] = passi[1]._replace(esito="ribattuta")
        passi.append(Passo("palla_morta", b, None, "sx", "palla_morta", causa))
        esito = EsitoPunto("palla_morta", causa, False, b.id, None, 0, 0, "ribattuta", None, "sx")
    else:
        passi += [Passo("controllo", b, None, "sx", "riuscito", None, False, 0.8, (0.01, 0.05, 0.94)),
                  Passo("colpo", b, "lungolineasx", "dx", "debole", "colpo_debole", False, 30.0, (0.05, 0.1, 0.85)),
                  Passo("palla_morta", b, "lungolineasx", "dx", "palla_morta", causa)]
        esito = EsitoPunto("palla_morta", causa, False, b.id, None, 0, 1, "scambio", "lungolineasx", "dx")
    return _gioca_passi(incontro, a, b, passi, esito)


@pytest.mark.parametrize("causa", ["pallina_ferma", "ribattuta_lenta", "colpo_debole"])
def test_le_palle_morte_si_fermano_a_centrocampo(causa):
    for seme in range(20):
        eventi = _palla_morta(causa, seme)
        assert controlla_invarianti(eventi) == []
        morta = next(e for e in eventi if e.tipo == E.PALLA_MORTA)
        # Lontana da tutti e due i giocatori, a non più di 60 cm dallo schermo; la pallina ferma e la ribattuta prima dello schermo.
        assert CENTROCAMPO[0] - 0.05 <= morta.pos[1] <= CENTROCAMPO[1] + 0.05 and min(morta.pos[1], LUNGHEZZA_TAVOLO - morta.pos[1]) >= CENTROCAMPO[0] - 0.05
        volo = next(e for e in reversed(eventi) if e.tipo == E.VOLO)
        assert volo.volo[-1].tipo == "fermo" and (round(volo.volo[-1].x, 1), round(volo.volo[-1].y, 1)) == morta.pos
        if causa != "colpo_debole":
            assert distanza_di(morta.pos[1], morta.parte) <= LUNGHEZZA_TAVOLO / 2
        if causa == "pallina_ferma":
            # La pallina sfuggita rotola via dal punto del blocco, sulla sponda, fino a fermarsi.
            assert volo.dati == {"sfuggita": True} and _sulla_sponda(volo.volo[0].x)


def test_le_invarianti_vedono_un_blocco_al_centro_e_un_trasporto_sbagliato():
    blocco = Evento(n=1, t=0.0, tipo=E.PARATA, fase=E.GIOCO, chi=2, parte="B", pos=(61.0, 340.0), lato="centro", esito="fermata")
    assert any("blocco" in problema for problema in controlla_invarianti([blocco]))
    controllo = Evento(n=2, t=0.0, tipo=E.CONTROLLO, fase=E.GIOCO, durata=1.0, chi=2, parte="B", pos=(116.0, 340.0), lato="sinistra", esito="riuscito",
                       dati={"porta_a": (61.0, 330.0), "trasporto": AL_CENTRO, "presa": 0.3})
    colpo = Evento(n=3, t=1.0, tipo=E.COLPO, fase=E.GIOCO, chi=2, parte="B", pos=(70.0, 330.0), lato="centro", esito="colpo", colpo="bomba")
    assert any("controllo" in problema for problema in controlla_invarianti([controllo, colpo]))
    morta = Evento(n=4, t=2.0, tipo=E.PALLA_MORTA, fase=E.GIOCO, chi=2, parte="B", pos=(116.0, 340.0), lato="sinistra", causa="pallina_ferma")
    assert any("palla morta" in problema for problema in controlla_invarianti([morta]))
    assert controlla_invarianti([dataclasses.replace(morta, causa="limite_tecnico")]) == []


# Gli esiti.

def test_esiti_uguali_alla_modalita_essenziale(partite):
    essenziali = _partite(ESSENZIALE)
    for (completa, _n), (essenziale, _m) in zip(partite, essenziali, strict=True):
        assert _risultato_in_json(completa) == _risultato_in_json(essenziale)


# Il suono.

def test_il_blocco_ha_il_suo_suono():
    evento = Evento(n=5, t=1.0, tipo=E.PARATA, fase=E.GIOCO, chi=2, parte="B", pos=(116.0, 340.0), lato="sinistra")
    assert ps.SUONI["blocco"] == "mess_partita_blocco" and ps.SUONI["parata"] == "mess_partita_parata"
    assert ps.suoni_fermi(dataclasses.replace(evento, esito="fermata")) == [("blocco", 0.0)]
    assert ps.suoni_fermi(dataclasses.replace(evento, esito="fermata", causa="sporca")) == [("blocco", 0.0)]
    for esito, causa in (("ribattuta", None), ("fallo", "difesa_irregolare"), ("fuori", "out_in_difesa")):
        assert ps.suoni_fermi(dataclasses.replace(evento, esito=esito, causa=causa)) == [("parata", 0.0)]
    # Breve, e diverso dalla parata, che ha l'assestamento dei pallini.
    assert ps.durata_della_sorgente("blocco") < 0.6 * ps.durata_della_sorgente("parata")


def _energia(stereo):
    return float(np.sum(stereo[:, 0].astype(np.float64) ** 2)), float(np.sum(stereo[:, 1].astype(np.float64) ** 2))


def test_il_suono_del_blocco_al_suo_posto_nel_buffer(partite, monkeypatch):
    vieta_la_cassa_vera(monkeypatch)
    risultato, _nomi = partite[0]
    eventi = risultato.eventi
    provati = set()
    for indice, ev in _blocchi(risultato):
        lato_per_a = lato_di(ev.pos[0], "A")
        if lato_per_a in provati:
            continue
        provati.add(lato_per_a)
        volo = eventi[indice - 1]
        assert volo.tipo == E.VOLO
        # Il buffer composto senza suonarlo, per chi ascolta da A, con il volo e il blocco, e con il volo soltanto: la differenza è il blocco.
        con = ps.componi([volo, ev], "A", da=volo.t)
        senza = ps.componi([volo], "A", da=volo.t, fine=ev.t + 1.0)
        (posato,) = [p for p in con.posati if p.ruolo == "blocco"]
        assert posato.t == ev.t and posato.posizioni == [ev.pos] and not [p for p in con.posati if p.ruolo == "parata"]
        n = min(len(con.buffer), len(senza.buffer))
        differenza = con.buffer[:n] - senza.buffer[:n]
        attivi = np.flatnonzero(np.any(np.abs(differenza) > 1e-7, axis=1))
        inizio = round(con.secondi(ev.t) * ps.FS)
        lunghezza = len(ps.sorgente("blocco", posato.variante))
        assert 0 <= attivi[0] - inizio <= 3 and attivi[-1] < inizio + lunghezza
        assert np.allclose(differenza[inizio:inizio + lunghezza], ps.spazializza(posato, "A"), atol=1e-6)
        # Viene dalla sua sponda: a sinistra o a destra di chi ascolta.
        sinistra, destra = _energia(differenza)
        assert (sinistra > 3 * destra) if lato_per_a == "sinistra" else (destra > 3 * sinistra), (ev.pos, sinistra, destra)
        if len(provati) == 2:
            break
    assert provati == {"sinistra", "destra"}
    # In tutto il primo incontro ogni blocco suona una volta, al suo istante, e nessuna parata suona per un blocco.
    posati = ps.posa(eventi)
    istanti = sorted(p.t for p in posati if p.ruolo == "blocco")
    assert istanti == sorted(ev.t for _i, ev in _blocchi(risultato))


def test_il_suono_del_controllo_si_sposta_con_la_pallina(partite):
    visti = 0
    for risultato, _nomi in partite[:6]:
        for ev, colpo in _controlli_col_colpo(risultato):
            if ev.dati["trasporto"] != ALTRA_SPONDA:
                continue
            visti += 1
            (posato,) = [p for p in ps.posati_dell_evento(ev) if p.ruolo == "controllo"]
            assert list(posato.tempi) == pytest.approx([0.0, ev.dati["presa"], max(ev.durata, 0.15)])
            assert posato.posizioni == [ev.pos, ev.pos, colpo.pos]
            stereo = ps.spazializza(posato, "A")
            presa = round(ev.dati["presa"] * ps.FS)
            coda = stereo[-round(0.1 * ps.FS):]
            partenza, arrivo = (0, 1) if ev.pos[0] < CENTRO_X else (1, 0)
            prima, dopo = _energia(stereo[:presa]), _energia(coda)
            assert prima[partenza] > 3 * prima[arrivo] and dopo[arrivo] > 3 * dopo[partenza], (ev.n, prima, dopo)
            if visti >= 10:
                return
    assert visti >= 5


# La cronaca.

def _parata(lato, **campi):
    return Evento(n=7, t=1.0, tipo=E.PARATA, fase=E.GIOCO, chi=1, parte="A", pos=(6.0 if lato == "sinistra" else 116.0, 25.0), lato=lato, esito="fermata", **campi)


def _controllo(esito, trasporto, porta_a, pos=(6.0, 25.0)):
    dati = {"valore": 0.8, "prob": [0.01, 0.05, 0.94], "trasporto": trasporto, "porta_a": porta_a, "presa": 0.3}
    return Evento(n=8, t=1.0, tipo=E.CONTROLLO, fase=E.GIOCO, durata=1.2, chi=1, parte="A", pos=pos, lato=lato_di(pos[0], "A"), esito=esito, dati=dati)


def test_la_cronaca_del_blocco_e_del_trasporto():
    nomi = {1: C.Nome("Rossi", "m")}
    assert C.frase(_parata("sinistra"), nomi) == "Rossi blocca la pallina sulla sponda sinistra."
    assert C.frase(_parata("destra", dritto=False), nomi) == "Rossi blocca la pallina sulla sponda destra di rovescio."
    assert C.frase(_parata("sinistra", dritto=True, causa="sporca"), nomi) == "Rossi blocca la pallina sulla sponda sinistra di dritto, ma non è un blocco pulito."
    assert C.frase(_parata("sinistra"), nomi, C.SINTETICA) is None
    attese = {
        (DAL_BLOCCO, (6.0, 26.0)): "Rossi tiene la pallina dove l'ha bloccata.",
        (DAL_BLOCCO, (6.0, 36.0)): "Rossi sposta la pallina lungo la sponda sinistra.",
        (AL_CENTRO, (64.0, 30.0)): "Rossi porta la pallina al centro.",
        (ALTRA_SPONDA, (112.0, 33.0)): "Rossi porta la pallina sulla sponda destra.",
    }
    for (trasporto, porta_a), testo in attese.items():
        assert C.frase(_controllo("riuscito", trasporto, porta_a), nomi) == testo
        assert C.frase(_controllo("riuscito", trasporto, porta_a), nomi, C.TECNICA).startswith(testo + " (secondo ")
        assert C.frase(_controllo("riuscito", trasporto, porta_a), nomi, C.SINTETICA) is None
    assert C.frase(_controllo("recupero", AL_CENTRO, (64.0, 30.0)), nomi) == "Rossi la riprende e la porta al centro."
    assert C.frase(_controllo("recupero", ALTRA_SPONDA, (112.0, 33.0)), nomi) == "Rossi la riprende e la porta sulla sponda destra."
    assert C.frase(_controllo("recupero", DAL_BLOCCO, (6.0, 26.0)), nomi) == "Rossi la riprende."
    # Per chi sta dall'altra parte del tavolo sinistra e destra si ribaltano.
    dall_altra = Evento(n=8, t=1.0, tipo=E.CONTROLLO, fase=E.GIOCO, durata=1.2, chi=1, parte="B", pos=(116.0, 340.0), lato="sinistra", esito="riuscito",
                        dati={"trasporto": ALTRA_SPONDA, "porta_a": (10.0, 335.0), "presa": 0.3})
    assert C.frase(dall_altra, nomi) == "Rossi porta la pallina sulla sponda destra."
    # Senza trasporto, come prima della issue 11, il controllo riuscito si legge soltanto al livello tecnico.
    vecchio = Evento(n=8, t=1.0, tipo=E.CONTROLLO, fase=E.GIOCO, durata=0.8, chi=1, parte="A", pos=(6.0, 25.0), lato="sinistra", esito="riuscito", dati={"valore": 0.8})
    assert C.frase(vecchio, nomi) is None and C.frase(vecchio, nomi, C.TECNICA).startswith("Rossi controlla la pallina.")


def test_la_cronaca_degli_incontri_dice_blocchi_e_trasporti(partite):
    blocchi = trasporti = 0
    for risultato, nomi in partite:
        for _indice, ev in _blocchi(risultato):
            blocchi += 1
            assert C.frase(ev, nomi).startswith(f"{nomi[ev.chi].testo} blocca la pallina sulla sponda {ev.lato}")
        for ev, _colpo in _controlli_col_colpo(risultato):
            testo = C.frase(ev, nomi)
            if ev.esito == "riuscito":
                trasporti += 1
                assert testo.startswith(nomi[ev.chi].testo) and " la pallina " in testo, testo
        righe = C.componi(risultato.momenti, nomi)
        assert not any(" ferma la pallina" in riga for riga in righe)
    assert blocchi >= 1000 and trasporti >= 1000
