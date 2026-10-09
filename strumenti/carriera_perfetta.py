"""
La carriera perfetta di MESS e i mondi sintetici, per fissare la classe e il ritmo dell'allenamento.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-09 con la tappa 11, decisione D31 e punto 12.3 del progetto della tappa. Usa le
funzioni vere di allenamento.py, tratti.py, esperienza.py e il motore di partita, non scrive niente
nel progetto e alla fine stampa il blocco da copiare in costanti.py.
La carriera di riferimento, decisa da Gabriele: il nato al novantesimo percentile del valore, senza
tratti speciali né tratti rari dell'allenamento, scelto fra 4.000 nati col seme 11, entra a 9 anni
in una polisportiva ed esce a 50, 4428 giorni simulati; si allena ogni giorno a intensità normale,
senza infortuni, e nel 90 per cento dei giorni, presi con un contatore fisso, gioca un'amichevole
al meglio dei 3 col motore vero, in modalità essenziale, contro un avversario del mondo sintetico
all'anno 10; i punti vengono dalla formula vera, con il premio al più debole; ha l'esperienza di
tutte le fonti, con un gruppo di esperienza media 5, e spende ogni giorno secondo completa, la
spesa che rende più valore. Un tesserato all'intensa senza infortuni può superarla, e resta A1.
I mondi sintetici: il mondo giovane, nato da zero, a un certo anno, e quello a regime, con le età
della decisione D18; ogni giocatore si allena dal suo ingresso con la seduta e la spesa della sua
indole, il 90 per cento dei giorni da tesserato, con il declino dai 50 anni e il calo dei livelli
alti, a passi di un anno. Servono agli avversari, alle lettere della classe e ai conti della
risposta 6 di Gabriele, i tetti propri dell'allenata tolti.
Lo strumento stampa: la somma della carriera perfetta, il valore e l'esperienza a 20, 30, 40 e 50
anni; l'esperienza del giorno in polisportiva che porta a 20 a 50 anni; le ancore della classe;
i casi del punto 7 con la loro classe; i punti attesi per amichevole secondo il distacco; le lettere
nei mondi sintetici; l'allenata più alta della carriera perfetta; la tabella degli specialisti; i
giocatori dei mondi sintetici sopra lo 0,45, lo 0,7 e le bande della popolazione di prova; e il
valore che cento punti comprano su ogni caratteristica, per lo stesso giocatore alla stessa età,
perché il costo è tarato sul valore e un punto deve comprare più o meno lo stesso valore qualunque
cosa si alleni: la differenza viene soltanto dal livello relativo da cui si parte.
Uso, dalla cartella del progetto o da qualunque altra:
    python strumenti/carriera_perfetta.py
    python strumenti/carriera_perfetta.py --costo 50 --crescita 2,5 --rapporto carriera.txt
    python strumenti/carriera_perfetta.py --veloce
Con --tornei e --sfide, a zero finché non c'è la tappa 12, la carriera gioca anche tanti incontri al
mese di torneo e di sfida, con i loro punti e la loro esperienza.
"""

import argparse
import copy
import datetime
import math
import random
import statistics
import sys
import time
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

import allenamento  # noqa: E402
import classe  # noqa: E402
import costanti  # noqa: E402
import economia  # noqa: E402
import esperienza  # noqa: E402
import valore  # noqa: E402
from modelli import Giocatore  # noqa: E402
from motore import ESSENZIALE, formato_singolare, simula_incontro  # noqa: E402
from partita import MotorePartita  # noqa: E402

