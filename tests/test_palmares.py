"""
Test del palmarès e dell'economia della tappa 12, punti 5.9, 5.11, 9.1 e 9.2 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Le voci nuove nei conti e nei bilanci, con il rimborso nel mese in cui arriva; la gloria che conta le
medaglie e le coppe dei 60 mesi e non quelle prima; la parte del palmarès nella gloria calcolata dalle
costanti; l'importanza; la coppa della sfida che pesa un cinquantesimo di una coppa d'importanza 1; lo
sfoltimento del primo del mese; i punti della classifica e l'ultimo anno; la classifica mondiale con le
vecchie glorie; la voce aggregata dell'anno, che si aggiorna e torna in cima, e si salva.
"""

import datetime
import math
import random

import pytest
from aiuti_motore import giocatore

import palmares
import testi
from costanti import (
    GLORIA_BASE,
    IMPORTANZA_COPPA_SFIDA,
    K_GLORIA_COPPE,
    K_GLORIA_MEDAGLIE,
    K_GLORIA_TESSERATI,
    MASSIMO_VOCI_RICERCA_AGGREGATA,
    QUOTA_GLORIA_ARGENTO_SFIDA,
)
from modelli import CAMPI_AGGREGATA_GIOCATORE, CAMPI_AGGREGATA_POLISPORTIVA, VOCI_CONTI, Giocatore, Polisportiva, annota_aggregata, conti_vuoti
from mondo import DECESSO, Mondo

OGGI = datetime.datetime(2031, 6, 15, 9, 0)


def _poli():
    return Polisportiva("Club Del Palmares", None, OGGI - datetime.timedelta(days=4000))


def test_le_voci_nuove_dei_conti_e_il_bilancio():
    # Le voci della tappa 12, e dalla tappa 13 gli stipendi dello staff.
    assert VOCI_CONTI[-4:] == ("iscrizioni", "premi", "rimborsi", "staff") and set(conti_vuoti()) == set(VOCI_CONTI)
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    poli = _poli()
    mondo.polisportive[poli.nome] = poli
    # L'iscrizione è di maggio, il rimborso arriva a giugno: ciascuno nella voce del suo mese, mai sotto zero.
    poli.conti_del_mese["iscrizioni"] = 30
    rapporto = Mondo.rapporto_vuoto(OGGI)
    mondo._primo_del_mese(datetime.datetime(2031, 6, 1, 9, 0), rapporto)
    poli.conti_del_mese["rimborsi"] += 10
    poli.conti_del_mese["premi"] += 120
    assert poli.bilanci[0]["iscrizioni"] == 30 and poli.bilanci[0]["rimborsi"] == 0
    assert all(v >= 0 for v in poli.conti_del_mese.values())
    testo = testi.bilancio(poli, mondo)
    assert "iscrizioni ai tornei 30 euro" in testo and "premi dei tornei 120 euro" in testo and "rimborsi delle iscrizioni 10 euro" in testo


def test_l_importanza_e_la_coppa_della_sfida():
    assert palmares.punti_medaglia("oro") == 30 and palmares.punti_medaglia("oro", 4) == 120 and palmares.punti_medaglia("legno", 2) == 2
    assert palmares.punti_coppa("oro", IMPORTANZA_COPPA_SFIDA) * 50 == pytest.approx(palmares.punti_coppa("oro"))
    assert palmares.punti_coppa("oro", 3) == 300


def test_perdere_tante_sfide_non_conviene():
    # La decisione 3 di Gabriele del 14 ottobre 2026: la coppa d'argento di una sfida vale nella gloria una
    # piccola parte di quella d'oro. Novanta sfide in cinque anni, tutte vinte, tutte perse o nessuna.
    oro = palmares.punti_coppa("oro", IMPORTANZA_COPPA_SFIDA)
    vince, perde, nessuna = _poli(), _poli(), _poli()
    for numero in range(90):
        data = OGGI - datetime.timedelta(days=20 * numero)
        palmares.aggiungi(vince, data, punti_coppe=oro)
        palmares.aggiungi(perde, data, punti_coppe=oro * QUOTA_GLORIA_ARGENTO_SFIDA)
    for poli in (vince, perde, nessuna):
        poli.aggiorna_gloria({}, set(), OGGI)
    assert vince.gloria == int(GLORIA_BASE + math.sqrt(90 * oro) * K_GLORIA_COPPE)
    assert nessuna.gloria < perde.gloria and perde.gloria - nessuna.gloria < (vince.gloria - nessuna.gloria) / 2


