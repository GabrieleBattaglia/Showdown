"""
La misura della rivendita al computer della decisione D40: quanto rende ancora tesserare un libero e rivenderlo al
computer, con la rampa del prezzo scelta da Gabriele il 3 novembre 2026.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-11-03 con la settima tranche di D40, dagli script commercio.py e rimedi_commercio.py della verifica
dei trucchi del 2 novembre 2026, rifatti come chiede la critica alla decisione 6. Il trucco: tesserare un libero
all'ingaggio che chiede, da 1 a 4 stipendi, e venderlo al computer, che pagava fino al valore di mercato col suo
rialzo, circa 6,9 stipendi. La misura vecchia contava la cassa meno lo sponsor, e gli stipendi dei mesi d'attesa
diventavano un costo del trucco; ma in quei mesi il giocatore sta in rosa, e una rosa onesta paga gli stessi
stipendi e incassa lo stesso sponsor. Qui le strategie sono due, tutte e due con la rosa piena: rivendi e riempi,
dove il commerciante mette i tesserati in vendita al prezzo più alto che il computer paga e il posto si riempie
appena il computer lo compra; tieni e rinnova, dove la rosa si tiene, i contratti si rinnovano e si riempie
soltanto il posto di chi se ne va. Il risultato è la differenza fra le due, per posto e per anno.
La settima tranche misurava i mesi d'attesa prima della rivendita, MESI_PRIMA_DELLA_RIVENDITA, col prezzo sempre al
tetto pieno: nessun numero fino a 12 chiudeva il commercio, e Gabriele ha scelto la rampa, economia.tetto_di_rivendita,
che il giorno della firma vale l'ingaggio chiesto e sale in linea retta fino al tetto pieno in MESI_DELLA_RAMPA mesi.
Lo stesso giorno lo strumento è passato a misurare la rampa: nella rivendita a t mesi il commerciante mette in
vendita un tesserato quando ha t mesi di firma, al tetto della rampa del giorno, e il computer compra come nel
gioco; il risultato dice, per ogni t, quanto rende ancora il commercio, e qual è il t più redditizio. I numeri delle
due misure, e i verdetti, stanno in strumenti/rivendita_d40.txt.
Lo stesso giorno, per la via di mezzo chiesta da Gabriele, l'opzione --mesi-della-rampa misura il commercio con una
rampa di un'altra durata, per esempio 42 mesi, senza cambiare il gioco: costanti.py ed economia.py restano come sono.
economia importa MESI_DELLA_RAMPA dalle costanti col suo nome, e la rampa di tetto_di_rivendita lo legge da lì a ogni
chiamata: imposta_la_rampa cambia quel nome, economia.MESI_DELLA_RAMPA, nel processo principale e, come
inizializzatore del ProcessPoolExecutor, in ogni processo figlio, e tetto_atteso legge lo stesso. Così la durata vale
per il computer che compra, Mondo._vendibili, per il commerciante che mette in vendita e per la scelta dei liberi da
tesserare. Di serie è la rampa del gioco, MESI_DELLA_RAMPA. La misura a 42 mesi e la proiezione per altre durate
stanno nella terza parte di strumenti/rivendita_d40.txt.
Lo stesso giorno, dopo la scelta di una rampa di 36 mesi e prima della decisione, Gabriele ha chiesto di misurare la
rampa che parte dall'ingaggio della firma. Nel gioco la rampa parte dall'ingaggio che il giocatore chiede il giorno
della vendita, e quell'ingaggio cresce mentre il giocatore resta in rosa e si allena: con --partenza-della-rampa firma
parte invece, in tutti i processi della corsa, dall'ingaggio che il giocatore ha chiesto alla polisportiva il giorno
della firma, cioè quello pagato, e resta quello per tutta la rampa; il tetto pieno resta quello del giorno della
vendita, e il resto della regola non cambia. Il giocatore del gioco ricorda soltanto il giorno della firma: l'ingaggio
lo scrive lo strumento, ricorda_la_firma, sul giocatore, ingaggio_della_firma, insieme al giorno della firma, quando
lo tessera e, per i quindici della partenza, all'inizio della corsa, dopo a_regime, con l'ingaggio chiesto quel
giorno, che è quello pagato. tetto_di_rivendita legge economia._rampa da economia a ogni chiamata, e imposta_la_rampa,
nel processo principale e come inizializzatore in ogni figlio, mette al suo posto rampa_dalla_firma, la stessa regola
con l'altra partenza. Così la stessa partenza vale per il computer che compra, Mondo._vendibili, per il commerciante
che mette in vendita, per la rosa pari e per il margine delle vendite, che contano l'ingaggio della firma con tutte e
due le partenze; tetto_atteso resta com'è, perché il giorno della firma le due partenze coincidono. Di serie la
partenza è vendita, la regola del gioco: costanti.py, economia.py e mondo.py restano come sono. Ogni corsa scrive nel
risultato la partenza che ha visto, e per ogni vendita conta anche il margine pieno, il tetto pieno meno l'ingaggio
della firma, e quanto è cresciuto in rosa l'ingaggio chiesto. È di Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus
5.5, UltraCode); la misura sta nella quarta parte di strumenti/rivendita_d40.txt.
I mondi nascono col codice di oggi, con mondi_sintetici.mondo_nato, uno per seme, e si salvano alle età date, di
serie 730 e 3.650 giorni, nella cartella di lavoro. In ogni mondo nascono, ciascuna da sola, due polisportive
dell'utente: la gloriosa, con la gloria tenuta a 275, e la media, a 150, la gloria che una polisportiva
dell'utente ha senza palmarès, con la rosa piena. La gloria mediana del computer non fa da media: nei mondi nati è
circa 215 a due anni e 290 a dieci, sopra la gloriosa. La gloria si tiene con un palmarès finto nel mese prima
della partenza, rifatto ogni giorno sulla rosa del giorno, che toglie le medaglie e le coppe vere e aggiunge le
coppe che mancano al bersaglio: così non dipende dai risultati, e le due strategie hanno la stessa gloria; una
rosa che senza palmarès sta già sopra il bersaglio resta alla sua gloria. La cassa parte da un milione di euro,
perché nessuna resti senza soldi. La partenza è comune: la polisportiva si riempie coi liberi fino a 30 anni che
rendono di più, il tetto del computer meno l'ingaggio chiesto, e che oggi una polisportiva del computer potrebbe
comprare, con l'ingaggio chiesto, che accettano una volta su due, ripetuto finché ci sono mosse. Il mondo con la
rosa piena si salva, e tutte le strategie partono da lì, con lo stesso caso.
Ogni giorno simulato, in tutte e due le strategie: Allena tutti, i rinnovi alla richiesta e alla durata proposta,
come lo scenario dell'utente di simulazione_lunga.py, e i posti vuoti riempiti con la regola della partenza. Nella
rivendita i posti si riempiono invece col guadagno per giorno del ciclo stimato, il tetto della rampa il giorno
della vendita meno l'ingaggio, diviso per i giorni dalla firma alla vendita, soltanto con chi non entra nel declino
prima della vendita e chi oggi una polisportiva del computer comprerebbe a quel prezzo. Da t mesi dopo la firma il
tesserato sta in vendita al tetto della rampa del giorno, e il prezzo si rifà ogni volta che il tetto cambia. Negli
ultimi tre mesi di contratto il tetto scende col valore, che nelle vendite dell'utente non conta il rinnovo
concordato: con un rinnovo concordato il commerciante toglie il tesserato dalla vendita e aspetta che il rinnovo
parta, quando il tetto torna pieno; senza, lo lascia in vendita al tetto che scende, per non perderlo libero alla
scadenza. La rampa è quella del gioco, di MESI_DELLA_RAMPA mesi, o quella di --mesi-della-rampa: t è la scelta del
commerciante.
La partenza a regime: nella rivendita a t mesi i quindici della partenza diventano i tesserati di un commercio che va
avanti da sempre. La firma si sposta indietro a passi regolari fra 0 e t mesi, e con lei il contratto, della stessa
durata e allo stesso stipendio, rinnovato per la stessa durata finché scadrebbe prima di oggi, e la fedeltà cresce
dei primi del mese passati. Così ogni tesserato arriva alla vendita col tetto della rampa a t mesi e col contratto al
punto in cui lo avrebbe chi ha firmato t mesi prima, come nei cicli che seguono; le vendite si spargono nel tempo, e
la differenza divisa per gli anni misura il guadagno a regime anche quando la durata non è un multiplo di t. La
settima tranche spostava soltanto la firma: col prezzo pieno bastava, con la rampa il prezzo dipende anche dalla
scadenza, e il primo ciclo trovava il contratto più lungo di quelli che seguono.
I conti sono tutte le voci dei conti del mese: sponsor, con la regola della seconda tranche di D40, vendite,
stipendi, arretrati, ingaggi, buonuscite, iscrizioni, premi e rimborsi; la loro somma è la cassa, e lo strumento lo
controlla. Accanto alla differenza lo strumento dà la differenza a rosa pari, dove ogni rosa conta al suo costo,
l'ingaggio da cui parte la rampa di ognuno, quella della fine in più e quella della partenza in meno: toglie l'effetto
di una rosa che alla fine non è come alla partenza, come nella vendita a 0 mesi, dove il computer compra più in fretta
di quanto il commerciante tesseri. Per ogni vendita conta anche il margine, il prezzo meno l'ingaggio di chi è venduto.
Non tocca mai il mondo salvato: ogni processo sposta la cartella del programma e quella del mondo in cartelle
temporanee, che alla fine si cancellano; i mondi e le partenze vivono nella cartella di lavoro, che senza
--cartella è temporanea anche lei. Le corse vanno in parallelo, al più --processi insieme.
Uso: python -B strumenti/misura_rivendita.py [--semi 11 2026 7 13] [--giorni-dei-mondi 730 3650]
[--mesi 0 1 3 6 12 18 24] [--durata 36] [--mesi-della-rampa 24] [--partenza-della-rampa vendita] [--gloria 275]
[--gloria-media 150] [--club gloriosa media] [--processi 16] [--cartella C] [--salva risultati.json]
"""

