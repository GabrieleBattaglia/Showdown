"""
Le prove dello staff della tappa 13, decisione D33, passo 1 del progetto: l'allenatore e il suo
salvataggio, la qualità dello staff e le tre ancore di ogni effetto, la classe migliore della carriera,
gli allenatori che nascono dai ritirati e quelli che il mondo genera, la prelazione, l'uscita di scena,
i fattori sui giocatori e i loro effetti sull'allenamento, sugli infortuni e sulla fedeltà, il formato
8 e l'aggiornamento dal 7. L'assunzione vera, coi contratti, arriva col passo 2: qui un aiuto mette
l'allenatore nello staff.
"""

import datetime
import json
import random

import pytest

import allenamento
import archivio
import classe
import infortuni
import staff
from costanti import (
    FATTORI_ALLENAMENTO_STAFF,
    FATTORI_FEDELTA_STAFF,
    FATTORI_RISCHIO_STAFF,
    FEDELTA_PER_MESE,
    GIORNI_PRELAZIONE,
    LIVELLO_MINIMO_ALLENATORE,
    PESI_STAFF,
    QUALITA_MEDIA_DELLO_STAFF,
    QUALITA_MINIMA_ALLENATORE,
)
from mondo import Mondo

INIZIO = datetime.datetime(2026, 5, 15, 12, 0)


@pytest.fixture
def mondo():
    random.seed(1313)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(30, INIZIO, annuncia=False)
    return m


def _nello_staff(mondo, poli, a, posto):
    """Mette l'allenatore nel posto dello staff, senza contratto: l'assunzione vera è del passo 2."""
    a.polisportiva = poli.nome
    a.ruolo = staff.CAPO if posto == 0 else staff.ASSISTENTE
    poli.staff[posto] = a.numero
    mondo.aggiorna_fattori_staff(poli)


def _allenatore(mondo, livello):
    a = mondo._nasce_un_allenatore(INIZIO, random.Random(livello))
    a.livello = livello
    return a


# Il modello e il salvataggio.

def test_l_allenatore_va_e_torna_dal_salvataggio(mondo):
    a = mondo._nasce_un_allenatore(INIZIO, random.Random(7))
    assert a.tipo == staff.NATO and 1 <= a.livello <= LIVELLO_MINIMO_ALLENATORE and a.giocatore_id == 0 and a.etamorte > a.eta(INIZIO)
    assert 35 <= a.eta_anni(INIZIO) <= 60 and a.eta_fine >= a.eta(INIZIO) + 5 * 108 and a.libero and a.tratti
    assert a.descrizione_fisica(INIZIO) and a.codice == classe.codice(a.livello)
    copia = staff.Allenatore.da_dizionario(json.loads(json.dumps(a.a_dizionario())))
    assert copia.a_dizionario() == a.a_dizionario()
    for campo, valore in (("tipo", "presidente"), ("livello", 71), ("visus", "ciechissimo"), ("giocatore_id", 4), ("ruolo", staff.CAPO)):
        dati = a.a_dizionario()
        dati[campo] = valore
        with pytest.raises(ValueError, match=campo):
            staff.Allenatore.da_dizionario(dati)


