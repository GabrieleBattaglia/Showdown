"""
Banco di prova del motore di partita di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto); dalla tappa 9
Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce con la tappa 1 del piano, il 2026-10-02, per misurare il vecchio motore: i suoi numeri sono
conservati in strumenti/banco_partite_prima.txt. Con la tappa 9, il 2026-10-07, è riscritto per il
motore nuovo: non avvolge più metodi privati, chiama simula_incontro e legge risultati e
statistiche. Non scrive nulla nel mondo e non registra niente: le partite si giocano in memoria.
Il rapporto tiene le frasi di prima, senza separatori, per il confronto con banco_partite_prima.txt,
e aggiunge le misure dei bersagli della taratura: cause dei falli, goal di battuta e da scambio,
lunghezza degli scambi, set oltre i 12 punti, partite fra forti alla pari, palle morte, sanzioni,
time-out, temperamento, esperienza, lettura del gioco, stanchezza, squadre, infortuni e tempo per
partita. Accanto a ogni bersaglio dice se la misura ci sta dentro; gli eventi rari, rotture e
penalità, si giudicano con l'intervallo di Poisson, e le bande del meglio dei 3 valgono soltanto lì.
Il temperamento si misura con una sonda a coppie, gli stessi giocatori impetuosi e calmi contro gli
stessi avversari e con gli stessi semi, perché il confronto fra gruppi di giocatori diversi è
confuso dalle altre differenze fra loro. Al meglio dei 5 aggiunge la sonda della stanchezza, un
trentenne con la resistenza innata più alta e un sessantenne poco resistente, e dalla decisione D26
un giovane molto resistente e allenato e un anziano poco resistente a fine quinto set, che la
popolazione di prova da sola non contiene: tutti giocatori che nel mondo possono esistere. I rapporti di prima e dopo la taratura della tappa 9
stanno accanto, in banco_partite_prima.txt e banco_partite_dopo.txt.
Il mondo predefinito è una popolazione di prova di strumenti/popolazione_di_prova.py, col 60 per
cento di allenati e l'esperienza fino a 12; con --mondo salvato si leggono in sola lettura i
giocatori del mondo salvato.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/banco_partite.py
    python strumenti/banco_partite.py --partite 1000 --set 5 --seme 42
    python strumenti/banco_partite.py --pari-forti --partite 500
    python strumenti/banco_partite.py --dettaglio completo --partite 200
    python strumenti/banco_partite.py --squadre 100
    python strumenti/banco_partite.py --taratura prova.json --rapporto banco_dopo.txt
"""

import argparse
import copy
import math
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

from popolazione_di_prova import genera  # noqa: E402

import archivio  # noqa: E402
import costanti  # noqa: E402
import infortuni  # noqa: E402
import percorsi  # noqa: E402
from mondo import Mondo  # noqa: E402
from motore import COMPLETO, ESSENZIALE, SQUADRE, TARATURA, Squadra, formato_singolare, simula_incontro  # noqa: E402
from motore.campo import InCampo  # noqa: E402
from motore.eventi import CAUSE, CHIAMATE  # noqa: E402
from motore.regia import controlla_invarianti  # noqa: E402
from motore.squadre import composizione_valida  # noqa: E402
from motore.taratura import carica_taratura  # noqa: E402
from version import __version__  # noqa: E402

# Le fasce di distacco fra i due indici di valore, per misurare quanto conta essere favoriti.
FASCE_DISTACCO = ((0.05, "meno del 5 per cento", (50, 58)), (0.15, "fra il 5 e il 15 per cento", (58, 70)),
                  (0.30, "fra il 15 e il 30 per cento", (70, 85)), (None, "oltre il 30 per cento", (85, 96)))
# Le chiamate dei falli nell'ordine del rapporto, con il bersaglio in quota dei falli.
BERSAGLI_CAUSE = (("schermo centrale", (28, 38)), ("out", (30, 42)), ("servizio irregolare", (8, 15)), ("body touch", (6, 15)),
                  ("difesa irregolare", (1.5, 6)), ("infrazione palla", (1, 5)), ("infrazione paletta", (0.5, 3)), ("invasione", (0.3, 2)))


def numero(valore, decimali=1):
    return f"{valore:.{decimali}f}".replace(".", ",")


def percentuale(parte, totale):
    if not totale:
        return "nessuno"
    return f"{numero(100 * parte / totale)} per cento"


def per_cento(parte, totale):
    return 100.0 * parte / totale if totale else 0.0


def esito_bersaglio(valore, intervallo):
    basso, alto = intervallo
    return "dentro" if basso <= valore <= alto else "FUORI"


def _poisson_fino_a(k, media):
    """La probabilità di contare al massimo k eventi, se in media se ne aspettano media."""
    termine = math.exp(-media)
    totale = termine
    for i in range(1, k + 1):
        termine *= media / i
        totale += termine
    return min(1.0, totale)


def esito_raro(osservati, attesi_minimo, attesi_massimo, soglia=0.025):
    """
    Il giudizio su un evento raro, come le rotture: con pochi eventi la banda non si confronta col
    numero contato, che oscilla per puro caso, ma con l'intervallo di Poisson. Fuori soltanto se
    contarne così pochi è improbabile anche col tasso più alto della banda, o contarne così tanti
    anche col più basso: con 1000 partite una rottura ogni 312 dà in media 3,2 eventi.
    """
    if osservati > 0 and _poisson_fino_a(osservati - 1, attesi_massimo) > 1.0 - soglia:
        return "FUORI"
    if _poisson_fino_a(osservati, attesi_minimo) < soglia:
        return "FUORI"
    return "dentro, con l'intervallo di Poisson"