import argparse
import datetime
import gc
import json
import os
import pickle
import random
import shutil
import statistics
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager, suppress
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
for _cartella in (RADICE, RADICE / "strumenti"):
    if str(_cartella) not in sys.path:
        sys.path.insert(0, str(_cartella))

import mondi_sintetici as ms  # noqa: E402

import allenamento  # noqa: E402
import archivio  # noqa: E402
import contratti  # noqa: E402
import economia  # noqa: E402
import palmares  # noqa: E402
import percorsi  # noqa: E402
import testi  # noqa: E402
import tratti  # noqa: E402
from costanti import (  # noqa: E402
    FEDELTA_PER_MESE,
    GIORNI_PER_MESE,
    K_GLORIA_COPPE,
    MAX_TESSERATI_POLISPORTIVA,
    MESI_DELLA_RAMPA,
    MESI_DI_INGAGGIO,
    MESI_DI_RISERVA_CPU,
    MESI_VALORE_PIENO,
    RIALZO_CPU,
    STIPENDIO_MINIMO,
)
from modelli import VOCI_CONTI, conti_vuoti  # noqa: E402

SEMI = (11, 2026, 7, 13)
GIORNI_DEI_MONDI = (730, 3650)
# I mesi di firma dopo i quali il commerciante mette in vendita: t, nella rivendita.
MESI_PROVATI = (0, 1, 3, 6, 12, 18, 24)
DURATA_MESI = 36
PROCESSI = 16
GLORIA_GLORIOSA = 275
GLORIA_MEDIA = 150
CASSA_DI_PARTENZA = 1_000_000
# I liberi fino a 30 anni, come lo scenario dell'utente di simulazione_lunga.py.
ETA_MASSIMA = 30.0
# I giorni concessi alla partenza per riempire la rosa: con cinque mosse e un sì su due ne bastano sei o sette.
GIORNI_DI_RIEMPIMENTO = 30
CLUB = {"gloriosa": ("Bottega Gloriosa", 1), "media": ("Bottega Media", 2)}
# Le voci che entrano in cassa; le altre escono.
ENTRATE = ("sponsor", "vendite", "premi", "rimborsi", "fondi_ricevuti")
# Le voci dette una per una nella tabella; le altre vanno insieme in tornei e resto.
VOCI_DETTE = ("vendite", "ingaggi", "stipendi", "sponsor", "buonuscite", "arretrati")
# Da dove parte la rampa del tetto: dall'ingaggio chiesto il giorno della vendita, come nel gioco, o da quello della firma.
PARTENZE_DELLA_RAMPA = ("vendita", "firma")
# La rampa del gioco, presa prima di ogni sostituzione: con la partenza vendita torna lei.
RAMPA_DEL_GIOCO = economia._rampa
# Le volte in cui, con la partenza firma, la rampa di un tesserato non trova l'ingaggio della sua firma e parte da quello
# di oggi; ogni corsa lo azzera e lo scrive nel risultato, e deve restare zero.
SENZA_FIRMA = {"volte": 0}


@contextmanager
def cartelle_temporanee():
    """La cartella del programma e quella del mondo in una cartella temporanea, cancellata alla fine. La vecchia non torna: meglio un errore che una scrittura nel mondo vero."""
    radice = Path(tempfile.mkdtemp(prefix="mess_rivendita_"))
    programma, mondo = radice / "programma", radice / "mondo"
    programma.mkdir()
    mondo.mkdir()
    percorsi.cartella_del_programma = lambda: str(programma)
    percorsi.imposta_cartella(str(mondo))
    try:
        yield
    finally:
        shutil.rmtree(radice, ignore_errors=True)


