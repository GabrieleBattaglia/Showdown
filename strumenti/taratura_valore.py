"""
La taratura del valore complessivo di MESS sul motore di partita, problema P14.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, secondo il punto 15 del progetto del motore. Il vecchio indice
sommava alla pari tutte le caratteristiche e dava 33 punti a ogni tratto raro; qui i pesi si
misurano su quanto ogni caratteristica conta davvero nelle partite. Lo strumento non scrive nulla
nel progetto: alla fine stampa il blocco da copiare in costanti.py.
Il metodo, in cinque passi, misura il valore sugli incontri al meglio dei 3 set, che sono la
maggior parte, decisione D26: i 5 set restano per rari tornei e per le finali.
Primo, il rating: una popolazione di prova di 3200 giocatori gioca contro quarantotto sparring
fissi, nati da un'altra popolazione, un incontro al meglio dei 3 set ciascuno, in modalità essenziale; il rating
è il logaritmo del rapporto fra i punti fatti e quelli subiti. Nella popolazione della regressione
i tratti sono ridistribuiti, uno su cinque per ciascuno: nati con le frequenze vere, i mancini
sarebbero un centinaio e gli ambidestri una sessantina, e il loro peso uscirebbe dal rumore.
Secondo, la regressione: i minimi quadrati del rating sulle caratteristiche del valore, prese per
ruolo come in valore.py, e sui quattro tratti, con tre regressori di controllo, temperamento,
lettura del gioco e fattore d'età della stanchezza, che si misurano ma non entrano nell'indice.
La resistenza ha una colonna sola, col totale. La parte allenata, che nella stanchezza conta anche
come abitudine ad allenarsi, decisione D26, rende un po' più di quella innata, ma la regressione
non sa separarle: nelle popolazioni di prova chi allena la resistenza allena anche il resto, e una
colonna in più per l'allenamento, provata dopo la revisione di D26, usciva negativa da un seme
all'altro, mentre a coppie l'allenata rende di più. Quanto rende ciascuna lo dice la verifica a
coppie del quinto passo; con K_ALLENAMENTO_FATICA a 0,3 le due stanno vicine al prezzo unico.
I colpi e le battute speculari, come il lungolinea sinistro e il destro, hanno un peso solo: la
differenza fra i due lati nasce dalla popolazione, quasi tutta destrimana, ed è più piccola del
rumore della misura, che da un seme all'altro la rovescia. Chiusure e blocchi invece restano
divisi fra dritto e rovescio, perché lì la differenza c'è sempre, e nello stesso verso.
I pesi non possono essere negativi: si risolve, si azzera il più negativo, si risolve di nuovo.
Una seconda popolazione, nata da un altro seme, verifica il risultato. I primi due passi si
ripetono su più semi, quattro se non si dice altro, e i pesi sono la media: con un seme solo il
mancino andava da 2,9 a 5,6 punti di valore secondo il seme, e la bomba scendeva sotto la soglia
delle caratteristiche quasi inerti in un seme su quattro.
Terzo, la scala: il mondo maturo di una simulazione lunga, dieci anni in una cartella temporanea,
fissa A e B perché il valore nuovo conservi due cose del valore della tappa 8, su cui contano
stipendi e gloria della decisione D22: la mediana, e la media del fattore dello stipendio, cioè e
elevato alla differenza fra il valore e 140, divisa per 40. Il progetto chiedeva la stessa
distanza fra decimo e novantesimo percentile, ma il valore di prima aveva una coda lunga, i 33
punti di ogni tratto, e con la stessa distanza fra i percentili il monte stipendi calava di un
decimo: nella simulazione lunga le casse del computer salivano da 5000 a 18000 euro di mediana.
Con la media del fattore il monte stipendi di un mondo fermo resta quello di prima; ma nel
mondo che si muove le polisportive del computer scelgono i giocatori più economici, e le casse
crescevano lo stesso. Dalla decisione D26 questa scala è soltanto la prima stima: quella vera si
cerca dopo, con strumenti/simulazione_lunga.py --cerca-scala, sulla cassa mediana delle
polisportive del computer in più semi.
Quarto, il rapporto: i pesi in punti di valore, le caratteristiche quasi inerti, l'effetto di
temperamento ed esperienza, la curva del favorito su una terza popolazione e il blocco da copiare.
Quinto, la verifica a coppie: gli stessi giocatori con un punto in più di precisione o di
resistenza, innata o allenata, oppure mancini, contro gli stessi avversari e con gli stessi semi.
Dice quanto valgono davvero nelle partite, e quanto il valore dà loro: la regressione ha un peso
solo per caratteristica, e dove l'effetto non è una retta, come la resistenza nella stanchezza,
o dove i giocatori sono pochi, come i mancini, può sbagliare. Anche la verifica si fa su tutti i
semi, con 480 soggetti per seme, e somma i loro incontri: con duecento soggetti e un seme solo il
mancino oscillava fra 1 e 5,5 punti, e non poteva confermare la banda da 2 a 6 di Gabriele. Il
rapporto dà anche il mancino seme per seme, con l'errore della media.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/taratura_valore.py
    python strumenti/taratura_valore.py --semi 9 19 29 39 --mondo salvato --rapporto taratura_valore.txt
"""

