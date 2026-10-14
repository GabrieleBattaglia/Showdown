"""
L'esito rapido di MESS: gli incontri del mondo senza il motore, tarati sul motore.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, modalità auto).
Nasce il 2026-10-13 con la tappa 12, decisione D32 e punto 6 del progetto. Le partite con almeno un
tesserato dell'utente si giocano col motore vero; tutte le altre, migliaia al giorno nel mondo a
regime, con l'esito rapido, che dà le stesse percentuali di vittoria e le stesse lunghezze dei set,
quaranta volte più in fretta. Come il motore, il modulo non conosce wx né il mondo.
Il giocatore ha una forza: la somma dei pesi per i livelli relativi delle 24 caratteristiche del
valore, più i pesi dei tratti presenti, più il peso della lettura del gioco, cioè dell'esperienza.
I pesi sono suoi, non quelli del valore: così la taratura del valore non sposta l'esito rapido.
L'incontro si gioca set per set e scambio per scambio, perché i set abbiano le lunghezze vere: ogni
scambio che assegna punti lo vince A con una probabilità logistica della differenza di forza, della
differenza di efficienza, cioè della stanchezza del motore col ritmo di ciascuno e le azioni stimate,
e del vantaggio di chi batte; chi vince lo scambio segna un goal, due punti, con una probabilità che
cresce col distacco e col livello dei due, altrimenti è un fallo dell'altro, un punto; ogni tanto lo
scambio diventa una penalità, due punti. Due servizi a testa, chi apre si alterna fra i set, il set a
11 con 2 di scarto, D25. L'acciacco moltiplica l'efficienza come nel motore; la fatica della
giornata parte dalle azioni iniziali. Gli infortuni seguono le regole del motore, a fine set quelli
che fermano e il ritiro, dopo l'ultimo set gli acciacchi, con le stesse probabilità, un generatore a
parte e le azioni stimate. La gara a squadre si gioca con la rotazione fissa del motore, tre servizi
a testa e un set a 31.
I numeri stanno in TaraturaRapida, sul modello di motore/taratura.py, e li trova
strumenti/taratura_esito_rapido.py con una regressione sugli scambi di migliaia di incontri del
motore; i nomi non ripetono quelli della taratura del motore né di costanti.py.
"""

import dataclasses
import math
import random

from costanti import CARATTERISTICHE_VALORE, PUNTI_PER_GOAL, PUNTI_PER_PENALITA
from motore import SQUADRE, TARATURA, RisultatoIncontro
from motore.campo import StatisticheGiocatore, braccio_della_sede, estrai_sede, lettura_possibile, ritmo_della_fatica
from motore.incontro import RITIRO, StatisticheIncontro, cumulata_infortunio, probabilita_acciacco
from motore.squadre import ordine_di_battuta, problema_squadra
from valore import caratteristiche

__all__ = ("TARATURA_RAPIDA", "RisultatoRapido", "TaraturaRapida", "forza", "gioca", "gioca_squadre", "livelli")

_FISICHE = ("precisione", "forza", "resistenza")
TRATTI_RAPIDI = ("mancino", "ambidestro", "giocorapido", "cambiovelocita")
# I pesi trovati da strumenti/taratura_esito_rapido.py: vedi la carta della taratura, strumenti/taratura_esito_rapido.txt.
# Il primo giro, del 14 ottobre 2026, 3.000 incontri e 800 gare a squadre, dava al favorito da 2 a 4 punti meno del motore.
# La taratura fine dello stesso giorno, passo 4 della tappa: 20.000 incontri e 4.000 gare a squadre su 4.500 giocatori di tre
# popolazioni, con il ritocco della pendenza, per 1,26, e del peso della fatica, per 1,65, e della pendenza della gara a squadre,
# per 1,48, perché la regressione sugli scambi li fa uscire più piatti del vero; la verifica su 40.000 incontri e 5.000 gare li
# mette tutti dentro i bersagli del punto 6.4 del progetto, qualcuno col rumore.
_PESI = {"lungolineasx": 0.417, "lungolineadx": 0.3, "diagonalesx": 0.358, "diagonaledx": 0.482, "singolaspondasx": 0.431, "singolaspondadx": 0.585,
         "doppiaspondasx": 0.488, "doppiaspondadx": 0.174, "triplaspondasx": 0.222, "triplaspondadx": 0.289, "bomba": 0.332, "battutasx": 0.742,
         "battutadx": 0.497, "chiusura_dritto": 2.298, "chiusura_rovescio": 3.02, "blocco_dritto": 1.05, "blocco_rovescio": 1.202, "difesa": 3.122,
         "tenutapaletta": 1.411, "controllopalla": 0.828, "attacco": 1.39, "precisione": 2.417, "forza": 1.525, "resistenza": 0.421}
