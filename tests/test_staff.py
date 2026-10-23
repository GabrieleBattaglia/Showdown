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
import contratti
import economia
import infortuni
import staff
import suoni
import testi
from costanti import (
    FATTORI_ALLENAMENTO_STAFF,
    FATTORI_FEDELTA_STAFF,
    FATTORI_RISCHIO_STAFF,
    FEDELTA_PER_MESE,
    GIORNI_PRELAZIONE,
    LIVELLO_MINIMO_ALLENATORE,
    MARGINE_CAMBIO_STAFF_CPU,
    MESI_DI_INGAGGIO,
    MINUTI_RISERVA_UTENTE,
    PESI_STAFF,
    QUALITA_MINIMA_ALLENATORE,
    QUOTA_STIPENDIO_ASSISTENTE,
    STIPENDIO_STAFF_MASSIMO,
    STIPENDIO_STAFF_MINIMO,
)
from mondo import Mondo, nome_completo
from utilita import adesso_utc

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
    # Lo staff medio è la qualità media del mondo di oggi, risposta 30: qui 0,4.
    senza, medio, migliore = ancore
    media = 0.4
    assert staff.fattore(0.0, ancore, media) == pytest.approx(senza)
    assert staff.fattore(media, ancore, media) == pytest.approx(medio) == 1.0
    assert staff.fattore(1.0, ancore, media) == pytest.approx(migliore)
    assert staff.fattore(media / 2, ancore, media) == pytest.approx((senza + medio) / 2)
    # In un mondo senza nessun allenatore tutti valgono lo staff medio.
    assert staff.fattore(0.0, ancore, 0.0) == medio


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
    return rapporto


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
    rapporto = _ritira(mondo, g)
    assert rapporto["tue_prelazioni"] == 1
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
    poli, altro = mondo.fonda_polisportiva("Club di prova"), mondo.fonda_polisportiva("Altro club")
    tesserato, dell_altro, libero = mondo.giocatori[5], mondo.giocatori[9], mondo.giocatori[6]
    mondo._tessera(poli, tesserato)
    mondo._tessera(altro, dell_altro)
    # Senza nessuno staff nel mondo, tutti valgono lo staff medio, risposta 30.
    mondo.aggiorna_fattori_staff()
    assert tesserato.fattore_staff == libero.fattore_staff == 1.0 and mondo.qualita_media_dello_staff == 0.0
    _nello_staff(mondo, poli, _allenatore(mondo, 1), 0)
    mondo.aggiorna_fattori_staff()
    # Lo staff medio è la media dei due club, uno col capo A1 e uno senza.
    q = staff.qualita_dello_staff(1, [None, None])
    assert mondo.qualita_media_dello_staff == pytest.approx(q / 2)
    col_capo, senza = staff.fattori(q, q / 2), staff.fattori(0.0, q / 2)
    assert col_capo[0] > 1.0 > col_capo[1] and senza == staff.FATTORI_SENZA_STAFF
    # Dalla risposta 35 i fattori si dividono per la loro media sui tesserati: il mondo vale 1, e i rapporti
    # fra i club restano quelli delle ancore.
    norma = tuple((a + b) / 2 for a, b in zip(col_capo, senza, strict=True))
    assert tesserato.fattore_staff == pytest.approx(col_capo[0] / norma[0]) and tesserato.fattore_rischio_staff == pytest.approx(col_capo[1] / norma[1])
    assert (tesserato.fattore_staff + dell_altro.fattore_staff) / 2 == pytest.approx(1.0)
    assert (tesserato.fattore_rischio_staff + dell_altro.fattore_rischio_staff) / 2 == pytest.approx(1.0)
    assert tesserato.fattore_staff / dell_altro.fattore_staff == pytest.approx(col_capo[0] / senza[0])
    assert dell_altro.fattore_staff == libero.fattore_staff == pytest.approx(0.85 / norma[0]) and libero.fattore_rischio_staff == pytest.approx(1.15 / norma[1])
    # Chi lascia il club torna senza staff, con la norma del giorno.
    mondo._lascia(poli, tesserato)
    assert tesserato.fattore_staff == pytest.approx(0.85 / norma[0])


def test_la_norma_toglie_lo_scalino_del_primo_allenatore(mondo):
    # Prima della risposta 35, in un mondo senza allenatori, al primo assunto tutti gli altri scendevano di colpo a 0,85.
    clubs = [mondo.fonda_polisportiva(f"Club {i}") for i in range(10)]
    for club, gid in zip(clubs, range(1, 11), strict=True):
        mondo._tessera(club, mondo.giocatori[gid])
    _nello_staff(mondo, clubs[0], _allenatore(mondo, 60), 1)
    mondo.aggiorna_fattori_staff()
    fattori = [mondo.giocatori[gid].fattore_staff for gid in range(1, 11)]
    assert sum(fattori) / len(fattori) == pytest.approx(1.0)
    assert min(fattori) > 0.98


