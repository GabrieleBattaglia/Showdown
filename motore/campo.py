"""
Il giocatore in campo, durante un incontro di MESS.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25. InCampo prende un Giocatore all'inizio
dell'incontro e calcola una volta sola le sue qualità da 0 a 100: per ogni colpo, per ogni battuta,
per la chiusura e il blocco di ogni zona del corpo e per il controllo palla. Ogni caratteristica ha
un ruolo distinto: la chiusura decide se la pallina passa, il blocco se si ferma o torna indietro,
il controllo quanto bene si prepara l'attacco, la tenuta paletta la bomba e la paletta caduta, la
resistenza soltanto la stanchezza.
La stanchezza è di ciascuno, cresce con le azioni giocate, più in fretta per chi è anziano o poco
resistente, e nelle pause non passa: il vecchio difetto del problema P1, la resistenza del primo
giocatore passata a chi batte, sparisce per costruzione. Il destrimano ha il rovescio a sinistra,
il mancino a destra; l'ambidestro sano non ha rovescio e cambia mano quando la pallina arriva dal
lato opposto alla mano che impugna, mentre con un braccio infortunato gioca con l'altro e ha il
rovescio dal lato del braccio fermo.
La scelta del colpo segue la regola di Gabriele: lucido e riposato, il giocatore sceglie bene i suoi
punti forti e il lato debole dell'avversario; stanco o inesperto, sceglie quasi a caso. Capire
l'avversario è alla portata di chi ha esperienza, e si costruisce durante l'incontro: prima di
capirlo, si immagina un destrimano, ed è questo il vantaggio del mancino.
"""

import math
from collections import Counter

from costanti import COLPI_DELLO_SCAMBIO, COLPI_DI_BATTUTA, SEDI_INFORTUNIO

ZONE = ("sx", "centro", "dx")
_BRACCIO_DELLA_SEDE = {codice: braccio for codice, _frase, braccio, _peso, _durata in SEDI_INFORTUNIO}
_FISICHE = ("precisione", "resistenza", "forza")


class StatisticheGiocatore:
    """I numeri di un giocatore in un incontro, aggiornati dalla catena degli esiti in entrambe le modalità."""

    __slots__ = (
        "ammonizioni",
        "attacchi",
        "attacchi_verso",
        "azioni",
        "colpi",
        "eff_finale",
        "falli",
        "falli_subiti",
        "goal",
        "goal_battuta",
        "goal_subiti",
        "penalita",
        "scambio_piu_lungo",
        "timeout",
    )

    def __init__(self):
        self.goal = 0
        self.goal_battuta = 0
        self.goal_subiti = 0
        self.falli = Counter()
        self.falli_subiti = 0
        self.ammonizioni = 0
        self.penalita = 0
        self.azioni = 0
        self.attacchi = 0
        self.colpi = Counter()
        self.attacchi_verso = Counter()
        self.scambio_piu_lungo = 0
        self.timeout = 0
        self.eff_finale = 1.0

    def __repr__(self):
        return f"StatisticheGiocatore(goal={self.goal}, falli={sum(self.falli.values())}, azioni={self.azioni})"

    def come_dizionario(self):
        return {nome: getattr(self, nome) for nome in self.__slots__}


def valore_relativo(g, nome):
    """Una caratteristica totale divisa per il suo massimo: 10 per precisione, resistenza e forza, 40 per le altre."""
    massimo = 10.0 if nome in _FISICHE else 40.0
    return max(0.0, min(1.0, g._get_valore_totale(nome + "_base") / massimo))


def braccio_infortunato(g):
    """Il braccio fermo per infortunio, dx o sx, oppure None."""
    if not getattr(g, "infortunato", False):
        return None
    return _BRACCIO_DELLA_SEDE.get(getattr(g, "infortunio_sede", None))


def lettura_possibile(g, taratura):
    """La lettura del gioco possibile per l'esperienza di carriera, da 0 verso 1."""
    esperienza = max(0.0, float(getattr(g, "esperienza", 0.0) or 0.0))
    return esperienza / (esperienza + taratura.K_LETTURA)


