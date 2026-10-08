"""
Test degli eventi della modalità completa, su trenta incontri con semi fissi: invarianti della
regia, annunci dal punto di vista di chi batte, domanda di pronto alle sole riprese lunghe, falli
con la causa del catalogo e il fischio singolo, goal col fischio doppio, nessun evento di pubblico;
la battuta regolare con una sponda sola prima dello schermo anche quando finisce in porta, il volo
della battuta irregolare secondo la causa, e il fischio nell'istante stesso di una rottura.
"""

import random

import pytest
from aiuti_motore import giocatore

from motore import eventi as E
from motore.eventi import CAUSE, Evento, Tappa
from motore.incontro import COMPLETO, SINGOLARE_3, SINGOLARE_5, Incontro, simula_incontro
from motore.regia import controlla_invarianti
from motore.scambio import Passo
from motore.tavolo import locale_in_assoluto

RIPRESE_LUNGHE = {E.INIZIO_SET, E.TIMEOUT_FINE, E.CAMBIO_CAMPO_FINE, E.SOSTITUZIONE_ATTREZZO}


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


def test_la_battuta_regolare_tocca_una_sponda_prima_dello_schermo(incontri):
    # Regola IBSA 15.3.7 e D25: anche quando finisce in porta, sul corpo o nell'area di porta.
    arrivi = set()
    for risultato in incontri:
        eventi = risultato.eventi
        for indice, evento in enumerate(eventi):
            if evento.tipo == E.BATTUTA and evento.esito == "regolare":
                volo = eventi[indice + 1]
                tipi = [tappa.tipo for tappa in volo.volo]
                prima = tipi[:tipi.index("sotto_schermo")]
                assert sum(1 for tipo in prima if tipo in ("sponda", "curva")) == 1
                arrivi.add(tipi[-1])
    assert {"paletta", "porta"} <= arrivi


def test_le_invarianti_vedono_una_battuta_senza_sponda_e_un_fischio_tardivo():
    battuta = Evento(n=1, t=0.0, tipo=E.BATTUTA, fase=E.GIOCO, esito="regolare")
    tappe = (Tappa(0.0, 63, 25, 450, "partenza"), Tappa(0.4, 5, 183, 400, "sotto_schermo"), Tappa(0.42, 3, 187, 390, "sponda"), Tappa(0.9, 66, 360, 300, "porta"))
    volo = Evento(n=2, t=0.0, tipo=E.VOLO, fase=E.GIOCO, durata=0.9, volo=tappe)
    assert any("sponde prima dello schermo" in problema for problema in controlla_invarianti([battuta, volo]))
    rottura = Evento(n=3, t=1.0, tipo=E.ROTTURA, fase=E.GIOCO)
    cambio = Evento(n=4, t=1.0, tipo=E.SOSTITUZIONE_ATTREZZO, fase=E.GIOCO, durata=30.0)
    fischio = Evento(n=5, t=31.0, tipo=E.FISCHIO, fase=E.GIOCO, fischio=E.SINGOLO)
    assert any("rottura" in problema for problema in controlla_invarianti([rottura, cambio, fischio]))


@pytest.mark.parametrize("colpo", ["battutasx", "battutadx"])
def test_il_volo_della_battuta_irregolare_secondo_la_causa(colpo):
    incontro = Incontro(giocatore(1), giocatore(2), SINGOLARE_3, seme=1, dettaglio=COMPLETO)
    regia = incontro.regia
    battitore = incontro.campo[2]
    for causa in ("battuta_senza_rimbalzo", "battuta_due_rimbalzi", "battuta_strisciata", "out_volo", "schermo_sopra", "battuta_doppio_tocco",
                  "battuta_a_vuoto", "battuta_prima_del_fischio", "battuta_oltre_due_secondi"):
        partenza = locale_in_assoluto(battitore.parte, 75.0 if colpo == "battutasx" else 47.0, 25.0)
        passo = Passo("battuta", battitore, colpo, None, "irregolare", causa, False)
        eventi = []
        fallo = regia._volo_battuta_irregolare(eventi, battitore.id, partenza, passo)
        if causa in ("battuta_a_vuoto", "battuta_prima_del_fischio", "battuta_oltre_due_secondi"):
            # Il fallo è di chi batte, nel momento in cui batte: nessun volo.
            assert eventi == [] and fallo == partenza
            continue
        (volo,) = eventi
        assert controlla_invarianti(eventi) == []
        tipi = [tappa.tipo for tappa in volo.volo]
        prima = tipi[:tipi.index("sotto_schermo")] if "sotto_schermo" in tipi else tipi
        sponde = sum(1 for tipo in prima if tipo in ("sponda", "curva"))
        attese = {"battuta_senza_rimbalzo": 0, "battuta_due_rimbalzi": 2, "battuta_strisciata": 1}
        if causa in attese:
            assert "sotto_schermo" in tipi and sponde == attese[causa], (causa, tipi)
        assert ("sopra_schermo" in tipi) == (causa == "schermo_sopra")
        assert ("terra" in tipi) == (causa == "out_volo")
        assert (volo.dati or {}).get("strisciata", False) == (causa == "battuta_strisciata")
        # Il fallo si segna nell'ultimo punto del volo che sta sul tavolo, lontano da chi batte
        # tranne che nel doppio tocco.
        lontano = abs(fallo[1] - partenza[1])
        assert (lontano < 40) == (causa == "battuta_doppio_tocco"), (causa, fallo)


class _RotturaForzata(Incontro):
    """Una rottura della paletta preparata prima del terzo punto."""

    def _fasce_imprevisti(self, battitore, ricevitore):
        fasce = super()._fasce_imprevisti(battitore, ricevitore)
        if self.set_n == 1 and self.punto_n == 2:
            return [0.0] * 6 + [1.0] + [0.0] * (len(fasce) - 7)
        return fasce


def test_la_rottura_ferma_il_gioco_subito_col_fischio():
    # Regole IBSA 15.9.3 e 15.10.2: il fischio alla rottura, poi il cambio dell'attrezzo e il
    # servizio ripetuto, senza un secondo fischio dopo il cambio.
    viste = 0
    for seme in range(30):
        risultato = _RotturaForzata(giocatore(1), giocatore(2), SINGOLARE_3, seme=seme, dettaglio=COMPLETO).gioca()
        tipi = [e.tipo for e in risultato.eventi]
        if E.ROTTURA not in tipi:
            continue
        viste += 1
        indice = tipi.index(E.ROTTURA)
        rottura, fischio = risultato.eventi[indice], risultato.eventi[indice + 1]
        assert fischio.tipo == E.FISCHIO and fischio.fischio == E.SINGOLO and fischio.t == rottura.t
        assert tipi[indice + 2:indice + 4] == [E.SOSTITUZIONE_ATTREZZO, E.RIPETIZIONE]
        assert controlla_invarianti(risultato.eventi) == []
    assert viste >= 3
