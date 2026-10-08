"""
MESS, la partita sonora della tappa 10: compone il suono della partita dal vivo e lo fa sentire.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-08 con le decisioni D28 e D29, dal prototipo strumenti/resa_prototipo.py, che
Gabriele ha ascoltato nell'ascolto libero e approvato: lati, movimento e tempi funzionano. Il
prototipo resta allo strumento d'ascolto e al banco alla cieca; questo è il modulo vero, ripulito.
Il motore conosce in anticipo tutti gli eventi di un punto con i loro tempi, quindi un punto, o una
tranche di più punti, si compone in un solo buffer stereo, con numpy e scipy, che va al mixer di
Acusticator con una chiamata sola: ogni suono cade esatto al campione, all'istante del suo evento.
Le tre parti del modulo.
Lo spazio. Chi ascolta sta alla testata della sua parte, di solito il giocatore A. Ogni suono si
sintetizza al centro e diventa una sorgente mono; lo spazio lo mette la classe Spazio, che dalla
posizione assoluta sul tavolo ricava il pan, il volume con la distanza e la cupezza, un passa basso il
cui taglio scende col lontano. Pan e distanza vengono sempre da motore.tavolo.vista, mai dal lato
del motore né dai nomi dei colpi, così il ribaltamento chiesto da D11 per il giocatore lontano resta
in un punto solo. I valori predefiniti sono quelli del prototipo; quelli che Gabriele sceglierà al
banco alla cieca si mettono nello Spazio, che ha un campo per ognuna delle tre domande di D28.
I suoni. La mappa SUONI dà un preset della collezione di GBUtils per ogni ruolo, per ora segnaposto,
e nessuno è un suono della finestra. Il suono si sceglie dal tipo dell'evento, dal suo esito e dalla
sua causa: le cause che fanno un rumore loro, la paletta che cade, il colpo a vuoto e il secondo
tocco, hanno il loro suono, come vuole D28, e gli altri falli si riconoscono dal suono della pallina,
dal fischio e dalla chiamata. Le parole dell'arbitro non suonano: le dice la cronaca. I suoni tonali
si sintetizzano una volta; quelli di rumore tengono quattro varianti, che girano dentro il buffer.
Il livello ha un margine: un guadagno fisso e un tetto, anche al volume degli effetti massimo.
La riproduzione e la cronologia. Il buffer parte come ciclo di Acusticator, con una coda di zeri, e
si ferma con la sua maniglia, come vuole D28: la pausa, il salto, l'uscita e il cambio di lato
fermano soltanto la partita, mai gli effetti della finestra, che Acusticator.stop zittirebbe. La
Cronologia divide l'incontro, svolto un momento alla volta, in segmenti che finiscono a ogni punto,
sanzione o fine set, e lascia al motore la velocità di gioco, che divide le pause e la procedura
dell'arbitro e mai l'azione: per questo il buffer non si ricompone mai per la velocità.
"""

import collections
import itertools
import math
import time
from dataclasses import dataclass

import numpy as np

from costanti import LUNGHEZZA_TAVOLO, META_TAVOLO, VOLUME_RIFERIMENTO_CM
from motore import eventi as E

FS = 44100
# Il passo di controllo lungo i voli: pan, volume e taglio cambiano ogni 5 millesimi.
PASSO = 0.005
CAMPIONI_PASSO = round(PASSO * FS)
# Il rotolamento: il suo guadagno, e la velocità a cui suona pieno; più lento, più piano.
GUADAGNO_ROTOLAMENTO = 0.6
V_RIF = 500.0
GUADAGNO_CONTROLLO = 0.5
# Il nastro del rotolamento, i secondi lasciati ai suoi capi e la sfumatura dei tratti tagliati.
FONDO_LUNGO = 8.0
MARGINE_FONDO = 0.5
SFUMATURA = 0.005
# Il secondo tocco della battuta col doppio tocco arriva poco dopo il primo.
RITARDO_SECONDO_TOCCO = 0.08
# I suoni di rumore e quante varianti ne restano in memoria.
KIND_DI_RUMORE = frozenset((5, 6, 7, 8))
VARIANTI_RUMORE = 4
# Il livello: il guadagno fisso della partita, e il tetto che nessun picco supera. Il volume degli
# effetti moltiplica il buffer come moltiplica i suoni della finestra, a 50 com'è stato pensato.
GUADAGNO_PARTITA = 1.0
TETTO = 0.8
VOLUME_DI_PROGETTO = 50
# Il silenzio lasciato davanti al primo suono quando il buffer accorcia quello in testa.
ANTICIPO = 0.3
# I secondi di zeri in coda al ciclo: se il battito che lo ferma arriva tardi, il punto non riparte.
CODA_DI_ZERI = 2.0
# La tolleranza sugli istanti: quelli degli eventi sono arrotondati al millesimo, quelli delle tappe no.
TOLLERANZA = 0.001

