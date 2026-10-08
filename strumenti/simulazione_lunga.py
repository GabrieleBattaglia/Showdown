"""
La simulazione lunga del mondo di MESS, per controllare l'economia.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, dallo script di lavoro della tappa 8 che aveva fissato le
cifre della decisione D22 in tre giri da dieci anni simulati. Fa nascere un mondo nuovo, sempre il
primo gennaio 2026, in una cartella temporanea e lo fa avanzare un giorno simulato alla volta, come farebbe il programma in
anni di uso; ogni anno dice quanti giocatori ci sono, quanti sono tesserati, come stanno le casse
delle polisportive del computer e gli stipendi, e alla fine confronta i numeri con quelli della
tappa 8. Serve tre volte: alla taratura del valore, che vi prende il mondo maturo su cui fissare la
prima stima della scala; per cercare la scala vera, con --cerca-scala; e dopo, per controllare che
col valore nuovo stipendi e casse restino quelli di prima.
La scala, decisione D26 di Gabriele, si tara qui e non su un mondo fermo: lo stipendio lo pagano
le polisportive del computer ai tesserati che scelgono, e con un valore più disperso scelgono
giocatori più economici, così il monte stipendi calava e le casse crescevano. Con --cerca-scala
lo strumento tiene ferma la mediana del valore, quella del valore della tappa 8 nel mondo maturo,
circa 140, e cerca B per bisezione, simulando dieci anni su più semi in parallelo, finché la cassa
mediana delle polisportive del computer torna sui 5000 euro della tappa 8.
Non tocca mai il mondo salvato: la cartella del programma è spostata in quella temporanea, che
alla fine si cancella. Il mondo per ora non gioca partite, problema P6, quindi il motore di partita
qui non entra: entra il valore complessivo, che decide stipendi, gloria e scelte di mercato.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/simulazione_lunga.py
    python strumenti/simulazione_lunga.py --anni 10 --seme 2026 --rapporto economia.txt
    python strumenti/simulazione_lunga.py --scala -58,25 1,2532 --semi 2026 7 13 21
    python strumenti/simulazione_lunga.py --cerca-scala --semi 2026 7 13 21 --cassa 5000
    python strumenti/simulazione_lunga.py --cerca-scala --mediana 135,5 --mediana-somme 156,9
"""

import argparse
import datetime
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
# che il valore nuovo conserva.
PESI_TAPPA_8 = dict.fromkeys(costanti.CARATTERISTICHE_VALORE, 1.0)
TRATTI_TAPPA_8 = {"mancino": 0.0, "ambidestro": 33.0, "giocorapido": 33.0, "cambiovelocita": 33.0}
# Il mondo nasce sempre lo stesso giorno, perché i conti del primo del mese cadano negli stessi
# giorni simulati e la stessa simulazione dia gli stessi numeri qualunque giorno la si lanci.
NASCITA_DEL_MONDO = datetime.datetime(2026, 1, 1, 9, 0, tzinfo=datetime.UTC)
# I numeri della tappa 8 dopo dieci anni simulati, punto 18.20 del progetto della tappa 9.
BERSAGLI = (("Stipendio mediano in euro", (190, 230)), ("Stipendio al decimo percentile", (120, 150)), ("Stipendio al novantesimo percentile", (450, 650)),
            ("Cassa mediana delle polisportive del computer", (4000, 6500)), ("Tesserati sui giocatori in attività, per cento", (85, 92)))


def numero(valore, decimali=0):
    return f"{valore:.{decimali}f}".replace(".", ",")


def percentile(valori, quota):
    ordinati = sorted(valori)
    if not ordinati:
        return 0.0
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))]


def in_attivita(mondo):
    """I giocatori vivi e non ritirati del mondo."""
    morti = mondo._ids_morti_processati_sessione
    return [g for gid, g in mondo.giocatori.items() if gid not in morti and not g.ritirato]


