"""
Test del campionato mondiale annuale per sesso, tappa 12, punto 5.8 del progetto e risposta 10 di Gabriele.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
La convocazione dei migliori per i punti dell'ultimo anno, fino a 32, con la parità al trentaduesimo
posto decisa dal punteggio di classe; i convocati gratis, senza la data del ritmo; l'iscrizione che si
sovrappone annullata col rimborso; l'infortunato sostituito al sorteggio; il convocato tolto a mano
che lascia il posto al seguente; il mondiale non disputato sotto il minimo di 8, che l'albo ricorda.
"""

import datetime

import pytest
from aiuti_calendario import apri, mondo_di_prova, polisportiva

import classe
import iscrizioni
import palmares
from mondo import Mondo

APERTURA = datetime.datetime(2026, 11, 30, 9, 0)
MONDIALE = "Campionato mondiale maschile"


def _con_punti(uomini):
    mondo = mondo_di_prova(uomini, 2, data=APERTURA)
    for gid in range(1, uomini + 1):
        palmares.aggiungi_punti(mondo.giocatori[gid], APERTURA.date() - datetime.timedelta(days=30), float(1000 - 10 * gid))
    return mondo


def test_la_convocazione_con_la_parita_al_trentaduesimo():
    mondo = _con_punti(40)
    # Il 32 e il 33 a pari punti: passa chi ha il punteggio di classe più alto.
    g32, g33 = mondo.giocatori[32], mondo.giocatori[33]
    g32.punti_recenti = [list(v) for v in g33.punti_recenti]
    g32.punti_recenti[0][1] = g33.punti_recenti[0][1] = 675.0
    if classe.punteggio(g32) > classe.punteggio(g33):
        g32.esperienza, g33.esperienza = 0.0, 20.0
    # Punti vecchi di più di un anno non contano.
    mondo.giocatori[40].punti_recenti = [[APERTURA.date().toordinal() - 400, 5000.0]]
    ed = apri(mondo, APERTURA, MONDIALE)[0]
    ids = ed.ids()
    assert len(ids) == 32 and set(ids) == set(range(1, 32)) | {33}
    assert all(iscritto["pagato"] == 0 and iscritto["origine"] == "qualificato" for iscritto in ed.iscritti)
    assert ed.data_inizio == datetime.date(2026, 12, 10)


def test_l_iscrizione_che_si_sovrappone_si_annulla_col_rimborso():
    mondo = _con_punti(32)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=100, ids=(1,))
    g1 = mondo.giocatori[1]
    rapporto = Mondo.rapporto_vuoto(APERTURA)
    sabati = apri(mondo, APERTURA, "Open maschile del sabato")
    vicino = next(ed for ed in sabati if ed.data_inizio == datetime.date(2026, 12, 12))
    iscrizioni.iscrivi(mondo, vicino.id, g1, poli)
    assert poli.cassa == 90
    apri(mondo, APERTURA, MONDIALE, rapporto=rapporto)
    assert 1 not in vicino.ids() and poli.cassa == 100 and poli.conti_del_mese["rimborsi"] == 10
    assert rapporto["tuoi_qualificati"] == 1 and any("convocato" in n for n in rapporto["notizie"])
    assert g1.prossimo_torneo is None


def test_l_infortunato_sostituito_e_il_tolto_a_mano():
    mondo = _con_punti(36)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=100, ids=(2,))
    ed = apri(mondo, APERTURA, MONDIALE)[0]
    iscrizioni.togli(mondo, ed.id, mondo.giocatori[2], poli)
    assert 2 not in ed.ids() and 33 in ed.ids() and len(ed.ids()) == 32
    fermo = mondo.giocatori[5]
    fermo.infortunato, fermo.infortunio_sede = True, "schiena"
    inizio = datetime.datetime(2026, 12, 10, 9, 0)
    mondo.datetime_corrente_simulazione = inizio
    mondo.calendario.sorteggi(mondo, inizio, Mondo.rapporto_vuoto(inizio))
    torneo = mondo.calendario.tornei[0]
    assert 5 not in torneo.iscritti and 34 in torneo.iscritti and len(torneo.iscritti) == 32
    # I convocati non toccano la data del ritmo.
    assert all(mondo.giocatori[gid].prossimo_torneo is None for gid in torneo.iscritti)


def test_il_mondiale_non_disputato_sotto_il_minimo():
    mondo = _con_punti(6)
    ed = apri(mondo, APERTURA, MONDIALE)[0]
    assert len(ed.ids()) == 6
    inizio = datetime.datetime(2026, 12, 10, 9, 0)
    mondo.datetime_corrente_simulazione = inizio
    rapporto = Mondo.rapporto_vuoto(inizio)
    mondo.calendario.sorteggi(mondo, inizio, rapporto)
    assert not mondo.calendario.tornei and rapporto["edizioni_annullate"] == 1
    voce = mondo.calendario.albo.voci[0]
    assert voce[0] == "modello_8" and voce[6] == 0 and voce[8] == [] and voce[7] == 6


@pytest.mark.parametrize("sesso", ["m", "f"])
def test_la_classifica_dell_anno_per_sesso(sesso):
    mondo = _con_punti(5)
    ordinati = iscrizioni.classifica_dell_anno(mondo, sesso, APERTURA.date())
    assert all(g.sesso == sesso for g in ordinati)
    if sesso == "m":
        assert [g.id for g in ordinati] == [1, 2, 3, 4, 5]
