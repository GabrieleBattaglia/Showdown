"""
I mondi sintetici di MESS, comuni agli strumenti di misura e alle impronte delle prove.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con la tappa 12, punto 1.5 del progetto. Qui si spostano da
strumenti/carriera_perfetta.py, che li importa da qui, i nati del generatore vero, l'allenamento
sintetico a passi di un anno e il mondo sintetico, nato della tappa 11: i giocatori in attività di
un mondo nato da un certo numero di anni, o a regime, ciascuno allenato dal suo ingresso secondo la
sua indole. Accanto nascono tre cose nuove.
Il mondo a regime: un Mondo vero, con i giocatori attivi e ritirati del mondo sintetico e le
polisportive del computer piene, su cui strumenti/profilo_giorno.py misura il giorno simulato e
tests/test_identita_motore.py prende la sua impronta. Soltanto lì ci sono giocatori nel declino e
abbastanza polisportive del computer da muovere il mercato.
Il mondo nato: quello che nasce con un seme, sempre lo stesso giorno, dai 50 giocatori del primo
avvio, e avanza giorno per giorno come nel programma, sul modello di strumenti/simulazione_lunga.py.
L'impronta del mondo: il salvataggio composto da archivio.py, tolti gli istanti del mondo reale e
le versioni del programma, in un'impronta SHA-256. Due mondi con la stessa impronta sono uguali fino
all'ultimo bit di ogni numero: è la prova che un'accelerazione non cambia niente.
Niente qui scrive nel progetto: chi fa avanzare un mondo sposta prima la cartella del programma,
come fanno gli strumenti e le prove, perché le uscite di scena scrivono nel registro delle vecchie glorie.
"""

import datetime
import hashlib
import json
import math
import random
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import allenamento  # noqa: E402
import archivio  # noqa: E402
import costanti  # noqa: E402
import esperienza  # noqa: E402
import tratti  # noqa: E402
from modelli import Giocatore, Polisportiva  # noqa: E402
from mondo import DURATA_TICK, Mondo  # noqa: E402

NASCITA = datetime.datetime(2026, 1, 1)  # noqa: DTZ001 - data segnaposto, come quelle del motore
GIORNI_ANNO = costanti.ANNO_SIMULAZIONE_GIORNI
FATTORE_GRUPPO = 1.0 + costanti.K_GRUPPO_ESPERIENZA * 5.0 / costanti.ESPERIENZA_MASSIMA
# Il giorno da cui parte il mondo a regime: un anno lontano, come se il mondo girasse da settant'anni.
# Il 27 gennaio, perché anche dieci giorni simulati passino da un primo del mese, con sponsor,
# stipendi, contratti e calo dei livelli alti.
DATA_REGIME = datetime.datetime(2096, 1, 27, 9, 0)  # noqa: DTZ001 - data simulata, come tutte quelle del mondo
# Le polisportive del computer del mondo a regime: la cassa mediana dei bersagli dell'economia, e la
# data di fondazione abbastanza lontana perché possano anche chiudere, come nel mondo vero.
CASSA_REGIME = 5000
GIORNI_DI_VITA_POLISPORTIVE = 400
# Del mondo sintetico a regime passa il 36 per cento circa dei nati, perché gli altri si sarebbero
# già ritirati, sarebbero morti o usciti di scena: tre candidati e mezzo per giocatore bastano.
CANDIDATI_PER_GIOCATORE_A_REGIME = 3.5
# Il mondo nato parte sempre lo stesso giorno, come quello della simulazione lunga, così i primi del
# mese cadono negli stessi giorni simulati qualunque giorno lo si faccia nascere.
NASCITA_DEL_MONDO = datetime.datetime(2026, 1, 1, 9, 0, tzinfo=datetime.UTC)
# I campi del salvataggio che dicono il mondo reale e non quello simulato: l'ora del salvataggio,
# l'ancora dell'ultimo avanzamento, gli istanti di nascita e dell'ultimo movimento, e le versioni del
# programma, che cambiano a ogni rilascio senza cambiare il mondo.
CAMPI_DEL_MONDO_REALE = ("salvato", "versione", "ultimo_avanzamento")
CAMPI_REALI_GIOCATORE = ("datacreazione_reale", "versione")
CAMPI_REALI_POLISPORTIVA = ("datacreazione_reale", "datetime_ultimo_movimento", "versione_creazione")
# L'esperienza delle gare di un tesserato del computer per anno d'età, dalla tappa 12, punto 6.4 del
# progetto: con le fonti nuove l'esperienza del club scende, e senza le gare il mondo sintetico
# avrebbe il 60 per cento d'esperienza in meno di quello vero. Una stima ai ritmi di regime: un
# torneo ogni 61 giorni, cioè 1,8 tornei per anno d'età, ciascuno con circa 3,5 incontri, una fase e
# mezza superata e un piazzamento medio, circa 0,08 d'esperienza a torneo, e qualche sfida.
ESPERIENZA_GARE_PER_ANNO = 0.15


