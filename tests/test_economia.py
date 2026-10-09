"""
Test della tappa 8: l'economia delle decisioni D22 e D23. Stipendi, ingaggi, sponsor e valori di
mercato; i conti del primo del mese, con arretrati, pazienza, partenze e bandiere; pagamenti,
vendite, acquisti e offerte d'acquisto; le scelte del computer; la migrazione al formato 4, che dalla
tappa 9 prosegue fino al 5; i testi.
"""

import datetime
import json
import math
import random

import pytest
from aiuti_formati import al_formato_5

import archivio
import economia
import mondo as modulo_mondo
import testi
from costanti import CAPITALE_INIZIALE, FILE_MONDO, QUOTA_SPONSOR_SUL_VALORE, SPONSOR_PER_GLORIA, STIPENDIO_DI_RIFERIMENTO, VALORE_DI_RIFERIMENTO
from modelli import Giocatore
from mondo import Mondo

INIZIO = datetime.datetime(2026, 5, 15, 12, 0)
PRIMO = datetime.datetime(2026, 6, 1, 12, 0)
SECONDO = datetime.datetime(2026, 7, 1, 12, 0)


@pytest.fixture
def mondo():
    random.seed(808)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(40, INIZIO, annuncia=False)
    return m


def _rapporto():
    return Mondo.rapporto_vuoto(PRIMO)


def _club(mondo, quanti, nome="Club di prova"):
    poli = mondo.fonda_polisportiva(nome)
    for gid in range(1, quanti + 1):
        mondo._tessera(poli, mondo.giocatori[gid])
    return poli


def _cpu(mondo, ids, gloria=10_000):
    poli = mondo.polisportive[mondo.crea_polisportiva_cpu(INIZIO)]
    poli.gloria = gloria
    for gid in ids:
        mondo._tessera(poli, mondo.giocatori[gid])
    return poli


def _euro(importo):
    return economia.scritta_in_euro(importo)


# I calcoli.

def test_stipendio_valore_tratti_ed_esperienza():
    random.seed(1)
    g = Giocatore(id_giocatore=1, datetime_creazione_sim=INIZIO)
    g.ambidestro = g.giocorapido = g.cambiovelocita = False
    g.indice_collettivo_valore = VALORE_DI_RIFERIMENTO
    assert economia.stipendio(g) == STIPENDIO_DI_RIFERIMENTO
    g.indice_collettivo_valore = VALORE_DI_RIFERIMENTO + 40
    assert economia.stipendio(g) == economia.arrotonda(STIPENDIO_DI_RIFERIMENTO * math.e)
    base = economia.stipendio(g)
    g.ambidestro = True
    assert economia.stipendio(g) > base
    g.ambidestro = False
    g.esperienza = 10.
    assert economia.stipendio(g) == economia.arrotonda(STIPENDIO_DI_RIFERIMENTO * math.e * 1.3)
    assert economia.valore_di_mercato(g) == economia.arrotonda(economia.stipendio(g) * 6, 100)
    assert economia.scritta_in_euro(12345) == "12.345 euro"


def test_ingaggio_reputazione_e_sponsor(mondo):
    g = mondo.giocatori[1]
    poli = mondo.fonda_polisportiva("Club di prova")
    poli.gloria = 10 ** 6
    assert economia.fattore_reputazione(g, poli) == .5
    assert economia.ingaggio_richiesto(g, poli) == economia.arrotonda(economia.stipendio(g) * 2 * .5)
    poli.gloria = 1
    assert economia.fattore_reputazione(g, poli) == 2.
    poli.gloria = 100
    # Dalla tappa 11 lo sponsor è metà per la gloria e metà per il valore della rosa.
    assert economia.sponsor_mensile(poli, []) == economia.arrotonda(100 * SPONSOR_PER_GLORIA)
    rosa = [mondo.giocatori[gid] for gid in (1, 2, 3)]
    atteso = economia.arrotonda(100 * SPONSOR_PER_GLORIA + QUOTA_SPONSOR_SUL_VALORE * sum(economia.valore_di_mercato_pieno(g) for g in rosa))
    assert economia.sponsor_mensile(poli, rosa) == atteso
    rosa[0].ritirato = True
    assert economia.sponsor_mensile(poli, rosa) < atteso


