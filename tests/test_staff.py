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
    atteso = staff.fattori(q, q / 2)
    assert tesserato.fattore_staff == pytest.approx(atteso[0]) and tesserato.fattore_rischio_staff == pytest.approx(atteso[1])
    assert atteso[0] > 1.0 > atteso[1]
    assert dell_altro.fattore_staff == libero.fattore_staff == 0.85 and libero.fattore_rischio_staff == 1.15
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
    # Lo staff migliore cresce del 25 per cento, chi non ne ha cala all'85 per cento.
    g.fedelta = h.fedelta = 0.0
    mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE, INIZIO)
    mondo._aggiungi_fedelta(h, altro, FEDELTA_PER_MESE, INIZIO)
    assert g.fedelta == pytest.approx(FEDELTA_PER_MESE * 1.25) and h.fedelta == pytest.approx(FEDELTA_PER_MESE * 0.85)


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


# Il passo 2: lo stipendio, l'ingaggio, i contratti, la paga e le mosse del computer.

def test_lo_stipendio_va_in_linea_retta_sulla_qualita(mondo):
    a1, h0 = _allenatore(mondo, 1), _allenatore(mondo, LIVELLO_MINIMO_ALLENATORE)
    assert staff.stipendio_richiesto(a1, staff.CAPO) == STIPENDIO_STAFF_MASSIMO and staff.stipendio_richiesto(h0, staff.CAPO) == STIPENDIO_STAFF_MINIMO
    assert staff.stipendio_richiesto(a1, staff.ASSISTENTE) == STIPENDIO_STAFF_MASSIMO * QUOTA_STIPENDIO_ASSISTENTE
    medio = _allenatore(mondo, 35)
    assert STIPENDIO_STAFF_MINIMO < staff.stipendio_richiesto(medio, staff.CAPO) < STIPENDIO_STAFF_MASSIMO
    assert staff.ingaggio_richiesto(a1, staff.CAPO) == STIPENDIO_STAFF_MASSIMO * MESI_DI_INGAGGIO
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
    assert assunti == 3 and all(cpu.staff) and in_prelazione.libero
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


def test_un_ora_di_riserva_per_l_utente(mondo):
    # Regola di Gabriele del 21 ottobre 2026, risposta 29: chi diventa allenatore resta dell'utente per un'ora vera.
    cpu = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    cpu.cassa = 100_000
    for a in list(mondo.allenatori.values()):
        del mondo.allenatori[a.numero]
    ora = datetime.datetime(2026, 10, 21, 20, 0, tzinfo=datetime.UTC)
    mondo._ora_reale = ora
    a = mondo._nasce_un_allenatore(INIZIO)
    assert a.riservato_fino == ora + datetime.timedelta(minutes=MINUTI_RISERVA_UTENTE) == ora + datetime.timedelta(hours=1)
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
    assert nuovo.allenatori and all(prima + datetime.timedelta(minutes=59) < a.riservato_fino <= adesso_utc() + datetime.timedelta(minutes=60)
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
    assert "riservato a te fino alle" in testi.riga_allenatore(libero, mondo)


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
    assert "il mercato degli allenatori è aperto, con 1 allenatore libero" in testo and "per un'ora sono riservati a te" in testo
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
