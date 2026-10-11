"""
Test dell'allenamento della tappa 11, decisione D31: il costo tarato sul valore, con l'integrale e
la sua inversa, la curva d'età e lo sconto degli ipovedenti, il solo tetto del totale, il calo dei
livelli alti e l'oblio dell'apprendista, il riempimento a livello della spesa secondo il programma,
e chi si allena e chi no.
"""

import datetime
import math

import pytest
from aiuti_motore import giocatore

import allenamento as al
import valore
from costanti import CRESCITA_DEL_COSTO, MAX_TOTALE_PRECISIONE_RESISTENZA, MAX_TOTALE_SKILL_GIOCO, TRATTI_ALLENAMENTO

OGGI = datetime.datetime(2026, 5, 4, 9, 0)


def _normale(gid=1, anni=25, **altro):
    """Un giocatore senza tratti rari, a 25 anni, con le caratteristiche di gioco a 8 e le fisiche a 1,5, salvo quel che si indica."""
    parametri = {"valore": 8.0, "fisico": 1.5, "talento": False, "apprendista_rapido": False, "maturazione": None} | altro
    return giocatore(gid, anni=anni, **parametri)


def test_integrale_e_inversa_coerenti():
    g = _normale()
    for c in ("precisione", "triplaspondasx", "chiusurasx", "difesa"):
        arrivo = al.totale_con(g, c, 137.0)
        assert al.costo_fra(g, c, al.totale(g, c), arrivo) == pytest.approx(137.0)
        spesa = al.anteprima(g, c, 137.0)
        assert spesa.a == pytest.approx(arrivo) and spesa.punti == pytest.approx(137.0)


def test_duecento_punti_rendono_come_due_volte_cento():
    a, b = _normale(), _normale()
    a.punti_allenamento = b.punti_allenamento = 200.0
    al.spendi(a, "chiusurasx", 200.0)
    al.spendi(b, "chiusurasx", 100.0)
    al.spendi(b, "chiusurasx", 100.0)
    assert a.chiusurasx_allenata == pytest.approx(b.chiusurasx_allenata)
    assert a.punti_allenamento == pytest.approx(0.0) and b.punti_allenamento == pytest.approx(0.0)


@pytest.mark.parametrize("mano", [{}, {"mancino": True}, {"ambidestro": True}])
def test_stesso_valore_per_punto_a_pari_livello_relativo(mano):
    # Ogni punto compra la stessa somma pesata in tutte le caratteristiche allo stesso livello relativo, D31.
    g = giocatore(3, valore=12.0, fisico=3.0, anni=25, talento=False, apprendista_rapido=False, maturazione=None, **mano)
    resa = []
    for c in ("precisione", "triplaspondasx", "chiusurasx", "chiusuradx", "bloccosx"):
        prova = giocatore(3, valore=12.0, fisico=3.0, anni=25, talento=False, apprendista_rapido=False, maturazione=None, **mano)
        prima = valore.somma_pesata(prova)
        # Una spesa piccola: in una grande il livello sale, e con lui il prezzo, più in fretta dove il peso è piccolo.
        prova.punti_allenamento = 0.2
        al.spendi(prova, c, 0.2)
        resa.append((valore.somma_pesata(prova) - prima) / 0.2)
    assert al.livello_relativo(g, "precisione") == pytest.approx(al.livello_relativo(g, "chiusurasx"))
    for r in resa[1:]:
        assert r == pytest.approx(resa[0], rel=1e-3)


def test_la_precisione_sale_piano_e_la_tripla_sponda_in_fretta():
    g = _normale()
    assert al.costo_del_prossimo_punto(g, "precisione") > 10 * al.costo_del_prossimo_punto(g, "triplaspondasx")


@pytest.mark.parametrize(("anni", "atteso"), [(9, 1.17), (17, 1.0), (25, 0.87), (30, 0.81), (50, 0.62), (75, 0.48)])
def test_la_curva_d_eta(anni, atteso):
    assert al.efficacia(_normale(anni=anni)) == pytest.approx(atteso, abs=0.005)


def test_lo_sconto_solo_sulle_caratteristiche_di_gioco_degli_ipovedenti():
    vedente, ipovedente = _normale(), _normale(ipovedente=True)
    assert al.costo_del_prossimo_punto(ipovedente, "difesa") == pytest.approx(0.93 * al.costo_del_prossimo_punto(vedente, "difesa"))
    assert al.costo_del_prossimo_punto(ipovedente, "precisione") == pytest.approx(al.costo_del_prossimo_punto(vedente, "precisione"))


