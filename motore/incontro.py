"""
L'incontro di showdown nel motore di MESS: l'arbitro che fa giocare i punti.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25. Sopra la catena degli esiti c'è l'incontro, che
fa l'arbitro: il sorteggio con la moneta, i set a 11 con 2 di scarto e senza tetto, i due servizi a
testa con chi apre che si alterna da un set all'altro, gli imprevisti a palla ferma con le
ammonizioni ricordate per tutto l'incontro, per il giocatore nel singolare e per la squadra nella
gara a squadre, i time-out, i cambi campo e la gara a squadre, dove durante l'incontro non si
sostituisce nessuno, decisione D26. Il set lo chiude anche una
penalità, e una sanzione prima del primo punto fa partire il set sul 2 a 0 senza cambiare
l'ordine di battuta; se invece la penalità porta qualcuno ai punti del cambio campo, si cambia
subito, prima della battuta che segue.
Il caso viene da tre generatori nati dal seme dell'incontro. Il dado degli esiti decide tutto ciò che
sposta i punti o il loro ordine. Il generatore delle procedure decide ciò che non tocca i punti ma
deve restare uguale nelle due modalità: i time-out, la faccia chiamata al sorteggio e il lato del
tavolo. Il generatore della scena decide i dettagli che esistono soltanto in modalità completa,
cioè coordinate, velocità e attese. Così la modalità essenziale, senza regia e senza eventi, dà
con lo stesso seme gli stessi punti della completa, e una partita si rigioca identica: senza un
seme, l'incontro ne preleva uno dal caso globale, un numero solo, e lo conserva nel risultato.
Dalla tappa 12, decisione D32, risposte 6 e 7 di Gabriele e la sua regola sugli infortuni, il motore
estrae gli infortuni dell'incontro, con un quarto generatore, nato anche lui dal seme: a ogni fine
set quelli che fermano, per i giocatori di A e poi di B, e dopo l'ultimo set gli acciacchi, nello
stesso ordine, uguali nelle due modalità. Chi riceve le basi d'infortunio le passa, una per
giocatore; senza, come negli strumenti e nel banco, non si estrae niente. Gli infortuni che fermano
sono un quinto della probabilità di oggi, ripartiti sui set in proporzione alle azioni giocate fino
al riferimento, e gli acciacchi prendono il resto, così la probabilità che succeda qualcosa resta
quella di prima. Chi si fa male a fine set e non può continuare si ritira: i set che servono
all'altro si aggiungono 11 a 0. L'ambidestro che si fa male a un braccio continua con l'altro. Dopo
il set che chiude l'incontro l'infortunio c'è, ma il risultato resta; la gara a squadre, che ha un
set solo, non conosce il ritiro. L'incontro riceve anche i cali degli acciacchi del giorno e le
azioni già giocate quel giorno in un torneo, per la fatica della giornata. Con le basi, i cali e le
azioni iniziali assenti il motore fa esattamente quello che faceva, e lo provano le impronte.
Qui nasce anche la sconfitta a tavolino, 11 a 0 in ogni set, o 31 a 0 nella gara a squadre, per
chi non si presenta.
"""

import dataclasses
import math
import random
from collections import Counter
from typing import NamedTuple

from costanti import (
    AVVISI_RISCALDAMENTO_SINGOLARE,
    AVVISI_RISCALDAMENTO_SQUADRE,
    AZIONI_RIFERIMENTO_INFORTUNIO,
    PUNTI_CAMBIO_CAMPO_SQUADRE,
    PUNTI_CAMBIO_CAMPO_ULTIMO_SET,
    PUNTI_PER_GOAL,
    PUNTI_PER_PENALITA,
    PUNTI_SET_SQUADRE,
    PUNTI_VANTAGGIO_NECESSARI,
    PUNTI_VITTORIA_SET_BASE,
    QUOTA_INFORTUNI_CHE_FERMANO,
    RISCALDAMENTO_SINGOLARE,
    RISCALDAMENTO_SQUADRE,
    SERVIZI_CONSECUTIVI_PER_GIOCATORE,
    SERVIZI_SQUADRE,
    SET_AMMESSI,
    TIMEOUT_PER_SET,
    TIMEOUT_SQUADRE,
)
from motore.campo import InCampo, StatisticheGiocatore, braccio_della_sede, efficienza, estrai_sede, fattore_carico
from motore.dado import Dado
from motore.eventi import ErroreMotore
from motore.regia import Regia
from motore.scambio import EsitoPunto, gioca_punto
from motore.squadre import Squadra, ordine_di_battuta, problema_squadra
from motore.taratura import TARATURA

__all__ = ("COMPLETO", "ESSENZIALE", "RITIRO", "SINGOLARE_3", "SINGOLARE_5", "SQUADRE", "TAVOLINO", "EsitoPunto", "Formato", "Incontro", "Momento",
           "RisultatoIncontro", "StatisticheGiocatore", "StatisticheIncontro", "StatoIncontro", "a_tavolino", "formato_singolare", "simula_incontro")

ESSENZIALE = "essenziale"
COMPLETO = "completo"
# Gli esiti di un incontro: regolare, per ritiro, a tavolino.
REGOLARE = "regolare"
RITIRO = "ritiro"
TAVOLINO = "tavolino"
# Il tetto della probabilità d'infortunio di un incontro, in percentuale, come in infortuni.py.
PROBABILITA_MASSIMA = 95.0
# I generi dei momenti dell'incontro.
PRELIMINARI = "preliminari"
PUNTO = "punto"
PALLA_FERMA = "palla_ferma"
CHIUSURA = "chiusura"


