"""
La simulazione lunga del mondo di MESS, per controllare l'economia.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, dallo script di lavoro della tappa 8 che aveva fissato le
cifre della decisione D22 in tre giri da dieci anni simulati. Fa nascere un mondo nuovo, sempre il
primo gennaio 2026, in una cartella temporanea e lo fa avanzare un giorno simulato alla volta, come farebbe il programma in
anni di uso; ogni anno dice quanti giocatori ci sono, quanti sono tesserati, come stanno le casse
delle polisportive del computer e gli stipendi, e alla fine confronta i numeri con i bersagli.
Serve alla taratura del valore, che vi prende il mondo maturo su cui fissare la prima stima della
scala, e alla taratura dell'economia.
Dalla tappa 11, il 2026-10-09, decisione D31, nel mondo che avanza c'è già l'allenamento, perché
sta in un giorno del mondo: sedute, spesa autonoma, esperienza, costanza, contratti e infortuni in
seduta; il mondo non gioca partite fino alla tappa 12. Le misure contano lo stipendio pagato, cioè
quello del contratto, la parte allenata e il valore per fasce d'età, le classi per lettera, i
rinnovi e le scadenze dell'anno, gli infortuni in seduta e i millisecondi del giorno. I bersagli
sono quelli del punto 5 del progetto della tappa, all'anno 10 su quattro semi: lo stipendio pagato
al decimo percentile dei tesserati fra 95 e 115 euro, attorno ai 105 di D31, e mediano fra 190 e
240; la cassa mediana delle polisportive del computer fra 4.500 e 5.500 euro; i tesserati dall'88
al 92 per cento dei giocatori in attività. Con --cerca-economia la scala del valore A e B si ricava
in forma chiusa, senza bisezioni annidate: da una corsa di riferimento si prendono le somme pesate
dei giocatori in attività e quelle dei tesserati con i loro moltiplicatori di stipendio, e si
calcolano l'A che tiene la mediana del valore a 135,5 e il B che porta lo stipendio al decimo
percentile a 105; si rifà la corsa con la scala nuova, due o tre volte, finché non si sposta più.
Poi una bisezione cerca soltanto lo sponsor per punto di gloria, con la quota sul valore fissa,
perché la cassa mediana torni a 5.000 euro.
Non tocca mai il mondo salvato: la cartella del programma è spostata in quella temporanea, che
alla fine si cancella; scala e sponsor provati vivono soltanto nei processi della simulazione.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/simulazione_lunga.py
    python strumenti/simulazione_lunga.py --anni 10 --seme 2026 --rapporto economia.txt
    python strumenti/simulazione_lunga.py --scala -58,25 1,2532 --semi 2026 7 13 21
    python strumenti/simulazione_lunga.py --cerca-economia --semi 2026 7 13 21 --cassa 5000
"""

import argparse
import datetime
import math
import os
import random
import shutil
import statistics
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import archivio  # noqa: E402
import classe  # noqa: E402
import costanti  # noqa: E402
import economia  # noqa: E402
import percorsi  # noqa: E402
import valore  # noqa: E402
from mondo import DURATA_TICK, Mondo  # noqa: E402