def test_l_offerta_e_un_ingaggio(mondo, monkeypatch):
    poli = mondo.fonda_polisportiva("Club di prova")
    g = mondo.giocatori[1]
    richiesta = economia.ingaggio_richiesto(g, poli)
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: False)
    accetta, probabilita = mondo.offerta(poli, g, richiesta)
    assert not accetta and probabilita == pytest.approx(50.)
    assert poli.cassa == CAPITALE_INIZIALE
    assert g.diario[0]["testo"] == f"Rifiuta l'offerta di Club di prova, con un ingaggio di {_euro(richiesta)}."
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    generoso = round(richiesta * 1.3) + 10
    accetta, probabilita = mondo.offerta(poli, g, generoso)
    assert accetta and probabilita == 97.
    assert poli.cassa == CAPITALE_INIZIALE - generoso
    assert poli.conti_del_mese["ingaggi"] == generoso
    assert g.appartenenza == "Club di prova" and g.fedelta == 0 and g.pazienza == 100 and g.arretrati == 0
    assert mondo.problema_offerta(poli, mondo.giocatori[2], poli.cassa + 1).startswith("La cassa di Club di prova ha ")


# I conti del primo del mese.

def test_il_primo_del_mese_con_la_cassa_che_basta(mondo):
    poli = _club(mondo, 3)
    sponsor = mondo.sponsor(poli)
    rapporto = _rapporto()
    mondo._primo_del_mese(PRIMO, rapporto)
    monte = mondo.monte_stipendi(poli)
    assert poli.cassa == CAPITALE_INIZIALE + sponsor - monte
    assert poli.bilanci == [{"data": PRIMO, "cassa": poli.cassa, "sponsor": sponsor, "vendite": 0, "stipendi": monte, "arretrati": 0, "ingaggi": 0, "acquisti": 0,
                             "buonuscite": 0}]
    assert set(poli.conti_del_mese.values()) == {0}
    for gid in poli.tesserati:
        g = mondo.giocatori[gid]
        # Dalla tappa 11 l'esperienza non cresce più il primo del mese ma ogni giorno, in _allenamento_del_giorno.
        assert g.fedelta == 2. and g.esperienza == 0.0 and g.arretrati == 0 and g.pazienza == 100
    assert rapporto["tuoi_non_pagati"] == 0


def test_senza_soldi_si_aspetta_e_poi_si_se_ne_va(mondo):
    poli = _club(mondo, 3)
    bandiera = mondo.giocatori[3]
    bandiera.bandiera = True
    bandiera.fedelta = 90.
    poli.cassa = 0
    poli.gloria = 1
    rapporto = _rapporto()
    sponsor = mondo.sponsor(poli)
    mondo._primo_del_mese(PRIMO, rapporto)
    rosa = [mondo.giocatori[gid] for gid in (1, 2, 3)]
    assert poli.cassa == sponsor
    assert all(g.arretrati == economia.stipendio_pagato(g) for g in rosa)
    assert rapporto["tuoi_non_pagati"] == 3
    assert 0 < rosa[0].pazienza < 100 and bandiera.pazienza == 100
    assert testi.umore(rosa[0]) == ("pronto ad andarsene" if rosa[0].sesso == "m" else "pronta ad andarsene")
    rapporto = _rapporto()
    mondo._primo_del_mese(SECONDO, rapporto)
    assert poli.tesserati == [3]
    assert rapporto["tuoi_partiti"] == rapporto["partiti"] == 2
    assert rosa[0].appartenenza == "*" and rosa[0].arretrati == 0
    assert rosa[0].diario[0]["testo"].startswith("Lascia Club di prova: aspettava ")
    assert bandiera.appartenenza == "Club di prova" and bandiera.arretrati > 0
    assert testi.umore(bandiera) == "paziente, da bandiera"


def test_pagare_gli_arretrati_rende_pazienza(mondo):
    poli = _club(mondo, 1)
    g = mondo.giocatori[1]
    poli.cassa = 0
    poli.gloria = 1
    mondo._primo_del_mese(PRIMO, _rapporto())
    dovuto = g.arretrati
    assert g.pazienza < 100
    poli.cassa = 10_000
    mondo.paga(poli, g, dovuto)
    assert g.arretrati == 0 and g.pazienza == pytest.approx(100.)
    assert poli.cassa == 10_000 - dovuto and poli.conti_del_mese["arretrati"] == dovuto
    assert g.diario[0]["testo"] == f"Riceve da Club di prova {_euro(dovuto)} di stipendi arretrati."
    with pytest.raises(ValueError, match="aspetta"):
        mondo.paga(poli, g, 1)
    with pytest.raises(ValueError, match="non è"):
        mondo.paga(poli, mondo.giocatori[5], 1)


