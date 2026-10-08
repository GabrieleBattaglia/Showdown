"""
MESS, il prototipo della resa sonora di un punto, strumento provvisorio dell'ascolto libero della tappa 10.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-08 dal prototipo scritto per le misure dell'inizio della tappa 10, quelle che hanno
portato alla decisione D28: il motore conosce in anticipo tutti gli eventi di un punto con i loro
tempi, e la resa li compone in un solo buffer stereo, con numpy e scipy, che poi va al mixer di
Acusticator con una chiamata sola. Qui non si suona niente: si restituisce il buffer.
È uno strumento provvisorio. Serve all'ascolto libero di strumenti/ascolta_partita.py, per sentire
lati, movimento e tempi con suoni segnaposto presi dalla collezione di GBUtils; i dosaggi dello
spazio si decidono dopo, alla cieca, e i timbri per ultimi. La partita live vera avrà il suo
modulo, che nascerà da questo dopo gli ascolti.
Come suona un punto. Chi ascolta sta alla testata della sua parte, di solito A. Ogni suono si
sintetizza al centro e si riduce a una sorgente mono: lo spazio lo mette la resa, con il pan dalla
coordinata laterale e il volume dalla distanza di motore.tavolo.vista e motore.tavolo.volume, così
il ribaltamento dei lati per il giocatore lontano, chiesto da D11, resta in un punto solo. Sopra c'è
un passa basso a due poli, il cui taglio scende con la distanza. Lungo i voli posizione, pan, volume
e taglio seguono la pallina a passi di 5 millesimi, e il rotolamento dura quanto il tratto del volo
che sta sul tavolo, tagliato da un nastro di rumore sintetizzato una volta sola, con un livello che
cala con la velocità.
Le correzioni rispetto al prototipo delle misure, secondo le obiezioni del critico. Il suono si
sceglie dal tipo dell'evento, dal suo esito e dalla sua causa, non dal solo tipo: il colpo a vuoto
non ha più il suono della battuta ma il suo, la battuta col doppio tocco fa sentire il secondo tocco,
la paletta che cade ha il suo suono al posto di quello del colpo o della parata, come vuole D28, e la
parata che non arriva, o quella che prende il corpo, non fa il rumore della paletta sulla pallina. I
suoni di rumore, che Acusticator sintetizza diversi ogni volta, hanno quattro varianti, scelte col
numero dell'evento, così due parate vicine non sono identiche campione per campione; quelli tonali si
sintetizzano una volta sola. Il livello si tiene con margine: un guadagno fisso di partita e un
tetto, sotto il quale il buffer scende tutto insieme se un picco lo supera, qualunque sia il volume
degli effetti della finestra. Le parole dell'arbitro, annuncio, domanda di pronto e chiamata, non
hanno un suono: nella live le dirà la cronaca, e nell'ascolto libero si leggono prima del punto.
Nessun segnaposto è più un suono della finestra: la sponda, che usava quello della scheda del
giocatore, prende un fruscio quasi uguale della collezione. Lo strumento non scrive più file WAV:
il punto si compone al volo.
"""

import itertools
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

RADICE = Path(__file__).resolve().parent.parent
if str(RADICE) not in sys.path:
    sys.path.insert(0, str(RADICE))

FS = 44100
# Il passo di controllo lungo i voli: pan, volume e taglio cambiano ogni 5 millesimi.
PASSO = 0.005
CAMPIONI_PASSO = round(PASSO * FS)
# Il passa basso: aperto fino a D0 centimetri, poi il taglio scende come D0 diviso la distanza, fino a FC_MIN.
FC_MAX = 18000.0
FC_MIN = 1500.0
D0 = 60.0
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
# Il livello: il guadagno fisso della partita, e il tetto che nessun picco supera.
GUADAGNO_PARTITA = 1.0
TETTO = 0.8