@dataclasses.dataclass(frozen=True)
class Formato:
    """Le regole di un tipo d'incontro: set, punti, servizi, cambio campo, time-out e riscaldamento."""
    nome: str
    tipo: str
    set_al_meglio: int
    punti_set: int
    scarto: int
    servizi_per_turno: int
    cambio_campo_a: int
    timeout: str
    timeout_quanti: int
    riscaldamento: int
    avvisi_riscaldamento: tuple


SINGOLARE_3 = Formato("singolare al meglio dei 3 set", "singolare", 3, PUNTI_VITTORIA_SET_BASE, PUNTI_VANTAGGIO_NECESSARI, SERVIZI_CONSECUTIVI_PER_GIOCATORE,
                      PUNTI_CAMBIO_CAMPO_ULTIMO_SET, "set", TIMEOUT_PER_SET, RISCALDAMENTO_SINGOLARE, AVVISI_RISCALDAMENTO_SINGOLARE)
SINGOLARE_5 = dataclasses.replace(SINGOLARE_3, nome="singolare al meglio dei 5 set", set_al_meglio=5)
SQUADRE = Formato("gara a squadre", "squadre", 1, PUNTI_SET_SQUADRE, PUNTI_VANTAGGIO_NECESSARI, SERVIZI_SQUADRE, PUNTI_CAMBIO_CAMPO_SQUADRE,
                  "incontro", TIMEOUT_SQUADRE, RISCALDAMENTO_SQUADRE, AVVISI_RISCALDAMENTO_SQUADRE)


def formato_singolare(set_al_meglio):
    """Il formato del singolare al meglio dei 3 o dei 5 set; ValueError per ogni altro numero."""
    if set_al_meglio not in SET_AMMESSI:
        raise ValueError("Il numero di set deve essere 3 o 5.")
    return SINGOLARE_3 if set_al_meglio == 3 else SINGOLARE_5


class StatisticheIncontro:
    """I numeri dell'incontro nel suo insieme: punti, palle morte, rotture, lunghezza degli scambi, time-out, sanzioni e cambi campo."""

    __slots__ = ("attacchi_per_punto", "cambi_campo", "palle_morte", "punti_giocati", "rotture", "sanzioni", "timeout")

    def __init__(self):
        self.punti_giocati = 0
        self.palle_morte = Counter()
        self.rotture = Counter()
        self.attacchi_per_punto = []
        # Le pause e le sanzioni, come tuple di set, punto e parte, per confrontarle fra le modalità.
        self.timeout = []
        self.sanzioni = []
        self.cambi_campo = []


@dataclasses.dataclass
class RisultatoIncontro:
    """
    Il risultato di un incontro: le parti con i loro identificativi, il vincitore A o B, i set
    come coppie, l'esito, la durata simulata in secondi soltanto in modalità completa, le statistiche
    per giocatore e dell'incontro, tutti i punti, e in modalità completa gli eventi e i momenti.
    Dalla tappa 12 l'esito è regolare, ritiro o tavolino; set_giocati dice quanti set si sono giocati
    davvero, perché col ritiro i set che servivano all'altro si aggiungono 11 a 0, e col tavolino
    nessuno; infortuni sono le terne di identificativo, set e sede degli infortuni che fermano,
    acciacchi le coppie di identificativo e sede, ritirato gli identificativi di chi si è ritirato.
    """
    formato: Formato
    seme: int
    parti: tuple
    vincitore: str
    set: list
    esito: str
    durata_simulata: float | None
    statistiche: dict
    incontro: StatisticheIncontro
    punti: list
    eventi: list | None
    momenti: list | None = None
    sorteggio: dict | None = None
    # Le frasi della registrazione nel mondo, che la facciata aggiunge dopo l'incontro.
    registrazione: list | None = None
    # Nella gara a squadre, i nomi delle due squadre, per la cronaca.
    nomi_squadre: tuple | None = None
    # La tappa 12: i set giocati davvero, gli infortuni, gli acciacchi e chi si è ritirato.
    set_giocati: int | None = None
    infortuni: list = dataclasses.field(default_factory=list)
    acciacchi: list = dataclasses.field(default_factory=list)
    ritirato: tuple = ()

    def __post_init__(self):
        if self.set_giocati is None:
            self.set_giocati = len(self.set)

    @property
    def set_vinti(self):
        """I set vinti da A e da B."""
        vinti_a = sum(1 for a, b in self.set if a > b)
        return vinti_a, len(self.set) - vinti_a


class Momento(NamedTuple):
    """Un tratto dell'incontro: preliminari, punto, palla ferma o chiusura, con i suoi eventi e l'esito del punto."""
    genere: str
    eventi: tuple
    esito: EsitoPunto | None


class StatoIncontro(NamedTuple):
    """Dove si è arrivati: set, punteggio del set, set vinti, battitore, numero del servizio e se è finito."""
    set_n: int
    punteggio: tuple
    set_vinti: tuple
    battitore: int | None
    numero_servizio: int
    finito: bool


def altra(parte):
    return "B" if parte == "A" else "A"


_INDICE = {"A": 0, "B": 1}


