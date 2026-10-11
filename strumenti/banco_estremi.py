"""
Il giro degli estremi del motore di partita di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11, risposta 6 di Gabriele e punto 12.2 del progetto della tappa.
Senza i tetti propri della parte allenata ogni caratteristica può arrivare al tetto del totale, e
il motore, tarato alla tappa 9 su giocatori poco allenati, va provato lassù, dove nessuno era mai
arrivato. Lo strumento è di sola lettura: usa il motore vero, in modalità essenziale al meglio dei
3, e non scrive niente nel progetto.
I soggetti sono nati della fascia mediana, fra il trentesimo e il settantesimo percentile della
somma pesata dei nati di un seme, destrimani e senza tratti speciali, con la loro innata; gli
avversari sono altri nati della stessa fascia. La fascia si dice in somma pesata e non in valore,
perché la scala del valore la ritocca la taratura dell'economia, che viene dopo. Per ogni
caratteristica da sola, per ognuna delle otto coppie di lato, battute, lungolinea, diagonali,
sponde, chiusure e blocchi, per tutti i colpi dello scambio insieme e per tutto, i soggetti si
portano al 30, 45, 60, 70, 80, 90 e 100 per cento del tetto del totale, e a ogni livello giocano
gli stessi incontri, contro gli stessi avversari, con gli stessi semi e a parti alternate: così il
confronto fra un livello e l'altro non porta il rumore di avversari e semi diversi.
Il rating è quello della taratura del valore, il logaritmo dei punti fatti sui subiti. La resa è
il rating guadagnato per punto di somma pesata, tratto per tratto, e la resa di riferimento è la
media del primo tratto, dall'innata al 30 per cento, sui sedici gruppi della taratura del valore:
è lì che la regressione ha misurato i pesi. L'errore di una resa viene dai lotti: i soggetti si
dividono in venti lotti, ognuno dà la sua resa, e l'errore è quello della media.
I bersagli di buon senso del progetto: nessun tratto sopra il 30 per cento renda più di
RESA_MASSIMA_RELATIVA volte la resa di riferimento, con un errore sotto un quinto di quella; il
rating non scenda mai, oltre il rumore, quando una caratteristica sale; fra due campioni gemelli con
tutto al 100 gli attacchi per punto siano al massimo il doppio di quelli fra due gemelli della
fascia, i punti per set fra 10 e 16, i falli per punto sopra 0,2, e nessuno scambio si fermi al
limite tecnico dei colpi; le efficienze di fine quinto set stiano nelle bande della sonda della
stanchezza di strumenti/banco_partite.py, per i nati della fascia e per i campioni. Le
caratteristiche che agli estremi rendono meno del loro peso, perché si saturano, si annotano e non
si correggono: sono un cattivo investimento, non un vantaggio indebito.
Per ogni prova il rapporto dà anche gli esiti al 100 per cento: punti per set, attacchi per punto,
goal, falli, fuori, palle morte e colpi deboli per punto, lo scambio più lungo e i time-out.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/banco_estremi.py
    python strumenti/banco_estremi.py --incontri 2000 --rapporto strumenti/banco_estremi_prima.txt
    python strumenti/banco_estremi.py --prove colpi --incontri 4000 --taratura prova.json
"""

import argparse
import copy
import datetime
import itertools
import math
import os
import random
import statistics
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))
STRUMENTI = Path(__file__).resolve().parent
if str(STRUMENTI) not in sys.path:
    sys.path.insert(0, str(STRUMENTI))

import allenamento  # noqa: E402
import costanti  # noqa: E402
import testi  # noqa: E402
import valore  # noqa: E402
from modelli import Giocatore  # noqa: E402
from motore import ESSENZIALE, SINGOLARE_3, TARATURA, simula_incontro  # noqa: E402
from motore.taratura import carica_taratura  # noqa: E402
from version import __version__  # noqa: E402