def test_il_costo_cresce_di_dodici_volte_dal_fondo_al_tetto():
    g = _normale(fisico=0.0)
    g.precisione_base = 0.0
    fondo = al.costo_fra(g, "precisione", 0.0, 0.01)
    cima = al.costo_fra(g, "precisione", 9.99, 10.0)
    assert cima / fondo == pytest.approx(math.exp(CRESCITA_DEL_COSTO), rel=0.01)


def test_il_tetto_del_totale_non_si_supera_e_i_punti_in_piu_restano():
    g = _normale()
    g.punti_allenamento = 1_000_000.0
    spesa = al.spendi(g, "triplaspondadx", 1_000_000.0)
    assert spesa.a == pytest.approx(MAX_TOTALE_SKILL_GIOCO)
    assert g.triplaspondadx_base + g.triplaspondadx_allenata == pytest.approx(MAX_TOTALE_SKILL_GIOCO)
    assert spesa.punti == pytest.approx(al.costo_fra(g, "triplaspondadx", 8.0, 40.0))
    assert g.punti_allenamento == pytest.approx(1_000_000.0 - spesa.punti)
    # Ora l'allenata supera il vecchio tetto di 20: arriva al tetto meno l'innata.
    assert g.triplaspondadx_allenata == pytest.approx(32.0)
    with pytest.raises(ValueError, match="massimo"):
        al.spendi(g, "triplaspondadx", 10.0)


def test_l_allenata_fisica_supera_cinque_quando_l_innata_lo_permette():
    g = _normale()
    g.punti_allenamento = 1_000_000.0
    al.spendi(g, "resistenza", 1_000_000.0)
    assert g.resistenza_allenata == pytest.approx(MAX_TOTALE_PRECISIONE_RESISTENZA - 1.5)
    assert al.allenata_massima(g, "resistenza") == pytest.approx(8.5)


def test_la_spesa_a_mano_rifiuta_quel_che_non_si_puo():
    g = _normale()
    g.punti_allenamento = 10.0
    with pytest.raises(ValueError, match="soltanto"):
        al.spendi(g, "difesa", 11.0)
    with pytest.raises(ValueError):
        al.spendi(g, "difesa", 0.0)
    g.infortunato = True
    g.infortunio_sede = "ginocchio"
    with pytest.raises(ValueError, match="non si allena"):
        al.spendi(g, "difesa", 5.0)
    assert g.punti_allenamento == 10.0


def test_la_spesa_a_mano_va_nel_diario_e_si_fonde_nello_stesso_giorno():
    g = _normale()
    g.diario.clear()
    g.punti_allenamento = 50.0
    al.spendi(g, "difesa", 20.0, OGGI)
    al.spendi(g, "difesa", 10.0, OGGI + datetime.timedelta(hours=1))
    assert len(g.diario) == 1
    voce = g.diario[0]
    assert voce["punti"] == pytest.approx(30.0) and voce["spesa"][0][0] == "difesa_base"
    assert voce["spesa"][0][1] == pytest.approx(8.0) and voce["spesa"][0][2] == pytest.approx(g.difesa_base + g.difesa_allenata)
    al.spendi(g, "attacco", 10.0, OGGI)
    al.spendi(g, "difesa", 10.0, OGGI + datetime.timedelta(days=1))
    assert len(g.diario) == 3


def test_il_calo_e_nullo_sotto_il_settanta_per_cento_e_piccolo_sopra():
    g = _normale()
    g.difesa_allenata = 19.0
    assert al.mantenimento_del_mese(g, 30) == 0.0
    g.difesa_allenata = 30.0
    perso = al.mantenimento_del_mese(g, 108)
    # A 38 su 40 si perde circa 1,2 punti per anno d'età.
    assert 1.0 < perso < 1.4
    g.difesa_base, g.difesa_allenata = 39.9, 0.05
    al.mantenimento_del_mese(g, 108)
    assert g.difesa_allenata == 0.0


def test_l_apprendista_rapido_dimentica():
    g = _normale(apprendista_rapido=True)
    g.attacco_allenata = 10.0
    al.mantenimento_del_mese(g, 30)
    assert g.attacco_allenata == pytest.approx(10.0 * TRATTI_ALLENAMENTO["apprendista_rapido"]["oblio_mensile"])
    assert al.efficacia(g) == pytest.approx(1.5 * al.efficacia(_normale()))


def test_il_riempimento_svuota_il_portafoglio():
    g = _normale()
    g.punti_allenamento = 777.7
    prima = valore.somma_pesata(g)
    spese = al.allena_secondo_programma(g, programma="difensiva")
    assert g.punti_allenamento == 0.0
    assert sum(s.punti for s in spese) == pytest.approx(777.7)
    assert valore.somma_pesata(g) > prima


