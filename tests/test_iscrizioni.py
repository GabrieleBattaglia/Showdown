"""
Test delle iscrizioni ai tornei, tappa 12, punti 5.3, 5.4 e 5.7 del progetto e risposte 2, 3 e 19 di Gabriele.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
La scelta nella finestra contata dalla data del ritmo, con la più importante, poi la più vicina, poi
il proprio sesso; lo scarto fra 58 e 64 giorni; il computer con la cassa al limite; la soglia del
carico per età; i liberi gratis; l'automatica dell'utente e la cassa che non basta, contata una volta;
la regola dei due mesi, con la data aggiornata al sorteggio e non toccata da un'iscrizione tolta né da
un'edizione annullata; l'iscrizione a mano senza il limite, e l'automatica che dopo aspetta i suoi due
mesi; la sovrapposizione rifiutata col nome dell'altro impegno.
"""

import datetime

import pytest
from aiuti_calendario import OGGI, apri, iscrivi_tutti, mondo_di_prova, polisportiva

import iscrizioni
from mondo import Mondo

MARTEDI, SABATO, GP = "Open maschile del martedì", "Open maschile del sabato", "Gran Premio maschile"


def _automatiche(mondo, data):
    rapporto = Mondo.rapporto_vuoto(data)
    mondo.datetime_corrente_simulazione = data
    iscrizioni.automatiche(mondo, mondo.calendario, data, rapporto)
    return rapporto


def _dove(mondo, gid):
    return [ed.nome for ed in mondo.calendario.edizioni if gid in ed.ids()]


def test_la_scelta_nella_finestra_dal_prossimo_torneo():
    mondo = mondo_di_prova(3, 1)
    apri(mondo, OGGI, MARTEDI, SABATO, GP, "Open misto del mese", "Open femminile del giovedì")
    mondo.giocatori[2].prossimo_torneo = datetime.datetime(2026, 10, 10, 9, 0)
    mondo.giocatori[3].prossimo_torneo = datetime.datetime(2026, 10, 18, 9, 0)
    _automatiche(mondo, OGGI)
    # Senza data la finestra va da domani al 13: tre open d'importanza 1, e vince il più vicino, quello del 6.
    assert _dove(mondo, 1) == [MARTEDI] and next(ed for ed in mondo.calendario.edizioni if 1 in ed.ids()).data_inizio == datetime.date(2026, 10, 6)
    # Con la data al 10 la finestra arriva al 17: il Gran Premio del 15, più importante, batte gli open del 10 e del 13.
    assert _dove(mondo, 2) == [GP]
    # Con la data al 18 non è ancora in attesa.
    assert _dove(mondo, 3) == []
    # La donna: l'open femminile e l'aperto misto cominciano tutti e due l'8, e vince il proprio sesso.
    assert _dove(mondo, 4) == ["Open femminile del giovedì"]
    # L'11 il terzo entra in attesa, e dalla sua data, il 18, il primo è l'open del 20.
    undici = datetime.datetime(2026, 10, 11, 9, 0)
    apri(mondo, undici, MARTEDI, SABATO, GP)
    _automatiche(mondo, undici)
    assert next(ed for ed in mondo.calendario.edizioni if 3 in ed.ids()).data_inizio == datetime.date(2026, 10, 20)


def test_lo_scarto_della_data_del_ritmo():
    g = mondo_di_prova(1, 0).giocatori[1]
    distanze = set()
    for id_edizione in range(1, 200):
        g.prossimo_torneo = None
        iscrizioni.aggiorna_ritmo(g, datetime.date(2026, 10, 6), id_edizione)
        distanze.add((g.prossimo_torneo.date() - datetime.date(2026, 10, 6)).days)
    assert distanze == set(range(58, 65))
    # La data non torna mai indietro.
    g.prossimo_torneo = datetime.datetime(2027, 6, 1, 9, 0)
    iscrizioni.aggiorna_ritmo(g, datetime.date(2026, 10, 6), 5)
    assert g.prossimo_torneo == datetime.datetime(2027, 6, 1, 9, 0)


def test_il_computer_paga_se_la_cassa_resta_sopra_un_mese_di_stipendi():
    mondo = mondo_di_prova(2, 0)
    poli = polisportiva(mondo, "PoliTeam01 Prova", cassa=0, ids=(1, 2))
    monte = mondo.monte_stipendi(poli)
    apri(mondo, OGGI, MARTEDI)
    poli.cassa = monte + 10
    _automatiche(mondo, OGGI)
    assert sum(1 for gid in (1, 2) if _dove(mondo, gid)) == 1 and poli.cassa == monte and poli.conti_del_mese["iscrizioni"] == 10


def test_la_soglia_del_carico_scende_con_l_eta():
    assert iscrizioni.soglia_carico(30) == 0.15 and iscrizioni.soglia_carico(45) == 0.15
    assert iscrizioni.soglia_carico(55) == pytest.approx(0.10) and iscrizioni.soglia_carico(65) == 0.05 and iscrizioni.soglia_carico(80) == 0.05
    mondo = mondo_di_prova(2, 0)
    giovane, anziano = mondo.giocatori[1], mondo.giocatori[2]
    giovane.eta, anziano.eta = 30 * 108, 62 * 108
    for g in (giovane, anziano):
        g.costanza = 0.5 + 0.09
    apri(mondo, OGGI, MARTEDI)
    _automatiche(mondo, OGGI)
    assert _dove(mondo, 1) and not _dove(mondo, 2)


