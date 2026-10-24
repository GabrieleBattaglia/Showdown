"""
Il banco dei tempi della finestra unica Mercato e ricerca di MESS, issue 8 e decisione D36.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-24 col passo 2 della proposta della issue 8: misura il motore della finestra, in
mercato.py, su un mondo a regime di strumenti/mondi_sintetici.py, quello dello studio della issue: 20.000
giocatori in attività, un terzo di ritirati, le polisportive del computer per nove tesserati su dieci,
2.900 allenatori quasi tutti impiegati, l'1% dei tesserati del computer in vendita, e due polisportive tue,
Pat-Bologna attiva con 12 tesserati e Pat-Milano con 4, uno dei quali in vendita a 1 euro. L'obiettivo della
proposta è ogni ricalcolo sotto i 300 ms dopo la pausa, e l'apertura sotto i 300 ms, sul Gigante.
Un ricalcolo è quello che la finestra fa dopo un filtro: la ricerca, le righe che l'elenco virtuale chiede
per prime, trenta, l'etichetta dei trovati e Filtri attivi. Si misura in due modi. A freddo, con una memoria
nuova, come all'apertura della finestra, quando classe e valore di mercato non sono ancora calcolati; a caldo,
con la memoria della finestra già usata, come per ogni ricalcolo seguente. Per ogni misura la mediana e il
peggiore di più prove. A mondo pronto la memoria si mette da parte per la raccolta dei cicli, come fa il programma
dopo il caricamento con archivio.congela_la_memoria. Non scrive niente nel progetto: le cartelle del programma e del mondo si spostano in una
temporanea, che alla fine si cancella, e il caso del mondo si rimette com'era. Il rapporto si scrive solo
quando lo si chiede.
Lo stesso giorno, coi preset dei filtri, le ricerche pronte che misura sono i dodici preset di serie, e le aperture
partono dallo stato di serie di ogni porta. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
La sera dello stesso giorno, col motore del costruttore di regole, il mondo ha anche l'1% dei ritirati uscito di scena,
e banco_delle_regole fa le stesse misure con le regole: le aperture delle porte con la memoria nuova, che costruisce
tutte le righe, la ricerca veloce sul Mercato un tasto alla volta, i preset di serie, le regole a mano e tutti i 41
ordini sulle due liste insieme. L'obiettivo di 300 ms vale per le aperture di Ctrl+K, Ctrl+Maiusc+G e Ctrl+F; quella di
Ctrl+O si confronta col motore di prima, e non deve andare peggio. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude
Opus 5.5, UltraCode).
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/banco_mercato.py
    python strumenti/banco_mercato.py --attivi 20000 --volte 5 --rapporto
"""

import argparse
import platform
import random
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
for _cartella in (RADICE, RADICE / "strumenti"):
    if str(_cartella) not in sys.path:
        sys.path.insert(0, str(_cartella))

import mondi_sintetici as ms  # noqa: E402

import archivio  # noqa: E402
import economia  # noqa: E402
import mercato  # noqa: E402
import percorsi  # noqa: E402
import staff  # noqa: E402
import testi  # noqa: E402
from version import __version__  # noqa: E402

