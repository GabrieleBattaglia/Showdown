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
"""

import dataclasses
import math
import random
from collections import Counter
from typing import NamedTuple

from costanti import (
    AVVISI_RISCALDAMENTO_SINGOLARE,
    AVVISI_RISCALDAMENTO_SQUADRE,
    PUNTI_CAMBIO_CAMPO_SQUADRE,
    PUNTI_CAMBIO_CAMPO_ULTIMO_SET,
    PUNTI_PER_GOAL,
    PUNTI_PER_PENALITA,
    PUNTI_SET_SQUADRE,
    PUNTI_VANTAGGIO_NECESSARI,
    PUNTI_VITTORIA_SET_BASE,
    RISCALDAMENTO_SINGOLARE,
    RISCALDAMENTO_SQUADRE,
    SERVIZI_CONSECUTIVI_PER_GIOCATORE,
    SERVIZI_SQUADRE,
    SET_AMMESSI,
    TIMEOUT_PER_SET,
    TIMEOUT_SQUADRE,
)
from motore.campo import InCampo, StatisticheGiocatore, efficienza
from motore.dado import Dado
from motore.eventi import ErroreMotore
from motore.regia import Regia
from motore.scambio import EsitoPunto, gioca_punto
from motore.squadre import Squadra, ordine_di_battuta, problema_squadra
from motore.taratura import TARATURA

__all__ = ("COMPLETO", "ESSENZIALE", "SINGOLARE_3", "SINGOLARE_5", "SQUADRE", "EsitoPunto", "Formato", "Incontro", "Momento", "RisultatoIncontro",
           "StatisticheGiocatore", "StatisticheIncontro", "StatoIncontro", "formato_singolare", "simula_incontro")

ESSENZIALE = "essenziale"
COMPLETO = "completo"
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
    come coppie, l'esito regolare (ritiro e tavolino arriveranno con la tappa 12), la durata
    simulata in secondi soltanto in modalità completa, le statistiche per giocatore e dell'incontro,
    tutti i punti, e in modalità completa gli eventi e i momenti.
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
    """

    def __init__(self, parte_a, parte_b, formato, *, seme=None, dettaglio=COMPLETO, taratura=TARATURA, riscaldamento=True, timeout=True, dado=None):
        if dettaglio not in (ESSENZIALE, COMPLETO):
            raise ValueError(f"Dettaglio sconosciuto: {dettaglio}.")
        self.formato = formato
        self.squadre = formato.tipo == "squadre"
        self.taratura = t = taratura
        self.completo = dettaglio == COMPLETO
        self.riscaldamento = riscaldamento
        self.timeout_attivo = timeout
        self.parti = {"A": parte_a, "B": parte_b}
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
                    self.campo[g.id] = InCampo(g, parte, t)
            self.formazione = {"A": [g.id for g in parte_a.titolari], "B": [g.id for g in parte_b.titolari]}
            self.riserve = {"A": [g.id for g in parte_a.riserve], "B": [g.id for g in parte_b.riserve]}
        else:
            if parte_a.id == parte_b.id:
                raise ValueError("I giocatori devono essere diversi.")
            self.campo = {parte_a.id: InCampo(parte_a, "A", t), parte_b.id: InCampo(parte_b, "B", t)}
            self.formazione = {"A": [parte_a.id], "B": [parte_b.id]}
            self.riserve = {"A": [], "B": []}
        # Il seme: senza, se ne preleva uno solo dal caso globale, e si conserva nel risultato.
        self.seme = seme if seme is not None else random.getrandbits(63)
        self.rng_procedure = random.Random(f"procedure-{self.seme}")
        self.rng_scena = random.Random(f"scena-{self.seme}")
        self.dado = dado if dado is not None else Dado(random.Random(self.seme))
        self.regia = None
        if self.completo:
            self.regia = Regia(self.rng_scena, t, formato, self.campo)
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
        self.info_sorteggio = None
        self.finito = False
        self.risultato = None
        self._iniziato = False

    # Lo stato, per la live e la barra braille.

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
        while True:
            yield from self._gioca_set()
            vincitore_set = "A" if self.punteggio[0] > self.punteggio[1] else "B"
            self.set_vinti[_INDICE[vincitore_set]] += 1
            self.set_giocati.append(tuple(self.punteggio))
            if max(self.set_vinti) >= da_vincere:
                break
            eventi = []
            if self.regia:
                eventi = self.regia.fine_set(self.set_n, tuple(self.punteggio), tuple(self.set_vinti), False)
                eventi += self.regia.cambio_campo(fra_set=True)
            self.statistiche_incontro.cambi_campo.append((self.set_n, "fine set"))
            yield self._momento(PALLA_FERMA, eventi, None)
        self.finito = True
        eventi = []
        if self.regia:
            eventi = self.regia.fine_set(self.set_n, tuple(self.punteggio), tuple(self.set_vinti), True)
            eventi += self.regia.fine_incontro(tuple(self.set_vinti), list(self.set_giocati))
        # Il risultato si compone prima di consegnare la chiusura: chi segue la partita un momento
        # alla volta e si ferma quando lo stato dice finito, come la live, lo trova già pronto.
        chiusura = self._momento(CHIUSURA, eventi, None)
        self.risultato = self._componi_risultato()
        yield chiusura

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
            eventi += self.regia.inizio_incontro(self._ids_al_tavolo_iniziali())
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
        """Le fasce del tiro degli imprevisti: sanzione, mascherina e telefono di A e di B, rotture, niente."""
        t = self.taratura
        per_parte = {battitore.parte: battitore, ricevitore.parte: ricevitore}
        a, b = per_parte["A"], per_parte["B"]

        def sanzione(g):
            return t.P_SANZIONE * math.exp(t.K_TEMP_SANZIONI * g.tau) * max(0.0, 1.0 - t.K_ESP_SANZIONI * g.L)

        def mascherina(g):
            return t.P_MASCHERINA * math.exp(t.K_TEMP_MASCHERINA * g.tau)

        fasce = [sanzione(a), sanzione(b), mascherina(a), mascherina(b), t.P_TELEFONO, t.P_TELEFONO, t.P_ROTTURA_PALETTA, t.P_ROTTURA_PALLINA]
        fasce.append(max(0.0, 1.0 - sum(fasce)))
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
            formato=self.formato, seme=self.seme, parti=parti, vincitore=vincitore, set=list(self.set_giocati), esito="regolare",
            durata_simulata=self.regia.t if self.regia else None, statistiche={gid: c.stats for gid, c in self.campo.items()},
            incontro=self.statistiche_incontro, punti=self.punti, eventi=self.eventi, momenti=self.momenti_giocati, sorteggio=self.info_sorteggio,
            nomi_squadre=nomi_squadre)


def simula_incontro(parte_a, parte_b, formato, **opzioni):
    """Gioca un incontro intero e ne restituisce il RisultatoIncontro."""
    return Incontro(parte_a, parte_b, formato, **opzioni).gioca()
