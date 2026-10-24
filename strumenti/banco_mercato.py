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
        for g in sorted((g for g in mondo.giocatori.values() if g.ritirato), key=lambda g: g.id)[:20]:
            mondo._ex_giocatore_allenatore(g, None, oggi, rng=rng)
    finally:
        random.setstate(stato)
    liberi_dello_staff = sum(1 for a in mondo.allenatori.values() if a.libero)
    in_vendita = sum(len(p.in_vendita) for p in mondo.polisportive.values())
    secondi = f"{time.perf_counter() - inizio:.1f}".replace(".", ",")
    scrivi(f"Mondo a regime del seme {seme}: {len(mondo.giocatori)} giocatori, {attivi} in attività, {ritirati} ritirati, {polisportive} polisportive del computer "
           f"e 2 tue, {in_vendita} giocatori in vendita, {len(mondo.allenatori)} allenatori di cui {liberi_dello_staff} liberi; costruito in {secondi} secondi.")
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
    Le misure del motore sul mondo dato: le aperture delle quattro porte, a freddo; le ricerche pronte e i
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
        filtri = mercato.stato_predefinito(porta).filtri
        misura(f"apertura di {porta}", lambda f=filtri: (testi.situazione(mondo), ricalcolo(mondo, f, mercato.Memoria(mondo)))[1])
    scrivi("Le ricerche pronte, a freddo e a caldo.")
    memoria = mercato.Memoria(mondo)
    prove = [(nome, mercato.filtri_della_pronta(chiave)) for chiave, nome in mercato.PRONTE[1:]]
    prove += [(nome, mercato.Filtri(**campi)) for nome, campi in FILTRI_A_MANO]
    for posto, (nome, filtri) in enumerate(prove):
        if posto == len(mercato.PRONTE) - 1:
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
        banco(mondo, argomenti.volte, scrivi)
    finally:
        random.setstate(stato)
        percorsi.cartella, percorsi.cartella_del_programma = vere
        shutil.rmtree(cartella, ignore_errors=True)
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