RAPPORTO_PREDEFINITO = RADICE / "strumenti" / "banco_mercato.txt"
# L'obiettivo della proposta, in millisecondi, e le righe che l'elenco virtuale chiede appena si riempie.
OBIETTIVO = 300.0
RIGHE_VISIBILI = 30
# Gli allenatori del mondo a regime dello studio: 2.900 per 20.000 attivi, quasi tutti impiegati.
ALLENATORI_PER_ATTIVO = 2900 / 20000
LIBERI_DELLO_STAFF = 7
# Le misure di filtri a mano, oltre alle ricerche pronte: il nome, il campo che dice e i filtri.
TUTTI = {"liberi": True, "in_vendita": True, "del_computer": True, "tuoi": True}
FILTRI_A_MANO = (
    ("tutti, donne fino a 25 anni", {**TUTTI, "sesso": "f", "eta_massima": 25}),
    ("tutti, classe migliore o uguale a E0", {**TUTTI, "classe_migliore": 50}),
    ("tutti, classe fra D0 e F0", {**TUTTI, "classe_migliore": 50, "classe_peggiore": 30}),
    ("tutti, cognome che contiene ros", {**TUTTI, "nome": "ros"}),
    ("tutti, numero che comincia con 12", {**TUTTI, "nome": "12"}),
    ("tutti, in Lombardia", {**TUTTI, "regione": "Lombardia"}),
    ("tutti, comune che contiene san", {**TUTTI, "comune": "san"}),
    ("tutti, mancini con talento", {**TUTTI, "tratti": {"mancino": True, "talento": True}}),
    ("tutti, bomba centrale maggiore di 12 e valore maggiore di 150", {**TUTTI, "condizioni": (("bomba_base", "maggiore", 12.0), ("valore", "maggiore", 150.0))}),
    ("tutti, valore minimo 150 e stipendio massimo 2.000 euro", {**TUTTI, "valore_minimo": 150, "stipendio_massimo": 2000}),
    ("tutti, senza infortunati né acciaccati", {**TUTTI, "senza_acciacchi": True}),
    ("tutti, mesi di contratto al massimo 6", {**TUTTI, "mesi_contratto_massimi": 6}),
    ("liberi e in vendita, costo massimo 5.000 euro", {"liberi": True, "in_vendita": True, "costo_massimo": 5000}),
    ("tesserati del computer, ordine per prezzo sul valore di mercato", {"del_computer": True, "ordine": "prezzo_sul_mercato"}),
    ("tutti e i ritirati, disponibili oggi", {**TUTTI, "ritirati": True, "disponibili_oggi": True}),
    ("ritirati che allenano", {"ritirati": True, "solo_ritirati_che_allenano": True}),
    ("ritirati e usciti di scena", {"ritirati": True, "comprendi_usciti": True}),
    ("tutti, otto filtri insieme", {**TUTTI, "sesso": "m", "eta_massima": 40, "classe_migliore": 70, "regione": "Lombardia", "tratti": {"ipovedente": False},
                                    "valore_minimo": 100, "stipendio_massimo": 5000, "condizioni": (("difesa_base", "maggiore", 5.0),)}),
    ("allenatori di tutti, uomini vedenti", {"allenatori": True, "liberi": True, "del_computer": True, "tuoi": True, "sesso": "m", "visus": staff.VEDENTE}),
)


def millisecondi(valore):
    return f"{valore:.1f}".replace(".", ",") + " ms"


