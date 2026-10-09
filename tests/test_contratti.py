"""
Test dei contratti della tappa 11, decisione D31 e risposte di Gabriele del 9 ottobre 2026: la
durata proposta, le date al primo del mese e la finestra dei tre mesi, la richiesta e la
probabilità del rinnovo, la buonuscita.
"""

import datetime
import random

import pytest
from aiuti_motore import giocatore

import contratti
import economia
import mondo as modulo_mondo
from modelli import Polisportiva
from mondo import Mondo

OGGI = datetime.datetime(2027, 11, 17, 9, 0)


def _poli(gloria=140):
    p = Polisportiva("Club Contratti", None, OGGI)
    p.gloria = gloria
    return p


@pytest.mark.parametrize("ambizione", [0.0, 50.0, 100.0])
def test_la_durata_proposta_sta_fra_quattro_e_ventiquattro_mesi(ambizione):
    durate = [contratti.durata_proposta(giocatore(1, anni=anni, ambizione=ambizione)) for anni in (9, 15, 20, 30, 40, 50, 60, 70)]
    assert all(4 <= d <= 24 for d in durate)
    assert durate == sorted(durate)


def test_i_giovani_e_gli_ambiziosi_la_vogliono_piu_corta():
    medio = {anni: contratti.durata_proposta(giocatore(1, anni=anni, ambizione=50.0)) for anni in (20, 30, 40, 50)}
    assert medio == {20: 9, 30: 12, 40: 15, 50: 18}
    assert contratti.durata_proposta(giocatore(1, anni=30, ambizione=95.0)) < medio[30] < contratti.durata_proposta(giocatore(1, anni=30, ambizione=5.0))


def test_inizi_e_scadenze_al_primo_del_mese():
    assert contratti.inizio(OGGI) == datetime.datetime(2027, 12, 1)
    assert contratti.inizio(datetime.datetime(2027, 12, 1, 9, 0)) == datetime.datetime(2027, 12, 1)
    assert contratti.scadenza_dopo(OGGI, 3) == datetime.datetime(2028, 3, 1)
    assert contratti.scadenza_dopo(OGGI, 14) == datetime.datetime(2029, 2, 1)
    assert contratti.aggiungi_mesi(datetime.datetime(2028, 3, 1), -3) == datetime.datetime(2027, 12, 1)
    assert contratti.mesi_interi(datetime.datetime(2027, 12, 1), datetime.datetime(2028, 3, 1)) == 3
    assert contratti.mesi_di_calendario(datetime.datetime(2028, 1, 1), datetime.datetime(2028, 1, 31)) == pytest.approx(30 / 30.44)


def test_la_finestra_dei_tre_mesi():
    g = giocatore(2, anni=30)
    assert not contratti.in_finestra(g, OGGI) and contratti.inizio_finestra(g) is None
    contratti.stipula(g, OGGI, 300, 3)
    assert g.contratto_scadenza == datetime.datetime(2028, 3, 1) and g.contratto_stipendio == 300
    assert contratti.inizio_finestra(g) == datetime.datetime(2027, 12, 1)
    assert not contratti.in_finestra(g, datetime.datetime(2027, 11, 30, 9, 0))
    assert contratti.in_finestra(g, datetime.datetime(2027, 12, 1, 9, 0))
    assert contratti.in_finestra(g, datetime.datetime(2028, 2, 29, 9, 0))
    assert not contratti.in_finestra(g, datetime.datetime(2028, 3, 1, 9, 0))
    assert contratti.mesi_al_termine(g, datetime.datetime(2028, 2, 1)) == pytest.approx(29 / 30.44)


def test_il_rinnovo_parte_dalla_scadenza_del_vecchio():
    g = giocatore(3, anni=30)
    contratti.stipula(g, OGGI, 300, 3)
    g.proposte_rinnovo = 2
    contratti.concorda_rinnovo(g, 420, 12)
    assert (g.rinnovo_stipendio, g.rinnovo_scadenza) == (420, datetime.datetime(2029, 3, 1))
    assert contratti.ha_rinnovo(g)
    contratti.subentra_il_rinnovo(g)
    assert (g.contratto_stipendio, g.contratto_scadenza, g.rinnovo_stipendio, g.rinnovo_scadenza, g.proposte_rinnovo) == (420, datetime.datetime(2029, 3, 1), 0, None, 0)


def test_la_richiesta_di_rinnovo_secondo_gloria_fedelta_e_durata():
    g = giocatore(4, anni=30, ambizione=50.0, esperienza=0.0)
    base = economia.stipendio(g)
    pari = _poli()
    pari.gloria = g.gloria_richiesta
    proposta = contratti.durata_proposta(g)
    assert contratti.richiesta_rinnovo(g, pari, proposta) == economia.arrotonda(base)
    assert contratti.richiesta_rinnovo(g, pari, proposta + 5) == economia.arrotonda(base * 1.10)
    g.fedelta = 100.0
    assert contratti.richiesta_rinnovo(g, pari, proposta) == economia.arrotonda(base * 0.75)
    g.fedelta = 0.0
    gloriosa = _poli(gloria=10 * g.gloria_richiesta)
    assert contratti.richiesta_rinnovo(g, gloriosa, proposta) < contratti.richiesta_rinnovo(g, pari, proposta)