def test_lo_staff_della_polisportiva_si_controlla(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    assert poli.staff == [0, 0, 0]
    for sbagliato in ([1, 1, 0], [0, 0], [-1, 0, 0]):
        dati = poli.a_dizionario()
        dati["staff"] = sbagliato
        with pytest.raises(ValueError, match="staff"):
            type(poli).da_dizionario(dati)


# La qualità e i fattori.

def test_la_qualita_va_da_h0_ad_a1():
    assert staff.qualita(LIVELLO_MINIMO_ALLENATORE) == pytest.approx(QUALITA_MINIMA_ALLENATORE) and staff.qualita(1) == pytest.approx(1.0)
    assert staff.qualita(35) < staff.qualita(20)
    capo, primo, secondo = PESI_STAFF
    assert staff.qualita_dello_staff(None, [None, None]) == 0.0
    assert staff.qualita_dello_staff(1, [1, 1]) == pytest.approx(capo + primo + secondo) == pytest.approx(1.0)
    # L'assistente migliore pesa di più, in qualunque posto stia.
    assert staff.qualita_dello_staff(None, [70, 1]) == pytest.approx(primo * 1.0 + secondo * QUALITA_MINIMA_ALLENATORE)
    # Gli assistenti contano anche senza il capo, risposta 27.
    assert 0 < staff.qualita_dello_staff(None, [10, None]) < staff.qualita_dello_staff(10, [None, None])


@pytest.mark.parametrize("ancore", [FATTORI_ALLENAMENTO_STAFF, FATTORI_RISCHIO_STAFF, FATTORI_FEDELTA_STAFF])
def test_le_tre_ancore(ancore):
    senza, medio, migliore = ancore
    assert staff.fattore(0.0, ancore) == pytest.approx(senza)
    assert staff.fattore(QUALITA_MEDIA_DELLO_STAFF, ancore) == pytest.approx(medio) == 1.0
    assert staff.fattore(1.0, ancore) == pytest.approx(migliore)
    assert staff.fattore(QUALITA_MEDIA_DELLO_STAFF / 2, ancore) == pytest.approx((senza + medio) / 2)


def test_le_ancore_di_gabriele():
    # D33: l'allenamento il 15 per cento più piano senza staff e il 20 più in fretta col migliore, il
    # rischio più o meno 15, la fedeltà dall'85 per cento al 125.
    assert FATTORI_ALLENAMENTO_STAFF == (0.85, 1.0, 1.20) and FATTORI_RISCHIO_STAFF == (1.15, 1.0, 0.85) and FATTORI_FEDELTA_STAFF == (0.85, 1.0, 1.25)
    assert staff.FATTORI_SENZA_STAFF == (0.85, 1.15, 0.85)


# La classe migliore e gli ex giocatori.

def test_la_classe_migliore_resta_la_piu_alta(mondo):
    g = mondo.giocatori[1]
    assert g.classe_migliore == pytest.approx(classe.punteggio(g))
    g.classe_migliore = 0.9
    assert g.aggiorna_classe_migliore() == 0.9 and g.livello_migliore() == classe.livello(0.9)
    g.classe_migliore = 0.0
    assert g.aggiorna_classe_migliore() == pytest.approx(classe.punteggio(g))


def _ritira(mondo, g, data=INIZIO):
    g.etaritiro = g.eta
    g.etamorte = max(g.etamorte, g.eta + 10_000)
    rapporto = Mondo.rapporto_vuoto(data)
    mondo._fai_invecchiare(data, rapporto)
    assert g.ritirato


def test_chi_si_ritira_da_h0_in_su_puo_allenare(mondo):
    bravo, scarso = mondo.giocatori[1], mondo.giocatori[2]
    bravo.classe_migliore = classe.soglia(25)
    scarso.classe_migliore = classe.soglia(LIVELLO_MINIMO_ALLENATORE + 1)
    prima = len(mondo.allenatori)
    _ritira(mondo, bravo)
    _ritira(mondo, scarso)
    nuovi = [a for a in mondo.allenatori.values() if a.tipo == staff.EX]
    assert len(mondo.allenatori) == prima + 1 and len(nuovi) == 1
    a = nuovi[0]
    assert a.giocatore_id == bravo.id and a.livello <= 25 and (a.nome, a.sesso) == (bravo.nome, bravo.sesso) and a.libero
    assert a.eta(INIZIO + datetime.timedelta(days=1)) == bravo.eta and a.prelazione is None


def test_la_prelazione_sul_tuo_ritirato(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = mondo.giocatori[3]
    mondo._tessera(poli, g)
    g.fedelta = 40.0
    g.classe_migliore = classe.soglia(30)
    _ritira(mondo, g)
    a = next(a for a in mondo.allenatori.values() if a.giocatore_id == g.id)
    assert a.prelazione == poli.nome and a.prelazione_fino == INIZIO + datetime.timedelta(days=GIORNI_PRELAZIONE)
    assert a.club_di_provenienza == poli.nome and a.fedelta_di_provenienza == 40.0
    assert "puoi assumerlo prima degli altri" in poli.diario[0]["testo"]
    mondo._invecchia_lo_staff(a.prelazione_fino)
    assert a.prelazione is None and a.prelazione_fino is None


def test_l_allenatore_esce_di_scena_col_suo_giocatore(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = mondo.giocatori[4]
    g.classe_migliore = classe.soglia(15)
    _ritira(mondo, g)
    a = next(a for a in mondo.allenatori.values() if a.giocatore_id == g.id)
    _nello_staff(mondo, poli, a, 0)
    g.etamorte = g.eta
    mondo._fai_invecchiare(INIZIO, Mondo.rapporto_vuoto(INIZIO))
    assert a.numero not in mondo.allenatori and poli.staff == [0, 0, 0]
    assert "muore" in poli.diario[0]["testo"]


def test_gli_allenatori_nati_smettono_e_muoiono(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    vecchio, giovane = _allenatore(mondo, 20), _allenatore(mondo, 30)
    _nello_staff(mondo, poli, vecchio, 0)
    _nello_staff(mondo, poli, giovane, 1)
    oggi = vecchio.nascita + datetime.timedelta(days=vecchio.eta_fine)
    giovane.etamorte = giovane.eta(oggi)
    mondo._invecchia_lo_staff(oggi)
    assert vecchio.numero not in mondo.allenatori and giovane.numero not in mondo.allenatori and poli.staff == [0, 0, 0]


def test_i_nati_sono_vedenti_tre_volte_su_quattro_e_rari_in_alto():
    rng = random.Random(33)
    nati = [staff.nato(n, INIZIO, rng) for n in range(1, 2001)]
    vedenti = sum(a.visus == staff.VEDENTE for a in nati) / len(nati)
    assert 0.72 < vedenti < 0.78
    livelli = [a.livello for a in nati]
    assert max(livelli) == LIVELLO_MINIMO_ALLENATORE and min(livelli) >= 1
    # Più alta, più rara: dalla H alla F molti, ad A pochissimi.
    assert sum(n >= 50 for n in livelli) > 10 * sum(n <= 20 for n in livelli)


def test_un_mondo_che_avanza_fa_nascere_allenatori(mondo):
    prima = len(mondo.allenatori)
    giorno = INIZIO
    for _ in range(60):
        giorno += datetime.timedelta(days=1)
        mondo._un_giorno(giorno, Mondo.rapporto_vuoto(giorno))
    # In media 5,5 nascite al giorno e un allenatore ogni venti: circa 16 in 60 giorni.
    assert 5 <= len(mondo.allenatori) - prima <= 35


# I fattori e i loro effetti.

def test_i_fattori_sui_giocatori(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    tesserato, libero = mondo.giocatori[5], mondo.giocatori[6]
    mondo._tessera(poli, tesserato)
    mondo.aggiorna_fattori_staff()
    assert tesserato.fattore_staff == libero.fattore_staff == 0.85 and tesserato.fattore_rischio_staff == 1.15
    a = _allenatore(mondo, 1)
    _nello_staff(mondo, poli, a, 0)
    atteso = staff.fattori(staff.qualita_dello_staff(1, [None, None]))
    assert tesserato.fattore_staff == pytest.approx(atteso[0]) and tesserato.fattore_rischio_staff == pytest.approx(atteso[1])
    assert libero.fattore_staff == 0.85
    # Chi lascia il club torna senza staff.
    mondo._lascia(poli, tesserato)
    assert tesserato.fattore_staff == 0.85


def test_l_allenamento_e_gli_infortuni_seguono_lo_staff(mondo):
    g = mondo.giocatori[7]
    g.fattore_staff, g.fattore_rischio_staff = 1.0, 1.0
    efficacia, rischio = allenamento.efficacia(g), infortuni.probabilita_base(g)
    g.fattore_staff, g.fattore_rischio_staff = 1.2, 0.85
    assert allenamento.efficacia(g) == pytest.approx(efficacia * 1.2) and infortuni.probabilita_base(g) == pytest.approx(rischio * 0.85)


def test_la_fedelta_segue_lo_staff(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = mondo.giocatori[8]
    mondo._tessera(poli, g)
    mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE, INIZIO)
    assert g.fedelta == pytest.approx(FEDELTA_PER_MESE * 0.85)
    for posto, livello in enumerate((1, 1, 1)):
        _nello_staff(mondo, poli, _allenatore(mondo, livello), posto)
    g.fedelta = 0.0
    mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE, INIZIO)
    assert g.fedelta == pytest.approx(FEDELTA_PER_MESE * 1.25)


# Il formato 8 e l'aggiornamento dal 7.

def test_andata_e_ritorno_del_formato_8(mondo, cartella_di_prova):
    poli = mondo.fonda_polisportiva("Club di prova")
    a = _allenatore(mondo, 12)
    _nello_staff(mondo, poli, a, 0)
    assert archivio.salva(mondo)
    ricaricato = Mondo()
    assert archivio.carica(ricaricato) == archivio.CARICATO
    assert {n: x.a_dizionario() for n, x in ricaricato.allenatori.items()} == {n: x.a_dizionario() for n, x in mondo.allenatori.items()}
    assert ricaricato.polisportive["Club di prova"].staff == [a.numero, 0, 0] and ricaricato.prossimo_allenatore == mondo.prossimo_allenatore
    assert not ricaricato.staff_appena_nato
    for gid, g in mondo.giocatori.items():
        assert ricaricato.giocatori[gid].classe_migliore == g.classe_migliore
    # Uno staff che non corrisponde all'allenatore non si legge.
    contenuto = archivio.componi(mondo)
    contenuto["mondo"]["allenatori"][0]["polisportiva"] = None
    contenuto["mondo"]["allenatori"][0]["ruolo"] = None
    with pytest.raises(archivio.ErroreSalvataggio, match="staff"):
        archivio.costruisci(contenuto, Mondo())


def test_l_aggiornamento_dal_formato_7(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    ritirato, scarso = mondo.giocatori[9], mondo.giocatori[10]
    for g, livello in ((ritirato, 18), (scarso, 80)):
        g.ritirato = True
        g.classe_migliore = classe.soglia(livello)
    contenuto = archivio.componi(mondo)
    contenuto["formato"] = 7
    dati = contenuto["mondo"]
    for g in dati["giocatori"]:
        del g["classe_migliore"]
    for p in dati["polisportive"].values():
        del p["staff"]
    del dati["allenatori"], dati["prossimo_allenatore"]
    archivio.MIGRAZIONI[7](contenuto)
    assert contenuto["formato"] == 8
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    assert nuovo.staff_appena_nato and nuovo.polisportive[poli.nome].staff == [0, 0, 0]
    ex = [a for a in nuovo.allenatori.values() if a.tipo == staff.EX]
    # La classe migliore riparte da quella di oggi, l'unica che si conosce.
    assert [a.giocatore_id for a in ex] == [gid for gid, g in sorted(nuovo.giocatori.items()) if g.ritirato and classe.livello(g.classe_migliore) <= 70]
    assert all(g.classe_migliore == pytest.approx(classe.punteggio(g)) for g in nuovo.giocatori.values())
    assert nuovo.prossimo_allenatore == max(nuovo.allenatori, default=0) + 1