# I preset segnaposto della collezione di GBUtils, uno per ruolo e mai lo stesso per due ruoli, gli
# stessi dell'ascolto libero approvato da Gabriele. Nessuno è fra quelli della finestra, in
# suoni.EVENTI, perché un suono della finestra non si confonda con un evento della partita: lo
# controlla una prova. I timbri veri arrivano per ultimi, secondo D28.
SUONI = {
    "battuta": "colpo_d_impatto_5",
    "colpo": "colpo_d_impatto_2",
    "secondo_tocco": "colpo_d_impatto_1",
    "colpo_a_vuoto": "meditimer_manuale",
    "parata": "carta_giocata",
    "paletta_caduta": "rimbalzo_stereo",
    "sponda": "carta_pescata",
    "rotolamento": "pioggia_leggera",
    "controllo": "pokermachine_rimescolo",
    "goal": "colpo_d_impatto_7",
    "schermo": "colpo_d_impatto_3",
    "terra": "colpo_d_impatto_10",
    "corpo": "colpo_d_impatto_6",
    "soffitto": "colpo_d_impatto_8",
    "tavola_contatto": "colpo_d_impatto_9",
    "rottura": "scudisciata",
    "recupero": "pokermachine_scarto",
    "fischio_singolo": "fide_pronto",
    "fischio_doppio": "doppio_tic_conferma",
    "fischio_lungo": "sys_tick_alto",
}
# Le tappe del volo che hanno un suono proprio. Paletta e porta suonano con la parata e il goal.
TAPPE_SONORE = {"sponda": "sponda", "curva": "sponda", "schermo": "schermo", "terra": "terra", "corpo": "corpo", "soffitto": "soffitto",
                "tavola_contatto": "tavola_contatto"}
# Il volo non dice se un tratto è sul tavolo o in aria: lo dice il tipo delle sue tappe.
FINE_IN_ARIA = frozenset(("terra", "soffitto", "sopra_schermo"))
INIZIO_IN_ARIA = frozenset(("fuori", "soffitto", "tavola_contatto", "sopra_schermo"))
# Oppure la causa del colpo che lo lancia: con queste la pallina parte in aria e il tavolo non la
# sente. Per il soffitto e lo schermo lo dicono già le tappe; per il volo fuori dal tavolo no, perché
# le sue tappe, partenza, fuori e terra, sono quelle della pallina che rotola e salta la sponda.
CAUSE_IN_ARIA = frozenset(("out_volo", "out_soffitto", "schermo_sopra"))
# Gli eventi che portano un volo da far sentire, e quelli che lanciano la pallina in un volo.
CON_VOLO = frozenset((E.VOLO, E.CONSEGNA, E.RISCALDAMENTO_COLPO))
LANCI = frozenset((E.BATTUTA, E.COLPO, E.PARATA))
# Le parate che non mettono la paletta sulla pallina: quella che non arriva, quella che prende il
# corpo, che suona con la tappa del volo, e quella a cui cade la paletta, che suona col fallo.
CAUSE_SENZA_PARATA = frozenset(("body_touch", "body_touch_pieno", "paletta_caduta"))


# Lo spazio.