def costruisci_mondo(attivi, seme, scrivi=print):
    """
    Il mondo a regime dello studio della issue 8, con gli allenatori, le vendite, le due polisportive tue, qualche
    impegno di oggi e i nuovi arrivati della sessione. Non tocca il caso del mondo. Restituisce il mondo.
    """
    inizio = time.perf_counter()
    ritirati = attivi // 3
    polisportive = max(2, int(attivi * 0.9 / 15))
    mondo = ms.mondo_a_regime(attivi, ritirati, polisportive, seme)
    oggi = mondo.datetime_corrente_simulazione
    rng = random.Random(f"banco-mercato-{seme}")
    stato = random.getstate()
    try:
        random.seed(seme)
        cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
        quanti = max(LIBERI_DELLO_STAFF + 1, round(attivi * ALLENATORI_PER_ATTIVO))
        allenatori = [mondo._nasce_un_allenatore(oggi, rng) for _ in range(quanti)]
        posti = [(p, posto) for p in cpu for posto in range(staff.POSTI)]
        rng.shuffle(posti)
        for a, (p, posto) in zip(allenatori[:quanti - LIBERI_DELLO_STAFF], posti, strict=False):
            a.prelazione = a.prelazione_fino = a.riservato_fino = None
            mondo.assumi_allenatore(p, a, posto, oggi)
        tesserati = [g for g in mondo.giocatori.values() if g.appartenenza != "*" and not g.ritirato]
        for g in rng.sample(tesserati, max(1, len(tesserati) // 100)):
            mondo.polisportive[g.appartenenza].in_vendita[g.id] = max(1, economia.valore_di_mercato(g, oggi))
        mia = mondo.fonda_polisportiva("Pat-Bologna", luogo="Bologna")
        altra = mondo.fonda_polisportiva("Pat-Milano", attiva=False, luogo="Milano")
        liberi = sorted((g for g in mondo.giocatori.values() if g.appartenenza == "*" and not g.ritirato), key=lambda g: g.id)
        for g in liberi[:12]:
            mondo._entra(mia, g, oggi)
        for g in liberi[12:16]:
            mondo._entra(altra, g, oggi)
        altra.in_vendita[liberi[12].id] = 1
        vivi = [g for g in mondo.giocatori.values() if not g.ritirato]
        for g in rng.sample(vivi, len(vivi) // 20):
            g.ultimo_impegno = oggi
        mondo.nuovi_giocatori_sessione = sorted(mondo.giocatori)[-max(1, len(mondo.giocatori) // 100):]
        # Qualche ritirato che allena, come nel mondo vero: un allenatore nato dal giocatore.
        ritirati_del_mondo = sorted((g for g in mondo.giocatori.values() if g.ritirato), key=lambda g: g.id)
        for g in ritirati_del_mondo[:20]:
            mondo._ex_giocatore_allenatore(g, None, oggi, rng=rng)
        # E l'1% dei ritirati uscito di scena nella sessione, che il motore delle regole scorre insieme a tutti gli altri.
        for g in ritirati_del_mondo[20:20 + max(1, len(ritirati_del_mondo) // 100)]:
            mondo._ids_morti_processati_sessione.add(g.id)
    finally:
        random.setstate(stato)
    liberi_dello_staff = sum(1 for a in mondo.allenatori.values() if a.libero)
    in_vendita = sum(len(p.in_vendita) for p in mondo.polisportive.values())
    secondi = f"{time.perf_counter() - inizio:.1f}".replace(".", ",")
    usciti = len(mondo._ids_morti_processati_sessione)
    scrivi(f"Mondo a regime del seme {seme}: {len(mondo.giocatori)} giocatori, {attivi} in attività, {ritirati} ritirati di cui {usciti} usciti di scena, "
           f"{polisportive} polisportive del computer e 2 tue, {in_vendita} giocatori in vendita, {len(mondo.allenatori)} allenatori di cui {liberi_dello_staff} "
           f"liberi; costruito in {secondi} secondi.")
    return mondo


def ricalcolo(mondo, filtri, memoria):
    """Quello che la finestra fa dopo un filtro: la ricerca, le prime righe dell'elenco, l'etichetta e Filtri attivi. Restituisce le righe."""
    righe = mercato.cerca(mondo, filtri, memoria)
    ordine = filtri.ordine_scelto
    for riga in righe[:RIGHE_VISIBILI]:
        testi.riga_trovato(riga, mondo, ordine, memoria)
    testi.etichetta_trovati(len(righe), filtri.allenatori)
    testi.filtri_attivi(filtri, mondo)
    return righe


def _tempi(funzione, volte):
    """La mediana e il peggiore in millisecondi di volte esecuzioni, e l'ultimo risultato."""
    tempi = []
    risultato = None
    for _ in range(volte):
        inizio = time.perf_counter()
        risultato = funzione()
        tempi.append((time.perf_counter() - inizio) * 1000)
    return statistics.median(tempi), max(tempi), risultato


def banco(mondo, volte=5, scrivi=print):
    """
    Le misure del motore sul mondo dato: le aperture delle quattro porte, a freddo; i preset di serie e i
    filtri a mano, a freddo e a caldo; tutti gli ordini, a caldo; il costo di una riga. Restituisce un
    dizionario dal nome della misura alla mediana, al peggiore e alle righe trovate, e il più lento dei
    ricalcoli a caldo e delle aperture.
    """
    misure = {}

    def misura(nome, funzione, ripetizioni=volte):
        mediana, peggiore, righe = _tempi(funzione, ripetizioni)
        misure[nome] = (mediana, peggiore, len(righe) if righe is not None else 0)
        scrivi(f"{nome}: {misure[nome][2]} righe, mediana {millisecondi(mediana)}, peggiore {millisecondi(peggiore)}")

    scrivi("Le aperture delle porte, a freddo: una memoria nuova a ogni prova.")
    for porta in mercato.PORTE:
        filtri = mercato.stato_di_serie(porta).attuali
        misura(f"apertura di {porta}", lambda f=filtri: (testi.situazione(mondo), ricalcolo(mondo, f, mercato.Memoria(mondo)))[1])
    scrivi("I preset di serie, che erano le ricerche pronte, a freddo e a caldo.")
    memoria = mercato.Memoria(mondo)
    prove = [(nome, mercato.filtri_di_serie(chiave)) for chiave, nome in mercato.PRESET_DI_SERIE]
    prove += [(nome, mercato.Filtri(**campi)) for nome, campi in FILTRI_A_MANO]
    for posto, (nome, filtri) in enumerate(prove):
        if posto == len(mercato.PRESET_DI_SERIE):
            scrivi("I filtri a mano, a freddo e a caldo.")
        misura(f"{nome}, a freddo", lambda f=filtri: ricalcolo(mondo, f, mercato.Memoria(mondo)), max(1, volte // 2))
        misura(f"{nome}, a caldo", lambda f=filtri: ricalcolo(mondo, f, memoria))
    scrivi("Tutti gli ordini dei giocatori in attività e degli allenatori, a caldo.")
    for chiave, nome in mercato.ORDINI_GIOCATORI:
        misura(f"ordine {nome}", lambda k=chiave: ricalcolo(mondo, mercato.Filtri(**TUTTI, ordine=k), memoria), max(1, volte // 2))
    for chiave, nome in mercato.ORDINI_ALLENATORI:
        misura(f"ordine degli allenatori {nome}", lambda k=chiave: ricalcolo(mondo, mercato.Filtri(allenatori=True, liberi=True, del_computer=True, tuoi=True,
                                                                                                         ordine_allenatori=k), memoria), max(1, volte // 2))
    righe = mercato.cerca(mondo, mercato.Filtri(**TUTTI), memoria)[:1000]
    mediana, _peggiore, _ = _tempi(lambda: [testi.riga_trovato(r, mondo, "valore_alto", memoria) for r in righe], volte)
    lunghezze = sorted(len(testi.riga_trovato(r, mondo, "valore_alto", memoria)) for r in righe)
    if righe:
        scrivi(f"Una riga dell'elenco costa {mediana * 1000 / len(righe):.0f} microsecondi; su {len(righe)} righe la lunghezza va da {lunghezze[0]} a {lunghezze[-1]} "
               f"caratteri, mediana {lunghezze[len(lunghezze) // 2]}.")
    a_caldo = {nome: valori for nome, valori in misure.items() if not nome.endswith(", a freddo") and not nome.startswith("apertura")}
    aperture = {nome: valori for nome, valori in misure.items() if nome.startswith("apertura")}
    a_freddo = {nome: valori for nome, valori in misure.items() if nome.endswith(", a freddo")}
    piu_lento = max(a_caldo.items(), key=lambda voce: voce[1][0])
    apertura_lenta = max(aperture.items(), key=lambda voce: voce[1][0])
    freddo_lento = max(a_freddo.items(), key=lambda voce: voce[1][0])
    for etichetta, (nome, valori) in (("Il ricalcolo a caldo più lento", piu_lento), ("L'apertura più lenta", apertura_lenta),
                                      ("Il primo ricalcolo a freddo più lento", freddo_lento)):
        esito = "sotto" if valori[0] < OBIETTIVO else "sopra"
        scrivi(f"{etichetta}: {nome}, mediana {millisecondi(valori[0])}, {esito} l'obiettivo di {millisecondi(OBIETTIVO)}.")
    return {"misure": misure, "piu_lento": piu_lento, "apertura_lenta": apertura_lenta, "freddo_lento": freddo_lento}


# Il motore del costruttore di regole, dalla sera del 24 ottobre 2026: le stesse misure con le regole. L'obiettivo di
# 300 ms vale per le aperture di Ctrl+K, Ctrl+Maiusc+G e Ctrl+F; quella di Ctrl+O, che ordina per classe tutti quelli
# che oggi giocano, non deve andare peggio del motore di prima. Le regole a mano: il nome, cioè Ctrl+F sul Mercato, le
# alternative, i limiti col dato che manca, i luoghi, i tratti, le caratteristiche di gioco e le due liste insieme.
PORTE_DA_300_MS = ("mercato", "allenatori", "ricerca")
_G = mercato.GIOCATORI
_A = mercato.ALLENATORI
_IN_ATTIVITA = mercato.Regola(mercato.E, _G, "stato", "uguale", mercato.IN_ATTIVITA)


def _o(regola):
    return mercato.Regola(mercato.O, *(getattr(regola, campo) for campo in ("bersaglio", "caratteristica", "operatore", "valore")))


def _e(bersaglio, chiave, operatore, valore):
    return mercato.Regola(mercato.E, bersaglio, chiave, operatore, valore)


REGOLE_A_MANO = (
    ("in attività, donne fino a 25 anni", (_IN_ATTIVITA, _e(_G, "sesso", "uguale", "f"), _e(_G, "eta", "minore_uguale", 25))),
    ("in attività, classe fra D0 e F0", (_IN_ATTIVITA, _e(_G, "classe", "migliore_uguale", 50), _e(_G, "classe", "peggiore_uguale", 30))),
    ("in attività, nome che contiene ros", (_IN_ATTIVITA, _e(_G, "nome", "contiene", "ros"))),
    ("in attività, numero che comincia con 12", (_IN_ATTIVITA, _e(_G, "nome", "comincia", "12"))),
    ("in attività, in Lombardia", (_IN_ATTIVITA, _e(_G, "regione", "uguale", "Lombardia"))),
    ("in attività, comune che contiene san", (_IN_ATTIVITA, _e(_G, "comune", "contiene", "san"))),
    ("in attività, mancini con talento", (_IN_ATTIVITA, _e(_G, "mancino", "uguale", True), _e(_G, "talento", "uguale", True))),
    ("in attività, bomba centrale maggiore di 12 e valore maggiore di 150", (_IN_ATTIVITA, _e(_G, "bomba_base", "maggiore", 12.0), _e(_G, "valore", "maggiore", 150.0))),
    ("in attività, stipendio fino a 2.000 euro, o senza stipendio", (_IN_ATTIVITA, _e(_G, "stipendio", "minore_uguale", 2000), _o(_IN_ATTIVITA),
                                                                     _e(_G, "stipendio", "manca", None))),
    ("in attività, senza infortunati né acciaccati", (_IN_ATTIVITA, _e(_G, "acciaccato", "uguale", False))),
    ("in attività, mesi di contratto al massimo 6", (_IN_ATTIVITA, _e(_G, "mesi_contratto", "minore_uguale", 6))),
    ("sul mercato, costo fino a 5.000 euro", (_e(_G, "stato", "uguale", mercato.SUL_MERCATO), _e(_G, "costo", "minore_uguale", 5000))),
    ("ritirati che allenano", (_e(_G, "allena", "uguale", True),)),
    ("ritirati o usciti di scena", (_e(_G, "stato", "uguale", mercato.RITIRATO), _o(_e(_G, "stato", "uguale", mercato.USCITO)))),
    ("tre alternative: liberi, tuoi, mancini del computer", (_e(_G, "stato", "uguale", mercato.LIBERO), _o(_e(_G, "stato", "uguale", mercato.TUO)),
                                                            _o(_e(_G, "stato", "uguale", mercato.DEL_COMPUTER)), _e(_G, "mancino", "uguale", True))),
    ("in attività e allenatori uomini vedenti", (_IN_ATTIVITA, _o(_e(_A, "sesso", "uguale", "m")), _e(_A, "visus", "uguale", staff.VEDENTE))),
)
# Le due liste insieme, per gli ordini: chi è in attività, o un allenatore di qualunque stato.
TUTTI_E_GLI_ALLENATORI = (_IN_ATTIVITA, _o(_e(_A, "stato", "uguale", mercato.LIBERO)), _o(_e(_A, "stato", "uguale", mercato.DEL_COMPUTER)),
                          _o(_e(_A, "stato", "uguale", mercato.TUO)))


def ricalcolo_a_regole(mondo, filtri, preparazione, memoria):
    """
    Quello che la finestra del costruttore fa dopo una mossa: le regole che contano, la ricerca, le prime righe
    dell'elenco, l'etichetta, il campo Trovati e l'annuncio. Restituisce le righe.
    """
    contano = mercato.con_la_preparazione(filtri, preparazione)
    righe = mercato.cerca_a_regole(mondo, contano, memoria)
    for riga in righe[:RIGHE_VISIBILI]:
        testi.riga_trovato(riga, mondo, contano.ordine, memoria)
    testi.trovati(righe, contano)
    testi.riepilogo_dei_trovati(righe, filtri, preparazione, mondo)
    testi.annuncio_dei_trovati(righe, contano, preparazione)
    return righe


def banco_delle_regole(mondo, volte=5, scrivi=print):
    """
    Le misure del motore delle regole sul mondo dato: le aperture delle quattro porte a freddo, con la memoria nuova
    che costruisce tutte le righe; Ctrl+F sul Mercato, cioè il nome scritto nella preparazione, a caldo; i preset di
    serie e le regole a mano, a freddo e a caldo; tutti gli ordini sulle due liste insieme, a caldo. Restituisce un
    dizionario dal nome della misura alla mediana, al peggiore e alle righe, con le aperture da 300 ms e il ricalcolo a caldo più lento.
    """
    misure = {}

    def misura(nome, funzione, ripetizioni=volte):
        mediana, peggiore, righe = _tempi(funzione, ripetizioni)
        misure[nome] = (mediana, peggiore, len(righe) if righe is not None else 0)
        scrivi(f"{nome}: {misure[nome][2]} righe, mediana {millisecondi(mediana)}, peggiore {millisecondi(peggiore)}")

    scrivi("Le regole: le aperture delle porte, a freddo, con una memoria nuova che costruisce tutte le righe.")
    for porta in mercato.PORTE:
        stato_della_porta = mercato.stato_di_serie_a_regole(porta)
        misura(f"regole, apertura di {porta}", lambda s=stato_della_porta: (testi.situazione(mondo),
                                                                            ricalcolo_a_regole(mondo, s.attuali, s.preparazione, mercato.Memoria(mondo)))[1])
    memoria = mercato.Memoria(mondo)
    stato_del_mercato = mercato.stato_di_serie_a_regole("mercato")
    ricalcolo_a_regole(mondo, stato_del_mercato.attuali, stato_del_mercato.preparazione, memoria)
    scrivi("Le regole: la ricerca veloce sul Mercato, il nome scritto un tasto alla volta, a caldo.")
    for scritto in ("r", "ro", "ros", "rossi", "12"):
        preparazione = mercato.Preparazione(mercato.E, _G, "nome", "contiene", scritto)
        misura(f"regole, Mercato e nome {scritto}", lambda p=preparazione: ricalcolo_a_regole(mondo, stato_del_mercato.attuali, p, memoria))
    scrivi("Le regole: i preset di serie e le regole a mano, a freddo e a caldo.")
    vuota = mercato.Preparazione()
    prove = [(nome, mercato.filtri_di_serie_a_regole(chiave)) for chiave, nome in mercato.PRESET_DI_SERIE]
    prove += [(nome, mercato.FiltriARegole(regole)) for nome, regole in REGOLE_A_MANO]
    for nome, filtri in prove:
        misura(f"regole, {nome}, a freddo", lambda f=filtri: ricalcolo_a_regole(mondo, f, vuota, mercato.Memoria(mondo)), max(1, volte // 2))
        misura(f"regole, {nome}, a caldo", lambda f=filtri: ricalcolo_a_regole(mondo, f, vuota, memoria))
    scrivi("Le regole: tutti gli ordini, sui giocatori in attività e su tutti gli allenatori insieme, a caldo.")
    for chiave, nome in mercato.ORDINI:
        misura(f"regole, ordine {nome}", lambda k=chiave: ricalcolo_a_regole(mondo, mercato.FiltriARegole(TUTTI_E_GLI_ALLENATORI, k), vuota, memoria),
               max(1, volte // 2))
    a_caldo = {nome: valori for nome, valori in misure.items() if not nome.endswith(", a freddo") and "apertura" not in nome}
    piu_lento = max(a_caldo.items(), key=lambda voce: voce[1][0])
    aperture = {porta: misure[f"regole, apertura di {porta}"] for porta in mercato.PORTE}
    for porta in mercato.PORTE:
        mediana = aperture[porta][0]
        if porta in PORTE_DA_300_MS:
            esito = f"{'sotto' if mediana < OBIETTIVO else 'sopra'} l'obiettivo di {millisecondi(OBIETTIVO)}"
        else:
            esito = "da confrontare col motore di prima: non deve andare peggio"
        scrivi(f"Le regole, l'apertura di {porta}: mediana {millisecondi(mediana)}, {esito}.")
    scrivi(f"Le regole, il ricalcolo a caldo più lento: {piu_lento[0]}, mediana {millisecondi(piu_lento[1][0])}.")
    return {"misure": misure, "aperture": aperture, "piu_lento": piu_lento}


def main():
    parser = argparse.ArgumentParser(description="I tempi del motore della finestra Mercato e ricerca di MESS, su un mondo a regime, in sola lettura.")
    parser.add_argument("--attivi", type=int, default=20000, help="i giocatori in attività del mondo a regime, 20000 se non indicato, come nello studio")
    parser.add_argument("--seme", type=int, default=31, help="il seme del mondo a regime, 31 se non indicato")
    parser.add_argument("--volte", type=int, default=5, help="le prove di ogni misura, 5 se non indicato; quelle a freddo e degli ordini la metà")
    parser.add_argument("--rapporto", nargs="?", type=Path, const=RAPPORTO_PREDEFINITO, default=None, help="salva il racconto, in strumenti/banco_mercato.txt se non si dà un file")
    argomenti = parser.parse_args()
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    scrivi(f"Banco della finestra Mercato e ricerca di MESS {__version__}, {time.strftime('%Y-%m-%d %H:%M')}, sulla macchina {platform.node()}, "
           f"Python {platform.python_version()}. I tempi assoluti cambiano da una macchina all'altra; l'obiettivo della proposta vale per il Gigante.")
    cartella = tempfile.mkdtemp(prefix="mess_banco_mercato_")
    vere = percorsi.cartella, percorsi.cartella_del_programma
    percorsi.cartella = percorsi.cartella_del_programma = lambda: cartella
    stato = random.getstate()
    try:
        mondo = costruisci_mondo(argomenti.attivi, argomenti.seme, scrivi)
        # Come il programma dopo il caricamento: la memoria del mondo si mette da parte per la raccolta dei
        # cicli, che altrimenti ogni tanto la ripasserebbe tutta, e il ricalcolo che la incontra durerebbe il doppio.
        archivio.congela_la_memoria()
        prima = banco(mondo, argomenti.volte, scrivi)
        regole = banco_delle_regole(mondo, argomenti.volte, scrivi)
        vecchia, nuova = prima["misure"]["apertura di amichevole"][0], regole["aperture"]["amichevole"][0]
        scrivi(f"L'apertura di amichevole: {millisecondi(vecchia)} col motore di prima, {millisecondi(nuova)} con le regole, "
               f"{'non peggio' if nuova <= vecchia * 1.1 else 'peggio'} di prima.")
    finally:
        random.setstate(stato)
        percorsi.cartella, percorsi.cartella_del_programma = vere
        shutil.rmtree(cartella, ignore_errors=True)
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