# Quanti giorni simulati fanno un anno per l'età dei giocatori: con 108 avanzamenti un giocatore
# invecchia di un anno, ed è la misura usata dalle simulazioni della tappa 6 e della tappa 8.
GIORNI_PER_ANNO = 108
# L'indice della tappa 8, tutti i pesi a 1 e 33 punti per i tratti rari: le cifre dell'economia
# della decisione D22 sono tarate su di lui, e la sua mediana nel mondo maturo, circa 140, è quella
# che il valore della tappa 9 conserva.
PESI_TAPPA_8 = dict.fromkeys(costanti.CARATTERISTICHE_VALORE, 1.0)
TRATTI_TAPPA_8 = {"mancino": 0.0, "ambidestro": 33.0, "giocorapido": 33.0, "cambiovelocita": 33.0}
# Il mondo nasce sempre lo stesso giorno, perché i conti del primo del mese cadano negli stessi
# giorni simulati e la stessa simulazione dia gli stessi numeri qualunque giorno la si lanci.
NASCITA_DEL_MONDO = datetime.datetime(2026, 1, 1, 9, 0, tzinfo=datetime.UTC)
# I bersagli della tappa 11 all'anno 10, punto 5 del progetto; il novantesimo percentile è un'informazione.
BERSAGLI = (("Stipendio pagato mediano in euro", (190, 240)), ("Stipendio pagato al decimo percentile", (95, 115)),
            ("Stipendio pagato al novantesimo percentile", (0, 100_000)), ("Cassa mediana delle polisportive del computer", (4500, 5500)),
            ("Tesserati sui giocatori in attività, per cento", (88, 92)))
# Le mete della scala in forma chiusa: la mediana del valore dei giocatori in attività e lo stipendio al decimo percentile dei tesserati.
MEDIANA_DEL_VALORE = 135.5
STIPENDIO_AL_DECIMO = 105.0
FASCE_ETA = ((9, 20), (20, 35), (35, 50), (50, 76))
# Le voci del riepilogo che si sommano anno per anno.
VOCI_DELL_ANNO = ("rinnovi_cpu", "contratti_scaduti", "infortunati_in_seduta", "autoallenati", "partiti")


def numero(valore_numerico, decimali=0):
    return f"{valore_numerico:.{decimali}f}".replace(".", ",")


def percentile(valori, quota):
    ordinati = sorted(valori)
    if not ordinati:
        return 0.0
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))]


def in_attivita(mondo):
    """I giocatori vivi e non ritirati del mondo."""
    morti = mondo._ids_morti_processati_sessione
    return [g for gid, g in mondo.giocatori.items() if gid not in morti and not g.ritirato]


def moltiplicatore_di_stipendio(g):
    """Quanto lo stipendio chiesto si allontana dalla curva del valore: i tratti rari e l'esperienza, come in economia.stipendio."""
    fattore = 1.0
    if g.ambidestro:
        fattore *= costanti.FATTORE_GLORIA_RICHIESTA_AMBIDESTRO
    if g.giocorapido:
        fattore *= costanti.FATTORE_GLORIA_RICHIESTA_GIOCO_RAPIDO
    if g.cambiovelocita:
        fattore *= costanti.FATTORE_GLORIA_RICHIESTA_CAMBIO_VEL
    return fattore * (1 + costanti.AUMENTO_STIPENDIO_PER_ESPERIENZA * g.esperienza)


def misure(mondo, dell_anno=None):
    """
    Le misure di un mondo: stipendi pagati dei tesserati, casse del computer, quota di tesserati,
    valore, parte allenata e valore per fasce d'età, classi per lettera, e le voci dell'anno.
    """
    attivi = in_attivita(mondo)
    tesserati = [g for g in attivi if g.appartenenza != "*"]
    cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
    stipendi = [economia.stipendio_pagato(g) for g in tesserati]
    casse = [p.cassa for p in cpu]
    monte = sum(mondo.monte_stipendi(p) for p in cpu)
    sponsor = sum(mondo.sponsor(p) for p in cpu)
    valori = [g.indice_collettivo_valore for g in attivi]
    fasce = {}
    for da, a in FASCE_ETA:
        gruppo = [g for g in attivi if da <= g.eta_anni < a]
        if gruppo:
            fasce[(da, a)] = (len(gruppo), statistics.median(g.indice_collettivo_valore for g in gruppo), statistics.median(valore.somma_pesata(g, "allenata") for g in gruppo))
    lettere = {}
    for g in attivi:
        lettera = classe.classe(g).codice[0]
        lettere[lettera] = lettere.get(lettera, 0) + 1
    return {
        "attivi": len(attivi), "tesserati": len(tesserati), "polisportive": len(cpu),
        "stipendi": (percentile(stipendi, 0.1), percentile(stipendi, 0.5), percentile(stipendi, 0.9)),
        "casse": (percentile(casse, 0.1), percentile(casse, 0.5), percentile(casse, 0.9)),
        "monte_su_sponsor": monte / max(1, sponsor),
        "valore": (percentile(valori, 0.1), percentile(valori, 0.5), percentile(valori, 0.9)),
        "fasce": fasce, "lettere": lettere, "anno": dict(dell_anno or {}),
    }