class Incontro:
    """
    Un incontro fra due giocatori, o fra due squadre nel formato SQUADRE. Si svolge con gioca(),
    oppure un momento alla volta con momenti(), che è un generatore. Il dado si può sostituire
    con un DadoTruccato, per le prove. Nella gara a squadre la formazione e la turnazione si
    dichiarano all'inizio, con l'ordine della Squadra: i primi tre giocano tutta la gara, e le
    riserve, lette dall'arbitro con le formazioni, non entrano durante l'incontro. Nella realtà le
    sostituzioni in corsa non si vedono: è uno scostamento voluto dalla regola IBSA 22.8,
    decisione D26 di Gabriele. Una riserva gioca soltanto se la squadra la mette fra i primi tre,
    e allora gioca tutta la gara.
    velocita è la velocità di gioco della decisione D29, che in modalità completa divide le pause e
    la procedura dell'arbitro e mai l'azione; la partita dal vivo la cambia anche a metà incontro con
    imposta_velocita, e il cambio vale dal momento che segue. Non tocca né i punti né il loro ordine:
    con lo stesso seme l'incontro dà lo stesso risultato a ogni velocità.
    Dalla tappa 12: basi_infortunio è un dizionario dall'identificativo alla probabilità d'infortunio
    del giocatore senza il carico, in percentuale, oppure None, e allora nessun infortunio e nessun
    acciacco; cali dà il calo dell'acciacco di oggi di ciascuno, azioni_iniziali le azioni con cui
    ciascuno comincia, per la fatica della giornata. caso_infortuni sostituisce il generatore degli
    infortuni, per le prove.
    """

    def __init__(self, parte_a, parte_b, formato, *, seme=None, dettaglio=COMPLETO, taratura=TARATURA, riscaldamento=True, timeout=True, dado=None,
                 velocita=1.0, basi_infortunio=None, cali=None, azioni_iniziali=None, caso_infortuni=None):
        if dettaglio not in (ESSENZIALE, COMPLETO):
            raise ValueError(f"Dettaglio sconosciuto: {dettaglio}.")
        self.formato = formato
        self.squadre = formato.tipo == "squadre"
        self.taratura = t = taratura
        self.completo = dettaglio == COMPLETO
        self.riscaldamento = riscaldamento
        self.timeout_attivo = timeout
        self.parti = {"A": parte_a, "B": parte_b}
        cali = cali or {}
        iniziali = azioni_iniziali or {}
        if self.squadre:
            for squadra in (parte_a, parte_b):
                if not isinstance(squadra, Squadra):
                    raise TypeError("Nella gara a squadre le parti sono due Squadra.")
                problema = problema_squadra(squadra)
                if problema:
                    raise ValueError(problema)
            if {g.id for g in parte_a.giocatori} & {g.id for g in parte_b.giocatori}:
                raise ValueError("Le due squadre hanno un giocatore in comune.")
            self.campo = {}
            for parte, squadra in (("A", parte_a), ("B", parte_b)):
                for g in squadra.giocatori:
                    self.campo[g.id] = InCampo(g, parte, t, cali.get(g.id, 0.0), iniziali.get(g.id, 0))
            self.formazione = {"A": [g.id for g in parte_a.titolari], "B": [g.id for g in parte_b.titolari]}
            self.riserve = {"A": [g.id for g in parte_a.riserve], "B": [g.id for g in parte_b.riserve]}
        else:
            if parte_a.id == parte_b.id:
                raise ValueError("I giocatori devono essere diversi.")
            self.campo = {parte_a.id: InCampo(parte_a, "A", t, cali.get(parte_a.id, 0.0), iniziali.get(parte_a.id, 0)),
                          parte_b.id: InCampo(parte_b, "B", t, cali.get(parte_b.id, 0.0), iniziali.get(parte_b.id, 0))}
            self.formazione = {"A": [parte_a.id], "B": [parte_b.id]}
            self.riserve = {"A": [], "B": []}
        # Il seme: senza, se ne preleva uno solo dal caso globale, e si conserva nel risultato.
        self.seme = seme if seme is not None else random.getrandbits(63)
        self.rng_procedure = random.Random(f"procedure-{self.seme}")
        self.rng_scena = random.Random(f"scena-{self.seme}")
        self.dado = dado if dado is not None else Dado(random.Random(self.seme))
        # Gli infortuni in gara della tappa 12: le basi, il generatore, e quello che è successo.
        self.basi_infortunio = dict(basi_infortunio) if basi_infortunio is not None else None
        self.rng_infortuni = None
        if self.basi_infortunio is not None:
            self.rng_infortuni = caso_infortuni if caso_infortuni is not None else random.Random(f"infortuni-{self.seme}")
        # Chi gioca al tavolo, nell'ordine delle estrazioni: i giocatori di A e poi quelli di B. Come
        # tutto il resto, si fotografa quando l'incontro nasce chi è già infortunato e chi ha un
        # acciacco: il gemello della partita dal vivo si gioca dopo la registrazione, e deve ripetere
        # le stesse estrazioni e la stessa presentazione.
        self._in_gara = (*self.formazione["A"], *self.formazione["B"])
        self._gia_infortunati = frozenset(gid for gid in self._in_gara if getattr(self.campo[gid].g, "infortunato", False))
        self._acciacchi_in_campo = tuple((gid, getattr(self.campo[gid].g, "acciacco_sede", None)) for gid in self._in_gara if self.campo[gid].calo)
        self.infortuni = []
        self.acciacchi = []
        self.ritirati = ()
        self.set_reali = None
        self._feriti = set()
        self._cumulate = {}
        self.regia = None
        if self.completo:
            self.regia = Regia(self.rng_scena, t, formato, self.campo)
            self.imposta_velocita(velocita)
        # Lo stato dell'arbitro.
        self.set_n = 0
        self.punteggio = [0, 0]
        self.set_vinti = [0, 0]
        self.set_giocati = []
        self.punto_n = 0
        self.apre = "A"
        self.battitore = "A"
        self.servizi_fatti = 0
        self.rotazione = 0
        self.ordine = ()
        self.timeout_usati = {"A": 0, "B": 0}
        self.prenotati = set()
        self.serie = {"A": 0, "B": 0}
        self.ammoniti = set()
        self.cambio_campo_fatto = False
        self.ripresa_lunga = True
        self.sanzioni_in_attesa = []
        self.punti = []
        self.eventi = [] if self.completo else None
        self.momenti_giocati = [] if self.completo else None
        self.statistiche_incontro = StatisticheIncontro()
        # Le fasce degli imprevisti, una volta per coppia al tavolo: vedi _fasce_imprevisti.
        self._fasce_per_coppia = {}
        self.info_sorteggio = None
        self.finito = False
        self.risultato = None
        self._iniziato = False

    # Lo stato, per la live e la barra braille.

    def imposta_velocita(self, velocita):
        """La velocità di gioco da qui in avanti, maggiore di zero; in modalità essenziale non ci sono tempi, e non cambia niente."""
        velocita = float(velocita)
        if not velocita > 0:
            raise ValueError("La velocità di gioco deve essere maggiore di zero.")
        if self.regia is not None:
            self.regia.velocita = velocita

    def stato(self):
        battitore = None
        if self.set_n:
            battitore = self._al_tavolo()[0].id
        return StatoIncontro(self.set_n, tuple(self.punteggio), tuple(self.set_vinti), battitore, self.servizi_fatti + 1, self.finito)

    def chiedi_timeout(self, parte):
        """Prenota un time-out per la parte alla prossima palla ferma; falso se non le spetta più."""
        if self.finito or self.timeout_usati[parte] >= self.formato.timeout_quanti:
            return False
        self.prenotati.add(parte)
        return True

    # Lo svolgimento.

    def gioca(self):
        """Svolge tutto l'incontro e restituisce il RisultatoIncontro."""
        for _momento in self.momenti():
            pass
        return self.risultato

    def momenti(self):
        """Il generatore dei momenti dell'incontro: preliminari, punti, palle ferme e chiusura."""
        if self._iniziato:
            raise ErroreMotore("L'incontro è già cominciato: un incontro si gioca una volta sola.")
        self._iniziato = True
        da_vincere = math.ceil(self.formato.set_al_meglio / 2)
        yield self._momento(PRELIMINARI, self._preliminari(), None)
        ritiro = None
        while True:
            yield from self._gioca_set()
            vincitore_set = "A" if self.punteggio[0] > self.punteggio[1] else "B"
            self.set_vinti[_INDICE[vincitore_set]] += 1
            self.set_giocati.append(tuple(self.punteggio))
            chiude = max(self.set_vinti) >= da_vincere
            nuovi = self._infortuni_a_fine_set(chiude)
            if chiude:
                break
            fermi = [(gid, sede) for gid, sede in nuovi if not self._continua(gid, sede)]
            eventi = []
            if self.regia:
                eventi = self.regia.fine_set(self.set_n, tuple(self.punteggio), tuple(self.set_vinti), False)
            if fermi:
                # Il ritiro: l'incontro finisce qui, e la chiusura la fa l'arbitro col ritiro.
                ritiro = self._ritira(fermi, vincitore_set, da_vincere)
                yield self._momento(PALLA_FERMA, eventi, None)
                break
            for gid, sede in nuovi:
                c = self.campo[gid]
                c.passa_all_altro_braccio(braccio_della_sede(sede))
                if self.regia:
                    eventi += self.regia.cambio_braccio(c, sede)
            if self.regia:
                eventi += self.regia.cambio_campo(fra_set=True)
            self.statistiche_incontro.cambi_campo.append((self.set_n, "fine set"))
            yield self._momento(PALLA_FERMA, eventi, None)
        self.finito = True
        self._acciacchi_finali()
        eventi = []
        if self.regia:
            if ritiro is None:
                eventi = self.regia.fine_set(self.set_n, tuple(self.punteggio), tuple(self.set_vinti), True)
            else:
                eventi = self.regia.ritiro(*ritiro)
            finali = [(gid, sede) for gid, set_n, sede in self.infortuni if set_n == self.set_n and gid not in self.ritirati]
            eventi += self.regia.fine_incontro(tuple(self.set_vinti), list(self.set_giocati), self.ritirati, finali, self.acciacchi)
        # Il risultato si compone prima di consegnare la chiusura: chi segue la partita un momento
        # alla volta e si ferma quando lo stato dice finito, come la live, lo trova già pronto.
        chiusura = self._momento(CHIUSURA, eventi, None)
        self.risultato = self._componi_risultato()
        yield chiusura

    # Gli infortuni in gara, tappa 12.

    def _cumulata(self, base, azioni, chiude):
        """
        La probabilità cumulata, in percentuale, che il giocatore si sia fatto male fino a questa fine
        set: a un quinto, QUOTA_INFORTUNI_CHE_FERMANO, della probabilità piena dell'incontro. Alla fine
        del set che chiude l'incontro è un quinto della probabilità piena, con il carico di tutte le sue
        azioni; prima, cresce in proporzione alle azioni giocate fino al riferimento, con il carico dove
        lo supera: così il minimo del carico pesa sull'ultimo set, invece che sul primo.
        """
        if chiude or AZIONI_RIFERIMENTO_INFORTUNIO <= 0:
            carico = fattore_carico(azioni)
        else:
            carico = min(fattore_carico(azioni), azioni / AZIONI_RIFERIMENTO_INFORTUNIO)
        return QUOTA_INFORTUNI_CHE_FERMANO * min(PROBABILITA_MASSIMA, base * carico)

    def _estraibile(self, gid):
        """Vero se per il giocatore si estrae: ha una base, non si è già fatto male nell'incontro e non era già infortunato, come l'ambidestro col braccio fermo."""
        return self.basi_infortunio.get(gid) is not None and gid not in self._feriti and gid not in self._gia_infortunati

    def _infortuni_a_fine_set(self, chiude):
        """
        Gli infortuni che fermano di una fine set, per i giocatori di A e poi di B: la probabilità di
        questa fine set è l'aumento della cumulata, diviso quello che restava. Restituisce le coppie
        di identificativo e sede di chi si è fatto male adesso.
        """
        if self.basi_infortunio is None:
            return []
        rng = self.rng_infortuni
        nuovi = []
        for gid in self._in_gara:
            if not self._estraibile(gid):
                continue
            c = self.campo[gid]
            prima = self._cumulate.get(gid, 0.0)
            cumulata = max(prima, self._cumulata(self.basi_infortunio[gid], c.stats.azioni, chiude))
            self._cumulate[gid] = cumulata
            probabilita = (cumulata - prima) / (100.0 - prima) if prima < 100.0 else 0.0
            if rng.random() < probabilita:
                sede = estrai_sede(c.g, rng)
                self._feriti.add(gid)
                self.infortuni.append((gid, self.set_n, sede))
                nuovi.append((gid, sede))
        return nuovi

    def _continua(self, gid, sede):
        """Vero se l'infortunio lascia giocare: l'ambidestro che si fa male a un braccio continua con l'altro, D25."""
        return bool(getattr(self.campo[gid].g, "ambidestro", False)) and braccio_della_sede(sede) is not None

    def _ritira(self, fermi, vincitore_set, da_vincere):
        """
        Il ritiro a fine set: chi non può continuare perde i set che restano, che si aggiungono 11 a 0
        all'altro. Se si ritirano tutti e due, risposta 7 di Gabriele, vince chi ha vinto più set e, a
        parità, chi ha vinto il set appena finito. Restituisce i dati della chiamata dell'arbitro.
        """
        self.ritirati = tuple(gid for gid, _sede in fermi)
        parti = {self.campo[gid].parte for gid in self.ritirati}
        if len(parti) == 1:
            vince = altra(parti.pop())
        elif self.set_vinti[0] != self.set_vinti[1]:
            vince = "A" if self.set_vinti[0] > self.set_vinti[1] else "B"
        else:
            vince = vincitore_set
        self.set_reali = len(self.set_giocati)
        punti = self.formato.punti_set
        while self.set_vinti[_INDICE[vince]] < da_vincere:
            self.set_vinti[_INDICE[vince]] += 1
            self.set_giocati.append((punti, 0) if vince == "A" else (0, punti))
        return self.ritirati, tuple(sede for _gid, sede in fermi), vince

    def _acciacchi_finali(self):
        """
        Dopo l'ultimo set, chi nell'incontro non si è fatto male risente di un acciacco con la
        probabilità piena meno la parte degli infortuni che fermano, divisa per quello che resta: così
        la probabilità che succeda qualcosa è quella di prima, e un caso su cinque ferma.
        """
        if self.basi_infortunio is None:
            return
        rng = self.rng_infortuni
        quota = QUOTA_INFORTUNI_CHE_FERMANO
        for gid in self._in_gara:
            if not self._estraibile(gid):
                continue
            c = self.campo[gid]
            piena = min(PROBABILITA_MASSIMA, self.basi_infortunio[gid] * fattore_carico(c.stats.azioni)) / 100.0
            probabilita = (piena - quota * piena) / (1.0 - quota * piena)
            if rng.random() < probabilita:
                self.acciacchi.append((gid, estrai_sede(c.g, rng)))

    def _momento(self, genere, eventi, esito):
        eventi = tuple(eventi)
        momento = Momento(genere, eventi, esito)
        if self.completo:
            self.eventi.extend(eventi)
            self.momenti_giocati.append(momento)
        return momento

    # I preliminari.

    def _preliminari(self):
        """
        Il sorteggio, con la moneta, e il riscaldamento; restituisce gli eventi. Nel singolare chi
        vince il sorteggio sceglie fra la battuta e il lato del tavolo. Nella gara a squadre,
        regole IBSA 22.5 e 22.7, dopo il lancio l'arbitro legge le formazioni, e la squadra che
        ha vinto, conoscendo l'ordine di gioco dell'altra, tiene il primo servizio o lo cede.
        """
        t = self.taratura
        vince = "A" if self.dado.tiro() < 0.5 else "B"
        faccia_chiamata = "testa" if self.rng_procedure.random() < 0.5 else "croce"
        faccia_uscita = faccia_chiamata if vince == "A" else ("croce" if faccia_chiamata == "testa" else "testa")
        sceglie_battuta = self.dado.tiro() < t.P_SCEGLIE_BATTUTA
        arbitro_a_sinistra_di_a = self.rng_procedure.random() < 0.5
        batte = vince if sceglie_battuta else altra(vince)
        self.apre = batte
        if self.squadre:
            scelta = "tiene" if sceglie_battuta else "cede"
        else:
            scelta = "battuta" if sceglie_battuta else "lato"
        self.info_sorteggio = {"chiama": "A", "faccia_chiamata": faccia_chiamata, "faccia_uscita": faccia_uscita, "vince": vince,
                               "scelta": scelta, "batte": batte, "arbitro_a_sinistra_di_a": arbitro_a_sinistra_di_a}
        if self.squadre:
            self.ordine = ordine_di_battuta(batte)
            self.info_sorteggio["formazioni"] = {parte: list(self.formazione[parte]) for parte in ("A", "B")}
            self.info_sorteggio["riserve"] = {parte: list(self.riserve[parte]) for parte in ("A", "B")}
        eventi = []
        if self.regia:
            eventi += self.regia.inizio_incontro(self._ids_al_tavolo_iniziali(), self._acciacchi_in_campo)
            eventi += self.regia.sorteggio(self.info_sorteggio)
            if self.riscaldamento:
                eventi += self.regia.riscaldamento(self._ids_al_tavolo_iniziali())
        return eventi

    def _ids_al_tavolo_iniziali(self):
        return self.formazione["A"][0], self.formazione["B"][0]

    # Il set.

    def _gioca_set(self):
        """I momenti di un set, fino alla sua fine; il set si chiude quando qualcuno arriva ai punti con lo scarto."""
        self.set_n += 1
        self.punteggio = [0, 0]
        self.punto_n = 0
        self.servizi_fatti = 0
        if self.set_n > 1:
            self.apre = altra(self.apre)
        self.battitore = self.apre
        if self.formato.timeout == "set":
            self.timeout_usati = {"A": 0, "B": 0}
        self.serie = {"A": 0, "B": 0}
        self.ripresa_lunga = True
        eventi = []
        if self.regia:
            eventi = self.regia.inizio_set(self.set_n, self._al_tavolo()[0])
        yield self._momento(PALLA_FERMA, eventi, None)
        dado = self.dado
        t = self.taratura
        while True:
            battitore, ricevitore = self._al_tavolo()
            # Gli imprevisti a palla ferma, con un tiro solo.
            fasce = self._fasce_imprevisti(battitore, ricevitore)
            banda, _residuo = dado.fascia(fasce)
            rottura_al_colpo = 0
            causa_rottura = "paletta_rotta"
            sanzioni = ()
            if banda < 6:
                eventi, sanzioni = self._sanzione(banda)
                if not self._set_finito():
                    # Una penalità può portare qualcuno ai punti del cambio campo: si cambia
                    # subito, a palla ferma, prima della battuta che segue.
                    eventi += self._forse_cambio_campo()
                yield self._momento(PALLA_FERMA, eventi, None)
                if self._set_finito():
                    return
                battitore, ricevitore = self._al_tavolo()
            elif banda < 8:
                rottura_al_colpo = dado.intero(1, t.COLPO_ROTTURA_MASSIMO)
                causa_rottura = "paletta_rotta" if banda == 6 else "pallina_rotta"
            yield self._gioca_un_punto(battitore, ricevitore, rottura_al_colpo, causa_rottura, sanzioni)
            if self._set_finito():
                return

    def _gioca_un_punto(self, battitore, ricevitore, rottura_al_colpo, causa_rottura, sanzioni):
        """Un punto: la catena degli esiti, l'assegnazione, e quello che segue a palla ferma."""
        parte_b, parte_r = battitore.parte, ricevitore.parte
        battitore.prepara_punto(ricevitore, self._palla_set_contro(parte_b))
        ricevitore.prepara_punto(battitore, self._palla_set_contro(parte_r))
        self.punto_n += 1
        numero_servizio = self.servizi_fatti + 1
        punteggio_prima = tuple(self.punteggio)
        passi = [] if self.completo else None
        esito = gioca_punto(battitore, ricevitore, self.dado, self.taratura, passi, rottura_al_colpo, causa_rottura)
        statistiche = self.statistiche_incontro
        statistiche.punti_giocati += 1
        statistiche.attacchi_per_punto.append(esito.attacchi)
        if esito.esito == "palla_morta":
            statistiche.palle_morte[esito.causa] += 1
        elif esito.esito == "rottura":
            statistiche.rotture[esito.causa] += 1
        assegnato = esito.punti > 0
        if assegnato:
            self._assegna(esito.a_chi, esito.punti)
        esito = esito._replace(set_n=self.set_n, punto_n=self.punto_n, battitore=battitore.id, ricevitore=ricevitore.id, parte_battitore=parte_b,
                               numero_servizio=numero_servizio, punteggio=tuple(self.punteggio), sanzioni_prima=sanzioni)
        self.punti.append(esito)
        eventi = []
        if self.regia:
            visto = (punteggio_prima[_INDICE[parte_b]], punteggio_prima[_INDICE[parte_r]])
            eventi += self.regia.ripresa(battitore, ricevitore, numero_servizio, visto, self.ripresa_lunga, passi, punteggio_prima)
            eventi += self.regia.punto(passi, esito, tuple(self.punteggio))
        self.ripresa_lunga = esito.esito == "rottura"
        if assegnato:
            self.servizi_fatti += 1
        if self._set_finito():
            return self._momento(PUNTO, eventi, esito)
        if assegnato:
            eventi += self._forse_timeout(altra(esito.a_chi))
        else:
            eventi += self._forse_timeout(None)
        if assegnato and self.servizi_fatti >= self.formato.servizi_per_turno:
            self.servizi_fatti = 0
            eventi += self._cambio_battitore()
        eventi += self._forse_cambio_campo()
        return self._momento(PUNTO, eventi, esito)

    def _al_tavolo(self):
        """Gli InCampo di chi batte e di chi riceve adesso."""
        if self.squadre:
            parte_b, posto_b = self.ordine[self.rotazione % len(self.ordine)]
            parte_r, posto_r = self.ordine[(self.rotazione + 1) % len(self.ordine)]
            return self.campo[self.formazione[parte_b][posto_b]], self.campo[self.formazione[parte_r][posto_r]]
        return self.campo[self.formazione[self.battitore][0]], self.campo[self.formazione[altra(self.battitore)][0]]

    def _per_parte(self):
        battitore, ricevitore = self._al_tavolo()
        return {battitore.parte: battitore, ricevitore.parte: ricevitore}

    def _assegna(self, parte, punti):
        self.punteggio[_INDICE[parte]] += punti
        self.serie[parte] += 1
        self.serie[altra(parte)] = 0

    def _set_finito(self):
        a, b = self.punteggio
        return max(a, b) >= self.formato.punti_set and abs(a - b) >= self.formato.scarto

    def _palla_set_contro(self, parte):
        """Vero se l'avversario chiude il set col prossimo goal, e la parte no."""
        io = self.punteggio[_INDICE[parte]]
        lui = self.punteggio[_INDICE[altra(parte)]]
        punti, scarto = self.formato.punti_set, self.formato.scarto
        lui_chiude = lui + PUNTI_PER_GOAL >= punti and lui + PUNTI_PER_GOAL - io >= scarto
        io_chiudo = io + PUNTI_PER_GOAL >= punti and io + PUNTI_PER_GOAL - lui >= scarto
        return lui_chiude and not io_chiudo

    # Gli imprevisti e le sanzioni.

    def _fasce_imprevisti(self, battitore, ricevitore):
        """
        Le fasce del tiro degli imprevisti: sanzione, mascherina e telefono di A e di B, rotture,
        niente. Dipendono soltanto dal temperamento e dalla lettura dei due al tavolo, che non
        cambiano durante l'incontro: dalla tappa 12, punto 1.3 del progetto, si calcolano una volta
        per coppia al tavolo e si riusano, con gli stessi numeri fino all'ultimo bit.
        """
        a, b = (battitore, ricevitore) if battitore.parte == "A" else (ricevitore, battitore)
        chiave = (a.id, b.id)
        fasce = self._fasce_per_coppia.get(chiave)
        if fasce is not None:
            return fasce
        t = self.taratura

        def sanzione(g):
            return t.P_SANZIONE * math.exp(t.K_TEMP_SANZIONI * g.tau) * max(0.0, 1.0 - t.K_ESP_SANZIONI * g.L)

        def mascherina(g):
            return t.P_MASCHERINA * math.exp(t.K_TEMP_MASCHERINA * g.tau)

        fasce = [sanzione(a), sanzione(b), mascherina(a), mascherina(b), t.P_TELEFONO, t.P_TELEFONO, t.P_ROTTURA_PALETTA, t.P_ROTTURA_PALLINA]
        fasce.append(max(0.0, 1.0 - sum(fasce)))
        self._fasce_per_coppia[chiave] = fasce = tuple(fasce)
        return fasce

    def _sanzione(self, banda):
        """
        Una sanzione a palla ferma: ammonizione la prima volta, poi penalità; mascherina e telefono
        sono penalità subito. Nel singolare l'ammonizione si ricorda per il giocatore; nella gara a
        squadre vale per tutta la squadra, regola IBSA 22.15: dopo l'ammonizione di un compagno,
        la prima infrazione di un altro è già una penalità.
        """
        parte = "A" if banda % 2 == 0 else "B"
        g = self._per_parte()[parte]
        if banda < 2:
            causa = self.dado.pesata(self.taratura.CAUSE_AMMONIZIONE)
            chi_ricorda = parte if self.squadre else g.id
            seconda = chi_ricorda in self.ammoniti
            tipo = "penalita" if seconda else "ammonizione"
            self.ammoniti.add(chi_ricorda)
        else:
            causa = "mascherina_toccata" if banda < 4 else "telefono"
            tipo = "penalita"
            seconda = False
        if tipo == "penalita":
            g.stats.penalita += 1
            self._assegna(altra(parte), PUNTI_PER_PENALITA)
        else:
            g.stats.ammonizioni += 1
        sanzione = (parte, tipo, causa)
        self.statistiche_incontro.sanzioni.append((self.set_n, self.punto_n, g.id, tipo, causa))
        eventi = []
        if self.regia:
            eventi = self.regia.sanzione(g, tipo, causa, seconda, tuple(self.punteggio))
        return eventi, (sanzione,)

    # Le pause.

    def _forse_timeout(self, perdente):
        """Il time-out dopo un punto perso, deciso col generatore delle procedure, oppure prenotato dalla live."""
        if not self.timeout_attivo:
            prenotato = [p for p in ("A", "B") if p in self.prenotati]
            return self._timeout(prenotato[0]) if prenotato else []
        for parte in ("A", "B"):
            if parte in self.prenotati and self.timeout_usati[parte] < self.formato.timeout_quanti:
                return self._timeout(parte)
        if perdente is None or self.timeout_usati[perdente] >= self.formato.timeout_quanti:
            return []
        serie = self.serie[altra(perdente)]
        t = self.taratura
        if serie < t.SERIE_TIMEOUT:
            return []
        g = self._per_parte()[perdente]
        probabilita = min(t.P_TIMEOUT_MAX, t.P_TIMEOUT_PER_PUNTO * (serie - 2)) * (1.0 + t.K_LETTURA_TIMEOUT * g.L)
        if self.rng_procedure.random() >= probabilita:
            return []
        return self._timeout(perdente)

    def _timeout(self, parte):
        if self.timeout_usati[parte] >= self.formato.timeout_quanti:
            self.prenotati.discard(parte)
            return []
        self.prenotati.discard(parte)
        self.timeout_usati[parte] += 1
        g = self._per_parte()[parte]
        g.stats.timeout += 1
        self.statistiche_incontro.timeout.append((self.set_n, self.punto_n, parte))
        self.ripresa_lunga = True
        if self.regia:
            return self.regia.timeout(g)
        return []

    def _cambio_battitore(self):
        uscente, _ricevitore = self._al_tavolo()
        if self.squadre:
            self.rotazione += 1
            battitore, ricevitore = self._al_tavolo()
            if self.regia:
                return self.regia.cambio_al_tavolo(uscente, battitore, ricevitore)
            return []
        self.battitore = altra(self.battitore)
        if self.regia:
            return self.regia.cambio_battitore(self._al_tavolo()[0])
        return []

    def _forse_cambio_campo(self):
        """Nell'ultimo set possibile si cambia campo la prima volta che qualcuno arriva ai punti indicati, una volta sola."""
        if self.cambio_campo_fatto or self.set_n != self.formato.set_al_meglio:
            return []
        if max(self.punteggio) < self.formato.cambio_campo_a:
            return []
        self.cambio_campo_fatto = True
        self.ripresa_lunga = True
        self.statistiche_incontro.cambi_campo.append((self.set_n, tuple(self.punteggio)))
        if self.regia:
            return self.regia.cambio_campo(fra_set=False)
        return []

    # Il risultato.

    def _componi_risultato(self):
        for c in self.campo.values():
            c.stats.eff_finale = efficienza(c.azioni, c.ritmo, self.taratura)
        nomi_squadre = None
        if self.squadre:
            parti = (tuple(g.id for g in self.parti["A"].giocatori), tuple(g.id for g in self.parti["B"].giocatori))
            nomi_squadre = (self.parti["A"].nome, self.parti["B"].nome)
        else:
            parti = (self.parti["A"].id, self.parti["B"].id)
        vincitore = "A" if self.set_vinti[0] > self.set_vinti[1] else "B"
        return RisultatoIncontro(
            formato=self.formato, seme=self.seme, parti=parti, vincitore=vincitore, set=list(self.set_giocati), esito=RITIRO if self.ritirati else REGOLARE,
            durata_simulata=self.regia.t if self.regia else None, statistiche={gid: c.stats for gid, c in self.campo.items()},
            incontro=self.statistiche_incontro, punti=self.punti, eventi=self.eventi, momenti=self.momenti_giocati, sorteggio=self.info_sorteggio,
            nomi_squadre=nomi_squadre, set_giocati=self.set_reali if self.set_reali is not None else len(self.set_giocati),
            infortuni=list(self.infortuni), acciacchi=list(self.acciacchi), ritirato=tuple(self.ritirati))


