"""
La taratura dell'esito rapido di MESS sul motore vero, tappa 12, punto 6.4 del progetto.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13. Lo strumento gioca col motore, in modalità essenziale, migliaia di incontri fra
giocatori di tre popolazioni, la popolazione di prova del banco e i mondi sintetici all'anno 10 e a
regime: il 60 per cento delle coppie a caso e il 40 vicine di forza, l'80 per cento al meglio dei 3
e il 20 dei 5, e in un incontro su dieci uno dei due con un acciacco. Da ogni scambio che assegna
punti prende chi l'ha vinto, chi batteva, e se con un goal o con un fallo, con le azioni stimate di
ciascuno fino a lì; una regressione logistica ai minimi quadrati ripesati, con un poco di
regolarizzazione, dà i pesi della forza, quelli dei tratti, il peso della lettura, la pendenza, il
peso della fatica e il vantaggio della battuta; una seconda dà la quota dei goal. La gara a squadre
si tara a parte, sulle gare a squadre del motore. Poi la verifica, su altre coppie e altri semi,
giocate col motore e con l'esito rapido: la vittoria del favorito per fascia di distacco, come nel
banco delle partite, i punti per set, i set oltre i 12 punti, i risultati in set, gli infortuni.
Non scrive niente nel progetto; stampa il blocco da copiare nei predefiniti di TaraturaRapida, in
esito_rapido.py, e con --rapporto scrive la carta della taratura.
La taratura fine del passo 4, il 14 ottobre 2026, ha aggiunto tre cose. Il ritocco della pendenza:
la regressione sugli scambi tratta ogni scambio da solo, e quello che lega gli scambi dello stesso
incontro, le differenze fra i due giocatori che la forza lineare non vede, la fa uscire un poco più
piatta del vero, così il favorito vinceva da 2 a 4 punti meno che col motore; ora la pendenza si
moltiplica per il fattore che rimette al loro posto le vittorie del favorito sugli incontri della
taratura stessa, rigiocati con l'esito rapido, e lo stesso per la gara a squadre. La verifica
completa del punto 6.4, con tutti i suoi bersagli: le fasce del favorito, i residui per indole, per
tratto, per fascia d'età, per le coppie miste e per gli acciaccati, i punti per set e i set lunghi,
i risultati in set, i forti alla pari, la sonda della stanchezza al meglio dei 5, infortuni, acciacchi
e ritiri, e la gara a squadre; ogni bersaglio dice dentro o FUORI, e per i residui, che sui gruppi
piccoli oscillano molto, anche quanto vale il rumore. E la popolazione di un mondo simulato, punto
13.5: con --popolazione si aggiunge quella che strumenti/simulazione_lunga.py --salva-popolazione ha
scritto, e con --solo-verifica la si gioca contro i numeri di adesso, senza ritarare.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/taratura_esito_rapido.py --veloce
    python strumenti/taratura_esito_rapido.py --incontri 20000 --squadre 4000 --processi 6 --rapporto strumenti/taratura_esito_rapido.txt
    python strumenti/taratura_esito_rapido.py --solo-verifica --popolazione anno_20.json.gz --processi 6
"""

import argparse
import concurrent.futures
import copy
import dataclasses
import gzip
import itertools
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
for _cartella in (RADICE, RADICE / "strumenti"):
    if str(_cartella) not in sys.path:
        sys.path.insert(0, str(_cartella))

import numpy as np  # noqa: E402
import popolazione_di_prova as pp  # noqa: E402
from banco_partite import FASCE_DISTACCO, distacco, indice_del_distacco  # noqa: E402
from mondi_sintetici import mondo_sintetico  # noqa: E402

import costanti  # noqa: E402
import esito_rapido  # noqa: E402
import infortuni  # noqa: E402
from costanti import ACCIACCO_CALO_MASSIMO, ACCIACCO_CALO_MINIMO, CARATTERISTICHE_VALORE  # noqa: E402
from modelli import Giocatore  # noqa: E402
from motore import ESSENZIALE, SQUADRE, TARATURA, Squadra, formato_singolare, simula_incontro  # noqa: E402
from motore.campo import lettura_possibile, ritmo_della_fatica  # noqa: E402
from motore.squadre import composizione_valida  # noqa: E402

TRATTI = esito_rapido.TRATTI_RAPIDI
QUOTA_VICINE = 0.4
QUOTA_CINQUE = 0.2
QUOTA_ACCIACCATI = 0.1
RIDGE = 1.0
# I fattori del ritocco della pendenza, da 0,9 a 1,6.
RITOCCHI = tuple(round(0.9 + 0.025 * i, 3) for i in range(29))
# I bersagli del punto 6.4 del progetto: lo scarto massimo dal motore, in punti percentuali dove non si dice altro.
SCARTO_FASCIA = 2.0
SCARTO_RESIDUI = 3.0
SCARTO_PUNTI_SET = 0.3
SCARTO_OLTRE_12 = 1.5
SCARTO_RISULTATI = 3.0
SCARTO_FATICA = 4.0
SCARTO_INFORTUNI = 0.05
SCARTO_SQUADRE = 3.0
SCARTO_PUNTI_SQUADRE = 1.0
# Sotto questi incontri una fascia o un gruppo si dicono ma non si giudicano.
MINIMO_PER_GIUDICARE = 150
# Il primo identificativo dei giocatori letti con --popolazione, perché non si confondano con quelli delle altre popolazioni.
PRIMO_ID_SALVATI = 1_000_000


def numero(valore, decimali=1):
    return f"{valore:.{decimali}f}".replace(".", ",")


def esito(scarto, massimo, errore=0.0):
    """
    Dentro se lo scarto sta nel bersaglio; dentro col rumore se ci sta togliendo una volta l'errore
    della misura; altrimenti FUORI. Fino alla revisione del 14 ottobre 2026 si toglievano due errori, e
    il bersaglio di 2 punti diventava di 4.
    """
    if abs(scarto) <= massimo:
        return "dentro"
    if errore and abs(scarto) - errore <= massimo:
        return "dentro col rumore"
    return "FUORI"


def scarto_appaiato(voci, vince_motore, vince_rapido):
    """Lo scarto del favorito, esito rapido meno motore sugli stessi incontri, in punti percentuali, con l'errore appaiato della media."""
    d = [(vince_rapido(v) == v["favorito"]) - (vince_motore(v) == v["favorito"]) for v in voci]
    if len(d) < 2:
        return 0.0, 0.0
    return 100.0 * statistics.fmean(d), 100.0 * statistics.pstdev(d) / math.sqrt(len(d))


# Le popolazioni.

def popolazioni(quanti):
    """I giocatori delle tre popolazioni, che possono giocare, con identificativi diversi."""
    prova = [g for g in pp.genera(quanti, 7, primo_id=1) if g.puo_giocare]
    anno_10 = [g for g in mondo_sintetico(quanti, 10, 2026, primo_id=200_000) if g.puo_giocare]
    regime = [g for g in mondo_sintetico(quanti, None, 2027, primo_id=400_000, candidati=int(quanti * 3.5)) if g.puo_giocare]
    return prova + anno_10 + regime