@dataclass(frozen=True)
class Spazio:
    """
    Le leggi dello spazio della partita, per chi ascolta dalla testata della sua parte. Ogni campo è
    una scelta da fare a orecchio, con i valori del prototipo approvato come predefiniti; per
    sostituirli basta uno Spazio nuovo, per esempio dataclasses.replace(SPAZIO, taglio_minimo=2500).
    volume_riferimento: i centimetri a cui il volume scende alla metà, con la legge 1 / (1 + d / r).
    taglio_massimo, taglio_minimo e distanza_aperta: il passa basso è aperto fino a distanza_aperta,
    poi il taglio scende come distanza_aperta diviso la distanza, fino a taglio_minimo.
    cupo_solo_dietro_lo_schermo: falso, il lontano diventa cupo con la distanza; vero, la metà del
    tavolo di chi ascolta resta aperta e la cupezza comincia dietro lo schermo, come un'ombra.
    larghezza_lontana: uno, la metà lontana suona larga quanto quella vicina, come fa il motore;
    meno di uno, si stringe verso il centro andando verso la testata lontana, fino a quella frazione.
    """
    volume_riferimento: float = float(VOLUME_RIFERIMENTO_CM)
    taglio_massimo: float = 18000.0
    taglio_minimo: float = 1500.0
    distanza_aperta: float = 60.0
    cupo_solo_dietro_lo_schermo: bool = False
    larghezza_lontana: float = 1.0

    def punto(self, pos, ascoltatore):
        """Pan, volume e taglio di un punto del tavolo, nel riferimento di A, per chi ascolta dalla parte indicata."""
        from motore.tavolo import vista

        pan, distanza, _lato = vista(pos, ascoltatore)
        profondita = pos[1] if ascoltatore == "A" else LUNGHEZZA_TAVOLO - pos[1]
        dietro = profondita > META_TAVOLO
        if dietro and self.larghezza_lontana != 1.0:
            oltre = min(1.0, (profondita - META_TAVOLO) / (LUNGHEZZA_TAVOLO - META_TAVOLO))
            pan *= 1.0 - (1.0 - self.larghezza_lontana) * oltre
        volume = 1.0 / (1.0 + distanza / self.volume_riferimento)
        if self.cupo_solo_dietro_lo_schermo and not dietro:
            taglio = self.taglio_massimo
        else:
            taglio = self.taglio_massimo * self.distanza_aperta / max(distanza, self.distanza_aperta)
        return pan, volume, float(min(self.taglio_massimo, max(self.taglio_minimo, taglio)))

    def campi(self, posizioni, ascoltatore):
        """Pan, volume e taglio di ogni posizione, come tre array."""
        valori = np.array([self.punto(p, ascoltatore) for p in posizioni], dtype=np.float64).reshape(-1, 3)
        return valori[:, 0], valori[:, 1], valori[:, 2]


SPAZIO = Spazio()


# Le strutture.

@dataclass
class Posato:
    """
    Un suono messo nella composizione: il ruolo, l'istante, la sorgente mono, gli istanti di
    controllo dal suo inizio con le posizioni, una sola se sta fermo, i guadagni lungo il suono se ci
    sono, il numero dell'evento da cui viene e la variante, che conta soltanto per i rumori.
    """
    ruolo: str
    t: float
    mono: np.ndarray
    tempi: np.ndarray
    posizioni: list
    guadagni: np.ndarray | None = None
    evento: int = 0
    variante: int = 0


@dataclass
class Resa:
    """Il buffer stereo composto, l'istante del suo primo campione e i suoni posati, per verificarlo."""
    buffer: np.ndarray
    t0: float
    posati: list

    @property
    def durata(self):
        return len(self.buffer) / FS


# Le sorgenti, dalla collezione.

_CACHE = {}


def svuota_cache():
    _CACHE.clear()


def allunga(score, durata):
    """Lo score con le durate delle quartine scalate perché il totale sia durata."""
    score = list(score)
    totale = sum(float(score[i]) for i in range(1, len(score), 4))
    fattore = durata / totale
    for i in range(1, len(score), 4):
        score[i] = float(score[i]) * fattore
    return score


def sorgente(ruolo, durata=None, piatto=False, variante=0):
    """
    La sorgente mono di un ruolo: al centro, allungata se si chiede una durata, senza inviluppo se
    piatto. I suoni tonali escono sempre uguali e si sintetizzano una volta; quelli di rumore
    tengono VARIANTI_RUMORE varianti, e variante sceglie quale. KeyError se il preset manca.
    """
    from GBUtils import Acusticator

    nome = SUONI[ruolo]
    score, kind, adsr = Acusticator.preset(nome)
    if not score:
        raise KeyError(f"Il preset {nome} del ruolo {ruolo} non c'è nella collezione.")
    variante = variante % VARIANTI_RUMORE if kind in KIND_DI_RUMORE else 0
    chiave = (nome, None if durata is None else round(durata, 3), piatto, variante)
    if chiave in _CACHE:
        return _CACHE[chiave]
    score = list(score)
    # Lo spazio lo mette lo Spazio: il panorama proprio del preset si porta al centro.
    for i in range(2, len(score), 4):
        score[i] = 0.0
    if durata is not None:
        score = allunga(score, max(durata, 0.02))
    if piatto:
        adsr = [0.002, 0.0, 100.0, 0.002]
    stereo = Acusticator.sintetizza(score, kind, adsr, FS)
    # Al centro la legge a potenza costante dà il coseno di 45 gradi per lato: il mono è un canale per la radice di due.
    mono = (np.asarray(stereo)[:, 0] * math.sqrt(2.0)).astype(np.float32)
    _CACHE[chiave] = mono
    return mono