_PESI_TRATTI = {"mancino": 0.042, "ambidestro": 0.089, "giocorapido": 0.016, "cambiovelocita": 0.096}
# Ogni quanti scambi si aggiorna la fatica: cambia piano, e calcolarla a ogni scambio costava metà dell'incontro.
SCAMBI_PER_FATICA = 4


@dataclasses.dataclass(frozen=True)
class TaraturaRapida:
    """
    I numeri dell'esito rapido. PESI e PESI_TRATTI_RAPIDI fanno la forza, con PESO_LETTURA per la
    lettura del gioco; PENDENZA è la pendenza della logistica dello scambio sulla differenza di forza,
    K_FATICA quella sulla differenza di efficienza, VANTAGGIO_BATTUTA il vantaggio di chi batte; la
    quota dei goal fra gli scambi vinti è logistica di GOAL_BASE, GOAL_DISTACCO per il distacco di forza
    di chi vince e GOAL_LIVELLO per il livello medio dei due; PENALITA è la probabilità che uno scambio
    diventi una penalità; AZIONI_PER_SCAMBIO e ATTACCHI_PER_SCAMBIO le azioni e gli attacchi di ciascuno
    per ogni scambio che assegna punti. Per la gara a squadre i quattro numeri suoi.
    """
    PESI: dict = dataclasses.field(default_factory=lambda: dict(_PESI))
    PESI_TRATTI_RAPIDI: dict = dataclasses.field(default_factory=lambda: dict(_PESI_TRATTI))
    PESO_LETTURA: float = 1.241
    PENDENZA: float = 0.3775
    K_FATICA: float = 3.434
    VANTAGGIO_BATTUTA: float = 0.0904
    GOAL_BASE: float = -0.179
    GOAL_DISTACCO: float = 0.225
    GOAL_LIVELLO: float = 0.0194
    PENALITA: float = 0.00028
    AZIONI_PER_SCAMBIO: float = 6.689
    ATTACCHI_PER_SCAMBIO: float = 1.707
    PENDENZA_SQUADRE: float = 0.4555
    K_FATICA_SQUADRE: float = 2.894
    VANTAGGIO_BATTUTA_SQUADRE: float = 0.1021
    GOAL_SQUADRE: float = 0.1831


TARATURA_RAPIDA = TaraturaRapida()


class RisultatoRapido(RisultatoIncontro):
    """
    Il risultato dell'esito rapido: gli stessi campi che la registrazione legge dal risultato del
    motore, con le statistiche stimate, e i punti, gli eventi e i momenti vuoti.
    """


# La forza.

def livelli(g):
    """I livelli relativi, da 0 a 1, delle 24 caratteristiche del valore: il totale sul tetto, 10 per le fisiche e 40 per le altre."""
    totali = caratteristiche(g)
    return {nome: max(0.0, min(1.0, totali[nome] / (10.0 if nome in _FISICHE else 40.0))) for nome in CARATTERISTICHE_VALORE}


def forza(g, taratura=TARATURA_RAPIDA, memoria=None):
    """
    La forza del giocatore nell'esito rapido. Con memoria, un dizionario che vive un giorno, la forza
    di ciascuno si calcola una volta sola: cambia soltanto con le spese e con l'esperienza.
    """
    if memoria is not None and g.id in memoria:
        return memoria[g.id]
    pesi = taratura.PESI
    valore = sum(pesi[nome] * livello for nome, livello in livelli(g).items())
    valore += sum(peso for nome, peso in taratura.PESI_TRATTI_RAPIDI.items() if getattr(g, nome, False))
    valore += taratura.PESO_LETTURA * lettura_possibile(g, TARATURA)
    if memoria is not None:
        memoria[g.id] = valore
    return valore


def _logistica(x):
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def _efficienza(azioni, k, forma, fatica_max):
    """L'efficienza del motore, con k il ritmo diviso la scala: la stessa formula di motore.campo.efficienza."""
    return 1.0 - fatica_max * (1.0 - math.exp(-((azioni * k) ** forma)))


