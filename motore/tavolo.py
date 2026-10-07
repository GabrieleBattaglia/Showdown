"""
Il tavolo da showdown di MESS: misure, coordinate, traiettorie e vista di chi ascolta.
Autori: Gabriele Battaglia (IZ4APU) & ClaudIA (Claude Opus 5.5, UltraCode).
Nasce il 2026-10-07 con la tappa 9, decisione D25. Il riferimento è uno solo, in centimetri, ancorato
alla parte A, cioè al primo giocatore o alla squadra A: x va da 0 a 122, da sinistra a destra viste
da A; y va da 0, sulla linea di porta di A, a 366, su quella di B. Lo schermo sta a y 183. Il
riferimento non cambia al cambio campo, perché chi ascolta resta alla sua testata.
Chi colpisce ragiona nel suo riferimento: u dalla sua sponda sinistra, v dalla sua linea di porta.
Per A coincide con quello assoluto, per B è lo specchio. I rimbalzi si calcolano col metodo delle
immagini: l'arrivo si specchia rispetto alle sponde in ordine inverso, si traccia la retta e la si
ripiega, così nessun punto di rimbalzo si sceglie a mano. Ogni tratto rallenta per il rotolamento e
ogni sponda toglie una parte della velocità.
La vista ribalta per il giocatore lontano sinistra e destra, come chiede la decisione D11, in un
punto solo: il pan va da -1, tutto a sinistra, a 1, tutto a destra, e la distanza si misura da un
punto d'ascolto 40 cm dietro il centro della testata di chi ascolta. Qui non c'è il caso.
"""

import itertools
import math

from costanti import (
    ASCOLTO_DIETRO_TESTATA,
    DISTANZA_ARBITRO,
    LARGHEZZA_TAVOLO,
    LUNGHEZZA_TAVOLO,
    META_TAVOLO,
    MEZZA_ZONA_CENTRALE,
    RAGGIO_AREA_PORTA,
    RAGGIO_CURVE,
    RAGGIO_PALLINA,
    RAGGIO_TASCA,
    VOLUME_RIFERIMENTO_CM,
)
from motore.eventi import ErroreMotore, Tappa

CENTRO_X = LARGHEZZA_TAVOLO / 2
# Le sponde e le linee di fondo efficaci per il centro della pallina.
SPONDA_SINISTRA_A = float(RAGGIO_PALLINA)
SPONDA_DESTRA_A = float(LARGHEZZA_TAVOLO - RAGGIO_PALLINA)
FONDO_A = float(RAGGIO_PALLINA)
FONDO_B = float(LUNGHEZZA_TAVOLO - RAGGIO_PALLINA)
# Il margine dalle sponde dentro cui la regia mette le palline in gioco.
MARGINE_GIOCO = 2.0 * RAGGIO_PALLINA


def specchia(x, y):
    """Il punto visto dall'altra testata."""
    return LARGHEZZA_TAVOLO - x, LUNGHEZZA_TAVOLO - y


def locale_in_assoluto(parte, u, v):
    """Dal riferimento di chi colpisce, u dalla sua sponda sinistra e v dalla sua linea di porta, a quello di A."""
    if parte == "A":
        return float(u), float(v)
    return specchia(u, v)


def sponda_assoluta(parte, nome):
    """La x efficace della sponda sinistra o destra di una parte, nel riferimento di A."""
    sinistra = nome == "sinistra"
    if parte == "B":
        sinistra = not sinistra
    return SPONDA_SINISTRA_A if sinistra else SPONDA_DESTRA_A


def lato_di(x, parte):
    """Sinistra, centro o destra, dal punto di vista della parte: il centro sta entro 20 cm dal mezzo."""
    scarto = x - CENTRO_X
    if parte == "B":
        scarto = -scarto
    if scarto < -MEZZA_ZONA_CENTRALE:
        return "sinistra"
    if scarto > MEZZA_ZONA_CENTRALE:
        return "destra"
    return "centro"


_ZONE = {"sinistra": "sx", "centro": "centro", "destra": "dx"}


def zona_di_difesa(x, parte):
    """La zona del corpo di chi difende, sx, centro o dx, con lo stesso confine di lato_di."""
    return _ZONE[lato_di(x, parte)]