def test_la_gloria_conta_i_60_mesi():
    poli = _poli()
    palmares.aggiungi(poli, OGGI, punti_medaglie=30.0)
    palmares.aggiungi(poli, OGGI - datetime.timedelta(days=59 * 30.4), punti_medaglie=15.0, punti_coppe=100.0)
    palmares.aggiungi(poli, OGGI - datetime.timedelta(days=61 * 30.4), punti_medaglie=1000.0, punti_coppe=1000.0)
    assert palmares.somma_finestra(poli, OGGI) == (45.0, 100.0)
    vuota = _poli()
    poli.aggiorna_gloria({}, set(), OGGI)
    vuota.aggiorna_gloria({}, set(), OGGI)
    assert vuota.gloria == GLORIA_BASE
    atteso = int(GLORIA_BASE + math.sqrt(100.0) * K_GLORIA_COPPE + math.sqrt(45.0) * K_GLORIA_MEDAGLIE)
    assert poli.gloria == atteso


def test_la_parte_del_palmares_nella_gloria():
    giocatori = {}
    poli = _poli()
    for gid in range(1, 16):
        g = giocatore(gid, valore=14.0, anni=28)
        g.appartenenza = poli.nome
        giocatori[gid] = g
        poli.tesserati.append(gid)
    poli.aggiorna_gloria(giocatori, set(), OGGI)
    senza = poli.gloria
    palmares.aggiungi(poli, OGGI, punti_medaglie=840.0, punti_coppe=260.0)
    poli.aggiorna_gloria(giocatori, set(), OGGI)
    parte = math.sqrt(840.0) * K_GLORIA_MEDAGLIE + math.sqrt(260.0) * K_GLORIA_COPPE
    assert poli.gloria == int(senza + parte) or poli.gloria == int(senza + parte) + 1
    assert senza > GLORIA_BASE + K_GLORIA_TESSERATI - 1


def test_lo_sfoltimento_del_primo_del_mese():
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    poli = _poli()
    mondo.polisportive[poli.nome] = poli
    poli.palmares_recente = {"2026-05": [30.0, 0.0], "2026-06": [15.0, 0.0], "2031-05": [5.0, 2.0]}
    mondo._primo_del_mese(datetime.datetime(2031, 6, 1, 9, 0), Mondo.rapporto_vuoto(OGGI))
    assert set(poli.palmares_recente) == {"2031-05"}
    assert palmares.nella_finestra("2026-07", OGGI) and not palmares.nella_finestra("2026-06", OGGI)


def test_i_punti_della_classifica_e_l_ultimo_anno():
    assert [palmares.punti_classifica(p) for p in (1, 2, 3, 4, 5, 8, 9, 16, 17, 32, 33, 200)] == [100, 70, 50, 40, 25, 25, 12, 12, 5, 5, 1, 1]
    assert palmares.punti_classifica(1, 4) == 400
    g = giocatore(1)
    palmares.aggiungi_punti(g, OGGI.date() - datetime.timedelta(days=400), 50.0)
    palmares.aggiungi_punti(g, OGGI.date() - datetime.timedelta(days=10), 25.0)
    assert g.punti_mondiali == 75.0 and palmares.punti_dell_anno(g, OGGI.date()) == 25.0
    palmares.sfoltisci_punti(g, OGGI.date())
    assert len(g.punti_recenti) == 1 and g.punti_mondiali == 75.0


def test_la_classifica_mondiale_per_sempre_con_le_vecchie_glorie():
    random.seed(7)
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = OGGI
    mondo.crea_giocatori_casuali(6, OGGI, annuncia=False)
    uomini = [g for g in mondo.giocatori.values() if g.sesso == "m"]
    donne = [g for g in mondo.giocatori.values() if g.sesso == "f"]
    if not uomini or not donne:
        pytest.skip("Il seme non dà tutti e due i sessi.")
    uomini[0].punti_mondiali, uomini[0].ori = 300.0, 2
    uomini[0].titoli = [{"data": "2031-06-01", "torneo": "Campionato mondiale maschile", "posto": 1, "mondiale": True}]
    if len(uomini) > 1:
        uomini[1].punti_mondiali = 120.0
    donne[0].punti_mondiali = 50.0
    mondo._uscita(uomini[0], DECESSO, OGGI, uomini[0].eta)
    classifica = palmares.classifica_mondiale(mondo, "m")
    assert classifica[0]["punti"] == 300.0 and classifica[0]["titoli"] == 1 and not classifica[0]["vivo"]
    assert all(r["id"] != donne[0].id for r in classifica)
    assert palmares.classifica_mondiale(mondo, "f")[0]["id"] == donne[0].id
    # La revisione del 14 ottobre 2026: fra i vivi, come fra le vecchie glorie, i titoli mondiali sono i
    # mondiali vinti; un argento al mondiale sta nei titoli del giocatore ma non è un titolo mondiale.
    if len(uomini) > 1:
        uomini[1].titoli = [{"data": "2031-06-01", "torneo": "Campionato mondiale maschile", "posto": 2, "mondiale": True}]
        assert next(r for r in palmares.classifica_mondiale(mondo, "m") if r["id"] == uomini[1].id)["titoli"] == 0