class _Gara:
    """
    Lo stato comune di un incontro rapido: i giocatori, le statistiche e gli infortuni. Gli infortuni
    si estraggono con lo stesso generatore dell'incontro, dopo gli scambi del set: un generatore a
    parte costerebbe da solo un decimo dell'incontro.
    """

    def __init__(self, giocatori, rng, basi_infortunio, cali, azioni_iniziali):
        self.giocatori = giocatori
        self.stats = {g.id: StatisticheGiocatore() for g in giocatori}
        self.basi = dict(basi_infortunio) if basi_infortunio is not None else None
        self.rng_infortuni = rng
        self.cali = cali or {}
        self.iniziali = azioni_iniziali or {}
        self.gia_infortunati = frozenset(g.id for g in giocatori if getattr(g, "infortunato", False))
        self.feriti = set()
        self.cumulate = {}
        self.infortuni = []
        self.acciacchi = []

    def _estraibile(self, gid):
        return self.basi.get(gid) is not None and gid not in self.feriti and gid not in self.gia_infortunati

    def infortuni_a_fine_set(self, ordine, set_n, chiude):
        """Gli infortuni che fermano a una fine set, nell'ordine dei giocatori al tavolo, come nel motore; le coppie di chi si è fatto male."""
        if self.basi is None:
            return []
        rng = self.rng_infortuni
        nuovi = []
        for g in ordine:
            gid = g.id
            if not self._estraibile(gid):
                continue
            prima = self.cumulate.get(gid, 0.0)
            cumulata = max(prima, cumulata_infortunio(self.basi[gid], self.stats[gid].azioni, chiude))
            self.cumulate[gid] = cumulata
            probabilita = (cumulata - prima) / (100.0 - prima) if prima < 100.0 else 0.0
            if rng.random() < probabilita:
                sede = estrai_sede(g, rng)
                self.feriti.add(gid)
                self.infortuni.append((gid, set_n, sede))
                nuovi.append((g, sede))
        return nuovi

    def acciacchi_finali(self, ordine):
        if self.basi is None:
            return
        rng = self.rng_infortuni
        for g in ordine:
            if self._estraibile(g.id) and rng.random() < probabilita_acciacco(self.basi[g.id], self.stats[g.id].azioni):
                self.acciacchi.append((g.id, estrai_sede(g, rng)))