def test_con_completa_tutte_salgono_allo_stesso_livello_relativo():
    g = giocatore(4, valore=10.0, fisico=2.5, anni=25, talento=False, apprendista_rapido=False, maturazione=None)
    g.punti_allenamento = 3000.0
    spese = al.allena_secondo_programma(g, programma="completa")
    assert len(spese) == 24
    livelli = [al.livello_relativo(g, c) for c in al.CARATTERISTICHE]
    assert max(livelli) - min(livelli) < 1e-9
    assert livelli[0] > 0.25


def test_le_caratteristiche_alla_pari_salgono_insieme():
    g = _normale()
    g.punti_allenamento = 50.0
    spese = {s.caratteristica: s for s in al.allena_secondo_programma(g, programma="battuta")}
    assert spese["battutasx"].a == pytest.approx(spese["battutadx"].a)


def test_le_principali_restano_avanti_di_ln2_su_k():
    g = giocatore(5, valore=10.0, fisico=2.5, anni=25, talento=False, apprendista_rapido=False, maturazione=None)
    g.punti_allenamento = 20000.0
    al.allena_secondo_programma(g, programma="controllo")
    principale = al.livello_relativo(g, "controllopalla")
    secondaria = al.livello_relativo(g, "difesa")
    altra = al.livello_relativo(g, "bomba")
    assert principale - altra == pytest.approx(math.log(2.0) / CRESCITA_DEL_COSTO, abs=1e-9)
    assert secondaria - altra == pytest.approx(math.log(1.4) / CRESCITA_DEL_COSTO, abs=1e-9)


def test_un_tetto_raggiunto_esce_dall_insieme():
    # Con una preferenza fortissima l'attacco, quasi al tetto, sale per primo; arrivato al tetto si
    # ferma, e il resto del portafoglio va alle altre.
    g = _normale()
    g.attacco_allenata = 31.8
    preferite = dict.fromkeys(al.CARATTERISTICHE, 1.0) | {"attacco": 1000.0}
    al_tetto = al.costo_fra(g, "attacco", 39.8, 40.0)
    arrivi, usati = al._riempimento(g, preferite, al_tetto + 100.0)
    per_nome = {c: (arrivo, costo) for c, arrivo, _prima, costo in arrivi}
    assert per_nome["attacco"][0] == pytest.approx(40.0)
    assert usati == pytest.approx(al_tetto + 100.0)
    altre = sum(al.costo_fra(g, c, al.totale(g, c), arrivo) for c, (arrivo, _costo) in per_nome.items() if c != "attacco")
    assert altre == pytest.approx(100.0)
    assert sum(costo for _arrivo, costo in per_nome.values()) == pytest.approx(usati)


def test_tutto_al_tetto_si_spende_soltanto_quel_che_serve():
    g = _normale()
    g.punti_allenamento = 1e9
    spese = al.allena_secondo_programma(g, programma="completa")
    assert all(al.livello_relativo(g, c) == pytest.approx(1.0) for c in al.CARATTERISTICHE)
    assert g.punti_allenamento == pytest.approx(1e9 - sum(s.punti for s in spese), rel=1e-9)
    assert al.allena_secondo_programma(g) == []


def test_la_spesa_a_mano_e_quella_del_programma_usano_gli_stessi_integrali():
    a, b = _normale(), _normale()
    a.punti_allenamento = b.punti_allenamento = 40.0
    spesa = al.spendi(a, "attacco", 40.0)
    preferite = dict.fromkeys(al.CARATTERISTICHE, 1e-9) | {"attacco": 1.0}
    arrivi, usati = al._riempimento(b, preferite, 40.0)
    per_nome = {c: (arrivo, costo) for c, arrivo, _prima, costo in arrivi}
    assert per_nome["attacco"][0] == pytest.approx(spesa.a) and usati == pytest.approx(40.0)
    assert per_nome["attacco"][1] == pytest.approx(spesa.punti, rel=1e-6)


def test_l_infortunato_non_si_allena_e_l_ambidestro_col_braccio_fermo_si():
    fermo = _normale(infortunato=True, infortunio_sede="ginocchio")
    fermo.punti_allenamento = 100.0
    assert not al.puo_allenarsi(fermo)
    assert al.allena_secondo_programma(fermo) == []
    ambidestro = _normale(ambidestro=True, infortunato=True, infortunio_sede="polso_dx")
    ambidestro.punti_allenamento = 100.0
    assert al.puo_allenarsi(ambidestro)
    assert al.allena_secondo_programma(ambidestro)