def carica_mondo_salvato():
    """I giocatori del mondo salvato, letti in sola lettura, senza ripiegare sulla copia."""
    percorso = percorsi.percorso(costanti.FILE_MONDO)
    mondo = Mondo()
    try:
        archivio.costruisci(archivio.leggi(percorso), mondo)
    except archivio.ErroreSalvataggio as e:
        sys.exit(f"Il mondo salvato in {percorso} non si può usare: {e}. Senza --mondo salvato il banco usa una popolazione di prova.")
    return list(mondo.giocatori.values())


def distacco(icv_a, icv_b):
    """Di quanto l'indice di valore del favorito supera quello dell'altro, in proporzione."""
    alto, basso = max(icv_a, icv_b), min(icv_a, icv_b)
    return (alto - basso) / max(1.0, basso)


def coppie_pari_forti(giocatori, quante, rng):
    """Coppie del quarto più forte, con un distacco sotto il 3 per cento."""
    forti = sorted(giocatori, key=lambda g: g.indice_collettivo_valore, reverse=True)[: max(2, len(giocatori) // 4)]
    coppie = []
    tentativi = 0
    while len(coppie) < quante and tentativi < quante * 200:
        tentativi += 1
        a, b = rng.sample(forti, 2)
        if distacco(a.indice_collettivo_valore, b.indice_collettivo_valore) < 0.03:
            coppie.append((a, b))
    if len(coppie) < quante:
        sys.exit("Non ci sono abbastanza coppie di forti alla pari: servono più giocatori.")
    return coppie


class Banco:
    """Raccoglie le misure dai risultati degli incontri."""

    def __init__(self, taratura):
        self.taratura = taratura
        self.punti = []
        self.set = []
        self.partite = []
        self.falli = Counter()
        self.goal = Counter()
        self.palle_morte = Counter()
        self.rotture = 0
        self.ammonizioni = 0
        self.penalita = 0
        self.mascherine = 0
        self.timeout = 0
        self.battute = 0
        self.battute_irregolari = 0
        self.durate = []
        self.invarianti = 0
        self.gruppi = {"impetuosi": Counter(), "calmi": Counter(), "esperti": Counter(), "inesperti": Counter()}
        self.lettura = {"esperti": Counter(), "inesperti": Counter()}
        self.fatica = {"trentenni con la resistenza innata più alta": [], "anziani poco resistenti": []}
        self.infortuni = []
        self._dp = {}

    def _difesa_vera(self, g):
        if g.id not in self._dp:
            self._dp[g.id] = InCampo(g, "A", self.taratura).Dp
        return self._dp[g.id]

    def aggiungi(self, a, b, risultato, completo):
        self.punti.extend(risultato.punti)
        self.set.extend(risultato.set)
        sa, sb = risultato.set_vinti
        self.partite.append({"icv": (a.indice_collettivo_valore, b.indice_collettivo_valore), "vince_il_primo": risultato.vincitore == "A",
                             "set": (max(sa, sb), min(sa, sb)), "punteggi": list(risultato.set)})
        for p in risultato.punti:
            if p.esito == "fallo" or p.causa == "goal_dopo_difesa_irregolare":
                self.falli[p.causa] += 1
            if p.esito == "goal":
                self.goal[p.causa] += 1
            if p.esito == "palla_morta":
                self.palle_morte[p.causa] += 1
            if p.esito == "rottura":
                self.rotture += 1
            self.battute += 1
            if p.origine == "battuta" and p.esito == "fallo" and CAUSE[p.causa].famiglia in ("battuta", "attacco") and p.attacchi == 0 and p.chi_commette == p.battitore:
                self.battute_irregolari += 1
        for sanzione in risultato.incontro.sanzioni:
            _set, _punto, _gid, tipo, causa = sanzione
            if tipo == "ammonizione":
                self.ammonizioni += 1
            else:
                self.penalita += 1
            if causa == "mascherina_toccata":
                self.mascherine += 1
        self.timeout += len(risultato.incontro.timeout)
        if completo:
            self.durate.append(risultato.durata_simulata)
            if controlla_invarianti(risultato.eventi):
                self.invarianti += 1
        for g, avversario in ((a, b), (b, a)):
            stats = risultato.statistiche[g.id]
            falli = sum(stats.falli.values())
            temperamento = g.temperamento_attuale
            for nome, dentro in (("impetuosi", temperamento >= 75), ("calmi", temperamento <= 25), ("esperti", g.esperienza >= 10), ("inesperti", g.esperienza < 1)):
                if dentro:
                    gruppo = self.gruppi[nome]
                    gruppo["falli"] += falli
                    gruppo["goal"] += stats.goal
                    gruppo["attacchi"] += stats.attacchi
                    gruppo["azioni"] += stats.azioni
            dp = self._difesa_vera(avversario)
            if abs(dp["sx"] - dp["dx"]) >= 15:
                debole = "sx" if dp["sx"] < dp["dx"] else "dx"
                forte = "dx" if debole == "sx" else "sx"
                for nome, dentro in (("esperti", g.esperienza >= 10), ("inesperti", g.esperienza < 1)):
                    if dentro:
                        self.lettura[nome]["debole"] += stats.attacchi_verso[debole]
                        self.lettura[nome]["laterali"] += stats.attacchi_verso[debole] + stats.attacchi_verso[forte]
            anni = g.eta_anni
            resistenza = g._get_valore_totale("resistenza_base")
            # I gruppi del punto 18.16, riletti dopo la revisione della decisione D26, non allenano
            # la resistenza: chi si allena si stanca più piano, e lo misura la sonda della
            # stanchezza. Il trentenne ha la resistenza innata più alta che si possa avere, fra 2,5
            # e 3: l'innata nasce fra 0 e 3 e non cresce, e il vecchio gruppo, con la resistenza da
            # 4 a 6 senza allenamento, restava sempre vuoto.
            if risultato.formato.set_al_meglio == 5 and g.resistenza_allenata < 0.5:
                if 25 <= anni <= 35 and g.resistenza_base >= 2.5:
                    self.fatica["trentenni con la resistenza innata più alta"].append(stats.eff_finale)
                elif 55 <= anni <= 65 and resistenza <= 3:
                    self.fatica["anziani poco resistenti"].append(stats.eff_finale)
            if not g.ambidestro:
                self.infortuni.append((infortuni.probabilita(g, stats.azioni), _probabilita_vecchia(g)))


def _probabilita_vecchia(g):
    """La probabilità d'infortunio del vecchio motore, senza il carico, per il confronto."""
    aumento = 0.0
    anni = g.eta_anni
    if anni > costanti.ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI:
        intervallo = max(1.0, costanti.ETA_MAX_PROB_INFORTUNIO_ANNI - costanti.ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI)
        aumento = (min(anni, costanti.ETA_MAX_PROB_INFORTUNIO_ANNI) - costanti.ETA_INIZIO_AUMENTO_PROB_INFORTUNIO_ANNI) / intervallo * costanti.PROB_INFORTUNIO_AUMENTO_MAX_PERC
    return costanti.PROB_INFORTUNIO_BASE_PER_PARTITA + aumento


def descrivi_contatore(contatore, totale, chiavi=None):
    """Una riga discorsiva per un contatore: voce, quantità e percentuale, dalla più frequente."""
    voci = chiavi or [k for k, _ in contatore.most_common()]
    return "; ".join(f"{k}: {contatore[k]}, {percentuale(contatore[k], totale)}" for k in voci if contatore[k])


def percentile(valori, quota):
    ordinati = sorted(valori)
    if not ordinati:
        return 0
    indice = min(len(ordinati) - 1, max(0, math.ceil(quota * len(ordinati)) - 1))
    return ordinati[indice]


def rapporto(banco, intestazione, pari_forti, set_al_meglio=3, sonde=()):
    """
    Il rapporto discorsivo del banco, con i bersagli della taratura. Le bande del meglio dei 3,
    cioè favorito, time-out e infortuni, si controllano soltanto al meglio dei 3, e gli infortuni
    soltanto fra coppie a caso; gli eventi rari si giudicano con l'intervallo di Poisson. Le
    sonde, come quella del temperamento, aggiungono le loro righe e i loro bersagli.
    """
    righe = list(intestazione)
    punti = banco.punti
    giocati = len(punti)
    morte = sum(1 for p in punti if p.esito in ("palla_morta", "rottura"))
    goal = sum(1 for p in punti if p.esito == "goal")
    falli = sum(1 for p in punti if p.esito == "fallo")
    assegnati = goal + falli
    bersagli = []
    righe.append(f"Punti giocati {giocati}: {assegnati} assegnati e {morte} palle morte o rotture, che si ripetono.")
    righe.append(f"Dei punti assegnati, {goal} sono goal, {percentuale(goal, assegnati)}, e {falli} sono falli, {percentuale(falli, assegnati)}.")
    goal_quota = per_cento(goal, giocati)
    bersagli.append(("Goal sui punti giocati", goal_quota, (50, 70) if pari_forti else (45, 60)))
    nomi_goal = {"goal_battuta": "goal di battuta", "goal_scambio": "goal da scambio", "goal_ribattuta": "goal su una palla tornata piano",
                 "goal_dopo_difesa_irregolare": "goal dopo una difesa irregolare", "autogoal": "autogoal"}
    righe.append("Come nascono i goal: " + descrivi_contatore(Counter({nomi_goal[k]: n for k, n in banco.goal.items()}), goal) + ".")
    da_scambio = sum(1 for p in punti if p.esito == "goal" and p.attacchi >= 2)
    righe.append(f"Goal arrivati dopo almeno due attacchi, cioè da uno scambio vero: {da_scambio}, {percentuale(da_scambio, goal)} dei goal.")
    bersagli.append(("Goal di battuta sui goal", per_cento(banco.goal["goal_battuta"], goal), (12, 25)))
    per_chiamata = Counter()
    for causa, n in banco.falli.items():
        chiamata = CHIAMATE[CAUSE[causa].chiamata] if CAUSE[causa].famiglia != "goal" else "difesa irregolare"
        per_chiamata[chiamata] += n
    totale_falli = sum(per_chiamata.values())
    righe.append("Come nascono i falli, per chiamata dell'arbitro: " + descrivi_contatore(per_chiamata, totale_falli) + ".")
    righe.append("I falli per causa IBSA: " + descrivi_contatore(banco.falli, totale_falli) + ".")
    for chiamata, intervallo in BERSAGLI_CAUSE:
        bersagli.append((f"Falli per {chiamata}", per_cento(per_chiamata[chiamata], totale_falli), intervallo))
    bersagli.append(("Battute irregolari sulle battute", per_cento(banco.battute_irregolari, banco.battute), (4, 8)))
    if banco.palle_morte:
        righe.append("Come nascono le palle morte: " + descrivi_contatore(banco.palle_morte, sum(banco.palle_morte.values())) + ".")
    bersagli.append(("Palle morte sui punti giocati", per_cento(sum(banco.palle_morte.values()), giocati), (0.5, 1.5)))
    bersagli.append(("Palle morte per limite tecnico", banco.palle_morte["limite_tecnico"], (0, 0)))
    attacchi = [p.attacchi for p in punti]
    classi = Counter()
    for n in attacchi:
        if n == 0:
            classi["finito sulla battuta"] += 1
        elif n == 1:
            classi["un attacco"] += 1
        elif n == 2:
            classi["due attacchi"] += 1
        elif n <= 5:
            classi["da tre a cinque attacchi"] += 1
        else:
            classi["oltre cinque attacchi"] += 1
    ordine = ["finito sulla battuta", "un attacco", "due attacchi", "da tre a cinque attacchi", "oltre cinque attacchi"]
    media = statistics.fmean(attacchi)
    righe.append(f"Lunghezza degli scambi: in media {numero(media, 2)} attacchi per punto, mediana {statistics.median(attacchi)}, "
                 f"novantesimo percentile {percentile(attacchi, 0.9)}, al massimo {max(attacchi)}.")
    righe.append("Punti per numero di attacchi: " + descrivi_contatore(classi, giocati, ordine) + ".")
    bersagli.append(("Punti finiti sulla battuta", per_cento(classi["finito sulla battuta"], giocati), (12, 22)))
    if not pari_forti:
        # Fra pari forti gli scambi devono essere più lunghi di quelli del mondo, di almeno un
        # decimo: le bande del mondo lì non valgono, e il confronto si fa fra i due rapporti.
        bersagli.append(("Attacchi per punto, media", media, (2.5, 5)))
        bersagli.append(("Attacchi per punto, mediana", statistics.median(attacchi), (2, 3)))
        bersagli.append(("Attacchi per punto, novantesimo percentile", percentile(attacchi, 0.9), (6, 12)))
    set_totali = len(banco.set)
    per_set = giocati / set_totali if set_totali else 0
    ai_vantaggi = sum(1 for a, b in banco.set if min(a, b) >= costanti.PUNTI_VITTORIA_SET_BASE - 1)
    oltre_12 = sum(1 for a, b in banco.set if max(a, b) > 12)
    segnati = statistics.fmean(a + b for a, b in banco.set) if set_totali else 0
    righe.append(f"Set giocati {set_totali}, in media {numero(per_set)} punti giocati per set, cioè scambi assegnati o ripetuti, e {numero(segnati)} punti segnati, la somma del punteggio.")
    righe.append(f"Set arrivati ai vantaggi, con entrambi almeno a {costanti.PUNTI_VITTORIA_SET_BASE - 1}: {ai_vantaggi}, {percentuale(ai_vantaggi, set_totali)}. "
                 f"Set oltre i 12 punti: {oltre_12}, {percentuale(oltre_12, set_totali)}; il più lungo finisce {max(banco.set, key=max)[0]} a {max(banco.set, key=max)[1]}.")
    # Il bersaglio dei punti per set viene dal vecchio motore, dove ogni scambio valeva un punto:
    # col goal da due si confronta con la somma del punteggio.
    bersagli.append(("Punti segnati per set", segnati, (15, 19)))
    punteggi = Counter(f"{max(a, b)} a {min(a, b)}" for a, b in banco.set)
    righe.append("Punteggi di set più frequenti: " + descrivi_contatore(Counter(dict(punteggi.most_common(6))), set_totali) + ".")
    partite = banco.partite
    risultati = Counter(f"{a} a {b}" for a, b in (p["set"] for p in partite))
    righe.append(f"Partite giocate {len(partite)}. Risultati in set: " + descrivi_contatore(risultati, len(partite)) + ".")
    con_oltre_12 = sum(1 for p in partite if any(max(a, b) > 12 for a, b in p["punteggi"]))
    scarti = [abs(a - b) for a, b in banco.set]
    stretti = sum(1 for s in scarti if s in (2, 3))
    righe.append(f"Partite con almeno un set oltre i 12 punti: {con_oltre_12}, una ogni {numero(len(partite) / con_oltre_12) if con_oltre_12 else 'nessuna'}. "
                 f"Set chiusi con 2 o 3 punti di scarto: {percentuale(stretti, set_totali)}; scarto medio {numero(statistics.fmean(scarti))}.")
    if pari_forti:
        bersagli.append(("Partite ogni set oltre i 12, fra pari forti", len(partite) / con_oltre_12 if con_oltre_12 else 999, (5.5, 9)))
        bersagli.append(("Set con 2 o 3 punti di scarto, fra pari forti", per_cento(stretti, set_totali), (30, 100)))
        bersagli.append(("Scarto medio dei set, fra pari forti", statistics.fmean(scarti), (0, 5.5)))
    con_favorito = [p for p in partite if p["icv"][0] != p["icv"][1]]
    vinte_favorito = sum(1 for p in con_favorito if p["vince_il_primo"] == (p["icv"][0] > p["icv"][1]))
    righe.append(f"Il favorito, cioè il giocatore con l'indice di valore più alto, vince {vinte_favorito} partite su {len(con_favorito)}, {percentuale(vinte_favorito, len(con_favorito))}.")
    minimo = 0.0
    for limite, nome, intervallo in FASCE_DISTACCO:
        massimo = limite if limite is not None else float("inf")
        nella_fascia = [p for p in con_favorito if minimo <= distacco(*p["icv"]) < massimo]
        vinte = sum(1 for p in nella_fascia if p["vince_il_primo"] == (p["icv"][0] > p["icv"][1]))
        minimo = massimo
        if nella_fascia:
            righe.append(f"Con un distacco {nome}: {len(nella_fascia)} partite, il favorito ne vince {vinte}, {percentuale(vinte, len(nella_fascia))}.")
            # Le bande del favorito valgono al meglio dei 3: al meglio dei 5 il favorito vince di più.
            if len(nella_fascia) >= 30 and set_al_meglio == 3:
                bersagli.append((f"Vittorie del favorito con un distacco {nome}", per_cento(vinte, len(nella_fascia)), intervallo))
    n = len(partite)
    righe.append(f"Imprevisti: {banco.rotture} rotture, {banco.ammonizioni} ammonizioni, {banco.penalita} penalità di cui {banco.mascherine} per la mascherina, "
                 f"{banco.timeout} time-out, in {n} partite.")
    # Rotture e penalità sono così rare che in mille partite se ne contano poche: il numero
    # contato si confronta con l'intervallo di Poisson della banda, non con la banda stessa.
    bersagli.append(("Partite per una rottura", n / banco.rotture if banco.rotture else 9999, (150, 400), esito_raro(banco.rotture, n / 400, n / 150)))
    bersagli.append(("Ammonizioni ogni 100 partite", 100 * banco.ammonizioni / n, (3, 10)))
    bersagli.append(("Penalità ogni 100 partite", 100 * banco.penalita / n, (0, 1.5), esito_raro(banco.penalita, 0.0, 1.5 * n / 100)))
    if set_al_meglio == 3:
        # Al meglio dei 5 ci sono più set, e quindi più time-out.
        bersagli.append(("Time-out a partita", banco.timeout / n, (0.3, 0.8)))
    g = banco.gruppi
    if g["impetuosi"]["attacchi"] and g["calmi"]["attacchi"]:
        imp = 100 * g["impetuosi"]["falli"] / g["impetuosi"]["attacchi"]
        calmi = 100 * g["calmi"]["falli"] / g["calmi"]["attacchi"]
        goal_imp = 100 * g["impetuosi"]["goal"] / g["impetuosi"]["attacchi"]
        goal_calmi = 100 * g["calmi"]["goal"] / g["calmi"]["attacchi"]
        # Un confronto fra giocatori diversi, confuso dalle altre differenze fra loro: resta come
        # informazione, e il bersaglio lo misura la sonda a coppie.
        righe.append(f"Temperamento nei gruppi, ogni 100 attacchi: gli impetuosi fanno {numero(imp)} falli e {numero(goal_imp)} goal, i calmi {numero(calmi)} falli e {numero(goal_calmi)} goal; "
                     f"il rapporto dei falli, {numero(imp / calmi if calmi else 0, 2)}, mescola il temperamento con le altre differenze fra i giocatori.")
    if g["esperti"]["azioni"] and g["inesperti"]["azioni"]:
        esp = 100 * g["esperti"]["falli"] / g["esperti"]["azioni"]
        ines = 100 * g["inesperti"]["falli"] / g["inesperti"]["azioni"]
        righe.append(f"Esperienza, ogni 100 azioni: chi ha esperienza da 10 in su fa {numero(esp, 2)} falli, chi è sotto 1 ne fa {numero(ines, 2)}.")
        bersagli.append(("Falli in meno degli esperti, per cento", 100 * (1 - esp / ines) if ines else 0, (18, 35)))
    letture = banco.lettura
    for nome, intervallo in (("esperti", (60, 100)), ("inesperti", (35, 55))):
        if letture[nome]["laterali"]:
            quota = per_cento(letture[nome]["debole"], letture[nome]["laterali"])
            righe.append(f"Lettura del gioco: contro un difensore con un lato debole, gli {nome} mandano lì il {numero(quota)} per cento degli attacchi laterali.")
            bersagli.append((f"Attacchi laterali sul lato debole, {nome}", quota, intervallo))
    for nome, valori in banco.fatica.items():
        if valori:
            intervallo = (0.86, 0.93) if nome.startswith("trentenni") else (0.72, 0.82)
            righe.append(f"Stanchezza a fine incontro al meglio di 5, {nome}: efficienza media {numero(statistics.fmean(valori), 3)}, minima {numero(min(valori), 3)}, su {len(valori)} incontri.")
            bersagli.append((f"Efficienza finale, {nome}", statistics.fmean(valori), intervallo))
    if banco.infortuni:
        nuova = statistics.fmean(p for p, _ in banco.infortuni)
        vecchia = statistics.fmean(v for _, v in banco.infortuni)
        righe.append(f"Infortuni, chi non è ambidestro: probabilità media per partita {numero(nuova, 3)} per cento, contro {numero(vecchia, 3)} del vecchio calcolo.")
        if set_al_meglio == 3 and not pari_forti:
            # Il bersaglio vale al meglio dei 3 e fra coppie a caso: al meglio dei 5, e fra pari
            # forti, le partite sono più lunghe, il carico più alto, e gli infortuni anche.
            bersagli.append(("Infortuni rispetto a prima, per cento", 100 * nuova / vecchia if vecchia else 0, (90, 110)))
    if banco.durate:
        righe.append(f"Durata simulata: in media {numero(statistics.fmean(banco.durate) / 60)} minuti, da {numero(min(banco.durate) / 60)} a {numero(max(banco.durate) / 60)}; "
                     f"incontri con le invarianti violate: {banco.invarianti}.")
        bersagli.append(("Durata simulata media in minuti", statistics.fmean(banco.durate) / 60, (12, 20)))
    for righe_sonda, bersagli_sonda in sonde:
        righe.extend(righe_sonda)
        bersagli.extend(bersagli_sonda)
    righe.append("I bersagli della taratura:")
    for nome, valore, intervallo, *giudizio in bersagli:
        esito = giudizio[0] if giudizio else esito_bersaglio(valore, intervallo)
        righe.append(f"{nome}: {numero(valore, 2)}, bersaglio da {numero(intervallo[0], 2)} a {numero(intervallo[1], 2)}, {esito}.")
    return righe


# I casi della sonda della stanchezza: descrizione, anni, resistenza innata e allenata, dove si
# misura e bersaglio. Sono giocatori che nel mondo possono esistere: la resistenza innata nasce fra
# 0 e 3 e non cresce, l'allenata arriva a 5. I primi due sono quelli del punto 18.16 del progetto,
# misurati su tutti gli incontri al meglio di 5; il trentenne, che il progetto voleva con
# resistenza 5, è riletto con la resistenza innata più alta, 3, senza allenamento, perché una
# resistenza 5 senza allenamento non esiste, e dalla decisione D26 l'allenamento conta anche da
# solo. Gli altri due vengono dalla decisione D26, e si misurano a fine quinto set: il giovane ha
# la resistenza più alta che si possa avere, 3 innata e 5 allenata.
CASI_FATICA = (
    ("un trentenne con resistenza 3, la più alta innata, che non si allena", 30, 3.0, 0.0, "tutti", (0.86, 0.93)),
    ("un sessantenne con resistenza 2", 60, 2.0, 0.0, "tutti", (0.72, 0.82)),
    ("un giovane di 24 anni con resistenza 8, la più alta possibile, 3 innata e 5 allenata", 24, 3.0, 5.0, "quinto", (0.94, 1.0)),
    ("un anziano di 65 anni con resistenza 1,5, che non si allena", 65, 1.5, 0.0, "quinto", (0.6, 0.78)),
)


def sonda_fatica(giocatori, quante, rng, opzioni):
    """
    La stanchezza a fine incontro al meglio di 5. Ogni caso nasce da giocatori a caso, cambiando età
    e resistenza: la popolazione di prova nasce fra 9 e 45 anni, e senza la sonda gli anziani non ci
    sarebbero. I casi del punto 18.16 del progetto, il trentenne e il sessantenne, giocano contro
    avversari a caso, e conta la media di tutti gli incontri. I casi della decisione D26, il giovane
    molto resistente e allenato che deve reggere cinque set senza risentirne troppo, e l'anziano
    poco resistente che invece perde molto, giocano contro il proprio gemello, uguale a lui, perché
    l'incontro sia equilibrato e arrivi spesso al quinto set: conta l'efficienza a fine quinto set.
    """
    righe = []
    for descrizione, anni, innata, allenata, dove, intervallo in CASI_FATICA:
        efficienze = []
        for _ in range(quante):
            g, avversario = rng.sample(giocatori, 2)
            g = copy.copy(g)
            g.eta = costanti.giorni_da_anni(anni)
            g.resistenza_base, g.resistenza_allenata = innata, allenata
            if dove == "quinto":
                avversario = copy.copy(g)
                avversario.id = g.id + 10_000_000
            risultato = simula_incontro(g, avversario, formato_singolare(5), seme=rng.getrandbits(63), **opzioni)
            if dove == "tutti" or len(risultato.set) == 5:
                efficienze.append(risultato.statistiche[g.id].eff_finale)
        if not efficienze:
            righe.append(f"Sonda della stanchezza, {descrizione}: nessun incontro arrivato al quinto set su {quante}.")
            continue
        media = statistics.fmean(efficienze)
        quali = f"{quante} incontri al meglio di 5" if dove == "tutti" else f"{len(efficienze)} incontri arrivati al quinto set su {quante}, contro il gemello"
        righe.append(f"Sonda della stanchezza, {descrizione}, {quali}: efficienza finale media {numero(media, 3)}, minima {numero(min(efficienze), 3)}, "
                     f"bersaglio da {numero(intervallo[0], 2)} a {numero(intervallo[1], 2)}, {esito_bersaglio(media, intervallo)}; "
                     f"mai sotto 0,6: {'sì' if min(efficienze) >= 0.6 else 'NO'}.")
    return righe


def sonda_temperamento(giocatori, quante, rng, opzioni, formato):
    """
    Il bersaglio 18.8 del progetto misurato a coppie: lo stesso giocatore, una volta impetuoso e
    una volta calmo, contro lo stesso avversario e con lo stesso seme, così che fra le due
    partite cambi soltanto il temperamento. I due temperamenti sono quelli medi dei gruppi del
    banco, chi sta da 75 in su e chi sta fino a 25, nella popolazione in prova. Il confronto
    fra gruppi di giocatori diversi era confuso dalle altre differenze fra loro: con tutti i
    temperamenti portati a 50 il rapporto dei falli restava 1,12 invece di 1.
    Restituisce le righe e i bersagli per il rapporto.
    """
    attuali = [g.temperamento_attuale for g in giocatori]
    impetuosi = [t for t in attuali if t >= 75] or [80.0]
    calmi = [t for t in attuali if t <= 25] or [20.0]
    livelli = (("impetuoso", statistics.fmean(impetuosi)), ("calmo", statistics.fmean(calmi)))
    conti = {nome: Counter() for nome, _livello in livelli}
    opzioni = {**opzioni, "dettaglio": ESSENZIALE}
    for _ in range(quante):
        g, avversario = rng.sample(giocatori, 2)
        seme = rng.getrandbits(63)
        for nome, livello in livelli:
            copia = copy.copy(g)
            # Il temperamento innato che, con la calma dell'età, dà proprio il livello cercato.
            copia.temperamento = min(100.0, livello + costanti.CALMA_PER_ANNO * max(0.0, g.eta_anni - costanti.ETA_INIZIO_CALMA))
            stats = simula_incontro(copia, avversario, formato, seme=seme, **opzioni).statistiche[g.id]
            conti[nome]["falli"] += sum(stats.falli.values())
            conti[nome]["goal"] += stats.goal
            conti[nome]["attacchi"] += stats.attacchi
    per_cento_attacchi = {nome: (100 * c["falli"] / c["attacchi"], 100 * c["goal"] / c["attacchi"]) for nome, c in conti.items() if c["attacchi"]}
    if len(per_cento_attacchi) < 2:
        return [], []
    (falli_imp, goal_imp), (falli_calmi, goal_calmi) = per_cento_attacchi["impetuoso"], per_cento_attacchi["calmo"]
    righe = [f"Sonda del temperamento, {quante} coppie di partite: gli stessi giocatori con temperamento {numero(livelli[0][1], 0)} e {numero(livelli[1][1], 0)}, "
             f"contro gli stessi avversari e con gli stessi semi. Ogni 100 attacchi l'impetuoso fa {numero(falli_imp)} falli e {numero(goal_imp)} goal, "
             f"il calmo {numero(falli_calmi)} falli e {numero(goal_calmi)} goal."]
    bersagli = [("Falli degli impetuosi su quelli dei calmi, a coppie", falli_imp / falli_calmi if falli_calmi else 0, (1.35, 1.7))]
    return righe, bersagli


def squadra_a_caso(giocatori, nome, rng, usati):
    """Una squadra valida di 3 a 6 giocatori presi a caso fra quelli non ancora usati."""
    liberi = [g for g in giocatori if g.id not in usati]
    for _tentativo in range(200):
        quanti = rng.randint(3, 6)
        scelti = rng.sample(liberi, quanti)
        if composizione_valida(scelti[:3]):
            usati.update(g.id for g in scelti)
            return Squadra(nome, tuple(scelti))
    sys.exit("Non si è trovata una squadra valida.")


def gioca_squadre(giocatori, quante, rng, opzioni):
    punti, segnati, timeout, durate = [], [], 0, []
    for i in range(quante):
        usati = set()
        a = squadra_a_caso(giocatori, f"Squadra A{i}", rng, usati)
        b = squadra_a_caso(giocatori, f"Squadra B{i}", rng, usati)
        risultato = simula_incontro(a, b, SQUADRE, seme=rng.getrandbits(63), **opzioni)
        punti.append(risultato.incontro.punti_giocati)
        segnati.append(sum(risultato.set[0]))
        timeout += len(risultato.incontro.timeout)
        if risultato.durata_simulata:
            durate.append(risultato.durata_simulata)
    righe = [f"Squadre: {quante} gare, in media {numero(statistics.fmean(punti))} punti giocati, da {min(punti)} a {max(punti)}; {timeout} time-out, nessuna sostituzione durante la gara."]
    if durate:
        righe.append(f"Durata simulata delle gare a squadre: in media {numero(statistics.fmean(durate) / 60)} minuti.")
    righe.append(f"Punti segnati per gara a squadre, la somma del punteggio: {numero(statistics.fmean(segnati), 2)}, bersaglio da 50 a 75, {esito_bersaglio(statistics.fmean(segnati), (50, 75))}.")
    return righe


def main():
    parser = argparse.ArgumentParser(description="Banco di prova del motore di partita di MESS: simula partite in memoria, senza scrivere nulla.")
    parser.add_argument("--partite", type=int, default=1000, help="quante partite simulare, 1000 se non indicato")
    parser.add_argument("--set", type=int, choices=(3, 5), default=3, help="partite al meglio dei 3 o dei 5 set, 3 se non indicato")
    parser.add_argument("--mondo", choices=("nuovo", "salvato"), default="nuovo", help="una popolazione di prova, oppure i giocatori del mondo salvato")
    parser.add_argument("--giocatori", type=int, default=400, help="quanti giocatori generare con --mondo nuovo, 400 se non indicato")
    parser.add_argument("--seme", type=int, default=None, help="il seme del banco, per ripetere una prova identica")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il rapporto anche in questo file")
    parser.add_argument("--dettaglio", choices=(ESSENZIALE, COMPLETO), default=ESSENZIALE, help="la modalità del motore; completo controlla anche le invarianti")
    parser.add_argument("--pari-forti", action="store_true", help="coppie del quarto più forte, con un distacco sotto il 3 per cento")
    parser.add_argument("--squadre", type=int, default=0, help="gioca anche tante gare a squadre")
    parser.add_argument("--senza-procedure", action="store_true", help="time-out e riscaldamento spenti, per la prova di neutralità")
    parser.add_argument("--taratura", type=Path, default=None, help="un file JSON di sostituzioni della taratura")
    parser.add_argument("--allenati", type=float, default=0.6, help="la quota di allenati della popolazione di prova, 0,6 se non indicata")
    parser.add_argument("--esperienza", type=float, default=12.0, help="l'esperienza massima della popolazione di prova, 12 se non indicata")
    argomenti = parser.parse_args()
    seme = argomenti.seme if argomenti.seme is not None else random.randrange(1_000_000)
    rng = random.Random(seme)
    taratura = carica_taratura(argomenti.taratura) if argomenti.taratura else TARATURA
    if argomenti.mondo == "salvato":
        giocatori = carica_mondo_salvato()
        descrizione = f"Mondo salvato in {costanti.FILE_MONDO}"
    else:
        giocatori = genera(argomenti.giocatori, seme, quota_allenati=argomenti.allenati, esperienza=(0, argomenti.esperienza))
        descrizione = f"Popolazione di prova con il {numero(100 * argomenti.allenati, 0)} per cento di allenati e l'esperienza fino a {numero(argomenti.esperienza, 0)}"
    disponibili = [g for g in giocatori if g.puo_giocare]
    if len(disponibili) < 2:
        sys.exit("Servono almeno due giocatori che possano giocare.")
    indici = sorted(g.indice_collettivo_valore for g in disponibili)
    formato = formato_singolare(argomenti.set)
    opzioni = {"dettaglio": argomenti.dettaglio, "taratura": taratura}
    if argomenti.senza_procedure:
        opzioni.update(riscaldamento=False, timeout=False)
    coppie = coppie_pari_forti(disponibili, argomenti.partite, rng) if argomenti.pari_forti else [tuple(rng.sample(disponibili, 2)) for _ in range(argomenti.partite)]
    banco = Banco(taratura)
    inizio = time.perf_counter()
    for a, b in coppie:
        risultato = simula_incontro(a, b, formato, seme=rng.getrandbits(63), **opzioni)
        banco.aggiungi(a, b, risultato, argomenti.dettaglio == COMPLETO)
    durata = time.perf_counter() - inizio
    tipo_coppie = "coppie di forti alla pari" if argomenti.pari_forti else "coppie estratte a caso"
    intestazione = [
        f"Banco di prova del motore di partita, MESS versione {__version__}, {time.strftime('%Y-%m-%d %H:%M')}.",
        f"{descrizione}: {len(giocatori)} giocatori, {len(disponibili)} disponibili, cioè che possono giocare.",
        f"Indice di valore dei disponibili: minimo {numero(indici[0], 0)}, mediana {numero(statistics.median(indici), 0)}, massimo {numero(indici[-1], 0)}.",
        f"{argomenti.partite} partite al meglio dei {argomenti.set} set fra {tipo_coppie}, in modalità {argomenti.dettaglio}, giocate in {numero(durata)} secondi, "
        f"cioè {numero(1000 * durata / argomenti.partite, 2)} millisecondi a partita, con il seme {seme}: per ripetere la prova identica si aggiunge --seme {seme}.",
    ]
    if argomenti.taratura:
        intestazione.append(f"Taratura letta da {argomenti.taratura}.")
    sonde = [sonda_temperamento(disponibili, 400, rng, opzioni, formato)]
    righe = rapporto(banco, intestazione, argomenti.pari_forti, argomenti.set, sonde)
    if argomenti.set == 5:
        # Quattrocento incontri per caso: dei giovani e degli anziani contro il gemello arriva al
        # quinto set meno della metà, e con duecento la media oscillava di un centesimo.
        righe.extend(sonda_fatica(disponibili, 400, rng, opzioni))
    if argomenti.squadre:
        righe.extend(gioca_squadre(disponibili, argomenti.squadre, rng, opzioni))
    testo = "\n".join(righe)
    print(testo)
    if argomenti.rapporto:
        argomenti.rapporto.write_text(testo + "\n", encoding="utf-8")
        print(f"Rapporto salvato in {argomenti.rapporto}.")


if __name__ == "__main__":
    main()