def popolazione_salvata(percorso, quanti=None, seme=1, spostamento=PRIMO_ID_SALVATI):
    """
    I giocatori in attività che strumenti/simulazione_lunga.py --salva-popolazione ha scritto, che possono
    giocare, con gli identificativi spostati; con quanti, un campione a caso di quella grandezza.
    """
    with gzip.open(percorso, "rt", encoding="utf-8") as f:
        dati = json.load(f)
    giocatori = []
    for voce in dati["giocatori"]:
        g = Giocatore.da_dizionario(voce)
        g.id += spostamento
        if g.puo_giocare:
            giocatori.append(g)
    if quanti and len(giocatori) > quanti:
        giocatori = random.Random(f"salvati-{seme}").sample(giocatori, quanti)
    return giocatori, dati.get("data_simulata", "")


def coppie(giocatori, quante, seme):
    """Le coppie: il 60 per cento a caso e il 40 vicine di forza; il formato, il seme dell'incontro e l'eventuale acciaccato con il suo calo."""
    rng = random.Random(f"coppie-{seme}")
    per_valore = sorted(giocatori, key=lambda g: g.indice_collettivo_valore)
    risultato = []
    for _ in range(quante):
        if rng.random() < QUOTA_VICINE:
            i = rng.randrange(len(per_valore) - 1)
            j = min(len(per_valore) - 1, i + 1 + rng.randrange(8))
            a, b = per_valore[i], per_valore[j]
            if rng.random() < 0.5:
                a, b = b, a
        else:
            a, b = rng.sample(giocatori, 2)
        set_al_meglio = 5 if rng.random() < QUOTA_CINQUE else 3
        acciaccato = None
        if rng.random() < QUOTA_ACCIACCATI:
            acciaccato = ((a if rng.random() < 0.5 else b).id, rng.uniform(ACCIACCO_CALO_MINIMO, ACCIACCO_CALO_MASSIMO))
        risultato.append((a.id, b.id, set_al_meglio, rng.getrandbits(63), acciaccato))
    return risultato


def squadre_a_caso(giocatori, quante, seme):
    """Le gare a squadre: due di un sesso e uno dell'altro, con una riserva a testa, e il seme."""
    rng = random.Random(f"squadre-{seme}")
    uomini = [g for g in giocatori if g.sesso == "m"]
    donne = [g for g in giocatori if g.sesso == "f"]
    gare = []
    while len(gare) < quante:
        scelti = []
        for _ in range(2):
            if rng.random() < 0.5:
                squadra = rng.sample(uomini, 2) + rng.sample(donne, 1) + [rng.choice(uomini + donne)]
            else:
                squadra = rng.sample(donne, 2) + rng.sample(uomini, 1) + [rng.choice(uomini + donne)]
            scelti.append(squadra)
        ids = [g.id for s in scelti for g in s]
        if len(set(ids)) != len(ids) or not all(composizione_valida(s[:3]) for s in scelti):
            continue
        gare.append(([g.id for g in scelti[0]], [g.id for g in scelti[1]], rng.getrandbits(63)))
    return gare


# Il lavoro di un processo: gli incontri del motore, e se serve dell'esito rapido.

_GIOCATORI = {}


def _prepara(dizionari):
    _GIOCATORI.clear()
    for dati in dizionari:
        g = Giocatore.da_dizionario(dati)
        _GIOCATORI[g.id] = g


def _basi(*giocatori):
    return {g.id: infortuni.probabilita_base(g) for g in giocatori}


def _riassunto(r):
    return {"vincitore": r.vincitore, "set": [list(s) for s in r.set], "esito": r.esito, "set_giocati": r.set_giocati, "infortuni": len(r.infortuni),
            "acciacchi": len(r.acciacchi)}


def gioca_singolari(lavori, rapido_anche, taratura_dati):
    taratura = esito_rapido.TaraturaRapida(**taratura_dati) if taratura_dati else None
    uscita = []
    for id_a, id_b, set_al_meglio, seme, acciaccato in lavori:
        a, b = _GIOCATORI[id_a], _GIOCATORI[id_b]
        cali = {acciaccato[0]: acciaccato[1]} if acciaccato else None
        formato = formato_singolare(set_al_meglio)
        r = simula_incontro(a, b, formato, seme=seme, dettaglio=ESSENZIALE, basi_infortunio=_basi(a, b), cali=cali)
        voce = {"a": id_a, "b": id_b, "formato": set_al_meglio, "cali": cali or {}, **_riassunto(r),
                "azioni": (r.statistiche[id_a].azioni + r.statistiche[id_b].azioni) / 2.0, "attacchi": (r.statistiche[id_a].attacchi + r.statistiche[id_b].attacchi) / 2.0,
                "penalita": sum(1 for s in r.incontro.sanzioni if s[3] == "penalita"),
                "scambi": [(p.a_chi, p.parte_battitore, p.esito == "goal") for p in r.punti if p.punti > 0]}
        if rapido_anche:
            rr = esito_rapido.gioca(a, b, formato, seme, basi_infortunio=_basi(a, b), cali=cali, taratura=taratura)
            voce["rapido"] = _riassunto(rr)
            voce.pop("scambi")
        uscita.append(voce)
    return uscita