NASCITA = datetime.datetime(2026, 1, 1)  # noqa: DTZ001 - data segnaposto, come quelle del motore
GIORNI_ANNO = costanti.ANNO_SIMULAZIONE_GIORNI
ETA_INGRESSO, ETA_USCITA = 9.0, 50.0
GIORNI_CARRIERA = int((ETA_USCITA - ETA_INGRESSO) * GIORNI_ANNO)
QUOTA_AMICHEVOLI = 0.9
FATTORE_GRUPPO = 1.0 + costanti.K_GRUPPO_ESPERIENZA * 5.0 / costanti.ESPERIENZA_MASSIMA
TAPPE = (20, 30, 40, 50)
# I punti attesi per amichevole dei casi dell'utente, misurati dalla carriera: il mediano 3,1 e il bravo 3,5.
PUNTI_AMICHEVOLE_MEDIANO = 3.1
PUNTI_AMICHEVOLE_BRAVO = 3.5
# Le bande dell'allenata della popolazione di prova, i vecchi tetti.
BANDE = {"fisica": 5.0, "gioco": 20.0}
SPECIALITA = ("triplaspondasx", "lungolineasx", "battutasx", "chiusurasx", "difesa", "precisione", "resistenza")
_FISICHE = ("precisione", "resistenza", "forza")


def numero(valore_numerico, decimali=1):
    return f"{valore_numerico:.{decimali}f}".replace(".", ",")


def imposta_ritmo(costo, crescita):
    """Il ritmo dell'allenamento da provare, soltanto nel modulo caricato per questa misura."""
    allenamento.COSTO_PER_PUNTO_PESATO = costo
    allenamento._K = crescita
    allenamento._EXP_K = math.exp(crescita)


def nati(quanti, seme, primo_id=1):
    """I nati del generatore vero, col caso del mondo seminato e poi rimesso com'era; ipovedenti come nel mondo."""
    stato = random.getstate()
    random.seed(seme)
    try:
        return [Giocatore(primo_id + i, NASCITA, ipovedente=random.uniform(0, 100) < costanti.PROBABILITA_IPOVEDENTE_CREAZIONE) for i in range(quanti)]
    finally:
        random.setstate(stato)


def senza_tratti(g):
    """Vero per chi non ha tratti speciali né tratti rari dell'allenamento."""
    return not (g.mancino or g.ambidestro or g.giocorapido or g.cambiovelocita or g.talento or g.apprendista_rapido or g.maturazione)


def al_percentile(gruppo, quota):
    ordinati = sorted(gruppo, key=valore.somma_pesata)
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))]


def percentile(valori, quota):
    ordinati = sorted(valori)
    return ordinati[min(len(ordinati) - 1, int(len(ordinati) * quota))] if ordinati else 0.0


def pronto(g, anni):
    """Una copia del giocatore all'età indicata, senza allenamento, esperienza, costanza né punti."""
    copia = copy.deepcopy(g)
    copia.eta = int(anni * GIORNI_ANNO)
    copia.esperienza = copia.costanza = copia.punti_allenamento = 0.0
    copia.diario = []
    copia.aggiorna_icv()
    return copia


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
        g.esperienza = min(costanti.ESPERIENZA_MASSIMA, g.esperienza + per_anno * tratto)
        g.eta = int((anni + tratto) * GIORNI_ANNO)
        if anni + tratto > 50.0:
            g._applica_declino_aggregato(int(giorni))
        anni += tratto
    g.aggiorna_icv()
    return g


def mondo_sintetico(quanti, anni_mondo, seme, primo_id=100_000):
    """
    I giocatori in attività di un mondo nato anni_mondo anni fa, o a regime con None: ingresso fra 9
    e 45 anni, ritiro fra 58 e 75, morte fra 70 e 103, l'uscita prematura; ciascuno si allena dal
    suo ingresso secondo la sua indole, il 90 per cento dei giorni da tesserato.
    """
    rng = random.Random(f"sintetico-{seme}-{anni_mondo}")
    candidati = nati(quanti * 2, seme, primo_id)
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
        g.esperienza = min(costanti.ESPERIENZA_MASSIMA, da_quanto * (costanti.ESPERIENZA_PER_ANNO_DI_VITA + 0.9 * esperienza.ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA * GIORNI_ANNO * FATTORE_GRUPPO))
        giocatori.append(g)
    return giocatori