# I preset segnaposto della collezione di GBUtils, uno per ruolo e mai lo stesso per due ruoli.
# Nessuno è fra quelli della finestra di MESS, in suoni.EVENTI, perché nell'ascolto un suono
# della finestra non si confonda con un evento della partita.
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
# Gli eventi che portano un volo da far sentire.
CON_VOLO = frozenset(("VOLO", "CONSEGNA", "RISCALDAMENTO_COLPO"))
# Le parate che non mettono la paletta sulla pallina: quella che non arriva, quella che prende il
# corpo, che suona con la tappa del volo, e quella a cui cade la paletta, che suona col fallo.
CAUSE_SENZA_PARATA = frozenset(("body_touch", "body_touch_pieno", "paletta_caduta"))
FINE_AZIONE = ("PUNTO", "RIPETIZIONE")
# Gli eventi della procedura prima del fischio: l'azione non comincia prima di loro.
PROCEDURA = frozenset(("RECUPERO", "CONSEGNA", "ANNUNCIO", "DOMANDA_PRONTO"))


@dataclass
class Posato:
    """Un suono messo nel punto: il ruolo, l'istante, la sorgente mono, le posizioni ai passi di controllo dal suo inizio, una sola se sta fermo."""
    ruolo: str
    t: float
    mono: np.ndarray
    tempi: np.ndarray
    posizioni: list
    guadagni: np.ndarray | None = None
    evento: int = 0


@dataclass
class Resa:
    """Il buffer stereo del punto, l'istante del suo primo campione e i suoni posati, per verificarlo."""
    buffer: np.ndarray
    t0: float
    posati: list


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
    tengono VARIANTI_RUMORE varianti, e variante, di solito il numero dell'evento, sceglie quale.
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
    # Lo spazio lo mette la resa: il panorama proprio del preset si porta al centro.
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


# La geometria.

def taglio(d):
    """La frequenza di taglio del passa basso alla distanza d, in centimetri."""
    return float(min(FC_MAX, max(FC_MIN, FC_MAX * D0 / max(d, D0))))


def campi(posizioni, ascoltatore):
    """Pan, volume e taglio di ogni posizione, per chi ascolta dalla testata della parte indicata."""
    from motore.tavolo import vista, volume

    pan = np.empty(len(posizioni))
    vol = np.empty(len(posizioni))
    fc = np.empty(len(posizioni))
    for i, p in enumerate(posizioni):
        pan[i], d, _lato = vista(p, ascoltatore)
        vol[i] = volume(d)
        fc[i] = taglio(d)
    return pan, vol, fc


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


def spazializza(posato, ascoltatore):
    """La sorgente mono di un suono resa stereo per chi ascolta: un array di campioni per 2, float32."""
    mono = posato.mono
    pan, vol, fc = campi(posato.posizioni, ascoltatore)
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
    if tipo == "BATTUTA":
        if causa == "battuta_a_vuoto":
            return [("colpo_a_vuoto", 0.0)]
        if causa == "battuta_doppio_tocco":
            return [("battuta", 0.0), ("secondo_tocco", RITARDO_SECONDO_TOCCO)]
        return [("battuta", 0.0)]
    if tipo in ("COLPO", "RISCALDAMENTO_COLPO"):
        return [] if causa == "paletta_caduta" else [("colpo", 0.0)]
    if tipo == "PARATA":
        return [] if esito == "goal" or causa in CAUSE_SENZA_PARATA else [("parata", 0.0)]
    if tipo == "FALLO":
        return [("paletta_caduta", 0.0)] if causa == "paletta_caduta" else []
    if tipo == "GOAL":
        return [("goal", 0.0)]
    if tipo == "ROTTURA":
        return [("rottura", 0.0)]
    if tipo == "RECUPERO":
        return [("recupero", 0.0)]
    return []


def _fermo(ruolo, t, pos, numero, mono=None, guadagno=None):
    if mono is None:
        mono = sorgente(ruolo, variante=numero)
    return Posato(ruolo, t, mono, np.array([0.0]), [pos], None if guadagno is None else np.array([guadagno]), numero)


def _in_aria(prima, dopo):
    return dopo.tipo in FINE_IN_ARIA or prima.tipo in INIZIO_IN_ARIA