def misure(mondo):
    """Le misure dell'economia di un mondo: stipendi dei tesserati, casse del computer, quota di tesserati."""
    attivi = in_attivita(mondo)
    tesserati = [g for g in attivi if g.appartenenza != "*"]
    cpu = [p for p in mondo.polisportive.values() if p.is_cpu_controlled]
    stipendi = [economia.stipendio(g) for g in tesserati]
    casse = [p.cassa for p in cpu]
    monte = sum(mondo.monte_stipendi(p) for p in cpu)
    sponsor = sum(economia.sponsor_mensile(p) for p in cpu)
    return {
        "attivi": len(attivi), "tesserati": len(tesserati), "polisportive": len(cpu),
        "stipendi": (percentile(stipendi, 0.1), percentile(stipendi, 0.5), percentile(stipendi, 0.9)),
        "casse": (percentile(casse, 0.1), percentile(casse, 0.5), percentile(casse, 0.9)),
        "monte_su_sponsor": monte / max(1, sponsor),
        "valore": (percentile([g.indice_collettivo_valore for g in attivi], 0.1), percentile([g.indice_collettivo_valore for g in attivi], 0.5),
                   percentile([g.indice_collettivo_valore for g in attivi], 0.9)),
    }


def riga_dell_anno(anno, m, millisecondi):
    s10, s50, s90 = m["stipendi"]
    c10, c50, c90 = m["casse"]
    v10, v50, v90 = m["valore"]
    return (f"Anno {anno}: {m['attivi']} giocatori in attività, {numero(100 * m['tesserati'] / max(1, m['attivi']))} per cento tesserati, "
            f"{m['polisportive']} polisportive del computer. Stipendi {numero(s10)}, {numero(s50)} e {numero(s90)} euro al decimo, cinquantesimo e novantesimo percentile; "
            f"casse {numero(c10)}, {numero(c50)} e {numero(c90)} euro; il monte stipendi è il {numero(100 * m['monte_su_sponsor'])} per cento dello sponsor. "
            f"Valore {numero(v10)}, {numero(v50)} e {numero(v90)}. Un giorno simulato chiede {numero(millisecondi)} millisecondi.")