NASCITA = datetime.datetime(2026, 1, 1)  # noqa: DTZ001 - data segnaposto, come quelle del motore
LIVELLI = (0.30, 0.45, 0.60, 0.70, 0.80, 0.90, 1.00)
# Un tratto sopra il 30 per cento non deve rendere più di questo multiplo della resa di riferimento,
# e la misura vale se il suo errore sta sotto questa parte della resa di riferimento.
RESA_MASSIMA_RELATIVA = 1.5
ERRORE_MASSIMO_RELATIVO = 0.2
# Sotto questa quota della resa di riferimento una caratteristica si satura: rende meno del suo peso.
RESA_SATURA_RELATIVA = 0.5
# La fascia dei soggetti e degli avversari: i percentili della somma pesata dei nati.
FASCIA = (0.30, 0.70)
# Da quanti nati si prende la fascia, e in quanti lotti si dividono i soggetti per l'errore delle rese.
NATI = 8000
LOTTI = 20
# I sedici gruppi della taratura del valore: le coppie speculari insieme, le altre da sole.
GRUPPI = {
    "precisione": ("precisione",), "resistenza": ("resistenza",), "forza": ("forza",),
    "battute": ("battutasx", "battutadx"), "lungolinea": ("lungolineasx", "lungolineadx"), "diagonali": ("diagonalesx", "diagonaledx"),
    "singola sponda": ("singolaspondasx", "singolaspondadx"), "doppia sponda": ("doppiaspondasx", "doppiaspondadx"),
    "tripla sponda": ("triplaspondasx", "triplaspondadx"), "bomba": ("bomba",), "attacco": ("attacco",),
    "chiusure": ("chiusurasx", "chiusuradx"), "blocchi": ("bloccosx", "bloccodx"), "difesa": ("difesa",),
    "controllo palla": ("controllopalla",), "tenuta paletta": ("tenutapaletta",),
}
COLPI = tuple(costanti.COLPI_DELLO_SCAMBIO)
CAUSE_FUORI = ("out_in_difesa", "out_sponda", "out_tavola_contatto", "out_volo", "out_soffitto")
# I bersagli dei campioni gemelli con tutto al 100.
PUNTI_PER_SET = (10.0, 16.0)
FALLI_PER_PUNTO_MINIMI = 0.2
ATTACCHI_RELATIVI_MASSIMI = 2.0


def numero(valore_numerico, decimali=2):
    return f"{valore_numerico:.{decimali}f}".replace(".", ",")


def prove():
    """Le prove del giro: ogni caratteristica da sola, le otto coppie di lato, tutti i colpi dello scambio insieme, e tutto."""
    singole = [(testi.nome_caratteristica(c + "_base").lower(), (c,)) for c in allenamento.CARATTERISTICHE]
    coppie = [(nome, nomi) for nome, nomi in GRUPPI.items() if len(nomi) > 1]
    return (*singole, *coppie, ("tutti i colpi dello scambio", COLPI), ("tutto", allenamento.CARATTERISTICHE))


def scelte(quali):
    """Le prove scelte con --prove: tutte, colpi, cioè i colpi dello scambio da soli e in coppia, oppure i nomi separati da virgole."""
    tutte = prove()
    if quali == "tutte":
        return tutte
    if quali == "colpi":
        return tuple((nome, nomi) for nome, nomi in tutte if set(nomi) <= set(COLPI))
    nomi_scelti = {n.strip() for n in quali.split(",")}
    return tuple((nome, nomi) for nome, nomi in tutte if nome in nomi_scelti)


def senza_tratti(g):
    return not (g.mancino or g.ambidestro or g.giocorapido or g.cambiovelocita)


def nati(quanti, seme):
    """I nati del generatore vero, col caso del mondo seminato e poi rimesso com'era."""
    stato = random.getstate()
    random.seed(seme)
    try:
        return [Giocatore(i + 1, NASCITA) for i in range(quanti)]
    finally:
        random.setstate(stato)


def soggetti_e_avversari(quanti_soggetti, quanti_avversari, seme, esperienza=0.0):
    """I soggetti e gli avversari della fascia mediana, destrimani e senza tratti speciali, e la fascia in somma pesata."""
    tutti = nati(max(NATI, 6 * (quanti_soggetti + quanti_avversari)), seme)
    somme = sorted(valore.somma_pesata(g) for g in tutti)
    basso, alto = somme[int(len(somme) * FASCIA[0])], somme[int(len(somme) * FASCIA[1])]
    fascia = [g for g in tutti if senza_tratti(g) and basso <= valore.somma_pesata(g) <= alto]
    if len(fascia) < quanti_soggetti + quanti_avversari:
        raise ValueError("Nella fascia non ci sono abbastanza nati: servono più nati o meno soggetti.")
    for g in fascia:
        g.esperienza = esperienza
    return fascia[:quanti_soggetti], fascia[quanti_soggetti:quanti_soggetti + quanti_avversari], (basso, alto)