def salva(oggetto, percorso):
    """Scrive l'oggetto in un pickle, passando da un file accanto, così un processo interrotto non lascia un file a metà."""
    percorso = Path(percorso)
    provvisorio = percorso.with_suffix(".provvisorio")
    with provvisorio.open("wb") as f:
        pickle.dump(oggetto, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(provvisorio, percorso)


def carica(percorso):
    """Legge un pickle con la raccolta dei cicli spenta, poi congela la memoria come il programma."""
    gc.disable()
    try:
        with Path(percorso).open("rb") as f:
            # I pickle li scrive soltanto questo strumento, nella sua cartella di lavoro.
            oggetto = pickle.load(f)  # noqa: S301
    finally:
        gc.enable()
    archivio.congela_la_memoria()
    return oggetto


def file_del_mondo(cartella, seme, giorni):
    return Path(cartella) / f"mondo_{seme}_{giorni}.pickle"


def file_della_partenza(cartella, seme, giorni, club):
    return Path(cartella) / f"partenza_{seme}_{giorni}_{club}.pickle"


def seme_del_gruppo(seme, giorni, club):
    """Il caso di tutte le corse di un mondo e di un club: lo stesso per tutte le strategie."""
    return seme * 1009 + giorni * 7 + CLUB[club][1]


# I mondi e le partenze.

def fai_nascere(seme, giorni_dei_mondi, cartella):
    """Il mondo del seme, nato col codice di oggi e salvato a ciascuna delle età date; restituisce il seme e i secondi."""
    inizio = time.perf_counter()
    tappe = set(giorni_dei_mondi)
    with cartelle_temporanee():
        def ogni_giorno(mondo, giorno, _rapporto):
            if giorno in tappe:
                salva(mondo, file_del_mondo(cartella, seme, giorno))
            if giorno % 365 == 0:
                archivio.congela_la_memoria()

        ms.mondo_nato(seme, max(giorni_dei_mondi), ogni_giorno)
    return seme, time.perf_counter() - inizio


def tieni_la_gloria(mondo, poli, bersaglio, chiave):
    """
    Tiene la gloria della polisportiva al bersaglio col palmarès finto del mese chiave, fuori dai mesi in cui si
    vince: toglie le medaglie e le coppe vere della finestra, e aggiunge le coppe che portano al bersaglio la rosa di
    adesso. Una rosa che da sola, senza palmarès, sta già sopra il bersaglio resta alla sua gloria.
    """
    oggi = mondo.datetime_corrente_simulazione
    morti = mondo._ids_morti_processati_sessione
    poli.palmares_recente[chiave] = [0.0, 0.0]
    medaglie, coppe = palmares.somma_finestra(poli, oggi)
    poli.palmares_recente[chiave] = [-medaglie, -coppe]
    poli.aggiorna_gloria(mondo.giocatori, morti, oggi)
    senza = poli.gloria
    if senza >= bersaglio:
        return
    # La gloria si tronca all'intero, e la rosa ha la sua parte decimale: le coppe portano la gloria a metà del passo, e
    # se la parte decimale lo fa scavalcare, sempre più vicino al bersaglio.
    for scarto in (0.5, 0.05, 0.0001):
        poli.palmares_recente[chiave] = [-medaglie, ((bersaglio - senza + scarto) / K_GLORIA_COPPE) ** 2 - coppe]
        poli.aggiorna_gloria(mondo.giocatori, morti, oggi)
        if poli.gloria == bersaglio:
            return


def tetto(g):
    """
    Il prezzo più alto che il computer pagava per un tesserato col contratto lontano dalla scadenza, prima della rampa: il
    valore pieno col rialzo. Sceglie i liberi della partenza e del tieni, come nella misura della settima tranche.
    """
    return int(economia.valore_di_mercato_pieno(g) * RIALZO_CPU)


def ricorda_la_firma(g, poli):
    """
    L'ingaggio che il giocatore chiede oggi alla polisportiva, scritto sul giocatore insieme al giorno della firma,
    ingaggio_della_firma, e restituito. Si chiama il giorno della firma, quando l'ingaggio chiesto è quello pagato, e
    per i quindici della partenza all'inizio della corsa: è il costo di ognuno, da cui partono il margine e la rosa pari
    con tutte e due le partenze, e la rampa con la partenza firma. Il gioco non lo salva: lo scrive lo strumento, e non
    finisce nei pickle, perché le corse non salvano il mondo.
    """
    ingaggio = economia.ingaggio_richiesto(g, poli)
    g.ingaggio_della_firma = (g.tesserato_dal, ingaggio)
    return ingaggio


def ingaggio_della_firma(g, poli):
    """
    L'ingaggio della firma che ricorda_la_firma ha scritto sul giocatore, se il giorno è quello della sua firma di oggi;
    senza, l'ingaggio che chiede oggi, come nel gioco, e la volta si conta in SENZA_FIRMA.
    """
    firma = getattr(g, "ingaggio_della_firma", None)
    if firma is not None and firma[0] == g.tesserato_dal:
        return firma[1]
    SENZA_FIRMA["volte"] += 1
    return economia.ingaggio_richiesto(g, poli)


def rampa_dalla_firma(g, poli, oggi, pieno):
    """
    economia._rampa con la partenza all'ingaggio della firma, per --partenza-della-rampa firma: la stessa regola del
    gioco, con la durata economia.MESI_DELLA_RAMPA del processo, ma la rampa parte dall'ingaggio che il giocatore ha
    pagato il giorno della firma, e non da quello che chiede oggi. Se la partenza non sta sotto il tetto pieno di oggi
    vale il tetto pieno, e così dal giorno del tetto pieno in poi.
    """
    if poli.is_cpu_controlled or g.tesserato_dal is None:
        return None
    partenza = ingaggio_della_firma(g, poli)
    if partenza >= pieno:
        return None
    fine = contratti.stesso_giorno_dopo(g.tesserato_dal, economia.MESI_DELLA_RAMPA)
    giorni = (fine.date() - g.tesserato_dal.date()).days
    passati = max(0, (oggi.date() - g.tesserato_dal.date()).days)
    if passati >= giorni:
        return None
    return partenza, passati, giorni, fine


def imposta_la_rampa(mesi, partenza="vendita"):
    """
    La durata della rampa del prezzo in questo processo, in mesi, per --mesi-della-rampa, e la sua partenza, per
    --partenza-della-rampa. economia importa MESI_DELLA_RAMPA dalle costanti col suo nome, e la rampa di
    tetto_di_rivendita lo legge da lì a ogni chiamata: basta cambiare quel nome, che vale per Mondo._vendibili, per
    metti_in_vendita_alla_rampa e per tetto_atteso. Cambiare costanti.MESI_DELLA_RAMPA non servirebbe, perché economia
    ha già il suo. Allo stesso modo tetto_di_rivendita chiama economia._rampa, che con la partenza firma diventa
    rampa_dalla_firma, e con la partenza vendita torna la rampa del gioco; Mondo._vendibili importa tetto_di_rivendita
    col suo nome, ma la funzione cerca _rampa in economia. Vale soltanto nel processo che la chiama: main la chiama per
    sé e la passa ai figli come inizializzatore, con esecutore.
    """
    economia.MESI_DELLA_RAMPA = mesi
    economia._rampa = rampa_dalla_firma if partenza == "firma" else RAMPA_DEL_GIOCO


def partenza_vista():
    """La partenza della rampa in questo processo, come la vede tetto_di_rivendita: firma o vendita."""
    return "firma" if economia._rampa is rampa_dalla_firma else "vendita"


def esecutore(processi, mesi_della_rampa, partenza="vendita"):
    """I processi figli della corsa, al più tanti insieme, ognuno con la rampa di tanti mesi e con la partenza data."""
    return ProcessPoolExecutor(max_workers=max(1, processi), initializer=imposta_la_rampa, initargs=(mesi_della_rampa, partenza))


def tetto_atteso(g, poli, oggi, giorni):
    """
    Il tetto della rampa, economia.tetto_di_rivendita, tanti giorni dopo una firma di oggi, coi valori di oggi: l'ingaggio
    che il giocatore chiede alla polisportiva, poi in linea retta fino al tetto pieno, lo stesso giorno del mese
    economia.MESI_DELLA_RAMPA mesi dopo, la rampa del processo, e da lì il tetto pieno. Chi chiede un ingaggio che non
    sta sotto il tetto pieno vale subito il tetto pieno, come nel gioco. Vale per tutte e due le partenze della rampa,
    perché il giorno della firma l'ingaggio chiesto oggi e quello della firma sono lo stesso.
    """
    pieno = economia.tetto_pieno_di_rivendita(g, poli, oggi)
    partenza = economia.ingaggio_richiesto(g, poli)
    rampa = (contratti.stesso_giorno_dopo(oggi, economia.MESI_DELLA_RAMPA).date() - oggi.date()).days
    if partenza >= pieno or giorni >= rampa:
        return pieno
    return partenza + (pieno - partenza) * max(0, giorni) // rampa


def compratori(mondo, oggi):
    """
    Per ogni polisportiva del computer quello che _compra_dal_mercato guarda: la cassa da spendere, lo stipendio
    che si permette e, a rosa piena, il valore del più debole.
    """
    righe = []
    for p in mondo.polisportive.values():
        if not p.is_cpu_controlled:
            continue
        rosa = mondo._rosa(p)
        piena = len(p.tesserati) >= p.maxtesserati
        if piena and not rosa:
            continue
        debole = min(rosa, key=lambda g: g.indice_collettivo_valore) if piena else None
        monte = mondo.monte_stipendi(p) - (economia.stipendio_pagato(debole) if debole else 0)
        buonuscita = contratti.buonuscita(debole, oggi) if debole else 0
        spendibile = p.cassa - monte * MESI_DI_RISERVA_CPU - buonuscita
        massimo = economia.spesa_mensile_cpu(mondo.sponsor(p), p.cassa) - monte
        righe.append((spendibile, massimo, debole.indice_collettivo_valore if debole else None))
    return righe


def vendibile(g, prezzo, righe):
    """Vero se oggi almeno una polisportiva del computer comprerebbe il giocatore a quel prezzo."""
    chiesto = economia.stipendio(g)
    valore = g.indice_collettivo_valore
    return any(spendibile >= prezzo and massimo >= chiesto and (soglia is None or valore > soglia) for spendibile, massimo, soglia in righe)


def ciclo_stimato(g, oggi, mesi):
    """
    I giorni dalla firma di oggi alla vendita al computer, stimati: tanti mesi dopo la firma il commerciante lo mette in
    vendita, e il computer lo compra il giorno dopo; se il contratto è allora negli ultimi tre mesi, il commerciante
    aspetta la scadenza, quando il rinnovo prende il suo posto e il valore torna pieno. Un contratto che finisce prima
    si rinnova per la stessa durata.
    """
    durata = contratti.durata_proposta(g)
    scadenza = contratti.scadenza_dopo(oggi, durata)
    dal = contratti.stesso_giorno_dopo(oggi, mesi)
    while dal >= scadenza:
        scadenza = contratti.aggiungi_mesi(scadenza, durata)
    if contratti.mesi_di_calendario(dal, scadenza) < MESI_VALORE_PIENO:
        dal = scadenza
    return max(1, (dal - oggi).days + 1)


def candidati(mondo, poli, mesi):
    """
    I liberi da tesserare, dal migliore, ciascuno col prezzo a cui il computer lo comprerà: fino a 30 anni, che possono
    giocare e rendono, cioè col tetto pieno sopra l'ingaggio chiesto. Senza mesi in ordine di guadagno, col tetto pieno
    di prima della rampa; coi mesi della rivendita in ordine di guadagno per giorno del ciclo, il tetto della rampa il
    giorno in cui va in vendita meno l'ingaggio, e soltanto chi non entra nel declino prima della vendita.
    """
    oggi = mondo.datetime_corrente_simulazione
    morti = mondo._ids_morti_processati_sessione
    righe = []
    for gid, g in mondo.giocatori.items():
        if g.appartenenza != "*" or g.ritirato or gid in morti or not g.puo_giocare or g.eta_anni > ETA_MASSIMA:
            continue
        ingaggio = economia.ingaggio_richiesto(g, poli)
        guadagno = tetto(g) - ingaggio
        if guadagno <= 0:
            continue
        if mesi is None:
            righe.append((guadagno, guadagno, gid, g, tetto(g)))
            continue
        giorni = ciclo_stimato(g, oggi, mesi)
        if g.eta + giorni < tratti.giorni_inizio_declino(g):
            # Il prezzo si mette il giorno prima di quello in cui il computer compra.
            prezzo = tetto_atteso(g, poli, oggi, giorni - 1)
            righe.append(((prezzo - ingaggio) / giorni, guadagno, gid, g, prezzo))
    # A pari resa vale il guadagno a tetto pieno, come nella partenza: nella vendita a 0 mesi il prezzo è l'ingaggio, la
    # resa è zero per tutti, e senza questo il commerciante sceglierebbe a caso, e chiuderebbe con una rosa più povera.
    righe.sort(key=lambda riga: (-riga[0], -riga[1], riga[2]))
    return [(g, prezzo) for _resa, _guadagno, _gid, g, prezzo in righe]


def riempi(mondo, poli, mesi, conti):
    """Riempie i posti vuoti coi candidati che il computer comprerebbe, offrendo l'ingaggio chiesto finché accettano o finiscono le mosse."""
    if len(poli.tesserati) >= poli.maxtesserati or mondo.mosse_rimaste(poli) <= 0:
        return
    righe = None
    for g, prezzo in candidati(mondo, poli, mesi):
        if len(poli.tesserati) >= poli.maxtesserati or mondo.mosse_rimaste(poli) <= 0:
            return
        if righe is None:
            righe = compratori(mondo, mondo.datetime_corrente_simulazione)
        if not vendibile(g, prezzo, righe):
            continue
        while mondo.mosse_rimaste(poli) > 0:
            try:
                accetta, _probabilita = mondo.offerta(poli, g)
            except ValueError:
                break
            if accetta:
                conti["firme"] += 1
                break
            conti["rifiuti"] += 1


def allena_tutti(mondo, poli):
    """Allena tutti: ognuno spende i suoi punti secondo il programma."""
    oggi = mondo.datetime_corrente_simulazione
    for g in mondo._rosa(poli):
        if allenamento.puo_allenarsi(g) and g.punti_allenamento >= 1.0:
            allenamento.allena_secondo_programma(g, data=oggi)


def rinnova_tutti(mondo, poli, conti):
    """Propone il rinnovo a chi è nella finestra, alla richiesta e alla durata proposta, una volta al giorno."""
    for g in mondo._rosa(poli):
        if mondo.problema_rinnovo(poli, g) is not None:
            continue
        mesi = contratti.durata_proposta(g)
        richiesta = contratti.richiesta_rinnovo(g, poli, mesi)
        accetta, _probabilita, _richiesta = mondo.rinnova(poli, g, max(STIPENDIO_MINIMO, richiesta), mesi)
        conti["rinnovi" if accetta else "rinnovi_rifiutati"] += 1


def in_vendita_dal(g, mesi):
    """Il giorno dal quale il commerciante mette in vendita il tesserato: lo stesso giorno del mese tanti mesi dopo la firma."""
    return contratti.stesso_giorno_dopo(g.tesserato_dal, mesi).date()


def aspetta_il_rinnovo(g, oggi):
    """
    Vero negli ultimi tre mesi di contratto con un rinnovo concordato: il tetto scende col valore, che nelle vendite
    dell'utente non conta il rinnovo, e torna pieno quando il rinnovo prende il posto del contratto.
    """
    return contratti.ha_rinnovo(g) and economia.fattore_scadenza(g, oggi, col_rinnovo=False) < 1.0


def metti_in_vendita_alla_rampa(mondo, poli, mesi):
    """
    Da tanti mesi dopo la firma ogni tesserato sta in vendita al tetto della rampa di oggi, e il prezzo si rifà ogni
    volta che il tetto cambia; chi è convocato aspetta. Chi aspetta il rinnovo esce dalla vendita, e chi non ha un
    rinnovo concordato resta in vendita anche quando il tetto scende con la scadenza.
    """
    oggi = mondo.datetime_corrente_simulazione
    for g in mondo._rosa(poli):
        if g.tesserato_dal is None or oggi.date() < in_vendita_dal(g, mesi):
            continue
        if aspetta_il_rinnovo(g, oggi):
            if g.id in poli.in_vendita:
                mondo.togli_dalla_vendita(poli, g)
            continue
        prezzo = economia.tetto_di_rivendita(g, poli, oggi)
        if poli.in_vendita.get(g.id) != prezzo:
            with suppress(ValueError):
                mondo.metti_in_vendita(poli, g, prezzo)


def a_regime(mondo, poli, g, giorni):
    """
    Il tesserato della partenza come se avesse firmato tanti giorni prima di oggi, in un commercio che va avanti da
    sempre: la firma si sposta indietro, e con lei il contratto, della stessa durata e allo stesso stipendio, rinnovato
    per la stessa durata finché scadrebbe prima di oggi; la fedeltà cresce dei primi del mese passati in più.
    """
    oggi = mondo.datetime_corrente_simulazione
    prima = g.tesserato_dal
    firma = oggi - datetime.timedelta(days=giorni)
    durata = contratti.mesi_interi(contratti.inizio(prima), g.contratto_scadenza)
    scadenza = contratti.scadenza_dopo(firma, durata)
    while scadenza.date() <= oggi.date():
        scadenza = contratti.aggiungi_mesi(scadenza, durata)
    g.tesserato_dal = firma
    g.contratto_scadenza = scadenza
    mesi = contratti.mesi_interi(firma, oggi) - contratti.mesi_interi(prima, oggi)
    if mesi > 0:
        mondo._aggiungi_fedelta(g, poli, FEDELTA_PER_MESE * mesi, oggi)


def prepara_la_partenza(seme, giorni, club, cartella, bersaglio):
    """
    La partenza comune di un mondo e di un club: la polisportiva fondata con la cassa piena e la gloria al
    bersaglio, riempita coi liberi che rendono di più. Salva il mondo e restituisce i dati della partenza.
    """
    inizio = time.perf_counter()
    with cartelle_temporanee():
        mondo = carica(file_del_mondo(cartella, seme, giorni))
        random.seed(seme_del_gruppo(seme, giorni, club) + 1)
        glorie = sorted(p.gloria for p in mondo.polisportive.values() if p.is_cpu_controlled)
        poli = mondo.fonda_polisportiva(CLUB[club][0], luogo="Bologna")
        poli.cassa = CASSA_DI_PARTENZA
        oggi = mondo.datetime_corrente_simulazione
        chiave = palmares.mese(contratti.aggiungi_mesi(oggi, -1))
        conti = {"firme": 0, "rifiuti": 0}
        giorni_usati = 0
        while True:
            tieni_la_gloria(mondo, poli, bersaglio, chiave)
            riempi(mondo, poli, None, conti)
            if len(poli.tesserati) >= poli.maxtesserati or giorni_usati >= GIORNI_DI_RIEMPIMENTO:
                break
            ms.avanza_un_giorno(mondo)
            giorni_usati += 1
        tieni_la_gloria(mondo, poli, bersaglio, chiave)
        poli.conti_del_mese = conti_vuoti()
        rosa = mondo._rosa(poli)
        dati = {"seme": seme, "giorni": giorni, "club": club, "bersaglio": bersaglio, "gloria": poli.gloria, "chiave": chiave,
                "giorni_di_riempimento": giorni_usati, "tesserati": len(rosa), "firme": conti["firme"], "rifiuti": conti["rifiuti"],
                "polisportive_del_computer": len(glorie), "gloria_del_computer": (glorie[0], int(statistics.median(glorie)), glorie[-1]) if glorie else None,
                "stipendio_medio": statistics.fmean(economia.stipendio_pagato(g) for g in rosa) if rosa else 0.0,
                "tetto_medio": statistics.fmean(tetto(g) for g in rosa) if rosa else 0.0,
                "reputazione_media": statistics.fmean(economia.fattore_reputazione(g, poli) for g in rosa) if rosa else 0.0,
                "giocatori": len(mondo.giocatori), "data": oggi.date().isoformat()}
        salva({"mondo": mondo, "nome": poli.nome, "dati": dati}, file_della_partenza(cartella, seme, giorni, club))
    dati["secondi"] = time.perf_counter() - inizio
    return dati


# Le corse.

def scade_entro(g, data):
    """Vero se il contratto del giocatore finisce entro quella data senza un rinnovo concordato."""
    return g.contratto_scadenza is not None and g.contratto_scadenza.date() <= data.date() and not contratti.ha_rinnovo(g)


def corsa(seme, giorni, club, strategia, mesi, durata, cartella):
    """
    Una strategia per tanti mesi di calendario, dalla partenza comune: rivendi, coi mesi di firma dopo i quali il
    commerciante mette in vendita, o tieni. Restituisce le voci dei conti sommate, il saldo e i conteggi di firme,
    vendite, uscite e rinnovi. Fino alla settima tranche i mesi prendevano il posto della costante dell'attesa; dalla
    rampa del prezzo, scelta da Gabriele il 3 novembre 2026, la rampa è quella del processo, imposta_la_rampa, e i mesi
    sono la scelta del commerciante; il risultato dice anche la durata della rampa che la corsa ha visto, e da dove
    parte, partenza_vista. Nella rivendita i quindici della partenza vanno a regime con a_regime. Per ogni vendita conta
    il margine, il prezzo meno l'ingaggio della firma, il margine pieno, il tetto pieno del giorno prima della vendita
    meno l'ingaggio della firma, e la crescita dell'ingaggio, quello chiesto il giorno prima della vendita meno quello
    della firma; ingaggi_alla_firma somma gli ingaggi ricordati di chi firma nella corsa, e deve fare la voce ingaggi.
    """
    inizio = time.perf_counter()
    SENZA_FIRMA["volte"] = 0
    with cartelle_temporanee():
        partenza = carica(file_della_partenza(cartella, seme, giorni, club))
        mondo, dati = partenza["mondo"], partenza["dati"]
        poli = mondo.polisportive[partenza["nome"]]
        bersaglio, chiave = dati["bersaglio"], dati["chiave"]
        rivendi = strategia == "rivendi"
        random.seed(seme_del_gruppo(seme, giorni, club))
        oggi = mondo.datetime_corrente_simulazione
        fine = contratti.stesso_giorno_dopo(oggi, durata)
        # Il giorno della corsa in cui ognuno ha firmato: per i quindici della partenza a regime, prima dell'inizio.
        firmato = dict.fromkeys(poli.tesserati, 0)
        if rivendi and mesi:
            # La partenza a regime: le firme dei quindici sparse a passi regolari negli ultimi t mesi, coi contratti.
            tesserati = sorted(poli.tesserati)
            for i, gid in enumerate(tesserati):
                spostamento = round(mesi * GIORNI_PER_MESE * (i + 0.5) / len(tesserati))
                a_regime(mondo, poli, mondo.giocatori[gid], spostamento)
                firmato[gid] = -spostamento
        # L'ingaggio della firma di ognuno, ricordato sul giocatore: il margine di una vendita è il prezzo meno questo, e
        # con la partenza firma la rampa parte da qui.
        pagato = {gid: ricorda_la_firma(mondo.giocatori[gid], poli) for gid in poli.tesserati}
        rosa_iniziale = sum(pagato.values())
        cassa_iniziale = poli.cassa
        totali = dict.fromkeys(VOCI_CONTI, 0)
        conti = {"firme": 0, "rifiuti": 0, "rinnovi": 0, "rinnovi_rifiutati": 0, "vendite": 0, "usciti": 0, "giorni_tenuti": 0, "margini": 0,
                 "sotto_l_ingaggio": 0, "margini_pieni": 0, "crescita_degli_ingaggi": 0, "ingaggi_alla_firma": 0}
        glorie, posti_giorno, giorno = [], 0, 0
        while mondo.datetime_corrente_simulazione < fine:
            tieni_la_gloria(mondo, poli, bersaglio, chiave)
            allena_tutti(mondo, poli)
            rinnova_tutti(mondo, poli, conti)
            riempi(mondo, poli, mesi if rivendi else None, conti)
            for gid in poli.tesserati:
                if gid not in firmato:
                    firmato[gid] = giorno
                    pagato[gid] = ricorda_la_firma(mondo.giocatori[gid], poli)
                    conti["ingaggi_alla_firma"] += pagato[gid]
            if rivendi:
                metti_in_vendita_alla_rampa(mondo, poli, mesi)
            tieni_la_gloria(mondo, poli, bersaglio, chiave)
            posti_giorno += len(poli.tesserati)
            # La gloria che lo sponsor paga domani, se domani è il primo del mese: i conti la leggono prima delle mosse del computer.
            domani = mondo.datetime_corrente_simulazione + datetime.timedelta(days=1)
            if domani.day == 1:
                glorie.append(poli.gloria)
            # Chi domani esce dalla rosa ed entra in una del computer è venduto se era in vendita, ma non se il contratto
            # gli scade domani senza rinnovo: torna libero, e il computer può tesserarlo lo stesso giorno.
            vendibili = {gid: prezzo for gid, prezzo in poli.in_vendita.items() if not scade_entro(mondo.giocatori[gid], domani)}
            # Il tetto pieno di domani e l'ingaggio chiesto oggi, coi valori di oggi, per il margine pieno e la crescita.
            pieni = {gid: (economia.tetto_pieno_di_rivendita(mondo.giocatori[gid], poli, domani), economia.ingaggio_richiesto(mondo.giocatori[gid], poli))
                     for gid in vendibili}
            prima = set(poli.tesserati)
            ms.avanza_un_giorno(mondo)
            giorno += 1
            for gid in sorted(prima - set(poli.tesserati)):
                g = mondo.giocatori.get(gid)
                quando, spesa = firmato.pop(gid, 0), pagato.pop(gid, 0)
                if g is not None and gid in vendibili and g.appartenenza not in ("*", poli.nome):
                    conti["vendite"] += 1
                    conti["giorni_tenuti"] += giorno - quando
                    conti["margini"] += vendibili[gid] - spesa
                    conti["sotto_l_ingaggio"] += vendibili[gid] < spesa
                    conti["margini_pieni"] += pieni[gid][0] - spesa
                    conti["crescita_degli_ingaggi"] += pieni[gid][1] - spesa
                else:
                    conti["usciti"] += 1
            if mondo.datetime_corrente_simulazione.day == 1:
                bilancio = poli.bilanci[0]
                for voce in VOCI_CONTI:
                    totali[voce] += bilancio[voce]
        for voce in VOCI_CONTI:
            totali[voce] += poli.conti_del_mese[voce]
        saldo = poli.cassa - cassa_iniziale
        somma = sum(totali[voce] if voce in ENTRATE else -totali[voce] for voce in VOCI_CONTI)
        rosa = mondo._rosa(poli)
        return {"seme": seme, "giorni": giorni, "club": club, "strategia": strategia, "mesi": mesi, "durata": durata,
                "mesi_della_rampa": economia.MESI_DELLA_RAMPA, "partenza_della_rampa": partenza_vista(), "rampe_senza_firma": SENZA_FIRMA["volte"],
                "giorni_corsi": giorno,
                "saldo": saldo, "somma_delle_voci": somma, "voci": totali, **conti, "posti_giorno": posti_giorno,
                "gloria_minima": min(glorie) if glorie else poli.gloria, "gloria_massima": max(glorie) if glorie else poli.gloria,
                "tesserati_alla_fine": len(rosa), "valore_alla_fine": sum(economia.valore_di_mercato_pieno(g) for g in rosa),
                "ingaggi_rosa_iniziale": rosa_iniziale, "ingaggi_rosa_finale": sum(pagato.get(gid, 0) for gid in poli.tesserati),
                "secondi": time.perf_counter() - inizio}


# Il conto e la tabella.

def per_posto_e_anno(cifra, durata):
    """Una cifra della corsa divisa per i posti della rosa e per gli anni della durata."""
    return cifra / MAX_TESSERATI_POLISPORTIVA / (durata / 12)


def euro(cifra):
    """Una cifra intera, col punto delle migliaia e il meno davanti."""
    return f"{round(cifra):,}".replace(",", ".")


def decimale(numero, cifre=1):
    """Un numero con la virgola dei decimali."""
    return f"{numero:.{cifre}f}".replace(".", ",")


def a_rosa_pari(r):
    """
    Il saldo della corsa con la rosa contata al suo costo, l'ingaggio della firma di ognuno, da cui parte la rampa il
    giorno della firma, e con la partenza firma per tutta la rampa: più la rosa della fine, meno quella della partenza. Toglie l'effetto di una rosa che alla fine non è quella della partenza, come nella
    vendita a 0 mesi, dove il computer compra più in fretta di quanto il commerciante tesseri e la rosa si svuota: i
    quindici della partenza non sono costati niente nella corsa, quelli della fine sì.
    """
    return r["saldo"] + r["ingaggi_rosa_finale"] - r["ingaggi_rosa_iniziale"]


def differenze(risultati, durata):
    """
    Per mondo, club e mesi, la differenza fra la rivendita e il tieni di ogni seme, per posto e per anno, anche a rosa
    pari, e le voci.
    """
    tieni = {(r["seme"], r["giorni"], r["club"]): r for r in risultati if r["strategia"] == "tieni"}
    gruppi = {}
    for r in risultati:
        if r["strategia"] != "rivendi":
            continue
        t = tieni.get((r["seme"], r["giorni"], r["club"]))
        if t is None:
            continue
        voci = {voce: per_posto_e_anno(r["voci"][voce] - t["voci"][voce], durata) for voce in VOCI_CONTI}
        gruppi.setdefault((r["giorni"], r["club"], r["mesi"]), []).append({
            "seme": r["seme"], "differenza": per_posto_e_anno(r["saldo"] - t["saldo"], durata), "voci": voci,
            "a_rosa_pari": per_posto_e_anno(a_rosa_pari(r) - a_rosa_pari(t), durata),
            "vendite_per_posto_e_anno": r["vendite"] / MAX_TESSERATI_POLISPORTIVA / (durata / 12),
            "giorni_tenuti": r["giorni_tenuti"] / r["vendite"] if r["vendite"] else None,
            "prezzo_medio": r["voci"]["vendite"] / r["vendite"] if r["vendite"] else None,
            "margine_medio": r["margini"] / r["vendite"] if r["vendite"] else None, "sotto_l_ingaggio": r["sotto_l_ingaggio"],
            "ingaggio_medio": r["voci"]["ingaggi"] / r["firme"] if r["firme"] else None,
            "rosa_media": r["posti_giorno"] / max(1, r["giorni_corsi"]), "rosa_media_tieni": t["posti_giorno"] / max(1, t["giorni_corsi"]),
            "valore_alla_fine": r["valore_alla_fine"], "valore_alla_fine_tieni": t["valore_alla_fine"],
            # Lo sponsor si paga il primo del mese, e una corsa di tanti mesi ne ha tanti primi.
            "sponsor_al_mese_tieni": t["voci"]["sponsor"] / durata,
            "gloria": (min(r["gloria_minima"], t["gloria_minima"]), max(r["gloria_massima"], t["gloria_massima"]))})
    return gruppi


def riassunto(righe, chiave="differenza"):
    """Media e scarto quadratico fra i semi della differenza, o di quella a rosa pari; lo scarto è zero con un seme solo."""
    valori = [r[chiave] for r in righe]
    media = statistics.fmean(valori)
    scarto = statistics.stdev(valori) if len(valori) > 1 else 0.0
    return media, scarto


def tabella(gruppi, partenze, durata):
    """Le righe della tabella: per mondo e club la partenza, poi una riga per i mesi di firma della vendita."""
    righe = []
    for giorni in sorted({g for g, _c, _m in gruppi}):
        for club in ("gloriosa", "media"):
            dati = [p for p in partenze if p["giorni"] == giorni and p["club"] == club]
            if dati:
                bersagli = sorted({p["bersaglio"] for p in dati})
                reputazione = statistics.fmean(p["reputazione_media"] for p in dati)
                righe.append(f"Mondo di {giorni} giorni, polisportiva {club}, gloria {', '.join(map(str, bersagli))}; alla partenza l'ingaggio "
                             f"chiesto vale in media {decimale(reputazione * MESI_DI_INGAGGIO, 2)} stipendi, lo stipendio medio "
                             f"{euro(statistics.fmean(p['stipendio_medio'] for p in dati))} euro e il tetto del computer "
                             f"{euro(statistics.fmean(p['tetto_medio'] for p in dati))} euro.")
            for mesi in sorted({m for g, c, m in gruppi if g == giorni and c == club}):
                gruppo = sorted(gruppi[(giorni, club, mesi)], key=lambda r: r["seme"])
                media, scarto = riassunto(gruppo)
                pari, scarto_pari = riassunto(gruppo, "a_rosa_pari")
                semi = ", ".join(euro(r["differenza"]) for r in gruppo)
                voci = {voce: statistics.fmean(r["voci"][voce] for r in gruppo) for voce in VOCI_CONTI}
                resto = sum(v if voce in ENTRATE else -v for voce, v in voci.items() if voce not in VOCI_DETTE)
                dette = "; ".join(f"{voce} {euro(voci[voce] if voce in ENTRATE else -voci[voce])}" for voce in VOCI_DETTE)
                vendite = statistics.fmean(r["vendite_per_posto_e_anno"] for r in gruppo)
                tenuti = [r["giorni_tenuti"] for r in gruppo if r["giorni_tenuti"] is not None]
                testo = (f"Vendita a {testi.conta(mesi, 'mese', 'mesi')} dalla firma: differenza {euro(media)} euro per posto e per anno, "
                         f"scarto fra i semi {euro(scarto)}; semi {semi}; a rosa pari {euro(pari)}, scarto {euro(scarto_pari)}. "
                         f"Voci, rivendita meno tieni, per posto e per anno: {dette}; tornei e resto {euro(resto)}.")
                if tenuti:
                    prezzi = [r["prezzo_medio"] for r in gruppo if r["prezzo_medio"] is not None]
                    margini = [r["margine_medio"] for r in gruppo if r["margine_medio"] is not None]
                    sotto = sum(r["sotto_l_ingaggio"] for r in gruppo)
                    testo += (f" Vendite per posto e per anno {decimale(vendite, 2)}, giorni dalla firma alla vendita {euro(statistics.fmean(tenuti))}, "
                              f"prezzo medio di una vendita {euro(statistics.fmean(prezzi))} euro, margine medio sull'ingaggio "
                              f"{euro(statistics.fmean(margini))} euro, vendite sotto l'ingaggio {sotto}.")
                else:
                    testo += " Nessuna vendita."
                testo += (f" Tesserati in media {decimale(statistics.fmean(r['rosa_media'] for r in gruppo))}, nel tieni "
                          f"{decimale(statistics.fmean(r['rosa_media_tieni'] for r in gruppo))}.")
                righe.append(testo)
    return righe


def piu_redditizio(gruppi, chiave="differenza"):
    """
    Per mondo e club i mesi di firma della vendita che rendono di più al commerciante, con la media e lo scarto fra i
    semi della differenza, o di quella a rosa pari.
    """
    esito = {}
    for giorni, club in sorted({(g, c) for g, c, _m in gruppi}):
        provati = [(mesi, *riassunto(gruppi[(giorni, club, mesi)], chiave)) for mesi in sorted(m for g, c, m in gruppi if g == giorni and c == club)]
        esito[(giorni, club)] = max(provati, key=lambda riga: riga[1])
    return esito


def residuo(gruppi, chiave="differenza"):
    """
    Le righe del residuo: per mondo e club quanto rende la vendita ai mesi più redditizi, per posto e per anno, con la
    rosa intera all'anno e al mese, e in percentuale dello sponsor della rosa onesta; e se la media sta entro lo scarto.
    Con la chiave a_rosa_pari, la differenza a rosa pari.
    """
    righe = []
    for (giorni, club), (mesi, media, scarto) in piu_redditizio(gruppi, chiave).items():
        sponsor = statistics.fmean(r["sponsor_al_mese_tieni"] for r in gruppi[(giorni, club, mesi)])
        al_mese = media * MAX_TESSERATI_POLISPORTIVA / 12
        percentuale = testi.con_articolo("il", f"{round(100 * al_mese / sponsor)}%") if sponsor > 0 else ""
        quota = f", {percentuale} dello sponsor della rosa onesta, {euro(sponsor)} euro al mese" if sponsor > 0 else ""
        pari = " a rosa pari" if chiave == "a_rosa_pari" else ""
        testo = (f"Mondo di {giorni} giorni, polisportiva {club}{pari}: rende di più la vendita a {testi.conta(mesi, 'mese', 'mesi')} dalla firma, "
                 f"{euro(media)} euro per posto e per anno, scarto fra i semi {euro(scarto)}; con la rosa intera "
                 f"{euro(media * MAX_TESSERATI_POLISPORTIVA)} euro all'anno, {euro(al_mese)} al mese{quota}.")
        if abs(media) <= scarto:
            testo += " La media sta entro lo scarto fra i semi."
        righe.append(testo)
    return righe


def in_parallelo(esecutore, compiti, racconta):
    """Lancia i compiti, coppie di funzione e argomenti, e ne raccoglie i risultati man mano che finiscono."""
    futuri = [esecutore.submit(funzione, *argomenti) for funzione, argomenti in compiti]
    risultati = []
    for futuro in as_completed(futuri):
        risultato = futuro.result()
        risultati.append(risultato)
        racconta(risultato)
    return risultati


def argomenti(argv=None):
    """Gli argomenti della riga di comando, o quelli dati; una rampa di meno di zero mesi è un errore."""
    parser = argparse.ArgumentParser(description="Misura quanto rende ancora la rivendita al computer di un tesserato dell'utente, con la rampa del prezzo.")
    parser.add_argument("--semi", type=int, nargs="+", default=list(SEMI))
    parser.add_argument("--giorni-dei-mondi", type=int, nargs="+", default=list(GIORNI_DEI_MONDI))
    parser.add_argument("--mesi", type=int, nargs="+", default=list(MESI_PROVATI), help="i mesi di firma dopo i quali il commerciante mette in vendita")
    parser.add_argument("--durata", type=int, default=DURATA_MESI, help="mesi di calendario di ogni corsa")
    parser.add_argument("--mesi-della-rampa", type=int, default=MESI_DELLA_RAMPA,
                        help=f"i mesi dalla firma al tetto pieno, in tutti i processi della corsa; di serie {MESI_DELLA_RAMPA}, quelli del gioco")
    parser.add_argument("--partenza-della-rampa", choices=PARTENZE_DELLA_RAMPA, default=PARTENZE_DELLA_RAMPA[0],
                        help="da dove parte la rampa del tetto, in tutti i processi della corsa: vendita, l'ingaggio chiesto il giorno "
                             "della vendita, come nel gioco, di serie; firma, l'ingaggio pagato il giorno della firma")
    parser.add_argument("--processi", type=int, default=PROCESSI)
    parser.add_argument("--gloria", type=int, default=GLORIA_GLORIOSA, help="la gloria della polisportiva gloriosa")
    parser.add_argument("--gloria-media", type=int, default=GLORIA_MEDIA, help="la gloria della polisportiva media")
    parser.add_argument("--club", nargs="+", choices=tuple(CLUB), default=list(CLUB))
    parser.add_argument("--cartella", type=Path, help="dove tenere mondi e partenze; senza, una cartella temporanea che si cancella")
    parser.add_argument("--salva", type=Path, help="il file JSON dove scrivere tutti i risultati")
    args = parser.parse_args(argv)
    if args.mesi_della_rampa < 0:
        parser.error("--mesi-della-rampa vuole un numero di mesi da zero in su")
    return args


def main():
    args = argomenti()
    imposta_la_rampa(args.mesi_della_rampa, args.partenza_della_rampa)
    # Lo stesso ordine degli insiemi in tutti i processi, perché la stessa corsa dia gli stessi numeri.
    os.environ.setdefault("PYTHONHASHSEED", "0")
    temporanea = args.cartella is None
    cartella = Path(tempfile.mkdtemp(prefix="mess_rivendita_mondi_")) if temporanea else args.cartella
    cartella.mkdir(parents=True, exist_ok=True)
    inizio = time.perf_counter()

    def racconta(testo):
        print(f"{time.perf_counter() - inizio:7.0f} s. {testo}", flush=True)

    del_gioco = "quella del gioco" if args.mesi_della_rampa == MESI_DELLA_RAMPA else f"al posto dei {MESI_DELLA_RAMPA} del gioco"
    dalla = ("dall'ingaggio pagato il giorno della firma, al posto di quello chiesto il giorno della vendita"
             if args.partenza_della_rampa == "firma" else "dall'ingaggio chiesto il giorno della vendita, la partenza del gioco")
    racconta(f"Rampa del prezzo di {testi.conta(args.mesi_della_rampa, 'mese', 'mesi')}, {del_gioco}; parte {dalla}.")
    try:
        with cartelle_temporanee(), esecutore(args.processi, args.mesi_della_rampa, args.partenza_della_rampa) as figli:
            mancanti = [s for s in args.semi if not all(file_del_mondo(cartella, s, g).exists() for g in args.giorni_dei_mondi)]
            in_parallelo(figli, [(fai_nascere, (s, args.giorni_dei_mondi, cartella)) for s in mancanti],
                         lambda r: racconta(f"Nato il mondo del seme {r[0]}, in {r[1]:.0f} s."))
            gruppi = [(s, g, c) for g in sorted(args.giorni_dei_mondi, reverse=True) for s in args.semi for c in args.club]
            bersagli = {"gloriosa": args.gloria, "media": args.gloria_media}
            partenze = in_parallelo(figli, [(prepara_la_partenza, (s, g, c, cartella, bersagli[c])) for s, g, c in gruppi],
                                    lambda d: racconta(f"Partenza del seme {d['seme']}, mondo di {d['giorni']} giorni, {d['club']}: gloria {d['gloria']} "
                                                       f"su {d['bersaglio']}, {d['tesserati']} tesserati in {d['giorni_di_riempimento']} giorni, "
                                                       f"{d['firme']} firme e {d['rifiuti']} rifiuti, in {d['secondi']:.0f} s."))
            compiti = [(corsa, (s, g, c, "tieni", None, args.durata, cartella)) for s, g, c in gruppi]
            compiti += [(corsa, (s, g, c, "rivendi", m, args.durata, cartella)) for s, g, c in gruppi for m in args.mesi]
            # Prima le corse lunghe, nei mondi più vecchi e coi mesi più corti, che vendono di più.
            compiti.sort(key=lambda compito: (-compito[1][1], compito[1][4] if compito[1][4] is not None else -1))
            risultati = in_parallelo(figli, compiti, lambda r: racconta(
                f"Corsa {r['strategia']}{'' if r['mesi'] is None else ' a ' + testi.conta(r['mesi'], 'mese', 'mesi')}, seme {r['seme']}, mondo di {r['giorni']} giorni, "
                f"{r['club']}: saldo {euro(r['saldo'])} euro, vendite {r['vendite']}, firme {r['firme']}, in {r['secondi']:.0f} s."))
        sbagliate = [r for r in risultati if r["saldo"] != r["somma_delle_voci"]]
        for r in sbagliate:
            racconta(f"Attenzione: nella corsa {r['strategia']} {r['mesi']}, seme {r['seme']}, mondo di {r['giorni']}, {r['club']}, "
                     f"le voci fanno {euro(r['somma_delle_voci'])} e la cassa {euro(r['saldo'])}.")
        for r in risultati:
            if r["mesi_della_rampa"] != args.mesi_della_rampa:
                racconta(f"Attenzione: la corsa {r['strategia']} {r['mesi']}, seme {r['seme']}, mondo di {r['giorni']}, {r['club']}, "
                         f"ha visto una rampa di {r['mesi_della_rampa']} mesi.")
            if r["partenza_della_rampa"] != args.partenza_della_rampa:
                racconta(f"Attenzione: la corsa {r['strategia']} {r['mesi']}, seme {r['seme']}, mondo di {r['giorni']}, {r['club']}, "
                         f"ha visto la partenza {r['partenza_della_rampa']} al posto di {args.partenza_della_rampa}.")
            if r["rampe_senza_firma"]:
                racconta(f"Attenzione: nella corsa {r['strategia']} {r['mesi']}, seme {r['seme']}, mondo di {r['giorni']}, {r['club']}, "
                         f"la rampa non ha trovato l'ingaggio della firma {testi.conta(r['rampe_senza_firma'], 'volta', 'volte')}.")
            if r["ingaggi_alla_firma"] != r["voci"]["ingaggi"]:
                racconta(f"Attenzione: nella corsa {r['strategia']} {r['mesi']}, seme {r['seme']}, mondo di {r['giorni']}, {r['club']}, "
                         f"gli ingaggi ricordati fanno {euro(r['ingaggi_alla_firma'])} e quelli pagati {euro(r['voci']['ingaggi'])}.")
        conto = differenze(risultati, args.durata)
        for riga in tabella(conto, partenze, args.durata) + residuo(conto) + residuo(conto, "a_rosa_pari"):
            print(riga, flush=True)
        if args.salva:
            gruppi_json = [{"giorni": g, "club": c, "mesi": m, "semi": righe} for (g, c, m), righe in sorted(conto.items())]
            migliori = [{"giorni": g, "club": c, "chiave": chiave, "mesi": m, "media": media, "scarto": scarto}
                        for chiave in ("differenza", "a_rosa_pari") for (g, c), (m, media, scarto) in piu_redditizio(conto, chiave).items()]
            args.salva.write_text(json.dumps({"mesi_della_rampa": args.mesi_della_rampa, "partenza_della_rampa": args.partenza_della_rampa,
                                              "partenze": partenze, "corse": risultati,
                                              "differenze": gruppi_json, "piu_redditizio": migliori}, ensure_ascii=False, indent=1), encoding="utf-8")
        racconta("Fine.")
    finally:
        if temporanea:
            shutil.rmtree(cartella, ignore_errors=True)


if __name__ == "__main__":
    main()