def distanza_di(y, parte):
    """I centimetri dalla linea di fondo della parte."""
    return y if parte == "A" else LUNGHEZZA_TAVOLO - y


def centro_porta(parte):
    return (CENTRO_X, 0.0) if parte == "A" else (CENTRO_X, float(LUNGHEZZA_TAVOLO))


def _dalla_porta(pos, parte):
    cx, cy = centro_porta(parte)
    return math.hypot(pos[0] - cx, pos[1] - cy)


def in_area_di_porta(pos, parte):
    """Vero se il punto sta nel semicerchio di 40 cm di diametro attorno alla tasca della parte."""
    return _dalla_porta(pos, parte) <= RAGGIO_AREA_PORTA


def in_tasca(pos, parte):
    """Vero se il punto sta nella tasca di porta della parte, larga 30 cm."""
    return _dalla_porta(pos, parte) <= RAGGIO_TASCA


def intervallo_zona(zona, parte):
    """L'intervallo di x, nel riferimento di A, della zona sx, centro o dx di chi difende, dentro i margini di gioco."""
    sinistra = (MARGINE_GIOCO, CENTRO_X - MEZZA_ZONA_CENTRALE - 0.5)
    centro = (CENTRO_X - MEZZA_ZONA_CENTRALE, CENTRO_X + MEZZA_ZONA_CENTRALE)
    destra = (CENTRO_X + MEZZA_ZONA_CENTRALE + 0.5, LARGHEZZA_TAVOLO - MARGINE_GIOCO)
    if zona == "centro":
        return centro
    vicino_a_x_zero = (zona == "sx") == (parte == "A")
    return sinistra if vicino_a_x_zero else destra


def _tratto(v_entrata, lunghezza, decelerazione):
    """Velocità d'uscita e durata di un tratto rettilineo che rallenta per il rotolamento."""
    if lunghezza <= 0:
        return v_entrata, 0.0
    if decelerazione <= 0:
        return v_entrata, lunghezza / max(v_entrata, 1e-9)
    quadrato = v_entrata * v_entrata - 2.0 * decelerazione * lunghezza
    v_uscita = math.sqrt(quadrato) if quadrato > 0 else 0.0
    return v_uscita, (v_entrata - v_uscita) / decelerazione


def _istante_a_distanza(v_entrata, distanza, decelerazione):
    """Il tempo e la velocità dopo una certa distanza percorsa dentro un tratto."""
    if decelerazione <= 0:
        return distanza / max(v_entrata, 1e-9), v_entrata
    quadrato = v_entrata * v_entrata - 2.0 * decelerazione * distanza
    v = math.sqrt(quadrato) if quadrato > 0 else 0.0
    return (v_entrata - v) / decelerazione, v


def _vicino_a_un_angolo(y):
    return y < FONDO_A + RAGGIO_CURVE or y > FONDO_B - RAGGIO_CURVE


def traiettoria(partenza, arrivo, sponde, v0, t0, decelerazione, perdita_per_sponda, tipo_arrivo="arrivo"):
    """
    Il volo della pallina da partenza ad arrivo, con i rimbalzi sulle sponde indicate, in ordine,
    come x efficaci nel riferimento di A. Restituisce la tupla delle tappe: la partenza, i
    rimbalzi, che vicino a un angolo diventano curve, il passaggio sotto lo schermo, e l'arrivo
    con il tipo indicato. Le sponde in fila devono essere diverse, altrimenti è ErroreMotore.
    """
    x, y = float(partenza[0]), float(partenza[1])
    xa, ya = float(arrivo[0]), float(arrivo[1])
    tappe = [Tappa(t0, x, y, v0, "partenza")]
    t, v = t0, v0
    rimaste = list(sponde)
    while True:
        if rimaste:
            immagine = xa
            for sponda in reversed(rimaste):
                immagine = 2.0 * sponda - immagine
            sponda = rimaste.pop(0)
            if abs(immagine - x) < 1e-9:
                raise ErroreMotore("Traiettoria impossibile: la pallina non raggiunge la sponda.")
            frazione = (sponda - x) / (immagine - x)
            if not 0.0 < frazione < 1.0:
                raise ErroreMotore(f"Traiettoria impossibile: la sponda a x {sponda} non sta fra la partenza e l'immagine dell'arrivo.")
            fine = (sponda, y + frazione * (ya - y))
            tipo_fine = "curva" if _vicino_a_un_angolo(fine[1]) else "sponda"
        else:
            fine = (xa, ya)
            tipo_fine = tipo_arrivo
        lunghezza = math.hypot(fine[0] - x, fine[1] - y)
        if (y - META_TAVOLO) * (fine[1] - META_TAVOLO) < 0:
            quota = (META_TAVOLO - y) / (fine[1] - y)
            dt, vs = _istante_a_distanza(v, quota * lunghezza, decelerazione)
            tappe.append(Tappa(t + dt, x + quota * (fine[0] - x), float(META_TAVOLO), vs, "sotto_schermo"))
        v, durata = _tratto(v, lunghezza, decelerazione)
        t += durata
        x, y = fine
        tappe.append(Tappa(t, x, y, v, tipo_fine))
        if tipo_fine in ("sponda", "curva"):
            v *= 1.0 - perdita_per_sponda
        else:
            break
    return tuple(tappe)