def nati(quanti, seme, primo_id=1):
    """I nati del generatore vero, col caso del mondo seminato e poi rimesso com'era; ipovedenti come nel mondo."""
    stato = random.getstate()
    random.seed(seme)
    try:
        return [Giocatore(primo_id + i, NASCITA, ipovedente=random.uniform(0, 100) < costanti.PROBABILITA_IPOVEDENTE_CREAZIONE) for i in range(quanti)]
    finally:
        random.setstate(stato)


def allena_a_passi(g, da, a, punti_al_giorno, programma, in_polisportiva=True, amichevoli_al_giorno=0.0, passo=1.0):
    """
    L'allenamento sintetico, a passi di un anno: i punti del passo, spesi secondo il programma
    all'età di metà passo, il calo dei livelli alti, il declino dai 50 anni; l'esperienza dalle sue fonti.
    """
    anni = da
    per_anno = costanti.ESPERIENZA_PER_ANNO_DI_VITA + (esperienza.ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * GIORNI_ANNO * FATTORE_GRUPPO if in_polisportiva else 0.0)
    per_anno += amichevoli_al_giorno * GIORNI_ANNO * costanti.ESPERIENZA_PER_AMICHEVOLE
    while anni < a - 1e-9:
        tratto = min(passo, a - anni)
        giorni = tratto * GIORNI_ANNO
        g.eta = int((anni + tratto / 2) * GIORNI_ANNO)
        g.punti_allenamento += punti_al_giorno * giorni
        allenamento.allena_secondo_programma(g, programma=programma)
        allenamento.mantenimento_del_mese(g, giorni)
        # Nel mondo l'oblio dell'apprendista rapido scatta il primo di ogni mese, e un anno d'età ne ha
        # circa tre e mezzo: mantenimento_del_mese l'ha applicato una volta, qui si aggiungono gli
        # altri mesi del passo. Prima della revisione della tappa 11 l'apprendista dei mondi sintetici
        # dimenticava una volta all'anno invece che a ogni mese.
        oblio = tratti.oblio_mensile(g) ** (giorni / costanti.GIORNI_PER_MESE - 1.0)
        if oblio != 1.0:
            for c in allenamento.CARATTERISTICHE:
                setattr(g, c + "_allenata", getattr(g, c + "_allenata") * oblio)
        g.esperienza = min(costanti.ESPERIENZA_MASSIMA, g.esperienza + per_anno * tratto)
        g.eta = int((anni + tratto) * GIORNI_ANNO)
        if anni + tratto > 50.0:
            g._applica_declino_aggregato(int(giorni))
        anni += tratto
    g.aggiorna_icv()
    return g