def temperamento_relativo(g):
    """Il temperamento attuale portato fra -1, calmissimo, e 1, impetuoso."""
    attuale = getattr(g, "temperamento_attuale", 50.0)
    return max(-1.0, min(1.0, (attuale - 50.0) / 50.0))


class InCampo:
    """Un giocatore durante l'incontro: qualità, mano, stanchezza, paura degli errori, lettura e scelte del punto."""

    __slots__ = (
        "B",
        "C",
        "D",
        "Dp",
        "L",
        "Q",
        "QB",
        "azioni",
        "cambia_mano",
        "cambiovelocita",
        "cum_battute",
        "cum_colpi",
        "eff",
        "forza",
        "g",
        "giocorapido",
        "id",
        "ln_mf",
        "mano",
        "mf",
        "osservati",
        "parte",
        "pesi_cause_battuta",
        "pi",
        "prob_battute",
        "prob_colpi",
        "ritmo",
        "rovescio",
        "serie_persi",
        "stats",
        "tar",
        "tau",
        "temperatura",
    )

    def __init__(self, g, parte, taratura):
        self.g = g
        self.id = g.id
        self.parte = parte
        self.tar = t = taratura
        self.tau = temperamento_relativo(g)
        self.L = lettura_possibile(g, t)
        self.giocorapido = bool(getattr(g, "giocorapido", False))
        self.cambiovelocita = bool(getattr(g, "cambiovelocita", False))
        anni = g.eta_anni
        fattore_eta = 1.0 + max(0.0, anni - t.ETA_INIZIO_FATICA) / t.ANNI_FATICA + max(0.0, t.ETA_FATICA_GIOVANI - anni) * t.FATICA_GIOVANI_PER_ANNO
        fattore_resistenza = t.RESISTENZA_BASE + t.RESISTENZA_PER_PUNTO * g._get_valore_totale("resistenza_base")
        self.ritmo = fattore_eta / max(0.05, fattore_resistenza)
        self._calcola_qualita(g, t)
        self.azioni = 0
        self.osservati = 0
        self.serie_persi = 0
        self.eff = 1.0
        self.mf = 1.0
        self.ln_mf = 0.0
        self.pi = 0.0
        self.temperatura = t.T0
        self.cum_colpi = ()
        self.cum_battute = ()
        self.prob_colpi = ()
        self.prob_battute = ()
        self.stats = StatisticheGiocatore()
        # Le cause della battuta irregolare piegate dal temperamento e dal gioco rapido, una volta
        # per incontro: il temperamento non cambia durante una partita.
        pesi = []
        for codice, peso in t.CAUSE_BATTUTA:
            if codice in ("battuta_prima_del_fischio", "battuta_doppio_tocco"):
                peso *= 1.0 + t.K_TEMP_CAUSE_BATTUTA * self.tau
            elif codice == "battuta_oltre_due_secondi":
                peso *= 1.0 - t.K_TEMP_CAUSE_BATTUTA * self.tau
            if codice == "battuta_prima_del_fischio" and self.giocorapido:
                peso *= 2.0
            pesi.append((codice, max(0.0, peso)))
        self.pesi_cause_battuta = tuple(pesi)

    def _calcola_qualita(self, g, t):
        c = {nome[:-5]: valore_relativo(g, nome[:-5]) for nome in _CARATTERISTICHE_BASE}
        self.forza = c["forza"]
        q = []
        for nome in COLPI_DELLO_SCAMBIO:
            pesi = t.PESI_BOMBA if nome == "bomba" else t.PESI_COLPO
            q.append(100.0 * (pesi[0] * c[nome] + pesi[1] * c["attacco"] + pesi[2] * c["precisione"] + pesi[3] * c["forza"]))
        self.Q = tuple(q)
        pb = t.PESI_BATTUTA
        self.QB = tuple(100.0 * (pb[0] * c[nome] + pb[1] * c["precisione"] + pb[2] * c["forza"] + pb[3] * c["attacco"]) for nome in COLPI_DI_BATTUTA)
        pc, pbl = t.PESI_CHIUSURA, t.PESI_BLOCCO
        d = {
            "sx": 100.0 * (pc[0] * c["chiusurasx"] + pc[1] * c["difesa"] + pc[2] * c["precisione"]),
            "centro": 100.0 * (pc[0] * c["tenutapaletta"] + pc[1] * c["difesa"] + pc[2] * c["precisione"]),
            "dx": 100.0 * (pc[0] * c["chiusuradx"] + pc[1] * c["difesa"] + pc[2] * c["precisione"]),
        }
        b = {
            "sx": 100.0 * (pbl[0] * c["bloccosx"] + pbl[1] * c["difesa"] + pbl[2] * c["precisione"]),
            "centro": 100.0 * (pbl[0] * (c["bloccosx"] + c["bloccodx"]) / 2.0 + pbl[1] * c["difesa"] + pbl[2] * c["precisione"]),
            "dx": 100.0 * (pbl[0] * c["bloccodx"] + pbl[1] * c["difesa"] + pbl[2] * c["precisione"]),
        }
        pk = t.PESI_CONTROLLO
        self.C = 100.0 * (pk[0] * c["controllopalla"] + pk[1] * c["precisione"] + pk[2] * c["tenutapaletta"])
        # La mano: il destrimano ha il rovescio a sinistra, il mancino a destra; l'ambidestro sano
        # non ha rovescio e cambia mano, quello con un braccio fermo gioca con l'altro.
        braccio = braccio_infortunato(g)
        if getattr(g, "ambidestro", False) and braccio is None:
            self.rovescio = None
            self.cambia_mano = True
            self.mano = "destra"
        elif getattr(g, "ambidestro", False):
            self.rovescio = braccio
            self.cambia_mano = False
            self.mano = "sinistra" if braccio == "dx" else "destra"
        elif getattr(g, "mancino", False):
            self.rovescio = "dx"
            self.cambia_mano = False
            self.mano = "sinistra"
        else:
            self.rovescio = "sx"
            self.cambia_mano = False
            self.mano = "destra"
        if self.rovescio is not None:
            d[self.rovescio] *= 1.0 - t.MALUS_ROVESCIO
            b[self.rovescio] *= 1.0 - t.MALUS_ROVESCIO
        self.D = d
        self.B = b
        # Le qualità di parata con il rovescio ma senza la stanchezza, quelle che l'avversario può
        # capire: la chiusura, con la parte del blocco che decide anch'essa se la pallina passa.
        peso = t.PESO_BLOCCO_PARATA
        self.Dp = {zona: d[zona] + peso * (b[zona] - d[zona]) for zona in ZONE}

    def conta_azione(self):
        self.azioni += 1
        self.stats.azioni += 1

    def difesa(self, zona):
        """Chiusura e blocco della zona, senza la stanchezza, e se per difendere cambia mano."""
        d = self.D[zona]
        b = self.B[zona]
        if self.cambia_mano and zona != "centro":
            lato_della_mano = "dx" if self.mano == "destra" else "sx"
            if zona != lato_della_mano:
                self.mano = "sinistra" if self.mano == "destra" else "destra"
                costo = 1.0 - self.tar.COSTO_CAMBIO_MANO
                return d * costo, b * costo, True
        return d, b, False

    def dritto(self, zona):
        """Vero se la zona è di dritto per la mano che impugna adesso, None al centro."""
        if zona == "centro":
            return None
        if self.rovescio is None:
            return True
        return zona != self.rovescio

    def prepara_punto(self, avversario, pressione_set=False):
        """
        Una volta per punto: stanchezza, paura degli errori e probabilità di scelta di colpi e
        battute contro l'avversario di adesso. Dentro il punto la stanchezza resta ferma.
        """
        t = self.tar
        self.eff = eff = 1.0 - t.FATICA_MAX * (1.0 - math.exp(-self.azioni * self.ritmo / t.FATICA_SCALA))
        s_rel = (1.0 - eff) / t.FATICA_MAX if t.FATICA_MAX > 0 else 0.0
        if pressione_set and t.PRESSIONE_PALLA_SET:
            self.pi = t.PRESSIONE_PALLA_SET * (1.0 + t.PRESSIONE_PALLA_SET_TEMPERAMENTO * self.tau) * (1.0 - t.PRESSIONE_PALLA_SET_ESPERIENZA * self.L)
        else:
            self.pi = 0.0
        self.mf = math.exp(t.K_TEMP_FALLI * self.tau) * (1.0 - t.K_ESP_FALLI * self.L) * (1.0 + t.K_FATICA_FALLI * (1.0 - eff)) * math.exp(self.pi)
        self.ln_mf = math.log(self.mf)
        self.temperatura = temperatura = t.T0 * (1.0 + t.K_FATICA_SCELTA * s_rel) * (1.0 + t.K_LETTURA_SCELTA * (1.0 - self.L))
        percepita = self.debolezza_percepita(avversario)
        q0 = t.Q0
        colpi = t.COLPI
        termine_potenza = t.PESO_POTENZA * self.tau
        utilita = []
        for indice, nome in enumerate(COLPI_DELLO_SCAMBIO):
            colpo = colpi[nome]
            utilita.append(math.log(self.Q[indice] * eff + q0) + t.PESO_DEBOLEZZA * percepita[colpo.zona] + termine_potenza * colpo.potenza - t.PESO_RISCHIO * colpo.fallo_base)
        self.prob_colpi, self.cum_colpi = _softmax_cumulata(utilita, temperatura)
        utilita_b = []
        for indice, nome in enumerate(COLPI_DI_BATTUTA):
            colpo = colpi[nome]
            utilita_b.append(math.log(self.QB[indice] * eff + q0) + t.PESO_DEBOLEZZA * percepita[colpo.zona] + termine_potenza * colpo.potenza)
        self.prob_battute, self.cum_battute = _softmax_cumulata(utilita_b, temperatura)

    def debolezza_vera(self, avversario):
        """Quanto ogni zona dell'avversario è più debole della sua media, senza la stanchezza."""
        q0 = self.tar.Q0
        dp = avversario.Dp
        media = (dp["sx"] + dp["centro"] + dp["dx"]) / 3.0 + q0
        return {zona: math.log(media / (dp[zona] + q0)) for zona in ZONE}

    def conoscenza(self):
        """Quanto il giocatore ha capito l'avversario: la sua lettura, costruita con gli attacchi giocati."""
        return self.L * (1.0 - math.exp(-self.osservati / self.tar.COLPI_PER_CAPIRE))

    def debolezza_percepita(self, avversario):
        """La debolezza delle zone come la vede il giocatore: la vera, per quanto l'ha capita, e il resto dal priore di un destrimano."""
        t = self.tar
        vera = self.debolezza_vera(avversario)
        k = self.conoscenza()
        priore = {"sx": t.PRIORE_ROVESCIO, "centro": t.PRIORE_ALTRE_ZONE, "dx": t.PRIORE_ALTRE_ZONE}
        return {zona: k * vera[zona] + (1.0 - k) * priore[zona] for zona in ZONE}


def _softmax_cumulata(utilita, temperatura):
    massimo = max(utilita)
    pesi = [math.exp((u - massimo) / temperatura) for u in utilita]
    totale = sum(pesi)
    probabilita = tuple(p / totale for p in pesi)
    cumulata = []
    somma = 0.0
    for p in probabilita:
        somma += p
        cumulata.append(somma)
    cumulata[-1] = 1.0
    return probabilita, tuple(cumulata)


def scegli(cumulata, u):
    """L'indice della fascia cumulata in cui cade il tiro u."""
    for indice, limite in enumerate(cumulata):
        if u < limite:
            return indice
    return len(cumulata) - 1


_CARATTERISTICHE_BASE = tuple(f"{nome}_base" for nome in (*COLPI_DELLO_SCAMBIO, *COLPI_DI_BATTUTA, "chiusurasx", "chiusuradx", "bloccosx", "bloccodx", "difesa",
                                                         "tenutapaletta", "controllopalla", "attacco", "precisione", "forza", "resistenza"))