def posati_del_volo(e):
    """Il rotolamento lungo il tratto del volo che sta sul tavolo, e i suoni delle tappe: sponde, schermo, terra, corpo."""
    from motore.tavolo import posizione_al_tempo

    volo = e.volo
    posati = []
    # Il rotolamento va dalla partenza fino alla prima tappa che lascia il tavolo.
    fine = volo[-1].t
    for prima, dopo in itertools.pairwise(volo):
        if _in_aria(prima, dopo):
            fine = prima.t
            break
    durata = fine - volo[0].t
    if durata > 0.02:
        tempi = np.arange(0.0, durata + PASSO, PASSO)
        posizioni = [posizione_al_tempo(volo, volo[0].t + x) for x in tempi]
        # Fra due tappe la velocità cala in modo uniforme: si interpola.
        v = np.interp(volo[0].t + tempi, [tp.t for tp in volo], [tp.v for tp in volo])
        guadagni = GUADAGNO_ROTOLAMENTO * np.clip(np.sqrt(np.maximum(v, 0.0) / V_RIF), 0.15, 1.3)
        posati.append(Posato("rotolamento", volo[0].t, nastro("rotolamento", durata, e.n), tempi, posizioni, guadagni, e.n))
    for k, tp in enumerate(volo[1:], 1):
        ruolo = TAPPE_SONORE.get(tp.tipo)
        if ruolo:
            posati.append(_fermo(ruolo, tp.t, (tp.x, tp.y), e.n + k))
    return posati


def posati_dell_evento(e):
    """I suoni di un evento: vuoto per quelli che sono stato del gioco, parole o silenzio."""
    posati = [_fermo(ruolo, e.t + ritardo, e.pos, e.n) for ruolo, ritardo in suoni_fermi(e)]
    if e.tipo == "CONTROLLO":
        posati.append(_fermo("controllo", e.t, e.pos, e.n, in_fila("controllo", max(e.durata, 0.15), e.n), GUADAGNO_CONTROLLO))
    elif e.tipo == "FISCHIO":
        posati.append(_fermo(f"fischio_{e.fischio}", e.t, e.pos, e.n, sorgente(f"fischio_{e.fischio}", e.durata)))
    if e.volo and e.tipo in CON_VOLO:
        posati.extend(posati_del_volo(e))
    return posati


def azione(eventi):
    """
    Gli eventi dell'azione di un punto: dal fischio che dà il via alla battuta, o dalla battuta se
    chi batte non l'aspetta, fino al PUNTO o alla RIPETIZIONE. La procedura che viene prima la fa
    l'arbitro con le parole, e quello che segue sono pause.
    """
    eventi = list(eventi)
    i_battuta = next((i for i, e in enumerate(eventi) if e.tipo == "BATTUTA"), None)
    if i_battuta is None:
        raise ValueError("Un punto senza battuta.")
    inizio = i_battuta
    for i in range(i_battuta - 1, -1, -1):
        if eventi[i].tipo in PROCEDURA:
            break
        if eventi[i].tipo == "FISCHIO":
            inizio = i
            break
    fine = next((i for i, e in enumerate(eventi) if i > i_battuta and e.tipo in FINE_AZIONE), len(eventi) - 1)
    return eventi[inizio:fine + 1]


def posa(eventi):
    """I suoni posati di tutti gli eventi, nell'ordine degli eventi."""
    posati = []
    for e in eventi:
        posati.extend(posati_dell_evento(e))
    return posati


def componi(eventi, ascoltatore="A"):
    """Il punto per chi ascolta dalla testata indicata: ogni suono posato, spazializzato e sommato al suo istante, esatto al campione."""
    eventi = list(eventi)
    posati = posa(eventi)
    if not posati:
        return Resa(np.zeros((0, 2), dtype=np.float32), eventi[0].t if eventi else 0.0, [])
    # Gli istanti degli eventi sono arrotondati al millesimo, quelli delle tappe no: un volo può
    # cominciare fino a mezzo millesimo prima del suo evento.
    t0 = min([eventi[0].t] + [p.t for p in posati])
    fine = max(p.t - t0 + len(p.mono) / FS for p in posati)
    buffer = np.zeros((math.ceil(fine * FS) + 1, 2), dtype=np.float32)
    for p in posati:
        stereo = spazializza(p, ascoltatore)
        inizio = round((p.t - t0) * FS)
        buffer[inizio:inizio + len(stereo)] += stereo
    return Resa(buffer, t0, posati)


def con_margine(buffer, guadagno=GUADAGNO_PARTITA, tetto=TETTO):
    """Il buffer al guadagno fisso della partita, abbassato tutto insieme se un picco supera il tetto."""
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