import argparse
import copy
import math
import os
import random
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))
STRUMENTI = Path(__file__).resolve().parent
if str(STRUMENTI) not in sys.path:
    sys.path.insert(0, str(STRUMENTI))

from popolazione_di_prova import genera  # noqa: E402
from simulazione_lunga import PESI_TAPPA_8, TRATTI_TAPPA_8, in_attivita, simula  # noqa: E402

import archivio  # noqa: E402
import costanti  # noqa: E402
import percorsi  # noqa: E402
import valore  # noqa: E402
from mondo import Mondo  # noqa: E402
from motore import ESSENZIALE, SINGOLARE_3, TARATURA, simula_incontro  # noqa: E402
from motore.campo import lettura_possibile, temperamento_relativo  # noqa: E402
from motore.taratura import carica_taratura  # noqa: E402

CONTROLLI = ("temperamento", "lettura", "fattore_eta")
# Le caratteristiche fisiche vanno da 0 a 10, le altre da 0 a 40.
FISICHE = ("precisione", "forza", "resistenza")
FASCE_DISTACCO = ((0.05, "meno del 5 per cento", (50, 58)), (0.15, "fra il 5 e il 15 per cento", (58, 70)),
                  (0.30, "fra il 15 e il 30 per cento", (70, 85)), (None, "oltre il 30 per cento", (85, 96)))


def numero(valore_numerico, decimali=1):
    return f"{valore_numerico:.{decimali}f}".replace(".", ",")


def percentile(valori, quota):
    ordinati = sorted(valori)
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))]


def massimo_di(nome):
    return 10.0 if nome in FISICHE else 40.0


def fattore_eta(g, t=TARATURA):
    anni = g.eta_anni
    return 1.0 + max(0.0, anni - t.ETA_INIZIO_FATICA) / t.ANNI_FATICA + max(0.0, t.ETA_FATICA_GIOVANI - anni) * t.FATICA_GIOVANI_PER_ANNO


def _gruppi():
    """Le colonne delle caratteristiche: le coppie speculari di colpi e battute insieme, le altre da sole."""
    nomi = costanti.CARATTERISTICHE_VALORE
    gruppi = []
    for nome in nomi:
        if nome.endswith("dx") and nome[:-2] + "sx" in nomi:
            continue
        if nome.endswith("sx") and nome[:-2] + "dx" in nomi:
            gruppi.append((nome, nome[:-2] + "dx"))
        else:
            gruppi.append((nome,))
    return tuple(gruppi)


GRUPPI = _gruppi()


def regressori(g):
    """Le caratteristiche del valore, i tratti e i controlli di un giocatore, nell'ordine delle colonne."""
    caratteristiche = valore.caratteristiche(g, "totale")
    tratti = valore.tratti(g)
    riga = [sum(caratteristiche[nome] for nome in gruppo) for gruppo in GRUPPI]
    riga += [1.0 if tratti[nome] else 0.0 for nome in valore.TRATTI]
    riga += [temperamento_relativo(g), lettura_possibile(g, TARATURA), fattore_eta(g)]
    riga.append(1.0)
    return riga


COLONNE = (*(" e ".join(gruppo) for gruppo in GRUPPI), *valore.TRATTI, *CONTROLLI, "costante")
VINCOLATE = frozenset(range(len(GRUPPI) + len(valore.TRATTI)))


def ridistribuisci_tratti(giocatori, quota, seme):
    """
    Ridà a ogni giocatore i quattro tratti, ciascuno con la probabilità indicata, mancino e
    ambidestro esclusi a vicenda come alla nascita; poi ricalcola il valore.
    """
    rng = random.Random(f"tratti-{seme}")
    for g in giocatori:
        g.mancino = rng.random() < quota
        g.ambidestro = not g.mancino and rng.random() < quota
        g.giocorapido = rng.random() < quota
        g.cambiovelocita = rng.random() < quota
        g.aggiorna_icv()
    return giocatori


def _rating_di_un_gruppo(giocatori, sparring, seme, taratura):
    """I rating di una parte dei giocatori: ognuno ha il suo generatore, così l'esito non dipende da come si dividono."""
    risultati = {}
    for g in giocatori:
        rng = random.Random(f"rating-{seme}-{g.id}")
        fatti = subiti = 0
        for indice, s in enumerate(sparring):
            primo = indice % 2 == 0
            a, b = (g, s) if primo else (s, g)
            r = simula_incontro(a, b, SINGOLARE_3, seme=rng.getrandbits(63), dettaglio=ESSENZIALE, taratura=taratura)
            punti_a = sum(x for x, _y in r.set)
            punti_b = sum(y for _x, y in r.set)
            fatti += punti_a if primo else punti_b
            subiti += punti_b if primo else punti_a
        risultati[g.id] = math.log(max(1, fatti) / max(1, subiti))
    return risultati