def partenza_massima_battuta(u_arrivo, v_arrivo, v_partenza=25.0, rimbalzo_massimo=175.0):
    """
    Per una battuta sinistra, nel riferimento di chi batte: la partenza u più lontana dalla sponda
    sinistra che, con l'arrivo indicato, mette il rimbalzo a rimbalzo_massimo cm dalla linea, cioè
    prima dello schermo. Per la battuta destra si usa lo specchio, 122 meno u.
    """
    f = (rimbalzo_massimo - v_partenza) / (v_arrivo - v_partenza)
    return (f * (u_arrivo - 2.0 * SPONDA_SINISTRA_A) + SPONDA_SINISTRA_A) / (1.0 - f)


def posizione_al_tempo(volo, t):
    """Dove sta la pallina all'istante t del volo, con il rallentamento uniforme di ogni tratto."""
    if t <= volo[0].t:
        return volo[0].x, volo[0].y
    for prima, dopo in itertools.pairwise(volo):
        if t <= dopo.t:
            durata = dopo.t - prima.t
            if durata <= 0:
                return dopo.x, dopo.y
            tau = t - prima.t
            # Velocità d'ingresso nel tratto: dopo una sponda è già ridotta, e si ricava dalla
            # lunghezza e dalla durata, perché il rallentamento è uniforme.
            lunghezza = math.hypot(dopo.x - prima.x, dopo.y - prima.y)
            v_entrata = 2.0 * lunghezza / durata - dopo.v
            decelerazione = (v_entrata - dopo.v) / durata
            percorsa = v_entrata * tau - decelerazione * tau * tau / 2.0
            quota = min(1.0, max(0.0, percorsa / lunghezza)) if lunghezza > 0 else 1.0
            return prima.x + quota * (dopo.x - prima.x), prima.y + quota * (dopo.y - prima.y)
    return volo[-1].x, volo[-1].y


def vista(pos, parte_osservatore):
    """
    Pan, distanza e lato di un punto per chi ascolta dalla testata della parte indicata: pan da
    -1, sinistra, a 1, destra; distanza dal punto d'ascolto 40 cm dietro il centro della testata.
    """
    x, y = pos
    scarto = x - CENTRO_X
    if parte_osservatore == "B":
        scarto = -scarto
        y = LUNGHEZZA_TAVOLO - y
    pan = max(-1.0, min(1.0, scarto / CENTRO_X))
    distanza = math.hypot(scarto, y + ASCOLTO_DIETRO_TESTATA)
    return pan, distanza, lato_di(pos[0], parte_osservatore)


def volume(distanza):
    """Il volume proposto per la tappa 10: pieno vicino, la metà a 150 cm."""
    return 1.0 / (1.0 + distanza / VOLUME_RIFERIMENTO_CM)


def posizione_arbitro(a_sinistra_di_a):
    """Dove sta l'arbitro, a metà tavolo, alla sinistra o alla destra di A."""
    if a_sinistra_di_a:
        return (-float(DISTANZA_ARBITRO), float(META_TAVOLO))
    return (float(LARGHEZZA_TAVOLO + DISTANZA_ARBITRO), float(META_TAVOLO))