def test_la_probabilita_cresce_con_l_offerta_e_la_fedelta_e_la_bandiera_accetta():
    g = giocatore(5, anni=30, ambizione=50.0)
    poli = _poli()
    mesi = contratti.durata_proposta(g)
    richiesta = contratti.richiesta_rinnovo(g, poli, mesi)
    probabilita = [contratti.probabilita_rinnovo(g, poli, int(richiesta * f), mesi) for f in (0.6, 0.85, 1.0, 1.15, 1.4)]
    assert probabilita == sorted(probabilita) and probabilita[0] == 3.0 and probabilita[-1] == 97.0
    assert probabilita[2] == pytest.approx(50.0, abs=2.0)
    g.fedelta = 60.0
    assert contratti.probabilita_rinnovo(g, poli, richiesta, mesi) > probabilita[2]
    g.bandiera, g.fedelta = True, 90.0
    assert contratti.probabilita_rinnovo(g, poli, 50, mesi) == 97.0


def test_la_buonuscita_e_meta_degli_stipendi_che_restano():
    g = giocatore(6, anni=30)
    assert contratti.buonuscita(g, OGGI) == 0
    contratti.stipula(g, datetime.datetime(2027, 12, 1, 9, 0), 220, 10)
    assert g.contratto_scadenza == datetime.datetime(2028, 10, 1)
    giorni = (g.contratto_scadenza - datetime.datetime(2027, 12, 1, 9, 0)).total_seconds() / 86400
    assert contratti.buonuscita(g, datetime.datetime(2027, 12, 1, 9, 0)) == economia.arrotonda(220 * giorni / 30.44 / 2)
    assert contratti.buonuscita(g, datetime.datetime(2028, 10, 1)) == 0


# Il contratto nel mondo: la firma in ogni via d'ingresso, la cancellazione all'uscita.

INIZIO = datetime.datetime(2026, 5, 15, 12, 0)


@pytest.fixture
def mondo():
    random.seed(909)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(40, INIZIO, annuncia=False)
    return m


def _cpu(mondo, ids, gloria=10_000):
    poli = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    poli.gloria = gloria
    poli.cassa = 1_000_000
    for gid in ids:
        mondo._tessera(poli, mondo.giocatori[gid])
    return poli


def _firmato(g, mondo, quando=INIZIO):
    """Vero se il giocatore ha il contratto della firma di oggi: lo stipendio che chiede e la durata che propone."""
    return (g.contratto_stipendio == economia.stipendio(g) and g.contratto_scadenza == contratti.scadenza_dopo(quando, contratti.durata_proposta(g))
            and g.programma == g.indole and g.intensita == "normale" and g.proposte_rinnovo == 0)


def test_la_firma_all_ingaggio_e_al_tesseramento_del_computer(mondo, monkeypatch):
    mia = mondo.fonda_polisportiva("Club di prova")
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    accetta, _p = mondo.offerta(mia, mondo.giocatori[1])
    assert accetta and _firmato(mondo.giocatori[1], mondo)
    cpu = _cpu(mondo, ())
    tesserati, _s, _c = mondo._esegui_logica_cpu_polisportive(INIZIO)
    assert tesserati > 0
    assert all(_firmato(mondo.giocatori[gid], mondo) for gid in cpu.tesserati)


def test_la_firma_allo_scambio_e_agli_acquisti(mondo, monkeypatch):
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    cpu = _cpu(mondo, range(2, 17))
    for gid in cpu.tesserati:
        mondo.giocatori[gid].indice_collettivo_valore = 10.0
    forte = max((g for g in mondo.giocatori.values() if g.appartenenza == "*"), key=lambda g: g.indice_collettivo_valore)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO)[1] == 1
    assert _firmato(forte, mondo) and forte.appartenenza == cpu.nome
    svincolato = next(g for g in mondo.giocatori.values() if g.appartenenza == "*" and g.diario[0]["testo"].startswith("Svincolat"))
    assert svincolato.contratto_scadenza is None and svincolato.contratto_stipendio == 0
    # L'acquisto, l'offerta d'acquisto e l'acquisto del computer firmano un contratto nuovo col compratore.
    mia = mondo.fonda_polisportiva("Club di prova")
    mia.cassa = 1_000_000
    g = mondo.giocatori[5]
    g.contratto_stipendio = 1
    mondo.metti_in_vendita(cpu, g, 500)
    mondo.acquista(mia, g)
    assert _firmato(g, mondo) and g.appartenenza == mia.nome
    altro = mondo.giocatori[6]
    altro.contratto_stipendio = 1
    assert mondo.offerta_d_acquisto(mia, altro, 10_000_000 // 20)
    assert _firmato(altro, mondo)
    terzo = _cpu(mondo, ())
    mondo.metti_in_vendita(mia, altro, 100)
    assert mondo._compra_dal_mercato(terzo, INIZIO)
    assert altro.appartenenza == terzo.nome and _firmato(altro, mondo)


def test_chi_lascia_o_muore_perde_il_contratto(mondo):
    mia = mondo.fonda_polisportiva("Club di prova")
    for gid in (1, 2):
        mondo._tessera(mia, mondo.giocatori[gid])
    g = mondo.giocatori[1]
    g.intensita = "intensa"
    g.programma = "tecnica" if g.indole != "tecnica" else "muro"
    contratti.concorda_rinnovo(g, 999, 12)
    mondo.svincola(mia, g)
    assert (g.contratto_stipendio, g.contratto_scadenza, g.rinnovo_stipendio, g.rinnovo_scadenza) == (0, None, 0, None)
    assert g.programma == g.indole and g.intensita == "normale"
    morto = mondo.giocatori[2]
    mondo._uscita(morto, modulo_mondo.DECESSO, INIZIO, morto.eta)
    assert morto.contratto_scadenza is None and morto.contratto_stipendio == 0