def rating(giocatori, sparring, seme, taratura=TARATURA, processi=1):
    """
    Il rating di ogni giocatore contro gli sparring: il logaritmo del rapporto fra punti fatti e
    subiti in un incontro al meglio dei 3 set contro ciascuno, a parti alternate. Con più
    processi i giocatori si dividono fra loro; il risultato è identico.
    """
    if processi <= 1:
        return _rating_di_un_gruppo(giocatori, sparring, seme, taratura)
    # I processi figli ricevono la funzione per nome: la si prende dal modulo importato col suo
    # nome, perché quella dello script lanciato direttamente si chiama __main__ e i figli non la
    # ritroverebbero.
    from taratura_valore import _rating_di_un_gruppo as lavoro
    gruppi = [giocatori[i::processi] for i in range(processi)]
    risultati = {}
    with ProcessPoolExecutor(max_workers=processi) as esecutore:
        for parziale in esecutore.map(lavoro, gruppi, [sparring] * processi, [seme] * processi, [taratura] * processi):
            risultati.update(parziale)
    return risultati


def _risolvi(matrice, termini):
    """Risolve un sistema lineare con l'eliminazione di Gauss e il pivot parziale."""
    n = len(termini)
    a = [[*riga, termini[i]] for i, riga in enumerate(matrice)]
    for colonna in range(n):
        pivot = max(range(colonna, n), key=lambda r: abs(a[r][colonna]))
        if abs(a[pivot][colonna]) < 1e-12:
            raise ValueError("Il sistema della regressione è singolare: servono più giocatori.")
        a[colonna], a[pivot] = a[pivot], a[colonna]
        for riga in range(colonna + 1, n):
            fattore = a[riga][colonna] / a[colonna][colonna]
            if fattore:
                for k in range(colonna, n + 1):
                    a[riga][k] -= fattore * a[colonna][k]
    soluzione = [0.0] * n
    for riga in range(n - 1, -1, -1):
        somma = a[riga][n] - sum(a[riga][k] * soluzione[k] for k in range(riga + 1, n))
        soluzione[riga] = somma / a[riga][riga]
    return soluzione


def minimi_quadrati(righe, y, vincolate=VINCOLATE):
    """
    I minimi quadrati con i pesi vincolati non negativi, col metodo dell'insieme attivo: si risolve
    sulle colonne ammesse, si azzera la vincolata più negativa e si risolve di nuovo.
    Restituisce i coefficienti, zero per le colonne escluse, e le colonne escluse in ordine.
    """
    n = len(righe[0])
    xtx = [[0.0] * n for _ in range(n)]
    xty = [0.0] * n
    for riga, valore_y in zip(righe, y, strict=True):
        for i in range(n):
            ri = riga[i]
            if ri:
                xty[i] += ri * valore_y
                riga_xtx = xtx[i]
                for j in range(n):
                    riga_xtx[j] += ri * riga[j]
    attive = list(range(n))
    escluse = []
    while True:
        soluzione = _risolvi([[xtx[i][j] for j in attive] for i in attive], [xty[i] for i in attive])
        coefficienti = [0.0] * n
        for indice, colonna in enumerate(attive):
            coefficienti[colonna] = soluzione[indice]
        negative = [(coefficienti[c], c) for c in attive if c in vincolate and coefficienti[c] < 0]
        if not negative:
            return coefficienti, escluse
        _peggiore, colonna = min(negative)
        attive.remove(colonna)
        escluse.append(colonna)


def previsione(coefficienti, riga):
    return sum(c * x for c, x in zip(coefficienti, riga, strict=True))


def r_quadro(coefficienti, righe, y):
    media = statistics.fmean(y)
    residui = sum((v - previsione(coefficienti, r)) ** 2 for r, v in zip(righe, y, strict=True))
    totale = sum((v - media) ** 2 for v in y)
    return 1.0 - residui / totale


def correlazione(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=True))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)


def pesi_dai_coefficienti(coefficienti):
    """
    I pesi del valore, normalizzati perché la media delle caratteristiche di gioco, quelle da 0 a
    40, valga 1 come nel valore di prima; i tratti nella stessa unità.
    """
    n = len(GRUPPI)
    grezzi = {nome: coefficienti[indice] for indice, gruppo in enumerate(GRUPPI) for nome in gruppo}
    di_gioco = [grezzi[nome] for nome in costanti.CARATTERISTICHE_VALORE if nome not in FISICHE]
    unita = statistics.fmean(di_gioco)
    pesi = {nome: grezzi[nome] / unita for nome in costanti.CARATTERISTICHE_VALORE}
    tratti = {nome: coefficienti[n + i] / unita for i, nome in enumerate(valore.TRATTI)}
    return pesi, tratti, unita