def simula(anni=10, seme=2026, stampa=print):
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
        for giorno in range(1, giorni + 1):
            mondo.processa_tempo_trascorso(mondo.datetime_ultimo_run_reale + DURATA_TICK)
            if giorno % GIORNI_PER_ANNO == 0:
                adesso = time.perf_counter()
                riga = riga_dell_anno(giorno // GIORNI_PER_ANNO, misure(mondo), (adesso - ultimo) * 1000 / GIORNI_PER_ANNO)
                ultimo = adesso
                righe.append(riga)
                if stampa:
                    stampa(riga)
    finally:
        percorsi.cartella = cartella_vera
        archivio.adesso, archivio.adesso_utc = orologi_veri
        random.setstate(stato)
        shutil.rmtree(cartella, ignore_errors=True)
    return mondo, righe


def confronto(mondo):
    """Le righe del confronto con i numeri della tappa 8, con dentro o FUORI accanto a ciascuno."""
    m = misure(mondo)
    valori = (m["stipendi"][1], m["stipendi"][0], m["stipendi"][2], m["casse"][1], 100 * m["tesserati"] / max(1, m["attivi"]))
    righe = ["Il confronto con l'economia della tappa 8:"]
    for (nome, (basso, alto)), misurato in zip(BERSAGLI, valori, strict=True):
        esito = "dentro" if basso <= misurato <= alto else "FUORI"
        righe.append(f"{nome}: {numero(misurato)}, bersaglio da {numero(basso)} a {numero(alto)}, {esito}.")
    attivi = in_attivita(mondo)
    indici = [g.indice_collettivo_valore for g in attivi]
    righe.append(f"Valore dei giocatori in attività: mediana {numero(statistics.median(indici), 1)}, dal decimo al novantesimo percentile "
                 f"{numero(percentile(indici, 0.1), 1)} e {numero(percentile(indici, 0.9), 1)}.")
    return righe


# La scala del valore che si sta provando. Le simulazioni girano in processi a parte, e ognuno mette
# la scala nel suo modulo valore, che vive soltanto per la simulazione: il progetto non cambia.
def _imposta_scala(a, b):
    valore.SCALA_VALORE_A, valore.SCALA_VALORE_B = a, b


def _misura_con_scala(anni, seme, a, b):
    """Dieci anni simulati con la scala indicata, in un processo a parte: le misure finali e il valore della tappa 8 dei giocatori in attività."""
    _imposta_scala(a, b)
    mondo, _righe = simula(anni, seme, stampa=None)
    m = misure(mondo)
    attivi = in_attivita(mondo)
    m["mediana_valore"] = statistics.median(g.indice_collettivo_valore for g in attivi)
    m["mediana_somme"] = statistics.median(valore.indice(g, a=0.0, b=1.0) for g in attivi)
    m["mediana_tappa_8"] = statistics.median(valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in attivi)
    return seme, m


def con_scala(anni, semi, a, b, processi):
    """Le misure finali di più semi simulati in parallelo con la scala indicata, come dizionario seme e misure."""
    # I processi figli ricevono la funzione per nome: la si prende dal modulo importato col suo
    # nome, perché quella dello script lanciato direttamente si chiama __main__.
    from simulazione_lunga import _misura_con_scala as lavoro
    with ProcessPoolExecutor(max_workers=max(1, min(processi, len(semi)))) as esecutore:
        futuri = [esecutore.submit(lavoro, anni, seme, a, b) for seme in semi]
        return dict(f.result() for f in futuri)


def riga_della_scala(a, b, misure_per_seme):
    casse = [m["casse"][1] for m in misure_per_seme.values()]
    stipendi = [m["stipendi"][1] for m in misure_per_seme.values()]
    bassi = [m["stipendi"][0] for m in misure_per_seme.values()]
    alti = [m["stipendi"][2] for m in misure_per_seme.values()]
    valori = [m["mediana_valore"] for m in misure_per_seme.values()]
    monte = [100 * m["monte_su_sponsor"] for m in misure_per_seme.values()]
    tesserati = [100 * m["tesserati"] / max(1, m["attivi"]) for m in misure_per_seme.values()]
    return (f"Scala A {numero(a, 2)}, B {numero(b, 4)}: cassa mediana {', '.join(numero(c) for c in casse)} euro, in media {numero(statistics.fmean(casse))}; "
            f"stipendio mediano {', '.join(numero(s) for s in stipendi)}, decimo percentile {', '.join(numero(s) for s in bassi)}, "
            f"novantesimo {', '.join(numero(s) for s in alti)}; monte stipendi {', '.join(numero(x) for x in monte)} per cento dello sponsor; "
            f"tesserati {', '.join(numero(x) for x in tesserati)} per cento; mediana del valore {', '.join(numero(v, 1) for v in valori)}.")


def cerca_scala(anni, semi, cassa_bersaglio, processi, passi=8, stampa=print, mediana=None, mediana_somme=None):
    """
    La scala del valore che riporta la cassa mediana delle polisportive del computer al bersaglio,
    in media sui semi indicati, tenendo la mediana del valore ferma: quella indicata, oppure quella
    del valore della tappa 8 nel mondo maturo. Un primo giro con la scala di costanti.py dà la
    mediana del valore della tappa 8 e quella della somma pesata, a meno che siano indicate tutte e
    due; poi, per ogni B provato, A tiene ferma la mediana, e B si cerca per bisezione: con B più
    alto il valore è più disperso, i forti chiedono di più e le casse scendono. Lo stipendio mediano
    lo decide soprattutto la mediana: abbassarla di 4 punti lo abbassa di un decimo circa.
    Restituisce A, B e le righe del racconto.
    """
    righe = []

    def annota(riga):
        righe.append(riga)
        if stampa:
            stampa(riga)

    a, b = costanti.SCALA_VALORE_A, costanti.SCALA_VALORE_B
    if mediana is None or mediana_somme is None:
        primo = con_scala(anni, semi, a, b, processi)
        annota("Primo giro, con la scala di costanti.py. " + riga_della_scala(a, b, primo))
        if mediana is None:
            mediana = statistics.fmean(m["mediana_tappa_8"] for m in primo.values())
        if mediana_somme is None:
            mediana_somme = statistics.fmean(m["mediana_somme"] for m in primo.values())
    annota(f"La mediana del valore da tenere ferma è {numero(mediana, 1)}; quella della somma pesata nel mondo maturo è {numero(mediana_somme, 1)}.")

    def cassa_con(b_provato):
        a_provato = mediana - b_provato * mediana_somme
        risultati = con_scala(anni, semi, a_provato, b_provato, processi)
        annota(riga_della_scala(a_provato, b_provato, risultati))
        return statistics.fmean(m["casse"][1] for m in risultati.values())

    basso, alto = 0.8 * b, 1.4 * b
    for _passo in range(passi):
        medio = (basso + alto) / 2.0
        if cassa_con(medio) > cassa_bersaglio:
            basso = medio
        else:
            alto = medio
    b = (basso + alto) / 2.0
    a = mediana - b * mediana_somme
    if min(b - 0.8 * costanti.SCALA_VALORE_B, 1.4 * costanti.SCALA_VALORE_B - b) < 0.01 * b:
        annota("Attenzione: la scala trovata sta al bordo dell'intervallo cercato, e il bersaglio forse sta fuori.")
    annota(f"La scala trovata, da copiare in costanti.py: SCALA_VALORE_A = {a:.2f}, SCALA_VALORE_B = {b:.4f}.")
    return a, b, righe


def _decimale(testo):
    return float(testo.replace(",", "."))


def main():
    parser = argparse.ArgumentParser(description="Simula il mondo di MESS per molti anni in una cartella temporanea e controlla l'economia.")
    parser.add_argument("--anni", type=int, default=10, help="quanti anni simulare, 10 se non indicato")
    parser.add_argument("--seme", type=int, default=2026, help="il seme del caso del mondo, 2026 se non indicato")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il racconto anche in questo file")
    parser.add_argument("--semi", type=int, nargs="+", default=None, help="più semi in parallelo, per --scala e --cerca-scala; 2026, 7, 13 e 21 se non indicati")
    parser.add_argument("--scala", type=_decimale, nargs=2, metavar=("A", "B"), default=None, help="simula i semi con questa scala del valore, senza toccare il progetto")
    parser.add_argument("--cerca-scala", action="store_true", help="cerca per bisezione la scala che riporta la cassa mediana al bersaglio")
    parser.add_argument("--cassa", type=float, default=5000.0, help="la cassa mediana delle polisportive del computer cercata, 5000 euro se non indicata")
    parser.add_argument("--passi", type=int, default=8, help="i passi della bisezione, 8 se non indicati")
    parser.add_argument("--mediana", type=_decimale, default=None, help="con --cerca-scala, la mediana del valore da tenere ferma; quella del valore della tappa 8 se non indicata")
    parser.add_argument("--mediana-somme", type=_decimale, default=None, help="con --cerca-scala e --mediana, la mediana della somma pesata nel mondo maturo, da una ricerca precedente: salta il primo giro")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti semi simulare insieme, fino a 8 se il computer li ha")
    argomenti = parser.parse_args()
    inizio = time.perf_counter()
    semi = argomenti.semi or [2026, 7, 13, 21]
    if argomenti.cerca_scala:
        _a, _b, righe = cerca_scala(argomenti.anni, semi, argomenti.cassa, argomenti.processi, argomenti.passi, mediana=argomenti.mediana, mediana_somme=argomenti.mediana_somme)
        righe = [f"Ricerca della scala del valore, {argomenti.anni} anni sui semi {', '.join(str(s) for s in semi)}, cassa mediana cercata {numero(argomenti.cassa)} euro.",
                 *righe, f"Ricerca completata in {numero(time.perf_counter() - inizio)} secondi."]
        print(righe[-1])
    elif argomenti.scala:
        a, b = argomenti.scala
        righe = [riga_della_scala(a, b, con_scala(argomenti.anni, semi, a, b, argomenti.processi))]
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