def amichevole(g, avversario, rng, distacchi):
    """Un'amichevole al meglio dei 3 col motore vero, in modalità essenziale: i punti allenamento della formula vera, con il premio al più debole."""
    risultato = simula_incontro(g, avversario, formato_singolare(3), seme=rng.getrandbits(63), dettaglio=ESSENZIALE)
    mie, sue = risultato.set_vinti
    if risultato.vincitore == "A":
        punti, _altri = MotorePartita.punti_della_partita(mie, sue)
    else:
        _altri, punti = MotorePartita.punti_della_partita(sue, mie)
    if MotorePartita.piu_debole(g, avversario) is g:
        punti += costanti.PA_BONUS_PIU_DEBOLE
    distacchi.append((valore.somma_pesata(g) + valore.bonus_tratti(g) - valore.somma_pesata(avversario) - valore.bonus_tratti(avversario), punti))
    return punti


def carriera(g0, avversari, seme, da=ETA_INGRESSO, a=ETA_USCITA, quota_amichevoli=QUOTA_AMICHEVOLI, programma="completa", tornei=0.0, sfide=0.0, motore=True,
             punti_amichevole=3.1, tappe=TAPPE):
    """
    La carriera giorno per giorno: la seduta a intensità normale, la costanza, l'esperienza col
    fattore del gruppo, le amichevoli col contatore fisso, la spesa del giorno secondo il programma,
    il calo dei livelli alti a ogni mese di trenta giorni. Restituisce il giocatore alla fine, le
    tappe con somma, valore, esperienza, allenata più alta e livello relativo più alto, e i distacchi.
    """
    rng = random.Random(f"carriera-{seme}")
    g = pronto(g0, da)
    contatore = 0.0
    distacchi = []
    registro = {}
    allenata_massima = 0.0
    for giorno in range(int((a - da) * GIORNI_ANNO)):
        g.punti_allenamento += costanti.PA_SEDUTA
        g.costanza = g.costanza * costanti.DECADIMENTO_COSTANZA + (1 - costanti.DECADIMENTO_COSTANZA)
        esperienza.del_giorno(g, True, FATTORE_GRUPPO)
        contatore += quota_amichevoli
        if contatore >= 1.0 - 1e-9:
            contatore -= 1.0
            g.punti_allenamento += amichevole(g, rng.choice(avversari), rng, distacchi) if motore else punti_amichevole
            esperienza.da_partita(g, esperienza.AMICHEVOLE)
            g.costanza += (1 - costanti.DECADIMENTO_COSTANZA) * costanti.COSTANZA_PER_PARTITA
        for quanti, tipo, bonus in ((tornei, esperienza.TORNEO, costanti.PA_BONUS_TORNEO), (sfide, esperienza.SFIDA, costanti.PA_BONUS_SFIDA)):
            if quanti and giorno % 30 == 0:
                for _ in range(int(quanti)):
                    g.punti_allenamento += 3.1 + bonus
                    esperienza.da_partita(g, tipo)
        allenamento.allena_secondo_programma(g, programma=programma)
        if giorno % 30 == 29:
            allenamento.mantenimento_del_mese(g, 30)
        g.eta += 1
        allenata_massima = max(allenata_massima, *(getattr(g, c + "_allenata") for c in allenamento.CARATTERISTICHE))
        anni = round(g.eta / GIORNI_ANNO, 6)
        if anni in tappe:
            registro[int(anni)] = {"somma": classe.somma_classe(g), "valore": g.indice_collettivo_valore, "esperienza": g.esperienza,
                                   "allenata": allenata_massima, "relativo": max(allenamento.livello_relativo(g, c) for c in allenamento.CARATTERISTICHE)}
    return g, registro, distacchi


def amichevoli_della_carriera(quota=QUOTA_AMICHEVOLI, giorni=GIORNI_CARRIERA):
    """Quante amichevoli fa la carriera con il contatore fisso."""
    contatore, quante = 0.0, 0
    for _ in range(giorni):
        contatore += quota
        if contatore >= 1.0 - 1e-9:
            contatore -= 1.0
            quante += 1
    return quante


def esperienza_per_giorno(amichevoli):
    """L'esperienza del giorno in polisportiva che porta la carriera perfetta a 20 a 50 anni, con le altre fonti."""
    altre = costanti.ESPERIENZA_PER_ANNO_DI_VITA * (ETA_USCITA - ETA_INGRESSO) + costanti.ESPERIENZA_PER_AMICHEVOLE * amichevoli
    return (costanti.ESPERIENZA_MASSIMA - altre) / (GIORNI_CARRIERA * FATTORE_GRUPPO)