def simula_incontro(parte_a, parte_b, formato, **opzioni):
    """Gioca un incontro intero e ne restituisce il RisultatoIncontro."""
    return Incontro(parte_a, parte_b, formato, **opzioni).gioca()


def a_tavolino(parte_a, parte_b, formato, assente, seme=0):
    """
    La sconfitta a tavolino della tappa 12, D32: chi non si presenta, la parte A o B indicata da
    assente, perde 11 a 0 ogni set che serve all'altro, 31 a 0 nella gara a squadre; nessun set
    giocato, statistiche a zero, nessun punto. Il tavolino doppio, con due assenti, lo conosce
    soltanto il motore dei tornei, che non ha bisogno di un incontro.
    """
    if assente not in ("A", "B"):
        raise ValueError("Chi non si presenta è la parte A o la parte B.")
    vince = altra(assente)
    punti = formato.punti_set
    necessari = math.ceil(formato.set_al_meglio / 2)
    if formato.tipo == "squadre":
        parti = (tuple(g.id for g in parte_a.giocatori), tuple(g.id for g in parte_b.giocatori))
        ids = (*parti[0], *parti[1])
        nomi_squadre = (parte_a.nome, parte_b.nome)
    else:
        parti = (parte_a.id, parte_b.id)
        ids = parti
        nomi_squadre = None
    return RisultatoIncontro(formato=formato, seme=seme, parti=parti, vincitore=vince, set=[(punti, 0) if vince == "A" else (0, punti)] * necessari,
                             esito=TAVOLINO, durata_simulata=None, statistiche={gid: StatisticheGiocatore() for gid in ids}, incontro=StatisticheIncontro(),
                             punti=[], eventi=None, nomi_squadre=nomi_squadre, set_giocati=0)