def fattore_stipendio(indice):
    """Il fattore dello stipendio della decisione D22 per un valore: uno al valore di riferimento."""
    return math.exp((indice - costanti.VALORE_DI_RIFERIMENTO) / costanti.SCALA_STIPENDIO)


def scala(giocatori, pesi, tratti):
    """
    A e B: la mediana del valore della tappa 8, e la media del suo fattore di stipendio, cioè il
    monte stipendi. Con A legato a B dalla mediana, la media del fattore cresce con B, e B si
    trova per bisezione.
    """
    vecchi = [valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in giocatori]
    somme = [valore.indice(g, pesi, tratti, 0.0, 1.0) for g in giocatori]
    mediana_vecchia, mediana_somme = statistics.median(vecchi), statistics.median(somme)
    obiettivo = statistics.fmean(fattore_stipendio(v) for v in vecchi)

    def media_del_fattore(b):
        a = mediana_vecchia - b * mediana_somme
        return statistics.fmean(fattore_stipendio(a + b * s) for s in somme)

    basso, alto = 0.0, 10.0
    for _passo in range(60):
        b = (basso + alto) / 2.0
        if media_del_fattore(b) < obiettivo:
            basso = b
        else:
            alto = b
    b = (basso + alto) / 2.0
    return mediana_vecchia - b * mediana_somme, b


def descrivi_distribuzione(nome, valori):
    return (f"{nome}: mediana {numero(statistics.median(valori))}, decimo percentile {numero(percentile(valori, 0.1))}, "
            f"novantesimo {numero(percentile(valori, 0.9))}, da {numero(min(valori))} a {numero(max(valori))}.")


def curva_del_favorito(giocatori, indice_di, quante, seme, taratura=TARATURA):
    """Quante partite vince il favorito per fasce di distacco dell'indice, su coppie estratte a caso."""
    rng = random.Random(seme)
    esiti = []
    for _ in range(quante):
        a, b = rng.sample(giocatori, 2)
        ia, ib = indice_di[a.id], indice_di[b.id]
        if ia == ib:
            continue
        r = simula_incontro(a, b, SINGOLARE_3, seme=rng.getrandbits(63), dettaglio=ESSENZIALE, taratura=taratura)
        distacco = (max(ia, ib) - min(ia, ib)) / max(1.0, min(ia, ib))
        esiti.append((distacco, (r.vincitore == "A") == (ia > ib)))
    righe = []
    minimo = 0.0
    for limite, nome, intervallo in FASCE_DISTACCO:
        massimo = limite if limite is not None else float("inf")
        fascia = [vinta for distacco, vinta in esiti if minimo <= distacco < massimo]
        minimo = massimo
        if fascia:
            quota = 100.0 * sum(fascia) / len(fascia)
            esito = "dentro" if intervallo[0] <= quota <= intervallo[1] else "FUORI"
            righe.append(f"Con un distacco {nome}: {len(fascia)} partite, il favorito ne vince il {numero(quota)} per cento, bersaglio da {intervallo[0]} a {intervallo[1]}, {esito}.")
    return righe


# La verifica a coppie del quinto passo: le modifiche da misurare, e quelle di riferimento, che
# danno quanto rating vale un punto di valore. Una modifica è un elenco di attributi con l'aumento,
# oppure il mancino: lo stesso giocatore con chiusure e blocchi specchiati e il tratto.
VERIFICHE = (("un punto di precisione allenata", (("precisione_allenata", 1.0),)), ("un punto di resistenza innata", (("resistenza_base", 1.0),)),
             ("un punto di resistenza allenata", (("resistenza_allenata", 1.0),)), ("il mancino, con chiusure e blocchi specchiati", "mancino"))
RIFERIMENTI = ((("difesa_allenata", 8.0),), (("chiusurasx_allenata", 8.0), ("chiusuradx_allenata", 8.0)), (("forza_allenata", 3.0),), (("attacco_allenata", 8.0),))


def modificato(g, modifica):
    """Una copia del giocatore con la modifica della verifica a coppie."""
    m = copy.copy(g)
    if modifica == "mancino":
        for radice in ("chiusura", "blocco"):
            for parte in ("_base", "_allenata"):
                sx, dx = radice + "sx" + parte, radice + "dx" + parte
                setattr(m, sx, getattr(g, dx))
                setattr(m, dx, getattr(g, sx))
        m.mancino, m.ambidestro = True, False
        return m
    for nome, aumento in modifica:
        setattr(m, nome, getattr(m, nome) + aumento)
    return m


def _coppie_di_un_gruppo(soggetti, avversari, seme, taratura):
    """I punti fatti e subiti da una parte dei soggetti, come sono e con ogni modifica, contro gli stessi avversari e con gli stessi semi."""
    modifiche = [(), *(m for _nome, m in VERIFICHE), *RIFERIMENTI]
    conti = [[0, 0] for _m in modifiche]
    for g in soggetti:
        rng = random.Random(f"coppie-{seme}-{g.id}")
        semi = [rng.getrandbits(63) for _a in avversari]
        for conto, modifica in zip(conti, modifiche, strict=True):
            m = modificato(g, modifica)
            for avversario, seme_incontro in zip(avversari, semi, strict=True):
                r = simula_incontro(m, avversario, SINGOLARE_3, seme=seme_incontro, dettaglio=ESSENZIALE, taratura=taratura)
                conto[0] += sum(x for x, _y in r.set)
                conto[1] += sum(y for _x, y in r.set)
    return conti