def test_i_liberi_gratis_e_la_regola_dei_due_mesi():
    mondo = mondo_di_prova(4, 0)
    edizioni = apri(mondo, OGGI, MARTEDI)
    _automatiche(mondo, OGGI)
    assert all(iscritto["pagato"] == 0 and iscritto["origine"] == "libero" for iscritto in edizioni[0].iscritti) and len(edizioni[0].iscritti) == 4
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    # Dopo il sorteggio la data del ritmo è fra due mesi: niente iscrizione all'open seguente.
    apri(mondo, martedi, MARTEDI)
    _automatiche(mondo, martedi)
    assert not any(_dove(mondo, gid) for gid in range(1, 5))


def test_l_automatica_dell_utente_e_la_cassa_che_non_basta():
    mondo = mondo_di_prova(3, 0)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=15, ids=(1, 2, 3))
    mondo.giocatori[3].iscrizione_automatica = False
    apri(mondo, OGGI, MARTEDI)
    rapporto = _automatiche(mondo, OGGI)
    assert rapporto["tue_iscrizioni"] == 1 and rapporto["tue_iscrizioni_saltate"] == 1 and poli.cassa == 5
    assert mondo.giocatori[1].diario[0]["testo"].startswith("Iscritto in automatico a ")
    # Il giorno dopo la stessa edizione non si conta di nuovo; il terzo, con l'automatica spenta, non entra mai.
    rapporto = _automatiche(mondo, OGGI)
    assert rapporto["tue_iscrizioni_saltate"] == 0 and not _dove(mondo, 3)


def test_la_data_del_ritmo_non_si_tocca_togliendo_o_annullando():
    mondo = mondo_di_prova(2, 0)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=100, ids=(1, 2))
    ed = apri(mondo, OGGI, MARTEDI)[1]
    iscrizioni.iscrivi(mondo, ed.id, mondo.giocatori[1], poli)
    assert poli.cassa == 90 and poli.conti_del_mese["iscrizioni"] == 10
    assert iscrizioni.togli(mondo, ed.id, mondo.giocatori[1], poli) == 10
    assert poli.cassa == 100 and poli.conti_del_mese["rimborsi"] == 10 and mondo.giocatori[1].prossimo_torneo is None
    with pytest.raises(ValueError, match="non è iscritto"):
        iscrizioni.togli(mondo, ed.id, mondo.giocatori[1], poli)


def test_a_mano_senza_il_limite_e_l_automatica_che_poi_aspetta():
    mondo = mondo_di_prova(4, 0)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1,))
    g = mondo.giocatori[1]
    g.iscrizione_automatica = False
    g.prossimo_torneo = OGGI + datetime.timedelta(days=50)
    prima, seconda = apri(mondo, OGGI, MARTEDI)
    iscrizioni.iscrivi(mondo, prima.id, g, poli)
    iscrizioni.iscrivi(mondo, seconda.id, g, poli)
    iscrivi_tutti(prima, mondo, (2, 3, 4))
    martedi = OGGI + datetime.timedelta(days=1)
    mondo.calendario.sorteggi(mondo, martedi, Mondo.rapporto_vuoto(martedi))
    # A mano la regola dei due mesi non c'è; l'automatica dopo il sorteggio aspetta comunque i suoi due mesi.
    assert 58 <= (g.prossimo_torneo.date() - prima.data_inizio).days <= 64


def test_la_sovrapposizione_rifiutata_col_nome_dell_altro_impegno():
    mondo = mondo_di_prova(1, 0)
    poli = polisportiva(mondo, "Club Di Prova", cpu=False, cassa=1000, ids=(1,))
    g = mondo.giocatori[1]
    gp = apri(mondo, OGGI, GP)[0]
    martedi = apri(mondo, OGGI, MARTEDI)
    sabato = apri(mondo, datetime.datetime(2026, 10, 10, 9, 0), SABATO)
    mondo.datetime_corrente_simulazione = OGGI
    iscrizioni.iscrivi(mondo, gp.id, g, poli)
    vicino = next(ed for ed in martedi if ed.data_inizio == datetime.date(2026, 10, 13))
    problema = iscrizioni.problema_iscrizione(mondo, vicino.id, g, poli)
    assert problema and "Gran Premio maschile" in problema and "negli stessi giorni" in problema
    lontano = next(ed for ed in sabato if ed.data_inizio == datetime.date(2026, 10, 24))
    assert iscrizioni.problema_iscrizione(mondo, lontano.id, g, poli) is None
    # I rifiuti per la cassa, per chi non è tuo e per chi non è idoneo.
    poli.cassa = 3
    assert "La cassa di Club Di Prova ha 3 euro" in iscrizioni.problema_iscrizione(mondo, lontano.id, g, poli)
    donne = apri(mondo, OGGI, "Open femminile del giovedì")
    poli.cassa = 1000
    assert "non può giocare" in iscrizioni.problema_iscrizione(mondo, donne[0].id, g, poli)
    estraneo = mondo_di_prova(2, 0).giocatori[2]
    assert "non è tesserato" in iscrizioni.problema_iscrizione(mondo, lontano.id, estraneo, poli)