def test_il_computer_senza_soldi_paga_i_meno_pazienti_e_vende(mondo, monkeypatch):
    poli = _cpu(mondo, (1, 2, 3))
    poli.cassa = 0
    poli.gloria = 1
    # Uno sponsor piccolo, che basta soltanto per una parte di uno stipendio.
    sponsor = 20
    monkeypatch.setattr(modulo_mondo, "sponsor_mensile", lambda _poli, _rosa: sponsor)
    pazienti, impaziente = mondo.giocatori[1], mondo.giocatori[2]
    impaziente.pazienza = 95.
    mondo._primo_del_mese(PRIMO, _rapporto())
    assert impaziente.arretrati == economia.stipendio_pagato(impaziente) - sponsor
    assert pazienti.arretrati == economia.stipendio_pagato(pazienti)
    caro = max((mondo.giocatori[gid] for gid in (1, 2, 3)), key=economia.stipendio_pagato)
    assert poli.in_vendita == {caro.id: economia.valore_di_mercato(caro, PRIMO)}


# Vendite, acquisti e offerte d'acquisto.

def test_il_computer_compra_chi_e_in_vendita(mondo):
    mia = _club(mondo, 1)
    g = mondo.giocatori[1]
    for gid, altro in mondo.giocatori.items():
        if gid != 1:
            altro.ritirato = True
    cpu = _cpu(mondo, ())
    cpu.cassa = 1_000_000
    troppo = round(economia.valore_di_mercato(g) * 1.5)
    mondo.metti_in_vendita(mia, g, troppo)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (0, 0, 0)
    prezzo = economia.valore_di_mercato(g)
    mondo.metti_in_vendita(mia, g, prezzo)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (0, 0, 1)
    assert g.appartenenza == cpu.nome and mia.in_vendita == {} and mia.tesserati == []
    assert mia.cassa == CAPITALE_INIZIALE + prezzo and mia.conti_del_mese["vendite"] == prezzo
    assert cpu.conti_del_mese["acquisti"] == prezzo
    assert g.diario[0]["testo"] == f"{testi.accorda(g, 'Venduto')} da Club di prova a {cpu.nome} per {_euro(prezzo)}."


def test_comprare_chi_e_in_vendita(mondo):
    mia = mondo.fonda_polisportiva("Club di prova")
    cpu = _cpu(mondo, (5,))
    g = mondo.giocatori[5]
    assert mondo.problema_acquisto(mia, g) == f"{g.nome} {g.cognome} non è in vendita."
    mondo.metti_in_vendita(cpu, g, 1000)
    cassa_cpu = cpu.cassa
    assert mondo.acquista(mia, g) == 1000
    assert g.appartenenza == "Club di prova" and mia.cassa == CAPITALE_INIZIALE - 1000 and cpu.cassa == cassa_cpu + 1000
    assert mia.movimenti_oggi == 1
    assert mia.diario[0]["testo"] == f"Comprato {g.nome} {g.cognome} da {cpu.nome} per 1.000 euro."


def test_offerta_d_acquisto_al_computer(mondo):
    mia = mondo.fonda_polisportiva("Club di prova")
    cpu = _cpu(mondo, (1, 2, 3))
    for gid, valore in ((1, 120.), (2, 140.), (3, 160.)):
        mondo.giocatori[gid].indice_collettivo_valore = valore
    forte, debole = mondo.giocatori[3], mondo.giocatori[1]
    assert mondo.posizione_in_rosa(forte) == (1, 3)
    assert mondo.soglia_di_vendita(cpu, forte) == economia.arrotonda(economia.valore_di_mercato(forte) * 1.5, 100)
    assert mondo.soglia_di_vendita(cpu, debole) == economia.arrotonda(economia.valore_di_mercato(debole), 100)
    soglia = mondo.soglia_di_vendita(cpu, forte)
    assert not mondo.offerta_d_acquisto(mia, forte, soglia - 100)
    assert forte.appartenenza == cpu.nome and mia.movimenti_oggi == 1
    assert mia.diario[0]["testo"].endswith("offerta rifiutata.")
    assert mondo.offerta_d_acquisto(mia, forte, soglia)
    assert forte.appartenenza == "Club di prova" and mia.cassa == CAPITALE_INIZIALE - soglia
    with pytest.raises(ValueError, match="polisportiva del computer"):
        mondo.offerta_d_acquisto(mia, mondo.giocatori[10], 100)