def _somma_conti(primi, secondi):
    return [[x + y for x, y in zip(c, p, strict=True)] for c, p in zip(primi, secondi, strict=True)]


def verifica_a_coppie(gruppi, pesi, tratti, a, b, taratura=TARATURA, processi=1):
    """
    Il quinto passo: quanto valgono davvero nelle partite alcune modifiche, misurate a coppie, gli
    stessi soggetti contro gli stessi avversari e con gli stessi semi, e quanto dà loro il valore.
    I gruppi sono terne di soggetti, avversari e seme, una per seme della taratura: i loro
    incontri si sommano, e il mancino, che oscilla di più, si dà anche gruppo per gruppo, con
    l'errore della media. Il rating guadagnato si porta in punti di valore con quello delle
    modifiche di riferimento, difesa, chiusure, forza e attacco, che il valore pesa giuste. La
    regressione dà un peso solo a ogni caratteristica: la resistenza allenata, che conta anche come
    abitudine ad allenarsi, rende un po' più di quella innata, e il prezzo unico deve stare fra le
    due; il mancino, portato da pochi giocatori, è il punto dove la regressione oscilla di più.
    """
    lavori = [(indice, soggetti[i::processi], avversari, seme) for indice, (soggetti, avversari, seme) in enumerate(gruppi) for i in range(max(1, processi))]
    if processi <= 1:
        parziali = [_coppie_di_un_gruppo(soggetti, avversari, seme, taratura) for _indice, soggetti, avversari, seme in lavori]
    else:
        from taratura_valore import _coppie_di_un_gruppo as lavoro
        with ProcessPoolExecutor(max_workers=processi) as esecutore:
            parziali = list(esecutore.map(lavoro, [x[1] for x in lavori], [x[2] for x in lavori], [x[3] for x in lavori], [taratura] * len(lavori)))
    per_gruppo = [None] * len(gruppi)
    for (indice, *_resto), parziale in zip(lavori, parziali, strict=True):
        per_gruppo[indice] = parziale if per_gruppo[indice] is None else _somma_conti(per_gruppo[indice], parziale)
    totale = per_gruppo[0]
    for conti in per_gruppo[1:]:
        totale = _somma_conti(totale, conti)
    tutti = [g for soggetti, _avversari, _seme in gruppi for g in soggetti]
    n = len(VERIFICHE)

    def rating_di(conti):
        return [math.log(fatti / subiti) - math.log(conti[0][0] / conti[0][1]) for fatti, subiti in conti]

    def punti_di_valore(modifica, soggetti):
        return statistics.fmean(valore.indice(modificato(g, modifica), pesi, tratti, a, b) - valore.indice(g, pesi, tratti, a, b) for g in soggetti)

    def per_punto_di(rating, soggetti):
        return statistics.fmean(rating[1 + n + i] / punti_di_valore(modifica, soggetti) for i, modifica in enumerate(RIFERIMENTI))

    rating = rating_di(totale)
    per_punto = per_punto_di(rating, tutti)
    avversari_per_gruppo = len(gruppi[0][1])
    righe = [f"Quinto passo, la verifica a coppie: {len(tutti)} soggetti destrimani in {len(gruppi)} gruppi, uno per seme, ciascuno contro {avversari_per_gruppo} avversari, "
             f"con gli stessi semi; un punto di valore vale {numero(1000 * per_punto, 2)} millesimi di rating, misurati su difesa, chiusure, forza e attacco."]
    for i, (nome, modifica) in enumerate(VERIFICHE):
        righe.append(f"Nelle partite {nome} vale {numero(rating[1 + i] / per_punto)} punti di valore; il valore gliene dà {numero(punti_di_valore(modifica, tutti))}.")
    indice_mancino = 1 + next(i for i, (_nome, modifica) in enumerate(VERIFICHE) if modifica == "mancino")
    if len(gruppi) > 1:
        mancini = []
        for (soggetti, _avversari, _seme), conti in zip(gruppi, per_gruppo, strict=True):
            rating_gruppo = rating_di(conti)
            mancini.append(rating_gruppo[indice_mancino] / per_punto_di(rating_gruppo, soggetti))
        errore = statistics.stdev(mancini) / math.sqrt(len(mancini))
        righe.append("Il mancino gruppo per gruppo, nell'ordine dei semi: " + ", ".join(numero(m) for m in mancini)
                     + f" punti di valore; la media {numero(statistics.fmean(mancini))}, con un errore della media di {numero(errore)}.")
    return righe