def mondo_sintetico(quanti, anni_mondo, seme, primo_id=100_000, candidati=None):
    """
    I giocatori in attività di un mondo nato anni_mondo anni fa, o a regime con None: ingresso fra 9
    e 45 anni, ritiro fra 58 e 75, morte fra 70 e 103, l'uscita prematura; ciascuno si allena dal
    suo ingresso secondo la sua indole, il 90 per cento dei giorni da tesserato. I nati candidati
    sono il doppio dei giocatori chiesti, se non si dice altro: a regime ne passa poco più di un
    terzo, e chi ne vuole tanti ne chiede di più.
    """
    rng = random.Random(f"sintetico-{seme}-{anni_mondo}")
    candidati = nati(quanti * 2 if candidati is None else candidati, seme, primo_id)
    uscita_annua = costanti.PROB_USCITA_PREMATURA_GIORNALIERA / 100.0 * GIORNI_ANNO
    giocatori = []
    for g in candidati:
        if len(giocatori) >= quanti:
            break
        ingresso = rng.uniform(costanti.ETA_MIN_CREAZIONE_ANNI, costanti.ETA_MAX_CREAZIONE_ANNI)
        da_quanto = rng.uniform(0, anni_mondo if anni_mondo is not None else 95.0)
        ritiro, morte = rng.uniform(costanti.ETA_MIN_RITIRO_ANNI, costanti.ETA_MAX_RITIRO_ANNI), rng.uniform(costanti.ETA_MIN_MORTE_ANNI, costanti.ETA_MAX_MORTE_ANNI)
        eta = ingresso + da_quanto
        if eta >= ritiro or eta >= morte or rng.random() > math.exp(-uscita_annua * da_quanto):
            continue
        g.eta = int(ingresso * GIORNI_ANNO)
        allena_a_passi(g, ingresso, eta, 0.9 * costanti.PA_SEDUTA + 0.1 * costanti.PA_SEDUTA * costanti.QUOTA_SEDUTA_LIBERI, g.indole, passo=1.0)
        per_anno = costanti.ESPERIENZA_PER_ANNO_DI_VITA + 0.9 * (esperienza.ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * GIORNI_ANNO * FATTORE_GRUPPO + ESPERIENZA_GARE_PER_ANNO)
        g.esperienza = min(costanti.ESPERIENZA_MASSIMA, da_quanto * per_anno)
        giocatori.append(g)
    return giocatori


def mondo_a_regime(attivi, ritirati, polisportive, seme, data=DATA_REGIME, per_polisportiva=costanti.MAX_TESSERATI_POLISPORTIVA):
    """
    Un Mondo a regime: attivi più ritirati giocatori del mondo sintetico a regime, dove i ritirati
    sono i più anziani, e tante polisportive del computer, ciascuna con per_polisportiva tesserati
    presi a caso fra gli attivi, cassa di 5.000 euro e un contratto firmato il giorno indicato. Le
    età del ritiro e della morte si spostano in là di qualche anno, così nei giorni misurati il mondo
    resta della grandezza chiesta, salvo le uscite premature. Non tocca il caso del mondo.
    Restituisce il mondo; ValueError se il mondo sintetico non dà abbastanza giocatori.
    """
    giocatori = mondo_sintetico(attivi + ritirati, None, seme, candidati=int((attivi + ritirati) * CANDIDATI_PER_GIOCATORE_A_REGIME))
    if len(giocatori) < attivi + ritirati:
        raise ValueError(f"Il mondo sintetico del seme {seme} dà {len(giocatori)} giocatori, non {attivi + ritirati}.")
    anziani = {g.id for g in sorted(giocatori, key=lambda g: (-g.eta, g.id))[:ritirati]}
    mondo = Mondo()
    mondo.datetime_corrente_simulazione = data
    mondo.datetime_ultimo_run_reale = data.replace(tzinfo=datetime.UTC)
    for g in giocatori:
        if g.id in anziani:
            g.ritirato = True
            g.etaritiro = min(g.etaritiro, g.eta)
            g.etamorte = max(g.etamorte, g.eta + 2000)
        else:
            g.etaritiro = max(g.etaritiro, g.eta + 400)
            g.etamorte = max(g.etamorte, g.etaritiro + 400)
        mondo.giocatori[g.id] = g
    mondo.prossimo_id = max(mondo.giocatori) + 1
    disponibili = [g for g in giocatori if not g.ritirato]
    random.Random(f"regime-{seme}").shuffle(disponibili)
    fondazione = data - datetime.timedelta(days=GIORNI_DI_VITA_POLISPORTIVE)
    stato = random.getstate()
    try:
        prossimo = 0
        for n in range(polisportive):
            poli = Polisportiva(nome=f"PoliTeam{n + 1:02d} Sintetica", password=None, datetime_creazione_sim=fondazione, is_cpu_controlled=True)
            poli.cassa = CASSA_REGIME
            mondo.polisportive[poli.nome] = poli
            for g in disponibili[prossimo:prossimo + per_polisportiva]:
                mondo._entra(poli, g, data)
            prossimo += per_polisportiva
    finally:
        random.setstate(stato)
    mondo.aggiorna_stato_polisportive(annuncia=False)
    return mondo