def prepara(taratura=None):
    """
    Sintetizza in anticipo tutte le sorgenti della partita, con le varianti dei rumori, i fischi
    alle durate della taratura e il nastro del rotolamento: la prima composizione costa allora come
    le altre, e Prosegui non fa aspettare. Si chiama all'apertura della finestra dal vivo.
    """
    from motore.taratura import TARATURA

    t = taratura or TARATURA
    for ruolo in SUONI:
        if ruolo.startswith("fischio_"):
            continue
        for variante in range(VARIANTI_RUMORE):
            sorgente(ruolo, variante=variante)
    for ruolo, durata in (("fischio_singolo", t.FISCHIO_SINGOLO), ("fischio_doppio", t.FISCHIO_DOPPIO), ("fischio_lungo", t.FISCHIO_LUNGO)):
        sorgente(ruolo, durata)
    sorgente("rotolamento", FONDO_LUNGO, piatto=True)


def _sfuma(mono):
    """Cinque millesimi di sfumatura ai due capi di un tratto tagliato, perché non faccia clic."""
    n = min(round(SFUMATURA * FS), len(mono) // 2)
    if n > 1:
        rampa = np.linspace(0.0, 1.0, n, dtype=np.float32)
        mono[:n] *= rampa
        mono[-n:] *= rampa[::-1]
    return mono


def nastro(ruolo, durata, numero):
    """Un tratto lungo durata del nastro di rumore del ruolo, sintetizzato una volta e senza inviluppo; numero sceglie da dove comincia."""
    n = max(1, round(durata * FS))
    fondo = sorgente(ruolo, FONDO_LUNGO, piatto=True)
    margine = round(MARGINE_FONDO * FS)
    spazio = len(fondo) - 2 * margine - n
    if spazio < 1:
        return _sfuma(np.resize(fondo[margine:len(fondo) - margine], n).astype(np.float32))
    inizio = margine + (numero * 7919) % spazio
    return _sfuma(fondo[inizio:inizio + n].copy())


def in_fila(ruolo, durata, numero):
    """Il preset del ruolo ripetuto alla sua velocità naturale per durata secondi: la pallina scossa nel controllo."""
    naturale = sorgente(ruolo, variante=numero)
    n = max(1, round(durata * FS))
    return _sfuma(np.tile(naturale, math.ceil(n / len(naturale)))[:n].copy())


# La spazializzazione.

def _coefficienti(fc):
    a = math.exp(-2.0 * math.pi * fc / FS)
    return [(1.0 - a) ** 2], [1.0, -2.0 * a, a * a]


def _filtra(mono, fc_blocchi):
    """Il passa basso a blocchi di un passo di controllo, con il taglio che cambia da un blocco all'altro e lo stato che prosegue."""
    from scipy.signal import lfilter

    uscita = np.empty_like(mono)
    stato = np.zeros(2)
    for k in range(math.ceil(len(mono) / CAMPIONI_PASSO)):
        b, a = _coefficienti(fc_blocchi[min(k, len(fc_blocchi) - 1)])
        tratto = slice(k * CAMPIONI_PASSO, (k + 1) * CAMPIONI_PASSO)
        uscita[tratto], stato = lfilter(b, a, mono[tratto], zi=stato)
    return uscita


def spazializza(posato, ascoltatore, spazio=SPAZIO):
    """La sorgente mono di un suono resa stereo per chi ascolta: un array di campioni per 2, float32."""
    mono = posato.mono
    pan, vol, fc = spazio.campi(posato.posizioni, ascoltatore)
    if len(posato.posizioni) == 1:
        from scipy.signal import lfilter

        b, a = _coefficienti(fc[0])
        segnale = lfilter(b, a, mono).astype(np.float32)
        angolo = (pan[0] + 1.0) * math.pi / 4.0
        g = vol[0] * (posato.guadagni[0] if posato.guadagni is not None else 1.0)
        return np.stack([segnale * (g * math.cos(angolo)), segnale * (g * math.sin(angolo))], axis=1).astype(np.float32)
    t = np.arange(len(mono)) / FS
    pan_s = np.interp(t, posato.tempi, pan)
    vol_s = np.interp(t, posato.tempi, vol)
    if posato.guadagni is not None:
        vol_s = vol_s * np.interp(t, posato.tempi, posato.guadagni)
    # Il taglio di ogni blocco è quello del passo di controllo in cui il blocco comincia.
    inizi = np.arange(0, len(mono), CAMPIONI_PASSO) / FS
    segnale = _filtra(mono.astype(np.float64), np.interp(inizi, posato.tempi, fc)).astype(np.float32)
    angolo = (pan_s + 1.0) * (math.pi / 4.0)
    return np.stack([segnale * vol_s * np.cos(angolo), segnale * vol_s * np.sin(angolo)], axis=1).astype(np.float32)


# Dagli eventi ai suoni posati.

def suoni_fermi(e):
    """
    I suoni istantanei di un evento, come coppie di ruolo e ritardo dal suo istante. Si sceglie dal
    tipo, dall'esito e dalla causa: il colpo a vuoto ha il suo suono, il doppio tocco ne ha due, la
    paletta che cade suona col fallo al posto del colpo o della parata, e la parata che non tocca la
    pallina resta muta. Fallo, palla morta, chiamate e annunci non hanno suono: si riconoscono dal
    suono della pallina, dal fischio e dalle parole della cronaca, come vogliono D25 e D28.
    """
    tipo, esito, causa = e.tipo, e.esito, e.causa
    if tipo == E.BATTUTA:
        if causa == "battuta_a_vuoto":
            return [("colpo_a_vuoto", 0.0)]
        if causa == "battuta_doppio_tocco":
            return [("battuta", 0.0), ("secondo_tocco", RITARDO_SECONDO_TOCCO)]
        return [("battuta", 0.0)]
    if tipo in (E.COLPO, E.RISCALDAMENTO_COLPO):
        return [] if causa == "paletta_caduta" else [("colpo", 0.0)]
    if tipo == E.PARATA:
        return [] if esito == "goal" or causa in CAUSE_SENZA_PARATA else [("parata", 0.0)]
    if tipo == E.FALLO:
        return [("paletta_caduta", 0.0)] if causa == "paletta_caduta" else []
    if tipo == E.GOAL:
        return [("goal", 0.0)]
    if tipo == E.ROTTURA:
        return [("rottura", 0.0)]
    if tipo == E.RECUPERO:
        return [("recupero", 0.0)]
    return []


class Varianti:
    """
    Il giro delle varianti dentro una composizione: ogni ruolo ha il suo contatore, che dà 0, 1, 2, 3
    e ricomincia, così due suoni di rumore dello stesso ruolo, uno dopo l'altro, non sono mai uguali
    campione per campione.
    """

    def __init__(self):
        self._conti = collections.defaultdict(itertools.count)

    def __call__(self, ruolo):
        return next(self._conti[ruolo]) % VARIANTI_RUMORE


def _fermo(ruolo, t, pos, evento, variante=0, mono=None, guadagno=None):
    if mono is None:
        mono = sorgente(ruolo, variante=variante)
    return Posato(ruolo, t, mono, np.array([0.0]), [pos], None if guadagno is None else np.array([guadagno]), evento, variante)


def _in_aria(prima, dopo):
    return dopo.tipo in FINE_IN_ARIA or prima.tipo in INIZIO_IN_ARIA


def posati_del_volo(e, varianti=None, causa=None):
    """
    Il rotolamento lungo il tratto del volo che sta sul tavolo, e i suoni delle tappe: sponde,
    schermo, terra, corpo. causa è quella del colpo che ha lanciato il volo, se si conosce.
    """
    from motore.tavolo import posizione_al_tempo

    if varianti is None:
        varianti = Varianti()
    volo = e.volo
    posati = []
    # Il rotolamento va dalla partenza fino alla prima tappa che lascia il tavolo; non c'è se la
    # pallina parte in aria.
    fine = volo[0].t if causa in CAUSE_IN_ARIA else volo[-1].t
    for prima, dopo in itertools.pairwise(volo):
        if _in_aria(prima, dopo):
            fine = min(fine, prima.t)
            break
    durata = fine - volo[0].t
    if durata > 0.02:
        tempi = np.arange(0.0, durata + PASSO, PASSO)
        posizioni = [posizione_al_tempo(volo, volo[0].t + x) for x in tempi]
        # Fra due tappe la velocità cala in modo uniforme: si interpola.
        v = np.interp(volo[0].t + tempi, [tp.t for tp in volo], [tp.v for tp in volo])
        guadagni = GUADAGNO_ROTOLAMENTO * np.clip(np.sqrt(np.maximum(v, 0.0) / V_RIF), 0.15, 1.3)
        posati.append(Posato("rotolamento", volo[0].t, nastro("rotolamento", durata, e.n), tempi, posizioni, guadagni, e.n))
    for tp in volo[1:]:
        ruolo = TAPPE_SONORE.get(tp.tipo)
        if ruolo:
            posati.append(_fermo(ruolo, tp.t, (tp.x, tp.y), e.n, varianti(ruolo)))
    return posati


def posati_dell_evento(e, varianti=None, causa=None):
    """
    I suoni di un evento: vuoto per quelli che sono stato del gioco, parole o silenzio. varianti è il
    giro della composizione, nuovo se manca; causa, per un volo, è quella del colpo che l'ha lanciato.
    """
    if varianti is None:
        varianti = Varianti()
    posati = [_fermo(ruolo, e.t + ritardo, e.pos, e.n, varianti(ruolo)) for ruolo, ritardo in suoni_fermi(e)]
    if e.tipo == E.CONTROLLO:
        variante = varianti("controllo")
        posati.append(_fermo("controllo", e.t, e.pos, e.n, variante, in_fila("controllo", max(e.durata, 0.15), variante), GUADAGNO_CONTROLLO))
    elif e.tipo == E.FISCHIO:
        posati.append(_fermo(f"fischio_{e.fischio}", e.t, e.pos, e.n, mono=sorgente(f"fischio_{e.fischio}", e.durata)))
    if e.volo and e.tipo in CON_VOLO:
        posati.extend(posati_del_volo(e, varianti, causa))
    return posati


def posa(eventi):
    """
    I suoni posati di tutti gli eventi, nell'ordine degli eventi, con un solo giro delle varianti.
    Ogni volo riceve la causa del colpo che l'ha lanciato: l'ultima battuta, colpo o parata di chi ha colpito.
    """
    varianti = Varianti()
    posati = []
    lancio = None
    for e in eventi:
        if e.tipo in LANCI:
            lancio = e
        causa = lancio.causa if e.tipo == E.VOLO and lancio is not None and lancio.chi == e.chi else None
        posati.extend(posati_dell_evento(e, varianti, causa))
    return posati


def componi(eventi, ascoltatore="A", spazio=SPAZIO, da=None, fine=None, anticipo=None):
    """
    Gli eventi dati composti in un buffer stereo per chi ascolta dalla testata della parte indicata:
    ogni suono posato, spazializzato e sommato al suo istante, esatto al campione. da è l'istante del
    primo campione: senza, il primo evento, o il primo suono se viene prima; gli eventi che vengono
    prima non suonano. fine è l'istante fin dove il buffer arriva almeno, anche in silenzio. Con
    anticipo il silenzio in testa si accorcia, e davanti al primo suono ne restano quei secondi, mai
    prima di da: è la ripartenza da fermi, che non fa aspettare chi ha premuto il tasto.
    """
    eventi = list(eventi)
    if da is not None:
        eventi = [e for e in eventi if e.t >= da - TOLLERANZA]
    posati = posa(eventi)
    if da is None:
        t0 = min([e.t for e in eventi[:1]] + [p.t for p in posati], default=0.0)
    else:
        t0 = da
    if anticipo is not None and posati:
        t0 = max(t0, min(p.t for p in posati) - anticipo)
    durata = max([p.t - t0 + len(p.mono) / FS for p in posati] + [0.0 if fine is None else fine - t0, 0.0])
    buffer = np.zeros((math.ceil(durata * FS) + 1, 2), dtype=np.float32)
    for p in posati:
        stereo = spazializza(p, ascoltatore, spazio)
        inizio = round((p.t - t0) * FS)
        if inizio < 0:
            # Un istante arrotondato può cadere mezzo millesimo prima del primo campione.
            stereo = stereo[-inizio:]
            inizio = 0
        buffer[inizio:inizio + len(stereo)] += stereo
    return Resa(buffer, t0, posati)


def con_margine(buffer, guadagno=GUADAGNO_PARTITA, tetto=TETTO):
    """Il buffer al guadagno dato, abbassato tutto insieme se un picco supera il tetto."""
    uscita = np.asarray(buffer, dtype=np.float32) * np.float32(guadagno)
    picco = float(np.max(np.abs(uscita))) if len(uscita) else 0.0
    if picco > tetto:
        # Il tetto nei float32 del buffer, arrotondato per difetto: 0,8 diventerebbe un soffio di più.
        limite = np.float32(tetto)
        if float(limite) > tetto:
            limite = np.nextafter(limite, np.float32(0.0))
        uscita *= limite / np.float32(picco)
        np.clip(uscita, -limite, limite, out=uscita)
    return uscita


def per_la_cassa(buffer, volume):
    """Il buffer pronto per la cassa al volume degli effetti, da 0 a 100: a 50 com'è stato pensato, mai sopra il tetto."""
    return con_margine(buffer, GUADAGNO_PARTITA * max(0, min(100, volume)) / VOLUME_DI_PROGETTO)


# La riproduzione.

class Cassa:
    """La cassa vera: un buffer acceso come ciclo di Acusticator, senza dissolvenza, con la maniglia che ferma soltanto lui."""

    @staticmethod
    def accendi(buffer):
        from GBUtils import Acusticator

        return Acusticator.ciclo_di(buffer, fs=FS, dissolvenza=0.0)


class Voce:
    """Un buffer che suona: la maniglia, quando è partito, da quale secondo, quanto dura e il silenzio messo davanti."""

    __slots__ = ("anticipo", "da", "durata", "maniglia", "partenza")

    def __init__(self, maniglia, partenza, da, durata, anticipo):
        self.maniglia = maniglia
        self.partenza = partenza
        self.da = da
        self.durata = durata
        self.anticipo = anticipo

    def posizione(self, adesso):
        """Il secondo del buffer che sta suonando."""
        return min(self.durata, self.da + max(0.0, adesso - self.partenza - self.anticipo))

    def finita(self, adesso):
        return adesso - self.partenza >= self.anticipo + self.durata - self.da

    def ferma(self):
        if self.maniglia is not None:
            self.maniglia.stop()
            self.maniglia = None


class Riproduttore:
    """
    Fa sentire i buffer della partita con la cassa, e tiene il tempo con l'orologio; le prove
    sostituiscono l'una e l'altro. Il buffer corrente è uno solo; quelli di prima, se si chiede di
    sovrapporli, finiscono di suonare la loro coda, e battito li ferma quando sono finiti. La coda di
    zeri fa sì che un battito in ritardo non faccia ripartire il ciclo. Se la cassa non si apre il
    tempo scorre lo stesso, in silenzio, e la finestra va avanti.
    """

    def __init__(self, cassa=None, orologio=time.monotonic):
        self.cassa = cassa if cassa is not None else Cassa()
        self.orologio = orologio
        self.corrente = None
        self._code = []

    def suona(self, buffer, da=0.0, anticipo=0.0, sovrapponi=False):
        """Fa partire buffer dal secondo da, dopo anticipo secondi di silenzio, e restituisce la Voce."""
        if sovrapponi:
            if self.corrente is not None:
                self._code.append(self.corrente)
        else:
            self.ferma()
        durata = len(buffer) / FS
        da = max(0.0, min(da, durata))
        pezzi = [np.zeros((round(anticipo * FS), 2), dtype=np.float32), np.asarray(buffer, dtype=np.float32)[round(da * FS):],
                 np.zeros((round(CODA_DI_ZERI * FS), 2), dtype=np.float32)]
        maniglia = self.cassa.accendi(np.concatenate(pezzi)) if np.any(buffer) else None
        self.corrente = Voce(maniglia, self.orologio(), da, durata, anticipo)
        return self.corrente

    def posizione(self):
        """Il secondo del buffer corrente che sta suonando, o None se non suona niente."""
        return None if self.corrente is None else self.corrente.posizione(self.orologio())

    def finito(self):
        """Vero se il buffer corrente è finito tutto, coda dei suoni compresa."""
        return self.corrente is not None and self.corrente.finita(self.orologio())

    def battito(self):
        """Ferma i buffer finiti, quelli di prima e il corrente; restituisce vero se il corrente è finito."""
        adesso = self.orologio()
        for voce in [v for v in self._code if v.finita(adesso)]:
            voce.ferma()
            self._code.remove(voce)
        if self.corrente is not None and self.corrente.finita(adesso):
            self.corrente.ferma()
            return True
        return False

    def ferma(self):
        """Ferma tutto e restituisce il secondo a cui era arrivato il buffer corrente, o None."""
        posizione = self.posizione()
        for voce in self._code:
            voce.ferma()
        self._code = []
        if self.corrente is not None:
            self.corrente.ferma()
        self.corrente = None
        return posizione


# La cronologia dell'incontro dal vivo.

# Le chiusure di un segmento: il punto, la ripetizione e le sanzioni, se non chiudono il set; la
# fine del set, se non è l'ultimo; la fine dell'incontro; e l'ultimo evento dei preliminari.
CHIUSURE_DEL_PUNTO = frozenset((E.PUNTO, E.RIPETIZIONE, E.AMMONIZIONE, E.PENALITA))
SANZIONI = frozenset((E.AMMONIZIONE, E.PENALITA))


@dataclass
class Segmento:
    """
    Un tratto dell'incontro fino a un punto, una sanzione o una fine di set. voci sono le terne di
    evento, momento e se l'evento apre il suo momento; inizio è da dove comincia il suono quando si
    riparte da fermi, cioè dalla ripresa del gioco, perché pause e procedura che vengono prima le
    decide chi ascolta; fine è l'istante della chiusura, dove comincia il segmento che segue.
    """
    voci: list
    inizio: float
    fine: float

    @property
    def eventi(self):
        return [e for e, _m, _a in self.voci]

    @property
    def chiusura(self):
        return self.voci[-1][0]

    @property
    def riscaldamento(self):
        """Vero se il segmento è quello dei preliminari, con il riscaldamento."""
        return any(e.tipo == E.RISCALDAMENTO_FINE for e in self.eventi)

    @property
    def fine_set(self):
        return self.chiusura.tipo in (E.FINE_SET, E.FINE_INCONTRO)

    @property
    def ultimo(self):
        return self.chiusura.tipo == E.FINE_INCONTRO


def set_finito(punteggio, formato):
    a, b = punteggio
    return max(a, b) >= formato.punti_set and abs(a - b) >= formato.scarto


class Cronologia:
    """
    L'incontro dal vivo diviso in segmenti, ciascuno fino a un punto, una sanzione o una fine di set.
    Svolge l'incontro un momento alla volta, solo quando serve, e prima di ogni momento gli dà la
    velocità di gioco del momento, così un cambio vale dalla procedura che segue.
    """

    def __init__(self, incontro):
        self.incontro = incontro
        self._momenti = incontro.momenti()
        self._in_attesa = collections.deque()
        self.esaurita = False

    def _chiude(self, evento, momento):
        if evento.tipo in CHIUSURE_DEL_PUNTO:
            return not (evento.punteggio is not None and evento.tipo != E.RIPETIZIONE and set_finito(evento.punteggio, self.incontro.formato))
        if evento.tipo == E.FINE_SET:
            return not (evento.dati or {}).get("ultimo")
        if evento.tipo == E.FINE_INCONTRO:
            return True
        return momento.genere == "preliminari" and evento is momento.eventi[-1]

    def _carica(self, velocita):
        if velocita is not None:
            self.incontro.imposta_velocita(velocita)
        try:
            momento = next(self._momenti)
        except StopIteration:
            self.esaurita = True
            return False
        self._in_attesa.extend((e, momento, i == 0) for i, e in enumerate(momento.eventi))
        return True

    def prossimo(self, velocita=None):
        """Il segmento che segue, svolgendo i momenti che servono alla velocità data; None a incontro finito."""
        voci = []
        while True:
            if not self._in_attesa and (self.esaurita or not self._carica(velocita)):
                break
            if not self._in_attesa:
                continue
            voce = self._in_attesa.popleft()
            voci.append(voce)
            if self._chiude(voce[0], voce[1]):
                break
        if not voci:
            return None
        chiusura = voci[-1][0]
        return Segmento(voci, _inizio_del_gioco(voci), chiusura.t + chiusura.durata)


def _inizio_del_gioco(voci):
    """L'istante del primo momento di gioco del segmento: i preliminari, un punto o una sanzione, dal suo primo evento."""
    for evento, momento, apre in voci:
        if apre and (momento.genere in ("preliminari", "punto") or any(e.tipo in SANZIONI for e in momento.eventi)):
            return evento.t
    return voci[0][0].t