def punteggio(somma, esp, somma_perfetta):
    return costanti.PESO_VALORE_CLASSE * somma / somma_perfetta + costanti.PESO_ESPERIENZA_CLASSE * min(1.0, esp / costanti.ESPERIENZA_MASSIMA)


def specialista(g0, caratteristica, da, punti_amichevole):
    """Chi spende tutto su una caratteristica, con un'amichevole ogni due giorni: il livello relativo alle età, il più alto, quando passa 0,7 e 0,9, l'allenata persa col calo."""
    g = pronto(g0, da)
    risultati = {"tappe": {}, "massimo": 0.0, "passa_07": None, "passa_09": None, "perso": 0.0}
    for giorno in range(int((ETA_USCITA - da) * GIORNI_ANNO)):
        g.punti_allenamento += costanti.PA_SEDUTA + 0.5 * punti_amichevole
        if allenamento.totale(g, caratteristica) < allenamento.tetto(caratteristica) - 1e-6:
            allenamento.spendi(g, caratteristica, g.punti_allenamento)
        if giorno % 30 == 29:
            prima = getattr(g, caratteristica + "_allenata")
            allenamento.mantenimento_del_mese(g, 30)
            risultati["perso"] += prima - getattr(g, caratteristica + "_allenata")
        g.eta += 1
        anni = g.eta / GIORNI_ANNO
        relativo = allenamento.livello_relativo(g, caratteristica)
        risultati["massimo"] = max(risultati["massimo"], relativo)
        for soglia, chiave in ((0.7, "passa_07"), (0.9, "passa_09")):
            if relativo >= soglia and risultati[chiave] is None:
                risultati[chiave] = anni
        if round(anni, 6) in (25, 30, 40, 50):
            risultati["tappe"][round(anni)] = relativo
    return risultati


def valore_per_punto_speso(g0, anni, punti=100.0):
    """
    Quanta somma pesata e quanto valore comprano tanti punti spesi su una caratteristica sola, per
    ognuna delle 24, partendo dallo stesso giocatore alla stessa età: elenco di quaterne con la
    caratteristica, il livello relativo di partenza, la somma pesata e il valore comprati.
    """
    righe = []
    for c in allenamento.CARATTERISTICHE:
        g = pronto(g0, anni)
        g.punti_allenamento = punti
        relativo = allenamento.livello_relativo(g, c)
        somma, indice = valore.somma_pesata(g), g.indice_collettivo_valore
        allenamento.spendi(g, c, punti)
        righe.append((c, relativo, valore.somma_pesata(g) - somma, g.indice_collettivo_valore - indice))
    return righe


def sopra_le_soglie(giocatori):
    """Quanti giocatori hanno una caratteristica sopra lo 0,45 e lo 0,7 del tetto, e l'allenata sopra le bande della popolazione di prova; il livello relativo più alto."""
    sopra_45 = sopra_70 = fuori = 0
    massimo = 0.0
    for g in giocatori:
        relativi = [allenamento.livello_relativo(g, c) for c in allenamento.CARATTERISTICHE]
        massimo = max(massimo, *relativi)
        sopra_45 += max(relativi) > 0.45
        sopra_70 += max(relativi) > 0.7
        fuori += any(getattr(g, c + "_allenata") > (BANDE["fisica"] if c in _FISICHE else BANDE["gioco"]) + 1e-9 for c in allenamento.CARATTERISTICHE)
    return sopra_45, sopra_70, fuori, massimo


def lettere(giocatori):
    conta = {}
    for g in giocatori:
        lettera = classe.classe(g).codice[0]
        conta[lettera] = conta.get(lettera, 0) + 1
    return ", ".join(f"{lettera} {numero(100 * quanti / len(giocatori))}" for lettera, quanti in sorted(conta.items()))