def riga_dell_anno(anno, m, millisecondi):
    s10, s50, s90 = m["stipendi"]
    c10, c50, c90 = m["casse"]
    v10, v50, v90 = m["valore"]
    fasce = "; ".join(f"dai {da} ai {a} anni {quanti}, valore {numero(v, 1)}, somma allenata {numero(s, 1)}" for (da, a), (quanti, v, s) in m["fasce"].items())
    lettere = ", ".join(f"{lettera} {numero(100 * quanti / max(1, m['attivi']), 1)}" for lettera, quanti in sorted(m["lettere"].items()))
    anno_trascorso = ", ".join(f"{voce} {m['anno'].get(voce, 0)}" for voce in VOCI_DELL_ANNO)
    return (f"Anno {anno}: {m['attivi']} giocatori in attività, {numero(100 * m['tesserati'] / max(1, m['attivi']))} per cento tesserati, "
            f"{m['polisportive']} polisportive del computer. Stipendi pagati {numero(s10)}, {numero(s50)} e {numero(s90)} euro al decimo, cinquantesimo e novantesimo percentile; "
            f"casse {numero(c10)}, {numero(c50)} e {numero(c90)} euro; il monte stipendi è il {numero(100 * m['monte_su_sponsor'])} per cento dello sponsor. "
            f"Valore {numero(v10)}, {numero(v50)} e {numero(v90)}. Per fasce d'età: {fasce}. Classi per lettera, per cento: {lettere}. "
            f"Nell'anno: {anno_trascorso}. Un giorno simulato chiede {numero(millisecondi)} millisecondi.")