def test_la_voce_aggregata_dell_anno():
    diario = []
    primo = OGGI - datetime.timedelta(days=100)
    annota_aggregata(diario, primo, CAMPI_AGGREGATA_GIOCATORE, tornei=1, incontri=4, vinti=3, ori=1)
    for n in range(5):
        diario.insert(0, {"data": primo + datetime.timedelta(days=n + 1), "testo": f"Voce {n}"})
    voce = annota_aggregata(diario, OGGI, CAMPI_AGGREGATA_GIOCATORE, tornei=1, incontri=2, vinti=0, bronzi=2, sfide=3, sfide_vinte=1)
    assert diario[0] is voce and len(diario) == 6
    assert (voce["tornei"], voce["incontri"], voce["vinti"], voce["ori"], voce["bronzi"], voce["da"], voce["data"]) == (2, 6, 3, 1, 2, primo, OGGI)
    assert testi.voce_diario(voce) == (f"Nel 2031, dal {testi.data_breve(primo)} al {testi.data_breve(OGGI)}, ha giocato 2 tornei, 6 incontri, 3 vinti, "
                                       "con un oro e 2 bronzi, e 3 sfide, 1 vinta.")
    # Un anno nuovo apre una voce nuova; oltre le prime venti voci la ricerca non arriva.
    annota_aggregata(diario, datetime.datetime(2032, 1, 2, 9, 0), CAMPI_AGGREGATA_GIOCATORE, tornei=1)
    assert diario[0]["anno"] == 2032 and diario[1] is voce
    lontano = [{"data": OGGI, "testo": "x"} for _ in range(MASSIMO_VOCI_RICERCA_AGGREGATA)] + [voce]
    annota_aggregata(lontano, OGGI, CAMPI_AGGREGATA_GIOCATORE, tornei=1)
    assert lontano[0] is not voce and lontano[0]["tornei"] == 1
    # La voce si salva e si rilegge, nel diario del giocatore e in quello della polisportiva.
    g = giocatore(9)
    g.diario = diario
    riletto = Giocatore.da_dizionario(g.a_dizionario())
    assert riletto.diario[1] == voce
    poli = _poli()
    annota_aggregata(poli.diario, OGGI, CAMPI_AGGREGATA_POLISPORTIVA, iscrizioni=12, tornei=3, ori=1, premi=240, sfide=2, sfide_vinte=1, coppe_oro=1)
    assert Polisportiva.da_dizionario(poli.a_dizionario()).diario[0] == poli.diario[0]
    assert "12 iscrizioni ai tornei, 3 tornei conclusi, medaglie: un oro, premi per 240 euro, 2 sfide, 1 vinta, 1 coppa d'oro" in testi.voce_diario(poli.diario[0])


def test_i_campi_del_palmares_si_salvano_e_si_controllano():
    g = giocatore(3)
    g.tornei_giocati, g.punti_mondiali = 4, 125.0
    g.punti_recenti = [[OGGI.toordinal(), 100.0]]
    g.titoli = [{"data": "2031-06-01", "torneo": "Coppa", "posto": 2, "mondiale": False}]
    riletto = Giocatore.da_dizionario(g.a_dizionario())
    assert (riletto.tornei_giocati, riletto.punti_mondiali, riletto.punti_recenti, riletto.titoli) == (4, 125.0, g.punti_recenti, g.titoli)
    for campo, valore in (("tornei_giocati", -1), ("punti_recenti", [[1, -2.0]]), ("titoli", [{"data": "x"}])):
        with pytest.raises(ValueError, match=campo):
            Giocatore.da_dizionario(dict(g.a_dizionario(), **{campo: valore}))
    poli = _poli()
    poli.palmares_recente = {"2031-06": [30.0, 2.0]}
    assert Polisportiva.da_dizionario(poli.a_dizionario()).palmares_recente == {"2031-06": [30.0, 2.0]}
    with pytest.raises(ValueError, match="palmares_recente"):
        Polisportiva.da_dizionario(dict(poli.a_dizionario(), palmares_recente={"giugno": [1.0, 1.0]}))