def mondo_salvato():
    """I giocatori in attività del mondo salvato, letti in sola lettura."""
    mondo = Mondo()
    archivio.costruisci(archivio.leggi(percorsi.percorso(costanti.FILE_MONDO)), mondo)
    return [g for g in mondo.giocatori.values() if not g.ritirato]


def blocco_costanti(pesi, tratti, a, b):
    righe = ["PESI_VALORE = {"]
    voci = [f'"{nome}": {pesi[nome]:.2f}' for nome in costanti.CARATTERISTICHE_VALORE]
    for inizio in range(0, len(voci), 6):
        righe.append("    " + ", ".join(voci[inizio:inizio + 6]) + ",")
    righe.append("}")
    righe.append("PESI_TRATTI = {" + ", ".join(f'"{nome}": {tratti[nome]:.1f}' for nome in valore.TRATTI) + "}")
    righe.append(f"SCALA_VALORE_A = {a:.2f}")
    righe.append(f"SCALA_VALORE_B = {b:.4f}")
    return righe


def misura_un_seme(seme, argomenti, taratura):
    """
    I primi due passi per un seme: le popolazioni, il rating contro gli sparring e la regressione.
    Restituisce i pesi normalizzati, i tratti e i controlli nella stessa unità, la popolazione di
    verifica col suo rating, gli sparring e le misure della regressione.
    """
    popolazione = genera(argomenti.giocatori, seme, quota_allenati=0.6, punti=(0, 220), esperienza=(0, 12), primo_id=1)
    sparring = genera(argomenti.sparring, seme + 1, quota_allenati=0.6, punti=(0, 220), esperienza=(0, 12), primo_id=500_001)
    verifica = genera(argomenti.verifica, seme + 2, quota_allenati=0.6, punti=(0, 220), esperienza=(0, 12), primo_id=600_001)
    ridistribuisci_tratti(popolazione, argomenti.quota_tratti, seme)
    ridistribuisci_tratti(verifica, argomenti.quota_tratti, seme + 2)
    rating_pop = rating(popolazione, sparring, seme * 1000 + 1, taratura, argomenti.processi)
    rating_ver = rating(verifica, sparring, seme * 1000 + 2, taratura, argomenti.processi)
    righe_x = [regressori(g) for g in popolazione]
    y = [rating_pop[g.id] for g in popolazione]
    coefficienti, escluse = minimi_quadrati(righe_x, y)
    righe_v = [regressori(g) for g in verifica]
    y_v = [rating_ver[g.id] for g in verifica]
    pesi, tratti, unita = pesi_dai_coefficienti(coefficienti)
    n = len(GRUPPI) + len(valore.TRATTI)
    return {"seme": seme, "pesi": pesi, "tratti": tratti, "controlli": {nome: coefficienti[n + i] / unita for i, nome in enumerate(CONTROLLI)},
            "escluse": [COLONNE[c] for c in escluse], "r2": r_quadro(coefficienti, righe_x, y), "r2_verifica": r_quadro(coefficienti, righe_v, y_v),
            "verifica": verifica, "rating_verifica": y_v, "sparring": sparring, "partite": (len(popolazione) + len(verifica)) * len(sparring)}


def elenco(valori):
    """Numeri separati da virgole, con la e prima dell'ultimo."""
    testi = [numero(v) if isinstance(v, float) else str(v) for v in valori]
    return testi[0] if len(testi) == 1 else ", ".join(testi[:-1]) + " e " + testi[-1]