def mondo_nato(seme, giorni=0, ogni_giorno=None):
    """
    Il mondo che nasce col seme dato, sempre lo stesso giorno e dai giocatori del primo avvio, e che
    avanza di tanti giorni simulati come nel programma, un avanzamento alla volta. Gli orologi
    dell'archivio si fermano sul giorno della nascita, e il caso del mondo si rimette com'era alla
    fine. Con ogni_giorno, una funzione, la chiama dopo ogni giorno col mondo, il numero del giorno e
    il riepilogo. La cartella del programma la sposta chi chiama.
    """
    orologi_veri = archivio.adesso, archivio.adesso_utc
    stato = random.getstate()
    archivio.adesso = lambda: NASCITA_DEL_MONDO.replace(tzinfo=None)
    archivio.adesso_utc = lambda: NASCITA_DEL_MONDO
    try:
        random.seed(seme)
        mondo = Mondo()
        archivio._fai_nascere(mondo)
        for giorno in range(1, giorni + 1):
            rapporto = mondo.processa_tempo_trascorso(mondo.datetime_ultimo_run_reale + DURATA_TICK)
            if ogni_giorno is not None:
                ogni_giorno(mondo, giorno, rapporto)
    finally:
        archivio.adesso, archivio.adesso_utc = orologi_veri
        random.setstate(stato)
    return mondo


def avanza_un_giorno(mondo):
    """Un giorno simulato del mondo, col caso del mondo così com'è: la data cresce di uno, come nel programma. Restituisce il riepilogo."""
    data = mondo.datetime_corrente_simulazione + datetime.timedelta(days=1)
    mondo.datetime_corrente_simulazione = data
    rapporto = mondo.rapporto_vuoto(data)
    mondo._un_giorno(data, rapporto)
    return rapporto


def avanza(mondo, giorni, seme):
    """
    Fa avanzare un mondo di tanti giorni simulati, col caso del mondo seminato e poi rimesso
    com'era, un giorno alla volta. Restituisce i riepiloghi dei giorni. La cartella del programma
    la sposta chi chiama.
    """
    stato = random.getstate()
    try:
        random.seed(seme)
        return [avanza_un_giorno(mondo) for _ in range(giorni)]
    finally:
        random.setstate(stato)


def documento_senza_istanti_reali(mondo):
    """Il salvataggio del mondo come lo compone l'archivio, senza gli istanti del mondo reale né le versioni del programma."""
    documento = archivio.componi(mondo)
    for campo in CAMPI_DEL_MONDO_REALE:
        documento.pop(campo, None)
        documento["mondo"].pop(campo, None)
    for g in documento["mondo"]["giocatori"]:
        for campo in CAMPI_REALI_GIOCATORE:
            g.pop(campo, None)
    for p in documento["mondo"]["polisportive"].values():
        for campo in CAMPI_REALI_POLISPORTIVA:
            p.pop(campo, None)
    return documento


def impronta_del_mondo(mondo):
    """L'impronta SHA-256 del mondo, tolti gli istanti reali: la forma canonica del documento, con ogni numero scritto per intero."""
    canonico = json.dumps(documento_senza_istanti_reali(mondo), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def riassunto_del_mondo(mondo):
    """Quattro numeri che aiutano a capire un'impronta cambiata: giocatori vivi, attivi, tesserati e polisportive."""
    morti = mondo._ids_morti_processati_sessione
    vivi = [g for gid, g in mondo.giocatori.items() if gid not in morti]
    attivi = [g for g in vivi if not g.ritirato]
    return {"vivi": len(vivi), "attivi": len(attivi), "tesserati": sum(1 for g in attivi if g.appartenenza != "*"), "polisportive": len(mondo.polisportive)}