def gioca_gare(lavori, rapido_anche, taratura_dati):
    taratura = esito_rapido.TaraturaRapida(**taratura_dati) if taratura_dati else None
    uscita = []
    for ids_a, ids_b, seme in lavori:
        sa = Squadra("A", tuple(_GIOCATORI[i] for i in ids_a))
        sb = Squadra("B", tuple(_GIOCATORI[i] for i in ids_b))
        r = simula_incontro(sa, sb, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        voce = {"a": ids_a, "b": ids_b, "vincitore": r.vincitore, "set": [list(s) for s in r.set],
                "scambi": [(p.battitore, p.ricevitore, p.a_chi, p.parte_battitore, p.esito == "goal") for p in r.punti if p.punti > 0]}
        if rapido_anche:
            rr = esito_rapido.gioca_squadre(sa, sb, seme, taratura=taratura)
            voce["rapido"] = {"vincitore": rr.vincitore, "set": [list(s) for s in rr.set]}
            voce.pop("scambi")
        uscita.append(voce)
    return uscita


def _lavora(funzione, dizionari, lavori, rapido_anche, taratura_dati):
    _prepara(dizionari)
    return funzione(lavori, rapido_anche, taratura_dati)


def in_parallelo(funzione, giocatori, lavori, processi, rapido_anche=False, taratura=None):
    """Divide i lavori fra i processi, ciascuno con i giocatori in dizionari, e rimette i risultati in ordine."""
    dizionari = [g.a_dizionario() for g in giocatori]
    taratura_dati = dataclasses.asdict(taratura) if taratura is not None else None
    if processi <= 1:
        return _lavora(funzione, dizionari, lavori, rapido_anche, taratura_dati)
    pezzi = [lavori[i::processi] for i in range(processi)]
    with concurrent.futures.ProcessPoolExecutor(max_workers=processi) as esecutore:
        risultati = list(esecutore.map(_lavora, [funzione] * processi, [dizionari] * processi, pezzi, [rapido_anche] * processi, [taratura_dati] * processi))
    uscita = [None] * len(lavori)
    for i, pezzo in enumerate(risultati):
        for j, voce in enumerate(pezzo):
            uscita[i + j * processi] = voce
    return uscita


# Le regressioni.

def logistica(X, y, ridge=RIDGE, giri=40):
    """La regressione logistica ai minimi quadrati ripesati, con la regolarizzazione indicata, senza intercetta se X non ce l'ha."""
    beta = np.zeros(X.shape[1])
    identita = np.eye(X.shape[1]) * ridge
    for _ in range(giri):
        z = X @ beta
        p = 1.0 / (1.0 + np.exp(-z))
        w = p * (1.0 - p)
        gradiente = X.T @ (y - p) - ridge * beta
        hessiana = X.T @ (X * w[:, None]) + identita
        passo = np.linalg.solve(hessiana, gradiente)
        beta += passo
        if np.max(np.abs(passo)) < 1e-9:
            break
    return beta


def _profilo(g):
    """Quello che serve di un giocatore alla regressione: i livelli, i tratti, la lettura e il ritmo della fatica diviso la scala."""
    livelli = esito_rapido.livelli(g)
    return (np.array([livelli[c] for c in CARATTERISTICHE_VALORE]), np.array([1.0 if getattr(g, t, False) else 0.0 for t in TRATTI]),
            lettura_possibile(g, TARATURA), ritmo_della_fatica(g, TARATURA) / TARATURA.FATICA_SCALA)


def _efficienza(azioni, k):
    return 1.0 - TARATURA.FATICA_MAX * (1.0 - math.exp(-((azioni * k) ** TARATURA.FORMA_FATICA)))


def tara_singolari(voci, profili):
    """Le due regressioni dei singolari; restituisce i numeri della taratura che ne vengono e le caratteristiche col peso negativo."""
    azioni_per_scambio = sum(v["azioni"] for v in voci) / sum(len(v["scambi"]) for v in voci)
    attacchi_per_scambio = sum(v["attacchi"] for v in voci) / sum(len(v["scambi"]) for v in voci)
    righe, esiti = [], []
    for v in voci:
        la, ta, letta, ka = profili[v["a"]]
        lb, tb, lettb, kb = profili[v["b"]]
        resa_a, resa_b = 1.0 - v["cali"].get(v["a"], 0.0), 1.0 - v["cali"].get(v["b"], 0.0)
        base = np.concatenate([la - lb, ta - tb, [letta - lettb]])
        for k, (a_chi, batte, _goal) in enumerate(v["scambi"]):
            azioni = azioni_per_scambio * k
            fatica = _efficienza(azioni, ka) * resa_a - _efficienza(azioni, kb) * resa_b
            righe.append(np.concatenate([base, [fatica, 1.0 if batte == "A" else -1.0]]))
            esiti.append(1.0 if a_chi == "A" else 0.0)
    beta = logistica(np.array(righe), np.array(esiti))
    n = len(CARATTERISTICHE_VALORE)
    grezzi = beta[:n]
    negativi = [c for c, b in zip(CARATTERISTICHE_VALORE, grezzi, strict=True) if b < 0]
    grezzi = np.maximum(grezzi, 0.0)
    pendenza = float(np.mean(grezzi)) or 1.0
    pesi = {c: round(float(b / pendenza), 3) for c, b in zip(CARATTERISTICHE_VALORE, grezzi, strict=True)}
    tratti = {t: round(float(b / pendenza), 3) for t, b in zip(TRATTI, beta[n:n + len(TRATTI)], strict=True)}
    lettura = round(float(beta[n + len(TRATTI)] / pendenza), 3)
    k_fatica = round(float(beta[n + len(TRATTI) + 1]), 3)
    vantaggio = round(float(beta[n + len(TRATTI) + 2]), 4)
    parziale = esito_rapido.TaraturaRapida(PESI=pesi, PESI_TRATTI_RAPIDI=tratti, PESO_LETTURA=lettura, PENDENZA=round(pendenza, 4))
    forze = {gid: esito_rapido.forza(_GIOCATORI_PER_FORZA[gid], parziale) for gid in profili}
    righe_goal, goal = [], []
    for v in voci:
        fa, fb = forze[v["a"]], forze[v["b"]]
        for a_chi, _batte, e_goal in v["scambi"]:
            distacco_vincitore = fa - fb if a_chi == "A" else fb - fa
            righe_goal.append([1.0, distacco_vincitore, (fa + fb) / 2.0])
            goal.append(1.0 if e_goal else 0.0)
    gb = logistica(np.array(righe_goal), np.array(goal), ridge=1e-3)
    penalita = sum(v["penalita"] for v in voci) / sum(len(v["scambi"]) + v["penalita"] for v in voci)
    taratura = dataclasses.replace(parziale, K_FATICA=k_fatica, VANTAGGIO_BATTUTA=vantaggio, GOAL_BASE=round(float(gb[0]), 4), GOAL_DISTACCO=round(float(gb[1]), 4),
                                   GOAL_LIVELLO=round(float(gb[2]), 4), PENALITA=round(penalita, 5), AZIONI_PER_SCAMBIO=round(azioni_per_scambio, 3),
                                   ATTACCHI_PER_SCAMBIO=round(attacchi_per_scambio, 3))
    return taratura, negativi


def tara_squadre(voci, profili, taratura):
    """La regressione della gara a squadre, con la forza dei singolari: pendenza, fatica, vantaggio della battuta e quota dei goal."""
    forze = {gid: esito_rapido.forza(_GIOCATORI_PER_FORZA[gid], taratura) for gid in profili}
    righe, esiti, goal = [], [], 0
    for v in voci:
        al_tavolo = {}
        for battitore, ricevitore, a_chi, batte, e_goal in v["scambi"]:
            azioni_b = taratura.AZIONI_PER_SCAMBIO * al_tavolo.get(battitore, 0)
            azioni_r = taratura.AZIONI_PER_SCAMBIO * al_tavolo.get(ricevitore, 0)
            fatica = _efficienza(azioni_b, profili[battitore][3]) - _efficienza(azioni_r, profili[ricevitore][3])
            righe.append([forze[battitore] - forze[ricevitore], fatica, 1.0])
            esiti.append(1.0 if a_chi == batte else 0.0)
            goal += e_goal
            al_tavolo[battitore] = al_tavolo.get(battitore, 0) + 1
            al_tavolo[ricevitore] = al_tavolo.get(ricevitore, 0) + 1
    beta = logistica(np.array(righe), np.array(esiti), ridge=1e-3)
    quota = goal / len(esiti)
    return dataclasses.replace(taratura, PENDENZA_SQUADRE=round(float(beta[0]), 4), K_FATICA_SQUADRE=round(float(beta[1]), 3),
                               VANTAGGIO_BATTUTA_SQUADRE=round(float(beta[2]), 4), GOAL_SQUADRE=round(math.log(quota / (1.0 - quota)), 4))


_GIOCATORI_PER_FORZA = {}


# Il favorito e le fasce.

def favorito_e_distacco(id_a, id_b):
    """Il favorito per l'indice di valore con la scala ferma del banco, A o B, e il distacco in proporzione."""
    ia, ib = indice_del_distacco(_GIOCATORI_PER_FORZA[id_a]), indice_del_distacco(_GIOCATORI_PER_FORZA[id_b])
    return ("A" if ia >= ib else "B"), distacco(ia, ib)


def favorita_e_distacco_squadre(ids_a, ids_b):
    """La squadra favorita per la media dell'indice di valore dei tre titolari, e il distacco in proporzione."""
    ia = statistics.fmean(indice_del_distacco(_GIOCATORI_PER_FORZA[i]) for i in ids_a[:3])
    ib = statistics.fmean(indice_del_distacco(_GIOCATORI_PER_FORZA[i]) for i in ids_b[:3])
    return ("A" if ia >= ib else "B"), distacco(ia, ib)


def _limiti():
    return [0.0] + [f[0] for f in FASCE_DISTACCO if f[0] is not None] + [math.inf]


def per_fascia(voci, vince_motore, vince_rapido, appaiato=False):
    """
    Per ogni fascia di distacco: il nome, gli incontri, e la vittoria del favorito col motore e con
    l'esito rapido, in percentuale; con appaiato anche l'errore appaiato dello scarto.
    """
    uscita = []
    for (basso, alto), (_l, nome, _b) in zip(itertools.pairwise(_limiti()), FASCE_DISTACCO, strict=True):
        fascia = [v for v in voci if basso <= v["distacco"] < alto]
        if fascia:
            motore = 100.0 * sum(1 for v in fascia if vince_motore(v) == v["favorito"]) / len(fascia)
            rapido = 100.0 * sum(1 for v in fascia if vince_rapido(v) == v["favorito"]) / len(fascia)
            if appaiato:
                uscita.append((nome, len(fascia), motore, rapido, scarto_appaiato(fascia, vince_motore, vince_rapido)[1]))
            else:
                uscita.append((nome, len(fascia), motore, rapido))
    return uscita


# Il ritocco della pendenza.

def _gioca_rapido_in_casa(lavoro, taratura, memoria=None):
    id_a, id_b, set_al_meglio, seme, acciaccato = lavoro
    a, b = _GIOCATORI_PER_FORZA[id_a], _GIOCATORI_PER_FORZA[id_b]
    cali = {acciaccato[0]: acciaccato[1]} if acciaccato else None
    return esito_rapido.gioca(a, b, formato_singolare(set_al_meglio), seme, basi_infortunio=_basi(a, b), cali=cali, taratura=taratura, memoria=memoria).vincitore


# Il ritocco a tre fattori: la pendenza della forza, il peso della fatica e, dalla revisione del 14
# ottobre 2026, la pendenza che scende col livello medio dei due. La prima griglia è larga, la seconda
# stringe attorno al migliore della prima.
GRIGLIA_PENDENZA = tuple(round(0.95 + 0.05 * i, 3) for i in range(7))
GRIGLIA_FATICA = tuple(round(1.0 + 0.25 * i, 3) for i in range(7))
GRIGLIA_LIVELLO = tuple(round(0.05 * i, 3) for i in range(9))
# I quarti di livello, che l'errore del ritocco e la verifica guardano fascia per fascia.
QUARTI_DI_LIVELLO = 4


def _gruppi_del_ritocco(v):
    """I gruppi che il ritocco guarda oltre alle fasce: le fasce d'età e gli acciaccati, quelli dove la fatica conta."""
    return {lato: [nome for nome in nomi if nome.startswith("età") or nome == "l'acciaccato"] for lato, nomi in gruppi_dei_residui(v).items()}


def quarti_di_livello(voci):
    """Le soglie dei quarti del livello medio delle coppie, che sta in v["livello"]."""
    livelli = sorted(v["livello"] for v in voci)
    return [livelli[len(livelli) * k // QUARTI_DI_LIVELLO] for k in range(1, QUARTI_DI_LIVELLO)]


def quarto_di(v, soglie):
    return sum(1 for s in soglie if v["livello"] >= s)


def errore_del_ritocco(voci, gruppi, chiave="rapido_prova", soglie=None):
    """
    La somma dei quadrati degli scarti fra motore ed esito rapido, in punti percentuali, pesati per gli
    incontri: le fasce del favorito, formato per formato e, con le soglie, quarto di livello per quarto
    di livello, e i residui delle fasce d'età e degli acciaccati.
    """
    errore = 0.0
    for set_al_meglio in (3, 5):
        gruppo = [v for v in voci if v["formato"] == set_al_meglio]
        for _nome, n, motore, rapido in per_fascia(gruppo, lambda v: v["vincitore"], lambda v, c=chiave: v[c]):
            errore += n * (motore - rapido) ** 2
        if soglie:
            for quarto in range(QUARTI_DI_LIVELLO):
                parte = [v for v in gruppo if quarto_di(v, soglie) == quarto]
                for _nome, n, motore, rapido in per_fascia(parte, lambda v: v["vincitore"], lambda v, c=chiave: v[c]):
                    errore += n * (motore - rapido) ** 2
    differenze = {}
    for v, gruppi_v in zip(voci, gruppi, strict=True):
        for lato, nomi in gruppi_v.items():
            d = (v["vincitore"] == lato) - (v[chiave] == lato)
            for nome in nomi:
                differenze.setdefault(nome, []).append(d)
    for valori in differenze.values():
        errore += len(valori) * (100.0 * statistics.fmean(valori)) ** 2
    return errore


def ritocca_pendenza(voci, lavori, taratura, scrivi):
    """
    I tre fattori che rimettono al loro posto le vittorie: uno sulla pendenza della forza, per il
    favorito, uno sul peso della fatica, per i giovani contro gli anziani e per gli acciaccati, perché
    la regressione sugli scambi li fa uscire tutti e due un poco più piatti del vero, e la pendenza del
    livello, PENDENZA_LIVELLO, perché nel motore il favorito conta meno fra i forti: la revisione del 14
    ottobre 2026 ha visto lo scarto del favorito salire dal quarto più debole al più forte delle coppie,
    da meno 2 a più 5 punti. Il livello di riferimento è la mediana del livello delle coppie. Gli
    incontri della taratura si rigiocano con l'esito rapido per ogni terna di fattori provata, con gli
    stessi semi, e vince la terna con la somma più piccola dei quadrati degli scarti, errore_del_ritocco,
    che guarda anche i quarti di livello: prima su una griglia larga, poi su una stretta attorno alla
    migliore. Restituisce la taratura ritoccata.
    """
    memoria = {}
    for v, lavoro in zip(voci, lavori, strict=True):
        v["favorito"], v["distacco"] = favorito_e_distacco(lavoro[0], lavoro[1])
        v["livello"] = (esito_rapido.forza(_GIOCATORI_PER_FORZA[lavoro[0]], taratura, memoria) + esito_rapido.forza(_GIOCATORI_PER_FORZA[lavoro[1]], taratura, memoria)) / 2.0
    riferimento = round(statistics.median(v["livello"] for v in voci), 2)
    soglie = quarti_di_livello(voci)
    gruppi = [_gruppi_del_ritocco(v) for v in voci]
    provati = {}

    def prova(c1, c2, c3):
        chiave = (round(c1, 4), round(c2, 4), round(c3, 4))
        if chiave not in provati:
            t = dataclasses.replace(taratura, PENDENZA=round(taratura.PENDENZA * c1, 4), K_FATICA=round(taratura.K_FATICA * c2, 3), PENDENZA_LIVELLO=round(c3, 4),
                                    LIVELLO_RIFERIMENTO=riferimento)
            for v, lavoro in zip(voci, lavori, strict=True):
                v["rapido_prova"] = _gioca_rapido_in_casa(lavoro, t, memoria)
            provati[chiave] = errore_del_ritocco(voci, gruppi, soglie=soglie)
        return provati[chiave]

    migliore = min(((c1, c2, c3) for c1 in GRIGLIA_PENDENZA for c2 in GRIGLIA_FATICA for c3 in GRIGLIA_LIVELLO), key=lambda c: prova(*c))
    stretta = [(round(migliore[0] + 0.0125 * i, 4), round(migliore[1] + 0.1 * j, 4), round(migliore[2] + 0.0125 * k, 4))
               for i in range(-2, 3) for j in range(-2, 3) for k in range(-2, 3) if migliore[1] + 0.1 * j > 0 and migliore[2] + 0.0125 * k >= 0]
    migliore = min(stretta, key=lambda c: prova(*c))
    senza = prova(1.0, 1.0, 0.0)
    scrivi(f"Il ritocco sugli incontri della taratura, rigiocati con l'esito rapido per {len(provati)} terne di fattori: la pendenza per {numero(migliore[0], 4)}, il peso "
           f"della fatica per {numero(migliore[1], 3)}, la pendenza del livello {numero(migliore[2], 4)} attorno al livello {numero(riferimento, 2)}; la somma pesata dei "
           f"quadrati degli scarti scende da {numero(senza / len(voci), 2)} senza ritocco a {numero(provati[migliore] / len(voci), 2)} per incontro.")
    for v in voci:
        v.pop("rapido_prova", None)
    return dataclasses.replace(taratura, PENDENZA=round(taratura.PENDENZA * migliore[0], 4), K_FATICA=round(taratura.K_FATICA * migliore[1], 3),
                               PENDENZA_LIVELLO=round(migliore[2], 4), LIVELLO_RIFERIMENTO=riferimento)


def ritocca_pendenza_squadre(gare, lavori, taratura, scrivi):
    """Lo stesso ritocco per la gara a squadre, sulle gare della taratura rigiocate con l'esito rapido."""
    for g, lavoro in zip(gare, lavori, strict=True):
        g["favorito"], g["distacco"] = favorita_e_distacco_squadre(lavoro[0], lavoro[1])
    migliore = None
    for fattore in RITOCCHI:
        prova = dataclasses.replace(taratura, PENDENZA_SQUADRE=round(taratura.PENDENZA_SQUADRE * fattore, 4))
        for g, (ids_a, ids_b, seme) in zip(gare, lavori, strict=True):
            sa = Squadra("A", tuple(_GIOCATORI_PER_FORZA[i] for i in ids_a))
            sb = Squadra("B", tuple(_GIOCATORI_PER_FORZA[i] for i in ids_b))
            g["rapido_prova"] = esito_rapido.gioca_squadre(sa, sb, seme, taratura=prova).vincitore
        errore = sum(n * (motore - rapido) ** 2 for _nome, n, motore, rapido in per_fascia(gare, lambda x: x["vincitore"], lambda x: x["rapido_prova"]))
        if migliore is None or errore < migliore[1]:
            migliore = (fattore, errore)
    for g in gare:
        g.pop("rapido_prova", None)
    scrivi(f"Il ritocco della pendenza della gara a squadre, sulle gare della taratura: il fattore scelto è {numero(migliore[0], 3)}.")
    return dataclasses.replace(taratura, PENDENZA_SQUADRE=round(taratura.PENDENZA_SQUADRE * migliore[0], 4))


# La verifica.

def _set_reali(e):
    return list(e["set"][:e["set_giocati"]])


def misure_dei_set(esiti):
    """Punti medi per set, quota dei set oltre i 12, e la distribuzione dei risultati in set degli incontri regolari."""
    reali = [s for e in esiti for s in _set_reali(e)]
    media = statistics.fmean(a + b for a, b in reali) if reali else 0.0
    oltre = 100.0 * sum(1 for a, b in reali if max(a, b) > 12) / len(reali) if reali else 0.0
    risultati = {}
    for e in esiti:
        if e["esito"] != "regolare":
            continue
        vinti = sum(1 for a, b in e["set"] if a > b)
        chiave = f"{max(vinti, len(e['set']) - vinti)} a {min(vinti, len(e['set']) - vinti)}"
        risultati[chiave] = risultati.get(chiave, 0) + 1
    regolari = sum(risultati.values()) or 1
    return media, oltre, {k: 100.0 * n / regolari for k, n in risultati.items()}


def gruppi_dei_residui(v):
    """I gruppi dei residui a cui appartiene ciascuno dei due giocatori dell'incontro: per indole, tratto, fascia d'età, e il gruppo delle coppie miste e degli acciaccati."""
    gruppi = {}
    a, b = _GIOCATORI_PER_FORZA[v["a"]], _GIOCATORI_PER_FORZA[v["b"]]
    for lato, g, altro in (("A", a, b), ("B", b, a)):
        nomi = [f"indole {g.indole}", f"età dai {int(g.eta_anni // 10) * 10} anni"]
        nomi += [f"tratto {t}" for t in TRATTI if getattr(g, t, False)]
        if g.sesso == "f" and altro.sesso == "m":
            nomi.append("la donna nelle coppie miste")
        if v["cali"].get(g.id):
            nomi.append("l'acciaccato")
        gruppi[lato] = nomi
    return gruppi


def residui(voci):
    """Per ogni gruppo: quante volte un suo giocatore ha giocato, e la vittoria col motore meno quella con l'esito rapido, con l'errore della media, in punti percentuali."""
    differenze = {}
    for v in voci:
        for lato, nomi in gruppi_dei_residui(v).items():
            d = (v["vincitore"] == lato) - (v["rapido"]["vincitore"] == lato)
            for nome in nomi:
                differenze.setdefault(nome, []).append(d)
    uscita = []
    for nome in sorted(differenze):
        valori = differenze[nome]
        media = 100.0 * statistics.fmean(valori)
        errore = 100.0 * statistics.pstdev(valori) / math.sqrt(len(valori)) if len(valori) > 1 else 0.0
        uscita.append((nome, len(valori), media, errore))
    return uscita


def sonda_fatica(giocatori, quante, seme, taratura):
    """
    La sonda della stanchezza al meglio dei 5: lo stesso giocatore da giovane resistente e allenato, a
    30 anni con resistenza 5 e costanza alta, contro sé stesso da anziano poco resistente, a 62 anni
    con resistenza 2 e costanza zero, con gli stessi semi, col motore e con l'esito rapido, al meglio
    dei 3 e dei 5. Restituisce, per formato, la vittoria del giovane col motore e con l'esito rapido.
    """
    rng = random.Random(f"fatica-{seme}")
    conti = {3: [0, 0, 0], 5: [0, 0, 0]}
    for _ in range(quante):
        g = rng.choice(giocatori)
        giovane, anziano = copy.copy(g), copy.copy(g)
        giovane.id, anziano.id = g.id + 50_000_000, g.id + 60_000_000
        giovane.eta, giovane.resistenza_base, giovane.resistenza_allenata, giovane.costanza = costanti.giorni_da_anni(30), 3.0, 2.0, 1.5
        anziano.eta, anziano.resistenza_base, anziano.resistenza_allenata, anziano.costanza = costanti.giorni_da_anni(62), 2.0, 0.0, 0.0
        for set_al_meglio in (3, 5):
            s = rng.getrandbits(63)
            formato = formato_singolare(set_al_meglio)
            m = simula_incontro(giovane, anziano, formato, seme=s, dettaglio=ESSENZIALE)
            r = esito_rapido.gioca(giovane, anziano, formato, s, taratura=taratura)
            conti[set_al_meglio][0] += 1
            conti[set_al_meglio][1] += m.vincitore == "A"
            conti[set_al_meglio][2] += r.vincitore == "A"
    return {k: (100.0 * c[1] / c[0], 100.0 * c[2] / c[0]) for k, c in conti.items()}


def sonda_pari_forti(giocatori, quante, seme, taratura):
    """I forti alla pari, D25 e D26: coppie del quarto più forte con meno del 3 per cento di distacco, e ogni quanti incontri uno ha un set oltre i 12 punti, col motore e con l'esito rapido."""
    rng = random.Random(f"pari-{seme}")
    forti = sorted(giocatori, key=lambda g: g.indice_collettivo_valore, reverse=True)[: max(2, len(giocatori) // 4)]
    con_lungo = [0, 0]
    giocati = 0
    tentativi = 0
    while giocati < quante and tentativi < quante * 200:
        tentativi += 1
        a, b = rng.sample(forti, 2)
        if distacco(indice_del_distacco(a), indice_del_distacco(b)) >= 0.03:
            continue
        s = rng.getrandbits(63)
        m = simula_incontro(a, b, formato_singolare(3), seme=s, dettaglio=ESSENZIALE)
        r = esito_rapido.gioca(a, b, formato_singolare(3), s, taratura=taratura)
        con_lungo[0] += any(max(x, y) > 12 for x, y in m.set)
        con_lungo[1] += any(max(x, y) > 12 for x, y in r.set)
        giocati += 1
    return giocati, con_lungo


def verifica(voci, gare, scrivi, extra=None):
    """
    Il motore e l'esito rapido sulle stesse coppie e gli stessi semi: le misure una accanto all'altra,
    con i bersagli del punto 6.4 del progetto. Restituisce l'elenco dei bersagli fuori.
    """
    fuori = []

    def giudica(nome, scarto, massimo, errore=0.0, n=None):
        giudizio = esito(scarto, massimo, errore) if n is None or n >= MINIMO_PER_GIUDICARE else "pochi incontri, non si giudica"
        if giudizio == "FUORI":
            fuori.append(nome)
        return giudizio

    soglie = quarti_di_livello(voci) if voci and "livello" in voci[0] else None
    for set_al_meglio in (3, 5):
        gruppo = [v for v in voci if v["formato"] == set_al_meglio]
        if not gruppo:
            continue
        scrivi(f"Al meglio dei {set_al_meglio}, {len(gruppo)} incontri.")
        for nome, n, motore, rapido, errore in per_fascia(gruppo, lambda v: v["vincitore"], lambda v: v["rapido"]["vincitore"], appaiato=True):
            scrivi(f"Distacco {nome}, {n} incontri: il favorito vince il {numero(motore)} per cento col motore e il {numero(rapido)} con l'esito rapido, "
                   f"scarto {numero(rapido - motore)}, con un errore appaiato di {numero(errore)}, bersaglio entro {numero(SCARTO_FASCIA)}: "
                   f"{giudica(f'fascia {nome} al meglio dei {set_al_meglio}', rapido - motore, SCARTO_FASCIA, errore, n)}.")
        if soglie:
            # Dalla revisione del 14 ottobre 2026 anche quarto di livello per quarto di livello, perché lì stava lo scarto del mondo maturo.
            for quarto in range(QUARTI_DI_LIVELLO):
                parte = [v for v in gruppo if quarto_di(v, soglie) == quarto]
                pezzi = []
                for nome, n, motore, rapido, errore in per_fascia(parte, lambda v: v["vincitore"], lambda v: v["rapido"]["vincitore"], appaiato=True):
                    giudizio = giudica(f"fascia {nome} al meglio dei {set_al_meglio}, quarto di livello {quarto + 1}", rapido - motore, SCARTO_FASCIA, errore, n)
                    pezzi.append(f"{nome}, {n} incontri, {numero(motore)} e {numero(rapido)}, scarto {numero(rapido - motore)} più o meno {numero(errore)}, {giudizio}")
                scrivi(f"Quarto di livello {quarto + 1} al meglio dei {set_al_meglio}: " + "; ".join(pezzi) + ".")
        media_m, oltre_m, ris_m = misure_dei_set(gruppo)
        media_r, oltre_r, ris_r = misure_dei_set([v["rapido"] for v in gruppo])
        scrivi(f"Punti medi per set {numero(media_m, 2)} col motore e {numero(media_r, 2)} con l'esito rapido, bersaglio entro {numero(SCARTO_PUNTI_SET, 1)}: "
               f"{giudica(f'punti per set al meglio dei {set_al_meglio}', media_r - media_m, SCARTO_PUNTI_SET)}. "
               f"Set oltre i 12 punti {numero(oltre_m)} e {numero(oltre_r)} per cento, bersaglio entro {numero(SCARTO_OLTRE_12)}: "
               f"{giudica(f'set oltre i 12 al meglio dei {set_al_meglio}', oltre_r - oltre_m, SCARTO_OLTRE_12)}.")
        chiavi = sorted(set(ris_m) | set(ris_r))
        peggiore = max((abs(ris_r.get(k, 0.0) - ris_m.get(k, 0.0)) for k in chiavi), default=0.0)
        scrivi("Risultati in set degli incontri regolari, motore ed esito rapido: " + "; ".join(f"{k} {numero(ris_m.get(k, 0.0))} e {numero(ris_r.get(k, 0.0))}" for k in chiavi)
               + f"; lo scarto più grande {numero(peggiore)}, bersaglio entro {numero(SCARTO_RISULTATI)}: {giudica(f'risultati al meglio dei {set_al_meglio}', peggiore, SCARTO_RISULTATI)}.")
    for chi, chiave in (("motore", None), ("esito rapido", "rapido")):
        esiti = [v[chiave] if chiave else v for v in voci]
        scrivi(f"{chi.capitalize()}, tutti gli incontri: infortuni che fermano {sum(e['infortuni'] for e in esiti)}, acciacchi {sum(e['acciacchi'] for e in esiti)}, "
               f"ritiri {sum(1 for e in esiti if e['esito'] == 'ritiro')}.")
    for nome, campo in (("infortuni che fermano", "infortuni"), ("acciacchi", "acciacchi"), ("ritiri", None)):
        motore = sum(v[campo] for v in voci) if campo else sum(1 for v in voci if v["esito"] == "ritiro")
        rapido = sum(v["rapido"][campo] for v in voci) if campo else sum(1 for v in voci if v["rapido"]["esito"] == "ritiro")
        relativo = (rapido - motore) / motore if motore else 0.0
        errore = math.sqrt(motore + rapido) / motore if motore else 0.0
        scrivi(f"{nome.capitalize()} per incontro: {numero(100.0 * motore / len(voci), 2)} col motore e {numero(100.0 * rapido / len(voci), 2)} con l'esito rapido ogni cento incontri, "
               f"scarto relativo {numero(100.0 * relativo)} per cento, con un errore di {numero(100.0 * errore)}, bersaglio entro {numero(100.0 * SCARTO_INFORTUNI, 0)}: "
               f"{giudica(nome, 100.0 * relativo, 100.0 * SCARTO_INFORTUNI, 100.0 * errore)}.")
    righe_residui = []
    for nome, n, media, errore in residui(voci):
        giudizio = giudica(f"residuo {nome}", media, SCARTO_RESIDUI, errore, n)
        righe_residui.append(f"{nome}, {n}, {numero(media)} più o meno {numero(errore)}, {giudizio}")
    scrivi(f"I residui, cioè la vittoria col motore meno quella con l'esito rapido di chi sta nel gruppo, in punti percentuali, con le volte che ha giocato "
           f"e l'errore della media, bersaglio entro {numero(SCARTO_RESIDUI)}: " + "; ".join(righe_residui) + ".")
    if gare:
        for g in gare:
            g["favorito"], g["distacco"] = favorita_e_distacco_squadre(g["a"], g["b"])
        for nome, n, motore, rapido, errore in per_fascia(gare, lambda x: x["vincitore"], lambda x: x["rapido"]["vincitore"], appaiato=True):
            scrivi(f"Gara a squadre, distacco {nome}, {n} gare: la favorita vince il {numero(motore)} per cento col motore e il {numero(rapido)} con l'esito rapido, "
                   f"scarto {numero(rapido - motore)}, con un errore appaiato di {numero(errore)}, bersaglio entro {numero(SCARTO_SQUADRE)}: "
                   f"{giudica(f'gara a squadre, fascia {nome}', rapido - motore, SCARTO_SQUADRE, errore, n)}.")
        punti_m = statistics.fmean(sum(g["set"][0]) for g in gare)
        punti_r = statistics.fmean(sum(g["rapido"]["set"][0]) for g in gare)
        scrivi(f"Gara a squadre, {len(gare)} gare: punti del set {numero(punti_m, 2)} col motore e {numero(punti_r, 2)} con l'esito rapido, bersaglio entro {numero(SCARTO_PUNTI_SQUADRE)}: "
               f"{giudica('punti della gara a squadre', punti_r - punti_m, SCARTO_PUNTI_SQUADRE)}.")
    if extra:
        fatica, (pari, lunghi) = extra
        for set_al_meglio, (motore, rapido) in sorted(fatica.items()):
            scrivi(f"Sonda della stanchezza al meglio dei {set_al_meglio}: il giovane resistente vince contro sé stesso anziano il {numero(motore)} per cento col motore e il "
                   f"{numero(rapido)} con l'esito rapido"
                   + (f", bersaglio entro {numero(SCARTO_FATICA)}: {giudica('sonda della stanchezza', rapido - motore, SCARTO_FATICA)}." if set_al_meglio == 5 else "."))
        scrivi(f"Forti alla pari, {pari} incontri al meglio dei 3: uno con un set oltre i 12 punti ogni {numero(pari / max(1, lunghi[0]))} col motore e ogni "
               f"{numero(pari / max(1, lunghi[1]))} con l'esito rapido, D25 e D26 da sette a otto.")
    return fuori


def tempo_dell_esito_rapido(giocatori, taratura, quanti=4000):
    rng = random.Random("tempo")
    coppie_tempo = [rng.sample(giocatori, 2) for _ in range(quanti)]
    memoria = {}
    for a, b in coppie_tempo:
        esito_rapido.forza(a, taratura, memoria)
        esito_rapido.forza(b, taratura, memoria)
    inizio = time.perf_counter()
    for a, b in coppie_tempo:
        esito_rapido.gioca(a, b, formato_singolare(3), rng.getrandbits(63), basi_infortunio=_basi(a, b), taratura=taratura, memoria=memoria)
    return (time.perf_counter() - inizio) / quanti * 1e6


def blocco(taratura):
    righe = ["Il blocco da copiare nei predefiniti di TaraturaRapida, in esito_rapido.py:", f"_PESI = {taratura.PESI!r}", f"_PESI_TRATTI = {taratura.PESI_TRATTI_RAPIDI!r}"]
    for campo in ("PESO_LETTURA", "PENDENZA", "K_FATICA", "VANTAGGIO_BATTUTA", "GOAL_BASE", "GOAL_DISTACCO", "GOAL_LIVELLO", "PENALITA", "AZIONI_PER_SCAMBIO",
                  "ATTACCHI_PER_SCAMBIO", "PENDENZA_SQUADRE", "K_FATICA_SQUADRE", "VANTAGGIO_BATTUTA_SQUADRE", "GOAL_SQUADRE", "PENDENZA_LIVELLO", "LIVELLO_RIFERIMENTO"):
        righe.append(f"{campo} = {getattr(taratura, campo)!r}")
    return righe


def main():
    parser = argparse.ArgumentParser(description="La taratura dell'esito rapido di MESS sul motore vero.")
    parser.add_argument("--incontri", type=int, default=20000, help="gli incontri della taratura, 20.000 se non indicato")
    parser.add_argument("--squadre", type=int, default=4000, help="le gare a squadre della taratura, 4.000 se non indicato")
    parser.add_argument("--verifica", type=int, default=40000, help="gli incontri della verifica, 40.000 se non indicato; le gare a squadre un ottavo")
    parser.add_argument("--giocatori", type=int, default=1500, help="i giocatori di ognuna delle tre popolazioni")
    parser.add_argument("--processi", type=int, default=1, help="quanti processi usare, uno se non indicato")
    parser.add_argument("--veloce", action="store_true", help="un primo giro piccolo: 1.500 incontri, 400 gare a squadre, 2.000 di verifica, 600 giocatori per popolazione")
    parser.add_argument("--popolazione", type=Path, nargs="*", default=[],
                        help="aggiunge i giocatori salvati da simulazione_lunga.py --salva-popolazione, anche di più file; con --solo-verifica si gioca soltanto su loro")
    parser.add_argument("--campione", type=int, default=3000, help="quanti giocatori prendere da ogni popolazione salvata, 3.000 se non indicato; zero per tutti")
    parser.add_argument("--solo-verifica", action="store_true", help="niente taratura: la verifica dei numeri di adesso di TaraturaRapida")
    parser.add_argument("--senza-ritocco", action="store_true", help="la taratura senza il ritocco della pendenza, per il confronto")
    parser.add_argument("--rapporto", type=Path, default=None, help="scrive la carta della taratura in questo file")
    argomenti = parser.parse_args()
    if argomenti.veloce:
        argomenti.incontri, argomenti.squadre, argomenti.verifica, argomenti.giocatori = 1500, 400, 2000, 600
    inizio = time.perf_counter()
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    # Le popolazioni salvate, ciascuna coi suoi identificativi, per dire la verifica popolazione per popolazione.
    salvati, origini = [], []
    for numero_file, percorso in enumerate(argomenti.popolazione, start=1):
        giocatori_file, data_file = popolazione_salvata(percorso, argomenti.campione or None, seme=numero_file, spostamento=PRIMO_ID_SALVATI * numero_file)
        salvati.extend(giocatori_file)
        origini.append((f"{percorso.name} al {data_file[:10]}", PRIMO_ID_SALVATI * numero_file, PRIMO_ID_SALVATI * (numero_file + 1)))
    if argomenti.solo_verifica and salvati:
        giocatori = salvati
    else:
        giocatori = popolazioni(argomenti.giocatori) + salvati
        origini = [("popolazione di prova", 0, 200_000), ("mondo sintetico all'anno 10", 200_000, 400_000), ("mondo sintetico a regime", 400_000, PRIMO_ID_SALVATI),
                   *origini]
    for g in giocatori:
        _GIOCATORI_PER_FORZA[g.id] = g
    profili = {g.id: _profilo(g) for g in giocatori}
    descrizione = f"{len(giocatori)} giocatori" + (f", di cui {len(salvati)} di {len(argomenti.popolazione)} mondi simulati" if salvati else " in tre popolazioni")
    if argomenti.solo_verifica:
        taratura = esito_rapido.TARATURA_RAPIDA
        scrivi(f"Verifica dell'esito rapido sul motore vero, coi numeri di adesso di TaraturaRapida: {descrizione}.")
    else:
        scrivi(f"Taratura dell'esito rapido sul motore vero: {descrizione}, {argomenti.incontri} incontri e {argomenti.squadre} gare a squadre, "
               f"pronti in {numero(time.perf_counter() - inizio)} secondi.")
        lavori = coppie(giocatori, argomenti.incontri, 1)
        voci = in_parallelo(gioca_singolari, giocatori, lavori, argomenti.processi)
        taratura, negativi = tara_singolari(voci, profili)
        lavori_gare = squadre_a_caso(giocatori, argomenti.squadre, 1)
        gare = in_parallelo(gioca_gare, giocatori, lavori_gare, argomenti.processi)
        taratura = tara_squadre(gare, profili, taratura)
        scrivi(f"Regressioni fatte in {numero(time.perf_counter() - inizio)} secondi, su {sum(len(v['scambi']) for v in voci)} scambi dei singolari e "
               f"{sum(len(g['scambi']) for g in gare)} delle gare a squadre; la pendenza della regressione è {numero(taratura.PENDENZA, 4)}, quella della gara a squadre "
               f"{numero(taratura.PENDENZA_SQUADRE, 4)}.")
        if negativi:
            scrivi("Le caratteristiche col peso negativo nella regressione, portate a zero: " + ", ".join(negativi) + ".")
        if not argomenti.senza_ritocco:
            taratura = ritocca_pendenza(voci, lavori, taratura, scrivi)
            taratura = ritocca_pendenza_squadre(gare, lavori_gare, taratura, scrivi)
    verifiche = in_parallelo(gioca_singolari, giocatori, coppie(giocatori, argomenti.verifica, 2), argomenti.processi, rapido_anche=True, taratura=taratura)
    memoria = {}
    for v in verifiche:
        v["favorito"], v["distacco"] = favorito_e_distacco(v["a"], v["b"])
        v["livello"] = (esito_rapido.forza(_GIOCATORI_PER_FORZA[v["a"]], taratura, memoria) + esito_rapido.forza(_GIOCATORI_PER_FORZA[v["b"]], taratura, memoria)) / 2.0
    gare_verifica = in_parallelo(gioca_gare, giocatori, squadre_a_caso(giocatori, max(1, argomenti.verifica // 8), 2), argomenti.processi, rapido_anche=True,
                                 taratura=taratura)
    extra = (sonda_fatica(giocatori, max(200, argomenti.verifica // 20), 3, taratura), sonda_pari_forti(giocatori, max(300, argomenti.verifica // 15), 4, taratura))
    scrivi(f"La verifica: {len(verifiche)} incontri e {len(gare_verifica)} gare a squadre su altre coppie e altri semi, giocati col motore e con l'esito rapido.")
    fuori = verifica(verifiche, gare_verifica, scrivi, extra)
    scrivi("Bersagli fuori: " + ("; ".join(fuori) if fuori else "nessuno") + ".")
    # La verifica popolazione per popolazione, sulle coppie con tutti e due i giocatori della stessa: si
    # dice, e i bersagli sono quelli di sopra; qui conta vedere che nessuna popolazione stia da parte.
    for nome, basso, alto in origini:
        sue = [v for v in verifiche if basso <= v["a"] < alto and basso <= v["b"] < alto]
        if len(sue) < MINIMO_PER_GIUDICARE:
            continue
        pezzi = []
        for set_al_meglio in (3, 5):
            for fascia, n, motore, rapido, errore in per_fascia([v for v in sue if v["formato"] == set_al_meglio], lambda v: v["vincitore"],
                                                               lambda v: v["rapido"]["vincitore"], appaiato=True):
                pezzi.append(f"al meglio dei {set_al_meglio}, {fascia}, {n} incontri, scarto {numero(rapido - motore)} più o meno {numero(errore)}"
                             + ("" if n < MINIMO_PER_GIUDICARE else f", {esito(rapido - motore, SCARTO_FASCIA, errore)}"))
        scrivi(f"Popolazione {nome}, {len(sue)} incontri: " + "; ".join(pezzi) + ".")
    scrivi(f"L'esito rapido costa {numero(tempo_dell_esito_rapido(giocatori, taratura), 1)} microsecondi a incontro al meglio dei 3, con la memoria della forza.")
    for riga in blocco(taratura):
        scrivi(riga)
    scrivi(f"{'Verifica' if argomenti.solo_verifica else 'Taratura'} completata in {numero(time.perf_counter() - inizio)} secondi.")
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