def gioca(g_a, g_b, formato, seme, basi_infortunio=None, azioni_iniziali=None, cali=None, taratura=TARATURA_RAPIDA, memoria=None):
    """
    Un singolare con l'esito rapido, al meglio dei set del formato: il RisultatoRapido. basi_infortunio,
    cali e azioni_iniziali come nel motore; memoria è quella della forza del giorno.
    """
    if g_a.id == g_b.id:
        raise ValueError("I giocatori devono essere diversi.")
    t = taratura
    tm = TARATURA
    rng = random.Random(seme)
    gara = _Gara((g_a, g_b), rng, basi_infortunio, cali, azioni_iniziali)
    fa, fb = forza(g_a, t, memoria), forza(g_b, t, memoria)
    differenza = t.PENDENZA * (fa - fb)
    livello = (fa + fb) / 2.0
    goal_a = t.GOAL_BASE + t.GOAL_DISTACCO * (fa - fb) + t.GOAL_LIVELLO * livello
    goal_b = t.GOAL_BASE + t.GOAL_DISTACCO * (fb - fa) + t.GOAL_LIVELLO * livello
    p_goal = (_logistica(goal_a), _logistica(goal_b))
    k_a, k_b = ritmo_della_fatica(g_a, tm) / tm.FATICA_SCALA, ritmo_della_fatica(g_b, tm) / tm.FATICA_SCALA
    resa_a, resa_b = 1.0 - gara.cali.get(g_a.id, 0.0), 1.0 - gara.cali.get(g_b.id, 0.0)
    iniziali_a, iniziali_b = gara.iniziali.get(g_a.id, 0), gara.iniziali.get(g_b.id, 0)
    forma, fatica_max, k_fatica = tm.FORMA_FATICA, tm.FATICA_MAX, t.K_FATICA
    vantaggio, penalita, per_scambio = t.VANTAGGIO_BATTUTA, t.PENALITA, t.AZIONI_PER_SCAMBIO
    # Un tiro solo decide se lo scambio vinto è una penalità, un goal o un fallo dell'altro.
    soglia_goal = (penalita + (1.0 - penalita) * p_goal[0], penalita + (1.0 - penalita) * p_goal[1])
    caso = rng.random
    esp = math.exp
    stats = (gara.stats[g_a.id], gara.stats[g_b.id])
    goal, falli, penalita_fatte = [0, 0], [0, 0], [0, 0]
    punti_set, scarto, da_vincere = formato.punti_set, formato.scarto, math.ceil(formato.set_al_meglio / 2)
    set_giocati = []
    set_vinti = [0, 0]
    apre = 0 if caso() < 0.5 else 1
    scambi = 0
    ritirati = ()
    set_n = 0
    p_batte = (0.5, 0.5)
    while True:
        set_n += 1
        pa = pb = 0
        batte = apre if set_n % 2 == 1 else 1 - apre
        servizi = 0
        while True:
            if scambi % SCAMBI_PER_FATICA == 0:
                # La fatica si aggiorna ogni pochi scambi: cambia piano, e così l'incontro costa poco.
                azioni = per_scambio * scambi
                eff_a = (1.0 - fatica_max * (1.0 - esp(-(((iniziali_a + azioni) * k_a) ** forma)))) * resa_a
                eff_b = (1.0 - fatica_max * (1.0 - esp(-(((iniziali_b + azioni) * k_b) ** forma)))) * resa_b
                x = differenza + k_fatica * (eff_a - eff_b)
                p_batte = (_logistica(x + vantaggio), _logistica(x - vantaggio))
            vince = 0 if caso() < p_batte[batte] else 1
            u = caso()
            if u < penalita:
                punti = PUNTI_PER_PENALITA
                penalita_fatte[1 - vince] += 1
            elif u < soglia_goal[vince]:
                punti = PUNTI_PER_GOAL
                goal[vince] += 1
            else:
                punti = 1
                falli[1 - vince] += 1
            if vince == 0:
                pa += punti
            else:
                pb += punti
            scambi += 1
            servizi += 1
            if servizi == 2:
                servizi = 0
                batte = 1 - batte
            if (pa >= punti_set or pb >= punti_set) and abs(pa - pb) >= scarto:
                break
        _aggiorna_statistiche(stats, scambi, goal, falli, penalita_fatte, t)
        vince_set = 0 if pa > pb else 1
        set_vinti[vince_set] += 1
        set_giocati.append((pa, pb))
        chiude = max(set_vinti) >= da_vincere
        nuovi = gara.infortuni_a_fine_set((g_a, g_b), set_n, chiude)
        if chiude:
            break
        fermi = [(g, sede) for g, sede in nuovi if not (getattr(g, "ambidestro", False) and braccio_della_sede(sede) is not None)]
        if fermi:
            ritirati = tuple(g.id for g, _sede in fermi)
            parti = {0 if g.id == g_a.id else 1 for g, _sede in fermi}
            if len(parti) == 1:
                vincitore = 1 - parti.pop()
            elif set_vinti[0] != set_vinti[1]:
                vincitore = 0 if set_vinti[0] > set_vinti[1] else 1
            else:
                vincitore = vince_set
            reali = len(set_giocati)
            while set_vinti[vincitore] < da_vincere:
                set_vinti[vincitore] += 1
                set_giocati.append((punti_set, 0) if vincitore == 0 else (0, punti_set))
            gara.acciacchi_finali((g_a, g_b))
            return _risultato(formato, seme, (g_a.id, g_b.id), "A" if vincitore == 0 else "B", set_giocati, reali, gara, ritirati)
    gara.acciacchi_finali((g_a, g_b))
    return _risultato(formato, seme, (g_a.id, g_b.id), "A" if set_vinti[0] > set_vinti[1] else "B", set_giocati, len(set_giocati), gara, ritirati)


def _aggiorna_statistiche(stats, scambi, goal, falli, penalita, t):
    """Le statistiche di ciascuno fin qui: le azioni e gli attacchi stimati dagli scambi, i goal, i falli e le penalità contati."""
    azioni = round(t.AZIONI_PER_SCAMBIO * scambi)
    attacchi = round(t.ATTACCHI_PER_SCAMBIO * scambi)
    for indice, s in enumerate(stats):
        s.azioni = azioni
        s.attacchi = attacchi
        s.goal = goal[indice]
        s.goal_subiti = goal[1 - indice]
        s.falli["fallo"] = falli[indice]
        s.falli_subiti = falli[1 - indice]
        s.penalita = penalita[indice]


def _risultato(formato, seme, parti, vincitore, set_giocati, reali, gara, ritirati, nomi_squadre=None):
    return RisultatoRapido(formato=formato, seme=seme, parti=parti, vincitore=vincitore, set=list(set_giocati), esito=RITIRO if ritirati else "regolare",
                           durata_simulata=None, statistiche=gara.stats, incontro=StatisticheIncontro(), punti=[], eventi=None, momenti=None,
                           nomi_squadre=nomi_squadre, set_giocati=reali, infortuni=list(gara.infortuni), acciacchi=list(gara.acciacchi), ritirato=tuple(ritirati))