def test_l_allenamento_e_gli_infortuni_seguono_lo_staff(mondo):
    g = mondo.giocatori[7]
    g.fattore_staff, g.fattore_rischio_staff = 1.0, 1.0
    efficacia, rischio = allenamento.efficacia(g), infortuni.probabilita_base(g)
    g.fattore_staff, g.fattore_rischio_staff = 1.2, 0.85
    assert allenamento.efficacia(g) == pytest.approx(efficacia * 1.2) and infortuni.probabilita_base(g) == pytest.approx(rischio * 0.85)


def test_la_fedelta_segue_lo_staff(mondo):
    poli, altro = mondo.fonda_polisportiva("Club di prova"), mondo.fonda_polisportiva("Altro club")
    g, h = mondo.giocatori[8], mondo.giocatori[10]
    mondo._tessera(poli, g)
    mondo._tessera(altro, h)
    # Senza nessuno staff nel mondo, la fedeltà cresce come prima.
    mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE, INIZIO)
    assert g.fedelta == FEDELTA_PER_MESE
    for posto, livello in enumerate((1, 1, 1)):
        _nello_staff(mondo, poli, _allenatore(mondo, livello), posto)
    mondo.aggiorna_fattori_staff()
    # Lo staff migliore cresce del 25 per cento rispetto allo staff medio, chi non ne ha cala all'85 per cento;
    # dalla risposta 35 i due fattori si dividono per la loro media, e il mondo cresce come prima.
    g.fedelta = h.fedelta = 0.0
    mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE, INIZIO)
    mondo._aggiungi_fedelta(h, altro, FEDELTA_PER_MESE, INIZIO)
    assert g.fedelta / h.fedelta == pytest.approx(1.25 / 0.85)
    assert (g.fedelta + h.fedelta) / 2 == pytest.approx(FEDELTA_PER_MESE)


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
    # La revisione del 22 ottobre 2026: la notizia della partenza resta nel diario delle polisportive dell'utente.
    assert nuovo.polisportive[poli.nome].diario[0]["testo"].startswith("Arriva lo staff, un capo e due assistenti")


def test_alla_migrazione_chi_e_oltre_l_eta_di_fine_non_smette_con_tutti(mondo):
    # La revisione del 22 ottobre 2026: gli ex giocatori della migrazione già oltre l'età estratta smettevano tutti lo stesso giorno.
    anziani = list(mondo.giocatori.values())[:12]
    for g in anziani:
        g.ritirato = True
        g.eta = 88 * 108
        g.etamorte = g.eta + 10_000
        g.classe_migliore = classe.soglia(30)
    mondo.fai_nascere_lo_staff()
    oggi = mondo.datetime_corrente_simulazione
    resti = [a.eta_fine - a.eta(oggi) for a in mondo.allenatori.values() if a.tipo == staff.EX]
    assert len(resti) == 12 and all(1 <= r <= 540 for r in resti) and len(set(resti)) > 6


# Il passo 2: lo stipendio, l'ingaggio, i contratti, la paga e le mosse del computer.

def test_lo_stipendio_va_in_linea_retta_sulla_qualita(mondo):
    a1, h0 = _allenatore(mondo, 1), _allenatore(mondo, LIVELLO_MINIMO_ALLENATORE)
    # Le cifre si arrotondano alla decina, come quelle dei giocatori: a un ottavo, 15 e 112 diventano 20 e 110.
    massimo, minimo = economia.arrotonda(STIPENDIO_STAFF_MASSIMO), economia.arrotonda(STIPENDIO_STAFF_MINIMO)
    assert staff.stipendio_richiesto(a1, staff.CAPO) == massimo and staff.stipendio_richiesto(h0, staff.CAPO) == minimo
    assert staff.stipendio_richiesto(a1, staff.ASSISTENTE) == economia.arrotonda(STIPENDIO_STAFF_MASSIMO * QUOTA_STIPENDIO_ASSISTENTE)
    medio = _allenatore(mondo, 35)
    assert minimo < staff.stipendio_richiesto(medio, staff.CAPO) < massimo
    assert staff.ingaggio_richiesto(a1, staff.CAPO) == massimo * MESI_DI_INGAGGIO
    assert 4 <= staff.durata_proposta(a1, INIZIO) <= 24


