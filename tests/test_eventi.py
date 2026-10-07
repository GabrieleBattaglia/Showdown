"""
Test degli eventi della modalità completa, su trenta incontri con semi fissi: invarianti della
regia, annunci dal punto di vista di chi batte, domanda di pronto alle sole riprese lunghe, falli
con la causa del catalogo e il fischio singolo, goal col fischio doppio, nessun evento di pubblico.
"""

import random

import pytest
from aiuti_motore import giocatore

from motore import eventi as E
from motore.eventi import CAUSE
from motore.incontro import COMPLETO, SINGOLARE_3, SINGOLARE_5, simula_incontro
from motore.regia import controlla_invarianti

RIPRESE_LUNGHE = {E.INIZIO_SET, E.TIMEOUT_FINE, E.CAMBIO_CAMPO_FINE, E.SOSTITUZIONE_ATTREZZO, E.SOSTITUZIONE}


@pytest.fixture(scope="module")
def incontri():
    rng = random.Random(8)
    risultati = []
    for seme in range(30):
        a = giocatore(1, valore=rng.uniform(6, 30), mancino=rng.random() < 0.2, giocorapido=rng.random() < 0.3, temperamento=rng.uniform(0, 100))
        b = giocatore(2, valore=rng.uniform(6, 30), ambidestro=rng.random() < 0.3, cambiovelocita=rng.random() < 0.3, sesso="f")
        risultati.append(simula_incontro(a, b, SINGOLARE_5 if seme % 3 == 0 else SINGOLARE_3, seme=seme, dettaglio=COMPLETO))
    return risultati


def test_le_invarianti_della_regia(incontri):
    for risultato in incontri:
        assert controlla_invarianti(risultato.eventi) == []
        assert risultato.durata_simulata == pytest.approx(max(e.t + e.durata for e in risultato.eventi), abs=5.0)


def test_l_annuncio_dal_punto_di_vista_di_chi_batte(incontri):
    for risultato in incontri:
        eventi = risultato.eventi
        numero_atteso = None
        for indice, evento in enumerate(eventi):
            if evento.tipo == E.INIZIO_SET:
                numero_atteso = 1
            elif evento.tipo == E.ANNUNCIO:
                battuta = next(e for e in eventi[indice:] if e.tipo == E.BATTUTA)
                a, b = evento.punteggio
                visto = (a, b) if battuta.parte == "A" else (b, a)
                assert evento.dati["punteggio_visto"] == visto
                assert evento.dati["battitore"] == battuta.chi
                assert evento.dati["numero_servizio"] == numero_atteso
            elif evento.tipo == E.PUNTO:
                numero_atteso = 2 if numero_atteso == 1 else 1
            elif evento.tipo == E.PENALITA and numero_atteso is None:
                continue


def test_la_domanda_di_pronto_solo_alle_riprese_lunghe(incontri):
    domande = 0
    for risultato in incontri:
        lunga = False
        attesa = vista = None
        for evento in risultato.eventi:
            if evento.tipo in RIPRESE_LUNGHE:
                lunga = True
            elif evento.tipo == E.ANNUNCIO:
                attesa, vista = lunga, False
            elif evento.tipo == E.DOMANDA_PRONTO:
                assert attesa, f"Domanda di pronto dopo una ripresa breve, evento {evento.n}."
                vista = True
                domande += 1
            elif evento.tipo == E.BATTUTA:
                assert vista == attesa, f"Ripresa lunga senza domanda di pronto, evento {evento.n}."
                lunga = False
    assert domande > 60


def test_falli_e_goal_con_causa_chiamata_e_fischio(incontri):
    falli = goal = 0
    for risultato in incontri:
        eventi = risultato.eventi
        for indice, evento in enumerate(eventi):
            if evento.tipo == E.FALLO:
                falli += 1
                assert evento.causa in CAUSE and evento.chiamata == CAUSE[evento.causa].chiamata
                assert evento.fischio == E.SINGOLO and evento.punti == 1
                seguenti = eventi[indice + 1:indice + 4]
                assert [e.tipo for e in seguenti[:2]] == [E.FISCHIO, E.CHIAMATA]
                assert seguenti[0].fischio == E.SINGOLO and seguenti[1].chiamata == evento.chiamata
            elif evento.tipo == E.GOAL:
                goal += 1
                assert evento.fischio == E.DOPPIO and evento.punti == 2 and evento.chiamata == "goal"
                assert eventi[indice + 1].tipo == E.FISCHIO and eventi[indice + 1].fischio == E.DOPPIO
    assert falli > 100 and goal > 100


def test_nessun_evento_di_pubblico_e_tipi_noti(incontri):
    for risultato in incontri:
        for evento in risultato.eventi:
            assert evento.tipo in E.TIPI
            assert "PUBBLICO" not in evento.tipo and "APPLAUSO" not in evento.tipo


def test_lati_e_distanze_visti_da_chi_agisce(incontri):
    for risultato in incontri:
        for evento in risultato.eventi:
            if evento.tipo == E.PARATA and evento.esito == "fermata":
                assert evento.distanza <= 40
            if evento.tipo == E.COLPO:
                assert 25 <= evento.distanza <= 40