def test_il_computer_tessera_solo_chi_puo_pagare(mondo, monkeypatch):
    cpu = _cpu(mondo, ())
    cpu.cassa = 0
    monkeypatch.setattr(modulo_mondo, "caso", lambda p: True)
    assert mondo._esegui_logica_cpu_polisportive(INIZIO) == (0, 0, 0)
    assert cpu.movimenti_oggi == 0
    cpu.cassa = 1_000_000
    tesserati, _s, _c = mondo._esegui_logica_cpu_polisportive(INIZIO)
    assert tesserati > 0
    assert cpu.cassa == 1_000_000 - cpu.conti_del_mese["ingaggi"]


# Il salvataggio e i testi.

def test_un_salvataggio_del_formato_3_si_aggiorna(mondo, cartella_di_prova):
    poli = _club(mondo, 2)
    for gid in (1, 2):
        mondo.giocatori[gid].diario[0]["data"] = INIZIO - datetime.timedelta(days=90)
    contenuto = al_formato_5(archivio.componi(mondo))
    dati = contenuto["mondo"]
    for p in dati["polisportive"].values():
        for campo in ("cassa", "in_vendita", "bilanci", "conti_del_mese"):
            del p[campo]
    for g in dati["giocatori"]:
        for campo in ("esperienza", "fedelta", "pazienza", "arretrati", "bandiera"):
            del g[campo]
    contenuto["formato"] = 3
    percorso = cartella_di_prova / FILE_MONDO
    percorso.write_text(json.dumps({**contenuto, "firma": archivio.firma(contenuto)}), encoding="utf-8")
    ricaricato = Mondo()
    archivio.carica(ricaricato)
    assert ricaricato.polisportive[poli.nome].cassa == CAPITALE_INIZIALE
    assert ricaricato.giocatori[1].fedelta == 6. and ricaricato.giocatori[1].esperienza == pytest.approx(.3)
    assert ricaricato.giocatori[5].fedelta == 0. and ricaricato.giocatori[5].pazienza == 100.
    assert all(g.bandiera == (g.id % 100 == 0) for g in ricaricato.giocatori.values())
    assert archivio.salva(ricaricato)
    assert archivio.leggi(percorso)["formato"] == archivio.FORMATO == 6


def test_i_testi_dell_economia(mondo):
    poli = _club(mondo, 2)
    g = mondo.giocatori[1]
    scheda = testi.scheda_giocatore(g, mondo)
    assert f"Stipendio: {_euro(economia.stipendio(g))} al mese, fisso fino al " in scheda and " | Valore di mercato: " in scheda
    assert "Fedeltà a Club di prova: 0 su 100 | Umore: sereno" in scheda
    assert "Punti allenamento: " in scheda
    g.arretrati = 300
    g.pazienza = 40.
    assert testi.umore(g) == "insofferente"
    assert "aspetta 300 euro di stipendi arretrati, e pazienterà ancora " in testi.scheda_giocatore(g, mondo)
    mondo.metti_in_vendita(poli, mondo.giocatori[2], 2500)
    bilancio = testi.bilancio(poli, mondo)
    assert "\n\n" not in bilancio
    assert bilancio.startswith(f"Bilancio di Club di prova: in cassa {_euro(poli.cassa)}.")
    assert "Arretrati da pagare: 300 euro, a 1 tesserato." in bilancio
    assert "a 2.500 euro" in bilancio
    scheda_poli = testi.scheda_polisportiva(poli, mondo)
    assert "[CONTI]" in scheda_poli and f"Cassa: {_euro(poli.cassa)} | Sponsor: " in scheda_poli
    assert ", in vendita a 2.500 euro" in scheda_poli
    assert testi.riga_arretrati(g).startswith(f"{g.nome} {g.cognome}, insofferente, aspetta 300 euro")


def test_la_posizione_in_rosa_a_parole():
    assert testi.posizione_in_rosa(1, 1) == "È l'unico della sua rosa"
    assert testi.posizione_in_rosa(1, 3) == "È il più forte dei 3 della sua rosa"
    assert testi.posizione_in_rosa(2, 15) == "È il 2° più forte dei 15 della sua rosa"