def simula(anni=10, seme=2026, stampa=print, misura_ogni_anno=True):
    """
    Fa nascere un mondo in una cartella temporanea e lo fa avanzare di tanti anni simulati.
    Restituisce il mondo e le righe del racconto; la cartella si cancella alla fine. Il caso del
    mondo si rimette com'era, così chi chiama non si accorge della simulazione.
    """
    cartella = tempfile.mkdtemp(prefix="mess_simulazione_lunga_")
    cartella_vera = percorsi.cartella
    orologi_veri = archivio.adesso, archivio.adesso_utc
    stato = random.getstate()
    percorsi.cartella = lambda: cartella
    archivio.adesso = lambda: NASCITA_DEL_MONDO.replace(tzinfo=None)
    archivio.adesso_utc = lambda: NASCITA_DEL_MONDO
    righe = []
    try:
        random.seed(seme)
        mondo = Mondo()
        archivio.carica(mondo)
        giorni = anni * GIORNI_PER_ANNO
        ultimo = time.perf_counter()
        dell_anno = dict.fromkeys(VOCI_DELL_ANNO, 0)
        for giorno in range(1, giorni + 1):
            rapporto = mondo.processa_tempo_trascorso(mondo.datetime_ultimo_run_reale + DURATA_TICK)
            for voce in VOCI_DELL_ANNO:
                dell_anno[voce] += rapporto[voce]
            if giorno % GIORNI_PER_ANNO == 0:
                adesso = time.perf_counter()
                millisecondi = (adesso - ultimo) * 1000 / GIORNI_PER_ANNO
                if misura_ogni_anno or giorno == giorni:
                    riga = riga_dell_anno(giorno // GIORNI_PER_ANNO, misure(mondo, dell_anno), millisecondi)
                    righe.append(riga)
                    if stampa:
                        stampa(riga)
                dell_anno = dict.fromkeys(VOCI_DELL_ANNO, 0)
                ultimo = time.perf_counter()
    finally:
        percorsi.cartella = cartella_vera
        archivio.adesso, archivio.adesso_utc = orologi_veri
        random.setstate(stato)
        shutil.rmtree(cartella, ignore_errors=True)
    return mondo, righe


def confronto(mondo):
    """Le righe del confronto con i bersagli, con dentro o FUORI accanto a ciascuno."""
    m = misure(mondo)
    valori = (m["stipendi"][1], m["stipendi"][0], m["stipendi"][2], m["casse"][1], 100 * m["tesserati"] / max(1, m["attivi"]))
    righe = ["Il confronto con i bersagli della tappa 11:"]
    for (nome, (basso, alto)), misurato in zip(BERSAGLI, valori, strict=True):
        esito = "dentro" if basso <= misurato <= alto else "FUORI"
        righe.append(f"{nome}: {numero(misurato)}, bersaglio da {numero(basso)} a {numero(alto)}, {esito}.")
    attivi = in_attivita(mondo)
    indici = [g.indice_collettivo_valore for g in attivi]
    righe.append(f"Valore dei giocatori in attività: mediana {numero(statistics.median(indici), 1)}, dal decimo al novantesimo percentile "
                 f"{numero(percentile(indici, 0.1), 1)} e {numero(percentile(indici, 0.9), 1)}.")
    return righe


# La scala e lo sponsor che si stanno provando. Le simulazioni girano in processi a parte, e ognuno li
# mette nei suoi moduli, che vivono soltanto per la simulazione: il progetto non cambia.
def _imposta(a, b, sponsor=None):
    valore.SCALA_VALORE_A, valore.SCALA_VALORE_B = a, b
    if sponsor is not None:
        economia.SPONSOR_PER_GLORIA = sponsor


def _misura_con_scala(anni, seme, a, b, sponsor=None):
    """Una simulazione con la scala e lo sponsor indicati, in un processo a parte: le misure finali e il campione per la scala in forma chiusa."""
    _imposta(a, b, sponsor)
    mondo, _righe = simula(anni, seme, stampa=None, misura_ogni_anno=False)
    m = misure(mondo)
    attivi = in_attivita(mondo)
    m["mediana_valore"] = statistics.median(g.indice_collettivo_valore for g in attivi)
    m["mediana_somme"] = statistics.median(valore.indice(g, a=0.0, b=1.0) for g in attivi)
    m["mediana_tappa_8"] = statistics.median(valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in attivi)
    m["somme_attivi"] = [valore.indice(g, a=0.0, b=1.0) for g in attivi]
    m["tesserati_campione"] = [(valore.indice(g, a=0.0, b=1.0), moltiplicatore_di_stipendio(g)) for g in attivi if g.appartenenza != "*"]
    return seme, m


def con_scala(anni, semi, a, b, processi, sponsor=None):
    """Le misure finali di più semi simulati in parallelo con la scala e lo sponsor indicati, come dizionario seme e misure."""
    # I processi figli ricevono la funzione per nome: la si prende dal modulo importato col suo
    # nome, perché quella dello script lanciato direttamente si chiama __main__.
    from simulazione_lunga import _misura_con_scala as lavoro
    with ProcessPoolExecutor(max_workers=max(1, min(processi, len(semi)))) as esecutore:
        futuri = [esecutore.submit(lavoro, anni, seme, a, b, sponsor) for seme in semi]
        return dict(f.result() for f in futuri)


def riga_della_scala(a, b, misure_per_seme, sponsor=None):
    casse = [m["casse"][1] for m in misure_per_seme.values()]
    stipendi = [m["stipendi"][1] for m in misure_per_seme.values()]
    bassi = [m["stipendi"][0] for m in misure_per_seme.values()]
    alti = [m["stipendi"][2] for m in misure_per_seme.values()]
    valori = [m["mediana_valore"] for m in misure_per_seme.values()]
    monte = [100 * m["monte_su_sponsor"] for m in misure_per_seme.values()]
    tesserati = [100 * m["tesserati"] / max(1, m["attivi"]) for m in misure_per_seme.values()]
    sponsor_testo = f", sponsor {numero(sponsor, 2)} per punto di gloria" if sponsor is not None else ""
    return (f"Scala A {numero(a, 2)}, B {numero(b, 4)}{sponsor_testo}: cassa mediana {', '.join(numero(c) for c in casse)} euro, in media {numero(statistics.fmean(casse))}; "
            f"stipendio pagato mediano {', '.join(numero(s) for s in stipendi)}, decimo percentile {', '.join(numero(s) for s in bassi)}, "
            f"novantesimo {', '.join(numero(s) for s in alti)}; monte stipendi {', '.join(numero(x) for x in monte)} per cento dello sponsor; "
            f"tesserati {', '.join(numero(x) for x in tesserati)} per cento; mediana del valore {', '.join(numero(v, 1) for v in valori)}.")


def _stipendio(valore_del_giocatore, moltiplicatore):
    euro = costanti.STIPENDIO_DI_RIFERIMENTO * math.exp((valore_del_giocatore - costanti.VALORE_DI_RIFERIMENTO) / costanti.SCALA_STIPENDIO) * moltiplicatore
    return max(costanti.STIPENDIO_MINIMO, economia.arrotonda(euro))


def scala_in_forma_chiusa(campioni, mediana=MEDIANA_DEL_VALORE, decimo=STIPENDIO_AL_DECIMO):
    """
    La scala del valore dal campione di una corsa: A tiene la mediana delle somme pesate dei
    giocatori in attività al valore indicato, e B, con A che lo segue, porta lo stipendio chiesto al
    decimo percentile dei tesserati alla cifra indicata. Il campione è un elenco, uno per seme, di
    coppie: le somme dei giocatori in attività, e le coppie di somma e moltiplicatore dei tesserati.
    Con B la mediana resta ferma e i deboli si allontanano: lo stipendio al decimo percentile scende
    al crescere di B, e B si trova con una ricerca sul campione, senza nessuna simulazione.
    """
    somme = [s for attivi, _t in campioni for s in attivi]
    tesserati = [t for _a, ts in campioni for t in ts]
    centro = statistics.median(somme)

    def al_decimo(b):
        a = mediana - b * centro
        return percentile([_stipendio(a + b * s, m) for s, m in tesserati], 0.1)

    basso, alto = 0.05, 10.0
    for _passo in range(60):
        medio = (basso + alto) / 2
        if al_decimo(medio) > decimo:
            basso = medio
        else:
            alto = medio
    b = (basso + alto) / 2
    return mediana - b * centro, b


def cerca_economia(anni, semi, cassa_bersaglio, processi, giri=3, passi=6, stampa=print, sponsor_iniziale=None):
    """
    La taratura dell'economia della tappa 11: prima la scala, in forma chiusa, rifatta per qualche
    giro finché non si sposta più; poi lo sponsor per punto di gloria, per bisezione, perché la cassa
    mediana delle polisportive del computer torni al bersaglio. Restituisce A, B, lo sponsor e le righe.
    """
    righe = []

    def annota(riga):
        righe.append(riga)
        if stampa:
            stampa(riga)

    a, b = costanti.SCALA_VALORE_A, costanti.SCALA_VALORE_B
    sponsor = costanti.SPONSOR_PER_GLORIA if sponsor_iniziale is None else sponsor_iniziale
    risultati = None
    for giro in range(1, giri + 1):
        risultati = con_scala(anni, semi, a, b, processi, sponsor)
        annota(f"Giro {giro} della scala. " + riga_della_scala(a, b, risultati, sponsor))
        nuova_a, nuova_b = scala_in_forma_chiusa([(m["somme_attivi"], m["tesserati_campione"]) for m in risultati.values()])
        annota(f"La scala in forma chiusa dal giro {giro}: A {numero(nuova_a, 2)}, B {numero(nuova_b, 4)}.")
        fermo = abs(nuova_b - b) < 0.005 * b and abs(nuova_a - a) < 0.5
        a, b = nuova_a, nuova_b
        if fermo:
            break

    def cassa_con(sponsor_provato):
        prova = con_scala(anni, semi, a, b, processi, sponsor_provato)
        annota(riga_della_scala(a, b, prova, sponsor_provato))
        return statistics.fmean(m["casse"][1] for m in prova.values())

    basso, alto = 0.25 * sponsor, 2.5 * sponsor
    for _passo in range(passi):
        medio = (basso + alto) / 2
        if cassa_con(medio) > cassa_bersaglio:
            alto = medio
        else:
            basso = medio
    sponsor = (basso + alto) / 2
    annota(f"L'economia trovata, da copiare in costanti.py: SCALA_VALORE_A = {a:.2f}, SCALA_VALORE_B = {b:.4f}, SPONSOR_PER_GLORIA = {sponsor:.1f}.")
    return a, b, sponsor, righe


def _decimale(testo):
    return float(testo.replace(",", "."))


def main():
    parser = argparse.ArgumentParser(description="Simula il mondo di MESS per molti anni in una cartella temporanea e controlla l'economia.")
    parser.add_argument("--anni", type=int, default=10, help="quanti anni simulare, 10 se non indicato")
    parser.add_argument("--seme", type=int, default=2026, help="il seme del caso del mondo, 2026 se non indicato")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il racconto anche in questo file")
    parser.add_argument("--semi", type=int, nargs="+", default=None, help="più semi in parallelo, per --scala e --cerca-economia; 2026, 7, 13 e 21 se non indicati")
    parser.add_argument("--scala", type=_decimale, nargs=2, metavar=("A", "B"), default=None, help="simula i semi con questa scala del valore, senza toccare il progetto")
    parser.add_argument("--sponsor", type=_decimale, default=None, help="con --scala o --cerca-economia, lo sponsor per punto di gloria da provare")
    parser.add_argument("--cerca-economia", action="store_true", help="ricava la scala in forma chiusa e cerca per bisezione lo sponsor per punto di gloria")
    parser.add_argument("--cassa", type=float, default=5000.0, help="la cassa mediana delle polisportive del computer cercata, 5000 euro se non indicata")
    parser.add_argument("--giri", type=int, default=3, help="i giri della scala in forma chiusa, 3 se non indicati")
    parser.add_argument("--passi", type=int, default=6, help="i passi della bisezione dello sponsor, 6 se non indicati")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti semi simulare insieme, fino a 8 se il computer li ha")
    argomenti = parser.parse_args()
    inizio = time.perf_counter()
    semi = argomenti.semi or [2026, 7, 13, 21]
    if argomenti.cerca_economia:
        _a, _b, _s, righe = cerca_economia(argomenti.anni, semi, argomenti.cassa, argomenti.processi, argomenti.giri, argomenti.passi, sponsor_iniziale=argomenti.sponsor)
        righe = [f"Taratura dell'economia, {argomenti.anni} anni sui semi {', '.join(str(s) for s in semi)}, cassa mediana cercata {numero(argomenti.cassa)} euro.",
                 *righe, f"Ricerca completata in {numero(time.perf_counter() - inizio)} secondi."]
        print(righe[-1])
    elif argomenti.scala:
        a, b = argomenti.scala
        righe = [riga_della_scala(a, b, con_scala(argomenti.anni, semi, a, b, argomenti.processi, argomenti.sponsor), argomenti.sponsor)]
        print(righe[0])
    else:
        mondo, righe = simula(argomenti.anni, argomenti.seme)
        righe = [f"Simulazione lunga del mondo, {argomenti.anni} anni col seme {argomenti.seme}, in {numero(time.perf_counter() - inizio)} secondi.", *righe, *confronto(mondo)]
        for riga in righe[-len(BERSAGLI) - 2:]:
            print(riga)
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Racconto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