def main():
    parser = argparse.ArgumentParser(description="Misura i pesi del valore complessivo di MESS sul motore di partita, senza scrivere nulla nel progetto.")
    parser.add_argument("--giocatori", type=int, default=3200, help="quanti giocatori nella popolazione della regressione per ogni seme, 3200 se non indicato")
    parser.add_argument("--verifica", type=int, default=400, help="quanti giocatori nella popolazione di verifica per ogni seme, 400 se non indicato")
    parser.add_argument("--sparring", type=int, default=48, help="quanti sparring fissi per ogni seme, 48 se non indicato")
    parser.add_argument("--quota-tratti", type=float, default=0.2, help="la frequenza di ogni tratto nelle popolazioni della regressione, 0,2 se non indicata")
    parser.add_argument("--curva", type=int, default=3000, help="quante partite per la curva del favorito, 3000 se non indicato")
    parser.add_argument("--coppie", type=int, default=480, help="quanti soggetti per seme nella verifica a coppie, 480 se non indicato, contro 40 sparring; 0 la salta")
    parser.add_argument("--semi", type=int, nargs="+", default=[9, 19, 29, 39], help="i semi della taratura, 9, 19, 29 e 39 se non indicati: i pesi sono la media")
    parser.add_argument("--anni", type=int, default=10, help="gli anni della simulazione lunga per il mondo maturo, 10 se non indicato")
    parser.add_argument("--mondo", choices=("nuovo", "salvato"), default="nuovo", help="con salvato aggiunge il controllo sul mondo salvato, letto in sola lettura")
    parser.add_argument("--taratura", type=Path, default=None, help="un file JSON di sostituzioni della taratura del motore")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti processi giocano le partite del rating, fino a 8 se il computer li ha")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il rapporto anche in questo file")
    argomenti = parser.parse_args()
    semi = argomenti.semi
    primo = semi[0]
    taratura = carica_taratura(argomenti.taratura) if argomenti.taratura else TARATURA
    inizio = time.perf_counter()
    righe = [f"Taratura del valore complessivo sul motore di partita, {time.strftime('%Y-%m-%d %H:%M')}, " + (f"semi {elenco(semi)}." if len(semi) > 1 else f"seme {primo}.")]
    if argomenti.taratura:
        righe.append(f"Taratura del motore letta da {argomenti.taratura}.")

    # Primo e secondo passo, per ogni seme: il rating dalle partite contro gli sparring e la
    # regressione con i pesi non negativi. I pesi sono la media dei semi.
    misure = [misura_un_seme(seme, argomenti, taratura) for seme in semi]
    righe.append(f"Primo passo: per ogni seme {argomenti.giocatori} giocatori, e {argomenti.verifica} per la verifica, contro {argomenti.sparring} sparring fissi; "
                 f"in tutto {sum(m['partite'] for m in misure)} incontri al meglio dei 3 set in {numero(time.perf_counter() - inizio)} secondi, con {argomenti.processi} processi.")
    pesi = {nome: statistics.fmean(m["pesi"][nome] for m in misure) for nome in costanti.CARATTERISTICHE_VALORE}
    tratti = {nome: statistics.fmean(m["tratti"][nome] for m in misure) for nome in valore.TRATTI}
    controlli = {nome: statistics.fmean(m["controlli"][nome] for m in misure) for nome in CONTROLLI}
    righe.append(f"Secondo passo: la regressione spiega, seme per seme, il {elenco([100 * m['r2'] for m in misure])} per cento della varianza del rating, "
                 f"e il {elenco([100 * m['r2_verifica'] for m in misure])} per cento nella popolazione di verifica."
                 + (" I pesi sono la media dei semi." if len(misure) > 1 else ""))
    for m in misure:
        if m["escluse"]:
            righe.append(f"Pesi azzerati perché sarebbero negativi, col seme {m['seme']}: " + ", ".join(m["escluse"]) + ".")
    vecchio, nuovo = [], []
    for m in misure:
        vecchio.append(correlazione([valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in m["verifica"]], m["rating_verifica"]))
        nuovo.append(correlazione([valore.indice(g, pesi, tratti, 0.0, 1.0) for g in m["verifica"]], m["rating_verifica"]))
    righe.append(f"Nella verifica il rating si lega al valore della tappa 8 con una correlazione media di {numero(statistics.fmean(vecchio), 3)}, "
                 f"e al valore nuovo, coi pesi medi, con {numero(statistics.fmean(nuovo), 3)}.")
    b_costanti = costanti.SCALA_VALORE_B
    if len(misure) > 1:
        righe.append("I tratti seme per seme, in punti di valore con la scala di costanti.py, B " + numero(b_costanti, 4) + ": "
                     + "; ".join(f"{nome} {elenco([b_costanti * m['tratti'][nome] for m in misure])}" for nome in valore.TRATTI) + ".")

    # Terzo passo: la scala sul mondo maturo, col primo seme.
    inizio_mondo = time.perf_counter()
    maturo, _racconto = simula(argomenti.anni, primo, stampa=None)
    attivi = in_attivita(maturo)
    a, b = scala(attivi, pesi, tratti)
    righe.append(f"Terzo passo: il mondo maturo di {argomenti.anni} anni simulati col seme {primo}, {len(attivi)} giocatori in attività, in {numero(time.perf_counter() - inizio_mondo)} secondi. "
                 f"La prima stima della scala, che conserva la mediana del valore di prima e il monte stipendi di questo mondo fermo: A {numero(a, 2)}, B {numero(b, 4)}. "
                 "Quella vera si cerca con simulazione_lunga.py --cerca-scala, dopo aver copiato i pesi.")
    vecchi = [valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in attivi]
    nuovi = [valore.indice(g, pesi, tratti, a, b) for g in attivi]
    righe.append(descrivi_distribuzione("Il valore di prima nel mondo maturo", vecchi))
    righe.append(descrivi_distribuzione("Il valore nuovo nel mondo maturo", nuovi))
    righe.append(f"Fra i due valori, nel mondo maturo, la correlazione è {numero(correlazione(vecchi, nuovi), 3)}. La media del fattore di stipendio è "
                 f"{numero(statistics.fmean(fattore_stipendio(v) for v in vecchi), 3)} col valore di prima e {numero(statistics.fmean(fattore_stipendio(v) for v in nuovi), 3)} col nuovo.")
    if argomenti.mondo == "salvato":
        salvati = mondo_salvato()
        righe.append(descrivi_distribuzione(f"Il valore di prima nel mondo salvato, {len(salvati)} giocatori", [valore.indice(g, PESI_TAPPA_8, TRATTI_TAPPA_8, 0.0, 1.0) for g in salvati]))
        righe.append(descrivi_distribuzione("Il valore nuovo nel mondo salvato", [valore.indice(g, pesi, tratti, a, b) for g in salvati]))
    neonati = genera(1000, primo + 4, quota_allenati=0.0, esperienza=(0, 0), primo_id=800_001)
    righe.append(descrivi_distribuzione("Il valore nuovo di mille neonati", [valore.indice(g, pesi, tratti, a, b) for g in neonati]))

    # Quarto passo: il rapporto.
    righe.append("Quarto passo, i pesi in punti di valore: per ogni punto della caratteristica, e fra parentesi da zero al massimo della scala.")
    voci = []
    for nome in costanti.CARATTERISTICHE_VALORE:
        voci.append(f"{nome} {numero(b * pesi[nome], 2)} ({numero(b * pesi[nome] * massimo_di(nome), 0)})")
    righe.append("; ".join(voci) + ".")
    righe.append("I tratti in punti di valore: " + "; ".join(f"{nome} {numero(b * tratti[nome])}" for nome in valore.TRATTI) + ".")
    # La scala vera la cerca poi la simulazione lunga: con quella già scritta in costanti.py i
    # punti di valore crescono o calano tutti nello stesso rapporto, e i tratti si leggono così.
    righe.append(f"Con la scala di costanti.py, B {numero(b_costanti, 4)}, i punti di valore si moltiplicano per {numero(b_costanti / b, 3)}: "
                 + "; ".join(f"{nome} {numero(b_costanti * tratti[nome])}" for nome in valore.TRATTI)
                 + f"; un punto di precisione {numero(b_costanti * pesi['precisione'], 2)}, uno di resistenza {numero(b_costanti * pesi['resistenza'], 2)}.")
    pieni = {nome: pesi[nome] * massimo_di(nome) for nome in costanti.CARATTERISTICHE_VALORE}
    media_gioco = statistics.fmean(pieni[nome] for nome in costanti.CARATTERISTICHE_VALORE if nome not in FISICHE)
    inerti = [nome for nome, peso in pieni.items() if peso < costanti.SOGLIA_PESO_INERTE * media_gioco]
    if inerti:
        righe.append(f"Caratteristiche quasi inerti, sotto {numero(costanti.SOGLIA_PESO_INERTE, 2)} volte il peso medio di gioco sulla scala piena: "
                     + ", ".join(inerti) + ". È un difetto da correggere nel motore, non nel valore.")
    else:
        righe.append("Nessuna caratteristica è quasi inerte: tutte pesano almeno un quarto della media di quelle di gioco.")
    righe.append(f"Il temperamento, dal calmissimo di tau meno 0,8 all'impetuoso di tau 0,8, vale {numero(controlli['temperamento'] * 1.6 * b)} punti di valore, bersaglio entro 5.")
    righe.append(f"L'esperienza di carriera, da 0 a 12, vale {numero(controlli['lettura'] * lettura_possibile(_Esperto(12.0), TARATURA) * b)} punti di valore; "
                 f"un punto di fattore d'età della stanchezza ne vale {numero(controlli['fattore_eta'] * b)}.")
    righe.append("La curva del favorito, col valore nuovo, su una terza popolazione:")
    terza = genera(800, primo + 3, quota_allenati=0.6, punti=(0, 220), esperienza=(0, 12), primo_id=700_001)
    indice_terza = {g.id: valore.indice(g, pesi, tratti, a, b) for g in terza}
    righe.extend(curva_del_favorito(terza, indice_terza, argomenti.curva, primo * 1000 + 3, taratura))

    # Quinto passo: la verifica a coppie, su tutti i semi, con soggetti destrimani nati apposta.
    if argomenti.coppie:
        gruppi = []
        for m in misure:
            seme = m["seme"]
            candidati = genera(2 * argomenti.coppie, seme + 5, quota_allenati=0.6, punti=(0, 220), esperienza=(0, 12), primo_id=1_000_001)
            soggetti = [g for g in candidati if not g.mancino and not g.ambidestro][:argomenti.coppie]
            gruppi.append((soggetti, m["sparring"][:40], seme * 1000 + 4))
        righe.extend(verifica_a_coppie(gruppi, pesi, tratti, a, b, taratura, argomenti.processi))
    righe.append("Il blocco da copiare in costanti.py, con la prima stima della scala:")
    righe.extend(blocco_costanti(pesi, tratti, a, b))
    righe.append(f"Taratura completata in {numero(time.perf_counter() - inizio)} secondi.")
    testo = "\n".join(righe)
    print(testo)
    if argomenti.rapporto:
        argomenti.rapporto.write_text(testo + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


class _Esperto:
    """Un segnaposto con la sola esperienza, per la lettura del gioco possibile."""

    def __init__(self, esperienza):
        self.esperienza = esperienza


if __name__ == "__main__":
    main()