def test_la_fedelta_al_vecchio_club_fa_chiedere_meno(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a = _allenatore(mondo, 20)
    a.club_di_provenienza, a.fedelta_di_provenienza = poli.nome, 100.0
    altro = mondo.fonda_polisportiva("Altro club")
    assert staff.ingaggio_richiesto(a, staff.CAPO, poli) == economia.arrotonda(staff.ingaggio_richiesto(a, staff.CAPO, altro) * 0.75)


def test_assumere_e_licenziare(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a, b = _allenatore(mondo, 10), _allenatore(mondo, 40)
    cassa = poli.cassa
    mondo.assumi_allenatore(poli, a, 0, INIZIO, 1000)
    assert poli.staff == [a.numero, 0, 0] and a.polisportiva == poli.nome and a.ruolo == staff.CAPO
    assert poli.cassa == cassa - 1000 and poli.conti_del_mese["ingaggi"] == 1000
    assert a.contratto_stipendio == staff.stipendio_richiesto(a, staff.CAPO) and a.contratto_scadenza.day == 1
    assert mondo.monte_stipendi(poli) == a.contratto_stipendio and mondo.monte_dello_staff(poli) == a.contratto_stipendio
    assert "Assume" in poli.diario[0]["testo"] and "Firma con Club di prova" in a.diario[0]["testo"]
    # I problemi: il posto occupato, chi allena già, la prelazione di un altro, la cassa che non basta.
    assert "occupato" in mondo.problema_assunzione(poli, b, 0, 0)
    altro = mondo.fonda_polisportiva("Altro club")
    assert "allena già" in mondo.problema_assunzione(altro, a, 0, 0)
    b.prelazione, b.prelazione_fino = "Altro club", INIZIO + datetime.timedelta(days=5)
    assert "soltanto Altro club" in mondo.problema_assunzione(poli, b, 1, 0)
    b.prelazione = b.prelazione_fino = None
    assert "supera la cassa" in mondo.problema_assunzione(poli, b, 1, poli.cassa + 1)
    with pytest.raises(ValueError):
        mondo.assumi_allenatore(poli, b, 0, INIZIO)
    # Il licenziamento paga metà degli stipendi che restano.
    attesa = contratti.buonuscita(a, INIZIO)
    assert attesa > 0 and mondo.licenzia_allenatore(poli, a, INIZIO) == attesa
    assert poli.staff == [0, 0, 0] and a.libero and a.contratto_stipendio == 0 and poli.conti_del_mese["buonuscite"] == attesa


def test_lo_staff_si_paga_il_primo_del_mese(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a, b = _allenatore(mondo, 10), _allenatore(mondo, 30)
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    mondo.assumi_allenatore(poli, b, 1, INIZIO)
    primo = datetime.datetime(2026, 6, 1, 12, 0)
    mondo._primo_del_mese(primo, Mondo.rapporto_vuoto(primo))
    assert poli.bilanci[0]["staff"] == a.contratto_stipendio + b.contratto_stipendio
    # Senza soldi per lo stipendio, nemmeno con lo sponsor appena arrivato, l'allenatore se ne va.
    poli.cassa = -100_000
    secondo = datetime.datetime(2026, 7, 1, 12, 0)
    mondo._primo_del_mese(secondo, Mondo.rapporto_vuoto(secondo))
    assert a.libero and b.libero and poli.staff == [0, 0, 0] and "lo stipendio non è arrivato" in a.diario[0]["testo"]


def test_il_contratto_scade_o_si_rinnova(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a, b = _allenatore(mondo, 10), _allenatore(mondo, 30)
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    mondo.assumi_allenatore(poli, b, 1, INIZIO)
    contratti.concorda_rinnovo(b, 300, 12)
    for x in (a, b):
        x.contratto_scadenza = datetime.datetime(2026, 6, 1)
    b.rinnovo_scadenza = datetime.datetime(2027, 6, 1)
    mondo._contratti_dello_staff(datetime.datetime(2026, 6, 1, 12, 0))
    assert a.libero and poli.staff == [0, b.numero, 0] and "è scaduto" in a.diario[0]["testo"]
    assert b.contratto_stipendio == 300 and b.contratto_scadenza == datetime.datetime(2027, 6, 1) and not contratti.ha_rinnovo(b)


def test_il_computer_assume_il_migliore_che_puo_pagare(mondo):
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    cpu.cassa = 100_000
    for gid in range(1, 6):
        mondo._tessera(cpu, mondo.giocatori[gid])
    for a in list(mondo.allenatori.values()):
        del mondo.allenatori[a.numero]
    scarso, bravo, carissimo = _allenatore(mondo, 60), _allenatore(mondo, 20), _allenatore(mondo, 1)
    in_prelazione = _allenatore(mondo, 2)
    in_prelazione.prelazione, in_prelazione.prelazione_fino = "Club di Gabriele", INIZIO + datetime.timedelta(days=5)
    random.seed(4)
    spazio = mondo._spazio_negli_stipendi(cpu)
    assunti = 0
    for _ in range(40):
        assunti += mondo._staff_del_computer([cpu], INIZIO)
        if all(cpu.staff):
            break
    # Dalla risposta 31 lo staff si paga soltanto con lo sponsor: il computer assume finché lo stipendio ci sta.
    assert assunti >= 2 and cpu.staff[0] and in_prelazione.libero
    assert mondo.monte_stipendi(cpu) <= mondo.sponsor(cpu)
    capo = mondo.allenatori[cpu.staff[0]]
    # Il capo è il migliore con lo stipendio alla portata, prima che arrivassero gli assistenti.
    alla_portata = [x for x in (scarso, bravo, carissimo) if staff.stipendio_richiesto(x, staff.CAPO) <= spazio]
    assert capo is min(alla_portata, key=lambda x: x.livello)
    assert cpu.staff[0] != in_prelazione.numero


def test_il_computer_rinnova_o_aspetta_uno_migliore(mondo):
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    cpu.cassa = 100_000
    for a in list(mondo.allenatori.values()):
        del mondo.allenatori[a.numero]
    mio = _allenatore(mondo, 40)
    mondo.assumi_allenatore(cpu, mio, 0, INIZIO)
    finestra = mio.contratto_scadenza - datetime.timedelta(days=40)
    mondo._rinnovo_dello_staff_cpu(cpu, mio, finestra)
    assert contratti.ha_rinnovo(mio)
    mio.rinnovo_stipendio, mio.rinnovo_scadenza = 0, None
    _allenatore(mondo, 40 - MARGINE_CAMBIO_STAFF_CPU)
    mondo._rinnovo_dello_staff_cpu(cpu, mio, finestra)
    assert not contratti.ha_rinnovo(mio)


def test_due_ore_di_riserva_per_l_utente(mondo):
    # Regola di Gabriele del 21 ottobre 2026, risposta 29: chi diventa allenatore resta dell'utente per un tempo vero,
    # un'ora e dalla risposta 37 due ore.
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    cpu.cassa = 100_000
    for a in list(mondo.allenatori.values()):
        del mondo.allenatori[a.numero]
    ora = datetime.datetime(2026, 10, 21, 20, 0, tzinfo=datetime.UTC)
    mondo._ora_reale = ora
    a = mondo._nasce_un_allenatore(INIZIO)
    # Dalla risposta 37 la riserva è di due ore.
    assert a.riservato_fino == ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE) == ora + datetime.timedelta(hours=2)
    random.seed(4)
    for _ in range(30):
        mondo._staff_del_computer([cpu], INIZIO)
    assert a.libero
    # Passata l'ora, il computer lo vede.
    mondo._ora_reale = ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE)
    for _ in range(30):
        mondo._staff_del_computer([cpu], INIZIO)
        if not a.libero:
            break
    assert cpu.staff[0] == a.numero and a.riservato_fino is None
    # Fuori dal programma, senza un'ora vera, nessuna riserva.
    mondo._ora_reale = None
    assert mondo._nasce_un_allenatore(INIZIO).riservato_fino is None


def test_all_aggiornamento_gli_allenatori_sono_dell_utente_per_un_ora(mondo):
    mondo.giocatori[11].ritirato = True
    mondo.giocatori[11].classe_migliore = classe.soglia(10)
    contenuto = archivio.componi(mondo)
    contenuto["formato"] = 7
    dati = contenuto["mondo"]
    for g in dati["giocatori"]:
        del g["classe_migliore"]
    for p in dati["polisportive"].values():
        del p["staff"]
    del dati["allenatori"], dati["prossimo_allenatore"]
    archivio.MIGRAZIONI[7](contenuto)
    nuovo = Mondo()
    prima = adesso_utc()
    archivio.costruisci(contenuto, nuovo)
    assert nuovo.allenatori and all(prima + datetime.timedelta(minutes=119) < a.riservato_fino <= adesso_utc() + datetime.timedelta(minutes=120)
                                    for a in nuovo.allenatori.values())


# Il passo 3: i testi.

def test_i_testi_dello_staff(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = mondo.giocatori[12]
    mondo._tessera(poli, g)
    scheda = testi.scheda_polisportiva(poli, mondo)
    assert "[STAFF]" in scheda and "Capo: nessuno." in scheda and "Assistente 2: nessuno." in scheda
    a = _allenatore(mondo, 13)
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    mondo.aggiorna_fattori_staff()
    # Con un club soltanto, il suo staff è lo staff medio del mondo.
    assert "allenamento come lo staff medio" in testi.scheda_polisportiva(poli, mondo)
    altro = mondo.fonda_polisportiva("Altro club")
    mondo._tessera(altro, mondo.giocatori[14])
    mondo.aggiorna_fattori_staff()
    scheda = testi.scheda_polisportiva(poli, mondo)
    assert f"Capo: {nome_completo(a)}, {a.codice}" in scheda and "Qualità dello staff" in scheda and "allenamento più" in scheda
    assert "Classe migliore della carriera:" in testi.scheda_giocatore(g, mondo)
    statistiche = testi.statistiche(mondo)
    assert "Allenatori:" in statistiche and "Polisportive con un capo: 1 su 2" in statistiche
    assert testi.scheda_allenatore(a, mondo).startswith("[ALLENATORE]" if a.sesso == "m" else "[ALLENATRICE]")
    assert "di Club di prova" in testi.riga_allenatore(a, mondo)
    libero = _allenatore(mondo, 40)
    assert "chiede" in testi.riga_allenatore(libero, mondo) and ("nato allenatore" if libero.sesso == "m" else "nata allenatrice") in testi.riga_allenatore(libero, mondo)
    # La riserva di un'ora si legge nell'elenco.
    libero.riservato_fino = adesso_utc() + datetime.timedelta(minutes=30)
    assert "a te fino alle" in testi.riga_allenatore(libero, mondo)


def test_la_scheda_dell_ex_giocatore(mondo):
    g = mondo.giocatori[13]
    g.classe_migliore = classe.soglia(8)
    _ritira(mondo, g)
    a = next(a for a in mondo.allenatori.values() if a.giocatore_id == g.id)
    assert "Ex giocatore" in testi.scheda_allenatore(a, mondo)
    assert f"Allena, classe da allenatore {a.codice}" in testi.scheda_giocatore(g, mondo)


def test_la_notizia_dello_staff_all_aggiornamento(mondo):
    _allenatore(mondo, 30)
    mondo.staff_appena_nato = True
    testo = testi.apertura(mondo, "caricato", [], None, adesso_utc(), adesso_utc())
    assert "il mercato degli allenatori è aperto, con 1 allenatore libero, e per due ore è riservato a te" in testo
    mondo.staff_appena_nato = False
    assert "mercato degli allenatori" not in testi.apertura(mondo, "caricato", [], None, adesso_utc(), adesso_utc())


# Le notizie dello staff dell'utente nell'avanzamento, progetto 4.5.

def _un_giorno_di(rapporto):
    rapporto["ticks"] = rapporto["giorni"] = 1
    return rapporto


def test_le_notizie_dei_contratti_del_tuo_staff(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a, b, c = _allenatore(mondo, 10), _allenatore(mondo, 30), _allenatore(mondo, 40)
    for posto, x in enumerate((a, b, c)):
        mondo.assumi_allenatore(poli, x, posto, INIZIO)
    a.contratto_scadenza = datetime.datetime(2026, 9, 1)
    b.contratto_scadenza = datetime.datetime(2026, 7, 1)
    c.contratto_scadenza = datetime.datetime(2026, 6, 1)
    rapporto = _un_giorno_di(Mondo.rapporto_vuoto(INIZIO))
    mondo._contratti_dello_staff(datetime.datetime(2026, 6, 1, 12, 0), rapporto)
    # Come per i tesserati: il promemoria all'ingresso nella finestra e all'ultimo mese, e la notizia di chi torna libero.
    assert c.libero and rapporto["tuo_staff_scaduto"] == 1 and rapporto["tuo_staff_in_scadenza"] == 2
    assert "da oggi si può rinnovare" in a.diario[0]["testo"] and "Ultimo mese di contratto" in b.diario[0]["testo"]
    assert suoni.evento_avanzamento(rapporto) == ("tuo_staff_scaduto", "1 allenatore libero a fine contratto")
    frasi = testi._fatti_dello_staff(rapporto)
    assert frasi == ["1 allenatore del tuo staff è tornato libero a fine contratto: lo staff si guarda con Ctrl+H.",
                     "2 contratti del tuo staff stanno per scadere: si rinnovano con Ctrl+H."]
    assert all(f in testi._fatti_avanzamento(rapporto) for f in frasi)
    rapporto["tuo_staff_scaduto"] = 0
    assert suoni.evento_avanzamento(rapporto) == ("tuo_staff_in_scadenza", "2 contratti di staff in scadenza")


def test_le_notizie_di_chi_lascia_il_tuo_staff(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a, b = _allenatore(mondo, 10), _allenatore(mondo, 30)
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    mondo.assumi_allenatore(poli, b, 1, INIZIO)
    poli.cassa = -100_000
    primo = datetime.datetime(2026, 6, 1, 12, 0)
    rapporto = _un_giorno_di(Mondo.rapporto_vuoto(primo))
    mondo._primo_del_mese(primo, rapporto)
    assert rapporto["tuo_staff_partito"] == 2 and suoni.evento_avanzamento(rapporto, ha_polisportive=True)[0] == "tuo_staff_partito"
    # Chi smette o muore nello staff di un club del computer non è una notizia tua.
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    vecchio, giovane = _allenatore(mondo, 20), _allenatore(mondo, 25)
    _nello_staff(mondo, poli, vecchio, 0)
    _nello_staff(mondo, cpu, giovane, 0)
    oggi = vecchio.nascita + datetime.timedelta(days=vecchio.eta_fine)
    giovane.eta_fine = giovane.eta(oggi)
    rapporto = _un_giorno_di(Mondo.rapporto_vuoto(oggi))
    mondo._invecchia_lo_staff(oggi, rapporto)
    assert rapporto["tuo_staff_uscito"] == 1 and vecchio.numero not in mondo.allenatori and giovane.numero not in mondo.allenatori
    assert suoni.evento_avanzamento(rapporto) == ("tuo_staff_uscito", "1 allenatore uscito dal tuo staff")


@pytest.mark.parametrize("n", [1, 12])
def test_le_notizie_dello_staff_stanno_nella_barra(n):
    for chiave in ("tuo_staff_partito", "tuo_staff_scaduto", "tuo_staff_uscito", "tue_prelazioni", "tuo_staff_in_scadenza"):
        rapporto = _un_giorno_di(Mondo.rapporto_vuoto(INIZIO))
        rapporto[chiave] = n
        evento, testo = suoni.evento_avanzamento(rapporto)
        assert evento in suoni.EVENTI and len(testo) <= 40, testo


def test_l_offerta_minima_del_computer_sta_sotto_ogni_offerta(mondo):
    # Il computer salta chi non ha in cassa l'offerta minima senza calcolare lo sponsor: il limite deve stare
    # sotto ogni offerta vera, anche con lo sconto pieno della polisportiva dove l'allenatore ha chiuso la carriera.
    from costanti import RIALZO_CPU

    poli = mondo.fonda_polisportiva("Club di prova")
    for livello in range(1, LIVELLO_MINIMO_ALLENATORE + 1):
        a = _allenatore(mondo, livello)
        a.club_di_provenienza, a.fedelta_di_provenienza = poli.nome, 100.0
        for ruolo in staff.RUOLI:
            minima = (staff.ingaggio_minimo(staff.stipendio_richiesto(a, ruolo)) - 5) * RIALZO_CPU - 5
            assert minima <= economia.arrotonda(staff.ingaggio_richiesto(a, ruolo, poli) * RIALZO_CPU)
            assert minima <= economia.arrotonda(staff.ingaggio_richiesto(a, ruolo) * RIALZO_CPU)



# La revisione del 22 ottobre 2026 e le risposte 35-38.

class _Fisso:
    """Un caso che estrae sempre lo stesso numero."""

    def __init__(self, valore):
        self.valore = valore

    def uniform(self, _a, _b):
        return self.valore


def test_i_cinque_anni_minimi_soltanto_oltre_l_eta_estratta():
    # Risposta 36 e progetto 1.4: chi comincia prima dell'età estratta smette a quella, chi comincia dopo allena cinque anni.
    assert staff.eta_di_fine(66 * 108, _Fisso(68.0)) == 68 * 108
    assert staff.eta_di_fine(73 * 108, _Fisso(70.0)) == 73 * 108 + 540


def test_l_ingaggio_porta_la_reputazione(mondo):
    povero, ricco = mondo.fonda_polisportiva("Club povero"), mondo.fonda_polisportiva("Club ricco")
    povero.gloria, ricco.gloria = 20, 5_000
    a = _allenatore(mondo, 1)
    due_stipendi = staff.stipendio_richiesto(a, staff.CAPO) * MESI_DI_INGAGGIO
    assert staff.ingaggio_richiesto(a, staff.CAPO, povero) == economia.arrotonda(due_stipendi * 2.0)
    assert staff.ingaggio_richiesto(a, staff.CAPO, ricco) == economia.arrotonda(due_stipendi * 0.5)
    assert staff.ingaggio_richiesto(a, staff.CAPO) == due_stipendi
    assert 150.0 <= _allenatore(mondo, 70).gloria_richiesta < a.gloria_richiesta == 600.0


def test_chi_smette_nello_staff_riceve_il_maturato(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a, b = _allenatore(mondo, 10), _allenatore(mondo, 30)
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    mondo.assumi_allenatore(poli, b, 1, INIZIO)
    cassa = poli.cassa
    mondo._fine_allenatore(a, datetime.datetime(2026, 6, 15, 12, 0), "Smette.", "Il capo smette.")
    pagato = round(a.contratto_stipendio * 14 / 30)
    assert poli.cassa == cassa - pagato and poli.conti_del_mese["staff"] == pagato and "stipendio maturato" in poli.diario[0]["testo"]
    # Il primo del mese si paga il mese intero appena finito.
    cassa = poli.cassa
    mondo._fine_allenatore(b, datetime.datetime(2026, 7, 1, 12, 0), "Smette.", "L'assistente smette.")
    assert poli.cassa == cassa - b.contratto_stipendio


def test_il_computer_prova_anche_gli_allenatori_piu_modesti(mondo, monkeypatch):
    import mondo as modulo_mondo
    from costanti import RIALZO_CPU

    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    for a in list(mondo.allenatori.values()):
        del mondo.allenatori[a.numero]
    bravo, modesto = _allenatore(mondo, 1), _allenatore(mondo, 65)
    monkeypatch.setattr(mondo, "_spazio_negli_stipendi", lambda poli: 100_000)
    monkeypatch.setattr(modulo_mondo, "caso", lambda _p: True)
    offerta = economia.arrotonda(staff.ingaggio_richiesto(modesto, staff.CAPO, cpu) * RIALZO_CPU)
    cpu.cassa = mondo.monte_stipendi(cpu) + offerta
    assert economia.arrotonda(staff.ingaggio_richiesto(bravo, staff.CAPO, cpu) * RIALZO_CPU) > offerta
    assert mondo._staff_del_computer([cpu], INIZIO) == 1 and cpu.staff[0] == modesto.numero and bravo.libero


def test_le_allenatrici_e_le_frasi_dello_staff(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = next(g for g in mondo.giocatori.values() if g.sesso == "f")
    mondo._tessera(poli, g)
    g.classe_migliore = classe.soglia(30)
    _ritira(mondo, g)
    a = next(a for a in mondo.allenatori.values() if a.giocatore_id == g.id)
    assert ", ex giocatrice, " in testi.riga_allenatore(a, mondo) and "Ex giocatrice, ha chiuso la carriera con Club di prova" in testi.scheda_allenatore(a, mondo)
    assert "puoi assumerla prima degli altri" in poli.diario[0]["testo"] and a.diario[-1]["testo"].startswith("Si ritira da giocatrice")
    assert a.diario[-1]["testo"].endswith("di classe " + a.codice + " da allenatrice, la sua classe migliore.")
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    contratti.concorda_rinnovo(a, 300, 12)
    assert ", e il rinnovo già concordato il " in testi.domanda_licenziamento(a, poli, mondo)
    mondo.licenzia_allenatore(poli, a, INIZIO)
    assert a.diario[0]["testo"].startswith("Licenziata da Club di prova")


def test_la_riserva_passata_non_si_mostra_e_la_fine_della_carriera(mondo):
    a = _allenatore(mondo, 20)
    a.riservato_fino = adesso_utc() - datetime.timedelta(hours=1)
    mondo._ora_reale = adesso_utc() - datetime.timedelta(hours=3)
    assert "a te fino" not in testi.riga_allenatore(a, mondo)
    a.riservato_fino = adesso_utc() + datetime.timedelta(minutes=30)
    assert "riservat" in testi.riga_allenatore(a, mondo)
    mondo._ora_reale = None
    oggi = mondo.datetime_corrente_simulazione
    # Dal collaudo del 23 ottobre 2026 l'anno del calendario simulato, con le parole di Gabriele.
    # Il giro del giorno in cui compie eta_fine lo toglie, quindi l'anno è quello del giorno prima.
    for giorni in (0, 30, 400, 11_000):
        a.eta_fine = a.eta(oggi) + giorni
        anno = (oggi + datetime.timedelta(days=max(0, giorni - 1))).year
        assert testi.scheda_allenatore(a, mondo).endswith(f"Sarà in attività sperabilmente fino al {anno}.")
    # A cavallo dell'anno: oggi il 29 dicembre, smette il primo gennaio, quindi lavora fino al 31 dicembre.
    mondo.datetime_corrente_simulazione = datetime.datetime(oggi.year, 12, 29, 12, 0)
    a.eta_fine = a.eta(mondo.datetime_corrente_simulazione) + 3
    assert testi.scheda_allenatore(a, mondo).endswith(f"Sarà in attività sperabilmente fino al {oggi.year}.")


def test_la_prelazione_al_singolare_e_al_plurale():
    assert "puoi assumerlo prima" in " ".join(testi._fatti_dello_staff({"tue_prelazioni": 1}))
    assert "puoi assumerli prima" in " ".join(testi._fatti_dello_staff({"tue_prelazioni": 2}))


def test_niente_promemoria_per_chi_non_tratta_piu(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    a = _allenatore(mondo, 10)
    mondo.assumi_allenatore(poli, a, 0, INIZIO)
    a.contratto_scadenza = datetime.datetime(2026, 7, 1)
    a.proposte_rinnovo = 3
    rapporto = Mondo.rapporto_vuoto(INIZIO)
    mondo._contratti_dello_staff(datetime.datetime(2026, 6, 1, 12, 0), rapporto)
    assert rapporto["tuo_staff_in_scadenza"] == 0 and not any("Ultimo mese" in v["testo"] for v in a.diario)


def test_i_diari_degli_allenatori_si_sfoltiscono(mondo):
    a = _allenatore(mondo, 20)
    for giorni in (20, 10, 5):
        a.annota(INIZIO - datetime.timedelta(days=giorni), f"Voce di {giorni} giorni fa.")
    mondo.datetime_corrente_simulazione = INIZIO
    mondo.conservazione_diari["giocatori"] = 10
    limite = INIZIO - datetime.timedelta(days=10)
    restano = [v for v in a.diario if v["data"] >= limite]
    assert len(restano) < len(a.diario)
    mondo.sfoltisci_diari()
    assert a.diario == restano and not any("20 giorni" in v["testo"] for v in a.diario)


def test_la_prelazione_decade_col_club_che_chiude(mondo):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = mondo.giocatori[3]
    mondo._tessera(poli, g)
    g.classe_migliore = classe.soglia(30)
    _ritira(mondo, g)
    a = next(a for a in mondo.allenatori.values() if a.giocatore_id == g.id)
    assert a.prelazione == poli.nome
    mondo.chiudi_polisportiva(poli)
    assert a.prelazione is None and a.prelazione_fino is None


def test_la_notizia_degli_allenatori_riservati_soltanto_nel_riepilogo(mondo):
    ora = adesso_utc()
    a, b = _allenatore(mondo, 30), _allenatore(mondo, 12)
    for x in (a, b):
        x.riservato_fino = ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE)
    # Un tuo ritirato in prelazione ha la sua notizia, e qui non si conta.
    in_prelazione = _allenatore(mondo, 5)
    in_prelazione.riservato_fino = ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE)
    in_prelazione.prelazione, in_prelazione.prelazione_fino = "Club di prova", INIZIO + datetime.timedelta(days=10)
    rapporto = Mondo.rapporto_vuoto(INIZIO)
    mondo._notizia_dei_riservati(ora, rapporto)
    # Senza una polisportiva dell'utente non c'è niente da dire.
    assert rapporto["riservati"] == ""
    mondo.fonda_polisportiva("Club di prova")
    mondo._notizia_dei_riservati(ora, rapporto)
    notizia = rapporto["riservati"]
    assert notizia.startswith("2 allenatori nuovi sono riservati a te fino alle ") and f"il migliore di classe {b.codice}" in notizia
    assert notizia in testi._fatti_avanzamento(rapporto | {"ticks": 1, "giorni": 1}) and rapporto["notizie"] == []
    # Risposta 38: soltanto nel riepilogo, senza suono e senza la barra.
    assert sum(v for k, v in rapporto.items() if isinstance(v, int) and k != "tue_prelazioni") == 0 and rapporto["tue_prelazioni"] == 1
    # Alla chiusura della sessione la riserva è quasi sempre scaduta: non si ripete.
    sessione = rapporto | {"ticks": 1, "giorni": 1}
    assert notizia not in testi.chiusura(datetime.timedelta(hours=3), 5, [], sessione)


def test_la_fine_minima_si_sa_dove_si_estrae():
    # La seconda revisione: chi estrae per caso proprio l'età più cinque anni non è una fine minima.
    class Estrae:
        def __init__(self, anni):
            self.anni = anni

        def uniform(self, _a, _b):
            return self.anni

    assert staff.fine_della_carriera(66 * 108, Estrae(71.0)) == (71 * 108, False) and 71 * 108 == 66 * 108 + 540
    assert staff.fine_della_carriera(73 * 108, Estrae(70.0)) == (73 * 108 + 540, True)



def test_la_prelazione_si_conta_a_fine_avanzamento(mondo):
    # La terza revisione: dopo un recupero lungo la prelazione può essere già scaduta, e la notizia diceva comunque dieci giorni.
    mondo.fonda_polisportiva("Club di prova")
    ora = adesso_utc()
    fine = ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE)
    ancora, scaduto = _allenatore(mondo, 20), _allenatore(mondo, 25)
    for x in (ancora, scaduto):
        x.riservato_fino = fine
    ancora.prelazione, ancora.prelazione_fino = "Club di prova", INIZIO + datetime.timedelta(days=7)
    rapporto = Mondo.rapporto_vuoto(INIZIO)
    rapporto["tue_prelazioni"] = 2
    mondo._notizia_dei_riservati(ora, rapporto)
    assert rapporto["tue_prelazioni"] == 1 and rapporto["prelazione_fino"] == ancora.prelazione_fino
    frasi = " ".join(testi._fatti_dello_staff(rapporto))
    assert f"puoi assumerlo prima degli altri fino al {testi.data_breve(ancora.prelazione_fino)}, dal mercato" in frasi
    # Chi ha perso la prelazione nel recupero resta soltanto fra i riservati, con la sua scadenza di due ore.
    assert " a te fino alle " in rapporto["riservati"] and testi.nome_completo(scaduto) in rapporto["riservati"]