def portato(g, nomi, livello):
    """Una copia del giocatore con le caratteristiche indicate portate almeno al livello indicato del tetto del totale, con la parte allenata."""
    m = copy.copy(g)
    if livello is None:
        return m
    for c in nomi:
        base = getattr(g, c + "_base")
        setattr(m, c + "_allenata", max(getattr(g, c + "_allenata"), livello * allenamento.tetto(c) - base))
    return m


def piano(soggetti, avversari, incontri, seme):
    """Gli incontri di ogni soggetto: l'avversario e il seme, gli stessi a ogni livello e in ogni prova."""
    per_soggetto = max(1, incontri // len(soggetti))
    rng = random.Random(f"estremi-{seme}")
    return [[(rng.randrange(len(avversari)), rng.getrandbits(63)) for _k in range(per_soggetto)] for _g in soggetti]


def esiti_vuoti():
    return {"incontri": 0, "set": 0, "punti": 0, "attacchi": 0, "goal": 0, "falli": Counter(), "palle_morte": Counter(), "piu_lungo": 0, "timeout": 0}


def aggiungi_esiti(esiti, risultato):
    """Gli esiti di un incontro, per tutti e due i giocatori: punti, set, attacchi, goal, falli per causa, palle morte, scambio più lungo e time-out."""
    incontro = risultato.incontro
    esiti["incontri"] += 1
    esiti["set"] += len(risultato.set)
    esiti["punti"] += incontro.punti_giocati
    esiti["attacchi"] += sum(incontro.attacchi_per_punto)
    esiti["palle_morte"].update(incontro.palle_morte)
    esiti["timeout"] += len(incontro.timeout)
    for stats in risultato.statistiche.values():
        esiti["goal"] += stats.goal
        esiti["falli"].update(stats.falli)
        esiti["piu_lungo"] = max(esiti["piu_lungo"], stats.scambio_piu_lungo)


def somma_esiti(primi, secondi):
    for chiave in ("incontri", "set", "punti", "attacchi", "goal", "timeout"):
        primi[chiave] += secondi[chiave]
    primi["falli"].update(secondi["falli"])
    primi["palle_morte"].update(secondi["palle_morte"])
    primi["piu_lungo"] = max(primi["piu_lungo"], secondi["piu_lungo"])
    return primi


def misure_esiti(esiti):
    """Gli esiti in numeri da leggere: per set, per punto, il più lungo e i time-out a incontro."""
    punti = max(1, esiti["punti"])
    falli = sum(esiti["falli"].values())
    return {"punti_per_set": esiti["punti"] / max(1, esiti["set"]), "attacchi_per_punto": esiti["attacchi"] / punti, "goal_per_punto": esiti["goal"] / punti,
            "falli_per_punto": falli / punti, "fuori_per_punto": sum(esiti["falli"][c] for c in CAUSE_FUORI) / punti,
            "palle_morte_per_punto": sum(esiti["palle_morte"].values()) / punti, "deboli_per_punto": esiti["palle_morte"]["colpo_debole"] / punti,
            "limite_tecnico": esiti["palle_morte"]["limite_tecnico"], "piu_lungo": esiti["piu_lungo"], "timeout_per_incontro": esiti["timeout"] / max(1, esiti["incontri"])}


# Il lavoro di un processo: soggetti, avversari e piano arrivano una volta, all'avvio del processo.
# I nati si fanno nel processo principale, perché farli in ogni processo costava quanto un terzo delle partite.
_LAVORO = {}


def prepara(soggetti, avversari, incontri, seme, taratura):
    _LAVORO.update(soggetti=soggetti, avversari=avversari, piano=piano(soggetti, avversari, incontri, seme), taratura=taratura)


def gioca_prova(nomi, livello, gemello=False):
    """
    Gli incontri di una prova a un livello: per ogni lotto di soggetti i punti fatti e subiti, le
    vittorie, gli incontri e la somma pesata media; e gli esiti di tutti gli incontri. Con gemello
    ognuno gioca contro una copia di sé, portata allo stesso livello.
    """
    soggetti, avversari, incontri, taratura = _LAVORO["soggetti"], _LAVORO["avversari"], _LAVORO["piano"], _LAVORO["taratura"]
    lotti = [{"fatti": 0, "subiti": 0, "vinte": 0, "giocate": 0, "somma": 0.0, "soggetti": 0} for _l in range(LOTTI)]
    esiti = esiti_vuoti()
    for i, (g, suoi) in enumerate(zip(soggetti, incontri, strict=True)):
        lotto = lotti[i * LOTTI // len(soggetti)]
        m = portato(g, nomi, livello)
        lotto["somma"] += valore.somma_pesata(m)
        lotto["soggetti"] += 1
        for k, (j, seme) in enumerate(suoi):
            if gemello:
                avversario = copy.copy(m)
                avversario.id = m.id + 10_000_000
            else:
                avversario = avversari[j]
            primo = k % 2 == 0
            a, b = (m, avversario) if primo else (avversario, m)
            r = simula_incontro(a, b, SINGOLARE_3, seme=seme, dettaglio=ESSENZIALE, taratura=taratura)
            punti_a = sum(x for x, _y in r.set)
            punti_b = sum(y for _x, y in r.set)
            lotto["fatti"] += punti_a if primo else punti_b
            lotto["subiti"] += punti_b if primo else punti_a
            lotto["vinte"] += (r.vincitore == "A") == primo
            lotto["giocate"] += 1
            aggiungi_esiti(esiti, r)
    return lotti, esiti


def gioca_fatica(su_campioni, quante, seme):
    """I casi di fine quinto set della sonda della stanchezza, sui nati della fascia o sui campioni con tutto al 100."""
    # Il banco delle partite porta con sé il mondo: lo si importa soltanto qui, dove serve la sua sonda.
    import banco_partite

    soggetti, taratura = _LAVORO["soggetti"], _LAVORO["taratura"]
    giocatori = [portato(g, allenamento.CARATTERISTICHE, 1.0) if su_campioni else copy.copy(g) for g in soggetti]
    rng = random.Random(f"estremi-fatica-{seme}-{su_campioni}")
    righe = banco_partite.sonda_fatica(giocatori, quante, rng, {"dettaglio": ESSENZIALE, "taratura": taratura}, solo_quinto=True)
    return su_campioni, righe


def rating(lotti):
    fatti = sum(lotto["fatti"] for lotto in lotti)
    subiti = sum(lotto["subiti"] for lotto in lotti)
    return math.log(max(1, fatti) / max(1, subiti))


def somma_media(lotti):
    return sum(lotto["somma"] for lotto in lotti) / max(1, sum(lotto["soggetti"] for lotto in lotti))


def vittorie(lotti):
    return 100.0 * sum(lotto["vinte"] for lotto in lotti) / max(1, sum(lotto["giocate"] for lotto in lotti))


def resa_di_un_tratto(prima, dopo, minimo=1e-6):
    """
    La resa di un tratto fra due livelli: il rating guadagnato per punto di somma pesata, sui
    lotti messi insieme, e il suo errore, quello della media delle rese dei lotti. None se nel
    tratto la somma pesata non cresce, perché i soggetti c'erano già.
    """
    delta_somma = somma_media(dopo) - somma_media(prima)
    if delta_somma <= minimo:
        return None
    resa = (rating(dopo) - rating(prima)) / delta_somma
    per_lotto = []
    for lotto_prima, lotto_dopo in zip(prima, dopo, strict=True):
        delta = lotto_dopo["somma"] / max(1, lotto_dopo["soggetti"]) - lotto_prima["somma"] / max(1, lotto_prima["soggetti"])
        if delta > minimo and lotto_prima["subiti"] and lotto_dopo["subiti"]:
            per_lotto.append((math.log(lotto_dopo["fatti"] / lotto_dopo["subiti"]) - math.log(lotto_prima["fatti"] / lotto_prima["subiti"])) / delta)
    errore = statistics.stdev(per_lotto) / math.sqrt(len(per_lotto)) if len(per_lotto) > 1 else float("inf")
    return resa, errore


def rese_della_prova(base, livelli):
    """Le rese dei tratti di una prova, dall'innata al primo livello e poi da un livello all'altro: elenco di coppie resa ed errore, o None."""
    passi = [base, *livelli]
    return [resa_di_un_tratto(prima, dopo) for prima, dopo in itertools.pairwise(passi)]


def gruppi_mancanti(prove_scelte):
    """I gruppi della taratura del valore che le prove scelte non giocano: senza tutti e sedici la resa di riferimento non si calcola."""
    giocati = {nomi for _nome, nomi in prove_scelte}
    return [nome for nome, nomi in GRUPPI.items() if nomi not in giocati]


def resa_di_riferimento(rese_per_prova):
    """
    La media del primo tratto, dall'innata al 30 per cento, sui sedici gruppi della taratura del
    valore. Con una parte soltanto dei gruppi la media sarebbe un'altra, e tutte le rese relative con
    lei: la revisione della tappa 11 l'ha visto con le sole battute e i colpi, 6,98 millesimi invece di
    9,07, e rese più alte di un terzo. Per questo vuole tutti e sedici i gruppi.
    """
    mancanti = [nome for nome, nomi in GRUPPI.items() if nomi not in rese_per_prova or rese_per_prova[nomi][0] is None]
    if mancanti:
        raise ValueError(f"Per la resa di riferimento servono i sedici gruppi; mancano {', '.join(mancanti)}.")
    return statistics.fmean(rese_per_prova[nomi][0][0] for nomi in GRUPPI.values())


def verdetto_dei_tratti(rese, riferimento, livelli=LIVELLI):
    """
    Il verdetto di una prova, tratto per tratto: troppo, cioè sopra RESA_MASSIMA_RELATIVA volte la
    resa di riferimento, per un tratto che arriva oltre il 30 per cento; incerto, se l'errore supera
    ERRORE_MASSIMO_RELATIVO della resa di riferimento; scende, se il rating cala oltre due errori;
    satura, sotto RESA_SATURA_RELATIVA, soltanto da annotare. Restituisce un elenco di coppie, il
    livello d'arrivo del tratto e il verdetto, per i tratti che ne hanno uno.
    """
    giudizi = []
    for livello, misura in zip(livelli, rese, strict=True):
        if misura is None:
            continue
        resa, errore = misura
        if resa < -2.0 * errore:
            giudizi.append((livello, "scende"))
        elif livello > livelli[0] + 1e-9 and resa > RESA_MASSIMA_RELATIVA * riferimento:
            giudizi.append((livello, "troppo" if errore < ERRORE_MASSIMO_RELATIVO * riferimento else "troppo, ma incerto"))
        elif errore >= ERRORE_MASSIMO_RELATIVO * riferimento:
            giudizi.append((livello, "incerto"))
        elif livello > livelli[0] + 1e-9 and resa < RESA_SATURA_RELATIVA * riferimento:
            giudizi.append((livello, "satura"))
    return giudizi


def verdetto_dei_campioni(campioni, gemelli_della_fascia):
    """I bersagli dei campioni gemelli con tutto al 100: un elenco di coppie, la frase e se sta dentro."""
    attacchi = campioni["attacchi_per_punto"] / max(1e-9, gemelli_della_fascia["attacchi_per_punto"])
    return [
        (f"attacchi per punto {numero(campioni['attacchi_per_punto'])}, {numero(attacchi)} volte quelli fra due gemelli della fascia, al massimo {numero(ATTACCHI_RELATIVI_MASSIMI, 0)}",
         attacchi <= ATTACCHI_RELATIVI_MASSIMI),
        (f"punti per set {numero(campioni['punti_per_set'], 1)}, bersaglio da {numero(PUNTI_PER_SET[0], 0)} a {numero(PUNTI_PER_SET[1], 0)}",
         PUNTI_PER_SET[0] <= campioni["punti_per_set"] <= PUNTI_PER_SET[1]),
        (f"falli per punto {numero(campioni['falli_per_punto'])}, almeno {numero(FALLI_PER_PUNTO_MINIMI, 1)}", campioni["falli_per_punto"] > FALLI_PER_PUNTO_MINIMI),
        (f"scambi fermati al limite tecnico {campioni['limite_tecnico']}", campioni["limite_tecnico"] == 0),
    ]


def frase_esiti(misure):
    return (f"punti per set {numero(misure['punti_per_set'], 1)}, attacchi per punto {numero(misure['attacchi_per_punto'])}, goal per punto {numero(misure['goal_per_punto'])}, "
            f"falli per punto {numero(misure['falli_per_punto'])}, fuori per punto {numero(misure['fuori_per_punto'], 3)}, palle morte per punto {numero(misure['palle_morte_per_punto'], 3)}, "
            f"colpi deboli per punto {numero(misure['deboli_per_punto'], 4)}, al limite tecnico {misure['limite_tecnico']}, scambio più lungo {misure['piu_lungo']}, "
            f"time-out a incontro {numero(misure['timeout_per_incontro'])}")


def innata_relativa(soggetti, nomi):
    return statistics.fmean(sum(getattr(g, c + "_base") / allenamento.tetto(c) for c in nomi) / len(nomi) for g in soggetti)


def esegui(argomenti, stampa=print):
    """Il giro intero: restituisce le righe del rapporto e il riepilogo dei verdetti."""
    inizio = time.perf_counter()
    taratura = carica_taratura(argomenti.taratura) if argomenti.taratura else TARATURA
    scelte_prove = scelte(argomenti.prove)
    if not argomenti.riferimento and gruppi_mancanti(scelte_prove):
        raise SystemExit("Le prove scelte non giocano tutti i sedici gruppi della taratura del valore: la resa di riferimento si indica con "
                         "--riferimento, quella di un giro intero, per esempio --riferimento 9,07.")
    livelli_scelti = tuple(sorted(argomenti.livelli)) if argomenti.livelli else LIVELLI
    alto = livelli_scelti[-1]
    soggetti, avversari, fascia = soggetti_e_avversari(argomenti.soggetti, argomenti.avversari, argomenti.seme, argomenti.esperienza)
    per_soggetto = max(1, argomenti.incontri // argomenti.soggetti)
    righe = []

    def scrivi(riga):
        righe.append(riga)
        if stampa:
            stampa(riga, flush=True)

    scrivi(f"Giro degli estremi del motore di partita, MESS versione {__version__}, {time.strftime('%Y-%m-%d %H:%M')}"
           + (f", taratura letta da {argomenti.taratura}." if argomenti.taratura else ", taratura di motore/taratura.py."))
    scrivi(f"Soggetti: {len(soggetti)} nati destrimani senza tratti speciali, con la somma pesata fra {numero(fascia[0], 1)} e {numero(fascia[1], 1)}, il trentesimo e il "
           f"settantesimo percentile dei nati del seme {argomenti.seme}, ed esperienza {numero(argomenti.esperienza, 1)}; avversari altri {len(avversari)} nati della "
           f"stessa fascia. Ogni soggetto gioca {per_soggetto} incontri al meglio dei 3 a ogni livello, in tutto {per_soggetto * len(soggetti)}, con gli stessi avversari e "
           f"gli stessi semi, a parti alternate; {argomenti.processi} processi.")
    lavori = [("base", (), None, False)]
    for nome, nomi in scelte_prove:
        lavori.extend((nome, nomi, livello, False) for livello in livelli_scelti)
    lavori.append(("gemelli della fascia", (), None, True))
    lavori.append(("campioni gemelli", allenamento.CARATTERISTICHE, 1.0, True))
    risultati = {}
    # I processi figli ricevono le funzioni per nome: le si prende dal modulo importato col suo nome,
    # perché quelle dello script lanciato direttamente stanno in __main__, come in taratura_valore.py.
    from banco_estremi import gioca_fatica, gioca_prova, prepara
    with ProcessPoolExecutor(max_workers=argomenti.processi, initializer=prepara,
                             initargs=(soggetti, avversari, argomenti.incontri, argomenti.seme, taratura)) as esecutore:
        futuri_fatica = [esecutore.submit(gioca_fatica, su_campioni, argomenti.fatica, argomenti.seme) for su_campioni in (False, True)] if argomenti.fatica else []
        futuri = {esecutore.submit(gioca_prova, nomi, livello, gemello): (nome, nomi, livello, gemello) for nome, nomi, livello, gemello in lavori}
        for futuro, (_nome, nomi, livello, gemello) in futuri.items():
            risultati[(nomi, livello, gemello)] = futuro.result()
        fatica = dict(f.result() for f in futuri_fatica)
    base_lotti, base_esiti = risultati[((), None, False)]
    scrivi(f"Partite giocate in {numero(time.perf_counter() - inizio, 0)} secondi. I soggetti alla loro innata, contro la fascia: rating {numero(rating(base_lotti), 3)}, "
           f"vittorie {numero(vittorie(base_lotti), 1)} per cento, somma pesata media {numero(somma_media(base_lotti), 1)}; {frase_esiti(misure_esiti(base_esiti))}.")
    rese_per_prova = {nomi: rese_della_prova(base_lotti, [risultati[(nomi, livello, False)][0] for livello in livelli_scelti]) for _nome, nomi in scelte_prove}
    riferimento = argomenti.riferimento / 1000.0 if argomenti.riferimento else resa_di_riferimento(rese_per_prova)
    scrivi(f"La resa di riferimento, la media del primo tratto, dall'innata al 30 per cento, sui sedici gruppi della taratura del valore: {numero(1000 * riferimento, 2)} "
           f"millesimi di rating per punto di somma pesata. Le rese che seguono sono in volte quella di riferimento, con l'errore fra parentesi; un tratto è troppo "
           f"sopra {numero(RESA_MASSIMA_RELATIVA, 1)} volte, incerto con l'errore da {numero(ERRORE_MASSIMO_RELATIVO, 1)} in su, saturo sotto {numero(RESA_SATURA_RELATIVA, 1)}.")
    riepilogo = {"troppo": [], "scende": [], "incerto": [], "satura": [], "riferimento": riferimento, "rese": {}}
    for nome, nomi in scelte_prove:
        livelli = [risultati[(nomi, livello, False)][0] for livello in livelli_scelti]
        rese = rese_per_prova[nomi]
        riepilogo["rese"][nome] = rese
        andamento = ", ".join(f"al {round(100 * livello)} rating {'più' if rating(lotti) >= rating(base_lotti) else 'meno'} {numero(abs(rating(lotti) - rating(base_lotti)))} "
                              f"e vittorie {numero(vittorie(lotti), 0)}" for livello, lotti in zip(livelli_scelti, livelli, strict=True))
        tratti = ", ".join(f"fino al {round(100 * livello)} " + ("nessuna" if misura is None else f"{numero(misura[0] / riferimento, 1)} ({numero(misura[1] / riferimento, 1)})")
                           for livello, misura in zip(livelli_scelti, rese, strict=True))
        giudizi = verdetto_dei_tratti(rese, riferimento, livelli_scelti)
        for livello, giudizio in giudizi:
            voce = f"{nome} fino al {round(100 * livello)}"
            if giudizio == "troppo, ma incerto":
                riepilogo["troppo"].append(voce + ", con un errore grande")
            else:
                riepilogo[giudizio].append(voce)
        giudizio_testo = "; ".join(f"{giudizio} fino al {round(100 * livello)}" for livello, giudizio in giudizi) or "niente da segnalare"
        scrivi(f"{nome.capitalize()}, innata media {numero(innata_relativa(soggetti, nomi))} del tetto: {andamento}. Resa per tratto: {tratti}. Verdetto: {giudizio_testo}.")
    scrivi(f"Gli esiti al {round(100 * alto)} per cento, prova per prova, contro la fascia:")
    for nome, nomi in scelte_prove:
        scrivi(f"{nome.capitalize()}: {frase_esiti(misure_esiti(risultati[(nomi, alto, False)][1]))}.")
    gemelli = misure_esiti(risultati[((), None, True)][1])
    campioni = misure_esiti(risultati[(allenamento.CARATTERISTICHE, 1.0, True)][1])
    campioni_lotti = risultati[(allenamento.CARATTERISTICHE, 1.0, True)][0]
    scrivi(f"Due gemelli della fascia, ciascuno contro una copia di sé: {frase_esiti(gemelli)}.")
    scrivi(f"Due campioni gemelli con tutto al 100: vittorie del primo {numero(vittorie(campioni_lotti), 1)} per cento; {frase_esiti(campioni)}.")
    bersagli_campioni = verdetto_dei_campioni(campioni, gemelli)
    scrivi("I bersagli dei campioni gemelli: " + "; ".join(f"{frase}, {'dentro' if dentro else 'FUORI'}" for frase, dentro in bersagli_campioni) + ".")
    riepilogo["campioni"] = all(dentro for _frase, dentro in bersagli_campioni)
    if (allenamento.CARATTERISTICHE, 1.0, False) in risultati:
        tutto = risultati[(allenamento.CARATTERISTICHE, 1.0, False)][0]
        scrivi(f"Il campione con tutto al 100 contro i nati della fascia vince il {numero(vittorie(tutto), 1)} per cento, con un rating di {numero(rating(tutto))}.")
    riepilogo["fatica"] = True
    for su_campioni, righe_fatica in sorted(fatica.items()):
        chi = "i campioni con tutto al 100, poi età, resistenza e costanza del caso" if su_campioni else "i nati della fascia, con età, resistenza e costanza del caso"
        scrivi(f"La sonda della stanchezza a fine quinto set, su {chi}:")
        for riga in righe_fatica:
            scrivi(riga)
            riepilogo["fatica"] = riepilogo["fatica"] and "FUORI" not in riga
    scrivi("Il riepilogo dei bersagli: " + "; ".join((
        f"tratti sopra {numero(RESA_MASSIMA_RELATIVA, 1)} volte la resa di riferimento: " + (", ".join(riepilogo["troppo"]) or "nessuno"),
        "tratti in cui il rating scende oltre il rumore: " + (", ".join(riepilogo["scende"]) or "nessuno"),
        "tratti con un errore troppo grande per giudicare: " + (", ".join(riepilogo["incerto"]) or "nessuno"),
        "campioni gemelli: " + ("dentro" if riepilogo["campioni"] else "FUORI"),
        "stanchezza a fine quinto set: " + ("dentro" if riepilogo["fatica"] else "FUORI" if fatica else "non misurata"),
    )) + ".")
    scrivi("Le caratteristiche che si saturano, da annotare e non da correggere, perché agli estremi rendono meno della metà del loro peso: "
           + (", ".join(riepilogo["satura"]) or "nessuna") + ".")
    scrivi(f"Giro completato in {numero(time.perf_counter() - inizio, 0)} secondi.")
    return righe, riepilogo


def main():
    parser = argparse.ArgumentParser(description="Il giro degli estremi del motore di MESS: le caratteristiche portate fino al tetto, contro la fascia mediana dei nati.")
    parser.add_argument("--incontri", type=int, default=2000, help="gli incontri per livello di ogni prova, 2000 se non indicato")
    parser.add_argument("--soggetti", type=int, default=200, help="quanti soggetti, 200 se non indicato")
    parser.add_argument("--avversari", type=int, default=400, help="quanti avversari, 400 se non indicato")
    parser.add_argument("--seme", type=int, default=5, help="il seme dei nati e degli incontri, 5 se non indicato")
    parser.add_argument("--esperienza", type=lambda t: float(t.replace(",", ".")), default=0.0, help="l'esperienza di soggetti e avversari, 0 come i nati se non indicata")
    parser.add_argument("--prove", default="tutte", help="tutte, colpi, oppure i nomi delle prove separati da virgole")
    parser.add_argument("--livelli", type=lambda t: float(t.replace(",", ".")), nargs="+", default=None,
                        help="i livelli del tetto a cui portare le caratteristiche, quelli del progetto se non indicati, per le prove veloci")
    parser.add_argument("--fatica", type=int, default=400, help="gli incontri al meglio dei 5 per ogni caso della sonda della stanchezza, 400 se non indicato; 0 la salta")
    parser.add_argument("--taratura", type=Path, default=None, help="un file JSON di sostituzioni della taratura del motore")
    parser.add_argument("--riferimento", type=lambda t: float(t.replace(",", ".")), default=None,
                        help="la resa di riferimento in millesimi di rating, presa da un giro intero, per le prove scelte senza i sedici gruppi")
    parser.add_argument("--processi", type=int, default=min(8, os.cpu_count() or 1), help="quanti processi giocano, fino a 8 se il computer li ha")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il rapporto anche in questo file")
    argomenti = parser.parse_args()
    righe, _riepilogo = esegui(argomenti)
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