def gioca_squadre(squadra_a, squadra_b, seme, basi_infortunio=None, cali=None, taratura=TARATURA_RAPIDA, memoria=None):
    """
    Una gara a squadre con l'esito rapido: la rotazione fissa del motore, tre servizi a testa, un set a
    31 con 2 di scarto; ogni scambio fra i due al tavolo con la loro forza e la loro fatica. Alla fine
    gli infortuni che fermano e gli acciacchi dei titolari, come nel motore; il ritiro non c'è.
    """
    for squadra in (squadra_a, squadra_b):
        problema = problema_squadra(squadra)
        if problema:
            raise ValueError(problema)
    t = taratura
    tm = TARATURA
    rng = random.Random(seme)
    titolari = {"A": squadra_a.titolari, "B": squadra_b.titolari}
    al_tavolo = (*titolari["A"], *titolari["B"])
    ids_a = frozenset(g.id for g in titolari["A"])
    gara = _Gara((*squadra_a.giocatori, *squadra_b.giocatori), rng, basi_infortunio, cali, None)
    forze = {g.id: forza(g, t, memoria) for g in al_tavolo}
    ritmi = {g.id: ritmo_della_fatica(g, tm) / tm.FATICA_SCALA for g in al_tavolo}
    rese = {g.id: 1.0 - gara.cali.get(g.id, 0.0) for g in al_tavolo}
    scambi_al_tavolo = dict.fromkeys(forze, 0)
    p_goal = _logistica(t.GOAL_SQUADRE)
    punteggio = [0, 0]
    batte_per_prima = "A" if rng.random() < 0.5 else "B"
    ordine = ordine_di_battuta(batte_per_prima)
    rotazione = 0
    servizi = 0
    forma, fatica_max = tm.FORMA_FATICA, tm.FATICA_MAX
    soglia_goal = t.PENALITA + (1.0 - t.PENALITA) * p_goal
    p_vince_chi_batte = 0.5
    while not (max(punteggio) >= SQUADRE.punti_set and abs(punteggio[0] - punteggio[1]) >= SQUADRE.scarto):
        parte_b, posto_b = ordine[rotazione % len(ordine)]
        parte_r, posto_r = ordine[(rotazione + 1) % len(ordine)]
        battitore, ricevitore = titolari[parte_b][posto_b], titolari[parte_r][posto_r]
        if servizi == 0:
            # La coppia al tavolo cambia a ogni turno di battuta: la sua fatica si calcola lì.
            eff_b = _efficienza(t.AZIONI_PER_SCAMBIO * scambi_al_tavolo[battitore.id], ritmi[battitore.id], forma, fatica_max) * rese[battitore.id]
            eff_r = _efficienza(t.AZIONI_PER_SCAMBIO * scambi_al_tavolo[ricevitore.id], ritmi[ricevitore.id], forma, fatica_max) * rese[ricevitore.id]
            x = t.PENDENZA_SQUADRE * (forze[battitore.id] - forze[ricevitore.id]) + t.K_FATICA_SQUADRE * (eff_b - eff_r) + t.VANTAGGIO_BATTUTA_SQUADRE
            p_vince_chi_batte = _logistica(x)
        vince, perde = (battitore, ricevitore) if rng.random() < p_vince_chi_batte else (ricevitore, battitore)
        indice = 0 if vince.id in ids_a else 1
        u = rng.random()
        if u < t.PENALITA:
            punteggio[indice] += PUNTI_PER_PENALITA
            gara.stats[perde.id].penalita += 1
        elif u < soglia_goal:
            punteggio[indice] += PUNTI_PER_GOAL
            gara.stats[vince.id].goal += 1
            gara.stats[perde.id].goal_subiti += 1
        else:
            punteggio[indice] += 1
            gara.stats[perde.id].falli["fallo"] += 1
            gara.stats[vince.id].falli_subiti += 1
        scambi_al_tavolo[battitore.id] += 1
        scambi_al_tavolo[ricevitore.id] += 1
        servizi += 1
        if servizi >= SQUADRE.servizi_per_turno:
            servizi = 0
            rotazione += 1
    for g in al_tavolo:
        gara.stats[g.id].azioni = round(t.AZIONI_PER_SCAMBIO * scambi_al_tavolo[g.id])
        gara.stats[g.id].attacchi = round(t.ATTACCHI_PER_SCAMBIO * scambi_al_tavolo[g.id])
    gara.infortuni_a_fine_set(al_tavolo, 1, True)
    gara.acciacchi_finali(al_tavolo)
    parti = (tuple(g.id for g in squadra_a.giocatori), tuple(g.id for g in squadra_b.giocatori))
    vincitore = "A" if punteggio[0] > punteggio[1] else "B"
    return _risultato(SQUADRE, seme, parti, vincitore, [tuple(punteggio)], 1, gara, (), (squadra_a.nome, squadra_b.nome))