def main():
    parser = argparse.ArgumentParser(description="La carriera perfetta e i mondi sintetici di MESS: somma, esperienza, ancore della classe e casi tipici.")
    parser.add_argument("--costo", type=lambda t: float(t.replace(",", ".")), default=costanti.COSTO_PER_PUNTO_PESATO, help="il ritmo C0, quello di costanti.py se non indicato")
    parser.add_argument("--crescita", type=lambda t: float(t.replace(",", ".")), default=costanti.CRESCITA_DEL_COSTO, help="la crescita del costo K, quella di costanti.py se non indicata")
    parser.add_argument("--tornei", type=float, default=0.0, help="incontri di torneo al mese nella carriera, per la tappa 12")
    parser.add_argument("--sfide", type=float, default=0.0, help="sfide al mese nella carriera, per la tappa 12")
    parser.add_argument("--giocatori", type=int, default=3000, help="i giocatori di ogni mondo sintetico, 3000 se non indicato")
    parser.add_argument("--veloce", action="store_true", help="mondi sintetici da 600 giocatori e niente tabella degli specialisti")
    parser.add_argument("--rapporto", type=Path, default=None, help="salva il racconto anche in questo file")
    argomenti = parser.parse_args()
    inizio = time.perf_counter()
    imposta_ritmo(argomenti.costo, argomenti.crescita)
    quanti = 600 if argomenti.veloce else argomenti.giocatori
    righe = []

    def scrivi(riga):
        righe.append(riga)
        print(riga, flush=True)

    scrivi(f"Carriera perfetta e mondi sintetici, ritmo C0 {numero(argomenti.costo)} e K {numero(argomenti.crescita, 2)}, tornei {numero(argomenti.tornei)} e sfide "
           f"{numero(argomenti.sfide)} al mese. La carriera di riferimento si allena a intensità normale: un tesserato all'intensa senza infortuni può superarla, e resta A1.")
    amichevoli = amichevoli_della_carriera()
    # Arrotondata per eccesso alla quinta cifra, quella che si copia in costanti.py: così la carriera arriva a 20 un poco prima dei 50 anni, e non un soffio sotto.
    per_giorno = math.ceil(esperienza_per_giorno(amichevoli) * 1e5) / 1e5
    esperienza.ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA = per_giorno
    scrivi(f"La carriera gioca {amichevoli} amichevoli in {GIORNI_CARRIERA} giorni; l'esperienza del giorno in polisportiva che la porta a 20 a 50 anni è {per_giorno:.6f}.")
    mondo_10 = mondo_sintetico(quanti, 10, 2026)
    scrivi(f"Mondo sintetico all'anno 10: {len(mondo_10)} giocatori, pronto in {numero(time.perf_counter() - inizio)} secondi.")
    nati_11 = nati(4000, 11)
    puliti = [g for g in nati_11 if senza_tratti(g)]
    riferimento = al_percentile(puliti, 0.9)
    perfetto, tappe, distacchi = carriera(riferimento, mondo_10, 11, tornei=argomenti.tornei, sfide=argomenti.sfide)
    somma_perfetta = tappe[50]["somma"]
    scrivi(f"Carriera perfetta, il nato numero {riferimento.id} al novantesimo percentile senza tratti, somma pesata da nato {numero(valore.somma_pesata(riferimento))}: "
           + "; ".join(f"a {anni} anni somma {numero(t['somma'])}, valore {numero(t['valore'])}, esperienza {numero(t['esperienza'], 2)}, "
                       f"allenata più alta {numero(t['allenata'])}, livello relativo più alto {numero(t['relativo'], 2)}" for anni, t in sorted(tappe.items())) + ".")
    scrivi(f"La carriera perfetta non tocca le bande della popolazione di prova: allenata fisica più alta {numero(max(getattr(perfetto, c + '_allenata') for c in _FISICHE))} su 5, "
           f"di gioco {numero(max(getattr(perfetto, c + '_allenata') for c in allenamento.CARATTERISTICHE if c not in _FISICHE))} su 20.")
    fasce = ((-1e9, -50), (-50, -25), (-25, 0), (0, 25), (25, 50), (50, 1e9))
    scrivi("Punti attesi per amichevole secondo il distacco di somma pesata dall'avversario: " + "; ".join(
        f"da {numero(basso, 0)} a {numero(alto, 0)}: {numero(statistics.fmean(p for d, p in distacchi if basso <= d < alto), 2)} su {sum(1 for d, _p in distacchi if basso <= d < alto)}"
        for basso, alto in fasce if any(basso <= d < alto for d, _p in distacchi)) + f"; in media {numero(statistics.fmean(p for _d, p in distacchi), 2)}.")
    # Le ancore della classe.
    somme_nati = sorted(valore.somma_pesata(g) + valore.bonus_tratti(g) for g in nati_11)
    p1 = punteggio(somme_nati[len(somme_nati) // 100], 0.0, somma_perfetta)
    p99 = punteggio(somme_nati[len(somme_nati) * 99 // 100], 0.0, somma_perfetta)
    bravo_nato = al_percentile(puliti, 0.75)
    _bravo, tappe_bravo, _d = carriera(bravo_nato, mondo_10, 15, da=15.0, a=30.0, quota_amichevoli=0.5, tappe=(30,))
    pb = punteggio(tappe_bravo[30]["somma"], tappe_bravo[30]["esperienza"], somma_perfetta)
    ancore = ((100, 0.0), (89, round(p1, 3)), (50, round(p99, 3)), (40, round(pb, 3)), (1, 1.0))
    classe.SOMMA_CARRIERA_PERFETTA = somma_perfetta
    classe.SOGLIE_CLASSE = classe._soglie(ancore)
    classe._SOGLIE_CRESCENTI = tuple(-s for s in classe.SOGLIE_CLASSE)
    scrivi(f"Ancore della classe: nato del primo percentile {numero(p1, 3)}, del novantanovesimo {numero(p99, 3)}, bravo a 30 anni {numero(pb, 3)}, "
           f"con somma {numero(tappe_bravo[30]['somma'])} ed esperienza {numero(tappe_bravo[30]['esperienza'], 2)}. Un livello vale {numero((p99 - p1) / 39, 4)} dalla I alla F, "
           f"{numero((pb - p99) / 10, 4)} dalla E alla D, {numero((1 - pb) / 39, 4)} dalla C alla A.")
    # I casi del punto 7.
    nati_ordinati = sorted(nati_11, key=valore.somma_pesata)
    casi = [(f"nato al {nome}", g) for nome, g in (("decimo percentile", nati_ordinati[len(nati_ordinati) // 10]), ("cinquantesimo", nati_ordinati[len(nati_ordinati) // 2]),
                                                       ("novantesimo", nati_ordinati[len(nati_ordinati) * 9 // 10]), ("più forte su 4000", nati_ordinati[-1]))]
    mediano = al_percentile(puliti, 0.5)
    for anni in (35, 50):
        casi.append((f"mediano del computer, in polisportiva dai 20 anni, a {anni}", allena_a_passi(pronto(mediano, 20), 20, anni, 1.0, mediano.indole)))
    casi.append(("libero mediano a 50 anni", allena_a_passi(pronto(mediano, 25), 25, 50, 0.5, mediano.indole, in_polisportiva=False)))
    for anni in (25, 30, 35, 40):
        casi.append((f"mediano dell'utente dai 20 anni, a {anni}", allena_a_passi(pronto(mediano, 20), 20, anni, 1.0 + 0.5 * PUNTI_AMICHEVOLE_MEDIANO, "completa", amichevoli_al_giorno=0.5)))
    for anni in (30, 40, 50):
        casi.append((f"bravo dell'utente dai 15 anni, a {anni}", allena_a_passi(pronto(bravo_nato, 15), 15, anni, 1.0 + 0.5 * PUNTI_AMICHEVOLE_BRAVO, "completa", amichevoli_al_giorno=0.5)))
    for anni, t in sorted(tappe.items()):
        scrivi(f"Carriera perfetta a {anni} anni: classe {classe.codice(classe.livello(punteggio(t['somma'], t['esperienza'], somma_perfetta)))}, valore {numero(t['valore'])}.")
    for nome, g in casi:
        scrivi(f"Caso, {nome}: classe {classe.classe(g).codice}, valore {numero(g.indice_collettivo_valore)}, esperienza {numero(g.esperienza, 2)}, stipendio {economia.stipendio(g)} euro.")
    # Le lettere nei mondi sintetici, e i giocatori sopra le soglie della risposta 6.
    mondi = {"all'anno 10": mondo_10}
    for anni in (20, 40, None):
        mondi["a regime" if anni is None else f"all'anno {anni}"] = mondo_sintetico(quanti, anni, 2026)
    for nome, giocatori in mondi.items():
        sopra_45, sopra_70, fuori, massimo = sopra_le_soglie(giocatori)
        scrivi(f"Mondo sintetico {nome}: lettere {lettere(giocatori)}. Sopra lo 0,45 del tetto {sopra_45}, sopra lo 0,7 {sopra_70}, oltre le bande della popolazione di prova {fuori}; "
               f"livello relativo più alto {numero(massimo, 2)}; valore mediano {numero(statistics.median(g.indice_collettivo_valore for g in giocatori))}.")
    righe_punto = valore_per_punto_speso(mediano, 25.0)
    comprate = [somma for _c, _x, somma, _v in righe_punto]
    # Corretta per il livello di partenza, la somma comprata è la stessa dappertutto, salvo lo sconto degli ipovedenti: il costo marginale cresce come exp(K per il livello).
    corrette = [somma * math.exp(allenamento._K * x) for _c, x, somma, _v in righe_punto]
    scrivi(f"Cento punti spesi dal mediano a 25 anni su una caratteristica sola comprano da {numero(min(comprate), 2)} a {numero(max(comprate), 2)} punti di somma pesata, "
           f"la mediana {numero(statistics.median(comprate), 2)}, e da {numero(min(v for *_r, v in righe_punto), 2)} a {numero(max(v for *_r, v in righe_punto), 2)} punti di valore; "
           f"portati allo stesso livello relativo, da {numero(min(corrette), 3)} a {numero(max(corrette), 3)}. Caratteristica per caratteristica, il livello di partenza e la somma "
           "comprata: " + "; ".join(f"{c} {numero(x, 2)} e {numero(somma, 2)}" for c, x, somma, _v in righe_punto) + ".")
    if not argomenti.veloce:
        for nome, g0, da, punti in (("mediano", mediano, 20.0, PUNTI_AMICHEVOLE_MEDIANO), ("bravo", bravo_nato, 15.0, PUNTI_AMICHEVOLE_BRAVO)):
            for c in SPECIALITA:
                r = specialista(g0, c, da, punti)
                tappe_testo = ", ".join(f"{anni} anni {numero(r['tappe'].get(anni, 0.0), 2)}" for anni in (25, 30, 40, 50))
                passaggi = ", ".join(f"passa {soglia} a {numero(r[chiave]) + ' anni' if r[chiave] else 'mai'}" for soglia, chiave in (("0,7", "passa_07"), ("0,9", "passa_09")))
                scrivi(f"Specialista, il {nome} dell'utente che spende tutto su {c}: livello relativo {tappe_testo}; il più alto {numero(r['massimo'], 2)}; {passaggi}; "
                       f"allenata persa col calo {numero(r['perso'])}.")
    scrivi("Il blocco da copiare in costanti.py:")
    scrivi(f"ESPERIENZA_PER_GIORNO_IN_POLISPORTIVA = {per_giorno:.5f}")
    scrivi(f"SOMMA_CARRIERA_PERFETTA = {somma_perfetta:.1f}")
    scrivi(f"ANCORE_CLASSE = {ancore!r}")
    scrivi(f"PESI_CLASSE = {costanti.PESI_VALORE!r}")
    scrivi(f"PESI_TRATTI_CLASSE = {costanti.PESI_TRATTI!r}")
    scrivi(f"Misura completata in {numero(time.perf_counter() - inizio)} secondi.")
    if argomenti.rapporto:
        argomenti.rapporto.write_text("\n".join(righe) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
