"""
Le prove dei luoghi di provenienza, tappa 13, richiesta di Gabriele del 22 ottobre 2026: la collezione dei
comuni, l'estrazione pesata con la popolazione e indipendente dal caso del mondo, le parole della scheda, i
giocatori e gli allenatori che nascono con un comune, l'ex giocatore che tiene il suo, e l'aggiornamento
dal formato 7 che lo dà anche ai giocatori dei mondi vecchi.
"""

import collections
import datetime
import json
import random

import archivio
import luoghi
import staff
import testi
from modelli import Giocatore
from mondo import Mondo

INIZIO = datetime.datetime(2026, 5, 15, 12, 0)


def test_la_collezione_e_tutta_di_comuni_con_gli_abitanti():
    tabella = luoghi._carica()
    assert len(tabella["comuni"]) == 1291 and tabella["totale"] == 37_399_284 and not luoghi.avvisi
    assert luoghi.provincia_e_regione("Avezzano") == ("L'Aquila", "Abruzzo") and luoghi.provincia_e_regione("Atlantide") is None


def test_l_estrazione_segue_la_popolazione_e_non_tocca_il_caso_del_mondo():
    random.seed(7)
    prima = random.random()
    random.seed(7)
    estratti = collections.Counter(luoghi.luogo_del_giocatore(i) for i in range(1, 40_001))
    assert random.random() == prima
    tabella = luoghi._carica()
    abitanti = {comune: totale - (tabella["cumulati"][i - 1] if i else 0) for i, (comune, totale) in enumerate(zip(tabella["comuni"], tabella["cumulati"], strict=True))}
    # Roma ha il 7,3 per cento degli abitanti della collezione: su 40.000 estrazioni, 2.940 attese.
    atteso = 40_000 * abitanti["Roma"] / tabella["totale"]
    assert abs(estratti["Roma"] - atteso) < 4 * atteso ** 0.5
    assert estratti["Milano"] > estratti["Bologna"] > estratti["Pescocostanzo"]
    # Lo stesso numero dà sempre lo stesso comune.
    assert luoghi.luogo_del_giocatore(123) == luoghi.luogo_del_giocatore(123)


def test_la_provenienza_a_parole():
    assert luoghi.descrivi("Avezzano") == "Avezzano, provincia dell'Aquila, Abruzzo"
    assert luoghi.descrivi("Chieti") == "Chieti, provincia di Chieti, Abruzzo"
    assert luoghi.descrivi("La Spezia").endswith("provincia della Spezia, Liguria")
    assert luoghi.descrivi("Atlantide") == "Atlantide"


def test_giocatori_e_allenatori_nascono_con_un_comune():
    random.seed(3)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(10, INIZIO, annuncia=False)
    g = m.giocatori[1]
    assert g.luogo == luoghi.luogo_del_giocatore(1) and f"Provenienza: {luoghi.descrivi(g.luogo)}" in testi.scheda_giocatore(g, m)
    nato = m._nasce_un_allenatore(INIZIO, random.Random(1))
    assert nato.luogo == luoghi.luogo_dell_allenatore(nato.numero) and f"Provenienza: {luoghi.descrivi(nato.luogo)}" in testi.scheda_allenatore(nato, m)
    ex = staff.ex_giocatore(m.nuovo_numero_allenatore(), g, INIZIO, random.Random(2))
    assert ex.luogo == g.luogo
    # Il comune va e torna dal salvataggio.
    copia = staff.Allenatore.da_dizionario(json.loads(json.dumps(nato.a_dizionario())))
    assert copia.luogo == nato.luogo


def test_l_aggiornamento_dal_formato_7_da_un_comune_a_tutti():
    random.seed(5)
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    m.crea_giocatori_casuali(12, INIZIO, annuncia=False)
    contenuto = archivio.componi(m)
    contenuto["formato"] = 7
    dati = contenuto["mondo"]
    for g in dati["giocatori"]:
        del g["classe_migliore"], g["luogo"]
    for p in dati["polisportive"].values():
        del p["staff"]
    del dati["allenatori"], dati["prossimo_allenatore"]
    archivio.MIGRAZIONI[7](contenuto)
    nuovo = Mondo()
    archivio.costruisci(contenuto, nuovo)
    assert all(g.luogo == luoghi.luogo_del_giocatore(gid) for gid, g in nuovo.giocatori.items())


def test_un_giocatore_senza_luogo_non_ha_la_riga():
    m = Mondo()
    m.datetime_corrente_simulazione = INIZIO
    g = Giocatore(1, INIZIO)
    g.luogo = ""
    m.giocatori[1] = g
    assert "Provenienza" not in testi.scheda_giocatore(g, m)
