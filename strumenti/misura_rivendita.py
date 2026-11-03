"""
La misura della rivendita al computer della decisione D40: quanti mesi, MESI_PRIMA_DELLA_RIVENDITA, il computer
aspetta prima di comprare un tesserato dell'utente, perché il commercio dei liberi non renda più.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-11-03 con la settima tranche di D40, dagli script commercio.py e rimedi_commercio.py della verifica
dei trucchi del 2 novembre 2026, rifatti come chiede la critica alla decisione 6. Il trucco: tesserare un libero
all'ingaggio che chiede, da 1 a 4 stipendi, e venderlo al computer, che paga fino al valore di mercato col suo
rialzo, circa 6,9 stipendi. La misura vecchia contava la cassa meno lo sponsor, e gli stipendi dei mesi d'attesa
diventavano un costo del trucco; ma in quei mesi il giocatore sta in rosa, e una rosa onesta paga gli stessi
stipendi e incassa lo stesso sponsor. Qui le strategie sono due, tutte e due con la rosa piena: rivendi e riempi,
dove ogni tesserato sta in vendita al prezzo più alto che il computer paga, il valore pieno col rialzo, e il posto
si riempie appena il computer lo compra; tieni e rinnova, dove la rosa si tiene, i contratti si rinnovano e si
riempie soltanto il posto di chi se ne va. Il risultato è la differenza fra le due, per posto e per anno. I numeri
della misura del 3 novembre 2026, e il verdetto, stanno in strumenti/rivendita_d40.txt.
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
rivendita i posti si riempiono invece col guadagno per giorno del ciclo stimato, dalla firma alla vendita, e
soltanto con chi non entra nel declino prima della vendita; il prezzo è sempre il tetto pieno, quindi chi è negli
ultimi tre mesi di contratto aspetta che il rinnovo concordato prenda il suo posto. Nella rivendita con N mesi la
firma dei quindici della partenza si sposta indietro, a passi regolari fra 0 e N mesi, come se il commercio
andasse avanti da sempre: le vendite si spargono nel tempo, e la differenza divisa per gli anni misura il guadagno a
regime anche quando la durata non è un multiplo di N; N prende il posto della costante soltanto durante la corsa,
in economia, dove lo legge rivendita_dal. I conti sono tutte le voci dei conti del mese: sponsor, con
la regola della seconda tranche di D40, vendite, stipendi, arretrati, ingaggi, buonuscite, iscrizioni, premi e
rimborsi; la loro somma è la cassa, e lo strumento lo controlla.
Non tocca mai il mondo salvato: ogni processo sposta la cartella del programma e quella del mondo in cartelle
temporanee, che alla fine si cancellano; i mondi e le partenze vivono nella cartella di lavoro, che senza
--cartella è temporanea anche lei. Le corse vanno in parallelo, al più --processi insieme.
Uso: python -B strumenti/misura_rivendita.py [--semi 11 2026 7 13] [--giorni-dei-mondi 730 3650]
[--mesi 0 3 6 9 12 18 24] [--durata 36] [--gloria 275] [--gloria-media 150] [--club gloriosa media] [--processi 16]
[--cartella C] [--salva risultati.json]
Il 3 novembre 2026 Gabriele ha scelto la rampa del prezzo, e MESI_PRIMA_DELLA_RIVENDITA ha lasciato il posto a
MESI_DELLA_RAMPA: lo strumento cambia quella costante, e col prezzo sempre al tetto pieno misura ancora l'attesa fino alla
fine della rampa. La misura della rampa, col prezzo che sale, è un lavoro a parte.
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
import tratti  # noqa: E402
from costanti import (  # noqa: E402
    GIORNI_PER_MESE,
    K_GLORIA_COPPE,
    MAX_TESSERATI_POLISPORTIVA,
    MESI_DI_INGAGGIO,
    MESI_DI_RISERVA_CPU,
    MESI_VALORE_PIENO,
    RIALZO_CPU,
    STIPENDIO_MINIMO,
)
from modelli import VOCI_CONTI, conti_vuoti  # noqa: E402

SEMI = (11, 2026, 7, 13)
GIORNI_DEI_MONDI = (730, 3650)
MESI_PROVATI = (0, 3, 6, 9, 12, 18, 24)
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
    """Il prezzo più alto che il computer paga per un tesserato col contratto lontano dalla scadenza: il valore pieno col rialzo."""
    return int(economia.valore_di_mercato_pieno(g) * RIALZO_CPU)


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
    I giorni dalla firma di oggi alla vendita al computer, stimati: il giorno in cui il computer lo compra, o, se
    il contratto è allora negli ultimi tre mesi, la scadenza, quando il rinnovo prende il suo posto e il valore
    torna pieno. Un contratto che finisce prima si rinnova per la stessa durata.
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
    I liberi da tesserare, dal migliore: fino a 30 anni, che possono giocare e rendono, cioè col tetto sopra
    l'ingaggio chiesto. Senza mesi in ordine di guadagno; coi mesi della rivendita in ordine di guadagno per giorno
    del ciclo, e soltanto chi non entra nel declino prima della vendita.
    """
    oggi = mondo.datetime_corrente_simulazione
    morti = mondo._ids_morti_processati_sessione
    righe = []
    for gid, g in mondo.giocatori.items():
        if g.appartenenza != "*" or g.ritirato or gid in morti or not g.puo_giocare or g.eta_anni > ETA_MASSIMA:
            continue
        guadagno = tetto(g) - economia.ingaggio_richiesto(g, poli)
        if guadagno <= 0:
            continue
        if mesi is None:
            righe.append((guadagno, gid, g))
            continue
        giorni = ciclo_stimato(g, oggi, mesi)
        if g.eta + giorni < tratti.giorni_inizio_declino(g):
            righe.append((guadagno / giorni, gid, g))
    righe.sort(key=lambda riga: (-riga[0], riga[1]))
    return [g for _resa, _gid, g in righe]


