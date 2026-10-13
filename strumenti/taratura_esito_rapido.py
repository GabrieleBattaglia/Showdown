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
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/taratura_esito_rapido.py --veloce
    python strumenti/taratura_esito_rapido.py --incontri 6000 --squadre 2000 --processi 4 --rapporto strumenti/taratura_esito_rapido.txt
"""

import argparse
import concurrent.futures
import dataclasses
import itertools
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


def numero(valore, decimali=1):
    return f"{valore:.{decimali}f}".replace(".", ",")


# Le popolazioni.

def popolazioni(quanti):
    """I giocatori delle tre popolazioni, che possono giocare, con identificativi diversi."""
    prova = [g for g in pp.genera(quanti, 7, primo_id=1) if g.puo_giocare]
    anno_10 = [g for g in mondo_sintetico(quanti, 10, 2026, primo_id=200_000) if g.puo_giocare]
    regime = [g for g in mondo_sintetico(quanti, None, 2027, primo_id=400_000, candidati=int(quanti * 3.5)) if g.puo_giocare]
    return prova + anno_10 + regime


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


def gioca_singolari(lavori, rapido_anche, taratura_dati):
    taratura = esito_rapido.TaraturaRapida(**taratura_dati) if taratura_dati else None
    uscita = []
    for id_a, id_b, set_al_meglio, seme, acciaccato in lavori:
        a, b = _GIOCATORI[id_a], _GIOCATORI[id_b]
        cali = {acciaccato[0]: acciaccato[1]} if acciaccato else None
        formato = formato_singolare(set_al_meglio)
        r = simula_incontro(a, b, formato, seme=seme, dettaglio=ESSENZIALE, basi_infortunio=_basi(a, b), cali=cali)
        voce = {"a": id_a, "b": id_b, "formato": set_al_meglio, "cali": cali or {}, "vincitore": r.vincitore, "set": r.set, "esito": r.esito, "set_giocati": r.set_giocati,
                "azioni": (r.statistiche[id_a].azioni + r.statistiche[id_b].azioni) / 2.0, "attacchi": (r.statistiche[id_a].attacchi + r.statistiche[id_b].attacchi) / 2.0,
                "penalita": sum(1 for s in r.incontro.sanzioni if s[3] == "penalita"), "infortuni": len(r.infortuni), "acciacchi": len(r.acciacchi),
                "scambi": [(p.a_chi, p.parte_battitore, p.esito == "goal") for p in r.punti if p.punti > 0]}
        if rapido_anche:
            rr = esito_rapido.gioca(a, b, formato, seme, basi_infortunio=_basi(a, b), cali=cali, taratura=taratura)
            voce["rapido"] = {"vincitore": rr.vincitore, "set": rr.set, "esito": rr.esito, "set_giocati": rr.set_giocati, "infortuni": len(rr.infortuni),
                              "acciacchi": len(rr.acciacchi)}
        uscita.append(voce)
    return uscita


def gioca_gare(lavori, rapido_anche, taratura_dati):
    taratura = esito_rapido.TaraturaRapida(**taratura_dati) if taratura_dati else None
    uscita = []
    for ids_a, ids_b, seme in lavori:
        sa = Squadra("A", tuple(_GIOCATORI[i] for i in ids_a))
        sb = Squadra("B", tuple(_GIOCATORI[i] for i in ids_b))
        r = simula_incontro(sa, sb, SQUADRE, seme=seme, dettaglio=ESSENZIALE)
        voce = {"a": ids_a, "b": ids_b, "vincitore": r.vincitore, "set": r.set,
                "scambi": [(p.battitore, p.ricevitore, p.a_chi, p.parte_battitore, p.esito == "goal") for p in r.punti if p.punti > 0]}
        if rapido_anche:
            rr = esito_rapido.gioca_squadre(sa, sb, seme, taratura=taratura)
            voce["rapido"] = {"vincitore": rr.vincitore, "set": rr.set}
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
    """Le due regressioni dei singolari; restituisce i numeri della taratura che ne vengono."""
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


# La verifica.

def verifica(voci, gare, scrivi):
    """Il motore e l'esito rapido sulle stesse coppie e gli stessi semi: le misure una accanto all'altra."""
    for set_al_meglio in (3, 5):
        gruppo = [v for v in voci if v["formato"] == set_al_meglio]
        if not gruppo:
            continue
        scrivi(f"Al meglio dei {set_al_meglio}, {len(gruppo)} incontri.")
        limiti = [0.0] + [f[0] for f in FASCE_DISTACCO if f[0] is not None] + [math.inf]
        for (basso, alto), (_l, nome, _b) in zip(itertools.pairwise(limiti), FASCE_DISTACCO, strict=True):
            fascia = [v for v in gruppo if basso <= v["distacco"] < alto]
            if not fascia:
                continue
            motore = 100.0 * sum(1 for v in fascia if v["vincitore"] == v["favorito"]) / len(fascia)
            rapido = 100.0 * sum(1 for v in fascia if v["rapido"]["vincitore"] == v["favorito"]) / len(fascia)
            scrivi(f"Distacco {nome}, {len(fascia)} incontri: il favorito vince il {numero(motore)} per cento col motore e il {numero(rapido)} con l'esito rapido, "
                   f"scarto {numero(rapido - motore)}.")
        for chi, chiave in (("motore", None), ("esito rapido", "rapido")):
            esiti = [v[chiave] if chiave else v for v in gruppo]
            reali = [s for e in esiti for s in e["set"][:e["set_giocati"]]]
            media = statistics.fmean(a + b for a, b in reali) if reali else 0.0
            oltre = 100.0 * sum(1 for a, b in reali if max(a, b) > 12) / len(reali) if reali else 0.0
            risultati = {}
            for e in esiti:
                if e["esito"] == "ritiro":
                    continue
                vinti = sum(1 for a, b in e["set"] if a > b)
                chiave_risultato = f"{max(vinti, len(e['set']) - vinti)} a {min(vinti, len(e['set']) - vinti)}"
                risultati[chiave_risultato] = risultati.get(chiave_risultato, 0) + 1
            regolari = sum(risultati.values()) or 1
            quote = ", ".join(f"{k} {numero(100.0 * n / regolari)}" for k, n in sorted(risultati.items()))
            infortuni_conto = sum(e["infortuni"] for e in esiti)
            acciacchi_conto = sum(e["acciacchi"] for e in esiti)
            ritiri = sum(1 for e in esiti if e["esito"] == "ritiro")
            scrivi(f"{chi.capitalize()}: punti medi per set {numero(media, 2)}, set oltre i 12 punti {numero(oltre)} per cento; risultati {quote}; "
                   f"infortuni che fermano {infortuni_conto}, acciacchi {acciacchi_conto}, ritiri {ritiri}.")
    if gare:
        motore = 100.0 * sum(1 for g in gare if g["vincitore"] == g["favorita"]) / len(gare)
        rapido = 100.0 * sum(1 for g in gare if g["rapido"]["vincitore"] == g["favorita"]) / len(gare)
        punti_m = statistics.fmean(sum(g["set"][0]) for g in gare)
        punti_r = statistics.fmean(sum(g["rapido"]["set"][0]) for g in gare)
        scrivi(f"Gara a squadre, {len(gare)} gare: la squadra più forte vince il {numero(motore)} per cento col motore e il {numero(rapido)} con l'esito rapido; "
               f"punti del set {numero(punti_m, 1)} col motore e {numero(punti_r, 1)} con l'esito rapido.")


def tempo_dell_esito_rapido(giocatori, taratura, quanti=2000):
    rng = random.Random("tempo")
    coppie_tempo = [rng.sample(giocatori, 2) for _ in range(quanti)]
    inizio = time.perf_counter()
    memoria = {}
    for a, b in coppie_tempo:
        esito_rapido.gioca(a, b, formato_singolare(3), rng.getrandbits(63), basi_infortunio=_basi(a, b), taratura=taratura, memoria=memoria)
    return (time.perf_counter() - inizio) / quanti * 1e6


def main():
    parser = argparse.ArgumentParser(description="La taratura dell'esito rapido di MESS sul motore vero.")
    parser.add_argument("--incontri", type=int, default=6000, help="gli incontri della taratura, 6.000 se non indicato")
    parser.add_argument("--squadre", type=int, default=2000, help="le gare a squadre della taratura, 2.000 se non indicato")
    parser.add_argument("--verifica", type=int, default=4000, help="gli incontri della verifica, 4.000 se non indicato; le gare a squadre un quarto")
    parser.add_argument("--giocatori", type=int, default=1500, help="i giocatori di ognuna delle tre popolazioni")
    parser.add_argument("--processi", type=int, default=1, help="quanti processi usare, uno se non indicato")
    parser.add_argument("--veloce", action="store_true", help="un primo giro piccolo: 1.500 incontri, 400 gare a squadre, 1.000 di verifica, 600 giocatori per popolazione")
    parser.add_argument("--rapporto", type=Path, default=None, help="scrive la carta della taratura in questo file")
    argomenti = parser.parse_args()
    if argomenti.veloce:
        argomenti.incontri, argomenti.squadre, argomenti.verifica, argomenti.giocatori = 1500, 400, 1000, 600
    inizio = time.perf_counter()
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    giocatori = popolazioni(argomenti.giocatori)
    for g in giocatori:
        _GIOCATORI_PER_FORZA[g.id] = g
    profili = {g.id: _profilo(g) for g in giocatori}
    scrivi(f"Taratura dell'esito rapido sul motore vero: {len(giocatori)} giocatori in tre popolazioni, {argomenti.incontri} incontri e {argomenti.squadre} gare a squadre, "
           f"pronti in {numero(time.perf_counter() - inizio)} secondi.")
    voci = in_parallelo(gioca_singolari, giocatori, coppie(giocatori, argomenti.incontri, 1), argomenti.processi)
    taratura, negativi = tara_singolari(voci, profili)
    gare = in_parallelo(gioca_gare, giocatori, squadre_a_caso(giocatori, argomenti.squadre, 1), argomenti.processi)
    taratura = tara_squadre(gare, profili, taratura)
    scrivi(f"Regressioni fatte in {numero(time.perf_counter() - inizio)} secondi, su {sum(len(v['scambi']) for v in voci)} scambi dei singolari e "
           f"{sum(len(g['scambi']) for g in gare)} delle gare a squadre.")
    if negativi:
        scrivi("Le caratteristiche col peso negativo nella regressione, portate a zero: " + ", ".join(negativi) + ".")
    verifiche = in_parallelo(gioca_singolari, giocatori, coppie(giocatori, argomenti.verifica, 2), argomenti.processi, rapido_anche=True, taratura=taratura)
    for v in verifiche:
        a, b = _GIOCATORI_PER_FORZA[v["a"]], _GIOCATORI_PER_FORZA[v["b"]]
        ia, ib = indice_del_distacco(a), indice_del_distacco(b)
        v["distacco"] = distacco(ia, ib)
        v["favorito"] = "A" if ia >= ib else "B"
    gare_verifica = in_parallelo(gioca_gare, giocatori, squadre_a_caso(giocatori, max(1, argomenti.verifica // 4), 2), argomenti.processi, rapido_anche=True,
                                 taratura=taratura)
    for g in gare_verifica:
        fa = statistics.fmean(esito_rapido.forza(_GIOCATORI_PER_FORZA[i], taratura) for i in g["a"][:3])
        fb = statistics.fmean(esito_rapido.forza(_GIOCATORI_PER_FORZA[i], taratura) for i in g["b"][:3])
        g["favorita"] = "A" if fa >= fb else "B"
    verifica(verifiche, gare_verifica, scrivi)
    scrivi(f"L'esito rapido costa {numero(tempo_dell_esito_rapido(giocatori, taratura), 1)} microsecondi a incontro al meglio dei 3, con la memoria della forza.")
    scrivi("Il blocco da copiare nei predefiniti di TaraturaRapida, in esito_rapido.py:")
    scrivi(f"_PESI = {taratura.PESI!r}")
    scrivi(f"_PESI_TRATTI = {taratura.PESI_TRATTI_RAPIDI!r}")
    for campo in ("PESO_LETTURA", "PENDENZA", "K_FATICA", "VANTAGGIO_BATTUTA", "GOAL_BASE", "GOAL_DISTACCO", "GOAL_LIVELLO", "PENALITA", "AZIONI_PER_SCAMBIO",
                  "ATTACCHI_PER_SCAMBIO", "PENDENZA_SQUADRE", "K_FATICA_SQUADRE", "VANTAGGIO_BATTUTA_SQUADRE", "GOAL_SQUADRE"):
        scrivi(f"{campo} = {getattr(taratura, campo)!r}")
    scrivi(f"Taratura completata in {numero(time.perf_counter() - inizio)} secondi.")
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