def riempi(mondo, poli, mesi, conti):
    """Riempie i posti vuoti coi candidati che il computer comprerebbe, offrendo l'ingaggio chiesto finché accettano o finiscono le mosse."""
    if len(poli.tesserati) >= poli.maxtesserati or mondo.mosse_rimaste(poli) <= 0:
        return
    righe = None
    for g in candidati(mondo, poli, mesi):
        if len(poli.tesserati) >= poli.maxtesserati or mondo.mosse_rimaste(poli) <= 0:
            return
        if righe is None:
            righe = compratori(mondo, mondo.datetime_corrente_simulazione)
        if not vendibile(g, tetto(g), righe):
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


def metti_tutti_in_vendita(mondo, poli):
    """Ogni tesserato in vendita al tetto pieno; il prezzo si rifà soltanto quando il tetto cambia, e chi è convocato aspetta."""
    for g in mondo._rosa(poli):
        prezzo = tetto(g)
        if poli.in_vendita.get(g.id) != prezzo:
            with suppress(ValueError):
                mondo.metti_in_vendita(poli, g, prezzo)


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
    Una strategia per tanti mesi di calendario, dalla partenza comune: rivendi, coi mesi della rivendita, o tieni.
    Restituisce le voci dei conti sommate, il saldo e i conteggi di firme, vendite, uscite e rinnovi. I mesi della
    rivendita prendono il posto della costante, in economia, dove la legge rivendita_dal, e alla fine la costante torna.
    Dalla rampa del prezzo scelta da Gabriele il 3 novembre 2026 la costante è MESI_DELLA_RAMPA, e la legge
    tetto_di_rivendita: col prezzo al tetto pieno il computer compra alla fine della rampa, come prima alla fine
    dell'attesa. La misura della rampa vera la rifà un altro passo.
    """
    costante = economia.MESI_DELLA_RAMPA
    if strategia == "rivendi":
        economia.MESI_DELLA_RAMPA = mesi
    try:
        return _corsa(seme, giorni, club, strategia, mesi, durata, cartella)
    finally:
        economia.MESI_DELLA_RAMPA = costante


def _corsa(seme, giorni, club, strategia, mesi, durata, cartella):
    """Il corpo di corsa, con i mesi della rivendita già al posto della costante."""
    inizio = time.perf_counter()
    with cartelle_temporanee():
        partenza = carica(file_della_partenza(cartella, seme, giorni, club))
        mondo, dati = partenza["mondo"], partenza["dati"]
        poli = mondo.polisportive[partenza["nome"]]
        bersaglio, chiave = dati["bersaglio"], dati["chiave"]
        rivendi = strategia == "rivendi"
        random.seed(seme_del_gruppo(seme, giorni, club))
        oggi = mondo.datetime_corrente_simulazione
        fine = contratti.stesso_giorno_dopo(oggi, durata)
        firmato = dict.fromkeys(poli.tesserati, 0)
        if rivendi and mesi:
            # La partenza a regime: le firme dei quindici sparse a passi regolari negli ultimi N mesi.
            tesserati = sorted(poli.tesserati)
            for i, gid in enumerate(tesserati):
                spostamento = round(mesi * GIORNI_PER_MESE * (i + 0.5) / len(tesserati))
                mondo.giocatori[gid].tesserato_dal = oggi - datetime.timedelta(days=spostamento)
        cassa_iniziale = poli.cassa
        totali = dict.fromkeys(VOCI_CONTI, 0)
        conti = {"firme": 0, "rifiuti": 0, "rinnovi": 0, "rinnovi_rifiutati": 0, "vendite": 0, "usciti": 0, "giorni_tenuti": 0}
        glorie, posti_giorno, giorno = [], 0, 0
        while mondo.datetime_corrente_simulazione < fine:
            tieni_la_gloria(mondo, poli, bersaglio, chiave)
            allena_tutti(mondo, poli)
            rinnova_tutti(mondo, poli, conti)
            riempi(mondo, poli, mesi if rivendi else None, conti)
            for gid in poli.tesserati:
                firmato.setdefault(gid, giorno)
            if rivendi:
                metti_tutti_in_vendita(mondo, poli)
            tieni_la_gloria(mondo, poli, bersaglio, chiave)
            posti_giorno += len(poli.tesserati)
            # La gloria che lo sponsor paga domani, se domani è il primo del mese: i conti la leggono prima delle mosse del computer.
            domani = mondo.datetime_corrente_simulazione + datetime.timedelta(days=1)
            if domani.day == 1:
                glorie.append(poli.gloria)
            # Chi domani esce dalla rosa ed entra in una del computer è venduto se era in vendita, ma non se il contratto
            # gli scade domani senza rinnovo: torna libero, e il computer può tesserarlo lo stesso giorno.
            vendibili = {gid for gid in poli.in_vendita if not scade_entro(mondo.giocatori[gid], domani)}
            prima = set(poli.tesserati)
            ms.avanza_un_giorno(mondo)
            giorno += 1
            for gid in sorted(prima - set(poli.tesserati)):
                g = mondo.giocatori.get(gid)
                quando = firmato.pop(gid, 0)
                if g is not None and gid in vendibili and g.appartenenza not in ("*", poli.nome):
                    conti["vendite"] += 1
                    conti["giorni_tenuti"] += giorno - quando
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
        return {"seme": seme, "giorni": giorni, "club": club, "strategia": strategia, "mesi": mesi, "durata": durata, "giorni_corsi": giorno,
                "saldo": saldo, "somma_delle_voci": somma, "voci": totali, **conti, "posti_giorno": posti_giorno,
                "gloria_minima": min(glorie) if glorie else poli.gloria, "gloria_massima": max(glorie) if glorie else poli.gloria,
                "tesserati_alla_fine": len(rosa), "valore_alla_fine": sum(economia.valore_di_mercato_pieno(g) for g in rosa),
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


def differenze(risultati, durata):
    """Per mondo, club e mesi, la differenza fra la rivendita e il tieni di ogni seme, per posto e per anno, e le voci."""
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
            "vendite_per_posto_e_anno": r["vendite"] / MAX_TESSERATI_POLISPORTIVA / (durata / 12),
            "giorni_tenuti": r["giorni_tenuti"] / r["vendite"] if r["vendite"] else None,
            "prezzo_medio": r["voci"]["vendite"] / r["vendite"] if r["vendite"] else None,
            "ingaggio_medio": r["voci"]["ingaggi"] / r["firme"] if r["firme"] else None,
            "rosa_media": r["posti_giorno"] / max(1, r["giorni_corsi"]), "rosa_media_tieni": t["posti_giorno"] / max(1, t["giorni_corsi"]),
            "valore_alla_fine": r["valore_alla_fine"], "valore_alla_fine_tieni": t["valore_alla_fine"],
            "gloria": (min(r["gloria_minima"], t["gloria_minima"]), max(r["gloria_massima"], t["gloria_massima"]))})
    return gruppi


def riassunto(righe):
    """Media e scarto quadratico fra i semi della differenza; lo scarto è zero con un seme solo."""
    valori = [r["differenza"] for r in righe]
    media = statistics.fmean(valori)
    scarto = statistics.stdev(valori) if len(valori) > 1 else 0.0
    return media, scarto


def tabella(gruppi, partenze, durata):
    """Le righe della tabella, una per mondo, club e mesi, e il verdetto per la gloriosa."""
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
                semi = ", ".join(euro(r["differenza"]) for r in gruppo)
                voci = {voce: statistics.fmean(r["voci"][voce] for r in gruppo) for voce in VOCI_CONTI}
                resto = sum(v if voce in ENTRATE else -v for voce, v in voci.items() if voce not in VOCI_DETTE)
                dette = "; ".join(f"{voce} {euro(voci[voce] if voce in ENTRATE else -voci[voce])}" for voce in VOCI_DETTE)
                vendite = statistics.fmean(r["vendite_per_posto_e_anno"] for r in gruppo)
                tenuti = [r["giorni_tenuti"] for r in gruppo if r["giorni_tenuti"] is not None]
                testo = (f"{mesi} mesi: differenza {euro(media)} euro per posto e per anno, scarto fra i semi {euro(scarto)}; semi {semi}. "
                         f"Voci, rivendita meno tieni, per posto e per anno: {dette}; tornei e resto {euro(resto)}.")
                if tenuti:
                    testo += f" Vendite per posto e per anno {decimale(vendite, 2)}, giorni in rosa {euro(statistics.fmean(tenuti))}."
                else:
                    testo += " Nessuna vendita."
                righe.append(testo)
    return righe


def verdetto(gruppi):
    """Per ogni mondo il numero più piccolo di mesi che porta la differenza della gloriosa a zero entro lo scarto fra i semi, o None."""
    esito = {}
    for giorni in sorted({g for g, _c, _m in gruppi}):
        esito[giorni] = None
        for mesi in sorted({m for g, c, m in gruppi if g == giorni and c == "gloriosa"}):
            media, scarto = riassunto(gruppi[(giorni, "gloriosa", mesi)])
            if abs(media) <= scarto or media <= 0:
                esito[giorni] = mesi
                break
    return esito


def in_parallelo(esecutore, compiti, racconta):
    """Lancia i compiti, coppie di funzione e argomenti, e ne raccoglie i risultati man mano che finiscono."""
    futuri = [esecutore.submit(funzione, *argomenti) for funzione, argomenti in compiti]
    risultati = []
    for futuro in as_completed(futuri):
        risultato = futuro.result()
        risultati.append(risultato)
        racconta(risultato)
    return risultati


def main():
    parser = argparse.ArgumentParser(description="Misura quanti mesi il computer deve aspettare prima di comprare un tesserato dell'utente.")
    parser.add_argument("--semi", type=int, nargs="+", default=list(SEMI))
    parser.add_argument("--giorni-dei-mondi", type=int, nargs="+", default=list(GIORNI_DEI_MONDI))
    parser.add_argument("--mesi", type=int, nargs="+", default=list(MESI_PROVATI))
    parser.add_argument("--durata", type=int, default=DURATA_MESI, help="mesi di calendario di ogni corsa")
    parser.add_argument("--processi", type=int, default=PROCESSI)
    parser.add_argument("--gloria", type=int, default=GLORIA_GLORIOSA, help="la gloria della polisportiva gloriosa")
    parser.add_argument("--gloria-media", type=int, default=GLORIA_MEDIA, help="la gloria della polisportiva media")
    parser.add_argument("--club", nargs="+", choices=tuple(CLUB), default=list(CLUB))
    parser.add_argument("--cartella", type=Path, help="dove tenere mondi e partenze; senza, una cartella temporanea che si cancella")
    parser.add_argument("--salva", type=Path, help="il file JSON dove scrivere tutti i risultati")
    args = parser.parse_args()
    # Lo stesso ordine degli insiemi in tutti i processi, perché la stessa corsa dia gli stessi numeri.
    os.environ.setdefault("PYTHONHASHSEED", "0")
    temporanea = args.cartella is None
    cartella = Path(tempfile.mkdtemp(prefix="mess_rivendita_mondi_")) if temporanea else args.cartella
    cartella.mkdir(parents=True, exist_ok=True)
    inizio = time.perf_counter()

    def racconta(testo):
        print(f"{time.perf_counter() - inizio:7.0f} s. {testo}", flush=True)

    try:
        with cartelle_temporanee(), ProcessPoolExecutor(max_workers=max(1, args.processi)) as esecutore:
            mancanti = [s for s in args.semi if not all(file_del_mondo(cartella, s, g).exists() for g in args.giorni_dei_mondi)]
            in_parallelo(esecutore, [(fai_nascere, (s, args.giorni_dei_mondi, cartella)) for s in mancanti],
                         lambda r: racconta(f"Nato il mondo del seme {r[0]}, in {r[1]:.0f} s."))
            gruppi = [(s, g, c) for g in sorted(args.giorni_dei_mondi, reverse=True) for s in args.semi for c in args.club]
            bersagli = {"gloriosa": args.gloria, "media": args.gloria_media}
            partenze = in_parallelo(esecutore, [(prepara_la_partenza, (s, g, c, cartella, bersagli[c])) for s, g, c in gruppi],
                                    lambda d: racconta(f"Partenza del seme {d['seme']}, mondo di {d['giorni']} giorni, {d['club']}: gloria {d['gloria']} "
                                                       f"su {d['bersaglio']}, {d['tesserati']} tesserati in {d['giorni_di_riempimento']} giorni, "
                                                       f"{d['firme']} firme e {d['rifiuti']} rifiuti, in {d['secondi']:.0f} s."))
            compiti = [(corsa, (s, g, c, "tieni", None, args.durata, cartella)) for s, g, c in gruppi]
            compiti += [(corsa, (s, g, c, "rivendi", m, args.durata, cartella)) for s, g, c in gruppi for m in args.mesi]
            # Prima le corse lunghe, nei mondi più vecchi e coi mesi più corti, che vendono di più.
            compiti.sort(key=lambda compito: (-compito[1][1], compito[1][4] if compito[1][4] is not None else -1))
            risultati = in_parallelo(esecutore, compiti, lambda r: racconta(
                f"Corsa {r['strategia']}{'' if r['mesi'] is None else ' a ' + str(r['mesi']) + ' mesi'}, seme {r['seme']}, mondo di {r['giorni']} giorni, "
                f"{r['club']}: saldo {euro(r['saldo'])} euro, vendite {r['vendite']}, firme {r['firme']}, in {r['secondi']:.0f} s."))
        sbagliate = [r for r in risultati if r["saldo"] != r["somma_delle_voci"]]
        for r in sbagliate:
            racconta(f"Attenzione: nella corsa {r['strategia']} {r['mesi']}, seme {r['seme']}, mondo di {r['giorni']}, {r['club']}, "
                     f"le voci fanno {euro(r['somma_delle_voci'])} e la cassa {euro(r['saldo'])}.")
        conto = differenze(risultati, args.durata)
        for riga in tabella(conto, partenze, args.durata):
            print(riga, flush=True)
        for giorni, mesi in verdetto(conto).items():
            print(f"Mondo di {giorni} giorni: per la gloriosa basta {mesi} mesi." if mesi is not None else
                  f"Mondo di {giorni} giorni: per la gloriosa nessun numero di mesi provato basta.", flush=True)
        if args.salva:
            gruppi_json = [{"giorni": g, "club": c, "mesi": m, "semi": righe} for (g, c, m), righe in sorted(conto.items())]
            args.salva.write_text(json.dumps({"partenze": partenze, "corse": risultati, "differenze": gruppi_json}, ensure_ascii=False, indent=1),
                                  encoding="utf-8")
        racconta("Fine.")
    finally:
        if temporanea:
            shutil.rmtree(cartella, ignore_errors=True)


if __name__ == "__main__":
    main()
